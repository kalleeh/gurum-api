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

class ServiceManager(StackManager):
    def __init__(self, event):
        self._stack_type = 'service'
        
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
        
        # mark parameters that should be re-used in CloudFormation and modify depending on payload.
        reuse_params = []
        
        params['ServiceBindings'] = payload['service_bindings'] if 'service_bindings' in payload else None

        params = tu.dict_to_kv(params, 'ParameterKey', 'ParameterValue', clean=True)
        params = params + tu.reuse_vals(reuse_params)
        
        return params