import boto3
import json
import logging
from botocore.exceptions import ValidationError, ClientError

import libs.util as util

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

# Create CloudFormation Client
CFN_CLIENT = boto3.client('cloudformation', region_name=util.PLATFORM_REGION)

"""
Events Resource Definition

    URI: /events/{name}
    Methods:
        GET - Get latest events for stack name
"""


def get(event, context):
    """ Fetches the 10 latest CloudFormation Events for App

    Args:
        name (string): Name of the app (CloudFormation Stack)
    Basic Usage:
        >>> GET /events/my-app
    Returns:
        List: List of JSON object containing events information
    """
    data = []

    name = util.addprefix(event['pathParameters']['name'])
    LOGGER.debug('Getting events for stack {}:'.format(name))

    # Get the user id for the request
    groups = event['requestContext']['authorizer']['claims']['cognito:groups']
    
    # Validate authorization
    if not util.validate_auth(name, groups):
        raise Exception('You do not have permission to modify this resource.')
    
    try:
        # List Events for Stack
        paginator = CFN_CLIENT.get_paginator('describe_stack_events')
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

    return util.respond(None, data)