import json

from exceptions import NoSuchObject, PermissionDenied, UnknownParameter
from aws_xray_sdk.core import patch_all
from logger import configure_logger

import response_builder

from managers.app_manager import AppManager

patch_all()

LOGGER = configure_logger(__name__)


def patch(event, _context):
    """ Validates that the app belongs to the authenticated user
    and updates the configuration.
    """
    app = AppManager(event)

    data = {}
    data['apps'] = []

    payload = json.loads(event['body-json'][0])

    # Configure default values if not present
    if 'product_flavor' not in payload:
        payload['product_flavor'] = 'shared-lb'
    if 'version' not in payload:
        payload['version'] = 'latest'

    try:
        resp = app.update_stack(
            payload
        )
    except NoSuchObject:
        return response_builder.error('No such application.', 400)
    except PermissionDenied:
        return response_builder.error('Permission denied.', 401)
    except UnknownParameter as ex:
        return response_builder.error('{}'.format(ex), 400)
    except Exception as ex:
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        data['apps'] = resp

        return response_builder.success(data)
