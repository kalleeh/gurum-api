# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# pylint: skip-file

import os
import boto3

from exceptions import InvalidServiceManifest
from pytest import fixture, raises
from mock import Mock
from service_manifest import ServiceManifest


@fixture
def cls():
    return ServiceManifest(
        manifest_schema_path='{0}/../service_manifest_schema.yaml'.format(
            os.path.dirname(os.path.realpath(__file__))
        ),
        manifest_path='{0}/stubs/service_manifest_stub.yaml'.format(
            os.path.dirname(os.path.realpath(__file__))
        )
    )


def test_validate_schema(cls):
    assert cls._validate() is None


def test_validate_invalid_no_content(cls):
    cls.manifest_path = ''
    with raises(InvalidServiceManifest):
        cls._validate()


def test_validate_path_only(cls):
    cls.manifest_contents = {"environments": [{"targets": [{"path": "/something"}]}]}
    assert cls._validate() is None
