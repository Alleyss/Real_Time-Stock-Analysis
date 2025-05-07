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
    """Saves fetched news articles, including full text content if available."""
    if not articles:
        logging.warning("No articles provided to save.")
        return 0

    conn = get_db_connection()
    if conn is None: return 0

    saved_count = 0
    articles_to_save = []
    for article in articles:
        published_dt = None
        published_str = article.get('publishedAt')
        if published_str:
            try:
                published_str = published_str.replace('Z', '+00:00')
                published_dt = datetime.fromisoformat(published_str)
            except ValueError:
                logging.warning(f"Could not parse timestamp: {published_str} for URL {article.get('url')}")

        # >>> Add full_text to the tuple <<<
        articles_to_save.append((
            ticker,
            article.get('title'),
            article.get('source', {}).get('name'),
            article.get('url'),
            article.get('full_text'), # Get the fetched full text
            published_dt
        ))

    try:
        with conn:
            cursor = conn.cursor()
            # >>> Update INSERT statement to include the content column <<<
            cursor.executemany("""
                INSERT OR IGNORE INTO NewsArticles
                (ticker, headline, source, url, content, published_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, articles_to_save)
            saved_count = cursor.rowcount
            logging.info(f"Attempted to save {len(articles_to_save)} articles for {ticker}. Successfully saved {saved_count} new articles (with content).")
    except sqlite3.Error as e:
        logging.error(f"Error saving news articles for {ticker}: {e}")
    finally:
        if conn:
            conn.close()

    return saved_count

def update_article_sentiment(analyzed_results):
    """Updates the sentiment score and label for articles already in the database."""
    if not analyzed_results:
        logging.warning("No analyzed results provided to update sentiment.")
        return 0

    conn = get_db_connection()
    if conn is None: return 0

    updates_to_perform = []
    for result in analyzed_results:
        url = result.get('url')
        score = result.get('score') # This is the normalized [-1, 1] score
        label = result.get('label') # This is 'positive', 'negative', 'neutral'

        if url is not None and score is not None and label is not None:
            updates_to_perform.append((score, label, url))
        else:
            logging.warning(f"Skipping sentiment update for item due to missing data: URL={url}, Score={score}, Label={label}")

    if not updates_to_perform:
        logging.warning("No valid data found in analyzed_results for sentiment update.")
        return 0

    updated_count = 0
    try:
        with conn:
            cursor = conn.cursor()
            # Prepare and execute the UPDATE statement
            cursor.executemany("""
                UPDATE NewsArticles
                SET sentiment_score = ?, sentiment_label = ?
                WHERE url = ?
            """, updates_to_perform)
            updated_count = cursor.rowcount # Number of rows actually updated
            logging.info(f"Attempted to update sentiment for {len(updates_to_perform)} articles. Successfully updated {updated_count} rows.")
    except sqlite3.Error as e:
        logging.error(f"Error updating article sentiments in database: {e}")
    finally:
        if conn:
            conn.close()

    return updated_count
# --- Main execution block ---
if __name__ == "__main__":
    print(f"Initializing database '{DB_NAME}'...")
    create_tables()
    print("Database initialization complete.")      