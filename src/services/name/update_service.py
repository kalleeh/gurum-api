"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from exceptions import NoSuchObject, PermissionDenied

import json

from logger import configure_logger
from servicemanager import ServiceManager

import transform_utils as tu

from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def patch(event, context):
    """ Updates the service belonging to the authenticated user.

    Args:
        name (string): Name of the service (CloudFormation Stack)
    Basic Usage:
        >>> POST /service
        >>> Payload Example:
            [{
                "service_name": "my-service",
                "service_bindings": "myapp1",
                "upgrade_version": "False"  [Optional] Forces platform version upgrade
            }]
    Returns:
        List: List of JSON objects containing service information
    """
    sm = ServiceManager(event)

    data = {}
    data['services'] = []

    payload = json.loads(event['body-json'][0])

    if 'subtype' not in payload:
        payload['subtype'] = 's3'
    if 'version' not in payload:
        payload['version'] = 'latest'

    bindings = payload['service_bindings'].split(',')
    for binding in bindings:
        if not sm.has_permissions(binding):
            return tu.respond(400, '{} doesn\'t exist or not enough permissions.'.format(binding))

    try:
        resp = sm.update_stack(
            payload
        )
    except NoSuchObject:
        return tu.respond(400, 'No such service.')
    except PermissionDenied:
        return tu.respond(401, 'Permission denied.')
    except Exception as ex:
        return tu.respond(500, 'Unknown Error: {}'.format(ex))
    else:
        data['services'] = resp

        return tu.respond(None, data)
