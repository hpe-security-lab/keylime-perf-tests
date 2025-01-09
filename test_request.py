import json
import time
import sys
import datetime

from sqlalchemy import text

import tornado.process

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import asyncio

from keylime import keylime_logging
from keylime.models import db_manager

logger = keylime_logging.init_logging("verifier")

db_manager.make_engine("cloud_verifier")

num = int(sys.argv[1])

AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")

begin = datetime.datetime.now()

async def create(agent_id):
    http_client = AsyncHTTPClient()
    start_time = time.time_ns()
    url = f"http://10.152.216.101:8881/v3.0/agents/{agent_id}/attestations"
    headers = {"content-type": "application/json"}
    req_body = json.dumps({"supported_hash_algorithms": ["sha256"],
                        "supported_signing_schemes": ["rsassa"],
                        "boottime": "1970-01-01 01:00:01+00:00"}) 
    request = HTTPRequest(url=url, method="POST", headers=headers, body=req_body)

    response = None

    try:
        response = await http_client.fetch(request)
        end_time = time.time_ns()
        if response.code != 200:
            print(f"Received {response.code} response for agent {agent_id}")
        else:
            print(f"Received {response.code} response for agent {agent_id}")
    except Exception as e:
        print(f"Request for agent {agent_id} failed: {e}")

    if response:
        res_body = json.loads(response.body.decode())

        if not isinstance(res_body, dict):
            print(f"Response received for agent {agent_id} is not valid JSON")
            exit()
    end_time = time.time_ns()
    create_time = end_time - start_time
    print(f"create time for {agent_id} is", format_time(create_time)) 



async def update(agent_id):
    http_client = AsyncHTTPClient()
    start_time = time.time_ns()
    url = f"http://10.152.216.101:8881/v3.0/agents/{agent_id}/attestations/latest"
    headers = {"content-type": "application/json"}

    with open("ima_ml.txt", "r") as f:
        ima = f.read()
    
    with open("mb_ml.txt", "r") as f:
        mb = f.read()

    req_body = json.dumps({"tpm_quote": "r/1RDR4AYACIAC7s9pXY4dla3uHjUOVIJLQQ+VXb8+AhpubvOfxvMGB/aABRTYjd0Tmxxc2QzMnVJMVpQV3REcwAAAAFoGSAKAAAAKwAAAAABAAECAAAAAAAAAAABAAsD//8BACA6FyLB7MLIIRkedpNB5VHSOHfXLsRkm1U74Y8eveoMKw==:ABQACwEACxh9sNgq3oYbq87obxRPA8v3tzwuBYLr53u1hz/iAaErnr5L+pHNvslCHXIm3SXDrpHdRp6GAO+1hR1w+VgQSaeN+4bsM0JO9kAr/3ToKx0Q2bAMRnMANEBUlnFJfkAGyG/Ms4koGGhgcSrHkc8zjOiYDCdwj0DxavzF0MpG/OCrYgAup60f7YyxfzJ5QzYx72owBPPUfA+N1QuBfzGDBAzwt0+TdVa3udPCF4CLtZrDcUERAok29PmVX6EFhMfw7GmSFCSAmUqtPIvjva8K46ynBVYGsR1sfVY58eqL53C4XLSkG1+vS4NV5KnSyBRVzvs27FUWlJOJekk5mEvZxw==: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", "starting_ima_offset": 0, "ak_tpm": "ARgAAQALAAUAcgAAABAAFAALCAAAAAAAAQDKCQgvW7DnsrfpQKm5GXULIdSgQsag5Q4sJnSDIHEw+Lm9LAVzmE5qwLyp3hNOCEslyPR46zNide/aRGBRy2RZS9vvZMPZim0iVoNU31nwV7+f2NZTi/I8c4owaPrL/Ti/VAT7uv7lrDvSxTOKNakdC4wBD5hMvERHwwAytgXKhpILXpvxj9LFtgUVGNtgjDXwqa1He+27CsZjL3g/oeILk1Mk590WMFcrD/TConyqlDDC3J+xdncC6KPuNPWqizUvHXrUtxD5wFqgPuMQvx3NxhPVgjtTFwT8QoDbRXAZQexk9TyZu2GrKqH9JPytwMDTIDroMe1ukCY4tS3iqMfh", "ima_entries": ima, "mb_entries": mb})

    request = HTTPRequest(url=url, method="PUT", headers=headers, body=req_body)

    response = None

    try:
        response = await http_client.fetch(request, raise_error=False)
        if response.code != 200:
            print(f"Received {response.code} response for agent {agent_id}: {response.body.decode()}")
        else:
            print(f"Received {response.code} response for agent {agent_id}")
    except Exception as e:
        print(f"Request for agent {agent_id} failed: {e}")

    if response:
        res_body = json.loads(response.body.decode())

        if not isinstance(res_body, dict):
            print(f"Response received for agent {agent_id} is not valid JSON")
            exit()
    
    end_time = time.time_ns()
    update_time = end_time - start_time
    print(f"update time for {agent_id} is", format_time(update_time))


def format_time(ns_elapsed) -> str:
    # pylint: disable=no-else-return

    #ns_elapsed = time.time_ns() - timestamp

    if ns_elapsed < 1000:
        return f"{ns_elapsed}ns"
    elif ns_elapsed < 1000000:
        return f"{round(ns_elapsed/1000)}μs"
    elif ns_elapsed < 1000000000:
        return f"{round(ns_elapsed/1000000)}ms"
    else:
        return f"{round(ns_elapsed/1000000000)}s"

async def main():
    # tornado.process.fork_processes(2)
    begin_create = time.time_ns()
    create_tasks = [ create(agent_id) for agent_id in range(1, num) ]
    await asyncio.gather(*create_tasks)
    total_create = time.time_ns() - begin_create
    

    with db_manager.engine.connect() as conn:
        conn.execute(text("UPDATE attestations SET nonce = :nonce"), nonce=bytes.fromhex("49beed365aac777dae23564f5ad0ec"))

    begin_update = time.time_ns()
    update_tasks = [ update(agent_id) for agent_id in range(1, num) ]
    await asyncio.gather(*update_tasks)
    total_update = time.time_ns() - begin_update
    
    print("\nTotal time taken to create", num - 1, "requests: ", format_time(total_create))
    avg_create_time = format_time(total_create / num - 1)
    print(f"Average time taken to create attestation per agent: {avg_create_time}")

    print("\nTotal time taken to update", num - 1, "requests: ", format_time(total_update))
    avg_update_time = format_time(total_update / num - 1)
    print(f"Average time taken to update attestation per agent: {avg_update_time}")

    print("\nTotal time taken to complete", num - 1, "requests: ", format_time(total_create + total_update))
    print("\n Start time: ", begin, "\n End time: ", datetime.datetime.now())

if __name__ == "__main__":
    asyncio.run(main())
