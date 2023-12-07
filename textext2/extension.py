"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2023 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.
"""
import os
import logging
from utils.log_util import install_logger
from utils.environment import system_env
from utils.settings import Settings, Cache

# Open logger before accessing Inkscape modules, so we can catch properly any errors thrown by them
logger, log_console_handler = install_logger(logfile_dir=os.path.join(system_env.textext_logfile_path),
                                            logfile_name="textext2.log", cached_console_logging=True)

# import warnings
# warnings.filterwarnings("ignore")
import inkex  # noqa # pylint: disable=wrong-import-position,wrong-import-order,import-error

# For addressing the SVG elements
TEXTEXT_NS = "http://www.iki.fi/pav/software/textext/"
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ID_PREFIX = "textext-"
NSS = {
    "textext": TEXTEXT_NS,
    "svg": SVG_NS,
    "xlink": XLINK_NS,
}


class TexText(inkex.EffectExtension):
    # The exit codes
    EXIT_CODE_OK = 0
    EXIT_CODE_EXPECTED_ERROR = 1
    EXIT_CODE_UNEXPECTED_ERROR = 60

    DEFAULT_TEXCMD = "pdflatex"
    DEFAULT_PREAMBLE = "default_packages.tex"
    DEFAULT_ALIGNMENT = "middle center"

    def __init__(self):

        # Before we do anything we set up the settings, the Cache system and
        # the loggers. By this we ensure that we catch all errors occurring
        # while calling the ctor of the base class.
        self.config = Settings(directory=system_env.textext_config_path)
        self.cache = Cache(directory=system_env.textext_config_path)
        self._setup_logging()

        super().__init__()

        self.arg_parser.add_argument(
            "--text",
            type=str,
            default=None)

        self.arg_parser.add_argument(
            "--preamble-file",
            type=str,
            default=self.DEFAULT_PREAMBLE
        )

        self.arg_parser.add_argument(
            "--scale-factor",
            type=float,
            default=1.0
        )

        self.arg_parser.add_argument(
            "--font-size-pt",
            type=int,
            default=10
        )

        self.arg_parser.add_argument(
            "--alignment",
            type=str,
            default=self.DEFAULT_ALIGNMENT
        )

        self.arg_parser.add_argument(
            "--tex_command",
            type=str,
            default=self.DEFAULT_TEXCMD
        )

    def effect(self):
        pass

    def _setup_logging(self):
        previous_exit_code = self.cache.get("previous_exit_code", None)

        if previous_exit_code is None:
            logging.disable(logging.NOTSET)
            logger.debug("First run of TexText. Enforcing DEBUG mode.")
        elif previous_exit_code == self.EXIT_CODE_UNEXPECTED_ERROR:
            logging.disable(logging.NOTSET)
            logger.debug(f"Enforcing DEBUG mode due to unexpected error in previous run.")
        elif previous_exit_code == self.EXIT_CODE_EXPECTED_ERROR:
            logging.disable(logging.DEBUG)
            logger.debug(f"Extended logging due to expected error in previous run")
        else:
            logging.disable(logging.CRITICAL)  # No logging in case everything went well in previous run
