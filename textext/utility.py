"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2022 TexText developers.

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
import tempfile
import re

from .errors import *


@contextlib.contextmanager
def change_to_temp_dir():
    with tempfile.TemporaryDirectory(prefix="textext_") as temp_dir:
        orig_dir = os.path.abspath(os.path.curdir)
        try:
            os.chdir(temp_dir)
            yield
        finally:
            os.chdir(orig_dir)


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
        else:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        self.values = {}
        self.directory = directory
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

    def delete_file(self):
        if os.path.exists(self.config_path):
            try:
                os.remove(self.config_path)
            except OSError as err:
                TexTextFatalError("Config `%s` could not be deleted. Error message: %s" % (
                                  self.config_path, str(err)))

    def __getitem__(self, key):
        return self.values.get(key)

    def __setitem__(self, key, value):
        if value is not None:
            self.values[key] = value
        else:
            self.values.pop(key, None)


class Cache(Settings):
    def __init__(self, basename=".cache.json", directory=None):
        try:
            super(Cache, self).__init__(basename, directory)
        except TexTextFatalError:
            pass


def version_greater_or_equal_than(version_str, other_version_str):
    """ Checks if a version number is >= than another version number

    Version numbers are passed as strings and must be of type "N.M.Rarb" where N, M, R
    are non negative decimal numbers < 1000 and arb is an arbitrary string.
    For example, "1.2.3" or "1.2.3dev" or "1.2.3-dev" or "1.2.3 dev" are valid version strings.

    Returns:
        True if the version number is equal or greater then the other version number,
        otherwise false

    """
    def ver_str_to_float(ver_str):
        """ Parse version string and returns it as a floating point value

        Returns The version string as floating point number for easy comparison
        (minor version and relase number padded with zeros). E.g. "1.23.4dev" -> 1.023004.
        If conversion fails returns NaN.

        """
        m = re.search(r"(\d+).(\d+).(\d+)[-\w]*", ver_str)
        if m is not None:
            ver_maj, ver_min, ver_rel = m.groups()
            return float("{}.{:0>3}{:0>3}".format(ver_maj, ver_min, ver_rel))
        else:
            return float("nan")

    return ver_str_to_float(version_str) >= ver_str_to_float(other_version_str)
