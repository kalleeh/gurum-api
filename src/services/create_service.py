import json

from exceptions import AlreadyExists
from aws_xray_sdk.core import patch_all
from logger import configure_logger

import response_builder
import transform_utils

from managers.service_manager import ServiceManager

patch_all()

LOGGER = configure_logger(__name__)


def post(event, _context):
    """ Creates a new service belonging to the authenticated user.
    Pre-requisites: User must create a new OAuth token on his GitHub-account
    that allows repo access to the requested repository for the service
    to be able to pull source.
    """
    sm = ServiceManager(event)

    data = {}
    data['services'] = []

    payload = json.loads(event['body-json'][0])
    LOGGER.debug(
        'Received payload: %s',
        payload)

    # Configure default values if not present

    name = transform_utils.add_prefix(payload['name'])

    if 'product_flavor' not in payload:
        payload['product_flavor'] = 's3'
    if 'version' not in payload:
        payload['version'] = 'latest'

    try:
        resp = sm.create_stack(
            name,
            payload
        )
    except AlreadyExists:
        return response_builder.error('A service with that name already exists.', 409)
    except Exception as ex:
        LOGGER.debug(
            'Exception: %s',
            ex,
            exc_info=True)
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        data['services'] = resp

        return response_builder.success(data)
