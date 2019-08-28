# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# pylint: skip-file

from pytest import raises
from datetime import datetime
import transform_utils

from stubs import transform_utils_stub


def test_datetime_serialize():
    result = transform_utils.datetime_serialize(datetime(2015, 1, 1))
    assert result == "2015-01-01 00:00:00"


def test_datetime_serialize_incorrect_type():
    result = transform_utils.datetime_serialize("I'm not a datetime instance.")
    assert result == "?"


def test_add_prefix():
    assert transform_utils.add_prefix('MyApp') == "gureume-MyApp"


def test_add_prefix_no_string():
    with raises(TypeError):
        assert transform_utils.add_prefix()


def test_remove_prefix():
    assert transform_utils.remove_prefix('gureume-MyApp') == "MyApp"


def test_remove_prefix_no_string():
    with raises(TypeError):
        assert transform_utils.remove_prefix()


def test_dict_to_kv():
    assert transform_utils.dict_to_kv(
        dict_to_expand=transform_utils_stub.compact_tags,
        key_name='Key',
        value_name='Value',
        clean=False) \
        == transform_utils_stub.expanded_tags
