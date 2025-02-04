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

    # Configure default values if not present
    if 'product_flavor' not in payload:
        payload['product_flavor'] = 's3'
    if 'version' not in payload:
        payload['version'] = 'latest'

    try:
        bindings = payload['ServiceBindings'].split(',')
        for binding in bindings:
            if not sm.has_permissions(binding):
                return response_builder.error('{} doesn\'t exist or not enough permissions.'.format(binding), 400)
    except KeyError:
        return response_builder.error('ServiceBindings not provided in payload.', 400)

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
