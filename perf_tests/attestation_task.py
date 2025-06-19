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

import asyncio

from perf_tests.request_attempt import RequestAttempt, DeserializedAttempt


class AttestationTask:
    def __init__(self, worker_index, agent, evidence):
        self._worker_index = worker_index
        self._agent = agent
        self._index = agent.task_count
        self._evidence = evidence.copy()

        self._asyncio_task = None
        self._create_attempts = []
        self._update_attempts = []

    async def _new_create_attempt(self):
        url = f"{self.task_manager.execution.verifier_url}/v3.0/agents/{self.agent.id}/attestations"
        req_attempt = RequestAttempt(self, "POST", url)
        req_attempt.set_body({
            "evidence_supported": [ item.render_supported() for item in self.evidence ],
            "system_info": {
                "boot_time": self.agent.boot_time
            }
        })
        self._create_attempts.append(req_attempt)
        return await req_attempt.perform()

    async def _new_update_attempt(self):
        url = f"{self.task_manager.execution.verifier_url}/v3.0/agents/{self.agent.id}/attestations/{self.index}"
        req_attempt = RequestAttempt(self, "PATCH", url)
        req_attempt.set_body({
            "evidence_collected": [ item.render_collected() for item in self.evidence ]
        })
        self._update_attempts.append(req_attempt)
        return await req_attempt.perform()

    async def execute(self):
        while True:
            create_attempt = await self._new_create_attempt()

            if create_attempt.retry_after:
                await asyncio.sleep(create_attempt.retry_after)
                continue

            if not create_attempt.ok:
                return False

            break

        while True:
            update_attempt = await self._new_update_attempt()

            if update_attempt.retry_after:
                await asyncio.sleep(update_attempt.retry_after)
                continue

            if not update_attempt.ok:
                return False

            break

        return True

    async def result(self):
        await self._asyncio_task

    def start_async(self):
        # self.task_manager.stats.start_tracking()
        self._asyncio_task = asyncio.create_task(self.execute())
        self._asyncio_task.add_done_callback(self.conclude)
        return self._asyncio_task

    def conclude(self, *args):
        # print(f"Task {self.index} for {self.agent.id} finished")
        self.task_manager.conclude_task(self)
        self.agent.conclude_task(self)

    def render(self):
        return {
            "agent_index": self.agent.index,
            "task_index": self.index,
            "worker_index": self.worker_index,
            "create_successful": self.create_successful,
            "update_successful": self.update_successful,
            "create_duration": self.create_duration,
            "update_duration": self.update_duration,
            "create_attempts": [ create_attempt.render() for create_attempt in self.create_attempts ],
            "update_attempts": [ update_attempt.render() for update_attempt in self.update_attempts ]
        }

    @property
    def worker_index(self):
        return self._worker_index

    @property
    def agent(self):
        return self._agent

    @property
    def agent_index(self):
        return self.agent.index
    
    @property
    def index(self):
        return self._index

    @property
    def evidence(self):
        return self._evidence

    @property
    def task_manager(self):
        return self.agent.task_manager

    @property
    def verifier_url(self):
        return self.task_manager.verifier_url

    @property
    def create_attempts(self):
        return self._create_attempts.copy()

    @property
    def update_attempts(self):
        return self._update_attempts.copy()

    @property
    def create_successful(self):
        if not self.create_attempts:
            return False

        return self.create_attempts[-1].ok

    @property
    def update_successful(self):
        if not self.update_attempts:
            return False

        return self.update_attempts[-1].ok

    @property
    def create_duration(self):
        duration = 0.0

        for create_attempt in self.create_attempts:
            if create_attempt.duration:
                duration += create_attempt.duration

        return duration

    @property
    def update_duration(self):
        duration = 0.0

        for update_attempt in self.update_attempts:
            if update_attempt.duration:
                duration += update_attempt.duration

        return duration

    @property
    def total_duration(self):
        return self.create_duration + self.update_duration

    @property
    def start_time(self):
        if not self.create_attempts:
            return None

        return self.create_attempts[0].start_time

    @property
    def end_time(self):
        if not self.create_attempts:
            return None

        if self.update_attempts:
            return self.update_attempts[-1].end_time
        else:
            return self.create_attempts[-1].end_time


class DeserializedTask(AttestationTask):
    def __init__(self, data):
        self._worker_index = data.get("worker_index")
        self._agent = None
        self._agent_index = data.get("agent_index")
        self._index = data.get("task_index")
        self._evidence = []

        self._asyncio_task = None
        self._create_attempts = [DeserializedAttempt(self, create_data) for create_data in data["create_attempts"]]
        self._update_attempts = [DeserializedAttempt(self, update_data) for update_data in data["update_attempts"]]

    @property
    def agent_index(self):
        return self._agent_index