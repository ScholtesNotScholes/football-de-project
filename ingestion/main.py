import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime
import logging
import sqlalchemy as sa
from pathlib import Path
import argparse


# INIT

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logging.info(f"[INIT] RUNNING EXTRACT / LOAD SCRIPT")

load_dotenv()

_KEY = os.getenv("API_FOOTBALL_API_KEY")
if not _KEY:
    raise Exception("Couldn't get API key")

_DB_PARAMS = {
    "host":     os.getenv("PGHOST"),
    "database": os.getenv("PGDATABASE"),
    "username": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD")
}
if None in _DB_PARAMS.values():
    raise Exception("Could not get some or all DB params")


BASE = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": _KEY}
PIPELINE_CONFIG_PATH = Path("pipeline-config.json")


# HELPER FUNCTIONS

def smoke_test_url(url: str, headers: dict = {}) -> None:
    """Smoke test an endpoint URL for connection"""
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return

def smoke_test_db(engine) -> None:
    """Smoke test a DB for an open connection using an sqlalchemy engine"""
    with engine.connect() as con:
        if con.closed != 0:
            raise Exception("Could not connect to DB")
    return

def get_pipeline_config(config_path: Path, config_key: str = None):
    """Get a JSON config file, and optionally a specific key-defined value from it."""
    with open(config_path, "r") as f:
        c = json.load(f)

    if config_key:
        try:
            return c[config_key]
        except KeyError:
            raise KeyError(f"Key {config_key} not found in config {config_path}")
    else:
        return c

def extract(pipeline_config_key: str) -> dict:
    """
    Extracts data from globally defined BASE url, using
    HEADERS. 

    Reads from PIPELINE_CONFIG_PATH JSON file to get required
    metadata to build the request.

    Requires key (string) of JSON file as input.
    Returns payload from API endpoint as JSON (dict).
    """
    config = get_pipeline_config(PIPELINE_CONFIG_PATH, pipeline_config_key)
    
    r = requests.get(f"{BASE}/{config['url-suffix']}", headers=HEADERS)
    return json.loads(r.text)

def load(pipeline_config_key: str, json_payload: dict, engine: sa.Engine) -> None:
    """
    Load JSON payload of a defined pipeline in PIPELINE_CONFIG_PATH 
    JSON into DB defined in the input sqlalchemy engine.
    """
    config = get_pipeline_config(PIPELINE_CONFIG_PATH, pipeline_config_key)

    # define destination table
    metadata = sa.MetaData()
    db_table = sa.Table(
        config["db-table"],
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("data", sa.dialects.postgresql.JSONB),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.sql.func.now()),
        schema="raw_data"
    )

    # define insertion
    db_table_insert = sa.insert(db_table).values(data=json_payload)

    # ensure destination exists, and insert
    with engine.connect() as con:
        con.execute(sa.schema.CreateSchema("raw_data", if_not_exists=True))
        metadata.create_all(con)
        con.execute(db_table_insert)
        con.commit()
    return


# MAIN

def main():
  p = argparse.ArgumentParser(description=f"Runs extract and load pipeline for defined pipelines in {PIPELINE_CONFIG_PATH}")
  p.add_argument("--mode", "-m", 
                 choices=["all", "single", "test"], default="all",
                 help="Mode to run. \
                  'all' runs all in pipeline config. \
                  'single' requires a key from pipeline config and runs pipeline only for that key. \
                  'test' runs a smoke test to the endpoint and DB and exits.")
  p.add_argument("--key", "-k",
                 help="Required if mode='single', defining the key to use from the pipeline config.")
  
  args = p.parse_args()

  # Run smoke tests regardless
  con_url = sa.URL.create(**_DB_PARAMS, drivername="postgresql")
  engine = sa.create_engine(con_url)

  logging.info("[SMOKE TEST] Testing DB connection")
  smoke_test_db(engine)
  logging.info("[SMOKE TEST] Testing API endpoint")
  smoke_test_url(BASE, HEADERS)
  logging.info("[SMOKE TEST] Complete")

  if args.mode == "test":
      return
  
  if args.mode == "single" and not args.key:
      raise Exception("'single' mode requires 'key'")
  
  elif args.mode == "single":
      start_time = datetime.now()
      logging.info(f"[EXTRACT] Running single pipeline ({args.key})")
      payload = extract(args.key)

      logging.info(f"[LOAD] Running single pipeline ({args.key})")
      load(args.key, payload, engine)
      end_time = datetime.now()

      logging.info(f"Pipeline complete ({round((end_time - start_time).total_seconds(), 2)} seconds)")

  elif args.mode == "all":
      start_time = datetime.now()
      all_keys = get_pipeline_config(PIPELINE_CONFIG_PATH)
      logging.info("Running all pipelines")

      for k in all_keys:
          start_time_sub = datetime.now()
          logging.info(f"[EXTRACT] Running all pipelines ({k})")
          payload = extract(k)

          logging.info(f"[LOAD] Running all pipelines ({k})")
          load(k, payload, engine)
          end_time_sub = datetime.now()

          logging.info(f"{k} pipeline complete ({round((end_time_sub - start_time_sub).total_seconds(), 2)} seconds)")
      
      end_time = datetime.now()
      logging.info(f"Pipeline complete ({round((end_time - start_time).total_seconds(), 2)} seconds)")

if __name__ == "__main__":
    main()