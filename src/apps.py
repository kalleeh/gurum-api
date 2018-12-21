import boto3
import json
import logging
import os
from botocore.exceptions import ValidationError, ClientError

import libs.util as util

"""
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()
"""

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

# Create CloudFormation Client
CFN_CLIENT = boto3.client('cloudformation', region_name=util.PLATFORM_REGION)

# Set constant S3 bucket for template files
PLATFORM_BUCKET = os.environ['PLATFORM_BUCKET']

"""
Apps Resource Definition

    URI: /apps
    Methods:
        GET - List all apps
        POST - Create a new app
"""


def get(event, context):
    """ Returns the apps belonging to the authenticated user.
    It uses filter_stacks() to filter the CloudFormation stacks with type 'app'
    and owner belonging to the same Cognito group as the user is logged in as.

    Args:
        None:
    Basic Usage:
        >>> GET /apps
    Returns:
        List: List of JSON objects containing app information
    """
    data = []
    stacks = []
    
    LOGGER.debug('Listing Apps:')

    # Get the user id for the request
    groups = event['claims']['groups']

    try:
        # List CloudFormation Stacks
        r = CFN_CLIENT.describe_stacks()
    except Exception as ex:
        logging.exception(ex)
        util.respond('Failed to list apps')

    # Filter stacks based on owner and retrieve wanted keys
    keys = ['StackName', 'Parameters', 'CreationTime', 'LastUpdatedTime']
    stacks = util.filter_stacks(r['Stacks'], keys, groups, 'app')

    try:
        for stack in stacks:
            name = util.remprefix(stack['StackName'])
            params = util.kv_to_dict(stack['Parameters'], 'ParameterKey', 'ParameterValue')
            data.append(
                {
                    'name': name,
                    'created_at': stack['CreationTime'],
                    'updated_at': stack['LastUpdatedTime'],
                    'tasks': params['DesiredCount']
                })
    except Exception as e:
        util.respond(e)
    else:
        return util.respond(None, data)


def post(event, context):
    """ Creates a new app belonging to the authenticated user.

    Args:
        None:
    Basic Usage:
        >>> POST /apps
        >>> Payload Example:
            {
                "name": "my-app",
                "tasks": "1",
                "health_check_path": "/health",
                "image": "nginx:latest"             [Optional]
            }
    Returns:
        List: List of JSON objects containing app information
    """
    params = {}
    tags = {}

    # Get the user id for the request
    user = event['claims']['email']
    groups = event['claims']['groups']

    payload = json.loads(event['body-json'][0])

    stack_name = util.addprefix(payload['name'])
    LOGGER.debug('Creating App: ' + stack_name)

    if 'app_type' in payload:
        app_type = payload['app_type']
    else:
        app_type = 'shared-lb'
    if 'app_version' in payload:
        app_version = payload['app_version']
    else:
        app_version = 'latest'
    
    exports = util.get_cfn_exports()

    params['DesiredCount'] = payload['tasks']
    params['Priority'] = str(util.iterate_rule_priority(exports['LoadBalancerListener']))
    params['Listener'] = exports['LoadBalancerListener']
    params['HealthCheckPath'] = payload['health_check_path']
    params['DockerImage'] = payload['image']
    params['GroupName'] = groups
    params = util.dict_to_kv(params, 'ParameterKey', 'ParameterValue')

    tags[util.PLATFORM_TAGS['TYPE']] = 'app'
    tags[util.PLATFORM_TAGS['SUBTYPE']] = app_type
    tags[util.PLATFORM_TAGS['VERSION']] = app_version
    tags[util.PLATFORM_TAGS['GROUPS']] = groups
    tags[util.PLATFORM_TAGS['REGION']] = util.PLATFORM_REGION
    tags[util.PLATFORM_TAGS['OWNER']] = user
    tags = util.dict_to_kv(tags, 'Key', 'Value')

    template_url = 'https://s3-eu-west-1.amazonaws.com/' + \
        PLATFORM_BUCKET + \
        '/cfn/apps/app-' + \
        app_type + '-' + \
        app_version + '.yaml'
    LOGGER.debug('Template URL: ' + template_url)

    try:
        stack = CFN_CLIENT.create_stack(
            StackName=stack_name,
            TemplateURL=template_url,
            TimeoutInMinutes=15,
            Parameters=params,
            Capabilities=[
                'CAPABILITY_NAMED_IAM',
            ],
            RoleARN=util.PLATFORM_DEPLOYMENT_ROLE,
            Tags=tags
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            return util.respond('An application with that name already exists.')
        else:
            logging.exception(e)
            return util.respond('Unexpected error: %s' % e)
    except Exception as ex:
        logging.exception(ex)
        return util.respond('Internal server error.')
    else:
        return util.respond(None, stack)