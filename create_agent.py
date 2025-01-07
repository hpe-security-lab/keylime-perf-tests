import sys
import json

from sqlalchemy import text

from keylime import keylime_logging
from keylime.models import db_manager

logger = keylime_logging.init_logging("verifier")

db_manager.make_engine("cloud_verifier")

num = int(sys.argv[1])

tpm_policy = { "mask": "0xffff" }
tpm_policy = json.dumps(tpm_policy)
# Do it again because KL expects tpm_policy to be a JSON string for some reason
tpm_policy = json.dumps(tpm_policy)

tpm_clock = {"clock":3481636670,"resetCount":9,"restartCount":0,"safe":1}
tpm_clock = json.dumps(tpm_clock)
# Do it again because KL expects tpm_clock to be a JSON string for some reason
tpm_clock = json.dumps(tpm_clock)

#pcr10 = "0A1447C37555073B670B94072E7AAF60ACE6BD320A7C81FE8DEC9A10289B85C8"

with db_manager.engine.connect() as conn:
    for id in range(1, num):
        
        conn.execute(text(f"""
            INSERT INTO verifiermain (
                agent_id, tpm_policy, accept_tpm_hash_algs, accept_tpm_signing_algs, 
                supported_version, ak_tpm, ima_policy_id, mb_policy_id, pcr10, ima_pcrs
            ) VALUES (
                {id}, '{tpm_policy}', '["sha256"]', 
                '["ecschnorr","rsassa"]', 2.2, 
                'ARgAAQALAAUAcgAAABAAFAALCAAAAAAAAQDKCQgvW7DnsrfpQKm5GXULIdSgQsag5Q4sJnSDIHEw+Lm9LAVzmE5qwLyp3hNOCEslyPR46zNide/aRGBRy2RZS9vvZMPZim0iVoNU31nwV7+f2NZTi/I8c4owaPrL/Ti/VAT7uv7lrDvSxTOKNakdC4wBD5hMvERHwwAytgXKhpILXpvxj9LFtgUVGNtgjDXwqa1He+27CsZjL3g/oeILk1Mk590WMFcrD/TConyqlDDC3J+xdncC6KPuNPWqizUvHXrUtxD5wFqgPuMQvx3NxhPVgjtTFwT8QoDbRXAZQexk9TyZu2GrKqH9JPytwMDTIDroMe1ukCY4tS3iqMfh', 
                1, 1, :pcr10, '[10]'
            )
        """), pcr10=None)
