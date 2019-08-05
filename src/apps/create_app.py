"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from exceptions import AlreadyExists
import json

from logger import configure_logger
from appmanager import AppManager

import transform_utils as tu

import response_builder

from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def post(event, context):
    """ Creates a new app belonging to the authenticated user.

    Args:
        None:
    Basic Usage:
        >>> POST /apps
        >>> Payload Example:
            {
                "name": "my-app",
                "health_check_path": "/",   [Optional]
                "tasks": "1",               [Optional]
                "image": "nginx:latest",    [Optional]
                "subtype": "shared-lb",     [Optional]
                "version": "latest"         [Optional]
            }
    Returns:
        List: List of JSON objects containing app information
    """
    app = AppManager(event)

    data = {}
    data['apps'] = []

    payload = json.loads(event['body-json'][0])
    LOGGER.debug(
        'Received payload: %s',
        payload)

    # Configure default values if not present

    name = tu.add_prefix(payload['name'])

    if 'subtype' not in payload:
        payload['subtype'] = 'shared-lb'
    if 'version' not in payload:
        payload['version'] = 'latest'

    try:
        resp = app.create_stack(
            name,
            payload
        )
    except AlreadyExists:
        return response_builder.error('An app with that name already exists.', 400)
    except Exception as ex:
        LOGGER.debug(
            'Exception: %s',
            ex,
            exc_info=True)
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        data['apps'] = resp

        return response_builder.success(data)
