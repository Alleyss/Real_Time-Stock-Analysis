# data_fetcher.py
import yfinance as yf
from newsapi import NewsApiClient
import requests # Keep for future Indian scraping
from bs4 import BeautifulSoup # Keep for future Indian scraping
import logging
from config import NEWSAPI_KEY, NEWS_ARTICLE_COUNT

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize NewsAPI client
if NEWSAPI_KEY:
    newsapi = NewsApiClient(api_key=NEWSAPI_KEY)
else:
    newsapi = None
    logging.warning("NewsAPI client not initialized because NEWSAPI_KEY is missing.")

# --- Phase 1 Implementation ---

def get_stock_info(ticker):
    """Fetches basic stock information and current price using yfinance."""
    logging.info(f"Attempting to fetch stock info for {ticker} using yfinance.")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Check if info was successfully retrieved
        if not info or info.get('regularMarketPrice') is None: # Check for a key field
             logging.warning(f"Could not retrieve valid info for ticker {ticker}. It might be delisted or invalid.")
             # Try history as fallback for price if info missing
             hist = stock.history(period="1d")
             current_price = hist['Close'].iloc[-1] if not hist.empty else 'N/A'
             company_name = ticker # Default to ticker if name not found
             info_dict = {'symbol': ticker, 'longName': company_name} # Basic fallback info
        else:
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A')) # Prefer currentPrice if available
            company_name = info.get('longName', ticker)
            info_dict = info # Use the full info dict

        logging.info(f"Successfully fetched yfinance data for {ticker}")
        return {"info": info_dict, "current_price": current_price, "company_name": company_name}

    except Exception as e:
        # Common errors include connection issues, or invalid tickers yfinance cannot resolve
        logging.error(f"Error fetching yfinance data for {ticker}: {e}")
        return None # Indicate failure

def get_us_news(query, articles_count=NEWS_ARTICLE_COUNT):
    """Fetches news articles for a US stock query using NewsAPI."""
    if not newsapi:
        logging.error("Cannot fetch US news: NewsAPI client not available.")
        return [] # Return empty list if client not set up

    logging.info(f"Fetching up to {articles_count} US news articles for query: '{query}' from NewsAPI.")
    try:
        # Use 'q' for keyword search. Consider adding domains for reliability e.g., domains='wsj.com,reuters.com'
        all_articles = newsapi.get_everything(q=query,
                                              language='en',
                                              sort_by='publishedAt', # Use 'relevancy' if preferred
                                              page_size=articles_count, # Fetch desired count
                                              page=1) # Get the first page

        fetched_articles = all_articles.get('articles', [])
        logging.info(f"Fetched {len(fetched_articles)} articles for '{query}' from NewsAPI.")
        # Optional: Add basic filtering here if needed (e.g., ensure title isn't '[Removed]')
        filtered_articles = [a for a in fetched_articles if a.get('title') and a.get('title') != '[Removed]']
        if len(filtered_articles) < len(fetched_articles):
             logging.info(f"Filtered out {len(fetched_articles) - len(filtered_articles)} articles with missing/removed titles.")

        return filtered_articles

    except Exception as e:
        # Handle potential API errors (rate limits, invalid queries, connection issues)
        logging.error(f"Error fetching NewsAPI data for query '{query}': {e}")
        # Check if the error response is available and log it
        if hasattr(e, 'response') and e.response is not None:
             try:
                 logging.error(f"NewsAPI Response: {e.response.json()}")
             except: # Handle cases where response is not JSON
                 logging.error(f"NewsAPI Response Text: {e.response.text}")
        return [] # Return empty list on error


# --- Placeholder for Phase 2 ---
def scrape_indian_news(ticker):
    """Placeholder for scraping news for Indian stocks."""
    logging.warning(f"Indian news scraping for {ticker} is not implemented in Phase 1.")
    return []