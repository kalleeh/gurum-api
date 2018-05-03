import json
import datetime

"""
Apps API Definition

    URI: /apps
    Methods:
        GET - List all apps

    URI: /apps/{name}
    Methods:
        POST - Create new app
        GET - Get the details of app
        PATCH - Update the app
        DELETE - Delete the app
"""

# List apps
def list_apps():
    data = []
    apps = []

    app.log.debug('Listing Apps:')

    try:
        # List CloudFormation Stacks
        r = cfn.describe_stacks()
    except Exception as ex:
        logging.exception()
        raise ChaliceViewError('Failed to list apps')

    # Filter stacks based on owner and retrieve wanted keys
    keys = ['StackName']
    apps = filter_apps(r['Stacks'], keys)

    for i in apps:
        name = funclib.remprefix(i['StackName'])
        data.append({'name': name})

    response = json.dumps(data, default=funclib.datetime_serialize)

    return response


# Create new App
def create_app():
    data = {}

    request = app.current_request
    user = request.context['authorizer']['claims']['email']
    groups = request.context['authorizer']['claims']['cognito:groups']

    payload = request.json_body  # Get the user id for the request

    stack_name = funclib.addprefix(payload['name'])
    app.log.debug('Creating App: ' + stack_name)

    exports = get_cfn_exports()
    priority = str(iterate_rule_priority(exports['Listener']))

    # params['DesiredCount'] = payload['tasks']
    params['Priority'] = str(iterate_rule_priority(exports['Listener']))
    params['Listener'] = exports['Listener']
    # params['HealthCheckPath'] = payload['health_check_path']
    params = funclib.dict_to_kv(params, 'ParameterKey', 'ParameterValue')

    tags[PLATFORM_TAGS['TYPE']] = 'app'
    tags[PLATFORM_TAGS['VERSION']] = '0.1'
    tags[PLATFORM_TAGS['GROUPS']] = groups
    tags[PLATFORM_TAGS['REGION']] = PLATFORM_REGION
    tags[PLATFORM_TAGS['OWNER']] = user
    tags = funclib.dict_to_kv(tags, 'Key', 'Value')

    try:
        stack = cfn.create_stack(
            StackName=stack_name,
            TemplateURL='https://s3-eu-west-1.amazonaws.com/storage-kalleh/cfn/app/app.yaml',
            TimeoutInMinutes=15,
            Parameters=params,
            Capabilities=[
                'CAPABILITY_NAMED_IAM',
            ],
            RoleARN=PLATFORM_DEPLOYMENT_ROLE,
            Tags=tags
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            raise ChaliceViewError('An application with that name already exists.')
        else:
            print("Unexpected error: %s" % e)
    except Exception as ex:
        print(ex)
        logging.exception()
        raise ChaliceViewError('Internal server error.')

    response = json.dumps(stack, default=funclib.datetime_serialize)

    return response


# Describe App
def describe_app(name):
    apps = {}
    data = {}

    app.log.debug('Describing Stack:')
    stack_name = funclib.addprefix(name)

    # List CloudFormation Stacks
    try:
        r = cfn.describe_stacks(StackName=stack_name)
    except Exception as ex:
        logging.exception()
        raise ChaliceViewError('Internal server error.')

    # Filter stacks based on owner and retrieve wanted keys
    keys = ['StackName', 'Description', 'StackStatus', 'Tags', 'Outputs']
    try:
        apps = filter_apps(r['Stacks'], keys)
    except Exception as ex:
        print(ex)
        logging.exception()
        raise ChaliceViewError('Error while filtering stacks.')

    if 'Outputs' in apps[0]:
        outputs = funclib.outputs_to_dict(apps[0]['Outputs'])
        data['endpoint'] = outputs['Endpoint']
        if 'Repository' in outputs:
            data['repository'] = outputs['Repository']
    data['name'] = funclib.remprefix(apps[0]['StackName'])
    data['description'] = apps[0]['Description']
    data['status'] = apps[0]['StackStatus']
    data['tags'] = funclib.tags_to_dict(apps[0]['Tags'])

    response = json.dumps(data, default=funclib.datetime_serialize)

    return response


# Update App
def update_app(name):
    data = {}
    params = {}
    tags = {}

    request = app.current_request
    user = request.context['authorizer']['claims']['email']
    groups = request.context['authorizer']['claims']['cognito:groups']

    payload = json.loads(request.json_body)  # Get the user id for the request

    # Validate authorization
    if not describe_app(name):
        raise ChaliceViewError('You do not have permission to modify this resource.')

    stack_name = funclib.addprefix(name)
    app.log.debug('Updating App: ' + str(stack_name))

    params['DesiredCount'] = payload['tasks']
    # params['Priority'] = payload['priority']
    # params['Listener'] = payload['listener']
    # params['HealthCheckPath'] = payload['health_check_path']
    params = funclib.dict_to_kv(params, 'ParameterKey', 'ParameterValue')
    params.append(
        {
            "ParameterKey": 'Priority',
            "UsePreviousValue": True
        }
    )
    params.append(
        {
            "ParameterKey": 'Listener',
            "UsePreviousValue": True
        }
    )
    params.append(
        {
            "ParameterKey": 'HealthCheckPath',
            "UsePreviousValue": True
        }
    )

    tags[PLATFORM_TAGS['TYPE']] = 'app'
    tags[PLATFORM_TAGS['VERSION']] = '0.2'
    tags[PLATFORM_TAGS['GROUPS']] = groups
    tags[PLATFORM_TAGS['REGION']] = PLATFORM_REGION
    tags[PLATFORM_TAGS['OWNER']] = user
    tags = funclib.dict_to_kv(tags, 'Key', 'Value')

    try:
        stack = cfn.update_stack(
            StackName=stack_name,
            UsePreviousTemplate=True,
            Parameters=params,
            Capabilities=[
                'CAPABILITY_NAMED_IAM',
            ],
            RoleARN=PLATFORM_DEPLOYMENT_ROLE,
            Tags=tags
        )
    except ValidationError as e:
        raise ChaliceViewError('No updates are to be performed.')
    except Exception as ex:
        print(ex)
        logging.exception()
        raise ChaliceViewError('Internal server error.')

    response = json.dumps(stack, default=funclib.datetime_serialize)

    return response


# Delete App
def delete_app(name):
    data = {}
    stack_name = funclib.addprefix(name)
    app.log.debug('Deleting App: ' + stack_name)

    try:
        stack = cfn.delete_stack(StackName=stack_name)
    except Exception as ex:
        logging.exception()
        raise ChaliceViewError('Internal server error.')

    response = json.dumps(stack, default=funclib.datetime_serialize)

    return response

def handler(event, context):
    data = {
        'output': 'Hello ypu World',
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    return {'statusCode': 200,
            'body': json.dumps(data),
            'headers': {'Content-Type': 'application/json'}}