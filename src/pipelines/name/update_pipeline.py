"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from exceptions import NoSuchObject, PermissionDenied

import json

from logger import configure_logger
from pipeline_manager import PipelineManager

import response_builder

from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def patch(event, _context):
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
                "github_user": "mygithubuser",
                "upgrade_version": "False"  [Optional] Forces platform
                    version upgrade
            }]
    Returns:
        List: List of JSON objects containing app information
    """
    pm = PipelineManager(event)

    data = {}
    data['pipelines'] = []

    payload = json.loads(event['body-json'][0])

    # Configure default values if not present
    if 'subtype' not in payload:
        payload['subtype'] = 'shared-lb'
    if 'version' not in payload:
        payload['version'] = 'latest'

    if 'app_name' in payload and not pm.has_permissions(payload['app_name']):
        raise PermissionDenied

    if 'app_dev' in payload and not pm.has_permissions(payload['app_dev']):
        raise PermissionDenied

    if 'app_test' in payload and not pm.has_permissions(payload['app_test']):
        raise PermissionDenied

    try:
        resp = pm.update_stack(
            payload
        )
    except NoSuchObject:
        return response_builder.error('No such pipeline.', 400)
    except PermissionDenied:
        return response_builder.error('Permission denied.', 401)
    except Exception as ex:
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        data['pipelines'] = resp

        return response_builder.success(data)
