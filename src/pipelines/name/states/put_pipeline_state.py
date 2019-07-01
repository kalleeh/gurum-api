"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""
import json

from logger import configure_logger
from pipelinemanager import PipelineManager

import transform_utils as tu

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def put(event, context):
    """ Send an approval result to the approval stage of a pipeline.
    
    Args:
        summary (string): Short description of the reason for approval result.
    Basic Usage:
        >>> PUT /pipelines/my-pipeline/states
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

    payload = json.loads(event['body-json'][0])
    
    try:
        stacks = pm.describe_stack()
    except Exception as ex:
        return tu.respond(500, 'Unknown Error: {}'.format(ex))
    else:
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

                if state['stageName'] == 'ApprovalStage' and action['actionName'] == 'Approval':
                    token = latest_execution['token']
                    summary = payload['summary']
                    status = payload['status']

                    approval_result = pm.put_approval_result(
                        pipeline_name = outputs['PipelineName'],
                        stage_name = state['stageName'],
                        action_name = action['actionName'],
                        summary = summary,
                        status = status,
                        token = token
                        )
                    
                    data['states'].append(
                        {
                            'stage_name': state['stageName'],
                            'name': action['actionName'],
                            'status': status,
                            'percent_complete': percent_complete,
                            'last_status_change': last_status_change,
                            'error_details': approval_result
                        }
                    )
        
        return tu.respond(None, data)