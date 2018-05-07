import boto3
import json
import logging
from botocore.exceptions import ValidationError, ClientError

"""
Pipeline Resource Definition

    URI: /pipelines
    Methods:
        GET - List all pipelines

    URI: /pipelines/{name}
    Methods:
        POST - Create new pipeline
        GET - Get the details of app
        PATCH - Update the specified pipeline
        DELETE - Delete the pipeline
"""


@app.route('/pipelines',
           authorizer=authorizer)
def list_pipelines():
    """ Returns the pipelines belonging to the authenticated user.
    It uses filter_stacks() to filter the CloudFormation stacks with type 'pipeline'
    and owner belonging to the same Cognito group as the user is logged in as.

    Args:
        None:
    Basic Usage:
        >>> GET /pipelines
    Returns:
        List: List of JSON objects containing app information
    """
    data = []
    stacks = []

    app.log.debug('Listing Pipelines:')

    try:
        # List CloudFormation Stacks
        r = cfn.describe_stacks()
    except Exception as ex:
        logging.exception(ex)
        raise ChaliceViewError('Failed to list pipelines')

    # Filter stacks based on owner and retrieve wanted keys
    keys = ['StackName', 'Parameters', 'CreationTime', 'LastUpdatedTime']
    stacks = filter_stacks(r['Stacks'], keys, 'pipeline')

    try:
        for stack in stacks:
            name = util.remprefix(stack['StackName'])
            params = util.kv_to_dict(stack['Parameters'], 'ParameterKey', 'ParameterValue')
            data.append(
                {
                    'name': name,
                    'created_at': stack['CreationTime'],
                    'updated_at': stack['LastUpdatedTime'],
                    'app_dev': params['ServiceDev'],
                    'app_test': params['ServiceTest'],
                    'app': params['ServiceProd']
                })
    except Exception as e:
        raise ChaliceViewError(e)

    response = json.dumps(data, default=util.datetime_serialize)

    return response


@app.route('/pipelines/{name}',
           methods=['POST'],
           authorizer=authorizer)
def create_pipeline(name):
    """ Creates a new pipeline belonging to the authenticated user.
    Pre-requisites: User must create a new OAuth token on his GitHub-account
    that allows repo access to the requested repository for the pipeline
    to be able to pull source.

    Args:
        name (string): Name of the pipeline (CloudFormation Stack)
    Basic Usage:
        >>> POST /pipeline
        >>> Payload Example:
            [{
                "app_name": "my-app",
                "app_dev": "my-app-dev",    [Optional]
                "app_test": "my-app-test",  [Optional]
                "github_repo": "2048",
                "github_branch": "master",
                "github_token": "b248f1e7360fe21c33e12d4bca3feaweEXAMPLE",
                "github_user": "mygithubuser"
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
    app.log.debug('Creating Pipeline: ' + stack_name)

    if 'app_dev' in payload:
        params['ServiceDev'] = util.addprefix(payload['app_dev'])
    if 'app_test' in payload:
        params['ServiceTest'] = util.addprefix(payload['app_test'])
    params['ServiceProd'] = util.addprefix(payload['app_name'])
    params['GitHubRepo'] = payload['github_repo']
    params['GitHubBranch'] = payload['github_branch']
    params['GitHubToken'] = payload['github_token']
    params['GitHubUser'] = payload['github_user']
    params = util.dict_to_kv(params, 'ParameterKey', 'ParameterValue')

    tags[PLATFORM_TAGS['TYPE']] = 'pipeline'
    tags[PLATFORM_TAGS['VERSION']] = '0.1'
    tags[PLATFORM_TAGS['GROUPS']] = groups
    tags[PLATFORM_TAGS['REGION']] = PLATFORM_REGION
    tags[PLATFORM_TAGS['OWNER']] = user
    tags = util.dict_to_kv(tags, 'Key', 'Value')

    try:
        stack = cfn.create_stack(
            StackName=stack_name,
            TemplateURL='https://s3-eu-west-1.amazonaws.com/storage-kalleh/cfn/app/pipeline.yaml',
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
            raise ChaliceViewError('A pipeline with that name already exists.')
        else:
            print("Unexpected error: %s" % e)
    except Exception as ex:
        logging.exception(ex)
        raise ChaliceViewError('Internal server error.')

    response = json.dumps(stack, default=util.datetime_serialize)

    return response


@app.route('/pipelines/{name}',
           authorizer=authorizer)
def describe_pipeline(name):
    """ Describes detailed information about a pipeline

    Args:
        name (string): Name of the pipeline (CloudFormation Stack)
    Basic Usage:
        >>> GET /pipelines/my-pipeline
    Returns:
        List: List of JSON object containing pipeline information
    """
    pipelines = []
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
        pipelines = filter_stacks(r['Stacks'], keys, 'pipeline')
    except Exception as ex:
        logging.exception(ex)
        raise ChaliceViewError('Error while filtering stacks.')
    
    if 'Outputs' in pipelines[0]:
        data['outputs'] = util.kv_to_dict(pipelines[0]['Outputs'], 'OutputKey', 'OutputValue')
    data['name'] = util.remprefix(pipelines[0]['StackName'])
    data['description'] = pipelines[0]['Description']
    data['status'] = pipelines[0]['StackStatus']
    data['tags'] = util.kv_to_dict(pipelines[0]['Tags'], 'Key', 'Value')

    response = json.dumps(data, default=util.datetime_serialize)

    return response


@app.route('/pipelines/{name}',
           methods=['PATCH'],
           authorizer=authorizer)
def update_pipeline(name):
    """ Updates the pipeline belonging to the authenticated user.

    Args:
        name (string): Name of the pipeline (CloudFormation Stack)
    Basic Usage:
        >>> POST /pipeline
        >>> Payload Example:
            [{
                "app_name": "my-app",
                "app_dev": "my-app-dev",    [Optional]
                "app_test": "my-app-test",  [Optional]
                "github_repo": "2048",
                "github_branch": "master",
                "github_token": "b248f1e7360fe21c33e12d4bca3feaweEXAMPLE",
                "github_user": "mygithubuser"
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
    app.log.debug('Updating Pipeline: ' + stack_name)

    # Validate authorization
    if not validate_auth(stack_name):
        raise ChaliceViewError('You do not have permission to modify this resource.')
    
    if 'app_dev' in payload:
        params['ServiceDev'] = util.addprefix(payload['app_dev'])
    if 'app_test' in payload:
        params['ServiceTest'] = util.addprefix(payload['app_test'])
    params['ServiceProd'] = util.addprefix(payload['app_name'])
    params['GitHubRepo'] = payload['github_repo']
    params['GitHubBranch'] = payload['github_branch']
    params['GitHubToken'] = payload['github_token']
    params['GitHubUser'] = payload['github_user']
    params = util.dict_to_kv(params, 'ParameterKey', 'ParameterValue')

    tags[PLATFORM_TAGS['TYPE']] = 'pipeline'
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
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            raise ChaliceViewError('A pipeline with that name already exists.')
        else:
            print("Unexpected error: %s" % e)
    except Exception as ex:
        logging.exception(ex)
        raise ChaliceViewError('Internal server error.')

    response = json.dumps(stack, default=util.datetime_serialize)

    return response


# Delete pipeline
@app.route('/pipelines/{name}',
           methods=['DELETE'],
           authorizer=authorizer)
def delete_pipeline(name):
    """ Validates that the pipeline belongs to the authenticated user
    and deletes the pipeline.

    Args:
        name (string): Name of the pipeline (CloudFormation Stack)
    Basic Usage:
    Returns:
        List: List of JSON objects containing pipeline information
    """
    stack_name = util.addprefix(name)
    app.log.debug('Deleting Pipeline: ' + stack_name)

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