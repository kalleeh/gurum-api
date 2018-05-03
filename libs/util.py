def datetime_serialize(o):
    """ Serialize boto3 datetime response to JSON compatible format
    """
    if isinstance(o, datetime.datetime):
        return o.__str__()


def subdict(dict, keys):
    """ Dict modifier to only return selected keys
    Args:
        dict (dict): Dict to remove items from.
        keys (list): List of keys to save and return.
    """
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
    return PLATFORM_PREFIX + s


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
    if s.startswith(PLATFORM_PREFIX):
        return s[len(PLATFORM_PREFIX):]


def tags_to_dict(tags_list):
    """ Convert a boto3 list of resource tags to a flat dict of key:value pairs
    Args:
        tags_list (list): List of dicts representing AWS tags.
    Basic Usage:
        >>> tags_list = [{'Key': 'MyTagKey', 'Value': 'MyTagValue'}]
        >>> tags_to_dict(tags_list)
        [
            {
                'Key': 'MyTagKey',
                'Value': 'MyTagValue'
            }
        ]
    Returns:
        Dict: Dict of key:value pairs representing AWS tags
         {
            'MyTagKey': 'MyTagValue',
        }
    """

    tags_dict = {}
    for tag in tags_list:
        tags_dict[tag['Key']] = tag['Value']

    return tags_dict


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


def outputs_to_dict(outputs_list):
    """ Convert a boto3 list of stack outputs to a flat dict of key:value pairs
    Args:
        outputs_list (list): List of dicts representing AWS CloudFormation Outputs.
    Basic Usage:
        >>> outputs_list = [{'Key': 'MyOutputKey', 'Value': 'MyOutputValue'}]
        >>> outputs_to_dict(outputs_list)
        [
            {
                'OutputKey': 'MyOutputKey',
                'OutputValue': 'MyOutputValue'
            }
        ]
    Returns:
        Dict: Dict of key:value pairs representing AWS output
         {
            'MyOutputKey': 'MyOutputValue',
        }
    """

    outputs_dict = {}
    for output in outputs_list:
        outputs_dict[output['OutputKey']] = output['OutputValue']

    return outputs_dict

def response_formatter(status_code='400',
                      body={'message': 'error'},
                      cache_control='max-age=120,public',
                      content_type='application/json',
                      expires='',
                      etag='',
                      date='',
                      vary=False
                      ):

    api_response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': content_type
        }
    }

    if str(os.environ.get('ENABLE_CORS')).upper() == "YES":
        api_response['headers']['Access-Control-Allow-Origin'] = os.environ.get('CORS_ORIGIN')

    if int(status_code) != 200:
        api_response['body'] = json.dumps(body)
        api_response['Cache-Control'] = cache_control
    else:
        api_response['body'] = body
        api_response['isBase64Encoded'] = 'true'
        api_response['headers']['Expires'] = expires
        api_response['headers']['Etag'] = etag
        api_response['headers']['Cache-Control'] = cache_control
        api_response['headers']['Date'] = date
    if vary:
        api_response['headers']['Vary'] = vary
    logging.debug(api_response)
    return api_response