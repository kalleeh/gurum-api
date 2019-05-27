"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

import boto3
from botocore.exceptions import ValidationError, ClientError

from logger import configure_logger
from paginator import paginator
from stackmanager import StackManager

import transform_utils as tu
import template_generator as tg
import config

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


"""
Stack Event Manager
"""

class EventManager(StackManager):
    def __init__(self, event):
        self._stack_type = 'any'
        
        StackManager.__init__(
            self,
            event=event,
            stack_type=self._stack_type
        )


    def get_stack_events(self, max_items=10):
        """ Return stack events for the queried stack.

        Args:
            max_items (int): Number of events to return per page.
        Basic Usage:
            >>> get_stack_events()
        Returns:
            List: List of dicts representing AWS Stacks and information
            [
                {
                    'StackName': 'mystack',
                    'StackStatus': 'status'
                }
            ]
        """
        name = tu.add_prefix(self._params['name'])
        LOGGER.debug('Getting events for stack {}:'.format(name))
        events = []

        try:
            for event in paginator(
                    self.client.describe_stack_events,
                    StackName=name,
                    PaginationConfig={
                        'MaxItems': max_items
                    }
                ):
                events.append(event)
        except Exception as ex:
            LOGGER.exception(ex)
            return None

        return events