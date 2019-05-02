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
    """ Describes detailed information about a pipeline

    Args:
        name (string): Name of the pipeline (CloudFormation Stack)
    Basic Usage:
        >>> GET /pipelines/my-pipeline/states
    Returns:
        Dict: Dict with list of JSON object containing pipeline information
        {
            'pipelines'
            [
                {
                    'name': 'mystack',
                    'description': 'status'
                    ...
                }
            ]
        }
    """
    pm = PipelineManager(event)

    data = {}
    data['states'] = []
    
    stacks = pm.describe_stack()
    stack = stacks[0]
    outputs = tu.kv_to_dict(stack['Outputs'], 'OutputKey', 'OutputValue') if 'Outputs' in stack else []

    states = pm.get_pipeline_state(outputs['PipelineName'])
    
    for state in states:
        keys = ['actionName', 'latestExecution']
        actions = pm.filter_keys(state['actionStates'], keys)
        
        for action in actions:
            latest_execution = action['latestExecution']
            status = latest_execution['status'] if 'status' in latest_execution else 'N/A'
            percent_complete = latest_execution['percentComplete'] if 'percentComplete' in latest_execution else 'N/A'
            last_status_change = latest_execution['lastStatusChange'] if 'lastStatusChange' in latest_execution else 'N/A'
            error_details = latest_execution['errorDetails'] if 'errorDetails' in latest_execution else 'N/A'

            data['states'].append(
                {
                    'stage_name': state['stageName'],
                    'name': action['actionName'],
                    'status': status,
                    'percent_complete': percent_complete,
                    'last_status_change': last_status_change,
                    'error_details': error_details
                }
            )
    
    return tu.respond(None, data)