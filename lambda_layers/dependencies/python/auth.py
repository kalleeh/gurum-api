from aws_xray_sdk.core import patch_all
from logger import configure_logger

import platform_config
import transform_utils

patch_all()

LOGGER = configure_logger(__name__)


# Static dict for role and permission mapping
# Sets permission constant to grant permission based on role membership

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
        self._user, self._groups, self._roles = platform_config.get_user_context(event)
        self.required_permission = required_permission
        self.stack_type = stack_type

    def validate_permissions(self, tags):
        """
        First validate that the users roles give enough
        permissions to perform the requested action.
        """
        if self.required_permission not in self._get_permissions_from_roles():
            raise PermissionError('Permission denied.', 403)

        # Secondly validate that the tags on the stack
        # matches the users groups and that it's a part of the platform.

        if not self._tags_are_valid(tags, self.stack_type):
            raise PermissionError('Permission denied.', 403)

    def _tags_are_valid(self, tags, stack_type):
        stack_tags = transform_utils.kv_to_dict(tags, 'Key', 'Value')

        if not platform_config.PLATFORM_TAGS['PRODUCT_TYPE'] in stack_tags:
            return False

        if not stack_type == platform_config.PLATFORM_TAGS['PRODUCT_TYPE']:
            return False

        if stack_tags[platform_config.PLATFORM_TAGS['GROUPS']] == self._groups:
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
