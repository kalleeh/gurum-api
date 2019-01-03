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
Pipeline Resource Definition

    URI: /pipelines
    Methods:
        GET - List all pipelines
        POST - Create new pipeline

"""


def get(event, context):
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

    LOGGER.debug('Listing Pipelines:')    

    # Get the user id for the request
    groups = event['claims']['groups']

    try:
        # List CloudFormation Stacks
        r = CFN_CLIENT.describe_stacks()
    except Exception as ex:
        logging.exception(ex)
        util.respond(500, 'Failed to list pipelines.')

    # Filter stacks based on owner and retrieve wanted keys
    keys = ['StackName', 'Parameters', 'CreationTime', 'LastUpdatedTime']
    stacks = util.filter_stacks(r['Stacks'], keys, groups, 'pipeline')

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
    except Exception as ex:
        logging.exception(ex)
        util.respond(500, 'Unexpected error')

    return util.respond(None, data)


def post(event, context):
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

    # Get the user id for the request
    user = event['claims']['email']
    groups = event['claims']['groups']

    payload = json.loads(event['body-json'][0])

    stack_name = util.addprefix(payload['name'])
    LOGGER.debug('Creating Pipeline: ' + stack_name)

    if 'pipeline_type' in payload:
        pipeline_type = payload['pipeline_type']
    else:
        pipeline_type = 'github'
    if 'pipeline_version' in payload:
        pipeline_version = payload['pipeline_version']
    else:
        pipeline_version = 'latest'
    
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

    tags[util.PLATFORM_TAGS['TYPE']] = 'pipeline'
    tags[util.PLATFORM_TAGS['VERSION']] = '0.1'
    tags[util.PLATFORM_TAGS['GROUPS']] = groups
    tags[util.PLATFORM_TAGS['REGION']] = util.PLATFORM_REGION
    tags[util.PLATFORM_TAGS['OWNER']] = user
    tags = util.dict_to_kv(tags, 'Key', 'Value')

    template_url = 'https://s3-{}.amazonaws.com/{}/cfn/pipelines/pipeline-{}-{}.yaml'.format(
        util.PLATFORM_REGION,
        PLATFORM_BUCKET,
        pipeline_type,
        pipeline_version
    )
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
            return util.respond(400, 'A pipeline with that name already exists.')
        else:
            logging.exception(e)
            return util.respond(400, 'Unexpected error: %s' % e)
    except Exception as ex:
        logging.exception(ex)
        return util.respond(500, 'Internal server error.')
    else:
        return util.respond(None, stack)