"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2021 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.

Provides Exception classes for error handling.
"""


class TexTextError(RuntimeError):
    """ Basic class of all TexText errors"""


class TexTextNonFatalError(TexTextError):
    """ TexText can continue execution properly """
    pass


class TexTextCommandError(TexTextNonFatalError):
    pass


class TexTextCommandNotFound(TexTextCommandError):
    pass


class TexTextCommandFailed(TexTextCommandError):

    def __init__(self, message, return_code, stdout=None, stderr=None):
        super(TexTextCommandFailed, self).__init__(message)
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr


class TexTextConversionError(TexTextCommandFailed):
    def __init__(self, message, return_code=None, stdout=None, stderr=None):
        super(TexTextConversionError, self).__init__(message, return_code, stdout, stderr)


class TexTextFatalError(TexTextError):
    """
        TexText can't continue properly

        Primary usage is assert-like statements:
        if <condition>: raise FatalTexTextError(...)

        Example: missing *latex executable
    """
    pass


class TexTextInternalError(TexTextFatalError):
    pass


class TexTextPreconditionError(TexTextInternalError):
    pass


class TexTextPostconditionError(TexTextInternalError):
    pass


class TexTextUnreachableBranchError(TexTextInternalError):
    pass


class BadTexInputError(TexTextNonFatalError):
    pass

