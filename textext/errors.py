"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2022 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

Provides Exception classes for error handling.
"""


class TexTextError(RuntimeError):
    """ Basic class of all TexText errors"""


class TexTextNonFatalError(TexTextError):
    """ TexText can continue execution properly """


class TexTextCommandError(TexTextNonFatalError):
    """ A system command failed during execution"""


class TexTextCommandNotFound(TexTextCommandError):
    """ A system command was not found"""


class TexTextCommandFailed(TexTextCommandError):

    def __init__(self, message, return_code, stdout=None, stderr=None):
        super().__init__(message)
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr


class TexTextConversionError(TexTextCommandFailed):
    def __init__(self, message, return_code=None, stdout=None, stderr=None):
        super().__init__(message, return_code, stdout, stderr)


class TexTextFatalError(TexTextError):
    """
        TexText can't continue properly

        Primary usage is assert-like statements:
        if <condition>: raise FatalTexTextError(...)

        Example: missing *latex executable
    """


class TexTextInternalError(TexTextFatalError):
    """An error not handled properly by TexText occured"""


class BadTexInputError(TexTextNonFatalError):
    """LaTeX compilation failed (LaTeX code error)"""
