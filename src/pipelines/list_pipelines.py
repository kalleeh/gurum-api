from aws_xray_sdk.core import patch_all
from logger import configure_logger

import transform_utils
import response_builder

from managers.pipeline_manager import PipelineManager

patch_all()

LOGGER = configure_logger(__name__)


def get(event, _context):
    """ Returns the pipelines belonging to the authenticated user.
    It uses filter_stacks() to filter the CloudFormation stacks with type
    'pipeline' and owner belonging to the same Cognito group as the user
    is logged in as.
    """
    pm = PipelineManager(event)

    data = {}
    data['pipelines'] = []

    keys = ['StackName', 'Parameters', 'CreationTime', 'LastUpdatedTime']

    try:
        stacks = pm.list_stacks(keys)
    except Exception as ex:
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        for stack in stacks:
            name = transform_utils.remove_prefix(
                stack['StackName'])
            params = transform_utils.kv_to_dict(
                stack['Parameters'],
                'ParameterKey',
                'ParameterValue')
            data['pipelines'].append(
                {
                    'name': transform_utils.remove_prefix(name),
                    'created_at': stack['CreationTime'],
                    'updated_at': stack['LastUpdatedTime'],
                    'app_dev': transform_utils.remove_prefix(params['ServiceDev']),
                    'app_test': transform_utils.remove_prefix(params['ServiceTest']),
                    'app': transform_utils.remove_prefix(params['ServiceProd'])
                })

        return response_builder.success(data)
