"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from abc import ABCMeta, abstractmethod

from exceptions import AlreadyExists, InvalidInput, NoSuchObject, \
    PermissionDenied, InsufficientCapabilities, LimitExceeded, \
    UnknownParameter, UnknownError

import boto3
from botocore.exceptions import ValidationError, ClientError

from aws_xray_sdk.core import patch_all
from logger import configure_logger

import platform_config
import stack_validator
import template_generator
import transform_utils

patch_all()

LOGGER = configure_logger(__name__)


"""
CloudFormation Stack Manager
"""


class StackManager():
    __metaclass__ = ABCMeta

    def __init__(self, event, product_type):
        self.event = event
        self.client = boto3.client(
            'cloudformation',
            region_name=platform_config.PLATFORM_REGION)
        self._user, self._groups, self._roles = platform_config.get_user_context(
            self.event)
        self._params = platform_config.get_request_params(self.event)
        self._product_type = product_type

    def list_stacks(self, keys):
        """ List of stacks validating they are stacks in the platform
        and belongs to the user performing the request and returns the chosen
        keys (arg) for those stacks.

        Args:
            product_type (string): Filter based on stack type, valid options are
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
        LOGGER.debug('Listing stacks of type %s', self._product_type)

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
        """

        params = self._generate_params(payload)
        tags = self._generate_tags(payload)
        template_url = template_generator.generate_template_url(
            self._product_type,
            payload)

        LOGGER.debug('Creating stack: %s', stack_name)
        try:
            stack = self.client.create_stack(
                StackName=stack_name,
                TemplateURL=template_url,
                TimeoutInMinutes=15,
                Parameters=params,
                Capabilities=[
                    'CAPABILITY_NAMED_IAM',
                ],
                RoleARN=platform_config.PLATFORM_DEPLOYMENT_ROLE,
                Tags=tags
            )
        except self.client.exceptions.AlreadyExistsException as ex:
            LOGGER.exception(
                'Error: A stack with that name already exists.',
                exc_info=True)

            raise AlreadyExists from ex
        except self.client.exceptions.InsufficientCapabilitiesException as ex:
            LOGGER.exception(
                'Error: The template contains resources with capabilities \
                that weren\'t specified in the Capabilities parameter.',
                exc_info=True)

            raise InsufficientCapabilities from ex
        except self.client.exceptions.LimitExceededException as ex:
            LOGGER.exception(
                'Error: The quota for the resource has already been reached.',
                exc_info=True)

            raise LimitExceeded from ex
        except ClientError as e:
            LOGGER.exception(e)
            if e.response['Error']['Code'] == 'ValidationError' and \
                    'do not exist in the template' in e.response['Error']['Message']:
                raise UnknownParameter from e
        except Exception as ex:
            LOGGER.exception(
                'Unknown error.', exc_info=True)

            raise UnknownError from ex
        else:
            return stack

    def describe_stack(self):
        """ Describe a stack validating it is in the platform
        and belongs to the user performing the request.

        Basic Usage:
            >>> describe_stack('app')
        Returns:
            Dict: Dict representing AWS Stacks and information
            [
                {
                    'StackName': 'mystack',
                    'StackStatus': 'status'
                }
            ]
        """
        stack_name = transform_utils.add_prefix(self._params['name'])
        LOGGER.debug('Describing stack %s', stack_name)

        try:
            stacks = self.client.describe_stacks(StackName=stack_name)
        except Exception as ex:
            LOGGER.exception(
                'Unknown error.', exc_info=True)

            raise UnknownError from ex

        stacks = stacks['Stacks']
        stacks = self.filter_stacks(stacks)

        return stacks

    def update_stack(self, payload):
        """ Updates a CloudFormation stack.
        """
        stack_name = transform_utils.add_prefix(self._params['name'])
        LOGGER.debug(
            'Updating stack %s',
            stack_name)

        params = self._generate_params(payload)
        tags = self._generate_tags(payload)

        try:
            if payload['upgrade_version']:
                template_url = template_generator.generate_template_url(
                    self._product_type,
                    payload)

                stack = self.client.update_stack(
                    StackName=stack_name,
                    TemplateURL=template_url,
                    Parameters=params,
                    Capabilities=[
                        'CAPABILITY_NAMED_IAM',
                    ],
                    RoleARN=platform_config.PLATFORM_DEPLOYMENT_ROLE,
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
                    RoleARN=platform_config.PLATFORM_DEPLOYMENT_ROLE,
                    Tags=tags
                )
        except ClientError as e:
            LOGGER.exception(e)
            if e.response['Error']['Code'] == 'ValidationError' and \
                    'do not exist in the template' in e.response['Error']['Message']:
                raise UnknownParameter(e.response['Error']['Message'])
            if e.response['Error']['Code'] == 'ValidationError' and \
                    'does not exist' in e.response['Error']['Message']:
                raise NoSuchObject from e
            if e.response['Error']['Code'] == 'ValidationError' and \
                    'ROLLBACK_COMPLETE' in e.response['Error']['Message']:
                raise Exception(
                    'Stack is in inconsistent state. Please re-create it.')
        except self.client.exceptions.InsufficientCapabilitiesException as ex:
            LOGGER.debug(
                'Error: The template contains resources with capabilities \
                that weren\'t specified in the Capabilities parameter.')

            raise InsufficientCapabilities from ex
        except Exception as ex:
            LOGGER.exception(
                'Unknown Exception.',
                exc_info=True)
            raise UnknownError from ex
        else:
            return stack

    def delete_stack(self):
        """ Deletes a CloudFormation stack.
        """
        stack_name = transform_utils.add_prefix(self._params['name'])
        LOGGER.debug(
            'Deleting stack: %s',
            stack_name)

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
            LOGGER.exception(
                'Permission Denied.',
                exc_info=True)

            raise PermissionDenied
        except ValidationError as e:
            LOGGER.exception(
                'Invalid Input.',
                exc_info=True)

            raise InvalidInput from e
        except Exception as ex:
            LOGGER.exception(
                'Unknown Error.',
                exc_info=True)
            raise UnknownError from ex
        else:
            return True

    def filter_stacks(self, list_of_dicts_of_stacks):
        """ Filters a list of stacks validating they are stacks in the
        platform and belongs to the user performing the request.

        Basic Usage:
            >>> stacks = [
                    {
                        'StackId': '12314-392839-1321',
                        'StackName': 'mystack'
                    }
                ]
            >>> filter_stacks(stacks, keys, 'app')
        Returns:
            List: List of dicts representing AWS Stacks and information
            {
                'Stacks':
                [
                    {
                        'StackName': 'mystack',
                        'StackStatus': 'status',
                        ...
                    }
                ]
            ]
        """
        data = []

        try:
            for stack in list_of_dicts_of_stacks:
                stack_tags = transform_utils.kv_to_dict(stack['Tags'], 'Key', 'Value')
                LOGGER.debug('(filter_stacks) Evaluating Stack: %s', stack)

                if not stack_validator.is_part_of_platform(stack_tags):
                    LOGGER.debug(
                        '%s is not part of the platform.',
                        stack['StackName'])
                    continue
                if not self._is_requested_type(stack_tags):
                    LOGGER.debug(
                        '%s is not not the correct type (%s)',
                        stack['StackName'],
                        self._product_type)
                    continue
                if not stack_validator.is_owned_by_group(self._groups, stack_tags):
                    LOGGER.debug(
                        '%s is not owned by requester.',
                        stack['StackName'])
                    continue

                LOGGER.debug(
                    '%s passed checks. Adding to return data.',
                    stack['StackName'])
                data.append(stack)
        except Exception as ex:
            LOGGER.exception(ex)

            raise UnknownError from ex
        else:
            return data

    def filter_keys(self, list_of_dicts_of_stacks, list_of_keys_to_save):
        """ Filters a list of stacks and returns the chosen keys (arg) for
        those stacks.

        Basic Usage:
            >>> stacks = [
                    {
                        'StackId': '12314-392839-1321',
                        'StackName': 'mystack',
                        ...
                    }
                ]
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
            for stack in list_of_dicts_of_stacks:
                filtered_stack = {}

                for key in list_of_keys_to_save:
                    if key not in stack:
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
        LOGGER.debug('Validating permissions for: %s', stack_name)

        try:
            stacks = self.client.describe_stacks(StackName=stack_name)
        except ClientError as e:
            LOGGER.exception(e)

            if e.response['Error']['Code'] == 'ValidationError' and \
                    'does not exist' in e.response['Error']['Message']:
                return False
        except Exception as ex:
            LOGGER.exception(ex)
            LOGGER.debug('Unknown error occurred. Denying user permission to this resource.')
            return False
        else:
            stack = stacks['Stacks'][0]
            stack_tags = transform_utils.kv_to_dict(stack['Tags'], 'Key', 'Value')
            return stack_validator.is_owned_by_group(self._groups, stack_tags)

        return False

    def _is_requested_type(self, tags):
        """
        Validate that the stack is of the requested type.
        """
        LOGGER.debug(
            'Validating type %s is %s:',
            tags[platform_config.PLATFORM_TAGS['PRODUCT_TYPE']],
            self._product_type)
        return self._product_type == 'any' or \
            tags[platform_config.PLATFORM_TAGS['PRODUCT_TYPE']] == self._product_type

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
        LOGGER.debug(
            'Fetching platform Tags.')

        tags[platform_config.PLATFORM_TAGS['PRODUCT_TYPE']] = self._product_type
        tags[platform_config.PLATFORM_TAGS['PRODUCT_FLAVOR']] = payload['product_flavor']
        tags[platform_config.PLATFORM_TAGS['VERSION']] = payload['version']
        tags[platform_config.PLATFORM_TAGS['GROUPS']] = self._groups
        tags[platform_config.PLATFORM_TAGS['REGION']] = platform_config.PLATFORM_REGION
        tags[platform_config.PLATFORM_TAGS['OWNER']] = self._user
        tags = transform_utils.dict_to_kv(tags, 'Key', 'Value')

        LOGGER.debug(
            'Loaded Tags: %s ',
            tags)

        return tags
