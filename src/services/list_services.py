"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from aws_xray_sdk.core import patch_all
from logger import configure_logger

import response_builder
import transform_utils

from service_manager import ServiceManager

patch_all()

LOGGER = configure_logger(__name__)


def get(event, _context):
    """ Returns the services belonging to the authenticated user.
    It uses filter_stacks() to filter the CloudFormation stacks with type 'service'
    and owner belonging to the same Cognito group as the user is logged in as.

    Args:
        None:
    Basic Usage:
        >>> GET /services
    Returns:
        List: List of JSON objects containing service information
    """
    sm = ServiceManager(event)

    data = {}
    data['services'] = []

    keys = ['StackName', 'Parameters', 'CreationTime', 'LastUpdatedTime']

    try:
        stacks = sm.list_stacks(keys)
    except Exception as ex:
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        for stack in stacks:
            name = transform_utils.remove_prefix(stack['StackName'])
            params = transform_utils.kv_to_dict(stack['Parameters'], 'ParameterKey', 'ParameterValue')
            data['services'].append(
                {
                    'name': name,
                    'created_at': stack['CreationTime'],
                    'updated_at': stack['LastUpdatedTime'],
                    'service_bindings': params['ServiceBindings']
                })

        return response_builder.success(data)
