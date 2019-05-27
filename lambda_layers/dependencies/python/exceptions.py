class Error(Exception):
    """Base class for other exceptions"""
    pass

class InvalidInput(Error):
    """Raised when invalid input has been passed"""
    pass

class AlreadyExists(Error):
    """Raised when a stack already exists"""
    pass

class NoSuchObject(Error):
    """Raised when trying to perform actions on an
    object that doesn't exist."""
    pass

class UnknownError(Error):
    """Raised for unhandled exceptions or errors
    that should be hidden from the client"""
    pass