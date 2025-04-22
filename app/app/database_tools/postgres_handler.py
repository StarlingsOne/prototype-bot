#!/usr/local/bin/python

import psycopg2
from psycopg2 import sql

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

    def create_news_table(self):
        """Create the news table if it doesn't already exist."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    pub_date TEXT,
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
                    sentiment JSON NOT NULL,
                    inserted_at TIMESTAMPTZ DEFAULT NOW(),
                    identifier TEXT
                )
            """)
            print("Ensured that the 'sentiment_results' table exists.")

    def fetch_news_headlines(self, identifier_filter=None, since=None):
        """
        Fetch news items from the database, optionally filtered by keyword and date.

        Returns:
            list of tuple: Each tuple contains (id, title, pub_date, source)
        """
        query = "SELECT id, title, pub_date, source FROM news"
        clauses = []
        params = []

        if identifier_filter:
            clauses.append("search_term = %s")
            params.append(identifier_filter)

        if since:
            clauses.append("pub_date >= %s")
            params.append(since)

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY id;"

        with self.conn.cursor() as cur:
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
            cur.executemany(insert_query, [(title, pub_date, source, search_term) for title, pub_date, source in news_items])
            print(f"Inserted {len(news_items)} news items into the database.")

    def insert_sentiment_result(self, sentiment_json, identifier=None):
        """
        Insert a sentiment result into the sentiment_results table.

        Parameters:
            sentiment_json (dict or str): A JSON object (or string) representing the sentiment analysis result.
            identifier (str): Optional text identifier to label the result.
        """
        with self.conn.cursor() as cur:
            insert_query = sql.SQL("""
                INSERT INTO sentiment_results (sentiment, identifier)
                VALUES (%s, %s)
            """)
            cur.execute(insert_query, (sentiment_json, identifier))
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
