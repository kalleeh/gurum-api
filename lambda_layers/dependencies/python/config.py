"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

"""
Config information passed to each command
"""

import os
import boto3

import transform_utils as tu

from logger import configure_logger

LOGGER = configure_logger(__name__)

PLATFORM_PREFIX = os.getenv('PLATFORM_PREFIX', 'gureume-')
PLATFORM_ACCOUNT_ID = os.getenv('PLATFORM_ACCOUNT_ID', '')
PLATFORM_REGION = os.getenv('PLATFORM_REGION', 'eu-west-1')
PLATFORM_ECS_CLUSTER = os.getenv('PLATFORM_ECS_CLUSTER', PLATFORM_PREFIX + 'cluster')
PLATFORM_DEPLOYMENT_ROLE = os.getenv('PLATFORM_DEPLOYMENT_ROLE', 'deployment_role')
PLATFORM_BUCKET = os.getenv('PLATFORM_BUCKET', None)

# Tags for the platform
PLATFORM_TAGS = {}
PLATFORM_TAGS['TYPE'] = os.getenv('PLATFORM_TAGS_TYPE', PLATFORM_PREFIX + 'platform-type')
PLATFORM_TAGS['SUBTYPE'] = os.getenv('PLATFORM_TAGS_SUBTYPE', PLATFORM_PREFIX + 'platform-subtype')
PLATFORM_TAGS['VERSION'] = os.getenv('PLATFORM_TAGS_VERSION', PLATFORM_PREFIX + 'platform-version')
PLATFORM_TAGS['OWNER'] = os.getenv('PLATFORM_TAGS_OWNER', PLATFORM_PREFIX + 'owner')
PLATFORM_TAGS['REGION'] = os.getenv('PLATFORM_TAGS_REGION', PLATFORM_PREFIX + 'region')
PLATFORM_TAGS['GROUPS'] = os.getenv('PLATFORM_TAGS_GROUPS', PLATFORM_PREFIX + 'groups')


def get_user_context(event):
    """
    Get the users groups and roles from the claims
    in the Lambda event
    """
    user = event['claims']['email']
    groups = event['claims']['groups']
    roles = event['claims']['roles'].split(',')
    
    return user, groups, roles


def get_request_params(event):
    """
    Get the parameters sent in the request
    """
    params = {}

    if 'params' in event:
        params = event['params']

    return params


def get_ssm_params():
    """
    Get the users groups and roles from the claims
    in the Lambda event
    """
    SSM_CLIENT = boto3.client('ssm', PLATFORM_REGION)
    ssm_params = SSM_CLIENT.get_parameters_by_path(Path='/gureume', Recursive=True)
    ssm_params = ssm_params['Parameters']

    # think about paging
    ssm_params = tu.kv_to_dict(ssm_params, 'Name', 'Value')

    return build_nested(ssm_params)


def build_nested_helper(path, value, container):
    segs = path.split('/')
    head = segs[0]
    tail = segs[1:]

    if not tail:
        # found end of path, write value to key
        container[head] = value
        LOGGER.debug('Wrote {} to {}'.format(value, head))
    elif not head or 'gureume' in head:
        # don't create container if empty or is platform name
        build_nested_helper('/'.join(tail), value, container)
    else:
        if head not in container:
            container[head] = {}
        build_nested_helper('/'.join(tail), value, container[head])


def build_nested(paths):
    container = {}

    for path, value in paths.items():
        build_nested_helper(path, value, container)
    print(container)
    return container