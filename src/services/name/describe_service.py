from exceptions import NoSuchObject, PermissionDenied
from aws_xray_sdk.core import patch_all
from logger import configure_logger

import response_builder
import transform_utils

from managers.service_manager import ServiceManager

patch_all()

LOGGER = configure_logger(__name__)


def get(event, _context):
    """ Describes detailed information about a service
    """
    sm = ServiceManager(event)

    data = {}
    data['services'] = []

    try:
        stacks = sm.describe_stack()
    except NoSuchObject:
        return response_builder.error('No such service.', 400)
    except PermissionDenied:
        return response_builder.error('Permission denied.', 401)
    except Exception as ex:
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        stack = stacks[0]

        outputs = transform_utils.kv_to_dict(stack['Outputs'], 'OutputKey', 'OutputValue') if 'Outputs' in stack else []

        data['services'].append(
            {
                'name': stack['StackName'],
                'description': stack['Description'],
                'status': stack['StackStatus'],
                'outputs': outputs
            })

        return response_builder.success(data)
