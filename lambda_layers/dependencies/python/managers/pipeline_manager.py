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


class PipelineManager(StackManager):
    def __init__(self, event):
        self._stack_type = 'pipeline'
        self.codepipeline = boto3.client(
            'codepipeline',
            region_name=platform_config.PLATFORM_REGION)

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
        LOGGER.debug(
            'Describing Pipeline State %s',
            pipeline_name)

        try:
            states = self.codepipeline.get_pipeline_state(name=pipeline_name)
        except Exception as ex:
            LOGGER.exception(ex)
            return None

        states = states['stageStates']

        return states

    def put_approval_result(
            self,
            pipeline_name,
            stage_name,
            action_name,
            summary,
            status,
            token):
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
        LOGGER.debug(
            'Approving deploy for %s',
            pipeline_name)

        result = {}
        result['summary'] = summary
        result['status'] = status

        print(result)

        try:
            states = self.codepipeline.put_approval_result(
                pipelineName=pipeline_name,
                stageName=stage_name,
                actionName=action_name,
                result=result,
                token=token
                )
        except Exception as ex:
            LOGGER.exception(ex)
            raise

        return states

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

        # mark parameters that should be re-used in CloudFormation
        # and modify depending on payload.
        reuse_params = []

        source = payload['source']
        params.update(source)

        #TODO: Make dynamic through generated templates.
        environments = ['ServiceProd']
        no_environments = len(payload['environments'])

        if no_environments >= 2:
            environments.append('ServiceDev')
        if no_environments == 3:
            environments.append('ServiceTest')

        i = 0
        for environment_name in payload['environments']:
            environment = {environments[i]: transform_utils.add_prefix(environment_name)}
            params.update(environment)
            i = i + 1

        params['GitHubToken'] = source['GitHubToken'] \
            if 'GitHubToken' in source else reuse_params.append('GitHubToken')

        source = payload['source']
        params.update(source)

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
