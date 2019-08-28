# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# pylint: skip-file

import os
import boto3

from exceptions import InvalidGurumManifest
from pytest import fixture, raises
from mock import Mock
from gurum_manifest import GurumManifest


@fixture
def cls():
    return GurumManifest(
        manifest_schema_path='{0}/../gurum_manifest_schema.yaml'.format(
            os.path.dirname(os.path.realpath(__file__))
        ),
        manifest_path='{0}/stubs/gurum_manifest_stub.yaml'.format(
            os.path.dirname(os.path.realpath(__file__))
        )
    )


def test_validate_schema(cls):
    assert cls._validate() is None


def test_validate_invalid_no_content(cls):
    cls.manifest_path = ''
    with raises(InvalidGurumManifest):
        cls._validate()


def test_validate_path_only(cls):
    cls.manifest_contents = {"environments": [{"targets": [{"path": "/something"}]}]}
    assert cls._validate() is None
