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
Pipeline Resource Definition

    URI: /pipelines/{name}
    Methods:
        GET - Get the details of pipeline
        PATCH - Update the specified pipeline
        DELETE - Delete the pipeline
"""


def get(event, context):
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

    LOGGER.debug('Describing Stack:')

    # Get the user id for the request
    groups = event['claims']['groups']
    name = event['params']['name']

    # List CloudFormation Stacks
    try:
        r = CFN_CLIENT.describe_stacks(StackName=name)
    except Exception as ex:
        logging.exception(ex)
        util.respond('Internal server error.')

    # Filter stacks based on owner and retrieve wanted keys
    keys = ['StackName', 'Description', 'StackStatus', 'Tags', 'Outputs']
    try:
        pipelines = util.filter_stacks(r['Stacks'], keys, groups, 'pipeline')
    except Exception as ex:
        logging.exception(ex)
        util.respond('Error while filtering stacks.')
    
    if 'Outputs' in pipelines[0]:
        data['outputs'] = util.kv_to_dict(pipelines[0]['Outputs'], 'OutputKey', 'OutputValue')
    data['name'] = util.remprefix(pipelines[0]['StackName'])
    data['description'] = pipelines[0]['Description']
    data['status'] = pipelines[0]['StackStatus']
    data['tags'] = util.kv_to_dict(pipelines[0]['Tags'], 'Key', 'Value')

    return util.respond(None, data)


def patch(event, context):
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
    stack = {}

    # Get the user id for the request
    user = event['claims']['email']
    groups = event['claims']['groups']
    name = event['params']['name']

    payload = json.loads(event['body-json'][0])

    stack_name = util.addprefix(name)
    LOGGER.debug('Updating Pipeline: ' + stack_name)

    # Validate authorization
    if not util.validate_auth(stack_name, groups):
        util.respond('You do not have permission to access this resource.')
    
    if 'app_dev' in payload:
        params['ServiceDev'] = util.addprefix(payload['app_dev'])
    if 'app_test' in payload:
        params['ServiceTest'] = util.addprefix(payload['app_test'])
    if 'app_name' in payload:
        params['ServiceProd'] = util.addprefix(payload['app_name'])
    if 'github_repo' in payload:
        params['GitHubRepo'] = payload['github_repo']
    if 'github_branch' in payload:
        params['GitHubBranch'] = payload['github_branch']
    if 'github_token' in payload:
        params['GitHubToken'] = payload['github_token']
    if 'github_user' in payload:
        params['GitHubUser'] = payload['github_user']
    params = util.dict_to_kv(params, 'ParameterKey', 'ParameterValue')

    tags[util.PLATFORM_TAGS['TYPE']] = 'pipeline'
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
            util.respond('A pipeline with that name already exists.')
        else:
            print("Unexpected error: %s" % e)
    except Exception as ex:
        logging.exception(ex)
        util.respond('Internal server error.')

    return util.respond(None, stack)


def delete(event, context):
    """ Validates that the pipeline belongs to the authenticated user
    and deletes the pipeline.

    Args:
        name (string): Name of the pipeline (CloudFormation Stack)
    Basic Usage:
    Returns:
        List: List of JSON objects containing pipeline information
    """
    # Get the user id for the request
    groups = event['claims']['groups']
    name = event['params']['name']

    stack_name = util.addprefix(name)
    LOGGER.debug('Deleting Pipeline: ' + stack_name)

    # Validate authorization
    if not util.validate_auth(stack_name, groups):
        util.respond('You do not have permission to access this resource.')
    
    try:
        CFN_CLIENT.delete_stack(StackName=stack_name)
    except ClientError as e:
        if e.response['Error']['Code'] == "NoSuchEntity":
            # no need to delete a thing that doesn't exist
            return util.respond(None, 'Pipeline does not exist, deletion succeeded')
    except Exception as ex:
        logging.exception(ex)
        return util.respond(ex)
    else:
        return util.respond(None, 'Successfully deleted the pipeline.')