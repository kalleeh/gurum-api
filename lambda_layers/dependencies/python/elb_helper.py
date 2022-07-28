import random
import boto3

from logger import configure_logger

import platform_config

LOGGER = configure_logger(__name__)


def get_random_rule_priority(listener_arn):
    """ Returns a random available rule priority number for a given ALB Listener Arn
    """
    client = boto3.client('elbv2', region_name=platform_config.PLATFORM_REGION)
    rules = {}

    try:
        rules = client.describe_rules(
            ListenerArn=listener_arn,
        )['Rules']
    except Exception as ex:
        LOGGER.exception(ex)
        raise

    priorities = [int(rule['Priority']) for rule in rules if rule['Priority'].isdigit()]

    if not priorities:
        return 1

    allocated_set = set(priorities)
    possible_range_set = set(range(50000))
    available_range_set = possible_range_set.difference(allocated_set)
    random_rule_priority = random.sample(available_range_set, 1)[0]

    return random_rule_priority
