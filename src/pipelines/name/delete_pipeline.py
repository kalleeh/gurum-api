"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from exceptions import NoSuchObject, PermissionDenied

from logger import configure_logger
from pipeline_manager import PipelineManager

import response_builder

from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


def delete(event, _context):
    """ Validates that the pipeline belongs to the authenticated user
    and deletes the pipeline.

    Args:
        name (string): Name of the pipeline (CloudFormation Stack)
    Basic Usage:
    Returns:
        List: List of JSON objects containing pipeline information
    """
    pm = PipelineManager(event)

    try:
        pm.delete_stack()
    except NoSuchObject:
        return response_builder.error('No such pipeline.', 400)
    except PermissionDenied:
        return response_builder.error('Permission denied.', 401)
    except Exception as ex:
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        return response_builder.success('Successfully deleted the pipeline.')
