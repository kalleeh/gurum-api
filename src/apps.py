import boto3
import json
import logging
from botocore.exceptions import ValidationError, ClientError

import libs.util as util

logger = logging.getLogger()
logger.setLevel(logging.INFO)

"""
Apps Resource Definition

    URI: /apps
    Methods:
        GET - List all apps
        POST - Create a new app
"""


def get():
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
    
    logger.debug('Listing Apps:')

    try:
        # List CloudFormation Stacks
        r = cfn.describe_stacks()
    except Exception as ex:
        logging.exception(ex)
        raise Exception('Failed to list apps')
    
    # Filter stacks based on owner and retrieve wanted keys
    keys = ['StackName', 'Parameters', 'CreationTime', 'LastUpdatedTime']
    stacks = util.filter_stacks(r['Stacks'], keys, 'app')

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
        raise Exception(e)

    response = json.dumps(data, default=util.datetime_serialize)

    return response


def post():
    """ Creates a new app belonging to the authenticated user.

    Args:
        None:
    Basic Usage:
        >>> POST /apps
        >>> Payload Example:
            [{
                "name": "my-app",
                "tasks": "1",
                "health_check_path": "/health",
                "image": "nginx:latest"     [Optional]
            }]
    Returns:
        List: List of JSON objects containing app information
    """
    params = {}
    tags = {}

    request = app.current_request

    # Get the user id for the request
    user = request.context['authorizer']['claims']['email']
    groups = request.context['authorizer']['claims']['cognito:groups']

    payload = json.loads(request.json_body[0])

    stack_name = util.addprefix(payload['name'])
    logger.debug('Creating App: ' + stack_name)

    exports = util.get_cfn_exports()

    params['DesiredCount'] = payload['tasks']
    params['Priority'] = str(util.iterate_rule_priority(exports['LoadBalancerListener']))
    params['Listener'] = exports['LoadBalancerListener']
    params['HealthCheckPath'] = payload['health_check_path']
    params['DockerImage'] = payload['image']
    params = util.dict_to_kv(params, 'ParameterKey', 'ParameterValue')

    tags[PLATFORM_TAGS['TYPE']] = 'app'
    tags[PLATFORM_TAGS['VERSION']] = '0.1'
    tags[PLATFORM_TAGS['GROUPS']] = groups
    tags[PLATFORM_TAGS['REGION']] = PLATFORM_REGION
    tags[PLATFORM_TAGS['OWNER']] = user
    tags = util.dict_to_kv(tags, 'Key', 'Value')

    try:
        stack = cfn.create_stack(
            StackName=stack_name,
            TemplateURL='https://s3-eu-west-1.amazonaws.com/storage-kalleh/cfn/app/app.yaml',
            TimeoutInMinutes=15,
            Parameters=params,
            Capabilities=[
                'CAPABILITY_NAMED_IAM',
            ],
            RoleARN=PLATFORM_DEPLOYMENT_ROLE,
            Tags=tags
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            raise Exception('An application with that name already exists.')
        else:
            print("Unexpected error: %s" % e)
    except Exception as ex:
        logging.exception(ex)
        raise Exception('Internal server error.')

    response = json.dumps(stack, default=util.datetime_serialize)

    return response


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }