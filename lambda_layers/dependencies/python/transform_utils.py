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

import config

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

    return '?'


def filter_dict(dict_to_filter, keys_to_save):
    """ Dict modifier to only return selected keys
    """
    # Create an empty key if requested key does not exist in dict
    for key in keys_to_save:
        if key not in dict_to_filter.keys():
            dict_to_filter[key] = ""

    return {key: dict_to_filter[key] for key in keys_to_save}


def add_prefix(string_to_add_prefix_to):
    """ String modifier to add platform prefix to application names
    """
    return config.PLATFORM_PREFIX + string_to_add_prefix_to
    # return string_to_add_prefix_to


def remove_prefix(string_to_remove_prefix_from):
    """ String modifier to remove platform prefix from application names
    """
    return_string = string_to_remove_prefix_from

    if string_to_remove_prefix_from.startswith(config.PLATFORM_PREFIX):
        return_string = string_to_remove_prefix_from[
            len(config.PLATFORM_PREFIX):]

    return return_string


def dict_to_kv(dict_to_expand, key_name, value_name, clean=False):
    """
    Convert a flat dict of key:value pairs representing AWS resource tags
    to a boto3 list of dicts.

    Basic Usage:
        >>> dict_to_expand = {'MyTagKey': 'MyTagValue'}
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
    list_to_return = []
    for k, v in dict_to_expand.items():
        if clean and v is None:
            continue
        list_to_return.append({key_name: k, value_name: v})

    return list_to_return


def kv_to_dict(list_to_flatten, key_name, value_name):
    """
    Convert boto3 list of dicts to a flat dict of key:value pairs
    representing AWS resource tags.

    Basic Usage:
        >>> list_to_flatten = [{ 'Key': 'MyTagKey', 'Value': 'MyTagValue' }]
        >>> dict_to_kv(my_list, 'Key', 'Value')
    Returns:
        my_dict (dict): Dict representing AWS resource dict.
        {
            'MyTagKey': 'MyTagValue'
        }
    """
    dict_to_return = {}
    for item in list_to_flatten:
        dict_to_return[item[key_name]] = item[value_name]

    return dict_to_return


def reuse_vals(key_names):
    """
    Used for keys that are required to be passed to CloudFormation but you
    don't want to update. Takes the key type (param|tag) and appends the
    key name and sets key value to 'UsePreviousValue'.

    Args:
        key_name (list): List of key names to re-use (case-sensitive)
        key_type (param|tag): Defines the format for key name.
            Defaults to 'param'.
    Basic Usage:
        >>> params = tu.reuse_vals(params, ['Listener','Priority'])
    Returns:
        my_list (list): List representing AWS exitinsg keypairs with the new
            one appended.
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
