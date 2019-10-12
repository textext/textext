
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

