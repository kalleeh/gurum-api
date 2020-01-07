# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# pylint: skip-file

from pytest import raises, fixture
from unittest import mock

from datetime import datetime
import elb_helper
import random

from stubs import elb_helper_stub

@mock.patch('elb_helper.boto3.client')
def test_get_random_rule_priority(client):
    client().describe_rules.return_value = elb_helper_stub.rules

    result = elb_helper.get_random_rule_priority(elb_helper_stub.listener_arn)
    assert result >= 0 and result < 50000

@mock.patch('elb_helper.boto3.client')
def test_uniqueness(client):
    client().describe_rules.return_value = elb_helper_stub.rules

    result1 = elb_helper.get_random_rule_priority(elb_helper_stub.listener_arn)
    result2 = elb_helper.get_random_rule_priority(elb_helper_stub.listener_arn)
    assert result1 != result2

@mock.patch('elb_helper.boto3.client')
def test_no_existing_rules(client):
    client().describe_rules.return_value = elb_helper_stub.empty_rules

    result = elb_helper.get_random_rule_priority(elb_helper_stub.listener_arn)
    assert result > 1 and result < 50000
