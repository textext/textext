"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2022 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

Utilities for improving, formatting and decorating log file output.
"""
import logging
import os

LOGLEVEL_VERBOSE = 5
LOGLEVEL_SUCCESS = 41
LOGLEVEL_UNKNOWN = 42


class TexTextLogger(logging.Logger):
    """
        Needed to produce correct line numbers
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
        return rv


class NestedLoggingGuard(object):
    """
    Esnures correct indentation of log file messages
    """
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
                self._logger.log(self._level, " " * NestedLoggingGuard.message_offset +
                                 self._message.strip() + " " + result)
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


class LoggingColors(object):
    """
    A helper class defining the colors we are using for logging. Objects of
    this class just return a pair level_colors, color_reset when they are called.

    level_colors is a dictionary the keys of which are the names of the
    logging level (e.g. "VERBOSE", "DEBUG", ...) and the values are two element
    lists. The first element of the list is the code of the level as defined
    in the Python logging module and the second element is the color associated
    to this level.

    color_reset is the string for reseting colored output in a terminal.

    Colored logging can be switched on and off via the attribute enable_colors.

    Example:
         get_level_colors = LoggingColors()
         get_level_colors()[0]["ERROR"][1]  # returns the color of an error
    """
    enable_colors = False

    COLOR_RESET = "\033[0m"
    FG_DEFAULT = "\033[39m"
    FG_BLACK = "\033[30m"
    FG_RED = "\033[31m"
    FG_GREEN = "\033[32m"
    FG_YELLOW = "\033[33m"
    FG_BLUE = "\033[34m"
    FG_MAGENTA = "\033[35m"
    FG_CYAN = "\033[36m"
    FG_LIGHT_GRAY = "\033[37m"
    FG_DARK_GRAY = "\033[90m"
    FG_LIGHT_RED = "\033[91m"
    FG_LIGHT_GREEN = "\033[92m"
    FG_LIGHT_YELLOW = "\033[93m"
    FG_LIGHT_BLUE = "\033[94m"
    FG_LIGHT_MAGENTA = "\033[95m"
    FG_LIGHT_CYAN = "\033[96m"
    FG_WHITE = "\033[97m"

    BG_DEFAULT = "\033[49m"
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_LIGHT_GRAY = "\033[47m"
    BG_DARK_GRAY = "\033[100m"
    BG_LIGHT_RED = "\033[101m"
    BG_LIGHT_GREEN = "\033[102m"
    BG_LIGHT_YELLOW = "\033[103m"
    BG_LIGHT_BLUE = "\033[104m"
    BG_LIGHT_MAGENTA = "\033[105m"
    BG_LIGHT_CYAN = "\033[106m"
    BG_WHITE = "\033[107m"

    UNDERLINED = "\033[4m"

    def __call__(self):
        levels = [
            LOGLEVEL_VERBOSE,  # 5
            logging.DEBUG,  # 10
            logging.INFO,  # 20
            logging.WARNING,  # 30
            logging.ERROR,  # 40
            LOGLEVEL_SUCCESS,  # 41
            LOGLEVEL_UNKNOWN,  # 42
            logging.CRITICAL  # 50
        ]
        names = [
            "VERBOSE ",
            "DEBUG   ",
            "INFO    ",
            "WARNING ",
            "ERROR   ",
            "SUCCESS ",
            "UNKNOWN ",
            "CRITICAL"
        ]
        colors = [
            self.COLOR_RESET,
            self.COLOR_RESET,
            self.BG_DEFAULT + self.FG_LIGHT_BLUE,
            self.BG_YELLOW + self.FG_WHITE,
            self.BG_DEFAULT + self.FG_RED,
            self.BG_DEFAULT + self.FG_GREEN,
            self.BG_DEFAULT + self.FG_YELLOW,
            self.BG_RED + self.FG_WHITE,
        ]
        if not LoggingColors.enable_colors:
            colors = [""] * len(colors)
            self.COLOR_RESET = ""
        return {name: (level, color) for level, name, color in zip(levels, names, colors)}, self.COLOR_RESET


def set_logging_levels():
    """ Sets the logging levels and colors of the central Python logging system (from logging module)

    """
    level_colors, color_reset = get_level_colors()
    for name, (level, color) in level_colors.items():
        logging.addLevelName(level, color + name + color_reset)


# Use this object for query logging colors
get_level_colors = LoggingColors()
