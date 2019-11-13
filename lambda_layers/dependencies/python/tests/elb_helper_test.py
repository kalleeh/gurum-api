# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# pylint: skip-file

from pytest import raises, fixture
from unittest import mock

from datetime import datetime
import elb_helper
import random

listener_arn = 'arn:aws:elasticloadbalancing:eu-west-1:012345678901:listener/app/gurum-platform/4ee400231fc306f9/d20a7078382ce4e'
rules = {
    "Rules": [
        {
            "Priority": "2280"
        },
        {
            "Priority": "26934"
        }
    ]
}

@mock.patch('elb_helper.boto3.client')
def test_get_random_rule_priority(client):
    client().describe_rules.return_value = rules

    result = elb_helper.get_random_rule_priority(listener_arn)
    assert result >= 0 and result < 50000

@mock.patch('elb_helper.boto3.client')
def test_uniqueness(client):
    client().describe_rules.return_value = rules

    result1 = elb_helper.get_random_rule_priority(listener_arn)
    result2 = elb_helper.get_random_rule_priority(listener_arn)
    assert result1 != result2
