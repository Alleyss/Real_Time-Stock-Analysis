# app/services/data_fetcher_service.py
import logging
import time
import re
from datetime import datetime, timedelta, timezone

import yfinance as yf
from newsapi import NewsApiClient
from newspaper import Article, ArticleException
import praw

from app.core.config import settings # Use backend settings

log = logging.getLogger(__name__)

# --- Initialize API Clients ---
# Note: These are initialized when the module is loaded. For scalability,
# consider managing clients within FastAPI's lifespan or using dependency injection.
newsapi_client = None
if settings.NEWSAPI_KEY:
    try:
        newsapi_client = NewsApiClient(api_key=settings.NEWSAPI_KEY)
        log.info("NewsAPI client initialized.")
    except Exception as e:
        log.error(f"Failed to initialize NewsAPI client: {e}")
else:
    log.warning("NewsAPI client not initialized (NEWSAPI_KEY missing in config).")

reddit_praw_client = None
if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET and settings.REDDIT_USER_AGENT:
    try:
        reddit_praw_client = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
            check_for_async=False
        )
        if reddit_praw_client.read_only:
             log.info("PRAW Reddit client initialized successfully (read-only).")
        else:
             log.warning("PRAW Reddit client initialized, but read_only check failed or skipped.")
    except Exception as e:
        log.error(f"Failed to initialize PRAW Reddit client: {e}")
else:
    log.warning("Reddit API credentials not fully configured. Reddit fetching disabled.")

# --- Helper Functions (Adapted from Streamlit version) ---
def _is_relevant(text_content, ticker_symbol, company_name, min_len, min_mentions):
    """Checks if the article text is relevant."""
    if not text_content or len(text_content) < min_len:
        return False
    mentions = 0
    try:
        ticker_pattern = r'\b{}\b|\${}\b'.format(re.escape(ticker_symbol), re.escape(ticker_symbol))
        mentions += len(re.findall(ticker_pattern, text_content, re.IGNORECASE))
        if company_name and len(company_name) > 2:
            company_pattern = r'\b{}\b'.format(re.escape(company_name))
            mentions += len(re.findall(company_pattern, text_content, re.IGNORECASE))
    except Exception as e:
        log.error(f"Regex error during relevance check: {e}") # Avoid crashing on bad regex
    return mentions >= min_mentions

def _fetch_full_text_newspaper(url):
    """Fetches full text using Newspaper3k."""
    if not url: return None
    try:
        log.debug(f"Newspaper3k: Attempting fetch: {url}")
        article = Article(url, language='en', fetch_images=False, memoize_articles=True)
        article.download()
        article.parse()
        log.debug(f"Newspaper3k: Successfully parsed: {url}")
        return article.text
    except (ArticleException, Exception) as e:
        log.warning(f"Newspaper3k failed for URL {url}: {e}")
        return None

# --- Main Fetching Functions for API ---
def fetch_stock_info(ticker: str) -> dict | None:
    """Fetches basic stock info using yfinance. API Version."""
    log.info(f"Fetching stock info for {ticker} via yfinance.")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        # Simplified logic from prototype - add more fallback/checks if needed
        if not info or not info.get('symbol'):
             log.warning(f"yfinance info for {ticker} is empty/invalid.")
             # Attempt history as a basic fallback for price
             hist = stock.history(period="2d")
             if hist.empty:
                  log.error(f"Cannot retrieve info or history for {ticker}.")
                  return None
             current_price = hist['Close'].iloc[-1] if not hist.empty else 'N/A'
             company_name = ticker
             # Return minimal info structure
             return {
                "symbol": ticker,
                "company_name": company_name,
                "current_price": current_price,
                "currency": info.get('currency', 'N/A'), # Get currency if possible
                "sector": "N/A",
                "industry": "N/A",
                "market_cap": None,
                "error": "Incomplete data from yfinance info, used history fallback."
            }
        else:
            current_price = info.get('currentPrice', info.get('regularMarketPrice', info.get('previousClose')))
            company_name = info.get('longName', info.get('shortName', ticker))
            return {
                "symbol": info.get('symbol'),
                "company_name": company_name,
                "current_price": current_price if current_price is not None else 'N/A',
                "currency": info.get('currency', info.get('financialCurrency')),
                "sector": info.get('sector', 'N/A'),
                "industry": info.get('industry', 'N/A'),
                "market_cap": info.get('marketCap'),
                "info": info # Include raw info dict if needed by frontend
            }
    except Exception as e:
        log.error(f"Error fetching yfinance data for {ticker}: {e}", exc_info=True)
        return None # Indicate failure

def fetch_news_data_service(ticker_symbol: str, company_name: str, articles_count: int = 15) -> list[dict]:
    """Fetches and processes NewsAPI data for the API."""
    if not newsapi_client:
        log.error("NewsAPI client not available for fetching news.")
        return [] # Return empty list, endpoint handler can raise HTTPException

    # Using values from config directly (consider passing them if needed)
    # Assuming NEWS_DOMAIN_BLACKLIST, NEWS_SOURCE_NAME_BLACKLIST are in settings
    # min_len = settings.MIN_ARTICLE_LENGTH_FOR_ANALYSIS
    # min_mentions = settings.MIN_TICKER_MENTIONS_FOR_RELEVANCE
    min_len = 100 # Example defaults if not in settings
    min_mentions = 1 # Example defaults
    domain_blacklist = getattr(settings, "NEWS_DOMAIN_BLACKLIST", []) # Use getattr for safety
    source_blacklist = getattr(settings, "NEWS_SOURCE_NAME_BLACKLIST", [])


    query = f'"{company_name}" OR "{ticker_symbol}"'
    log.info(f"Fetching {articles_count} news for query: '{query}' (Service Layer)")
    
    try:
        api_response = newsapi_client.get_everything(
            q=query, language='en', sort_by='publishedAt',
            page_size=min(articles_count * 2, 100), # Fetch more for filtering
            page=1
        )
        articles_metadata = api_response.get('articles', [])
    except Exception as e:
        log.error(f"NewsAPI error in service for query '{query}': {e}", exc_info=True)
        return []

    processed_content = []
    processed_urls = set()
    for meta in articles_metadata:
        title = meta.get('title')
        url = meta.get('url')
        published_at_str = meta.get('publishedAt')
        source_info = meta.get('source', {})
        source_name = source_info.get('name', 'Unknown News Source')

        if not title or title == '[Removed]' or not url or url in processed_urls or not published_at_str:
            continue
        processed_urls.add(url)

        # --- Filtering ---
        try: # Domain filtering
            domain = url.split('/')[2].replace('www.', '')
            if domain in domain_blacklist: continue
        except IndexError: pass # Ignore bad URLs for domain filter
        if source_name in source_blacklist: continue # Source name filtering
        # --- End Filtering ---

        full_text = _fetch_full_text_newspaper(url)
        if not full_text or len(full_text) < min_len:
            full_text = meta.get('description', title)
            if not full_text: full_text = title

        # Use _is_relevant helper
        if _is_relevant(full_text, ticker_symbol, company_name, min_len, min_mentions):
            processed_content.append({
                'id': url, # Use URL as ID for news consistency
                'headline': title,
                'full_text': full_text,
                'url': url,
                'publishedAt': published_at_str,
                'source_name': source_name,
                'source_type': 'news'
            })
            if len(processed_content) >= articles_count: break # Stop when count reached

    log.info(f"Service fetched {len(processed_content)} relevant news articles for {ticker_symbol}.")
    return processed_content

def fetch_reddit_data_service(ticker_symbol: str, company_name: str, posts_limit: int = 10, comments_limit: int = 5) -> list[dict]:
    """Fetches and processes Reddit data for the API."""
    if not reddit_praw_client:
        log.warning("Reddit client not available for fetching data.")
        return []

    # Assuming values from config are needed
    # min_len = settings.MIN_ARTICLE_LENGTH_FOR_ANALYSIS
    # min_mentions = settings.MIN_TICKER_MENTIONS_FOR_RELEVANCE
    # relevant_subreddits = settings.RELEVANT_SUBREDDITS
    # search_timespan = settings.REDDIT_SEARCH_TIMESPAN
    min_len = 100 # Example defaults
    min_mentions = 1
    relevant_subreddits = ['stocks', 'investing', 'wallstreetbets'] # Example defaults
    search_timespan = 'week'

    search_query = f'"{company_name}" OR "{ticker_symbol}" OR "${ticker_symbol}"' # Simple query
    log.info(f"Fetching Reddit data for query: '{search_query}' (Service Layer)")
    processed_content = []
    processed_ids = set()

    for sub_name in relevant_subreddits:
        # Add overall limit check if needed
        try:
            subreddit = reddit_praw_client.subreddit(sub_name)
            for submission in subreddit.search(search_query, sort='new', time_filter=search_timespan, limit=posts_limit):
                if submission.id in processed_ids: continue
                
                post_title = submission.title
                post_body = submission.selftext or ""
                combined_text = f"{post_title}. {post_body}"

                if _is_relevant(combined_text, ticker_symbol, company_name, min_len, min_mentions):
                    processed_ids.add(submission.id)
                    processed_content.append({
                        'id': submission.id,
                        'headline': post_title[:250],
                        'full_text': combined_text,
                        'url': f"https://reddit.com{submission.permalink}",
                        'publishedAt': datetime.fromtimestamp(submission.created_utc, timezone.utc).isoformat(),
                        'source_name': f"r/{submission.subreddit.display_name}",
                        'source_type': 'reddit_post',
                        'author_name': submission.author.name if submission.author else "[deleted]",
                        'item_score': submission.score,
                        'num_comments_on_post': submission.num_comments,
                    })
                    # Comment fetching logic (simplified)
                    # ... (add comment fetching loop similar to prototype's data_fetcher if needed) ...
        except Exception as e:
            log.error(f"Error fetching data from subreddit r/{sub_name}: {e}")
            time.sleep(0.5)

    log.info(f"Service fetched {len(processed_content)} relevant Reddit items for {ticker_symbol}.")
    return processed_content

# --- Placeholder for Indian News ---
def fetch_indian_news_service(*args, **kwargs):
     log.warning("Indian news fetching service not implemented.")
     return []