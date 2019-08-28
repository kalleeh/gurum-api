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


class InvalidGurumManifest(Error):
    """Raised when invalid service manifest has been passed"""
    pass
