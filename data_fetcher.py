# data_fetcher.py
import yfinance as yf
from newsapi import NewsApiClient
import requests # Keep for future Indian scraping
from bs4 import BeautifulSoup # Keep for future Indian scraping
import logging
from config import NEWSAPI_KEY, NEWS_ARTICLE_COUNT
import time # Import time for delays
from newspaper import Article, ArticleException # <<< Import Newspaper3k >>>
import streamlit as st 
# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize NewsAPI client
if NEWSAPI_KEY:
    newsapi = NewsApiClient(api_key=NEWSAPI_KEY)
else:
    newsapi = None
    logging.warning("NewsAPI client not initialized because NEWSAPI_KEY is missing.")

# --- Phase 1 Implementation ---

# >>> Add Streamlit Caching Decorator <<<
# Cache data for 15 minutes to reduce yfinance calls for repeated analysis
# Use show_spinner=False because the main app has its own spinner
@st.cache_data(ttl="15m", show_spinner=False)
def get_stock_info(ticker):
    """Fetches basic stock information and current price using yfinance. Results are cached."""
    logging.info(f"Executing get_stock_info for {ticker} (Cacheable).") # Log when the actual function runs (not when cache hit)
    try:
        stock = yf.Ticker(ticker)
        info = stock.info # This is often the main call triggering requests

        # Check if info was successfully retrieved
        # >>> Consider adding a check early to avoid further calls if info is empty <<<
        if not info or not info.get('symbol'): # Check for a key field like symbol
             logging.warning(f"Initial info fetch for {ticker} returned empty or invalid data.")
             # Attempt history as a fallback, but the core issue might be the ticker itself
             hist = stock.history(period="1d")
             if hist.empty:
                  logging.error(f"Cannot retrieve info or history for {ticker}. Likely invalid or delisted.")
                  return None # Return None early if basic info fails

             current_price = hist['Close'].iloc[-1]
             company_name = ticker # Default to ticker if name not found
             info_dict = {'symbol': ticker, 'longName': company_name, 'currency': hist.iloc[-1].get('Currency','N/A')} # Basic fallback info
             logging.warning(f"Using fallback history data for {ticker}.")

        else:
             # Proceed with extracting data from the 'info' dict
             current_price = info.get('currentPrice', info.get('regularMarketPrice'))
             if current_price is None: # If both are missing, try 'previousClose' as another fallback
                 current_price = info.get('previousClose', 'N/A')

             company_name = info.get('longName', info.get('shortName', ticker)) # Prefer longName, then shortName
             info_dict = info # Use the full info dict

        logging.info(f"Successfully processed yfinance data for {ticker}")
        # Ensure essential fields exist before returning
        return {"info": info_dict, "current_price": current_price, "company_name": company_name}

    except Exception as e:
        # Catching specific yfinance errors might be helpful if they exist
        logging.error(f"Error fetching yfinance data for {ticker}: {e}")
        # Check if the error message indicates rate limiting specifically
        if "Rate limited" in str(e) or "Too Many Requests" in str(e):
             logging.error(f"RATE LIMIT HIT for {ticker}. Consider waiting before next analysis.")
        return None # Indicate failure

def fetch_full_article_text(url):
    """Uses Newspaper3k to download and extract full text from a URL."""
    if not url:
        return None
    try:
        logging.debug(f"Attempting to fetch full text for: {url}")
        article = Article(url, language='en')
        article.download()
        time.sleep(1) # Be polite between downloads
        article.parse()
        logging.debug(f"Successfully parsed: {url}")
        return article.text
    except ArticleException as e:
        logging.warning(f"Newspaper3k failed for URL {url}: {e}")
        return None # Return None if fetching/parsing fails
    except Exception as e:
        logging.error(f"Unexpected error fetching article {url}: {e}", exc_info=False) # Keep log less verbose
        return None
def get_us_news(query, articles_count=NEWS_ARTICLE_COUNT):
    """
    Fetches news articles using NewsAPI and then attempts to fetch
    the full text for each article using Newspaper3k.
    """
    if not newsapi:
        logging.error("Cannot fetch US news: NewsAPI client not available.")
        return [] # Return empty list if client not set up

    logging.info(f"Fetching initial {articles_count} US news article metadata for query: '{query}' from NewsAPI.")
    initial_articles = []
    try:
        # Fetch metadata first
        all_articles_meta = newsapi.get_everything(q=query,
                                                   language='en',
                                                   sort_by='publishedAt', # Use 'relevancy' if preferred
                                                   page_size=articles_count, # Fetch desired count
                                                   page=1) # Get the first page

        fetched_articles_meta = all_articles_meta.get('articles', [])
        logging.info(f"Fetched metadata for {len(fetched_articles_meta)} articles for '{query}' from NewsAPI.")
        # Filter out articles without URL or title early
        initial_articles = [a for a in fetched_articles_meta if a.get('title') and a.get('title') != '[Removed]' and a.get('url')]
        if len(initial_articles) < len(fetched_articles_meta):
             logging.info(f"Filtered out {len(fetched_articles_meta) - len(initial_articles)} articles with missing title/URL.")

    except Exception as e:
        # Handle potential API errors
        logging.error(f"Error fetching NewsAPI metadata for query '{query}': {e}")
        if hasattr(e, 'response') and e.response is not None:
             try: logging.error(f"NewsAPI Response: {e.response.json()}")
             except: logging.error(f"NewsAPI Response Text: {e.response.text}")
        return [] # Return empty list on API error

    # --- Fetch Full Text using Newspaper3k ---
    enriched_articles = []
    logging.info(f"Attempting to fetch full text for {len(initial_articles)} articles...")
    processed_count = 0
    fetch_success_count = 0
    for article_meta in initial_articles:
        url = article_meta.get('url')
        full_text = fetch_full_article_text(url) # Call the newspaper function
        processed_count += 1
        if full_text:
            article_meta['full_text'] = full_text # Add the full text to the dictionary
            fetch_success_count += 1
        else:
            article_meta['full_text'] = None # Explicitly set to None if failed

        enriched_articles.append(article_meta)
        # Optional: Add progress logging if processing many articles
        # if processed_count % 5 == 0:
        #     logging.info(f"Processed {processed_count}/{len(initial_articles)} articles for full text...")

    logging.info(f"Finished fetching full text. Success rate: {fetch_success_count}/{len(initial_articles)}.")
    return enriched_articles
# --- Placeholder for Phase 2 ---
def scrape_indian_news(ticker):
    """Placeholder for scraping news for Indian stocks."""
    logging.warning(f"Indian news scraping for {ticker} is not implemented in Phase 1.")
    return []