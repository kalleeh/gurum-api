"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from abc import ABCMeta, abstractmethod

import boto3
from botocore.exceptions import ValidationError, ClientError
from exceptions import AlreadyExists, InvalidInput, NoSuchObject, PermissionDenied, UnknownError

from logger import configure_logger
from paginator import paginator

import transform_utils as tu
import template_generator as tg
import config

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)


"""
CloudFormation Stack Manager
"""

class StackManager():
    __metaclass__ = ABCMeta
    def __init__(self, event, stack_type):
        self.event = event
        self.client = boto3.client('cloudformation', region_name=config.PLATFORM_REGION)
        self._user, self._groups, self._roles = config.get_user_context(self.event)
        self._params = config.get_request_params(self.event)
        self._stack_type = stack_type


    def list_stacks(self, keys):
        """ List of stacks validating they are stacks in the platform
        and belongs to the user performing the request and returns the chosen
        keys (arg) for those stacks.

        Args:
            stack_type (string): Filter based on stack type, valid options are
                'app','pipeline' or 'any'
        Basic Usage:
            >>> list_stacks('app')
        Returns:
            List: List of dicts representing AWS Stacks and information
            [
                {
                    'StackName': 'mystack',
                    'StackStatus': 'status'
                }
            ]
        """
        LOGGER.debug('Listing stacks of type {}'.format(self._stack_type))

        try:
            stacks = self.client.describe_stacks()
        except Exception as ex:
            LOGGER.exception(ex)
            raise UnknownError from ex
        
        stacks = stacks['Stacks']
        stacks = self.filter_stacks(stacks)
        stacks = self.filter_keys(stacks, keys)
        
        return stacks
    

    def create_stack(self, stack_name, payload):
        """ Creates a new stack.

        Args:
            type: (app|pipeline|service)
            stack_name: 
            payload: 
        Basic Usage:
        Returns:
            List: List of ..
        """
        LOGGER.debug('Creating stack: {}'.format(stack_name))

        params = self._generate_params(payload)
        tags = self._generate_tags(payload)
        template_url = tg.generate_template_url(
            config.PLATFORM_REGION,
            config.PLATFORM_BUCKET,
            self._stack_type,
            payload)

        try:
            stack = self.client.create_stack(
                StackName=stack_name,
                TemplateURL=template_url,
                TimeoutInMinutes=15,
                Parameters=params,
                Capabilities=[
                    'CAPABILITY_NAMED_IAM',
                ],
                RoleARN=config.PLATFORM_DEPLOYMENT_ROLE,
                Tags=tags
            )
        except self.client.exceptions.AlreadyExistsException as ex:
            LOGGER.exception(ex)
            raise AlreadyExists from ex
        except self.client.exceptions.InsufficientCapabilities as ex:
            LOGGER.exception(ex)
            LOGGER.debug('Error: The template contains resources with capabilities that weren\'t specified in the Capabilities parameter.')
            raise UnknownError from ex
        except self.client.exceptions.LimitExceeded as ex:
            LOGGER.exception(ex)
            LOGGER.debug('Error: The quota for the resource has already been reached.')
            raise UnknownError from ex
        except Exception as ex:
            LOGGER.exception(ex)
            raise UnknownError from ex
        else:
            return stack


    def describe_stack(self):
        """ List of stacks validating they are stacks in the platform
        and belongs to the user performing the request and returns the chosen
        keys (arg) for those stacks.

        Args:
            stack_type (string): Filter based on stack type, valid options are
                'app','pipeline' or 'any'
        Basic Usage:
            >>> list_stacks('app')
        Returns:
            List: List of dicts representing AWS Stacks and information
            [
                {
                    'StackName': 'mystack',
                    'StackStatus': 'status'
                }
            ]
        """
        stack_name = tu.add_prefix(self._params['name'])
        LOGGER.debug('Describing stack {}'.format(stack_name))
        
        try:
            stacks = self.client.describe_stacks(StackName=stack_name)
        except Exception as ex:
            LOGGER.exception(ex)
            raise UnknownError from ex
        
        stacks = stacks['Stacks']
        stacks = self.filter_stacks(stacks)
        
        return stacks


    def update_stack(self, payload):
        """ Creates a new stack.

        Args:
            type: (app|pipeline|service)
            stack_name: 
            payload: 
        Basic Usage:
        Returns:
            List: List of ..
        """
        stack_name = tu.add_prefix(self._params['name'])
        LOGGER.debug('Updating stack {}'.format(stack_name))

        params = self._generate_params(payload)
        tags = self._generate_tags(payload)

        try:
            if(payload['upgrade_version']):
                template_url = tg.generate_template_url(
                    config.PLATFORM_REGION,
                    config.PLATFORM_BUCKET,
                    self._stack_type,
                    payload)
                
                stack = self.client.update_stack(
                    StackName=stack_name,
                    TemplateURL=template_url,
                    Parameters=params,
                    Capabilities=[
                        'CAPABILITY_NAMED_IAM',
                    ],
                    RoleARN=config.PLATFORM_DEPLOYMENT_ROLE,
                    Tags=tags
                )
            else:
                stack = self.client.update_stack(
                    StackName=stack_name,
                    UsePreviousTemplate=True,
                    Parameters=params,
                    Capabilities=[
                        'CAPABILITY_NAMED_IAM',
                    ],
                    RoleARN=config.PLATFORM_DEPLOYMENT_ROLE,
                    Tags=tags
                )
        except ClientError as e:
            LOGGER.exception(e)
            if e.response['Error']['Code'] == 'ValidationError' and \
                'does not exist' in e.response['Error']['Message']:
                raise NoSuchObject from e
            if e.response['Error']['Code'] == 'ValidationError' and \
                'ROLLBACK_COMPLETE' in e.response['Error']['Message']:
                raise Exception('Stack is in inconsistent state. Please re-create it.')
        except self.client.exceptions.InsufficientCapabilities as ex:
            LOGGER.exception(ex)
            LOGGER.debug('Error: The template contains resources with capabilities that weren\'t specified in the Capabilities parameter.')
            raise UnknownError from ex
        except Exception as ex:
            LOGGER.exception(ex)
            raise UnknownError from ex
        else:
            return stack


    def delete_stack(self):
        """ Deletes a CloudFormation stack.

        Args:
            name (string): Name of the CloudFormation Stack
        Basic Usage:
        Returns:
            List: List of JSON objects containing stack information
        """
        stack_name = tu.add_prefix(self._params['name'])
        LOGGER.debug('Deleting stack: ' + stack_name)

        if not self.has_permissions(stack_name):
            raise PermissionDenied
        
        try:
            self.client.delete_stack(StackName=stack_name)
        except ClientError as e:
            LOGGER.exception(e)
            if e.response['Error']['Code'] == 'ValidationError' and \
                'does not exist' in e.response['Error']['Message']:
                raise NoSuchObject from e
        except PermissionDenied as e:
            LOGGER.exception(e)
            raise
        except ValidationError as e:
            LOGGER.exception(e)
            raise InvalidInput from e
        except Exception as ex:
            LOGGER.exception(ex)
            raise UnknownError from ex
        else:
            return True


    def filter_stacks(self, stacks):
        """ Filters a list of stacks validating they are stacks in the platform
        and belongs to the user performing the request.

        Args:
            stacks (list): List of dicts representing AWS CloudFormation Stacks.
            stack_type (string): Filter based on stack type, valid options are
                'app','pipeline' or 'any'
        Basic Usage:
            >>> stacks = [{'StackId': '12314-392839-1321', 'StackName': 'mystack'} ...]
            >>> filter_stacks(stacks, keys, 'app')
        Returns:
            List: List of dicts representing AWS Stacks and information
            {
                'Stacks':
                [
                    {
                        'StackName': 'mystack',
                        'StackStatus': 'status'
                    }
                ]
            ]
        """
        data = []

        try:
            for stack in stacks:
                stack_tags = tu.kv_to_dict(stack['Tags'], 'Key', 'Value')
                LOGGER.debug('(filter_stacks) Evaluating Stack: {}'.format(stack))

                if not self._is_platform_stack(stack_tags):
                    LOGGER.debug('{} is not part of the platform.'.format(stack['StackName']))
                    continue
                if not self._is_requested_type(stack_tags):
                    LOGGER.debug('{} is not not the correct type ({})'.format(stack['StackName'], self._stack_type))
                    continue
                if not self._owned_by_group(stack_tags):
                    LOGGER.debug('{} is not owned by requester.'.format(stack['StackName']))
                    continue
                
                """
                If checks passed, add the requested keys to the data dict to return
                """
                LOGGER.debug('{} passed checks. Adding to return data.'.format(stack['StackName']))
                data.append(stack)
        except Exception as ex:
            LOGGER.exception(ex)
            raise UnknownError from ex
        else:
            return data
    
    
    def filter_keys(self, stacks, keys):
        """ Filters a list of stacks and returns the chosen keys (arg) for those stacks.

        Args:
            stacks (list): List of dicts representing AWS CloudFormation Stacks.
            keys (list): List of keys representing the desired information to return.
        Basic Usage:
            >>> stacks = [{'StackId': '12314-392839-1321', 'StackName': 'mystack'} ...]
            >>> keys = ['StackName','StackStatus']
            >>> filter_stacks(stacks, keys)
        Returns:
            List: List of dicts representing AWS Stacks and information
            [
                {
                    'StackName': 'mystack',
                    'StackStatus': 'status'
                }
            ]
        """
        data = []

        try:
            for stack in stacks:
                filtered_stack = {}
                
                for key in keys:
                    if not key in stack:
                        filtered_stack[key] = "N/A"
                    else:
                        filtered_stack[key] = stack[key]
                
                data.append(filtered_stack)
        except KeyError as ex:
            LOGGER.exception(ex)
            raise
        except Exception as ex:
            LOGGER.exception(ex)
            raise UnknownError from ex
        else:
            return data
        
        
    def has_permissions(self, stack_name):
        """ Check if the authenticated user has permissions to the
        requested stack.

        Args:
            stack_name (string): Name of the stack to validate.
        Basic Usage:
            >>> has_permissions('app')
        Returns:
            Bool: Boolean with the result of the permission check.
        """
        LOGGER.debug('Validating permissions for: {}'.format(stack_name))
        
        try:
            stacks = self.client.describe_stacks(StackName=stack_name)
        except ClientError as e:
            LOGGER.exception(e)
            if e.response['Error']['Code'] == 'ValidationError' and \
                'does not exist' in e.response['Error']['Message']:
                return False
        except Exception as ex:
            LOGGER.exception(ex)

            """ Catch and log unhandled exceptions but just returns False.
            This is desired if something goes wrong permissions should
            still be denied. """
            return False
        else:
            stack = stacks['Stacks'][0]
            stack_tags = tu.kv_to_dict(stack['Tags'], 'Key', 'Value')
            
            if(self._owned_by_group(stack_tags)):
                return True
        
        return False
    

    def _is_platform_stack(self, tags):
        """
        Validate that the stack is part of the platform.
        """
        if config.PLATFORM_TAGS['VERSION'] in tags:
            LOGGER.debug('Found {} in tags'.format(config.PLATFORM_TAGS['VERSION']))
            return True
    

    def _is_requested_type(self, tags):
        """
        Validate that the stack is of the requested type.
        """
        LOGGER.debug('Validating type {} = {}:'.format(tags[config.PLATFORM_TAGS['TYPE']], self._stack_type))
        if self._stack_type == 'any':
            return True
        if tags[config.PLATFORM_TAGS['TYPE']] == self._stack_type:
            return True
    

    def _owned_by_group(self, tags):
        """
        Validate that the stack owned by the requesters groups.
        """
        LOGGER.debug('Validating owner {} = {}:'.format(tags[config.PLATFORM_TAGS['GROUPS']], self._groups))
        if tags[config.PLATFORM_TAGS['GROUPS']] == self._groups:
            return True


    def _get_exports(self):
        """ Gets the CloudFormation Exports in the region and returns
        a flat dict of key:value pairs

        Args:
        Basic Usage:
            >>> resp = get_exports()
        Returns:
            Dict: Dict of key:value pairs representing AWS output
            {
                'MyExportName': 'MyExportValue',
                'MyExportName2': 'MyExportValue2'
            }
        """
        cfn_exports = {}

        try:
            cfn_exports = self.client.list_exports()
        except Exception as ex:
            LOGGER.exception(ex)
            raise UnknownError from ex

        exports = {}
        for export in cfn_exports['Exports']:
            exports[export['Name']] = export['Value']

        return exports

    
    @abstractmethod
    def _generate_params(self, payload):
        """ ABC method instantiated in each child-class
        because of the uniqueness in each types parameters.
        """
        pass


    def _generate_tags(self, payload):
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
        tags = {}

        tags[config.PLATFORM_TAGS['TYPE']] = self._stack_type
        tags[config.PLATFORM_TAGS['SUBTYPE']] = payload['subtype']
        tags[config.PLATFORM_TAGS['VERSION']] = payload['version']
        tags[config.PLATFORM_TAGS['GROUPS']] = self._groups
        tags[config.PLATFORM_TAGS['REGION']] = config.PLATFORM_REGION
        tags[config.PLATFORM_TAGS['OWNER']] = self._user
        tags = tu.dict_to_kv(tags, 'Key', 'Value')

        return tags