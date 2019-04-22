"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from logger import configure_logger
from stackmanager import StackManager

import transform_utils as tu

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def get(event, context):
    """ Describes detailed information about a pipeline

    Args:
        name (string): Name of the pipeline (CloudFormation Stack)
    Basic Usage:
        >>> GET /pipelines/my-pipeline/state
    Returns:
        List: List of JSON object containing pipeline information
    """
    data = {}

    LOGGER.debug('Describing Stack:')

    # Get the user id for the request
    name = event['params']['name']

    stack_name = tu.add_prefix(name)
    
    # List CloudFormation Stacks
    try:
        resp = sm.describe_stacks(StackName=stack_name)
    except Exception as ex:
        LOGGER.exception(ex)
        return tu.respond(500, 'Internal server error.')
    else:
        stack = resp['Stacks'][0]
        if 'Outputs' in stack:
            data['outputs'] = tu.kv_to_dict(stack['Outputs'], 'OutputKey', 'OutputValue')
        
        pipeline_name = data['outputs']['PipelineName']
        # Get Pipeline State
        pipeline_state = CPI_CLIENT.get_pipeline_state(PipelineName=pipeline_name)

        return tu.respond(None, pipeline_state)