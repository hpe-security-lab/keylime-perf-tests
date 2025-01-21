import json

from keylime import keylime_logging
from keylime.models import db_manager

logger = keylime_logging.init_logging("verifier")

db_manager.make_engine("cloud_verifier")

with open("runtime_policy.json", "r") as f:
    ima = json.load(f)

with open("mb_refstate.json", "r") as f:
    mb = json.load(f)


with db_manager.engine.connect() as conn:
    conn.execute("INSERT INTO allowlists (id, name, ima_policy)  VALUES (1, 1, %s);", json.dumps(ima))
    conn.execute("INSERT INTO mbpolicies (id, name, mb_policy)  VALUES (1, 1, %s)",json.dumps(mb))
