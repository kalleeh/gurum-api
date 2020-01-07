# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# pylint: skip-file

from pytest import raises, fixture
from unittest import mock

from datetime import datetime
from managers.stack_manager import StackManager

from stubs import stack_manager_stub


def getTemplateSummaryMock():
    return mock.MagicMock(return_value=stack_manager_stub.template_summary)

# @mock.patch('managers.stack_manager.boto3.client')
# def test_update_stack(client):
#     stack_manager = StackManager(stack_manager_stub.event, 'app')
#     client().get_template_summary.return_value = stack_manager_stub.template_summary
#     client().update_stack.return_value = stack_manager_stub.update_stack_response

#     result = stack_manager.update_stack(stack_manager_stub.payload)
#     assert result >= 0 and result < 50000

@mock.patch('managers.stack_manager.boto3.client')
def test_get_existing_parameters(client):
    client().get_template_summary.return_value = stack_manager_stub.template_summary
    stack_manager = StackManager(stack_manager_stub.event, 'app')

    result = stack_manager._get_existing_parameters('gurum-game-dev')
    assert result == ['Test', 'Test2']
