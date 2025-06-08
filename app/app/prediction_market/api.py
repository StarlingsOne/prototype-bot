import requests
from datetime import datetime, timezone
from prediction_market.context_schema import CONTEXT_SCHEMA

def fetch_user_info(domain, username):
    url = f"{domain}/api/v0/userinfo/{username}"
    resp = requests.get(url)
    try:
        resp.raise_for_status()
        user_json = resp.json()
    except Exception as e:
        print(f"[ERROR] Could not parse user info JSON from {url}")
        print(f"[ERROR] Status code: {resp.status_code}")
        print(f"[ERROR] Content: {resp.content!r}")
        raise
    return user_json


def extract_market_context(domain: str, market_id: int) -> dict:
    url = f"{domain}/api/v0/markets/{market_id}"
    resp = requests.get(url)
    resp.raise_for_status()
    api_json = resp.json()
    market = api_json.get("market", {})
    prob_changes = api_json.get("probabilityChanges", [])
    # Get the LAST probability change (latest), or fallback to initial
    latest_prob = prob_changes[-1]["probability"] if prob_changes else market.get("initialProbability", 0.5)
    # Extract the resolution datetime as a string (keep as-is for prompt, or parse for calculations)
    resolution_datetime = market.get("resolutionDateTime", "")

    # Optionally, for time delta (forecasting window):
    if resolution_datetime:
        try:
            # Parse ISO8601 string, always in UTC
            dt_resolution = datetime.fromisoformat(resolution_datetime.replace("Z", "+00:00"))
            hours_to_resolution = (dt_resolution - datetime.now(timezone.utc)).total_seconds() / 3600
        except Exception:
            hours_to_resolution = None
    else:
        hours_to_resolution = None

    return {
        "question_title": market.get("questionTitle", ""),
        "resolution_datetime": resolution_datetime,
        "hours_to_resolution": hours_to_resolution,  # float, or None
        "market_current_probability": latest_prob,
        "market_total_volume": api_json.get("totalVolume", 0),
    }

def fetch_maximum_debt_allowed(domain: str) -> int:
    url = f"{domain}/api/v0/setup"
    resp = requests.get(url)
    resp.raise_for_status()
    setup = resp.json()
    # Defensive: dig to User/MaximumDebtAllowed, default to 0 if missing
    return int(setup.get("User", {}).get("MaximumDebtAllowed", 0))

def validate_context_types(context, schema=CONTEXT_SCHEMA):
    for k, v in context.items():
        expected_type = schema.get(k, {}).get("type")
        if expected_type and not isinstance(v, expected_type):
            print(f"⚠️ Warning: Key '{k}' expected {expected_type}, got {type(v)}")
