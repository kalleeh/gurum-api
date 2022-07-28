from aws_xray_sdk.core import patch_all
from logger import configure_logger

import transform_utils
import response_builder

from managers.app_manager import AppManager

patch_all()

LOGGER = configure_logger(__name__)


def get(event, _context):
    """ Returns the apps belonging to the authenticated user.
    """
    LOGGER.debug('Instantiating AppManager.')
    app = AppManager(event)

    data = {}
    data['apps'] = []

    keys = ['StackName', 'Parameters', 'CreationTime', 'LastUpdatedTime']

    try:
        LOGGER.debug('Calling list_stacks.')
        stacks = app.list_stacks(keys)
    except Exception as ex:
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        LOGGER.debug('Looping through stacks and building response.')
        for stack in stacks:
            name = transform_utils.remove_prefix(stack['StackName'])
            params = transform_utils.kv_to_dict(stack['Parameters'], 'ParameterKey', 'ParameterValue')
            data['apps'].append(
                {
                    'name': name,
                    'created_at': stack['CreationTime'],
                    'updated_at': stack['LastUpdatedTime'],
                    'tasks': params['DesiredCount']
                })

        return response_builder.success(data)
