"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2023 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

Utilities for improving, formatting and decorating log file output.
"""
import logging
import logging.handlers
import os
import sys
import platform
from typing import Tuple, Union
from .environment import system_env

# Open logger before accessing Inkscape modules, so we can catch properly any errors thrown by them


class TexTextLogger(logging.Logger):
    """
        Needed to produce correct line numbers
    """
    def findCaller(self, *args):
        # pylint: disable=unused-argument
        n_frames_upper = 2
        cur_frame = logging.currentframe()
        for _ in range(2 + n_frames_upper):  # <-- correct frame
            if cur_frame is not None:
                cur_frame = cur_frame.f_back
        ret_val = "(unknown file)", 0, "(unknown function)", None
        while hasattr(cur_frame, "f_code"):
            cur_code = cur_frame.f_code
            filename = os.path.normcase(cur_code.co_filename)
            if filename == logging._srcfile:  # noqa  # pylint: disable=protected-access
                cur_frame = cur_frame.f_back
                continue
            ret_val = (cur_code.co_filename, cur_frame.f_lineno, cur_code.co_name, None)
            break
        return ret_val


class LoggingFormatter(logging.Formatter):
    """
    Formatter for the log messages. Color, date and time as well as
    message source can be configured.
    """

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

    def __init__(self, colored_messages: bool, with_datetime: bool, with_source: bool):
        """

        Args:
            colored_messages (bool): Set to True if the level of the message should be printed in color
            with_datetime (bool): Set to True if the log message shoud start with the date and time
            with_source (bool): Set to True of the filename and the linenumber of the source of the
                message should be added to the end to the message.
        """
        super().__init__()

        if colored_messages:
            log_format = "[%(name)s][{0}%(levelname)-8s{1}]: %(message)s"
        else:
            log_format = "[%(name)s][%(levelname)-8s]: %(message)s"

        if with_datetime:
            log_format = f"[%(asctime)s] {log_format}"

        if with_source:
            log_format += " // %(filename)s:%(lineno)d"

        if colored_messages:
            self.formats = {
                logging.DEBUG: log_format.format(self.COLOR_RESET, self.COLOR_RESET),
                logging.INFO: log_format.format(self.BG_DEFAULT + self.FG_LIGHT_BLUE, self.COLOR_RESET),
                logging.WARNING: log_format.format(self.BG_YELLOW + self.FG_WHITE, self.COLOR_RESET),
                logging.ERROR: log_format.format(self.BG_DEFAULT + self.FG_RED, self.COLOR_RESET),
                logging.CRITICAL: log_format.format(self.BG_DEFAULT + self.FG_RED, self.COLOR_RESET)
            }
        else:
            self.formats = {
                logging.DEBUG: log_format,
                logging.INFO: log_format,
                logging.WARNING: log_format,
                logging.ERROR: log_format,
                logging.CRITICAL: log_format
            }

    def format(self, record):
        log_fmt = self.formats.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class NestedLoggingGuard:
    """
    Ensures correct indentation of log file messages depending on the context
    the log message is written.
    """
    MESSAGE_OFFSET = 0
    MESSAGE_INDENT = 2

    def __init__(self, _logger, lvl=None, message=None):
        self._logger = _logger
        self._level = lvl
        self._message = message
        if lvl is not None and message is not None:
            self._logger.log(self._level, " " * NestedLoggingGuard.MESSAGE_OFFSET + self._message)

    def __enter__(self):
        assert self._level is not None
        assert self._message is not None
        NestedLoggingGuard.MESSAGE_OFFSET += NestedLoggingGuard.MESSAGE_INDENT

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self._level is not None
        assert self._message is not None
        if exc_type is None:
            result = "done"
        else:
            result = "failed"
        NestedLoggingGuard.MESSAGE_OFFSET -= NestedLoggingGuard.MESSAGE_INDENT

        def tmp1():  # this nesting needed to even number of stack frames in __enter__ and __exit__
            def tmp2():
                self._logger.log(self._level, " " * NestedLoggingGuard.MESSAGE_OFFSET +
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

    def log_system_info(self):
        self.debug(f"platform.system() = {repr(platform.system())}")
        self.debug(f"platform.release() = {platform.release()}")
        self.debug(f"platform.version() = {platform.version()}")

        self.debug(f"platform.machine() = {platform.machine()}")
        self.debug(f"platform.uname() = {platform.uname()}")
        self.debug(f"platform.mac_ver() = {platform.mac_ver()}")

        self.debug(f"sys.executable = {sys.executable}")
        self.debug(f"sys.version = {sys.version}")
        self.debug(f"os.environ = {os.environ}")


class CycleBufferHandler(logging.handlers.BufferingHandler):

    def emit(self, record):
        self.buffer.append(record)
        if len(self.buffer) > self.capacity:
            self.buffer = self.buffer[-self.capacity:]

    def show_messages(self):
        sys.stderr.write("\n".join([self.format(record) for record in self.buffer]))
        self.flush()


def install_logger(logfile_dir: str, logfile_name: str, cached_console_logging: bool) -> \
        Tuple[NestedLoggingGuard, Union[logging.StreamHandler, CycleBufferHandler]]:
    """
    Setup the logging system: One logger which logs onto the console (optionally cached),
    one that logs into a file.

    Args:
        logfile_dir (str): The full path of the directory in which the logfile
            will be created.
        logfile_name (str): The name of the logfile.
        cached_console_logging (bool): Set to True if you want to have the console
            output cached. You need to empty the buffer manually later.

    Returns:
        A two element Tuple: The frist element is the TheNestedLoggingGuard logger object
        which can be used for logging. The second element is the handler for the
        console output. It is of type logging.StreamHandler or CycleBuferHandler depending
        on the value of cached_console_logging. In case of cached logging use the show_messages
        method of the CycleBufferHandler object to write the message to stderr.
    """

    # Get the root logger
    logging.setLoggerClass(TexTextLogger)
    basic_logger = logging.getLogger('TexText')
    basic_logger.setLevel(logging.DEBUG)

    # Add the handler for the console output
    if cached_console_logging:
        log_stream_handler = CycleBufferHandler(capacity=1024)
        handler_colored = False
    else:
        log_stream_handler = logging.StreamHandler()
        handler_colored = True
    log_stream_handler.setLevel(logging.INFO)
    log_stream_handler.setFormatter(LoggingFormatter(colored_messages=handler_colored,
                                                     with_datetime=False,
                                                     with_source=False))
    basic_logger.addHandler(log_stream_handler)

    # Add the handler for file output
    try:
        os.makedirs(logfile_dir, exist_ok=True)
        # log_file_handler = logging.handlers.RotatingFileHandler(os.path.join(logfile_dir, logfile_name),
        #                                                         maxBytes=500 * 1024,  # up to 500 kB
        #                                                         backupCount=2,  # up to two log files
        #                                                         encoding="utf-8")
        log_file_handler = logging.FileHandler(os.path.join(logfile_dir, logfile_name),
                                               mode="w", encoding="utf-8")

    except OSError as error:
        msg = f"Unable to create logfile. Error message: {error.strerror}"
        basic_logger.error(msg)
    else:
        log_file_handler.setLevel(logging.DEBUG)
        log_file_handler.setFormatter(LoggingFormatter(colored_messages=False, with_datetime=True, with_source=True))
        basic_logger.addHandler(log_file_handler)

    # Enable nesting of log messages
    return NestedLoggingGuard(basic_logger), log_stream_handler


logger, log_console_handler = install_logger(logfile_dir=str(os.path.join(system_env.textext_logfile_path)),
                                             logfile_name="textext2.log",
                                             cached_console_logging=True)
