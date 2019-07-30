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
from servicemanager import ServiceManager

import transform_utils as tu

import response_builder

from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def delete(event, context):
    """ Validates that the service belongs to the authenticated user
    and deletes the service.

    Args:
        name (string): Name of the service (CloudFormation Stack)
    Basic Usage:
    Returns:
        List: List of JSON objects containing service information
    """
    sm = ServiceManager(event)

    data = {}
    data['services'] = []

    try:
        sm.delete_stack()
    except NoSuchObject:
        return response_builder.error(400, 'No such service.')
    except PermissionDenied:
        return response_builder.error(401, 'Permission denied.')
    except Exception as ex:
        return response_builder.error(500, 'Unknown Error: {}'.format(ex))
    else:
        return response_builder.success('Successfully deleted the service.')
