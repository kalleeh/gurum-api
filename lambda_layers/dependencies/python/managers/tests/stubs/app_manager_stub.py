# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Stubs for testing app_manager.py
"""

event = {
    'claims': {
        'email': 'myuser@mycompany.com', 'groups': 'team1', 'roles': 'admin'
    },
    'body-json': [
        {
            "name": "coolgamesam-dev",
            "config": [
                {
                    "health_check_path": "/"
                },
                {
                    "tasks": "1"
                }
            ],
            "env_vars": [
                {
                    "environment": "prod"
                },
                {
                    "YourVar": "AnotherEnvVar"
                }
            ]
        }
    ]
}
