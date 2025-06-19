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

class EventLog:
    def __init__(self, evidence_type, entries):
        self.evidence_type = evidence_type
        self.capabilities = None
        self.data = None

    def render_supported(self):
        if not self.capabilities:
            return None

        return {
            "evidence_class": "log",
            "evidence_type": self.evidence_type,
            "capabilities": self.capabilities.render()
        }

    def render_collected(self):
        if not self.data:
            return None

        return {
            "evidence_class": "log",
            "evidence_type": self.evidence_type,
            "data": self.data.render()
        }


class EventLogCapabilities:
    def __init__(self, entry_count, supports_partial_access = False, appendable = False, formats = None):
        self.entry_count = entry_count
        self.supports_partial_access = supports_partial_access
        self.appendable = appendable
        self.formats = formats
        
        if not formats:
            self.formats = []
            self.formats.append("text/plain")

    def render(self):
        output = {
            "entry_count": self.entry_count,
            "formats": self.formats
        }

        if self.supports_partial_access:
            output["supports_partial_access"] = True

        if self.appendable:
            output["appendable"] = True

        return output


class EventLogData:
    def __init__(self, entries):
        self.entries = entries

    def render(self):
        return {
            "entries": self.entries
        }