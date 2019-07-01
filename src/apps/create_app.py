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

from aws_xray_sdk.core import xray_recorder
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
                "tasks": "1",
                "health_check_path": "/health",
                "image": "nginx:latest" [Optional]
            }
    Returns:
        List: List of JSON objects containing app information
    """
    app = AppManager(event)

    data = {}
    data['apps'] = []

    payload = json.loads(event['body-json'][0])

    """
    Configure default values if not present
    """
    name = tu.add_prefix(payload['name'])

    if not 'subtype' in payload:
        payload['subtype'] = 'shared-lb'
    if not 'version' in payload:
        payload['version'] = 'latest'
    
    try:
        resp = app.create_stack(
            name,
            payload
        )
    except AlreadyExists:
        return tu.respond(400, 'An app with that name already exists.')
    except Exception as ex:
        return tu.respond(500, 'Unknown Error: {}'.format(ex))
    else:
        data['apps'] = resp

        return tu.respond(None, data)