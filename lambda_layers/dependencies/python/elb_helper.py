"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

import boto3

from logger import configure_logger

import config

from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def get_next_rule_priority(listener_arn):
    """ Returns the next rule priority number for a given ALB Listener Arn

    Args:
        listener_arn (string): String of the ARN to the ALB Listener
    Basic Usage:
        >>> resp = iterate_rule_priority(listener_arn)
    Returns:
        Number: Number of the next available rule priority number
        Default: 1
    """
    client = boto3.client('elbv2', region_name=config.PLATFORM_REGION)
    rules = {}

    try:
        rules = client.describe_rules(
            ListenerArn=listener_arn,
        )['Rules']
    except Exception as ex:
        LOGGER.exception(ex)
        raise

    rules = [rule for rule in rules if rule['Priority'].isdigit()]

    if not rules:
        return 1

    sorted_rules = sorted(rules, key=lambda x: int(x['Priority']), reverse=True)
    priority = int(sorted_rules[0]['Priority'])+1

    return priority
