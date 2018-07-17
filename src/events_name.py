import boto3
import json
import logging
from botocore.exceptions import ValidationError, ClientError

import libs.util as util

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create CloudFormation Client
cfn = boto3.client('cloudformation', region_name=util.PLATFORM_REGION)

"""
Events Resource Definition

    URI: /events/{name}
    Methods:
        GET - Get latest events for stack name
"""


def get(name):
    """ Fetches the 10 latest CloudFormation Events for App

    Args:
        name (string): Name of the app (CloudFormation Stack)
    Basic Usage:
        >>> GET /events/my-app
    Returns:
        List: List of JSON object containing events information
    """
    data = []

    logger.debug('Getting events for stack {}:'.format)
    
    # Validate authorization
    if not util.validate_auth(name):
        raise Exception('You do not have permission to modify this resource.')
    
    try:
        # List Events for Stack
        paginator = cfn.get_paginator('describe_stack_events')
        response_iterator = paginator.paginate(
            StackName=name,
            PaginationConfig={
                'MaxItems': 10
            }
        )

        for page in response_iterator:
            for event in page['StackEvents']:
                if not 'ResourceStatusReason' in event:
                    event['ResourceStatusReason'] = ""
                data.append(
                    {
                        'app_name': event['StackName'],
                        'timestamp': event['Timestamp'],
                        'resource': event['LogicalResourceId'],
                        'status': event['ResourceStatus'],
                        'message': event['ResourceStatusReason']
                    })
    except Exception as ex:
        logging.exception(ex)
        raise Exception('Failed to list events')

    response = json.dumps(data, default=util.datetime_serialize)

    return response