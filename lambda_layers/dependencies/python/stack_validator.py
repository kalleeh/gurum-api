"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from logger import configure_logger

import platform_config

LOGGER = configure_logger(__name__)

def is_part_of_platform(stack_tags):
    platform_tags = platform_config.PLATFORM_TAGS['VERSION']

    if platform_tags in stack_tags:
        LOGGER.debug('Found %s in tags', platform_tags)
        return True

    return False

def is_owned_by_group(groups, tags):
    LOGGER.debug(
        'Validating owning group %s is %s:',
        tags[platform_config.PLATFORM_TAGS['GROUPS']],
        groups)

    return tags[platform_config.PLATFORM_TAGS['GROUPS']] == groups
