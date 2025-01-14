# Paginator used with certain boto3 calls when pagination is required


def paginator(method, **kwargs):
    client = method.__self__
    iterator = client.get_paginator(method.__name__)
    for page in iterator.paginate(**kwargs).result_key_iters():
        for result in page:
            yield result
