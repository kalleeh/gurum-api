"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

"""Template Generator module
"""

from logger import configure_logger

LOGGER = configure_logger(__name__)


def generate_template_url(region, bucket, stack_type, payload):
    """Generates a template URL to pass to CloudFormation based on input
    parameters for type, region, version etc.
    """

    if stack_type == 'app':
        prefix_path = 'cfn/apps'
    elif stack_type == 'pipeline':
        prefix_path = 'cfn/pipelines'
    elif stack_type == 'service':
        prefix_path = 'cfn/services'

    template_url = 'https://s3-{}.amazonaws.com/{}/{}/{}-{}-{}.yaml'.format(
        region,
        bucket,
        prefix_path,
        stack_type,
        payload['subtype'],
        payload['version']
    )
    
    return template_url