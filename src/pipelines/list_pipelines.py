"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from logger import configure_logger
from pipelinemanager import PipelineManager

import transform_utils as tu

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def get(event, context):
    """ Returns the pipelines belonging to the authenticated user.
    It uses filter_stacks() to filter the CloudFormation stacks with type 'pipeline'
    and owner belonging to the same Cognito group as the user is logged in as.

    Args:
        None:
    Basic Usage:
        >>> GET /pipelines
    Returns:
        List: List of JSON objects containing app information
    """
    pm = PipelineManager(event)

    data = {}
    data['pipelines'] = []
    
    keys = ['StackName', 'Parameters', 'CreationTime', 'LastUpdatedTime']

    try:
        stacks = pm.list_stacks(keys)
    except Exception as ex:
        return tu.respond(500, 'Unknown Error: {}'.format(ex))
    else:
        for stack in stacks:
            name = tu.remove_prefix(stack['StackName'])
            params = tu.kv_to_dict(stack['Parameters'], 'ParameterKey', 'ParameterValue')
            data['pipelines'].append(
                {
                    'name': name,
                    'created_at': stack['CreationTime'],
                    'updated_at': stack['LastUpdatedTime'],
                    'app_dev': params['ServiceDev'],
                    'app_test': params['ServiceTest'],
                    'app': params['ServiceProd']
                })

        return tu.respond(None, data)