# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Module used for working with the Service Manifest file.
"""

import os

from exceptions import InvalidGurumManifest

import yaml
import yamale

from logger import configure_logger
LOGGER = configure_logger(__name__)


class GurumManifest:
    def __init__(
            self,
            manifest_schema_path,
            manifest_path=None
    ):
        self.manifest_path = manifest_path or 'gurum.yaml'
        self.manifest_dir_path = manifest_path or 'gurum_manifest'
        self.manifest_schema_path = manifest_schema_path or 'gurum_manifest_schema.yaml'
        self._get_all()
        self.account_ou_names = {}
        self._validate()

    def _read(self, file_path=None):
        if file_path is None:
            file_path = self.manifest_path
        try:
            LOGGER.info('Loading service_manifest file %s', file_path)
            with open(file_path, 'r') as stream:
                return yaml.load(stream, Loader=yaml.FullLoader)
        except FileNotFoundError:
            LOGGER.info('No manifest file found at %s, continuing', file_path)
            return {}

    def determine_extend_map(self, service_manifest):
        if service_manifest.get('environments'):
            self.manifest_contents['environments'].extend(service_manifest['environments'])

    def _get_all(self):
        self.manifest_contents = {}
        self.manifest_contents['environments'] = []
        if os.path.isdir(self.manifest_dir_path):
            for file in os.listdir(self.manifest_dir_path):
                if file.endswith(".yaml") and file != 'example-gurum.yaml':
                    self.determine_extend_map(
                        self._read('{0}/{1}'.format(self.manifest_dir_path, file))
                    )
        self.determine_extend_map(
            self._read()  # Calling with default no args to get service.yaml in root if it exists
        )
        if not self.manifest_contents['environments']:
            raise InvalidGurumManifest("No manifest files found..")

    def _validate(self):
        """
        Validates the deployment map contains valid configuration
        """
        try:
            schema = yamale.make_schema(self.manifest_schema_path)
            data = yamale.make_data(self.manifest_path)

            yamale.validate(schema, data)
        except ValueError:
            raise InvalidGurumManifest(
                "Deployment Map target or regions specification is invalid"
            )
        except KeyError:
            raise InvalidGurumManifest(
                "Deployment Map target or regions specification is invalid"
            )
        except FileNotFoundError:
            raise InvalidGurumManifest(
                "No Service Map files found, create a service.yaml file."
            )
