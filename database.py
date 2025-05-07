# database.py
import sqlite3
from config import DB_NAME # Make sure DB_NAME is correctly defined in config.py
import logging
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)

def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database '{DB_NAME}': {e}")
        return None

def create_tables():
    conn = get_db_connection()
    if conn is None:
        logging.critical("CRITICAL: Cannot create tables - Database connection failed.") # More severe log
        raise ConnectionError("DB connection failed for table creation.")
    try:
        with conn:
            cursor = conn.cursor()
            # Stocks table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Stocks (
                ticker TEXT PRIMARY KEY,
                company_name TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            logging.info("Checked/Created Stocks table.")

            # NewsMediaItems Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS NewsMediaItems (
                id INTEGER PRIMARY KEY AUTOINCREMENT, -- Auto-incrementing ID
                ticker TEXT NOT NULL,
                headline TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                publisher_name TEXT,
                full_text_content TEXT,
                published_at TIMESTAMP,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sentiment_score REAL,
                sentiment_label TEXT,
                FOREIGN KEY (ticker) REFERENCES Stocks (ticker) ON DELETE CASCADE
            );
            """)
            logging.info("Checked/Created NewsMediaItems table.")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_newsmedia_ticker_published ON NewsMediaItems (ticker, published_at DESC);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_newsmedia_url ON NewsMediaItems (url);") # For UNIQUE constraint

            # RedditItems Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS RedditItems (
                reddit_id TEXT PRIMARY KEY,     -- PRAW's submission.id or comment.id
                ticker TEXT NOT NULL,
                item_type TEXT NOT NULL,        -- 'post' or 'comment'
                title_text TEXT,                -- For posts (from 'headline' in fetched item)
                body_text_content TEXT,         -- Post selftext or comment body (from 'full_text' in fetched item)
                url TEXT UNIQUE NOT NULL,       -- Permalink
                subreddit_name TEXT,            -- From 'source_name' in fetched item
                author_name TEXT,
                item_score INTEGER,
                num_comments_on_post INTEGER,
                published_at TIMESTAMP,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sentiment_score REAL,
                sentiment_label TEXT,
                FOREIGN KEY (ticker) REFERENCES Stocks (ticker) ON DELETE CASCADE
            );
            """)
            logging.info("Checked/Created RedditItems table.")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reddit_ticker_published ON RedditItems (ticker, published_at DESC);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reddit_url ON RedditItems (url);") # For UNIQUE constraint


        logging.info("All database tables checked/created successfully.")
    except sqlite3.Error as e:
        logging.critical(f"CRITICAL: Error creating tables: {e}", exc_info=True)
        raise
    finally:
        if conn: conn.close()

def save_stock_info(ticker, company_name):
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO Stocks (ticker, company_name, last_updated)
                VALUES (?, ?, ?)
            """, (ticker, company_name, datetime.now(timezone.utc)))
        logging.debug(f"Saved/Updated stock info for {ticker}")
        return True
    except sqlite3.Error as e:
        logging.error(f"Error saving stock info for {ticker}: {e}")
        return False
    finally:
        if conn: conn.close()

def _parse_datetime(published_str):
    """Helper to parse datetime strings robustly, returning timezone-aware UTC datetime or None."""
    if not published_str: return None
    try:
        if isinstance(published_str, datetime): # If already a datetime object
            if published_str.tzinfo is None or published_str.tzinfo.utcoffset(published_str) is None:
                return published_str.replace(tzinfo=timezone.utc) # Assume UTC if naive
            return published_str.astimezone(timezone.utc) # Convert to UTC if timezone-aware

        # Handle ISO format strings, especially those ending with 'Z'
        if published_str.endswith('Z'):
            published_str = published_str[:-1] + '+00:00'
        dt = datetime.fromisoformat(published_str)
        
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.replace(tzinfo=timezone.utc) # Assume UTC if naive
        return dt.astimezone(timezone.utc) # Convert to UTC
    except ValueError:
        logging.warning(f"Could not parse timestamp: '{published_str}'. Storing as NULL.")
        return None
    except Exception as e:
        logging.error(f"Unexpected error parsing timestamp '{published_str}': {e}")
        return None

# --- Internal save functions for each table ---
def _save_news_media_items_internal(conn, ticker_symbol, news_items):
    tuples_to_save = []
    for item in news_items:
        url = item.get('url')
        if not url: # URL is critical for news items as unique identifier
            logging.warning(f"Skipping news item due to missing URL: {item.get('headline', 'No Headline')}")
            continue
        tuples_to_save.append((
            ticker_symbol,
            item.get('headline', 'N/A')[:500], # Limit headline length
            url,
            item.get('source_name'), # This maps to publisher_name
            item.get('full_text'),   # This maps to full_text_content
            _parse_datetime(item.get('publishedAt'))
        ))
    
    saved_count = 0
    if not tuples_to_save: return 0
    try:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT OR IGNORE INTO NewsMediaItems
            (ticker, headline, url, publisher_name, full_text_content, published_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, tuples_to_save)
        saved_count = cursor.rowcount
        if saved_count > 0: logging.info(f"Saved {saved_count} new news items for {ticker_symbol}.")
    except sqlite3.Error as e:
        logging.error(f"DB Error saving news items for {ticker_symbol}: {e}", exc_info=True)
    return saved_count

def _save_reddit_items_internal(conn, ticker_symbol, reddit_items):
    tuples_to_save = []
    for item in reddit_items:
        reddit_native_id = item.get('id') # This is 'reddit_id' (PK)
        url = item.get('url')
        if not reddit_native_id or not url:
            logging.warning(f"Skipping Reddit item due to missing 'id' or 'url': Title='{item.get('headline')}'")
            continue
        
        tuples_to_save.append((
            reddit_native_id,
            ticker_symbol,
            item.get('source_type', 'reddit_unknown').replace('reddit_', ''), # 'post' or 'comment'
            item.get('title_text', item.get('headline')), # 'title_text' for DB
            item.get('body_text_content', item.get('full_text')), # 'body_text_content' for DB
            url,
            item.get('source_name'), # subreddit_name
            item.get('author_name', 'N/A'),
            item.get('item_score', 0),
            item.get('num_comments_on_post', 0),
            _parse_datetime(item.get('publishedAt'))
        ))

    saved_count = 0
    if not tuples_to_save: return 0
    try:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT OR IGNORE INTO RedditItems
            (reddit_id, ticker, item_type, title_text, body_text_content, url, subreddit_name, author_name, item_score, num_comments_on_post, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuples_to_save)
        saved_count = cursor.rowcount
        if saved_count > 0: logging.info(f"Saved {saved_count} new Reddit items for {ticker_symbol}.")
    except sqlite3.Error as e:
        logging.error(f"DB Error saving Reddit items for {ticker_symbol}: {e}", exc_info=True)
    return saved_count


# --- Public function to save content (this is what app.py imports) ---
def save_content_items(ticker_symbol, content_items_list):
    """
    Routes content items to their respective internal save functions based on 'source_type'.
    """
    if not content_items_list: return 0
    conn = get_db_connection()
    if conn is None: return 0

    news_to_save, reddit_to_save = [], []
    for item in content_items_list:
        source_type = item.get('source_type', 'unknown').lower()
        if 'news' in source_type: news_to_save.append(item)
        elif 'reddit' in source_type: reddit_to_save.append(item)
        else: logging.warning(f"Unknown source_type '{source_type}' for item URL: {item.get('url')}")

    total_saved_count = 0
    try:
        with conn: # Use a single transaction for all saves
            if news_to_save:
                total_saved_count += _save_news_media_items_internal(conn, ticker_symbol, news_to_save)
            if reddit_to_save:
                total_saved_count += _save_reddit_items_internal(conn, ticker_symbol, reddit_to_save)
       
        if total_saved_count > 0:
            logging.info(f"Successfully saved a total of {total_saved_count} items to DB for {ticker_symbol}.")
    except sqlite3.Error as e: # Catch transaction-level errors if any
        logging.error(f"Transaction error during save_content_items for {ticker_symbol}: {e}", exc_info=True)
    finally:
        if conn: conn.close() # Ensure connection is closed even if transaction context manager was used.
    
    return total_saved_count


def update_sentiment_for_items(analyzed_results_list):
    """Updates sentiment for items in their respective tables using their source-specific ID or URL."""
    if not analyzed_results_list: return 0
    conn = get_db_connection()
    if conn is None: return 0

    updates_by_table = {'NewsMediaItems': [], 'RedditItems': []}
    # Define the ID column used in the WHERE clause for each table
    id_column_map = {'NewsMediaItems': 'url', 'RedditItems': 'reddit_id'}

    for result in analyzed_results_list:
        score = result.get('score')
        label = result.get('label')
        source_type = result.get('source_type', 'unknown').lower()
        item_identifier = result.get('source_specific_id') # Should be populated by sentiment_analyzer
        
        table_name = None
        id_column_name = None

        if 'news' in source_type:
            table_name = 'NewsMediaItems'
            id_column_name = id_column_map[table_name]
            # For news, source_specific_id in analyzed_results should be the URL
            if not item_identifier: item_identifier = result.get('url') 
        elif 'reddit' in source_type:
            table_name = 'RedditItems'
            id_column_name = id_column_map[table_name]
            id_column_name = id_column_map[table_name]
        else:
            logging.warning(f"Cannot update sentiment for unknown source_type: {source_type}")
            continue

        if table_name and item_identifier is not None and score is not None and label is not None:
            updates_by_table[table_name].append((score, label, item_identifier))
        else:
            logging.warning(f"Skipping sentiment update due to missing data: ID={item_identifier}, Score={score}, Label={label} for {source_type}")

    total_updated_count = 0
    try:
        with conn:
            cursor = conn.cursor()
            for table_name, updates in updates_by_table.items():
                if updates:
                    id_col_for_where = id_column_map[table_name]
                    # Only update if sentiment_score is currently NULL (avoid re-processing)
                    # Or remove "AND sentiment_score IS NULL" to always update.
                    sql = f""" 
                        UPDATE {table_name}
                        SET sentiment_score = ?, sentiment_label = ?
                        WHERE {id_col_for_where} = ? AND (sentiment_score IS NULL OR sentiment_label IS NULL)
                    """
                    try:
                        cursor.executemany(sql, updates)
                        updated_for_table = cursor.rowcount
                        if updated_for_table > 0:
                            logging.info(f"Updated sentiment for {updated_for_table} items in {table_name}.")
                        total_updated_count += updated_for_table
                    except sqlite3.Error as e_table:
                        logging.error(f"Error updating {table_name}: {e_table}. Updates: {updates[:2]}") # Log first few failing updates
    except sqlite3.Error as e:
        logging.error(f"Transaction error during update_sentiment_for_items: {e}", exc_info=True)
    finally:
        if conn: conn.close()
    return total_updated_count

if __name__ == "__main__":
    print(f"Initializing database '{DB_NAME}'...")
    create_tables() # This will also create indexes
    print("Database initialization complete.")