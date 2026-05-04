import requests

def _make_request(endpoint: str):
    url = f"https://api.openligadb.de/{endpoint}"
    headers = {"content-type": "application/json"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()

def get_matches(league: str, season: int):
    return _make_request(f"getmatchdata/{league}/{season}")