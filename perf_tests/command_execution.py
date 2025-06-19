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

import os
import sys
import argparse

from urllib.parse import urlparse, urlunparse


class CommandExecution:
    @classmethod
    def _make_arg_parser(cls):
        parser = argparse.ArgumentParser(
            prog="run_perf_tests",
            usage="run_perf_tests <verifier_url> <db_url> [options]",
            description="Runs performance tests against a Keylime verifier's push attestation endpoints",
        )

        parser.add_argument('verifier_url', help="the URL at which to contact the verifier")

        parser.add_argument('db_url', help="the URL at which to contact the verifier's database engine")

        parser.add_argument(
            "-w", "--workers",
            metavar="<worker_count>",
            dest="worker_count",
            default="0",
            help="the no. of worker processes to use for testing (uses no. of cores by default)"
        )

        parser.add_argument(
            "-a", "--agents",
            metavar="<agent_count>",
            dest="agent_count",
            default="0",
            help="the no. of mock agents to create for testing (same as the no. of workers by default)"
        )

        parser.add_argument(
            "-t", "--tasks",
            metavar="<task_count>",
            dest="task_count",
            default="0",
            help="the no. of attestation tasks to perform per agent (continues until stopped by default)"
        )

        parser.add_argument(
            "-v", "--verbose",
            dest="verbose",
            action="store_true",
            default=False,
            help="output additional debugging information"
        )

        return parser

    @classmethod
    def parse_args(cls):
        parser = cls._make_arg_parser()

        if len(sys.argv) <= 1:
            parser.print_help()
            sys.exit(1)
        
        args = parser.parse_args()
        verifier_url = urlparse(args.verifier_url, scheme="https")
        db_url = urlparse(args.db_url or "", scheme="postgresql")

        if not verifier_url.netloc:
            print("Invalid verifier URL")
            exit(1)

        if not verifier_url.port:
            port = 8880 if verifier_url.scheme == "http" else 8881
            verifier_url._replace(netloc=f"{verifier_url.netloc}:{port}")

        if not db_url.netloc:
            port = 3306 if db_url.scheme.startswith("mysql") else 5432
            db_url._replace(netloc=f"{verifier_url.hostname}:{port}")

        if db_url.scheme.startswith("sqlite"):
            print("Performance tests can only be run using a full database engine such as PostgreSQL or MySQL")
            sys.exit(1)

        if not args.worker_count.isdigit():
            print("<worker_count> must be an integer")

        if not args.agent_count.isdigit():
            print("<agent_count> must be an integer")

        if not args.task_count.isdigit():
            print("<task_count> must be an integer")

        verifier_url = urlunparse(verifier_url)
        db_url = urlunparse(db_url)
        worker_count = int(args.worker_count)
        agent_count = int(args.agent_count)
        task_count = int(args.task_count)
        verbose = args.verbose

        if worker_count < 0:
            print("<worker_count> must be '0' or greater")
            sys.exit(1)

        if agent_count < 0:
            print("<agent_count> must be '0' or greater")
            sys.exit(1)

        if task_count < 0:
            print("<task_count> must be '0' or greater")
            sys.exit(1)

        return cls(verifier_url, db_url, worker_count, agent_count, task_count, verbose)

    def __init__(self, verifier_url, db_url, worker_count, agent_count, task_count, verbose):
        if worker_count == 0:
            worker_count = os.cpu_count()

        if agent_count == 0:
            agent_count = worker_count

        self._verifier_url = verifier_url
        self._db_url = db_url
        self._worker_count = worker_count
        self._agent_count = agent_count
        self._task_count = task_count
        self._verbose = verbose

    @property
    def verifier_url(self):
        return self._verifier_url

    @property
    def db_url(self):
        return self._db_url

    @property
    def worker_count(self):
        return self._worker_count

    @property
    def agent_count(self):
        return self._agent_count

    @property
    def task_count(self):
        return self._task_count

    @property
    def verbose(self):
        return self._verbose
