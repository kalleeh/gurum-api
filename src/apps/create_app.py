"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

import json

from exceptions import AlreadyExists
from aws_xray_sdk.core import patch_all
from logger import configure_logger

import response_builder
import transform_utils

from managers.app_manager import AppManager

patch_all()

LOGGER = configure_logger(__name__)


def post(event, _context):
    """ Creates a new app belonging to the authenticated user.
    """
    app = AppManager(event)

    data = {}
    data['apps'] = []

    payload = json.loads(event['body-json'][0])
    LOGGER.debug(
        'Received payload: %s',
        payload)

    # Configure default values if not present

    name = transform_utils.add_prefix(payload['name'])

    if 'subtype' not in payload:
        payload['subtype'] = 'ecs-fargate'
    if 'version' not in payload:
        payload['version'] = 'latest'

    try:
        resp = app.create_stack(
            name,
            payload
        )
    except AlreadyExists:
        return response_builder.error('An app with that name already exists.', 409)
    except Exception as ex:
        LOGGER.debug(
            'Exception: %s',
            ex,
            exc_info=True)
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        data['apps'] = resp

        return response_builder.success(data)
