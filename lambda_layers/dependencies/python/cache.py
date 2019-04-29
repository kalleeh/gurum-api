"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""


class Cache:
    """
    Used as a cache for calls within threads.
    A single instance of this class is passed into all threads to act
    as a cache.
    """

    def __init__(self):
        self._stash = {}

    def check(self, key):
        try:
            return self._stash[key]
        except KeyError:
            return None

    def add(self, key, value):
        self._stash[key] = value