import json
import argparse
import requests
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database_tools.postgres_handler import PostgresHandler

def fetch_market_price(domain, market_id):
    domain = domain.rstrip("/")
    url = f"{domain}/api/v0/markets/{market_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        changes = data.get("probabilityChanges", [])
        if not changes:
            print(f"⚠️ No probability changes found for market {market_id}")
            return 0.0

        # Sort by timestamp to get the most recent
        latest = max(changes, key=lambda x: x["timestamp"])
        return latest.get("probability", 0.0)
    except Exception as e:
        print(f"❌ Error fetching market price from {url}: {e}")
        return 0.0


def fetch_user_balance(domain, username):
    url = f"{domain}/v0/userinfo/{username}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        return int(data.get("accountBalance", 0))
    except Exception as e:
        print(f"❌ Error fetching user balance from {url}: {e}")
        return 0


def get_latest_sentiment(identifier, since_hours_ago=24):

    db = PostgresHandler()
    since = datetime.now() - timedelta(hours=since_hours_ago)
    row = db.get_most_recent_sentiment_result(identifier, since=since)
    db.close()

    if not row:
        return None

    _, sentiment_raw, _, _ = row
    return json.loads(sentiment_raw) if isinstance(sentiment_raw, str) else sentiment_raw


    sentiment_raw = results[0][1]
    return json.loads(sentiment_raw) if isinstance(sentiment_raw, str) else sentiment_raw

def calculate_bet_amount(conviction, assessment, market_price, user_balance, scale=100):
    if assessment != market_price:
        delta = abs(assessment - market_price)
        amount = int(delta * scale * conviction)
        return max(0, amount)
    else:
        return 0


def calculate_bet_direction(assessment, market_price):
    if assessment > market_price:
        return "YES"
    if assessment < market_price:
        return "NO"
    else:
        return "NULL"

def place_bet(domain, market_id, amount, outcome, api_key=None):
    if outcome == "NULL":
        print("No bet.")
        return

    payload = {
        "marketId": market_id,
        "outcome": outcome,
        "amount": amount
    }

    headers = {
        "Content-Type": "application/json"
    }

    if api_key:
        headers["X-API-Key"] = api_key

    url = f"{domain}/api/v0/bet"

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.ok:
            print("✅ Bet placed successfully!")
            print("📄 Response:", response.json())
        else:
            print("❌ Failed to place bet:", response.text)
    except Exception as e:
        print(f"❌ Exception during placing bet: {e}")


def run_betting_bot(identifier, domain, market_id, api_key):
    sentiment_data = get_latest_sentiment(identifier)

    if not sentiment_data:
        print(f"⚠️ No sentiment data found for '{identifier}' in the last 24 hours — skipping bet.")
        return

    print(f"conviction {sentiment_data["conviction"]}")
    print(f"conviction type: {type(sentiment_data["conviction"])}")

    print(f"assessment {sentiment_data["assessment"]}")
    print(f"assessment type: {type(sentiment_data["assessment"])}")

    market_price = fetch_market_price(domain, market_id)
    print(f"market_price: {market_price}")

    # user_balance = fetch_user_balance(domain, username)
    user_balance = 500

    amount = calculate_bet_amount(
        sentiment_data["conviction"], 
        sentiment_data["assessment"], 
        market_price, 
        user_balance
    )
    print(f"amount {amount}")

    outcome = calculate_bet_direction(sentiment_data["assessment"], market_price)
    print(f"outcome: {outcome}")

    place_bet(domain, market_id, amount, outcome, api_key)


def main():
    parser = argparse.ArgumentParser(description="Run daily conviction betting bot.")
    parser.add_argument("--domain", required=False, help="Domain for SocialPredict API")
    parser.add_argument("--market_id", type=int, required=False, help="MarketID for Market In Question")    
    parser.add_argument("--user_id", required=False, help="Bot user ID (used to fetch balance)")
    parser.add_argument("--username", required=False, help="Bot username in SocialPredict")
    parser.add_argument("--api_key", required=False, help="SocialPredict API Key (currently unused)")
    parser.add_argument("--identifier", required=True, help="Asset or entity identifier (e.g., 'NVIDIA')")

    args = parser.parse_args()

    run_betting_bot(

        identifier=args.identifier,
        domain=args.domain,
        market_id=args.market_id,
        api_key=args.api_key

    )