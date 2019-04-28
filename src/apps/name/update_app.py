"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

import json

from logger import configure_logger
from appmanager import AppManager

import transform_utils as tu

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def patch(event, context):
    """ Validates that the app belongs to the authenticated user
    and updates the configuration.

    Args:
        name (string): Name of the app (CloudFormation Stack)
    Basic Usage:
        >>> PATCH /apps/-my-app
        >>> Payload Example:
            [{
                "tasks": "2",
                "health_check_path": "/health",
                "image": "nginx:latest"     [Optional]
                "upgrade_version": "False"  [Optional] Forces platform version upgrade
            }]
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
    if not 'subtype' in payload:
        payload['subtype'] = 'shared-lb'
    if not 'version' in payload:
        payload['version'] = 'latest'
    
    resp = app.update_stack(
        payload
    )

    data['apps'] = resp

    return tu.respond(None, data)