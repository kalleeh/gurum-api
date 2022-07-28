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
