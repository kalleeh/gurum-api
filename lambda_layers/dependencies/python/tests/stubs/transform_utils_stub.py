# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Stubs for testing transform_utils.py
"""

compact_tags = {
    'MyTagKey': 'MyTagValue',
    'TagKeyName': 'TagKeyValue'
}

expanded_tags = [
    {
        'Key': 'MyTagKey',
        'Value': 'MyTagValue'
    },
    {
        'Key': 'TagKeyName',
        'Value': 'TagKeyValue'
    }
]
