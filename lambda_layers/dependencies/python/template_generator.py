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


def generate_template_url(stack_type, payload):
    """Generates a template URL to pass to CloudFormation based on input
    parameters for type, region, version etc.
    """
    LOGGER.debug('Generating template URL.')

    if stack_type == 'app':
        prefix_path = 'apps'
    elif stack_type == 'pipeline':
        prefix_path = 'pipelines'
    elif stack_type == 'service':
        prefix_path = 'services'

    template_url = 'https://s3.amazonaws.com/{}/{}/{}-{}-{}.yaml'.format(
        platform_config.PLATFORM_BUCKET,
        prefix_path,
        stack_type,
        payload['subtype'],
        payload['version']
    )

    LOGGER.debug(
        'Returning template URL: %s',
        template_url)

    return template_url
