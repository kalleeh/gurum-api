"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

import json

from logger import configure_logger
from pipelinemanager import PipelineManager

import transform_utils as tu

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


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
    pm = PipelineManager(event)

    data = {}
    data['pipelines'] = []

    payload = json.loads(event['body-json'][0])

    """
    Configure default values if not present
    """
    name = tu.add_prefix(payload['name'])

    if not 'subtype' in payload:
        payload['subtype'] = 'github'
    if not 'version' in payload:
        payload['version'] = 'latest'
    
    resp = pm.create_stack(
        name,
        payload
    )

    data['pipelines'] = resp

    return tu.respond(None, data)