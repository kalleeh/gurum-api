# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# pylint: skip-file

from pytest import fixture
import datetime
import response_builder


def test_success_with_string_param():
    expected_response = {
        'body': 'Woo!',
        'headers': {'Content-Type': 'application/json'},
        'statusCode': 200
    }

    response = response_builder.success('Woo!')

    assert response == expected_response
