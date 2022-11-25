"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2022 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.
"""
# ToDo Remove this when Inkscape extension manager handles modules properly
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# pylint: disable=wrong-import-position
import traceback  # noqa
from textext.base import TexText, Cache, \
    EXIT_CODE_OK, EXIT_CODE_UNEXPECTED_ERROR, EXIT_CODE_EXPECTED_ERROR, \
    logger, log_console_handler, system_env  # noqa
from textext.errors import TexTextInternalError, TexTextFatalError  # noqa


if __name__ == "__main__":
    # ToDo: Re-think this exception ladder
    try:
        effect = TexText()
        effect.run()
        effect.cache["previous_exit_code"] = EXIT_CODE_OK
        effect.cache.save()

    except TexTextInternalError as e:
        # TexTextInternalError should never be raised.
        # It's TexText logic error and should be reported.
        logger.error(str(e))
        logger.error(traceback.format_exc())
        logger.info("TexText finished with error, please run extension again")
        logger.info("If problem persists, please file a bug "
                    "https://github.com/textext/textext/issues/new?template=bug_report.md")
        log_console_handler.show_messages()
        # noinspection PyBroadException
        try:
            cache = Cache(directory=system_env.textext_config_path)
            cache["previous_exit_code"] = EXIT_CODE_UNEXPECTED_ERROR
            cache.save()
        except Exception as _:  # pylint: disable=broad-except
            pass
        sys.exit(EXIT_CODE_UNEXPECTED_ERROR)  # TexText internal error

    except TexTextFatalError as e:
        logger.error(str(e))
        log_console_handler.show_messages()
        # noinspection PyBroadException
        try:
            cache = Cache(directory=system_env.textext_config_path)
            cache["previous_exit_code"] = EXIT_CODE_EXPECTED_ERROR
            cache.save()
        except Exception as _:  # pylint: disable=broad-except
            pass
        sys.exit(EXIT_CODE_EXPECTED_ERROR)  # Bad setup

    except Exception as e:  # pylint: disable=broad-except
        # All errors should be handled by above clause.
        # If any propagates here it's TexText logic error and should be reported.
        logger.error(str(e))
        logger.error(traceback.format_exc())
        logger.info("TexText finished with error, please run extension again, "
                    "so we can collect additional debug information.")
        logger.info("If problem persists, please open a bug report at "
                    "https://github.com/textext/textext/issues/new?template=bug_report.md")
        log_console_handler.show_messages()
        # noinspection PyBroadException
        try:
            cache = Cache(directory=system_env.textext_config_path)
            cache["previous_exit_code"] = EXIT_CODE_UNEXPECTED_ERROR
            cache.save()
        except Exception as _:  # pylint: disable=broad-except
            pass
        sys.exit(EXIT_CODE_UNEXPECTED_ERROR)  # TexText internal error
