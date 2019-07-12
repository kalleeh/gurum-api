# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# pylint: skip-file

from pytest import raises
from datetime import datetime
import transform_utils as tu


def test_datetime_serialize():
    result = tu.datetime_serialize(datetime(2015, 1, 1))
    assert result == "2015-01-01 00:00:00"


def test_datetime_serialize_incorrect_type():
    result = tu.datetime_serialize("I'm not a datetime instance.")
    assert result == "?"


def test_add_prefix():
    assert tu.add_prefix('MyApp') == "gureume-MyApp"


def test_add_prefix_no_string():
    with raises(TypeError):
        assert tu.add_prefix()
