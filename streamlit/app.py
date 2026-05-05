import os
from dotenv import load_dotenv
import sqlalchemy as sa
import streamlit as st
import pandas as pd

load_dotenv()

def create_neon_engine():
    load_dotenv()

    _DB_PARAMS = {
        "host":     os.getenv("PGHOST"),
        "database": os.getenv("PGDATABASE"),
        "username": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD")
    }
    if None in _DB_PARAMS.values():
        raise Exception("Could not get some or all DB params")
    
    neon_url = sa.URL.create(**_DB_PARAMS, drivername="postgresql")
    
    return sa.create_engine(neon_url)


engine = create_neon_engine()

with engine.connect() as con:
    df = pd.read_sql("SELECT * FROM football_etl_gold.league_table;", con=con)

st.write(df)