# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Stubs for testing stack_manager.py
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

update_stack_response = {
    'StackId': 'string'
}

template_summary = {
    'Parameters': [
        {
            'ParameterKey': 'Test',
            'DefaultValue': 'string',
            'ParameterType': 'string',
            'NoEcho': False,
            'Description': 'string',
            'ParameterConstraints': {
                'AllowedValues': [
                    'string',
                ]
            }
        },
        {
            'ParameterKey': 'Test2',
            'DefaultValue': 'string',
            'ParameterType': 'string',
            'NoEcho': False,
            'Description': 'string',
            'ParameterConstraints': {
                'AllowedValues': [
                    'string',
                ]
            }
        },
    ],
    'Description': 'string',
    'Capabilities': [
        'CAPABILITY_NAMED_IAM',
    ],
    'CapabilitiesReason': 'string',
    'ResourceTypes': [
        'string',
    ],
    'Version': 'string',
    'Metadata': 'string',
    'DeclaredTransforms': [
        'string',
    ],
    'ResourceIdentifierSummaries': [
        {
            'ResourceType': 'string',
            'LogicalResourceIds': [
                'string',
            ],
            'ResourceIdentifiers': [
                'string',
            ]
        },
    ]
}
