"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from exceptions import NoSuchObject, PermissionDenied
from aws_xray_sdk.core import patch_all
from logger import configure_logger

import response_builder
import transform_utils

from managers.app_manager import AppManager

patch_all()

LOGGER = configure_logger(__name__)


def get(event, _context):
    """ Describes detailed information about an app

    Args:
        name (string): Name of the app (CloudFormation Stack)
    Basic Usage:
        >>> GET /apps/my-app
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

    try:
        stacks = app.describe_stack()
    except NoSuchObject:
        return response_builder.error('No such application.', 400)
    except PermissionDenied:
        return response_builder.error('Permission denied.', 401)
    except Exception as ex:
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        stack = stacks[0]

        outputs = transform_utils.kv_to_dict(stack['Outputs'], 'OutputKey', 'OutputValue') if 'Outputs' in stack else []
        tags = transform_utils.kv_to_dict(stack['Tags'], 'Key', 'Value')

        data['apps'].append(
            {
                'name': stack['StackName'],
                'description': stack['Description'],
                'status': stack['StackStatus'],
                'outputs': outputs,
                'tags': tags
            })

        return response_builder.success(data)
