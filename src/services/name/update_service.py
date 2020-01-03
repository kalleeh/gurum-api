"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

import json

from exceptions import NoSuchObject, PermissionDenied, UnknownParameter
from aws_xray_sdk.core import patch_all
from logger import configure_logger

import response_builder

from managers.service_manager import ServiceManager

patch_all()

LOGGER = configure_logger(__name__)


def patch(event, _context):
    """ Updates the service belonging to the authenticated user.
    """
    sm = ServiceManager(event)

    data = {}
    data['services'] = []

    payload = json.loads(event['body-json'][0])

    if 'version' not in payload:
        payload['version'] = 'latest'

    validate_permissions(sm, payload)

    try:
        resp = sm.update_stack(
            payload
        )
    except NoSuchObject:
        return response_builder.error('No such service.', 400)
    except PermissionDenied:
        return response_builder.error('Permission denied.', 401)
    except UnknownParameter as ex:
        return response_builder.error('{}'.format(ex), 400)
    except Exception as ex:
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        data['services'] = resp

        return response_builder.success(data)

def validate_permissions(sm, payload):
    try:
        bindings = payload['ServiceBindings'].split(',')
        for binding in bindings:
            if not sm.has_permissions(binding):
                return response_builder.error('{} doesn\'t exist or not enough permissions.'.format(binding), 400)
    except KeyError:
        return response_builder.error('ServiceBindings not provided in payload.', 400)
    else:
        return None
