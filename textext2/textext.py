"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2023 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.
"""
from extension import TexText  # , Cache, EXIT_CODE_UNEXPECTED_ERROR, EXIT_CODE_EXPECTED_ERROR, logger, log_console_handler, system_env  # noqa
# from textext2.errors import TexTextInternalError, TexTextFatalError  # noqa


if __name__ == "__main__":
    textext_extension = TexText()
    textext_extension.run()
    textext_extension.cache["previous_exit_code"] = TexText.EXIT_CODE_OK
    textext_extension.cache.save()
