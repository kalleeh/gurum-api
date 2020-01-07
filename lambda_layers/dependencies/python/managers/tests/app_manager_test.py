# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# pylint: skip-file

from pytest import raises, fixture
from unittest import mock

from datetime import datetime
from managers.app_manager import AppManager

from stubs import app_manager_stub


def getNumberMock(number):
    return mock.MagicMock(return_value=number)

def getSSMParamsMock():
    return mock.MagicMock(return_value=app_manager_stub.ssm_params_result)

@mock.patch('managers.app_manager.elb_helper.get_random_rule_priority', getNumberMock(3976))
@mock.patch('managers.app_manager.ParameterStore.get_parameters', getSSMParamsMock())
def test_generate_parameters():
    app = AppManager(app_manager_stub.event)

    parameters = app._generate_params(app_manager_stub.payload)

    assert parameters == app_manager_stub.expected_parameters

@mock.patch('managers.app_manager.elb_helper.get_random_rule_priority', getNumberMock(3976))
@mock.patch('managers.app_manager.ParameterStore.get_parameters', getSSMParamsMock())
def test_generate_updated_parameters():
    app = AppManager(app_manager_stub.event)

    parameters = app._generate_params(
        app_manager_stub.payload,
        app_manager_stub.existing_params
    )

    assert parameters == app_manager_stub.expected_parameters
