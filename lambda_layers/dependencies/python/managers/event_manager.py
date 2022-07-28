from aws_xray_sdk.core import patch_all
from logger import configure_logger
from paginator import paginator

import transform_utils

from managers.stack_manager import StackManager

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
        name = transform_utils.add_prefix(self._params['name'])
        LOGGER.debug(
            'Getting events for stack %s:',
            name)
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
