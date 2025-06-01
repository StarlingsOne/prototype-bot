# news_utils.py
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database_tools.postgres_handler import PostgresHandler

def news_recently_inserted(topic, since_insertion_hours=0.5):
    """Return True if news for topic has been inserted in the last N hours (using inserted_at)."""
    db_handler = PostgresHandler()
    since = datetime.now(timezone.utc) - timedelta(hours=since_insertion_hours)
    results = db_handler.fetch_news_headlines(identifier_filter=topic, since_inserted=since)
    db_handler.close()
    return bool(results)

def news_recently_published(topic, since_publication_hours=2.0):
    """Return True if news for topic has been published in the last N hours (using pub_date)."""
    db_handler = PostgresHandler()
    since = datetime.now(timezone.utc) - timedelta(hours=since_publication_hours)
    results = db_handler.fetch_news_headlines(identifier_filter=topic, since_published=since)
    db_handler.close()
    return bool(results)