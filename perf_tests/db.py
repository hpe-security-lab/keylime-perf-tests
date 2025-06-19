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

from sqlalchemy import create_engine, text


class DB:
    execution = None
    engine = None

    @classmethod
    def init_engine(cls, execution):
        cls.execution = execution
        cls.engine = create_engine(execution.db_url)

    @classmethod
    def set_up(cls):
        with cls.engine.begin() as db_conn:
            cls.create_ima_policy(db_conn, "perf-test-policy")
            cls.create_uefi_refstate(db_conn, "perf-test-refstate")

            for i in range(0, cls.execution.agent_count):
                cls.create_agent(db_conn, f"perf-test-agent-{i}")

    @classmethod
    def tear_down(cls):
        with cls.engine.begin() as db_conn:
            cls.delete_agents(db_conn, "perf-test-agent-%")
            cls.delete_ima_policy(db_conn, "perf-test-policy")
            cls.delete_uefi_refstate(db_conn, "perf-test-refstate")

    @classmethod
    def create_ima_policy(cls, db_conn, name):
        with open("data/ima_runtime_policy.json", "r") as f:
            ima_policy = json.load(f)

        db_conn.execute(
            text("INSERT INTO allowlists (id, name, ima_policy) VALUES (:id, :name, :ima_policy);"),
            {"id": 99999, "name": name, "ima_policy": json.dumps(ima_policy)}
        )

    @classmethod
    def delete_ima_policy(cls, db_conn, name):
        db_conn.execute(text(f"DELETE FROM allowlists WHERE name='{name}'"))

    @classmethod
    def create_uefi_refstate(cls, db_conn, name):
        with open("data/uefi_refstate.json", "r") as f:
            uefi_refstate = json.load(f)

        db_conn.execute(
            text("INSERT INTO mbpolicies (id, name, mb_policy) VALUES (:id, :name, :mb_refstate);"),
            {"id": 99999, "name": name, "mb_refstate": json.dumps(uefi_refstate)}
        )

    @classmethod
    def delete_uefi_refstate(cls, db_conn, name):
        db_conn.execute(text(f"DELETE FROM mbpolicies WHERE name='{name}'"))

    @classmethod
    def create_agent(cls, db_conn, agent_id):
        tpm_policy = { "mask": "0xffff" }
        tpm_policy = json.dumps(tpm_policy)

        db_conn.execute(text("""
            INSERT INTO verifiermain (
                agent_id, tpm_policy, accept_tpm_hash_algs, accept_tpm_signing_algs, 
                supported_version, ak_tpm, ima_policy_id, mb_policy_id, ima_pcrs
            ) VALUES (
                :agent_id, :tpm_policy, '["sha256", "sha1"]', 
                '["ecschnorr","rsassa"]', 2.2, 
                'ARgAAQALAAUAcgAAABAAFAALCAAAAAAAAQDKCQgvW7DnsrfpQKm5GXULIdSgQsag5Q4sJnSDIHEw+Lm9LAVzmE5qwLyp3hNOCEslyPR46zNide/aRGBRy2RZS9vvZMPZim0iVoNU31nwV7+f2NZTi/I8c4owaPrL/Ti/VAT7uv7lrDvSxTOKNakdC4wBD5hMvERHwwAytgXKhpILXpvxj9LFtgUVGNtgjDXwqa1He+27CsZjL3g/oeILk1Mk590WMFcrD/TConyqlDDC3J+xdncC6KPuNPWqizUvHXrUtxD5wFqgPuMQvx3NxhPVgjtTFwT8QoDbRXAZQexk9TyZu2GrKqH9JPytwMDTIDroMe1ukCY4tS3iqMfh', 
                99999, 99999, '[10]'
            )
        """), {"agent_id": agent_id, "tpm_policy": tpm_policy})

    @classmethod
    def delete_agents(cls, db_conn, agent_id_pattern):
        db_conn.execute(text(f"DELETE FROM evidence_items WHERE agent_id LIKE '{agent_id_pattern}'"))
        db_conn.execute(text(f"DELETE FROM attestations WHERE agent_id LIKE '{agent_id_pattern}'"))
        db_conn.execute(text(f"DELETE FROM verifiermain WHERE agent_id LIKE '{agent_id_pattern}'"))
