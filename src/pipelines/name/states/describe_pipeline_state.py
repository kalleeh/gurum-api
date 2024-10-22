from aws_xray_sdk.core import patch_all
from logger import configure_logger

import response_builder
import transform_utils

from managers.pipeline_manager import PipelineManager

patch_all()

LOGGER = configure_logger(__name__)


def get(event, _context):
    """ Describes detailed information about a pipeline
    """
    pm = PipelineManager(event)

    data = {}
    data['states'] = []

    try:
        stacks = pm.describe_stack()
    except Exception as ex:
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        stack = stacks[0]
        outputs = transform_utils.kv_to_dict(stack['Outputs'], 'OutputKey', 'OutputValue') if 'Outputs' in stack else []

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

        return response_builder.success(data)
