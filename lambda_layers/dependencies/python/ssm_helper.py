"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

"""
Helper for managing SSM parameters
"""

import os
import boto3

from paginator import paginator

import transform_utils as tu
import config

from logger import configure_logger

LOGGER = configure_logger(__name__)


def get_params(path='/gureume', max_items=100):
    LOGGER.debug('Fetching SSM parameters.')
    SSM_CLIENT = boto3.client('ssm', config.PLATFORM_REGION)
    params = []

    try:
        for param in paginator(
                SSM_CLIENT.get_parameters_by_path,
                Path=path,
                Recursive=True,
                PaginationConfig={
                    'MaxItems': max_items
                }
            ):
            params.append(param)
    except Exception as ex:
        LOGGER.exception(ex)
    
    LOGGER.debug('Got params from SSM:\n {} '.format(params))
    
    ssm_params = tu.kv_to_dict(params, 'Name', 'Value')
    ssm_params = tu.build_nested(ssm_params)

    LOGGER.debug('Loaded SSM Dictionary into Config:\n {} '.format(ssm_params))
    
    return ssm_params