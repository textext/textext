"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2021 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.
"""

# ToDo Remove this when Inkscape extension manager handles modules properly
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from textext.base import *
import traceback

if __name__ == "__main__":
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
        user_log_channel.show_messages()
        try:
            cache = Cache()
            cache["previous_exit_code"] = EXIT_CODE_UNEXPECTED_ERROR
            cache.save()
        except:
            pass
        exit(EXIT_CODE_UNEXPECTED_ERROR)  # TexText internal error
    except TexTextFatalError as e:
        logger.error(str(e))
        user_log_channel.show_messages()
        try:
            cache = Cache()
            cache["previous_exit_code"] = EXIT_CODE_EXPECTED_ERROR
            cache.save()
        except:
            pass
        exit(EXIT_CODE_EXPECTED_ERROR)  # Bad setup
    except Exception as e:
        # All errors should be handled by above clause.
        # If any propagates here it's TexText logic error and should be reported.
        logger.error(str(e))
        logger.error(traceback.format_exc())
        logger.info("TexText finished with error, please run extension again")
        logger.info("If problem persists, please file a bug "
                    "https://github.com/textext/textext/issues/new?template=bug_report.md")
        user_log_channel.show_messages()
        try:
            cache = Cache()
            cache["previous_exit_code"] = EXIT_CODE_UNEXPECTED_ERROR
            cache.save()
        except:
            pass
        exit(EXIT_CODE_UNEXPECTED_ERROR)  # TexText internal error
