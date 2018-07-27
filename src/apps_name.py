import boto3
import json
import logging
from botocore.exceptions import ValidationError, ClientError

import libs.util as util

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

logger = logging.getLogger()
logger.setLevel(logging.ERROR)

# Create CloudFormation Client
cfn = boto3.client('cloudformation', region_name=util.PLATFORM_REGION)

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
    apps = {}
    data = {}

    logger.debug('Describing Stack:')

    # Get the user id for the request
    groups = event['requestContext']['authorizer']['claims']['cognito:groups']

    stack_name = util.addprefix(event['pathParameters']['name'])

    # List CloudFormation Stacks
    try:
        r = cfn.describe_stacks(StackName=stack_name)
    except Exception as ex:
        logging.exception(ex)
        raise Exception('Internal server error.')

    # Filter stacks based on owner and retrieve wanted keys
    keys = ['StackName', 'Description', 'StackStatus', 'Tags', 'Outputs']
    try:
        apps = util.filter_stacks(r['Stacks'], keys, groups, 'app')
    except Exception as ex:
        logging.exception(ex)
        raise Exception('Error while filtering stacks.')

    if 'Outputs' in apps[0]:
        outputs = util.kv_to_dict(apps[0]['Outputs'], 'OutputKey', 'OutputValue')
        data['endpoint'] = outputs['Endpoint']
        if 'Repository' in outputs:
            data['repository'] = outputs['Repository']
    data['name'] = util.remprefix(apps[0]['StackName'])
    data['description'] = apps[0]['Description']
    data['status'] = apps[0]['StackStatus']
    data['tags'] = util.kv_to_dict(apps[0]['Tags'], 'Key', 'Value')

    response = json.dumps(data, default=util.datetime_serialize)

    return util.respond(None, response)


def patch(name, event, context):
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

    # Get the user id for the request
    user = event['requestContext']['authorizer']['claims']['email']
    groups = event['requestContext']['authorizer']['claims']['cognito:groups']

    payload = json.loads(event['body'])

    stack_name = util.addprefix(event['pathParameters']['name'])
    logger.debug('Updating App: ' + str(stack_name))

    # Validate authorization
    if not util.validate_auth(stack_name, groups):
        raise Exception('You do not have permission to modify this resource.')

    if 'tasks' in payload:
        params['DesiredCount'] = payload['tasks']
    if 'health_check_path' in payload:
        params['HealthCheckPath'] = payload['health_check_path']
    if 'image' in payload:
        params['DockerImage'] = payload['image']
    params = util.dict_to_kv(params, 'ParameterKey', 'ParameterValue')
    params.append(
        {
            "ParameterKey": 'Priority',
            "UsePreviousValue": True
        }
    )
    params.append(
        {
            "ParameterKey": 'Listener',
            "UsePreviousValue": True
        }
    )
    if not 'tasks' in payload:
        params.append(
            {
                "ParameterKey": 'DesiredCount',
                "UsePreviousValue": True
            }
        )
    if not 'health_check_path' in payload:
        params.append(
            {
                "ParameterKey": 'HealthCheckPath',
                "UsePreviousValue": True
            }
        )
    if not 'image' in payload:
        params.append(
            {
                "ParameterKey": 'DockerImage',
                "UsePreviousValue": True
            }
        )

    tags[util.PLATFORM_TAGS['TYPE']] = 'app'
    tags[util.PLATFORM_TAGS['VERSION']] = '0.2'
    tags[util.PLATFORM_TAGS['GROUPS']] = groups
    tags[util.PLATFORM_TAGS['REGION']] = util.PLATFORM_REGION
    tags[util.PLATFORM_TAGS['OWNER']] = user
    tags = util.dict_to_kv(tags, 'Key', 'Value')

    try:
        stack = cfn.update_stack(
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
        raise Exception('No updates are to be performed. {}'.format(e))
    except Exception as ex:
        logging.exception(ex)
        raise Exception('Internal server error.')

    response = json.dumps(stack, default=util.datetime_serialize)

    return util.respond(None, response)


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
    stack_name = util.addprefix(event['pathParameters']['name'])
    logger.debug('Deleting App: ' + stack_name)

    # Get the user id for the request
    groups = event['requestContext']['authorizer']['claims']['cognito:groups']

    # Validate authorization
    if not util.validate_auth(stack_name, groups):
        raise Exception('You do not have permission to modify this resource.')
    
    try:
        stack = cfn.delete_stack(StackName=stack_name)
    except ValidationError as e:
        error_msg = util.boto_exception(e)
        if error_msg.endswidth('does not exist'):
            raise Exception('No such item.')
    except Exception as ex:
        logging.exception(ex)
        raise Exception('Internal server error.')

    response = json.dumps(stack, default=util.datetime_serialize)

    return util.respond(None, response)