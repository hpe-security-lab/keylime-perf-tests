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

import ctypes

from multiprocessing import Value
from datetime import datetime, timezone

from perf_tests.attestation_task import AttestationTask


class Agent:
    def __init__(self, task_manager, index):
        self._task_manager = task_manager
        self._index = index
        self._busy = Value(ctypes.c_bool, False)
        self._task_count = Value(ctypes.c_int, 0)

    def _increment_task_count(self):
        with self._task_count.get_lock():
            self._task_count.value += 1

    def new_task(self, worker_index, evidence):
        if self.busy or self.finished:
            return None

        task = AttestationTask(worker_index, self, evidence)
        self._busy.value = True
        self._increment_task_count()
        return task

    def conclude_task(self, task):
        self._busy.value = False

    @property
    def task_manager(self):
        return self._task_manager

    @property
    def index(self):
        return self._index

    @property
    def id(self):
        return f"perf-test-agent-{self.index}"

    @property
    def busy(self):
        return self._busy.value

    @property
    def finished(self):
        if not self.task_manager.tasks_per_agent:
            return False
            
        return self.task_count >= self.task_manager.tasks_per_agent

    @property
    def task_count(self):
        return self._task_count.value

    @property
    def boot_time(self):
        return datetime.fromtimestamp(self._task_count.value, tz=timezone.utc).isoformat()
