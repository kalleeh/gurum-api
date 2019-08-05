"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from logger import configure_logger
from app_manager import AppManager

import transform_utils as tu

import response_builder

from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def get(event, _context):
    """ Returns the apps belonging to the authenticated user.
    It uses filter_stacks() to filter the CloudFormation stacks with type 'app'
    and owner belonging to the same Cognito group as the user is logged in as.

    Args:
        None:
    Basic Usage:
        >>> GET /apps
    Returns:
        Dict: Dict with list of JSON object containing app information
        {
            'apps'
            [
                {
                    'name': 'mystack',
                    'description': 'status'
                    ...
                }
            ]
        }
    """
    app = AppManager(event)

    data = {}
    data['apps'] = []

    keys = ['StackName', 'Parameters', 'CreationTime', 'LastUpdatedTime']

    try:
        stacks = app.list_stacks(keys)
    except Exception as ex:
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        for stack in stacks:
            name = tu.remove_prefix(stack['StackName'])
            params = tu.kv_to_dict(stack['Parameters'], 'ParameterKey', 'ParameterValue')
            data['apps'].append(
                {
                    'name': name,
                    'created_at': stack['CreationTime'],
                    'updated_at': stack['LastUpdatedTime'],
                    'tasks': params['DesiredCount']
                })

        return response_builder.success(data)
