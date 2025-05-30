# news_utils.py
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database_tools.postgres_handler import PostgresHandler

def news_recently_loaded(topic, since_minutes=30):
    """Return True if news for topic has been loaded in the last since_minutes."""
    db_handler = PostgresHandler()
    since = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
    results = db_handler.fetch_news_headlines(identifier_filter=topic, since=since)
    db_handler.close()
    return bool(results)
