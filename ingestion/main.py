from extract import get_matches
from load import create_neon_engine, load_table

LEAGUE_ID = "bl1"
CURRENT_SEASON = 2025

def run_pipeline():
    engine = create_neon_engine()

    # MATCHES
    payload = get_matches(LEAGUE_ID, CURRENT_SEASON)
    load_table("matches", payload, engine)

if __name__ == "__main__":
    run_pipeline()