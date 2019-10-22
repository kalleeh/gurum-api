# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# pylint: skip-file

from pytest import raises
from datetime import datetime
import elb_helper
import random

listener_arn = 'arn:aws:elasticloadbalancing:eu-west-1:789073296014:listener/app/gurum-platform/4ee4cd0d1fc306f9/d20a70244b82ce4e'

def test_get_random_rule_priority():
    result = elb_helper.get_random_rule_priority(listener_arn)
    assert result >= 0 and result < 50000

def test_uniqueness():
    result1 = elb_helper.get_random_rule_priority(listener_arn)
    result2 = elb_helper.get_random_rule_priority(listener_arn)
    assert result1 != result2
