"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2024 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.
"""
import sys
import traceback
import inkex
from extension import TexText
from settings import Cache
from utils.environment import system_env
from utils.errors import TexTextFatalError
from utils.log_util import logger, log_console_handler


if __name__ == "__main__":
    sys.path.append("../textext")
    cache = Cache(directory=system_env.textext_config_path)
    previous_exit_code = cache.get("previous_exit_code", None)

    try:
        textext_extension = TexText(previous_exit_code)
        textext_extension.run()

    except (TexTextFatalError, Exception) as e:
        # If any error propagates here it's TexText logic error and should be reported.
        logger.error(str(e))
        logger.error(traceback.format_exc())
        logger.info("TexText finished with error, please run extension again, "
                    "so we can collect additional debug information.")
        logger.info("If problem persists, please open a bug report at "
                    "https://github.com/textext/textext/issues/new?template=bug_report.md")
        log_console_handler.show_messages()
        exit_code = TexText.EXIT_CODE_UNEXPECTED_ERROR
        inkex.errormsg("Hallo")

    else:
        exit_code = TexText.EXIT_CODE_OK

    cache["previous_exit_code"] = exit_code
    cache.save()

    sys.exit(exit_code)
