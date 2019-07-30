"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

import json

from transform_utils import datetime_serialize

def success(data):
    return {
        'body': json.dumps(data, default=datetime_serialize),
        'statusCode': '200',
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def error(code, data):
    return {
        'body': data,
        'statusCode': code,
        'headers': {
            'Content-Type': 'application/json',
        },
    }
