"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

import json

from exceptions import NoSuchObject, PermissionDenied
from aws_xray_sdk.core import patch_all
from logger import configure_logger

import transform_utils
import response_builder

from managers.pipeline_manager import PipelineManager

patch_all()

LOGGER = configure_logger(__name__)


def patch(event, _context):
    """ Updates the pipeline belonging to the authenticated user.
    """
    pm = PipelineManager(event)

    data = {}
    data['pipelines'] = []

    payload = json.loads(event['body-json'][0])

    if 'type' not in payload:
        payload['type'] = 'github/cfn'
    if 'version' not in payload:
        payload['version'] = 'latest'

    validate_permissions(pm, payload)

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

def validate_permissions(pm, payload):
    if 'app_name' in payload and not pm.has_permissions(transform_utils.add_prefix(payload['app_name'])):
        raise PermissionDenied('Application Permission denied.')

    if 'app_dev' in payload and not pm.has_permissions(transform_utils.add_prefix(payload['app_dev'])):
        raise PermissionDenied('Application (dev) Permission denied.')

    if 'app_test' in payload and not pm.has_permissions(transform_utils.add_prefix(payload['app_test'])):
        raise PermissionDenied('Application (test) Permission denied.')
