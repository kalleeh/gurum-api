"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

import boto3

from aws_xray_sdk.core import patch_all
from logger import configure_logger

import platform_config
import transform_utils

from managers.stack_manager import StackManager
from parameter_store import ParameterStore

patch_all()

LOGGER = configure_logger(__name__)


"""
Application Stack Manager
"""


class ServiceManager(StackManager):
    def __init__(self, event):
        self._product_type = 'service'

        StackManager.__init__(
            self,
            event=event,
            product_type=self._product_type
        )

    def _generate_params(self, payload):
        """ Dynamically generates a CloudFormation compatible
        dict with the params passed in from a request payload.
        """
        params = {}
        LOGGER.debug('Generating parameters.')
        parameter_store = ParameterStore(
            platform_config.PLATFORM_REGION,
            boto3
        )

        ssm_params = parameter_store.get_parameters()
        LOGGER.debug(
            'Loaded SSM Dictionary into Config: %s',
            ssm_params)

        config = payload['config']
        params.update(config)

        params = transform_utils.dict_to_kv(
            params,
            'ParameterKey',
            'ParameterValue',
            clean=True)

        LOGGER.debug(
            'Returning parameters: %s',
            params)

        return params
