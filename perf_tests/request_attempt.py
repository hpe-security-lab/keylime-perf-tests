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
import time
import traceback

from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from perf_tests.output import OutputHelpers


class RequestAttempt:
    def __init__(self, task, method, url):
        self._task = task

        self._method = method
        self._url = url
        self._req_headers = {}
        self._req_body = None
        
        self._start_time = None
        self._end_time = None
        self._request = None
        self._response = None
        self._exception = None

    def _log(self, status, msg, details=None):
        print(f"{self.id} (w{self.task.worker_index}): [{status}] {msg}")

        if not details:
            return

        for line in details.splitlines():
            indent = "  " if details.startswith(line) else "      "
            print(f"{indent}{line}")

    def _log_info(self, msg, details=None):
        if self.task.task_manager.execution.verbose:
            self._log("info", msg, details)

    def _log_ok(self, msg, details=None):
        self._log("\033[92mok\033[0m", msg, details)

    def _log_retry(self, msg, details=None):
        self._log("\033[93mretry\033[0m", msg, details)

    def _log_fail(self, msg, details=None):
        self._log("\033[91mfail\033[0m", msg, details)

    def _log_request(self):
        self._log_info(f"{self._method} {self._url}")

    def _log_outcome(self):
        operation = f"{self.action} attestation {self.task.index} for {self.task.agent.id}"

        if self.ok:
            self._log_ok(f"{operation} in {OutputHelpers.format_duration(self.duration)}")
            return

        if self.retry_after:
            retry_after_f = OutputHelpers.format_count(self.retry_after, "second", "seconds")
            
            if self.conflicts:
                issue = "already in progress"
            else:
                issue = "performed too early"

            self._log_retry(f"{operation} {issue}, retrying in {retry_after_f}")
            return

        if self.exception:
            trace = traceback.format_exception(self.exception)
            trace = "".join(trace)
            details = f"Unexpected exception occurred during request/response:\n{trace}"
        elif not self.response:
            details = f"No response received"
        elif not self.response_text:
            details = f"Received empty response body (status={self.response.code})"
        elif not self.response_json:
            details = f"Response body could not be parsed as JSON: (status={self.response.code})\n{self.response_text}"
        elif self.response.code and (self.response.code < 200 or self.response.code > 299):
            details = f"Received unexpected status code {self.response.code} and JSON response body:\n{self.response_text}"
        else:
            details = "An unknown error occurred"

        self._log_fail(f"{operation} failed after {OutputHelpers.format_duration(self.duration)}", details)

    def _curl_set_opts(self, curl_obj):
        curl_obj.setopt(curl_obj.SSL_VERIFYPEER, False)
        curl_obj.setopt(curl_obj.SSL_VERIFYHOST, False)

    def set_header(self, name, value):
        self._req_headers[name] = value

    def set_body(self, req_body):
        if isinstance(req_body, (dict, list)):
            self.set_header("Content-Type", "application/json")
            self._req_body = json.dumps(req_body)
        else:
            self.set_header("Content-Type", "text/plain")
            self._req_body = str(req_body)

    async def perform(self):
        self._log_request()

        AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
        http_client = AsyncHTTPClient()

        self._request = HTTPRequest(
            url = self._url,
            method = self._method,
            headers = self._req_headers,
            body = self._req_body,
            connect_timeout = 20,
            request_timeout = 45,
            prepare_curl_callback = self._curl_set_opts
        )

        self._start_time = time.perf_counter()

        try:
            self._response = await http_client.fetch(self._request, raise_error=False)
        except Exception as exc:
            self._exception = exc

        self._end_time = time.perf_counter()
        self._log_outcome()
        return self

    def render(self):
        return {
            "action": self.action,
            "method": self.request.method,
            "url": self.request.url,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "ok": self.ok,
            "conflicts": self.conflicts,
            "retry_after": self.retry_after
        }

    @property
    def task(self):
        return self._task

    @property
    def id(self):
        agent_index = self.task.agent.index
        task_index = self.task.index

        if self in self.task.create_attempts:
            request_type = "c"
            request_index = self.task.create_attempts.index(self)
        else:
            request_type = "u"
            request_index = self.task.update_attempts.index(self)

        return f"a{agent_index}|t{task_index}|{request_type}{request_index}"

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def duration(self):
        if not self.response or not self.response.request_time:
            if not self.end_time or not self.start_time:
                return None

            return self.end_time - self.start_time

        return self.response.request_time
    
    @property
    def request(self):
        return self._request

    @property
    def action(self):
        if not self.request or not self.request.method:
            return None

        match self.request.method.upper():
            case "POST":
                return "create"
            case "GET":
                return "read"
            case "PUT" | "PATCH":
                return "update"
            case "DELETE":
                return "delete"
            case _:
                return None

    @property
    def response(self):
        return self._response

    @property
    def response_text(self):
        if not self.response or not self.response.body:
            return None

        return self.response.body.decode().strip()

    @property
    def response_json(self):
        text = self.response_text

        if not text:
            return None

        try:
            return json.loads(text)
        except Exception:
            return None

    @property
    def exception(self):
        return self._exception

    @property
    def ok(self):
        if not self.response:
            return None

        return bool(
            not self.exception
            and self.response_json 
            and self.response.code 
            and self.response.code >= 200 
            and self.response.code <= 299
        )

    @property
    def conflicts(self):
        if not self.response or not self.response.code:
            return None

        return bool(self.response.code == 409)

    @property
    def retry_after(self):
        if not self.response or not self.response.headers or not self.response.code:
            return None

        retry_after = int(self.response.headers.get("Retry-After", 0))

        if retry_after <= 0 and self.conflicts:
            return 1

        return retry_after


class DeserializedAttempt(RequestAttempt):
    def __init__(self, task, data):
        self._task = task

        self._method = data["method"]
        self._url = data["url"]
        self._req_headers = {}
        self._req_body = None
        
        self._start_time = data["start_time"]
        self._end_time = data["end_time"]
        self._request = None
        self._response = None
        self._exception = None

        self._duration = data["duration"]
        self._ok = data["ok"]
        self._conflicts = data["conflicts"]
        self._retry_after = data["retry_after"]

    @property
    def duration(self):
        return self._duration

    @property
    def ok(self):
        return self._ok

    @property
    def conflicts(self):
        return self._conflicts

    @property
    def retry_after(self):
        return self._retry_after

    