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

import config
import transform_utils
import elb_helper

from managers.stack_manager import StackManager
from parameter_store import ParameterStore

patch_all()

LOGGER = configure_logger(__name__)


"""
Application Stack Manager
"""


class AppManager(StackManager):
    def __init__(self, event):
        self._stack_type = 'app'

        StackManager.__init__(
            self,
            event=event,
            stack_type=self._stack_type
        )

    def _generate_params(self, payload):
        """ Dynamically generates a CloudFormation compatible
        dict with the params passed in from a request payload.

        Args:
        Basic Usage:
            >>> resp = _generate_params(params)
        Returns:
            List: List of dicts containing key:value pairs
            representing CloudFormation Params
            [
                {
                    'ParameterKey': 'Name',
                    'ParamaterValue': 'value-of-parameter'
                }
            ]
        """
        params = {}
        LOGGER.debug('Generating parameters.')
        parameter_store = ParameterStore(
            config.PLATFORM_REGION,
            boto3
        )

        ssm_params = parameter_store.get_parameters()
        LOGGER.debug(
            'Loaded SSM Dictionary into Config: %s',
            ssm_params)

        # mark parameters that should be re-used in CloudFormation and
        # modify depending on payload.
        reuse_params = []
        params['DesiredCount'] = payload['tasks'] if 'tasks' in payload else reuse_params.append('DesiredCount')
        params['HealthCheckPath'] = payload['health_check_path'] if 'health_check_path' in payload else reuse_params.append('HealthCheckPath')
        params['DockerImage'] = payload['image'] if 'image' in payload else reuse_params.append('DockerImage')
        LOGGER.debug(
            'Reusing parameters: %s',
            reuse_params)

        # we need to dynamically generate the priorty param to insert
        # since it's required by CFN.
        params['Priority'] = str(elb_helper.get_random_rule_priority(
            ssm_params['platform']['loadbalancer']['listener-arn']))

        params = transform_utils.dict_to_kv(
            params,
            'ParameterKey',
            'ParameterValue',
            clean=True)
        params = params + transform_utils.reuse_vals(reuse_params)

        LOGGER.debug(
            'Returning parameters: %s',
            params)

        return params
