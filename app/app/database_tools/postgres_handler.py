#!/usr/local/bin/python

import json
import psycopg2
from psycopg2 import sql
import psycopg2.extras
from dateutil import parser as date_parser
import sys

class PostgresHandler:
    def __init__(self, host="localhost", port=5440, dbname="newsdb", user="user", password="password"):
        self.config = {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password,
        }
        self.conn = None
        self.connect()

    def connect(self):
        """Establish a connection to the Postgres database."""
        try:
            self.conn = psycopg2.connect(**self.config)
            self.conn.autocommit = True
            self.create_news_table()
            self.create_sentiment_table()
        except Exception as e:
            print(f"Error connecting to Postgres: {e}")
            raise

    @staticmethod
    def parse_pub_date(raw_date):
        try:
            return date_parser.parse(raw_date)
        except Exception as e:
            print(f"Error parsing date: {raw_date}\n{e}", file=sys.stderr)
            return None

    def create_news_table(self):
        """Create the news table if it doesn't already exist."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    id SERIAL PRIMARY KEY,
                    inserted_at TIMESTAMPTZ DEFAULT NOW(),                        
                    title TEXT NOT NULL,
                    pub_date TIMESTAMPTZ,
                    source TEXT,
                    search_term TEXT
                )
            """)
            print("Ensured that the 'news' table exists.")

    def create_sentiment_table(self):
        """Create the sentiment_results table if it doesn't already exist."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_results (
                    id SERIAL PRIMARY KEY,
                    inserted_at TIMESTAMPTZ DEFAULT NOW(),                        
                    sentiment JSON NOT NULL,
                    identifier TEXT,
                    bot_name TEXT    -- <-- Add this line
                )
            """)
            print("Ensured that the 'sentiment_results' table exists.")


    def fetch_news_headlines(self, identifier_filter=None, since_published=None, since_inserted=None):
        query = "SELECT id, title, pub_date, inserted_at, source FROM news"
        clauses = []
        params = []

        if identifier_filter:
            clauses.append("search_term = %s")
            params.append(identifier_filter)
        if since_published:
            clauses.append("pub_date >= %s")
            params.append(since_published)
        if since_inserted:
            clauses.append("inserted_at >= %s")
            params.append(since_inserted)

        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id;"

        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(query, tuple(params))
            return cur.fetchall()

    def fetch_sentiment_results(self, identifier_filter, since=None):
        """
        Fetch sentiment results that match the given identifier and are newer than `since` timestamp.

        Parameters:
            identifier_filter (str): String to filter the identifier column (case-insensitive).
            since (datetime, optional): Only return rows inserted after this timestamp.

        Returns:
            list of tuple: Each tuple represents a row in the sentiment_results table.
        """
        with self.conn.cursor() as cur:
            query = """
                SELECT id, sentiment, inserted_at, identifier
                FROM sentiment_results
                WHERE identifier ILIKE %s
            """
            params = [f"%{identifier_filter}%"]

            if since:
                query += " AND inserted_at >= %s"
                params.append(since)

            query += " ORDER BY inserted_at DESC;"
            cur.execute(query, tuple(params))
            return cur.fetchall()
        
    def get_most_recent_sentiment_result(self, identifier: str, since=None):
        """
        Fetch the most recent sentiment result for an exact identifier, optionally filtered by timestamp.

        Parameters:
            identifier (str): Exact match for the identifier column (e.g., "sp500").
            since (datetime, optional): Only return results inserted at or after this timestamp.

        Returns:
            tuple or None: A single row as (id, sentiment, inserted_at, identifier), or None if not found.
        """
        with self.conn.cursor() as cur:
            query = """
                SELECT id, sentiment, inserted_at, identifier
                FROM sentiment_results
                WHERE identifier = %s
            """
            params = [identifier]

            if since:
                query += " AND inserted_at >= %s"
                params.append(since)

            query += " ORDER BY inserted_at DESC LIMIT 1;"

            cur.execute(query, tuple(params))
            return cur.fetchone()    

    def insert_news_items(self, news_items, search_term):
        """
        Insert multiple news items into the database.

        Parameters:
            news_items (list of tuple): Each tuple should have (title, pub_date, source)
            search_term (str): Topic identifier to associate with the news items
        """
        with self.conn.cursor() as cur:
            insert_query = sql.SQL("""
                INSERT INTO news (title, pub_date, source, search_term)
                VALUES (%s, %s, %s, %s)
            """)

            rows_to_insert = []
            for title, raw_date, source in news_items:
                parsed_date = self.parse_pub_date(raw_date)
                if parsed_date is None:
                    print(f"Skipping insertion due to invalid date: {raw_date}", file=sys.stderr)
                    continue
                rows_to_insert.append((title, parsed_date, source, search_term))

            if not rows_to_insert:
                print("No valid news items to insert.")
                return

            cur.executemany(insert_query, rows_to_insert)
            print(f"Inserted {len(rows_to_insert)} news items into the database.")

    def insert_sentiment_result(self, sentiment_json, identifier=None, bot_name=None):
        """
        Insert a sentiment result into the sentiment_results table.

        Parameters:
            sentiment_json (dict or str): JSON object or string representing the sentiment analysis result.
            identifier (str): Optional text identifier to label the result.
            bot_name (str): Optional, the bot name or username.
        """
        with self.conn.cursor() as cur:
            insert_query = sql.SQL("""
                INSERT INTO sentiment_results (sentiment, identifier, bot_name)
                VALUES (%s, %s, %s)
            """)
            cur.execute(insert_query, (json.dumps(sentiment_json), identifier, bot_name))
            print("Inserted sentiment result into the database.")

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Closed the database connection.")

# Simple test routine to verify the connection
if __name__ == "__main__":
    try:
        # Use default connection parameters or override with your own values
        handler = PostgresHandler(
            host="localhost",   # or "localhost" if testing locally
            port=5440,
            dbname="newsdb",
            user="user",
            password="password"
        )
        print("Connection to Postgres established and table ensured.")
    except Exception as e:
        print("Test failed:", e)
    finally:
        if 'handler' in locals():
            handler.close()
