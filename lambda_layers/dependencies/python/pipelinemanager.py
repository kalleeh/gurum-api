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

class PipelineManager(StackManager):
    def __init__(self, event):
        self._stack_type = 'pipeline'
        self.codepipeline = boto3.client('codepipeline', region_name=config.PLATFORM_REGION)
        
        StackManager.__init__(
            self,
            event=event,
            stack_type=self._stack_type
        )
    

    def get_pipeline_state(self, pipeline_name):
        """ Returns information about the state of a pipeline,
        including the stages and actions.

        Args:
        Basic Usage:
            >>> get_pipeline_state()
        Returns:
            Dict: Dict representing AWS CodePipeline States and information
            {
                'pipelineName': 'string',
                'pipelineVersion': 123,
                'stageStates': [
                    {
                        'actionStates': [
                            {
                ...
        """
        LOGGER.debug('Describing Pipeline State {}'.format(pipeline_name))
        
        try:
            states = self.codepipeline.get_pipeline_state(name=pipeline_name)
        except Exception as ex:
            LOGGER.exception(ex)
            return None
        
        states = states['stageStates']
        
        return states
    

    def put_approval_result(self, pipeline_name, stage_name, action_name, summary, status, token):
        """ Returns information about the state of a pipeline,
        including the stages and actions.

        Args:
        Basic Usage:
            >>> put_approval_result()
        Returns:
            Dict: Dict representing approval datetime.
            {
                'approvedAt': datetime(2015, 1, 1)
            }
        """
        LOGGER.debug('Approving deploy for {}'.format(pipeline_name))

        result = {}
        result['summary'] = summary
        result['status'] = status

        print(result)
        
        try:
            states = self.codepipeline.put_approval_result(
                pipelineName = pipeline_name,
                stageName = stage_name,
                actionName = action_name,
                result = result,
                token = token
                )
        except Exception as ex:
            LOGGER.exception(ex)
            raise 
        
        return states
    

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

        params['GitHubUser'] = payload['github_user'] if 'github_user' in payload else reuse_params.append('GitHubUser')
        params['GitHubToken'] = payload['github_token'] if 'github_token' in payload else reuse_params.append('GitHubToken')
        params['GitHubRepo'] = payload['github_repo'] if 'github_repo' in payload else reuse_params.append('GitHubRepo')
        
        params['ServiceDev'] = tu.add_prefix(payload['app_dev']) if 'app_dev' in payload else None
        params['ServiceTest'] = tu.add_prefix(payload['app_test']) if 'app_test' in payload else None
        params['ServiceProd'] = tu.add_prefix(payload['app_name']) if 'app_name' in payload else None
        params['GitHubBranch'] = payload['github_branch'] if 'github_branch' in payload else None
        params = tu.dict_to_kv(params, 'ParameterKey', 'ParameterValue', clean=True)
        params = params + tu.reuse_vals(reuse_params)
        
        return params
