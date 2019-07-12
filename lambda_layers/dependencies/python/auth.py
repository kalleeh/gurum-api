"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

from logger import configure_logger

import transform_utils as tu
import config

from aws_xray_sdk.core import patch_all

patch_all()

LOGGER = configure_logger(__name__)

"""
Static dict for role and permission mapping
Sets permission constant to grant permission based on role membership
"""
ROLE_PERMISSIONS = {}
ROLE_PERMISSIONS['owner'] = [
    'create',
    'read',
    'update',
    'delete',
    'transfer_ownership']
ROLE_PERMISSIONS['admin'] = [
    'create',
    'read',
    'update',
    'delete']
ROLE_PERMISSIONS['operator'] = [
    'read',
    'update']
ROLE_PERMISSIONS['read_only'] = [
    'read']

"""
Authentication Class
"""


class Auth:
    """ Class validating the user performing the request
        has permissions to perform the operation on the stack.
    Args:
        required_permission (string): Permission required to
            perform operation (read, write, admin, owner)
        stack_type (string): Optionally validates the stack
            type the operation is to be performed on.
    Basic Usage:
        >>> @authenticate_access('read','app')
        >>> my_decorated_function():
    """

    def __init__(self, event, required_permission, stack_type='any'):
        self._user, self._groups, self._roles = config.get_user_context(event)
        self.required_permission = required_permission
        self.stack_type = stack_type

    def validate_permissions(self, tags):
        """
        First validate that the users roles give enough
        permissions to perform the requested action.
        """
        if self.required_permission not in self._get_permissions_from_roles():
            raise PermissionError('Permission denied.', 403)

        """
        Secondly validate that the tags on the stack
        matches the users groups and that it's a part of the platform.
        """
        if not self._tags_are_valid(tags, self.stack_type):
            raise PermissionError('Permission denied.', 403)

    def _tags_are_valid(self, tags, stack_type):
        stack_tags = tu.kv_to_dict(tags, 'Key', 'Value')

        if not config.PLATFORM_TAGS['TYPE'] in stack_tags:
            return False

        if not stack_type == config.PLATFORM_TAGS['TYPE']:
            return False

        if stack_tags[config.PLATFORM_TAGS['GROUPS']] == self._groups:
            return True

        return False

    def _get_permissions_from_roles(self):
        """ Function to retrieve the permissions that a set of roles give.
        Args:
            roles (list): A list of roles that the function can map to.
        Basic Usage:
            >>> my_permissions = get_permissions_from_roles(['admin',
                    'operator'])
            >>> my_permissions['read','write']
        Returns:
            List: List of permissions granted by roles.
        """
        permissions = []

        try:
            for role in self._roles:
                LOGGER.debug(
                    'Member of Role: %s',
                    role)
                for permission in ROLE_PERMISSIONS[role]:
                    LOGGER.debug(
                        'Adding %s from role: %s',
                        permission,
                        role)
                    permissions.append(permission)
        except Exception:
            raise PermissionError(
                'Permission denied. Invalid role or role does not \
                    grant any permissions.',
                403)

        return permissions
