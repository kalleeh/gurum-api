import os
import datetime
import logging
import boto3
import json

PLATFORM_PREFIX = os.getenv('PLATFORM_PREFIX', 'platform-')

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

PLATFORM_NAME = os.getenv('PLATFORM_NAME', 'platform')
PLATFORM_PREFIX = os.getenv('PLATFORM_PREFIX', 'platform-')
PLATFORM_REGION = os.getenv('PLATFORM_REGION', 'eu-west-1')
PLATFORM_ECS_CLUSTER = os.getenv('PLATFORM_ECS_CLUSTER', PLATFORM_PREFIX + 'cluster')
PLATFORM_DEPLOYMENT_ROLE = os.getenv('PLATFORM_DEPLOYMENT_ROLE', 'deployment_role')
# Tags for the platform
PLATFORM_TAGS = {}
PLATFORM_TAGS['TYPE'] = os.getenv('PLATFORM_TAGS_TYPE', PLATFORM_PREFIX + 'platform-type')
PLATFORM_TAGS['VERSION'] = os.getenv('PLATFORM_TAGS_VERSION', PLATFORM_PREFIX + 'platform-version')
PLATFORM_TAGS['OWNER'] = os.getenv('PLATFORM_TAGS_OWNER', PLATFORM_PREFIX + 'owner')
PLATFORM_TAGS['REGION'] = os.getenv('PLATFORM_TAGS_REGION', PLATFORM_PREFIX + 'region')
PLATFORM_TAGS['GROUPS'] = os.getenv('PLATFORM_TAGS_GROUPS', PLATFORM_PREFIX + 'groups')

# Create CloudFormation Client
CFN_CLIENT = boto3.client('cloudformation', region_name=PLATFORM_REGION)


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res, default=datetime_serialize),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def filter_stacks(stacks, keys, groups, stack_type='any'):
    """ Filters a list of stacks validating they are stacks in the platform
    and belongs to the user performing the request and returns the chosen
    keys (arg) for those stacks.
    Args:
        stacks (list): List of dicts representing AWS CloudFormation Stacks.
        keys (list): List of keys representing the desired information to return.
        groups (string): The name of the group that the authenticated request belongs to.
        stack_type (string): Filter based on stack type, valid options are
            'app','pipeline' or 'any'
    Basic Usage:
        >>> stacks = [{'StackId': '12314-392839-1321', 'StackName': 'mystack'} ...]
        >>> keys = ['StackName','StackStatus']
        >>> filter_stacks(stacks, keys, 'app')
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

    # Loop through stacks
    for stack in stacks:
        stack_name = remprefix(stack['StackName'])
        stack_tags = kv_to_dict(stack['Tags'], 'Key', 'Value')

        # Check if the stack is a platform app, has a type requirement and if so, has the right type
        if (PLATFORM_TAGS['TYPE'] in stack_tags) and (stack_tags[PLATFORM_TAGS['TYPE']] == stack_type) or (stack_type == 'any'):
            # Check if stack has outputs, else remove from keys to avoid key error
            if 'Outputs' not in stack:
                if 'Outputs' in keys:
                    keys.remove('Outputs')
            # Check if app belongs to group by comparing groups tag to the cognito group in claim
            if stack_tags[PLATFORM_TAGS['GROUPS']] == groups:
                LOGGER.debug('Found stack {} with owner group: {}'.format(stack_name, groups))
                data.append(subdict(stack, keys))
            else:
                LOGGER.debug('{} does not belong to group: {}'.format(stack_name, groups))
        else:
            LOGGER.debug('Type is not {} for {}'.format(stack_type, stack_name))

    return data


def validate_auth(stack_name, groups):
    """ Describes a stack validating they are in the platform
    and belongs to the user performing the request.
    Args:
        stack_name (string): Name of stack to check permissions for
        groups (string): The name of the group that the authenticated request belongs to
    Basic Usage:
        >>> stack_name = 'my-stack'
        >>> validate_auth(stack_name, "administrators")
    Returns:
        Bool: True/False
    """

    try:
        r = CFN_CLIENT.describe_stacks(StackName=stack_name)
    except Exception as ex:
        logging.exception(ex)
        raise('No such object.')
    
    # Loop through stacks
    for stack in r['Stacks']:
        stack_name = remprefix(stack['StackName'])
        stack_tags = kv_to_dict(stack['Tags'], 'Key', 'Value')

        # Check if the stack is part of the platform
        if (PLATFORM_TAGS['TYPE'] in stack_tags):
            # Check if stack belongs to group by comparing groups tag to the cognito group in claim
            if stack_tags[PLATFORM_TAGS['GROUPS']] == groups:
                LOGGER.debug('Authorization Successful: Stack {} owned by: {}'.format(stack_name, groups))
                return True
            else:
                LOGGER.debug('{} does not belong to group: {}'.format(stack_name, groups))
                raise('Permission denied.')
        else:
            LOGGER.debug('Stack {} does not have a platform type.'.format(stack_name))
            raise('No such object.')

    return False


def get_cfn_exports():
    """ Gets the CloudFormation Exports in the region and returns a flat dict of key:value pairs
    Args:
    Basic Usage:
        >>> r = get_cfn_exports()
    Returns:
        Dict: Dict of key:value pairs representing AWS output
        {
            'MyExportName': 'MyExportValue',
            'MyExportName2': 'MyExportValue2'
        }
    """
    cfn_exports = {}

    try:
        cfn_exports = CFN_CLIENT.list_exports()
    except Exception as ex:
        logging.exception(ex)
        raise('Internal server error.')

    exports = {}
    for export in cfn_exports['Exports']:
        exports[export['Name']] = export['Value']

    return exports


def iterate_rule_priority(listener_arn):
    """ Returns the next rule priority number for a given ALB Listener Arn
    Args:
        listener_arn (string): String of the ARN to the ALB Listener
    Basic Usage:
        >>> r = iterate_rule_priority(listener_arn)
    Returns:
        Number: Number of the next available rule priority number
        Default: 1
    """
    client = boto3.client('elbv2', region_name=PLATFORM_REGION)
    rules = {}

    try:
        rules = client.describe_rules(
            ListenerArn=listener_arn,
        )['Rules']
    except Exception as ex:
        logging.exception(ex)
        raise('Internal server error.')

    rules = [rule for rule in rules if rule['Priority'].isdigit()]

    if not rules:
        return 1

    sorted_rules = sorted(rules, key=lambda x: int(x['Priority']), reverse=True)
    priority = int(sorted_rules[0]['Priority'])+1

    return priority


def datetime_serialize(o):
    """ Serialize boto3 datetime response to JSON compatible format
    """
    if isinstance(o, datetime.datetime):
        return o.strftime('%Y-%m-%d %H:%M:%S')


def subdict(dict, keys):
    """ Dict modifier to only return selected keys
    Args:
        dict (dict): Dict to remove items from.
        keys (list): List of keys to save and return.
    """
    
    # Create an empty key if requested key does not exist in dict
    for key in keys:
        if not key in dict.keys():
            dict[key] = ""
    
    return {key: dict[key] for key in keys}


def addprefix(s):
    """ String modifier to add platform prefix to application names
    Args:
        s (string): String to add prefix to.
    Basic Usage:
        >>> app_name = "app-name"
        >>> addprefix(app_name)
    Returns:
        (string): "platform-app-name"
    """
    # return PLATFORM_PREFIX + s
    return s


def remprefix(s):
    """ String modifier to remove platform prefix from application names
    Args:
        s (string): String to remove prefix from.
    Basic Usage:
        >>> prefixed_app_name = "platform-app-name"
        >>> remprefix(prefixed_app_name)
    Returns:
        (string): "app-name"
    """
    # if s.startswith(PLATFORM_PREFIX):
    #    return s[len(PLATFORM_PREFIX):]
    return s


def dict_to_kv(my_dict, key_name, value_name):
    """
    Convert a flat dict of key:value pairs representing AWS resource tags to a boto3 list of dicts
    Args:
        my_dict (dict): Dict representing AWS resource dict.
        key_name (string): String of the key name that holds the key name.
        value_name (string): String of the key name that holds the value.
    Basic Usage:
        >>> my_dict = {'MyTagKey': 'MyTagValue'}
        >>> dict_to_kv(my_dict, 'Key', 'Value')
    Returns:
        List: List of dicts containing tag keys and values
        [
            {
                'Key': 'MyTagKey',
                'Value': 'MyTagValue'
            }
        ]
    """

    my_list = []
    for k, v in my_dict.items():
        my_list.append({key_name: k, value_name: v})

    return my_list


def kv_to_dict(my_list, key_name, value_name):
    """
    Convert boto3 list of dicts to a flat dict of key:value pairs representing AWS resource tags
    Args:
        my_list (list): List of dicts containing tag keys and values.
        key_name (string): String of the key name that holds the key name.
        value_name (string): String of the key name that holds the value.
    Basic Usage:
        >>> my_list = [{ 'Key': 'MyTagKey', 'Value': 'MyTagValue' }]
        >>> dict_to_kv(my_list, 'Key', 'Value')
    Returns:
        my_dict (dict): Dict representing AWS resource dict.
        {
            'MyTagKey': 'MyTagValue'
        }
    """
    my_dict = {}
    for item in my_list:
        my_dict[item[key_name]] = item[value_name]

    return my_dict


def boto_exception(err):
    """
    generic error message handler
    """
    if hasattr(err, 'error_message'):
        error = err.error_message
    elif hasattr(err, 'message'):
        error = err.message + ' ' + str(err) + ' - ' + str(type(err))
    else:
        error = '%s: %s' % (Exception, err)

    return error