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

from managers.event_manager import EventManager

patch_all()

LOGGER = configure_logger(__name__)


def get(event, _context):
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

    for stack_event in em.get_stack_events():
        if 'ResourceStatusReason' not in stack_event:
            stack_event['ResourceStatusReason'] = ""
        data['events'].append(
            {
                'name': stack_event['StackName'],
                'timestamp': stack_event['Timestamp'],
                'resource': stack_event['LogicalResourceId'],
                'status': stack_event['ResourceStatus'],
                'message': stack_event['ResourceStatusReason']
            })

    return response_builder.success(data)
