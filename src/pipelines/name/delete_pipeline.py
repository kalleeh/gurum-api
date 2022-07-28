from exceptions import NoSuchObject, PermissionDenied
from aws_xray_sdk.core import patch_all
from logger import configure_logger

import response_builder

from managers.pipeline_manager import PipelineManager

patch_all()

LOGGER = configure_logger(__name__)


def delete(event, _context):
    """ Validates that the pipeline belongs to the authenticated user
    and deletes the pipeline.
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
