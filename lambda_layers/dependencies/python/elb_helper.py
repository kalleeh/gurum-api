"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

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
        priorities = []

    allocated_set = set(priorities)
    possible_range_set = set(range(50000))
    available_range_set = possible_range_set.difference(allocated_set)
    random_rule_priority = random.sample(available_range_set, 1)[0]

    return random_rule_priority
