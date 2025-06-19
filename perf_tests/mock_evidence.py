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

from perf_tests.certification import *
from perf_tests.event_log import *


class MockTPMQuote(Certification):
    def __init__(self):
        self.evidence_type = "tpm_quote"
        self._set_capabilities()
        self._set_data()

    def _set_capabilities(self):
        attestation_key = CertificationKey(
            key_class = "asymmetric",
            key_algorithm = "rsa",
            key_size = 2048,
            server_identifier = "ak"
        )

        self.capabilities = CertificationCapabilities(
            component_version = "2.0",
            hash_algorithms = [ "sha256", "sha1" ],
            signature_schemes = [ "rsassa" ],
            available_subjects = {
                "sha1": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
                "sha256": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
            },
            certification_keys = [ attestation_key ]
        )

    def _set_data(self):
        subject_data = (
            "AQAAAAsAA///AQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwAAAAgAAAAgAC3cxiiWwb3dJKKzge0JHJiK"
            "LwGiqVsEtsPUBN25tdf5AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAP7ErT+kac4IevtZ8P4KYWDbqNCT3VOMBab+yIXNG+"
            "ywAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgANHzUtYtqVybhs47cdiuTWmZFeF8+Zf8HPzmx2Zou8VpAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAgAD1FjP5VzAPqH0Q/FWK+7I31HHXhSp/PmnI0oT8ZjnlpAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAgAKvos/pq7LNsL9k8b27d5mHCGzU9AHQQonOdab+n4bm+AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAPQexFad"
            "Crm+/XirWJafGQGdyZwfuT2T9egqIW9NQvfdAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAGPVCCQKlULigxIYYtt78HVqif"
            "j3TPZC1qKShcguFNxjAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAImEH1qasjDZTOWVkrFb2Dm1lefxjASmJ4q23DVXEsxa"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAIABpRSqT4KQWN0sh93YPCCEy0n7zi7uK+EEPaGAcDjVGOAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIACDCiZeiQ32aziYlEs/qFzTAD7q+qk5iRC5EQW2dpjBlAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAIAAKFEfDdVUHO2cLlAcueq9grOa9Mgp8gf6N7JoQKJuFyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAwb52LlPF9k9xufPj1x51lLrTGxNE94t3cJK9BbhPsrwAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAQAAACAAC8Qme3wDd7pKlPsu+wgL12NorW1NPtVGarc+cum8Ht8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
        )

        message = (
            "/1RDR4AYACIAC7s9pXY4dla3uHjUOVIJLQQ+VXb8+AhpubvOfxvMGB/aABRTYjd0Tmxxc2QzMnVJMVpQV3REcwAAAAFoGSAKAAAAKwAAAA"
            "ABAAECAAAAAAAAAAABAAsD//8BACA6FyLB7MLIIRkedpNB5VHSOHfXLsRkm1U74Y8eveoMKw=="
        )

        signature = (
            "ABQACwEACxh9sNgq3oYbq87obxRPA8v3tzwuBYLr53u1hz/iAaErnr5L+pHNvslCHXIm3SXDrpHdRp6GAO+1hR1w+VgQSaeN+4bsM0JO9k"
            "Ar/3ToKx0Q2bAMRnMANEBUlnFJfkAGyG/Ms4koGGhgcSrHkc8zjOiYDCdwj0DxavzF0MpG/OCrYgAup60f7YyxfzJ5QzYx72owBPPUfA+N"
            "1QuBfzGDBAzwt0+TdVa3udPCF4CLtZrDcUERAok29PmVX6EFhMfw7GmSFCSAmUqtPIvjva8K46ynBVYGsR1sfVY58eqL53C4XLSkG1+vS4"
            "NV5KnSyBRVzvs27FUWlJOJekk5mEvZxw=="
        )

        self.data = CertificationData(subject_data, message, signature)


class MockUEFILog(EventLog):
    file_contents = None

    def __init__(self):
        self.evidence_type = "uefi_log"
        self._set_capabilities()
        self._set_data()

    def _set_capabilities(self):
        self.capabilities = EventLogCapabilities(
            entry_count = 20,
            supports_partial_access = False, 
            appendable = False,
            formats = ["application/octet-stream"]
        )
    
    def _set_data(self):
        if not type(self).file_contents:
            with open("data/uefi_log.txt", "r") as f:
                type(self).file_contents = f.read()

        self.data = EventLogData(type(self).file_contents)


class MockIMALog(EventLog):
    file_contents = None

    def __init__(self):
        self.evidence_type = "ima_log"
        self._set_capabilities()
        self._set_data()

    def _set_capabilities(self):
        self.capabilities = EventLogCapabilities(
            entry_count = 20,
            supports_partial_access = True, 
            appendable = True,
            formats = ["text/plain"]
        )

    def _set_data(self):
        if not type(self).file_contents:
            with open("data/ima_log.txt", "r") as f:
                type(self).file_contents = f.read()

        self.data = EventLogData(type(self).file_contents)