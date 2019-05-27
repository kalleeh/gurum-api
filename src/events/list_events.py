"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from logger import configure_logger
from eventmanager import EventManager

import transform_utils as tu

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def get(event, context):
    """ Fetches the 10 (default) latest CloudFormation Events for stack

    Args:
        name (string): Name of the stack (CloudFormation Stack)
    Basic Usage:
        >>> GET /events/my-stack
    Returns:
        Dict: Dict with list of JSON objects containing event information
        {
            'events'
            [
                {
                    'name': 'mystack',
                    'timestamp': '123456'
                    ...
                }
            ]
        }
    """
    em = EventManager(event)
    data = {}
    data['events'] = []
    
    for event in em.get_stack_events():
        if not 'ResourceStatusReason' in event:
            event['ResourceStatusReason'] = ""
        data['events'].append(
            {
                'name': event['StackName'],
                'timestamp': event['Timestamp'],
                'resource': event['LogicalResourceId'],
                'status': event['ResourceStatus'],
                'message': event['ResourceStatusReason']
            })
    
    return tu.respond(None, data)