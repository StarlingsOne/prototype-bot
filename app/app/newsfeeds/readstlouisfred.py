#!/usr/local/bin/python

import requests
import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database_tools.postgres_handler import PostgresHandler
from intake_streams.stlouisfred import build_fred_url

KEY_FILE_PATH = os.path.join(os.environ["KEYS_DIR"], "stlouisfred", "stlouisfred_key")

try:
    with open(KEY_FILE_PATH, "r") as key_file:
        api_key = key_file.read().strip()
except FileNotFoundError:
    print(f"Error: API key file not found at {KEY_FILE_PATH}", file=sys.stderr)
    sys.exit(1)

def fetch_sp500_prices_from_api(start_date, end_date):
    url = build_fred_url(api_key, start_date, end_date)
    print(f"Fetching from FRED URL: {url}")
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Error: FRED API {url} (status: {resp.status_code})", file=sys.stderr)
        return {}
    js = resp.json()
    obs = js.get("observations", [])
    return {ob["date"]: float(ob["value"]) for ob in obs if ob.get("value") and ob["value"] != "."}

def fetch_sp500_prices_last_7_days():
    db_handler = PostgresHandler()
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=7)
    # 1. Get all prices for last 7 days from DB
    db_prices = db_handler.fetch_sp500_prices_between(start_date, today)
    db_price_dict = {row["price_date"].strftime("%Y-%m-%d"): row["close_value"] for row in db_prices}
    # 2. Find missing days
    all_days = [(today - timedelta(days=d)).strftime("%Y-%m-%d") for d in range(7, -1, -1)]
    missing = [d for d in all_days if d not in db_price_dict]
    if not missing:
        return db_price_dict  # All up to date
    # 3. Rate limit: don't call API if last insert <5min ago
    last_insert = db_handler.fetch_last_sp500_price_insert_time()
    if last_insert and (datetime.utcnow() - last_insert).total_seconds() < 300:
        print("API recently called (<5min ago); skipping FRED fetch. Returning database values only.")
        return db_price_dict
    # 4. Batch API call for missing window
    api_prices = fetch_sp500_prices_from_api(min(missing), max(missing))
    for date, value in api_prices.items():
        if not db_handler.has_sp500_price_for_date(date):
            db_handler.insert_sp500_price(date, value, source="fred")
            db_price_dict[date] = value
    db_handler.close()
    return db_price_dict

def main():

    price_dict = fetch_sp500_prices_last_7_days()
    print("S&P500 closing prices (last 7 days):")
    for date in sorted(price_dict):
        print(f"{date}: {price_dict[date]}")


if __name__ == "__main__":
    main()
