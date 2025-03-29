# database.py
import sqlite3
from config import DB_NAME
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        # Enable foreign key support if you plan to use relationships later
        # conn.execute("PRAGMA foreign_keys = ON;")
        logging.info(f"Successfully connected to database: {DB_NAME}")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database: {e}")
        return None # Indicate failure

def create_tables():
    """Creates the necessary tables in the database if they don't exist."""
    conn = get_db_connection()
    if conn is None:
        logging.error("Cannot create tables: Database connection failed.")
        return

    cursor = conn.cursor()
    try:
        # Stocks table - Basic info about tracked stocks
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Stocks (
            ticker TEXT PRIMARY KEY,
            company_name TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
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
            content TEXT,             -- For full article text later
            published_at DATETIME,    -- Timestamp from the source
            fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- When we fetched it
            sentiment_score REAL,     -- To be populated by analysis phase
            sentiment_label TEXT,     -- e.g., 'positive', 'negative', 'neutral'
            FOREIGN KEY (ticker) REFERENCES Stocks (ticker) -- Optional foreign key link
        );
        """)
        logging.info("Checked/Created NewsArticles table.")

        # Add index for faster lookups later (optional but recommended)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_ticker_published ON NewsArticles (ticker, published_at DESC);")
        logging.info("Checked/Created index on NewsArticles.")

        conn.commit()
        logging.info("Database tables checked/created successfully.")

    except sqlite3.Error as e:
        logging.error(f"Error creating tables: {e}")
    finally:
        if conn:
            conn.close()
            logging.info("Database connection closed.")

# --- Main execution block ---
# Allows running this script directly to initialize the database
if __name__ == "__main__":
    print(f"Initializing database '{DB_NAME}'...")
    create_tables()
    print("Database initialization complete.")