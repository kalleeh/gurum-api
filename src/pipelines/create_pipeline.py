import json

from exceptions import AlreadyExists
from aws_xray_sdk.core import patch_all
from logger import configure_logger

import response_builder
import transform_utils

from managers.pipeline_manager import PipelineManager

patch_all()

LOGGER = configure_logger(__name__)


def post(event, _context):
    """ Creates a new pipeline belonging to the authenticated user.
    Pre-requisites: User must create a new OAuth token on his GitHub-account
    that allows repo access to the requested repository for the pipeline
    to be able to pull source.
    """
    pm = PipelineManager(event)

    data = {}
    data['pipelines'] = []

    payload = json.loads(event['body-json'][0])

    name = transform_utils.add_prefix(payload['name'])

    # Configure default values if not present
    if 'product_flavor' not in payload:
        payload['product_flavor'] = 'github/cfn'
    if 'version' not in payload:
        payload['version'] = 'latest'

    try:
        resp = pm.create_stack(
            name,
            payload
        )
    except AlreadyExists:
        return response_builder.error('A pipeline with that name already exists.', 409)
    except Exception as ex:
        return response_builder.error('Unknown Error: {}'.format(ex))
    else:
        data['pipelines'] = resp

        return response_builder.success(data)
