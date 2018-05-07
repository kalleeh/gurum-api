import os
import datetime
import logging

PLATFORM_PREFIX = os.getenv('PLATFORM_PREFIX', 'platform-')


def filter_stacks(stacks, keys, stack_type='any'):
    """ Filters a list of stacks validating they are stacks in the platform
    and belongs to the user performing the request and returns the chosen
    keys (arg) for those stacks.
    Args:
        stacks (list): List of dicts representing AWS CloudFormation Stacks.
        keys (list): List of keys representing the desired information to return.
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

    # Get the user id for the request
    request = app.current_request
    groups = request.context['authorizer']['claims']['cognito:groups']

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
                app.log.debug('Found stack {} with owner group: {}'.format(stack_name, groups))
                data.append(subdict(stack, keys))
            else:
                app.log.debug('{} does not belong to group: {}'.format(stack_name, groups))
        else:
            app.log.debug('Type is not {} for {}'.format(stack_type, stack_name))

    return data


def validate_auth(stack_name):
    """ Describes a stack validating they are in the platform
    and belongs to the user performing the request.
    Args:
        stack_name (string): Name of stack to check permissions for
    Basic Usage:
        >>> stack_name = 'my-stack'
        >>> validate_auth(stack_name)
    Returns:
        Bool: True/False
    """
    # Get the user id for the request
    request = app.current_request
    groups = request.context['authorizer']['claims']['cognito:groups']

    try:
        r = cfn.describe_stacks(StackName=stack_name)
    except Exception as ex:
        logging.exception(ex)
        raise ChaliceViewError('No such object.')
    
    # Loop through stacks
    for stack in r['Stacks']:
        stack_name = remprefix(stack['StackName'])
        stack_tags = kv_to_dict(stack['Tags'], 'Key', 'Value')

        # Check if the stack is part of the platform
        if (PLATFORM_TAGS['TYPE'] in stack_tags):
            # Check if stack belongs to group by comparing groups tag to the cognito group in claim
            if stack_tags[PLATFORM_TAGS['GROUPS']] == groups:
                app.log.debug('Authorization Successful: Stack {} owned by: {}'.format(stack_name, groups))
                return True
            else:
                app.log.debug('{} does not belong to group: {}'.format(stack_name, groups))
                raise ChaliceViewError('Permission denied.')
        else:
            app.log.debug('Stack {} does not have a platform type.'.format(stack_name))
            raise ChaliceViewError('No such object.')

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
        cfn_exports = cfn.list_exports()
    except Exception as ex:
        logging.exception(ex)
        raise ChaliceViewError('Internal server error.')

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
        raise ChaliceViewError('Internal server error.')

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
    Basic Usage:
        >>> my_dict = {'MyTagKey': 'MyTagValue'}
        >>> dict_to_kv(my_dict, 'Key', 'Value')
        {
            'MyKey': 'MyValue'
        }
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
    Convert a flat dict of key:value pairs representing AWS resource tags to a boto3 list of dicts
    Args:
        my_dict (dict): Dict representing AWS resource dict.
    Basic Usage:
        >>> my_dict = {'MyTagKey': 'MyTagValue'}
        >>> dict_to_kv(my_dict, 'Key', 'Value')
        {
            'MyKey': 'MyValue'
        }
    Returns:
        List: List of dicts containing tag keys and values
        [
            {
                'Key': 'MyTagKey',
                'Value': 'MyTagValue'
            }
        ]
    """
    my_dict = {}
    for item in my_list:
        my_dict[item[key_name]] = item[value_name]

    return my_dict