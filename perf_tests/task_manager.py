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

from multiprocessing import Value, Array
from multiprocessing.sharedctypes import Synchronized
from datetime import datetime, timezone

from perf_tests.attestation_task import AttestationTask
from perf_tests.agent import Agent
from perf_tests.stats import GlobalStats
from perf_tests.result_serializer import ResultSerializer


class TaskManager:
    def __init__(self, execution):
        self._execution = execution

        self._new_tasks_allowed = Value(ctypes.c_bool, True)
        self._next_agent_index = Value(ctypes.c_int, 0)
        self._agents = []

        for i in range(execution.agent_count):
            self._agents.append(Agent(self, i))

        self._current_worker_tasks = set()
        self._stats = GlobalStats()
        self._serializer = ResultSerializer()

    def _increment_next_agent(self):
        with self._next_agent_index.get_lock():
            if self._next_agent_index.value < self.agent_count - 1:
                self._next_agent_index.value += 1
            else:
                self._next_agent_index.value = 0

    def new_task(self, worker_index, evidence):
        with self._next_agent_index.get_lock():
            if not self.new_tasks_allowed or self.all_finished:
                raise StopIteration

            if self.all_busy:
                return None

            # print("finding next available agent")
            # print(self.next_agent.busy)
            # print(self.next_agent.finished)
            # print(self.tasks_per_agent)

            while self.next_agent.busy or self.next_agent.finished:
                self._increment_next_agent()

            # print("agent index:", self.next_agent.index)
            # print("agent task count:", self.next_agent.task_count)

            task = self.next_agent.new_task(worker_index, evidence)
            self._increment_next_agent()
            self._current_worker_tasks.add(task)

        return task

    def conclude_task(self, task):
        self._current_worker_tasks.remove(task)
        self.serializer.queue_task(task)
        self.stats.record_task(task)

    def get_agent(self, index_or_id):
        if isinstance(index_or_id, str):
            index_or_id = int(index_or_id.split("perf-test-agent-")[-1])

        return self.agents[index_or_id]

    def disallow_new_tasks(self):
        self._new_tasks_allowed.value = False

    @property
    def execution(self):
        return self._execution

    @property
    def agents(self):
        return self._agents.copy()

    @property
    def agent_count(self):
        return len(self.agents)

    @property
    def tasks_per_agent(self):
        return self._execution.task_count

    @property
    def next_agent(self):
        return self.get_agent(self._next_agent_index.value)

    @property
    def new_tasks_allowed(self):
        return self._new_tasks_allowed.value

    @property
    def all_busy(self):
        return all(agent.busy for agent in self.agents)

    @property
    def all_finished(self):
        if not self.tasks_per_agent:
            return False
        
        return all(agent.finished for agent in self.agents)

    @property
    def current_worker_tasks(self):
        return self._current_worker_tasks.copy()

    @property
    def stats(self):
        return self._stats

    @property
    def serializer(self):
        return self._serializer