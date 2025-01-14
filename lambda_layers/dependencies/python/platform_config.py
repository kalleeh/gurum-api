import os

from logger import configure_logger

LOGGER = configure_logger(__name__)

PLATFORM_PREFIX = os.getenv('PLATFORM_PREFIX', 'gurum')
PLATFORM_ACCOUNT_ID = os.getenv('PLATFORM_ACCOUNT_ID', '')
PLATFORM_REGION = os.getenv('PLATFORM_REGION', 'eu-west-1')
PLATFORM_ECS_CLUSTER = os.getenv('PLATFORM_ECS_CLUSTER', '{}-{}'.format(PLATFORM_PREFIX, 'cluster'))
PLATFORM_DEPLOYMENT_ROLE = os.getenv('PLATFORM_DEPLOYMENT_ROLE', 'deployment_role')
PLATFORM_BUCKET = os.getenv('PLATFORM_BUCKET', None)

# Tags for the platform
PLATFORM_TAGS = {}
PLATFORM_TAGS['PRODUCT_TYPE'] = os.getenv('PLATFORM_TAGS_PRODUCT_TYPE', '{}-{}'.format(PLATFORM_PREFIX, 'product-type'))
PLATFORM_TAGS['PRODUCT_FLAVOR'] = os.getenv('PLATFORM_TAGS_PRODUCT_FLAVOR', '{}-{}'.format(PLATFORM_PREFIX, 'product-flavor'))
PLATFORM_TAGS['VERSION'] = os.getenv('PLATFORM_TAGS_VERSION', '{}-{}'.format(PLATFORM_PREFIX, 'platform-version'))
PLATFORM_TAGS['OWNER'] = os.getenv('PLATFORM_TAGS_OWNER', '{}-{}'.format(PLATFORM_PREFIX, 'owner'))
PLATFORM_TAGS['REGION'] = os.getenv('PLATFORM_TAGS_REGION', '{}-{}'.format(PLATFORM_PREFIX, 'region'))
PLATFORM_TAGS['GROUPS'] = os.getenv('PLATFORM_TAGS_GROUPS', '{}-{}'.format(PLATFORM_PREFIX, 'groups'))


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
