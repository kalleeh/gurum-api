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
    data = {}

    LOGGER.debug('Describing Stack:')

    # Get the user id for the request
    groups = event['claims']['groups']
    name = event['params']['name']

    stack_name = util.addprefix(name)

    # Validate authorization
    if not util.validate_auth(stack_name, groups, 'service'):
        util.respond(403, 'You do not have permission to access this resource.')
    
    # List CloudFormation Stacks
    try:
        resp = CFN_CLIENT.describe_stacks(StackName=stack_name)
    except Exception as ex:
        logging.exception(ex)
        return util.respond(500, 'Internal server error.')
    else:
        stack = resp['Stacks'][0]
        if 'Outputs' in stack:
            data['outputs'] = util.kv_to_dict(stack['Outputs'], 'OutputKey', 'OutputValue')
        data['name'] = util.remprefix(stack['StackName'])
        data['description'] = stack['Description']
        data['status'] = stack['StackStatus']
        data['tags'] = util.kv_to_dict(stack['Tags'], 'Key', 'Value')

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
        util.respond(403, 'You do not have permission to access this resource.')
    
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
            util.respond(400, 'A service with that name already exists.')
        else:
            print("Unexpected error: %s" % e)
    except Exception as ex:
        logging.exception(ex)
        util.respond(500, 'Internal server error.')

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
        util.respond(403, 'You do not have permission to access this resource.')
    
    try:
        CFN_CLIENT.delete_stack(StackName=stack_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError' and 'does not exist' in e.response['Error']['Message']:
            return util.respond(None, 'Service does not exist')
    except ValidationError as e:
        logging.exception(e)
        util.respond(400, 'Invalid input')
    except Exception as ex:
        logging.exception(ex)
        util.respond(500, 'Internal server error')
    else:
        return util.respond(None, 'Successfully deleted the service')