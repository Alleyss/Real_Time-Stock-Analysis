# database.py
import sqlite3
from config import DB_NAME
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
        # Enable foreign key support if using relationships
        # conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database: {e}")
        return None

def create_tables():
    """Creates the necessary tables in the database if they don't exist."""
    conn = get_db_connection()
    if conn is None:
        logging.error("Cannot create tables: Database connection failed.")
        return

    try:
        with conn: # Use context manager for commit/rollback
            cursor = conn.cursor()
            # Stocks table - Basic info about tracked stocks
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Stocks (
                ticker TEXT PRIMARY KEY,
                company_name TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            logging.info("Checked/Created Stocks table.")

            # News Articles table - Stores fetched news data
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS NewsArticles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                headline TEXT NOT NULL,
                source TEXT,
                url TEXT UNIQUE NOT NULL, -- Unique URL to prevent duplicates
                content TEXT,             -- For full article text later (Phase 2+)
                published_at TIMESTAMP,   -- Timestamp from the source
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When we fetched it
                sentiment_score REAL,     -- Populated by analysis
                sentiment_label TEXT,     -- e.g., 'POSITIVE', 'NEGATIVE', 'NEUTRAL'
                FOREIGN KEY (ticker) REFERENCES Stocks (ticker)
            );
            """)
            logging.info("Checked/Created NewsArticles table.")

            # Add index for faster lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_ticker_published ON NewsArticles (ticker, published_at DESC);")
            logging.info("Checked/Created index on NewsArticles.")

        logging.info("Database tables checked/created successfully.")

    except sqlite3.Error as e:
        logging.error(f"Error creating tables: {e}")
    finally:
        if conn:
            conn.close()
            # logging.info("Database connection closed after table creation.") # Optional log

def save_stock_info(ticker, company_name):
    """Saves or updates basic stock information."""
    conn = get_db_connection()
    if conn is None: return False

    try:
        with conn:
            cursor = conn.cursor()
            # Use INSERT OR REPLACE to handle existing tickers
            cursor.execute("""
                INSERT OR REPLACE INTO Stocks (ticker, company_name, last_updated)
                VALUES (?, ?, ?)
            """, (ticker, company_name, datetime.now()))
            logging.info(f"Saved/Updated stock info for {ticker}")
        return True
    except sqlite3.Error as e:
        logging.error(f"Error saving stock info for {ticker}: {e}")
        return False
    finally:
        if conn: conn.close()

def save_news_articles(ticker, articles):
    """Saves fetched news articles to the database, avoiding duplicates based on URL."""
    if not articles:
        logging.warning("No articles provided to save.")
        return 0

    conn = get_db_connection()
    if conn is None: return 0

    saved_count = 0
    articles_to_save = []
    for article in articles:
        # Parse timestamp string into datetime object if possible
        published_dt = None
        published_str = article.get('publishedAt')
        if published_str:
            try:
                # Handle different possible formats, especially the 'Z' for UTC
                published_str = published_str.replace('Z', '+00:00')
                published_dt = datetime.fromisoformat(published_str)
            except ValueError:
                logging.warning(f"Could not parse timestamp: {published_str} for URL {article.get('url')}")

        articles_to_save.append((
            ticker,
            article.get('title'),
            article.get('source', {}).get('name'), # Safely access nested dict
            article.get('url'),
            published_dt # Store as datetime object
            # Add 'content' here in Phase 2+
        ))

    try:
        with conn:
            cursor = conn.cursor()
            # Use INSERT OR IGNORE to skip insertion if URL constraint is violated (duplicate)
            cursor.executemany("""
                INSERT OR IGNORE INTO NewsArticles (ticker, headline, source, url, published_at)
                VALUES (?, ?, ?, ?, ?)
            """, articles_to_save)
            # The rowcount gives the number of rows *affected* (inserted or updated)
            # For INSERT OR IGNORE, it's the count of successful inserts.
            saved_count = cursor.rowcount
            logging.info(f"Attempted to save {len(articles_to_save)} articles for {ticker}. Successfully saved {saved_count} new articles.")
    except sqlite3.Error as e:
        logging.error(f"Error saving news articles for {ticker}: {e}")
    finally:
        if conn:
            conn.close()

    return saved_count


# --- Main execution block ---
if __name__ == "__main__":
    print(f"Initializing database '{DB_NAME}'...")
    create_tables()
    print("Database initialization complete.")      