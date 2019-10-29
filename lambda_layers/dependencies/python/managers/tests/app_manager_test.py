# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# pylint: skip-file

from pytest import raises, fixture
from unittest import mock

from stubs import app_manager_stub
from managers.app_manager import AppManager

event = app_manager_stub.event

payload = {
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

@mock.patch('managers.appmanager.parameter_store')
def test_parameter_generation(client):
    parameter_store().get_parameters.return_value = params

    expected_output = {
        "health_check_path": "/"
    },
    {
        "tasks": "1"
    }

    app = AppManager(event)
    params = app._generate_params(payload)

    assert params == expected_output
