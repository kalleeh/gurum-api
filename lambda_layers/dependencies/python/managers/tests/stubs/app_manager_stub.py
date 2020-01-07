# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Stubs for testing app_manager.py
"""

event = {
    'claims': {
        'email': 'test@company.com',
        'groups': 'team1',
        'roles': ''
    },
    'body-json': [
        {
            "name": "game-dev",
            "product_flavor": "ecs-fargate",
            "config": {
                "HealthCheckPath": "/",
                "DesiredCount": "2"
            },
            "env_vars": {
                "environment": "dev"
            }
        }
    ]
}

payload = {
    'name': 'game-dev',
    'product_flavor': 'ecs-fargate',
    'config': {
        'HealthCheckPath': '/',
        'DesiredCount': '2'
    },
    'env_vars': {
        'environment': 'dev'
    },
    'version': 'latest'
}

parameters = [
    {"ParameterKey": "HealthCheckPath", "ParameterValue": "Value"},
    {"ParameterKey": "DesiredCount", "UsePreviousValue": True},
    {"ParameterKey": "Priority", "UsePreviousValue": False},
]

random_priority_result = 3976

expected_parameters = [
    {
        'ParameterKey': 'HealthCheckPath',
        'ParameterValue': '/'
    },
    {
        'ParameterKey': 'DesiredCount',
        'ParameterValue': '2'
    },
    {
        'ParameterKey': 'Priority',
        'ParameterValue': '3976'
    }
]

ssm_params_result = {
    'api': {
        'api-endpoint': 'https://1119ffff08.execute-api.eu-west-1.amazonaws.com/v1/',
        'cognito-app-client-id': '5ll4gb12345ogeivq88dp7958g',
        'cognito-identity-pool-id': 'eu-west-1:bf5a53db-365f-1457-b217-83bd4ca3e542',
        'cognito-user-pool-id': 'eu-west-1_wRvq18x4w',
        'deployment-role-arn': 'arn:aws:iam::123456789012:role/gurum-api-DeploymentRole-VBU8ST34KEWB'
    },
    'platform': {
        'domain-name': 'gurum.cloud',
        'ecs': 'gurum-platform',
        'loadbalancer': {
            'dns-name': 'gurum-platform-1305888448.eu-west-1.elb.amazonaws.com',
            'security-group': 'sg-0471c505fa4750ab9',
            'hosted-zone-id': 'Z32O12XQLNTSW2',
            'listener-arn': 'arn:aws:elasticloadbalancing:eu-west-1:123456789012:listener/app/gurum-platform/4ee4cd0d1fc306f9/d20a70244b82ce4e'
        },
        'vpc': 'vpc-0575f2f02807bb855',
        'service-discovery': {
            'namespace': 'gurum.local',
            'namespace-id': 'ns-gxo3tfedk47kty7k'
        },
        'subnets': {
            'private': 'subnet-06330e4973647e3f3,subnet-06657956bfaf6e3f1',
            'public': 'subnet-0a7f03ebc30aee3f4,subnet-0633c7a866d14e3f2'
        }
    },
    'products': {
        'bucket': 'gurum-api-productsbucket-1fdk5gj3ewn64'
    }
}

existing_params = {}
