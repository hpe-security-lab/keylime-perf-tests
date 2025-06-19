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
import time
import datetime

from multiprocessing import Value

from perf_tests.output import OutputHelpers, Table, ColumnGroup


class GlobalStats:
    def __init__(self):
        self._create_requests = RequestStats()
        self._create_phases = ProtocolStats()
        self._update_requests = RequestStats()
        self._update_phases = ProtocolStats()
        self._full_protocol_runs = ProtocolStats()

        self._start_time = Value(ctypes.c_double, 0.0)
        self._end_time = Value(ctypes.c_double, 0.0)
        self._worker_count = Value(ctypes.c_int, 0)
        self._agent_count = Value(ctypes.c_int, 0)

    def update_start_time(self, start_time):
        if not start_time:
            return

        with self._start_time.get_lock():
            if self._start_time.value == 0 or start_time < self._start_time.value:
                self._start_time.value = start_time

    def update_end_time(self, end_time):
        if not end_time:
            return

        with self._end_time.get_lock():
            if self._end_time.value == 0 or end_time > self._end_time.value:
                self._end_time.value = end_time

    def update_worker_count(self, worker_count):
        if not worker_count:
            return

        with self._worker_count.get_lock():
            if worker_count > self._worker_count.value:
                self._worker_count.value = worker_count

    def update_agent_count(self, agent_count):
        if not agent_count:
            return

        with self._agent_count.get_lock():
            if agent_count > self._agent_count.value:
                self._agent_count.value = agent_count

    def record_task(self, task):
        self.update_start_time(task.start_time)
        self.update_end_time(task.end_time)
        self.update_worker_count(task.worker_index + 1)
        self.update_agent_count(task.agent_index + 1)

        # print(f"Recorded task started at {task.start_time} and finished at {task.end_time}")
        # print("Overall start time:", self._start_time.value)
        # print("Overall end time:", self._end_time.value)
        
        if task.create_successful:
            self.create_phases.success.record(task.create_duration)
        else:
            self.create_phases.fail.record(task.create_duration)

        if task.update_successful:
            self.update_phases.success.record(task.update_duration)
            self.full_protocol_runs.success.record(task.total_duration)
        else:
            self.update_phases.fail.record(task.update_duration)
            self.full_protocol_runs.fail.record(task.total_duration)

        for create_attempt in task.create_attempts:
            if create_attempt.ok:
                self.create_requests.ok.record(create_attempt.duration)
            elif create_attempt.retry_after:
                self.create_requests.retry.record(create_attempt.duration)
            else:
                self.create_requests.fail.record(create_attempt.duration)

        for update_attempt in task.update_attempts:
            if update_attempt.ok:
                self.update_requests.ok.record(update_attempt.duration)
            elif update_attempt.retry_after:
                self.update_requests.retry.record(update_attempt.duration)
            else:
                self.update_requests.fail.record(update_attempt.duration)

    def print_all(self):
        print("\n")
        print("\u001b[40;1m" + ("─" * 105) + "\u001b[0m")
        print("\u001b[40;1m" + OutputHelpers.center("TEST RESULT SUMMARY", 105) + "\u001b[0m")
        print("\u001b[40;1m" + ("═" * 105) + "\u001b[0m")

        friendly_duration = str(datetime.timedelta(seconds = round(self.track_duration, 0)))
        seconds = f"({round(self.track_duration, 1)}s)" if self.track_duration > 60 else ""

        print(f"\n  Performed {self.full_protocol_runs.all.count} attestations in {friendly_duration} {seconds}")
        print(f"  Used {self.worker_count} worker processes and {self.agent_count} mock agents\n")

        create_group = (
            ColumnGroup()
            .set_title("Capabilities Negotiation Phase", "^")
            .add(
                ColumnGroup()
                .set_title("Individual Requests", "^")
                .add(self.create_requests.make_table("Create Requests"))
            )
            .add(
                ColumnGroup()
                .set_title("Phase Executions", "^")
                .add(self.create_phases.make_table("Executions"))
            )
        )

        update_group = (
            ColumnGroup()
            .set_title("Evidence Handling Phase", "^")
            .add(
                ColumnGroup()
                .set_title("Individual Requests", "^")
                .add(self.update_requests.make_table("Update Requests"))
            )
            .add(
                ColumnGroup()
                .set_title("Phase Executions", "^")
                .add(self.update_phases.make_table("Executions"))
            )
        )

        full_protocol_runs_group = (
            ColumnGroup()
            .set_title("Complete Protocol Runs", "^")
            .add(
                OutputHelpers.center(self.full_protocol_runs.make_table("Attestation Tasks", self.track_duration).output, 50)
            )
        )

        create_group.print()
        update_group.print()
        print(OutputHelpers.center(full_protocol_runs_group.get_output(), 103))
        print("")

    @property
    def create_requests(self):
        return self._create_requests

    @property
    def create_phases(self):
        return self._create_phases

    @property
    def update_requests(self):
        return self._update_requests

    @property
    def update_phases(self):
        return self._update_phases

    @property
    def full_protocol_runs(self):
        return self._full_protocol_runs

    @property
    def start_time(self):
        return self._start_time.value

    @property
    def end_time(self):
        return self._end_time.value

    @property
    def track_duration(self):
        return self.end_time - self.start_time

    @property
    def worker_count(self):
        return self._worker_count.value

    @property
    def agent_count(self):
        return self._agent_count.value


class RequestStats:
    def __init__(self):
        self._all = StatCounter()
        self._ok = StatCounter(self._all)
        self._retry = StatCounter(self._all)
        self._fail = StatCounter(self._all)

    def make_table(self, label):
        table = (
            Table("<18", ">6", ">6", ">6", ">6")
            .head("", "ok", "retry", "fail", "all")
            .row(label + ":")
            .row(     "  Number",     self.ok.count,      self.retry.count,      self.fail.count,      self.all.count)
            .percents("  Percentage", self.ok.percentage, self.retry.percentage, self.fail.percentage)
            .row("Durations:")
            .times("  Average", self.ok.average_duration, self.retry.average_duration, self.fail.average_duration, self.all.average_duration)
            .times("  Shortest", self.ok.shortest_duration, self.retry.shortest_duration, self.fail.shortest_duration, self.all.shortest_duration)
            .times("  Longest", self.ok.longest_duration, self.retry.longest_duration, self.fail.longest_duration, self.all.longest_duration)
        )

        return table

    @property
    def all(self):
        return self._all

    @property
    def ok(self):
        return self._ok

    @property
    def retry(self):
        return self._retry

    @property
    def fail(self):
        return self._fail


class ProtocolStats:
    def __init__(self):
        self._all = StatCounter()
        self._success = StatCounter(self._all)
        self._fail = StatCounter(self._all)

    def make_table(self, label, track_duration=None):
        table = (
            Table("<18", ">8", ">6", ">6")
            .head("", "success", "fail", "all")
            .row(label + ":")
            .row(     "  Number",     self.success.count, self.fail.count, self.all.count)
            .percents("  Percentage", self.success.percentage, self.fail.percentage)
            .row("Durations:")
            .times("  Average", self.success.average_duration, self.fail.average_duration, self.all.average_duration)
            .times("  Shortest", self.success.shortest_duration, self.fail.shortest_duration, self.all.shortest_duration)
            .times("  Longest", self.success.longest_duration, self.fail.longest_duration, self.all.longest_duration)
        )

        if track_duration:
            s = track_duration
            m = s / 60
            h = m / 60

            table = (
                table
                .row("Rates:")
                .decimals("  Per second", self.success.get_rate(s), self.fail.get_rate(s), self.all.get_rate(s))
                .decimals("  Per minute", self.success.get_rate(m), self.fail.get_rate(m), self.all.get_rate(m))
                .integers("  Per hour", self.success.get_rate(h), self.fail.get_rate(h), self.all.get_rate(h))
            )

        return table

    @property
    def all(self):
        return self._all

    @property
    def success(self):
        return self._success

    @property
    def fail(self):
        return self._fail


class StatCounter:
    def __init__(self, total_counter=None):
        self._count = Value(ctypes.c_int, 0)
        self._total_duration = Value(ctypes.c_double, 0.0)
        self._shortest_duration = Value(ctypes.c_float, 9999.0)
        self._longest_duration = Value(ctypes.c_float, 0.0)

        self._total_counter = None

        if total_counter:
            self._total_counter = total_counter

    def record(self, duration):
        if duration is None:
            return

        with self._count.get_lock():
            self._count.value += 1

        with self._total_duration.get_lock():
            self._total_duration.value += duration
    
        with self._shortest_duration.get_lock():
            if duration < self._shortest_duration.value:
                self._shortest_duration.value = duration

        with self._longest_duration.get_lock():
            if duration > self._longest_duration.value:
                self._longest_duration.value = duration

        if self.total_counter:
            self.total_counter.record(duration)

    def get_rate(self, denominator):
        if not denominator:
            return None

        return self.count / denominator

    @property
    def count(self):
        return self._count.value

    @property
    def total_duration(self):
        if not self.count:
            return None

        return self._total_duration.value

    @property
    def longest_duration(self):
        if not self.count:
            return None

        return self._longest_duration.value
    
    @property
    def shortest_duration(self):
        if not self.count:
            return None

        return self._shortest_duration.value

    @property
    def average_duration(self):
        if not self.count:
            return None

        return self.total_duration / self.count

    @property
    def total_counter(self):
        return self._total_counter

    @property
    def percentage(self):
        if not self.total_counter.count:
            return None

        return self.count / self.total_counter.count
