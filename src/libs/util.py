import os
import datetime

PLATFORM_PREFIX = os.getenv('PLATFORM_PREFIX', 'platform-')


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