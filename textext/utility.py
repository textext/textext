"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2021 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

Provides handlers for temp-dir management, logging, settings and
system command execution
"""
import contextlib
import json
import logging.handlers
import os
import platform
import shutil
import stat
import subprocess
import tempfile

from .errors import *
import sys


class ChangeDirectory(object):
    def __init__(self, dir):
        self.new_dir = dir
        self.old_dir = os.path.abspath(os.path.curdir)

    def __enter__(self):
        os.chdir(self.new_dir)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.old_dir)


class TemporaryDirectory(object):
    """ Mimic tempfile.TemporaryDirectory from python3 """
    def __init__(self):
        self.dir_name = None

    def __enter__(self):
        self.dir_name = tempfile.mkdtemp("textext_")
        return self.dir_name

    def __exit__(self, exc_type, exc_val, exc_tb):

        def retry_with_chmod(func, path, exec_info):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        if self.dir_name:
            shutil.rmtree(self.dir_name, onerror=retry_with_chmod)


@contextlib.contextmanager
def ChangeToTemporaryDirectory():
    with TemporaryDirectory() as temp_dir:
        with ChangeDirectory(temp_dir):
            yield None


class MyLogger(logging.Logger):
    """
        Needs to produce correct line numbers
    """
    def findCaller(self, *args):
        n_frames_upper = 2
        f = logging.currentframe()
        for _ in range(2 + n_frames_upper):  # <-- correct frame
            if f is not None:
                f = f.f_back
        rv = "(unknown file)", 0, "(unknown function)", None
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename == logging._srcfile:
                f = f.f_back
                continue
            rv = (co.co_filename, f.f_lineno, co.co_name, None)
            break
        if sys.version_info[0] == 2:  # ToDo: Remove when Python 2 support is deprecated
            rv = rv[0:3]
        return rv


class NestedLoggingGuard(object):
    message_offset = 0
    message_indent = 2

    def __init__(self, _logger, lvl=None, message=None):
        self._logger = _logger
        self._level = lvl
        self._message = message
        if lvl is not None and message is not None:
            self._logger.log(self._level, " " * NestedLoggingGuard.message_offset + self._message)

    def __enter__(self):
        assert self._level is not None
        assert self._message is not None
        NestedLoggingGuard.message_offset += NestedLoggingGuard.message_indent

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self._level is not None
        assert self._message is not None
        if exc_type is None:
            result = "done"
        else:
            result = "failed"
        NestedLoggingGuard.message_offset -= NestedLoggingGuard.message_indent

        def tmp1():  # this nesting needed to even number of stack frames in __enter__ and __exit__
            def tmp2():
                self._logger.log(self._level, " " * NestedLoggingGuard.message_offset + self._message.strip() + " " + result)
            tmp2()
        tmp1()

    def debug(self, message):
        return self.log(logging.DEBUG, message)

    def info(self, message):
        return self.log(logging.INFO, message)

    def error(self, message):
        return self.log(logging.ERROR, message)

    def warning(self, message):
        return self.log(logging.WARNING, message)

    def critical(self, message):
        return self.log(logging.CRITICAL, message)

    def log(self, lvl, message):
        return NestedLoggingGuard(self._logger, lvl, message)


class CycleBufferHandler(logging.handlers.BufferingHandler):

    def __init__(self, capacity):
        super(CycleBufferHandler, self).__init__(capacity)

    def emit(self, record):
        self.buffer.append(record)
        if len(self.buffer) > self.capacity:
            self.buffer = self.buffer[-self.capacity:]

    def show_messages(self):
        import sys
        version_is_good = (2, 7) <= sys.version_info < (3, 0)
        if version_is_good:
            import inkex
            """show messages to user and empty buffer"""
            inkex.errormsg("\n".join([self.format(record) for record in self.buffer]))
        else:
            sys.stderr.write("\n".join([self.format(record) for record in self.buffer]))
        self.flush()


class Settings(object):
    def __init__(self, basename="config.json", directory=None):
        if directory is None:
            directory = os.getcwd()
        self.values = {}
        self.config_path = os.path.join(directory, basename)
        try:
            self.load()
        except ValueError as e:
            raise TexTextFatalError("Bad config `%s`: %s. Please fix it and re-run TexText." % (self.config_path, str(e)) )

    def load(self):
        if os.path.isfile(self.config_path):
            with open(self.config_path) as f:
                self.values = json.load(f)

    def save(self):
        with open(self.config_path, "w") as f:
            json.dump(self.values, f, indent=2)

    def get(self, key, default=None):
        result = self.values.get(key, default)
        if result is None:
            return default
        return result

    def __getitem__(self, key):
        return self.values.get(key)

    def __setitem__(self, key, value):
        self.values[key] = value


class Cache(Settings):
    def __init__(self, basename=".cache.json"):
        try:
            super(Cache, self).__init__(basename)
        except TexTextFatalError:
            pass


class SuppressStream(object):
    """
    "Suppress stream output" context manager

    Effectively redirects output to /dev/null by switching fileno
    """

    def __init__(self, stream=sys.stderr):
        self.orig_stream_fileno = stream.fileno()

    def __enter__(self):
        self.orig_stream_dup = os.dup(self.orig_stream_fileno)
        self.devnull = open(os.devnull, 'w')
        os.dup2(self.devnull.fileno(), self.orig_stream_fileno)

    def __exit__(self, type, value, traceback):
        os.close(self.orig_stream_fileno)
        os.dup2(self.orig_stream_dup, self.orig_stream_fileno)
        os.close(self.orig_stream_dup)
        self.devnull.close()


def exec_command(cmd, ok_return_value=0):
    """
    Run given command, check return value, and return
    concatenated stdout and stderr.
    :param cmd: Command to execute
    :param ok_return_value: The expected return value after successful completion
    :raises: TexTextCommandNotFound, TexTextCommandFailed
    """

    try:
        # hides the command window for cli tools that are run (in Windows)
        info = None
        if PLATFORM == WINDOWS:
            info = subprocess.STARTUPINFO()
            info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            info.wShowWindow = subprocess.SW_HIDE

        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.PIPE,
                             startupinfo=info)
        out, err = p.communicate()
    except OSError as err:
        raise TexTextCommandNotFound("Command %s failed: %s" % (' '.join(cmd), err))

    if ok_return_value is not None and p.returncode != ok_return_value:
        raise TexTextCommandFailed(message="Command %s failed (code %d)" % (' '.join(cmd), p.returncode),
                                   return_code=p.returncode,
                                   stdout=out,
                                   stderr=err)
    return out + err


MAC = "Darwin"
WINDOWS = "Windows"
PLATFORM = platform.system()