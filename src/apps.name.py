import boto3
import json
import logging
from botocore.exceptions import ValidationError, ClientError

"""
Apps Resource Definition

    URI: /apps
    Methods:
        GET - List all apps

    URI: /apps/{name}
    Methods:
        POST - Create new app
        GET - Get the details of app
        PATCH - Update the app
        DELETE - Delete the app
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

    app.log.debug('Listing Apps:')

    try:
        # List CloudFormation Stacks
        r = cfn.describe_stacks()
    except Exception as ex:
        logging.exception(ex)
        raise ChaliceViewError('Failed to list apps')
    
    # Filter stacks based on owner and retrieve wanted keys
    keys = ['StackName', 'Parameters', 'CreationTime', 'LastUpdatedTime']
    stacks = filter_stacks(r['Stacks'], keys, 'app')

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
        raise ChaliceViewError(e)

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
    print(payload)

    stack_name = util.addprefix(payload['name'])
    app.log.debug('Creating App: ' + stack_name)

    exports = get_cfn_exports()

    params['DesiredCount'] = payload['tasks']
    params['Priority'] = str(iterate_rule_priority(exports['LoadBalancerListener']))
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
            raise ChaliceViewError('An application with that name already exists.')
        else:
            print("Unexpected error: %s" % e)
    except Exception as ex:
        logging.exception(ex)
        raise ChaliceViewError('Internal server error.')

    response = json.dumps(stack, default=util.datetime_serialize)

    return response


def get(name):
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

    app.log.debug('Describing Stack:')
    stack_name = util.addprefix(name)

    # List CloudFormation Stacks
    try:
        r = cfn.describe_stacks(StackName=stack_name)
    except Exception as ex:
        logging.exception(ex)
        raise ChaliceViewError('Internal server error.')

    # Filter stacks based on owner and retrieve wanted keys
    keys = ['StackName', 'Description', 'StackStatus', 'Tags', 'Outputs']
    try:
        apps = filter_stacks(r['Stacks'], keys, 'app')
    except Exception as ex:
        logging.exception(ex)
        raise ChaliceViewError('Error while filtering stacks.')

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

    return response


def patch(name):
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

    request = app.current_request

    # Get the user id for the request
    user = request.context['authorizer']['claims']['email']
    groups = request.context['authorizer']['claims']['cognito:groups']

    payload = json.loads(request.json_body[0])

    stack_name = util.addprefix(name)
    app.log.debug('Updating App: ' + str(stack_name))

    # Validate authorization
    if not validate_auth(stack_name):
        raise ChaliceViewError('You do not have permission to modify this resource.')

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

    tags[PLATFORM_TAGS['TYPE']] = 'app'
    tags[PLATFORM_TAGS['VERSION']] = '0.2'
    tags[PLATFORM_TAGS['GROUPS']] = groups
    tags[PLATFORM_TAGS['REGION']] = PLATFORM_REGION
    tags[PLATFORM_TAGS['OWNER']] = user
    tags = util.dict_to_kv(tags, 'Key', 'Value')

    try:
        stack = cfn.update_stack(
            StackName=stack_name,
            UsePreviousTemplate=True,
            Parameters=params,
            Capabilities=[
                'CAPABILITY_NAMED_IAM',
            ],
            RoleARN=PLATFORM_DEPLOYMENT_ROLE,
            Tags=tags
        )
    except ValidationError as e:
        raise ChaliceViewError('No updates are to be performed. {}'.format(e))
    except Exception as ex:
        logging.exception(ex)
        raise ChaliceViewError('Internal server error.')

    response = json.dumps(stack, default=util.datetime_serialize)

    return response


def delete(name):
    """ Validates that the app belongs to the authenticated user
    and deletes the app.

    Args:
        name (string): Name of the app (CloudFormation Stack)
    Basic Usage:
        >>> DELETE /apps/my-app
    Returns:
        List: List of JSON objects containing app information
    """
    stack_name = util.addprefix(name)
    app.log.debug('Deleting App: ' + stack_name)

    # Validate authorization
    if not validate_auth(stack_name):
        raise ChaliceViewError('You do not have permission to modify this resource.')
    
    try:
        stack = cfn.delete_stack(StackName=stack_name)
    except ValidationError as e:
        if e.response['Error']['Message'].endswidth('does not exist'):
            raise ChaliceViewError('No such item.')
    except Exception as ex:
        logging.exception(ex)
        raise ChaliceViewError('Internal server error.')

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


def lambda_handler(event, context):
    """Demonstrates a simple HTTP endpoint using API Gateway. You have full
    access to the request and response payload, including headers and
    status code.
    To scan a DynamoDB table, make a GET request with the TableName as a
    query string parameter. To put, update, or delete an item, make a POST,
    PUT, or DELETE request respectively, passing in the payload to the
    DynamoDB API as a JSON body.
    """

    #print("Received event: " + json.dumps(event, indent=2))

    operations = {
        'DELETE': lambda dynamo, x: dynamo.delete_item(**x),
        'GET': lambda dynamo, x: dynamo.scan(**x),
        'POST': lambda dynamo, x: dynamo.put_item(**x),
        'PUT': lambda dynamo, x: dynamo.update_item(**x),
    }

    operation = event['httpMethod']
    if operation in operations:
        payload = event['queryStringParameters'] if operation == 'GET' else json.loads(event['body'])
        return respond(None, operations[operation](dynamo, payload))
    else:
        return respond(ValueError('Unsupported method "{}"'.format(operation)))