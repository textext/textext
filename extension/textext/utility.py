
import contextlib
import logging.handlers
import os
import platform
import shutil
import stat
import subprocess
import tempfile

from errors import *


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
    def findCaller(self):
        n_frames_upper = 2
        f = logging.currentframe()
        for _ in range(2 + n_frames_upper):  # <-- correct frame
            if f is not None:
                f = f.f_back
        rv = "(unknown file)", 0, "(unknown function)"
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename == logging._srcfile:
                f = f.f_back
                continue
            rv = (co.co_filename, f.f_lineno, co.co_name)
            break
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
        import inkex
        """show messages to user and empty buffer"""
        inkex.errormsg("\n".join([self.format(record) for record in self.buffer]))
        self.flush()


class Settings(object):
    def __init__(self):
        self.values = {}

        if PLATFORM == WINDOWS:
            self.keyname = r"Software\TexText\TexText"
        else:
            self.filename = os.path.expanduser("~/.inkscape/textextrc")

        self.load()

    def load(self):
        if PLATFORM == WINDOWS:
            import _winreg

            try:
                key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, self.keyname)
            except WindowsError:
                return
            try:
                self.values = {}
                for j in range(1000):
                    try:
                        name, data, dtype = _winreg.EnumValue(key, j)
                    except EnvironmentError:
                        break
                    self.values[name] = str(data)
            finally:
                key.Close()
        else:
            try:
                f = open(self.filename, 'r')
            except (IOError, OSError):
                return
            try:
                self.values = {}
                for line in f.read().split("\n"):
                    if '=' not in line:
                        continue
                    k, v = line.split("=", 1)
                    self.values[k.strip()] = v.strip()
            finally:
                f.close()

    def save(self):
        if PLATFORM == WINDOWS:
            import _winreg

            try:
                key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                                      self.keyname,
                                      0,
                                      _winreg.KEY_SET_VALUE | _winreg.KEY_WRITE)
            except WindowsError:
                key = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER, self.keyname)
            try:
                for k, v in self.values.iteritems():
                    _winreg.SetValueEx(key, str(k), 0, _winreg.REG_SZ, str(v))
            finally:
                key.Close()
        else:
            d = os.path.dirname(self.filename)
            if not os.path.isdir(d):
                os.makedirs(d)

            f = open(self.filename, 'w')
            try:
                data = '\n'.join(["%s=%s" % (k, v) for k, v in self.values.iteritems()])
                f.write(data)
            finally:
                f.close()

    def get(self, key, typecast, default=None):
        try:
            return typecast(self.values[key])
        except (KeyError, ValueError, TypeError):
            return default

    def set(self, key, value):
        self.values[key] = str(value)

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
        raise TexTextCommandFailed("Command %s failed (code %d): %s" % (' '.join(cmd), p.returncode, out + err))
    return out + err


MAC = "Darwin"
WINDOWS = "Windows"
PLATFORM = platform.system()