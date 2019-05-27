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

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def delete(event, context):
    """ Validates that the app belongs to the authenticated user
    and deletes the app.

    Args:
        name (string): Name of the app (CloudFormation Stack)
    Basic Usage:
        >>> DELETE /apps/my-app
    Returns:
        List: List of JSON objects containing app information
    """
    app = AppManager(event)

    try:
        app.delete_stack()
    except NoSuchObject:
        return tu.respond(400, 'No such application.')
    except PermissionDenied:
        return tu.respond(401, 'Permission denied.')
    except Exception as ex:
        print(ex.args)
        return tu.respond(500, 'Unknown Error: {}'.format(ex))
    else:
        return tu.respond(None, 'Successfully deleted the app.')