import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime
import logging
import sqlalchemy


# INIT

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logging.info(f"[INIT] RUNNING EXTRACT / LOAD SCRIPT")

load_dotenv()

KEY = os.getenv("API_FOOTBALL_API_KEY")
if not KEY:
    raise Exception("Couldn't get API key")

DB_PARAMS = {
    "host":     os.getenv("PGHOST"),
    "database":   os.getenv("PGDATABASE"),
    "username":     os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD")
}
if None in DB_PARAMS.values():
    raise Exception("Could not get some or all DB params")


# SMOKE TEST
# TODO: refactor this and EL sections into functions?

BASE = "https://v3.football.api-sports.io"

h = {"x-apisports-key": KEY}

logging.info(f"[SMOKE TEST] Running smoke test for {BASE}")
r = requests.get(BASE, headers=h)
r.raise_for_status()

logging.info("[SMOKE TEST] Running smoke test for DB")
CONN_URL = sqlalchemy.URL.create(**DB_PARAMS, drivername="postgresql")
engine = sqlalchemy.create_engine(CONN_URL)
with engine.connect() as con:
    if con.closed != 0:
        raise Exception("Could not connect to DB")
logging.info("[SMOKE TEST] Smoke test passed")


# EXTRACT
# TODO: when more is added to this, convert it to a loop since it will be the same structure 
# TODO: create a config for each pipeline, which is used by E and L sections (refactored as functions)

logging.info("[EXTRACT] Beginning extraction")

logging.info("[EXTRACT] Leagues")
start_time  = datetime.now()
# r_leagues   = requests.get(f"{BASE}/leagues", headers=h)
# d_leagues   = json.loads(r_leagues.text)
# with open("d_leagues.json", "w") as f:
#     f.write(json.dumps(d_leagues))

with open("d_leagues.json", "r") as f: # just for tests (saves API usage)
    d_leagues = json.load(f)
end_time    = datetime.now()
logging.info(f"[EXTRACT] Leagues extracted ({round((end_time - start_time).total_seconds(), 2)} seconds)")


# LOAD

logging.info("[LOAD] Beginning loading")

# create unique table suffix based on current time
table_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

logging.info("[LOAD] Leagues")
start_time  = datetime.now()
db_table_leagues_metadata = sqlalchemy.MetaData()
db_table_leagues = sqlalchemy.Table(
    "leagues",
    db_table_leagues_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("data", sqlalchemy.dialects.postgresql.JSONB),
    sqlalchemy.Column("created_at", sqlalchemy.TIMESTAMP, server_default=sqlalchemy.sql.func.now()),
    schema="raw_data"
)
db_table_leagues_insert = sqlalchemy.insert(db_table_leagues).values(data=d_leagues)
with engine.connect() as con:
    con.execute(sqlalchemy.schema.CreateSchema("raw_data", if_not_exists=True))
    db_table_leagues_metadata.create_all(con)
    con.execute(db_table_leagues_insert)
    con.commit()
end_time    = datetime.now()
logging.info(f"[LOAD] Leagues loaded to DB ({round((end_time - start_time).total_seconds(), 2)} seconds)")
