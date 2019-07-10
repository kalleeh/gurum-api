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

class PermissionDenied(Error):
    """Raised when an action is performed on a resource 
    the principal doesn't have permissions to."""
    pass

class LimitExceeded(Error):
    """Raised for unhandled exceptions or errors
    that should be hidden from the client"""
    pass

class InsufficientCapabilities(Error):
    """Raised for unhandled exceptions or errors
    that should be hidden from the client"""
    pass

class UnknownError(Error):
    """Raised for unhandled exceptions or errors
    that should be hidden from the client"""
    pass
