import json
import argparse
import requests
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import PostgresHandler
from input.postgres_handler import PostgresHandler

def fetch_market_price(domain, market_id):
    url = f"{domain}/v0/markets/{market_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data["market"]["probability"]
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
    results = db.fetch_sentiment_results(identifier, since=since)
    db.close()

    if not results:
        return None

    sentiment_raw = results[0][1]
    return json.loads(sentiment_raw) if isinstance(sentiment_raw, str) else sentiment_raw

def calculate_bet_amount(conviction, assessment, market_price, user_balance, scale=100):
    if conviction <= market_price:
        return 0
    return min(int((conviction - market_price) * scale * assessment), user_balance)

def place_bet(username, market_id, amount, outcome="yes"):
    payload = {
        "username": username,
        "marketId": market_id,
        "amount": amount,
        "outcome": outcome
    }
    response = requests.post("http://localhost:8080/v0/bet", json=payload)
    if response.ok:
        print("✅ Bet placed successfully!")
    else:
        print("❌ Failed to place bet:", response.text)

def run_betting_bot(identifier):
    sentiment_data = get_latest_sentiment(identifier)

    if not sentiment_data:
        print(f"⚠️ No sentiment data found for '{identifier}' in the last 24 hours — skipping bet.")
        return

    print(f"conviction {sentiment_data["conviction"]}")
    print(f"conviction type: {type(sentiment_data["conviction"])}")

    print(f"assessment {sentiment_data["assessment"]}")
    print(f"assessment type: {type(sentiment_data["assessment"])}")

    # market_price = fetch_market_price(domain, market_id)
    # user_balance = fetch_user_balance(domain, username)

    # amount = calculate_bet_amount(conviction, assessment, market_price, user_balance)

    # if amount > 0:
    #    print(f"📈 Placing bet of {amount} (conviction: {conviction}, market price: {market_price})")
    #    place_bet(username, market_id, amount)
    # else:
    #    print(f"🛑 Conviction ({conviction}) not greater than market price ({market_price}); no bet placed.")



def main():
    parser = argparse.ArgumentParser(description="Run daily conviction betting bot.")
    parser.add_argument("--domain", required=False, help="Domain for SocialPredict API")
    parser.add_argument("--user_id", required=False, help="Bot user ID (used to fetch balance)")
    parser.add_argument("--username", required=False, help="Bot username in SocialPredict")
    parser.add_argument("--api_key", required=False, help="SocialPredict API Key (currently unused)")
    parser.add_argument("--identifier", required=True, help="Asset or entity identifier (e.g., 'NVIDIA')")
    parser.add_argument("--market_id", type=int, required=False, help="Market ID for the prediction market")

    args = parser.parse_args()
    run_betting_bot(

        identifier=args.identifier,

    )
