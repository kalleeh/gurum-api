"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from logger import configure_logger
from servicemanager import ServiceManager

import transform_utils as tu

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def get(event, context):
    """ Describes detailed information about a service

    Args:
        name (string): Name of the service (CloudFormation Stack)
    Basic Usage:
        >>> GET /services/my-service
    Returns:
        List: List of JSON object containing service information
    """
    sm = ServiceManager(event)

    data = {}
    data['services'] = []
    
    stacks = sm.describe_stack()
    stack = stacks[0]
    
    outputs = tu.kv_to_dict(stack['Outputs'], 'OutputKey', 'OutputValue') if 'Outputs' in stack else []
    params = tu.kv_to_dict(stack['Parameters'], 'ParameterKey', 'ParameterValue')

    data['services'].append(
        {
            'name': stack['StackName'],
            'description': stack['Description'],
            'status': stack['StackStatus'],
            'outputs': outputs,
            'params': params
        })
    
    return tu.respond(None, data)