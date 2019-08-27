"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""


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


class ParameterNotFoundError(Error):
    """
    Parameter not found in Parameter Store
    """
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
