import json

from transform_utils import datetime_serialize


def success(data, code=200):
    return {
        "body": prepareBody(data),
        "statusCode": code
    }


def error(data, code=500):
    raise Exception(json.dumps({
        "body": prepareBody(data),
        "statusCode": code
    }))


def prepareBody(data):
    return serializeDict(data) if isinstance(data, dict) else data


def serializeDict(obj):
    return json.dumps(obj, default=datetime_serialize)
