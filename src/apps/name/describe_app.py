"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from exceptions import NoSuchObject, PermissionDenied

from logger import configure_logger
from appmanager import AppManager

import transform_utils as tu

from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def get(event):
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
        return tu.respond(400, 'No such application.')
    except PermissionDenied:
        return tu.respond(401, 'Permission denied.')
    except Exception as ex:
        return tu.respond(500, 'Unknown Error: {}'.format(ex))
    else:
        stack = stacks[0]

        outputs = tu.kv_to_dict(stack['Outputs'], 'OutputKey', 'OutputValue') if 'Outputs' in stack else []
        tags = tu.kv_to_dict(stack['Tags'], 'Key', 'Value')

        data['apps'].append(
            {
                'name': stack['StackName'],
                'description': stack['Description'],
                'status': stack['StackStatus'],
                'outputs': outputs,
                'tags': tags
            })

        return tu.respond(None, data)
