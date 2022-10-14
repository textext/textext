"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2022 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

Provides a class for managing the TexText settings. In fact
a convinience wrapper around a json dict.
"""
import json
import os
from .errors import *


class Settings(object):
    """
    Adds some convinient stuf around a json dict
    """

    def __init__(self, basename="config.json", directory=None):
        """

        Args:
            basename (str): The file name the config is stored. Default: "config.json"
            directory (str): The directory in which the file is located. Set to None if
                             file should be stored in the current working directory
        """
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
    """
    Same as Settings but silently discard any errors if file cannot be opened

    ToDo: Check if this really does make sense...
    """
    def __init__(self, basename=".cache.json", directory=None):
        try:
            super(Cache, self).__init__(basename, directory)
        except TexTextFatalError:
            pass
