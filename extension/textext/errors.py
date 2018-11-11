
class TexTextError(RuntimeError):
    """ Basic class of all TexText errors"""
    pass


class TexTextNonFatalError(TexTextError):
    """ TexText can continue execution properly """
    pass


class TexTextCommandError(TexTextError):
    pass


class TexTextCommandNotFound(TexTextCommandError):
    pass


class TexTextCommandFailed(TexTextCommandError):
    pass


class TexTextConversionError(TexTextNonFatalError):
    pass


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

