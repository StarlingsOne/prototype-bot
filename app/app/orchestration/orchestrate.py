#!/usr/bin/env python3

import argparse
from datetime import datetime, timezone, timedelta
import subprocess
import yaml
import os
import random
import time
import sys
import os
from prediction_market.api import extract_market_context, fetch_user_info, fetch_maximum_debt_allowed
from prompts.generate_prompt import generate_prompt
from newsfeeds.readnews import ingest_news_for_topic
from newsfeeds.readstlouisfred import fetch_sp500_prices_last_7_days
from sentiment.sentiment import main as sentiment
from newsfeeds.news_utils import news_recently_inserted
from database_tools.postgres_handler import PostgresHandler

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
NEWSFEEDS_DIR = os.path.join(PROJECT_ROOT, "newsfeeds")
BETTINGBOT_PATH = os.path.join(PROJECT_ROOT, "bettingbot", "bettingbot")

if NEWSFEEDS_DIR not in sys.path:
    sys.path.insert(0, NEWSFEEDS_DIR)

from news_utils import news_recently_inserted


TEMPLATE_CONFIG = {
    "since_hours": 2,
    "domain": "http://localhost",
    "market_ids": [3],
    "username": "default",
    "api_key": "MISSING_API_KEY",
    "topic": None,
    "prompt": "headline_sentiment.prompt",
}

def run_cmd(cmd_list):
    adjusted_cmd_list = [
        os.path.join(PROJECT_ROOT, cmd) if cmd.startswith("./input") or cmd.startswith("./output") else cmd
        for cmd in cmd_list
    ]
    print(f"\n→ Running: {' '.join(map(str, adjusted_cmd_list))}")
    try:
        subprocess.run(adjusted_cmd_list, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        return False

def run_pipeline(bot_name: str, config: dict, since_insertion_hours=0.5):
    topic = config.get("topic")
    prompt_template = config.get("prompt")
    since_publication_hours = config.get("since_hours")
    domain = config.get("domain")
    username = config.get("username")
    market_ids = config.get("market_ids", [])

    if not topic:
        raise ValueError(f"Missing topic for bot '{bot_name}'")

    print(f"\n=== Running bot '{bot_name}' for topic '{topic}' ===")
    print(f"📅 {datetime.now().isoformat()}")

    # 1. News ingestion
    if news_recently_inserted(topic, since_insertion_hours):
        print(f"⏩ News for topic '{topic}' inserted in last {since_insertion_hours} hours. Skipping readnews.")
    else:
        try:
            ingest_news_for_topic(topic)
        except Exception as e:
            print(f"⚠️ Failed reading news for bot '{bot_name}': {e}")
            return
                
    # 2. Fetch headlines from DB (using your existing logic)
    db_handler = PostgresHandler()
    since = datetime.now(timezone.utc) - timedelta(hours=since_publication_hours)
    headlines = db_handler.fetch_news_headlines(identifier_filter=topic, since_published=since)
    db_handler.close()

    print(f"Queried headlines since {since} (UTC): found {len(headlines) if headlines else 0}")
    if not headlines:
        # Optionally print the most recent news item's pub_date for debugging
        debug_db_handler = PostgresHandler()
        recent_items = debug_db_handler.fetch_news_headlines(identifier_filter=topic, since_published=datetime(1970,1,1))
        print("Most recent items (by pub_date):")
        for item in recent_items[:5]:
            print(item)
        debug_db_handler.close()

    # 3. Fetch context for the first market (or loop if you want one per market)
    market_id = market_ids[0] if market_ids else None
    if not (domain and username and market_id):
        print("Missing domain, username, or market_id for context build.")
        return

    # --- Fetch Prediction Market API data ---
    try:
        print("Fetching market info...")
        market_json = extract_market_context(domain, market_id)
        print("Fetching user info...")
        user_json = fetch_user_info(domain, username)
        print("Fetching setup info...")
        max_debt = fetch_maximum_debt_allowed(domain)
    except Exception as e:
        print(f"Error fetching market/user/setup info: {e}")
        return

    # Optionally compute hours to resolution
    hours_to_resolution = None
    if market_json.get("resolution_datetime", ""):
        try:
            dt_resolution = datetime.fromisoformat(market_json.get("resolution_datetime", "").replace("Z", "+00:00"))
            hours_to_resolution = (dt_resolution - datetime.now(timezone.utc)).total_seconds() / 3600
        except Exception:
            pass

    context = {
        "question_title": market_json["question_title"],
        "resolution_datetime": market_json.get("resolution_datetime", ""),
        "hours_to_resolution": hours_to_resolution,
        "market_current_probability": market_json["market_current_probability"],
        "market_total_volume": market_json.get("totalVolume", 0),
        "bot_balance": user_json.get("accountBalance", 0),
        "maximum_debt_allowed": max_debt,
        "topic": topic,
        "headlines": headlines,
        "sp500_fred_api_price_7_day_history": dict(sorted(fetch_sp500_prices_last_7_days().items())[-5:]),
        "today_datetime_utc": datetime.now(timezone.utc).isoformat()
    }

    # --- Generate prompt (now you have all fields ready) ---
    prompt_str = generate_prompt(prompt_template, **context)
    with open("/tmp/generated_prompt.txt", "w") as f:
        f.write(prompt_str)

    # 5: Call sentiment script (pass prompt via file, stdin, or CLI arg)
    sentiment_cmd = [
        "python3", "-m", "sentiment.sentiment",
        "--prompt_file", "/tmp/generated_prompt.txt",
        "--identifier", topic,
        "--username", bot_name
    ]
    run_cmd(sentiment_cmd)

    # Step 6: Betting (unchanged)
    for mid in config["market_ids"]:
        betting_cmd = [
            BETTINGBOT_PATH,
            "--domain", config["domain"],
            "--market_id", str(mid),
            "--username", config["username"],
            "--api_key", config["api_key"],
            "--identifier", topic
        ]
        if not run_cmd(betting_cmd):
            print(f"⚠️ Failed betting for market {mid} in bot '{bot_name}', continuing to next market.")

    RATE_LIMIT_SECONDS = 6
    time.sleep(RATE_LIMIT_SECONDS)


def load_all_bot_configs(yaml_path):
    if not yaml_path or not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Missing config file at: {yaml_path}")
    
    with open(yaml_path, "r") as f:
        all_bots = yaml.safe_load(f)

    merged = {}
    for bot_name, bot_config in all_bots.items():
        config = {**TEMPLATE_CONFIG, **bot_config}
        # Backwards compatibility: convert single market_id to market_ids
        if "market_id" in bot_config and "market_ids" not in bot_config:
            config["market_ids"] = [bot_config["market_id"]]
        merged[bot_name] = config
    return merged


def main():
    parser = argparse.ArgumentParser(description="Run full prediction pipeline for bots.")
    parser.add_argument("config", type=str, help="YAML config file with bot definitions")
    parser.add_argument("--bot", help="Optional: run only a specific bot")
    parser.add_argument("--topic", help="Optional: override topic")
    parser.add_argument("--since_insertion_hours", type=float, default=0.5,  # e.g., 0.5 hours = 30 min
        help="If no news for the topic has been INSERTED in the last N hours, reload news (uses ingest timestamp).")
    parser.add_argument("--since_publication_hours", type=float, default=2.0,
        help="Filter news for sentiment/betting if PUBLISHED in the last N hours (uses article's publication date).")

    args = parser.parse_args()
    bot_configs = load_all_bot_configs(args.config)

    if args.bot:
        if args.bot not in bot_configs:
            raise KeyError(f"Bot '{args.bot}' not found in config.")
        config = bot_configs[args.bot]
        if args.topic:
            config["topic"] = args.topic
        if args.since_publication_hours is not None:
            config["since_publication_hours"] = args.since_publication_hours
        run_pipeline(args.bot, config, since_insertion_hours=args.since_insertion_hours)
    else:
        bot_items = list(bot_configs.items())
        random.shuffle(bot_items)
        for bot_name, config in bot_items:
            if args.since_publication_hours is not None:
                config["since_publication_hours"] = args.since_publication_hours
            run_pipeline(bot_name, config, since_insertion_hours=args.since_insertion_hours)

if __name__ == "__main__":
    main()
