"""Domain errors."""


class OsLabError(Exception):
    """Base for everything this app raises on purpose."""


class AssembleError(OsLabError):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class BackendError(OsLabError):
    pass


class BadTransition(OsLabError):
    pass
