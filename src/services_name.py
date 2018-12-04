import boto3
import json
import logging
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

"""
Service Resource Definition

    URI: /services/{name}
    Methods:
        GET - Get the details of service
        PATCH - Update the specified service
        DELETE - Delete the service
"""


def get(event, context):
    """ Describes detailed information about a service

    Args:
        name (string): Name of the service (CloudFormation Stack)
    Basic Usage:
        >>> GET /services/my-service
    Returns:
        List: List of JSON object containing service information
    """
    services = []
    data = {}

    LOGGER.debug('Describing Stack:')

    # Get the user id for the request
    groups = event['claims']['groups']
    name = event['params']['name']

    # List CloudFormation Stacks
    try:
        r = CFN_CLIENT.describe_stacks(StackName=name)
    except Exception as ex:
        logging.exception(ex)
        raise Exception('Internal server error.')

    # Filter stacks based on owner and retrieve wanted keys
    keys = ['StackName', 'Description', 'StackStatus', 'Tags', 'Outputs']
    try:
        services = util.filter_stacks(r['Stacks'], keys, groups, 'service')
    except Exception as ex:
        logging.exception(ex)
        raise Exception('Error while filtering stacks.')
    
    if 'Outputs' in services[0]:
        data['outputs'] = util.kv_to_dict(services[0]['Outputs'], 'OutputKey', 'OutputValue')
    data['name'] = util.remprefix(services[0]['StackName'])
    data['description'] = services[0]['Description']
    data['status'] = services[0]['StackStatus']
    data['tags'] = util.kv_to_dict(services[0]['Tags'], 'Key', 'Value')

    return util.respond(None, data)


def patch(event, context):
    """ Updates the service belonging to the authenticated user.

    Args:
        name (string): Name of the service (CloudFormation Stack)
    Basic Usage:
        >>> POST /service
        >>> Payload Example:
            [{
                "service_name": "my-service",
                "service_dev": "my-service-dev",    [Optional]
                "service_test": "my-service-test",  [Optional]
                "github_repo": "2048",
                "github_branch": "master",
                "github_token": "b248f1e7360fe21c33e12d4bca3feaweEXAMPLE",
                "github_user": "mygithubuser"
            }]
    Returns:
        List: List of JSON objects containing service information
    """
    params = {}
    tags = {}
    stack = {}

    # Get the user id for the request
    user = event['claims']['email']
    groups = event['claims']['groups']
    name = event['params']['name']

    payload = json.loads(event['body-json'][0])

    stack_name = util.addprefix(name)
    LOGGER.debug('Updating Service: ' + stack_name)

    # Validate authorization
    if not util.validate_auth(stack_name, groups):
        raise Exception('You do not have permission to modify this resource.')
    
    if 'service_dev' in payload:
        params['ServiceDev'] = util.addprefix(payload['service_dev'])
    if 'service_test' in payload:
        params['ServiceTest'] = util.addprefix(payload['service_test'])
    if 'service_name' in payload:
        params['ServiceProd'] = util.addprefix(payload['service_name'])
    if 'github_repo' in payload:
        params['GitHubRepo'] = payload['github_repo']
    if 'github_branch' in payload:
        params['GitHubBranch'] = payload['github_branch']
    if 'github_token' in payload:
        params['GitHubToken'] = payload['github_token']
    if 'github_user' in payload:
        params['GitHubUser'] = payload['github_user']
    params = util.dict_to_kv(params, 'ParameterKey', 'ParameterValue')

    tags[util.PLATFORM_TAGS['TYPE']] = 'service'
    tags[util.PLATFORM_TAGS['VERSION']] = '0.2'
    tags[util.PLATFORM_TAGS['GROUPS']] = groups
    tags[util.PLATFORM_TAGS['REGION']] = util.PLATFORM_REGION
    tags[util.PLATFORM_TAGS['OWNER']] = user
    tags = util.dict_to_kv(tags, 'Key', 'Value')

    try:
        stack = CFN_CLIENT.update_stack(
            StackName=stack_name,
            UsePreviousTemplate=True,
            Parameters=params,
            Capabilities=[
                'CAPABILITY_NAMED_IAM',
            ],
            RoleARN=util.PLATFORM_DEPLOYMENT_ROLE,
            Tags=tags
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            raise Exception('A service with that name already exists.')
        else:
            print("Unexpected error: %s" % e)
    except Exception as ex:
        logging.exception(ex)
        raise Exception('Internal server error.')

    return util.respond(None, stack)


def delete(event, context):
    """ Validates that the service belongs to the authenticated user
    and deletes the service.

    Args:
        name (string): Name of the service (CloudFormation Stack)
    Basic Usage:
    Returns:
        List: List of JSON objects containing service information
    """
    # Get the user id for the request
    groups = event['claims']['groups']
    name = event['params']['name']

    stack_name = util.addprefix(name)
    LOGGER.debug('Deleting Service: ' + stack_name)

    # Validate authorization
    if not util.validate_auth(stack_name, groups):
        raise Exception('You do not have permission to modify this resource.')
    
    try:
        stack = CFN_CLIENT.delete_stack(StackName=stack_name)
    except ValidationError as e:
        error_msg = util.boto_exception(e)
        if error_msg.endswidth('does not exist'):
            raise Exception('No such item.')
    except Exception as ex:
        logging.exception(ex)
        raise Exception('Internal server error.')

    return util.respond(None, stack)