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
Service Resource Definition

    URI: /services
    Methods:
        GET - List all services
        POST - Create new service

"""


def get(event, context):
    """ Returns the services belonging to the authenticated user.
    It uses filter_stacks() to filter the CloudFormation stacks with type 'service'
    and owner belonging to the same Cognito group as the user is logged in as.

    Args:
        None:
    Basic Usage:
        >>> GET /services
    Returns:
        List: List of JSON objects containing service information
    """
    data = []
    stacks = []

    LOGGER.debug('Listing Services:')    

    # Get the user id for the request
    groups = event['claims']['groups']

    try:
        # List CloudFormation Stacks
        r = CFN_CLIENT.describe_stacks()
    except Exception as ex:
        logging.exception(ex)
        util.respond(500, 'Failed to list services.')

    # Filter stacks based on owner and retrieve wanted keys
    keys = ['StackName', 'Parameters', 'CreationTime', 'LastUpdatedTime']
    stacks = util.filter_stacks(r['Stacks'], keys, groups, 'service')

    try:
        for stack in stacks:
            name = util.remprefix(stack['StackName'])
            params = util.kv_to_dict(stack['Parameters'], 'ParameterKey', 'ParameterValue')
            data.append(
                {
                    'name': name,
                    'created_at': stack['CreationTime'],
                    'updated_at': stack['LastUpdatedTime'],
                    'service_bindings': params['ServiceBindings']
                })
    except Exception as e:
        util.respond(e)

    return util.respond(None, data)


def post(event, context):
    """ Creates a new service belonging to the authenticated user.
    Pre-requisites: User must create a new OAuth token on his GitHub-account
    that allows repo access to the requested repository for the service
    to be able to pull source.

    Args:
        name (string): Name of the service (CloudFormation Stack)
    Basic Usage:
        >>> POST /service
        >>> Payload Example:
            [{
                "service_name": "my-service",
                "service_type": "s3|sqs",
                "service_bindings": "app1,app2",
                "service_version": "0.1|latest"     [Optional]
            }]
    Returns:
        List: List of JSON objects containing service information
    """
    params = {}
    tags = {}

    # Get the user id for the request
    user = event['claims']['email']
    groups = event['claims']['groups']

    payload = json.loads(event['body-json'][0])

    stack_name = util.addprefix(payload['name'])
    LOGGER.debug('Creating Service: ' + stack_name)

    if 'service_type' in payload:
        service_type = payload['service_type']
    else:
        service_type = 's3'
    if 'service_bindings' in payload:
        binding_list = ['arn:aws:iam::789073296014:role/platform-role-' + b for b in payload['service_bindings'].split(',')]
        service_bindings = ','.join(map(str, binding_list))
    if 'service_version' in payload:
        service_version = payload['service_version']
    else:
        service_version = 'latest'
    
    params['ServiceBindings'] = service_bindings
    params = util.dict_to_kv(params, 'ParameterKey', 'ParameterValue')

    tags[util.PLATFORM_TAGS['TYPE']] = 'service'
    tags[util.PLATFORM_TAGS['SUBTYPE']] = service_type
    tags[util.PLATFORM_TAGS['VERSION']] = service_version
    tags[util.PLATFORM_TAGS['GROUPS']] = groups
    tags[util.PLATFORM_TAGS['REGION']] = util.PLATFORM_REGION
    tags[util.PLATFORM_TAGS['OWNER']] = user
    tags = util.dict_to_kv(tags, 'Key', 'Value')
    
    template_url = 'https://s3-eu-west-1.amazonaws.com/' + \
        PLATFORM_BUCKET + \
        '/cfn/services/service-' + \
        service_type + '-' + \
        service_version + '.yaml'
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
            util.respond(400, 'A service with that name already exists.')
        else:
            print("Unexpected error: %s" % e)
    except Exception as ex:
        logging.exception(ex)
        util.respond(500, 'Internal server error.')

    return util.respond(None, stack)