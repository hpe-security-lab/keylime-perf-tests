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

import json

from datetime import datetime
from pathlib import Path

from perf_tests.attestation_task import DeserializedTask


class ResultSerializer:
    def __init__(self, file_path=None):
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            directory = Path("results")
            directory.mkdir(exist_ok=True)
            file_path = directory.joinpath(timestamp).with_suffix(".jsonl")
        else:
            file_path = Path(file_path)

            if not file_path.is_file():
                file_path = Path("results").joinpath(file_path)

            if not file_path.is_file():
                file_path = Path(file_path).with_suffix(".jsonl")

        self._file_path = file_path
        self._queued_tasks = set()

    def queue_task(self, task):
        self._queued_tasks.add(task)

    def write_tasks(self):
        with open(self.file_path, "a") as f:
            for task in self.queued_tasks:
                serialized_task = json.dumps(task.render())
                f.write(serialized_task + "\n")
                self._queued_tasks.remove(task)

    def read_tasks(self):
        if not self.file_path.is_file():
            raise ValueError(f"no file exists at {self.file_path}")

        tasks = []

        with open(self.file_path, "r") as f:
            for line in f:
                task_data = json.loads(line)
                tasks.append(DeserializedTask(task_data))

        return tasks
    
    @property
    def file_path(self):
        return self._file_path

    @property
    def queued_tasks(self):
        return self._queued_tasks.copy()




