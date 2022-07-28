from exceptions import NoSuchObject, PermissionDenied
from aws_xray_sdk.core import patch_all
from logger import configure_logger

import response_builder

from managers.service_manager import ServiceManager

patch_all()

LOGGER = configure_logger(__name__)


def delete(event, _context):
    """ Validates that the service belongs to the authenticated user
    and deletes the service.
    """
    sm = ServiceManager(event)

    data = {}
    data['services'] = []

    try:
        sm.delete_stack()
    except NoSuchObject:
        return response_builder.error('No such service.', 400)
    except PermissionDenied:
        return response_builder.error('Permission denied.', 401)
    except Exception as ex:
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        return response_builder.success('Successfully deleted the service.')
