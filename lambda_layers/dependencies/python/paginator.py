"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

"""
Paginator used with certain boto3 calls
when pagination is required
"""


def paginator(method, **kwargs):
    client = method.__self__
    iterator = client.get_paginator(method.__name__)
    for page in iterator.paginate(**kwargs).result_key_iters():
        for result in page:
            yield result
