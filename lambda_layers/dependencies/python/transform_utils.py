"""
This is a sample, non-production-ready template.

© 2019 Amazon Web Services, In​c. or its affiliates. All Rights Reserved.

This AWS Content is provided subject to the terms of the
AWS Customer Agreement available at http://aws.amazon.com/agreement
or other written agreement between Customer and either
Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.
"""

import datetime
import json

from logger import configure_logger

LOGGER = configure_logger(__name__)


def respond(err, res=None):
    """ Function to correctly format HTTP responses

    Args:
        err (int|None): HTTP Response code to return, no value will
            generate a 200 OK response.
        res (string): Response message to include in body.
    """
    return {
        'body': res if err else json.dumps(res, default=datetime_serialize),
        'statusCode': err if err else '200',
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def datetime_serialize(o):
    """ Serialize boto3 datetime response to JSON compatible format
    """
    if isinstance(o, datetime.datetime):
        return o.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return '?'


def filter_dict(dict, keys):
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


def add_prefix(s):
    """ String modifier to add platform prefix to application names
    Args:
        s (string): String to add prefix to.
    Basic Usage:
        >>> app_name = "app-name"
        >>> add_prefix(app_name)
    Returns:
        (string): "platform-app-name"
    """
    # return PLATFORM_PREFIX + s
    return s


def remove_prefix(s):
    """ String modifier to remove platform prefix from application names
    Args:
        s (string): String to remove prefix from.
    Basic Usage:
        >>> prefixed_app_name = "platform-app-name"
        >>> remove_prefix(prefixed_app_name)
    Returns:
        (string): "app-name"
    """
    # if s.startswith(PLATFORM_PREFIX):
    #    return s[len(PLATFORM_PREFIX):]
    return s


def dict_to_kv(my_dict, key_name, value_name, clean=False):
    """
    Convert a flat dict of key:value pairs representing AWS resource tags to a boto3 list of dicts
    Args:
        my_dict (dict): Dict representing AWS resource dict.
        key_name (string): String of the key name that holds the key name.
        value_name (string): String of the key name that holds the value.
        clean (bool): If true, remove keys that have a None value.
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
        if clean and v == None:
            continue
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


def reuse_vals(key_names, key_type='param'):
    """
    Used for keys that are required to be passed to CloudFormation but you don't want to update.
    Takes the key type (param|tag) and appends the key name and sets key value to 'UsePreviousValue'.

    Args:
        key_name (list): List of key names to re-use (case-sensitive)
        key_type (param|tag): Defines the format for key name. Defaults to 'param'.
    Basic Usage:
        >>> params = tu.reuse_vals(params, ['Listener','Priority'])
    Returns:
        my_list (list): List representing AWS exitinsg keypairs with the new one appended.
        {
            "ParameterKey": 'ExistingKey',
            "ParameterValue": 'ExistingValue'
        },
        {
            "ParameterKey": 'Listener',
            "UsePreviousValue": True
        },
        {
            "ParameterKey": 'Priority',
            "UsePreviousValue": True
        }
    """
    my_list = []
    
    for key_name in key_names:
        my_list.append(
            {
                "ParameterKey": key_name,
                "UsePreviousValue": True
            }
        )

    return my_list


def build_nested_helper(path, value, container):
    """ Helper function for build_nested function """
    segs = path.split('/')
    head = segs[0]
    tail = segs[1:]

    if not tail:
        # found end of path, write value to key
        container[head] = value
    elif not head or 'gureume' in head:
        # don't create container if empty or is platform name
        build_nested_helper('/'.join(tail), value, container)
    else:
        if head not in container:
            container[head] = {}
        build_nested_helper('/'.join(tail), value, container[head])


def build_nested(paths):
    """ Function to build a python dict representing 
    a SSM parameter paths """
    container = {}

    for path, value in paths.items():
        build_nested_helper(path, value, container)
    
    return container
