# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Stubs for testing elb_helper.py
"""

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

empty_rules = {
    "Rules": [
    ]
}
