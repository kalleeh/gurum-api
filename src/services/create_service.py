"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

import json

from aws_xray_sdk.core import patch_all
from logger import configure_logger

import response_builder
import transform_utils

from managers.service_manager import ServiceManager

patch_all()

LOGGER = configure_logger(__name__)


def post(event, _context):
    """ Creates a new service belonging to the authenticated user.
    Pre-requisites: User must create a new OAuth token on his GitHub-account
    that allows repo access to the requested repository for the service
    to be able to pull source.

    Args:
        name (string): Name of the service (CloudFormation Stack)
    Basic Usage:
        >>> POST /service
        >>> Payload Example:
            [{
                "service_name": "my-service",
                "service_type": "s3|sqs",
                "service_bindings": "app1,app2",
                "service_version": "0.1|latest"     [Optional]
            }]
    Returns:
        List: List of JSON objects containing service information
    """
    sm = ServiceManager(event)

    data = {}
    data['services'] = []

    payload = json.loads(event['body-json'][0])

    # Configure default values if not present

    name = transform_utils.add_prefix(payload['name'])

    if 'subtype' not in payload:
        payload['subtype'] = 's3'
    if 'version' not in payload:
        payload['version'] = 'latest'

    try:
        resp = sm.create_stack(
            name,
            payload
        )
    except Exception as ex:
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        data['services'] = resp

        return response_builder.success(data)
