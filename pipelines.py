"""
Pipeline API Definition

    URI: /pipelines
    Methods:
        GET - List all pipelines

    URI: /pipelines/{name}
    Methods:
        POST - Create new pipeline
        GET - Get the details of app
        PATCH - Update the specified pipeline
        DELETE - Delete the pipeline
"""


# List pipelines
@app.route('/pipelines',
           authorizer=authorizer)
def list_pipelines():
    data = []
    pipelines = []

    app.log.debug('Listing Pipelines:')

    try:
        # List CloudFormation Stacks
        r = cfn.describe_stacks()
    except Exception as ex:
        logging.exception()
        raise ChaliceViewError('Failed to list pipelines')

    # Filter stacks based on owner and retrieve wanted keys
    keys = ['StackName']
    pipelines = filter_pipelines(r['Stacks'], keys)

    for i in pipelines:
        name = funclib.remprefix(i['StackName'])
        data.append({'name': name})

    response = json.dumps(data, default=funclib.datetime_serialize)

    return response


# Create new pipeline for app
@app.route('/pipelines/{name}',
           methods=['POST'],
           authorizer=authorizer)
def create_pipeline(name):
    data = {}

    request = app.current_request
    user = request.context['authorizer']['claims']['email']
    groups = request.context['authorizer']['claims']['cognito:groups']

    payload = json.loads(request.json_body)  # Get the user id for the request

    stack_name = funclib.addprefix(name) + '-pipeline'
    app.log.debug('Creating Pipeline: ' + stack_name)

    params['Service'] = funclib.addprefix(payload['app_name'])
    params['GitHubRepo'] = payload['github_repo']
    params['GitHubBranch'] = payload['github_branch']
    params['GitHubToken'] = payload['github_token']
    params['GitHubUser'] = payload['github_user']
    params = funclib.dict_to_kv(params, 'ParameterKey', 'ParameterValue')

    tags[PLATFORM_TAGS['TYPE']] = 'pipeline'
    tags[PLATFORM_TAGS['VERSION']] = '0.1'
    tags[PLATFORM_TAGS['GROUPS']] = groups
    tags[PLATFORM_TAGS['REGION']] = PLATFORM_REGION
    tags[PLATFORM_TAGS['OWNER']] = user
    tags = funclib.dict_to_kv(tags, 'Key', 'Value')

    try:
        stack = cfn.create_stack(
            StackName=stack_name,
            TemplateURL='https://s3-eu-west-1.amazonaws.com/storage-kalleh/cfn/app/pipeline.yaml',
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
            raise ChaliceViewError('A pipeline with that name already exists.')
        else:
            print("Unexpected error: %s" % e)
    except Exception as ex:
        print(ex)
        logging.exception()
        raise ChaliceViewError('Internal server error.')

    response = json.dumps(stack, default=funclib.datetime_serialize)

    return response


# Describe Pipeline
@app.route('/pipelines/{name}',
           authorizer=authorizer)
def describe_app(name):
    pipelines = {}
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
        pipelines = filter_pipelines(r['Stacks'], keys)
    except Exception as ex:
        print(ex)
        logging.exception()
        raise ChaliceViewError('Error while filtering stacks.')

    if 'Outputs' in pipelines[0]:
        outputs = funclib.outputs_to_dict(pipelines[0]['Outputs'])
        data['endpoint'] = outputs['Endpoint']
        if 'Repository' in outputs:
            data['repository'] = outputs['Repository']
    data['name'] = funclib.remprefix(pipelines[0]['StackName'])
    data['description'] = pipelines[0]['Description']
    data['status'] = pipelines[0]['StackStatus']
    data['tags'] = funclib.tags_to_dict(pipelines[0]['Tags'])

    response = json.dumps(data, default=funclib.datetime_serialize)

    return response


# Update new pipeline for App
@app.route('/pipelines/{name}',
           methods=['PATCH'],
           authorizer=authorizer)
def update_pipeline(name):
    data = {}

    request = app.current_request
    user = request.context['authorizer']['claims']['email']
    groups = request.context['authorizer']['claims']['cognito:groups']

    payload = json.loads(request.json_body)  # Get the user id for the request

    stack_name = funclib.addprefix(name) + '-pipeline'
    app.log.debug('Creating Pipeline: ' + stack_name)

    params['Service'] = funclib.addprefix(payload['app_name'])
    params['GitHubRepo'] = payload['github_repo']
    params['GitHubBranch'] = payload['github_branch']
    params['GitHubToken'] = payload['github_token']
    params['GitHubUser'] = payload['github_user']
    params = funclib.dict_to_kv(params, 'ParameterKey', 'ParameterValue')

    tags[PLATFORM_TAGS['TYPE']] = 'pipeline'
    tags[PLATFORM_TAGS['VERSION']] = '0.1'
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
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            raise ChaliceViewError('A pipeline with that name already exists.')
        else:
            print("Unexpected error: %s" % e)
    except Exception as ex:
        print(ex)
        logging.exception()
        raise ChaliceViewError('Internal server error.')

    response = json.dumps(stack, default=funclib.datetime_serialize)

    return response


# Delete pipeline
@app.route('/pipelines/{name}',
           methods=['DELETE'],
           authorizer=authorizer)
def delete_pipeline(name):
    data = {}
    stack_name = funclib.addprefix(name)
    app.log.debug('Deleting Pipeline: ' + stack_name)

    try:
        stack = cfn.delete_stack(StackName=stack_name)
    except Exception as ex:
        logging.exception()
        raise ChaliceViewError('Internal server error.')

    response = json.dumps(stack, default=funclib.datetime_serialize)

    return response