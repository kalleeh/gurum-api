"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

import boto3
from botocore.exceptions import ValidationError, ClientError

from logger import configure_logger
from paginator import paginator
from stackmanager import StackManager

import transform_utils as tu
import template_generator as tg
import config

from aws_xray_sdk.core import xray_recorder
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
        exports = self._get_exports()
        
        # mark parameters that should be re-used in CloudFormation and modify depending on payload.
        reuse_params = []
        params['DesiredCount'] = payload['tasks'] if 'tasks' in payload else reuse_params.append('DesiredCount')
        params['HealthCheckPath'] = payload['health_check_path'] if 'health_check_path' in payload else reuse_params.append('HealthCheckPath')
        params['DockerImage'] = payload['image'] if 'image' in payload else reuse_params.append('DockerImage')

        params['Priority'] = str(self._iterate_rule_priority(exports['LoadBalancerListener']))
        params['Listener'] = exports['LoadBalancerListener']
        params['GroupName'] = self._groups
        params = tu.dict_to_kv(params, 'ParameterKey', 'ParameterValue', clean=True)
        params = params + tu.reuse_vals(reuse_params)

        return params


    def _iterate_rule_priority(self, listener_arn):
        """ Returns the next rule priority number for a given ALB Listener Arn

        Args:
            listener_arn (string): String of the ARN to the ALB Listener
        Basic Usage:
            >>> resp = iterate_rule_priority(listener_arn)
        Returns:
            Number: Number of the next available rule priority number
            Default: 1
        """
        client = boto3.client('elbv2', region_name=config.PLATFORM_REGION)
        rules = {}

        try:
            rules = client.describe_rules(
                ListenerArn=listener_arn,
            )['Rules']
        except Exception as ex:
            LOGGER.exception(ex)
            raise('Internal server error.')

        rules = [rule for rule in rules if rule['Priority'].isdigit()]

        if not rules:
            return 1

        sorted_rules = sorted(rules, key=lambda x: int(x['Priority']), reverse=True)
        priority = int(sorted_rules[0]['Priority'])+1

        return priority