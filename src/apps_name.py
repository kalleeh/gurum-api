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
Apps Resource Definition

    URI: /apps/{name}
    Methods:
        GET - Get the details of app
        PATCH - Update the app
        DELETE - Delete the app
"""


def get(event, context):
    """ Describes detailed information about an app

    Args:
        name (string): Name of the app (CloudFormation Stack)
    Basic Usage:
        >>> GET /apps/my-app
    Returns:
        List: List of JSON object containing app information
    """
    data = {}

    LOGGER.debug('Describing Stack:')

    # Get the user id for the request
    groups = event['claims']['groups']
    name = event['params']['name']

    stack_name = util.addprefix(name)

    # Validate authorization
    if not util.validate_auth(stack_name, groups, 'app'):
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
    """ Validates that the app belongs to the authenticated user
    and updates the configuration.

    Args:
        name (string): Name of the app (CloudFormation Stack)
    Basic Usage:
        >>> PATCH /apps/-my-app
        >>> Payload Example:
            [{
                "tasks": "2",
                "health_check_path": "/health",
                "image": "nginx:latest"     [Optional]
            }]
    Returns:
        List: List of JSON objects containing app information
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
    LOGGER.debug('Updating App: ' + str(stack_name))

    # Validate authorization
    if not util.validate_auth(stack_name, groups):
        util.respond(403, 'You do not have permission to access this resource.')
    
    # mark parameters that should be re-used in CloudFormation and modify depending on paylod.
    reuse_params = ['Priority','Listener','GroupName']
    if 'tasks' in payload:              params['DesiredCount'] = payload['tasks'] 
    else:                               reuse_params.append('DesiredCount')
    if 'health_check_path' in payload:  params['HealthCheckPath'] = payload['health_check_path']
    else:                               reuse_params.append('HealthCheckPath')
    if 'image' in payload:              params['DockerImage'] = payload['image']
    else:                               reuse_params.append('DockerImage')
    params = util.dict_to_kv(params, 'ParameterKey', 'ParameterValue')
    params = params + util.reuse_vals(reuse_params)

    tags[util.PLATFORM_TAGS['TYPE']] = 'app'
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
    except ValidationError as e:
        logging.exception(e)
        util.respond(400, 'Invalid input')
    except Exception as ex:
        logging.exception(ex)
        util.respond(500, 'Unexpected error')
    else:
        return util.respond(None, stack)


def delete(event, context):
    """ Validates that the app belongs to the authenticated user
    and deletes the app.

    Args:
        name (string): Name of the app (CloudFormation Stack)
    Basic Usage:
        >>> DELETE /apps/my-app
    Returns:
        List: List of JSON objects containing app information
    """
    # Get the user id for the request
    groups = event['claims']['groups']
    name = event['params']['name']

    stack_name = util.addprefix(name)
    LOGGER.debug('Deleting App: ' + stack_name)

    # Validate authorization
    if not util.validate_auth(stack_name, groups):
        util.respond(403, 'You do not have permission to access this resource.')
    
    try:
        CFN_CLIENT.delete_stack(StackName=stack_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError' and 'does not exist' in e.response['Error']['Message']:
            return util.respond(None, 'App does not exist')
    except ValidationError as e:
        logging.exception(e)
        util.respond(400, 'Invalid input')
    except Exception as ex:
        logging.exception(ex)
        util.respond(500, 'Internal server error')
    else:
        return util.respond(None, 'Successfully deleted the app')