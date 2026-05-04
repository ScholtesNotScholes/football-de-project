import os
from dotenv import load_dotenv
import sqlalchemy as sa

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


def load_table(table_name: str, payload: list, engine: sa.Engine):
    metadata = sa.MetaData()
    db_table = sa.Table(
        table_name,
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("data", sa.dialects.postgresql.JSONB),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.sql.func.now()),
        schema="football_etl_raw_data"
    )

    # define insertion
    db_table_insert = sa.insert(db_table).values(data=payload)

    # ensure destination exists, and insert
    with engine.connect() as con:
        con.execute(sa.schema.CreateSchema("football_etl_raw_data", if_not_exists=True))
        metadata.create_all(con)
        con.execute(db_table_insert)
        con.commit()
    return