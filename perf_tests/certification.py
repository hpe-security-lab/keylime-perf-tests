# (C) Copyright 2024 Hewlett Packard Enterprise Development LP
# Author: Jean Snyman <jean.snyman@hpe.com>
# Author: Supreshna Gurung <supreshna.gurung@hpe.com>
# SPDX-License-Identifier: Apache-2.0

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


class Certification:
    def __init__(self, evidence_type):
        self.evidence_type = evidence_type
        self.capabilities = None
        self.data = None

    def render_supported(self):
        if not self.capabilities:
            return None

        return {
            "evidence_class": "certification",
            "evidence_type": self.evidence_type,
            "capabilities": self.capabilities.render()
        }

    def render_collected(self):
        if not self.data:
            return None

        return {
            "evidence_class": "certification",
            "evidence_type": self.evidence_type,
            "data": self.data.render()
        }


class CertificationCapabilities:
    def __init__(self, component_version, hash_algorithms, signature_schemes, available_subjects, certification_keys):
        self.component_version = component_version
        self.hash_algorithms = hash_algorithms
        self.signature_schemes = signature_schemes
        self.available_subjects = available_subjects
        self.certification_keys = certification_keys

    def render(self):
        return {
            "component_version": self.component_version,
            "hash_algorithms": self.hash_algorithms,
            "signature_schemes": self.signature_schemes,
            "available_subjects": self.available_subjects,
            "certification_keys": [ key.render() for key in self.certification_keys ]
        }

class CertificationKey:
    def __init__(self, key_class, key_algorithm, key_size, server_identifier):
        self.key_class = key_class
        self.key_algorithm = key_algorithm
        self.key_size = key_size
        self.server_identifier = server_identifier

    def render(self):
        return {
            "key_class": self.key_class,
            "key_algorithm": self.key_algorithm,
            "key_size": self.key_size,
            "server_identifier": self.server_identifier
        }

class CertificationData:
    def __init__(self, subject_data, message, signature):
        self.subject_data = subject_data
        self.message = message
        self.signature = signature

    def render(self):
        return {
            "subject_data": self.subject_data,
            "message": self.message,
            "signature": self.signature
        }