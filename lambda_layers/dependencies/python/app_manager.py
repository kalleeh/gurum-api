"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

import boto3

from logger import configure_logger
from stack_manager import StackManager
# from parameter_store import ParameterStore

import transform_utils as tu
import ssm_helper
import elb_helper

# import config

from aws_xray_sdk.core import patch_all

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
        ssm = ssm_helper.get_params()
        # parameter_store = ParameterStore(region=config.PLATFORM_REGION, role=boto3)
        # ssm = parameter_store.fetch_parameters_by_path('/gureume')
        # ssm_params = tu.kv_to_dict(ssm, 'Name', 'Value')
        # ssm_params = tu.build_nested(ssm_params)

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
        params['Priority'] = str(elb_helper.get_next_rule_priority(
            ssm['platform']['loadbalancer']['listener-arn']))
        params = tu.dict_to_kv(
            params,
            'ParameterKey',
            'ParameterValue',
            clean=True)
        params = params + tu.reuse_vals(reuse_params)

        return params
