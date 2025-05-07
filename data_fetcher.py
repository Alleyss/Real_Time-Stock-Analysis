# data_fetcher.py
import yfinance as yf
from newsapi import NewsApiClient
import logging
import time
import re # For relevance checking
from newspaper import Article, ArticleException
import praw
from datetime import datetime, timedelta, timezone
import streamlit as st # For caching

from config import (
    NEWSAPI_KEY, NEWS_ARTICLE_COUNT,
    MIN_ARTICLE_LENGTH_FOR_ANALYSIS, MIN_TICKER_MENTIONS_FOR_RELEVANCE,
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
    REDDIT_POST_LIMIT_PER_SUBREDDIT, RELEVANT_SUBREDDITS, REDDIT_SEARCH_TIMESPAN, REDDIT_COMMENT_LIMIT_PER_POST,NEWS_DOMAIN_BLACKLIST, NEWS_SOURCE_NAME_BLACKLIST
)

# Setup logging (handled by app.py, but good for standalone testing)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Initialize API Clients ---
newsapi_client = None
if NEWSAPI_KEY:
    newsapi_client = NewsApiClient(api_key=NEWSAPI_KEY)
else:
    logging.warning("NewsAPI client not initialized (NEWSAPI_KEY missing).")

reddit_praw_client = None
if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET and REDDIT_USER_AGENT:
    try:
        reddit_praw_client = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            check_for_async=False # Important for Streamlit/sync environments
        )
        if reddit_praw_client.read_only: # Check if authentication was successful for read-only mode
             logging.info("PRAW Reddit client initialized successfully in read-only mode.")
        else:
             logging.warning("PRAW Reddit client initialized, but not in read-only mode. Check credentials if issues arise.")
    except Exception as e:
        logging.error(f"Failed to initialize PRAW Reddit client: {e}")
else:
    logging.warning("Reddit API credentials not fully configured. Reddit fetching disabled.")


# --- Helper Functions ---
def is_article_relevant(text_content, ticker_symbol, company_name):
    """Checks if the article text is relevant based on mentions and length."""
    if not text_content or len(text_content) < MIN_ARTICLE_LENGTH_FOR_ANALYSIS:
        return False

    mentions = 0
    # Case-insensitive search for ticker (especially if it's like 'AAPL' or '$AAPL')
    # For ticker, we might want to ensure it's a whole word or common cashtag format
    ticker_pattern = r'\b{}\b|\${}\b'.format(re.escape(ticker_symbol), re.escape(ticker_symbol))
    mentions += len(re.findall(ticker_pattern, text_content, re.IGNORECASE))

    # Case-insensitive search for company name (as a whole phrase)
    if company_name and len(company_name) > 2: # Avoid matching very short generic company names
        company_pattern = r'\b{}\b'.format(re.escape(company_name))
        mentions += len(re.findall(company_pattern, text_content, re.IGNORECASE))
    
    return mentions >= MIN_TICKER_MENTIONS_FOR_RELEVANCE

@st.cache_data(ttl="15m", show_spinner=False)
def get_stock_info(ticker):
    logging.info(f"Executing get_stock_info for {ticker} (Cacheable).")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info or not info.get('symbol'):
            logging.warning(f"Initial yfinance info for {ticker} is empty/invalid. Trying history.")
            hist = stock.history(period="2d") # Get 2 days to ensure we have a close
            if hist.empty:
                logging.error(f"Cannot retrieve info or history for {ticker}. Likely invalid or delisted.")
                return None
            current_price = hist['Close'].iloc[-1] if not hist.empty else 'N/A'
            company_name = ticker
            info_dict = {'symbol': ticker, 'longName': company_name, 'currency': info.get('currency', 'N/A')} # Minimal info
        else:
            current_price = info.get('currentPrice', info.get('regularMarketPrice', info.get('previousClose')))
            company_name = info.get('longName', info.get('shortName', ticker))
            info_dict = info
        
        if current_price is None: current_price = "N/A" # Ensure price is not None

        logging.info(f"Successfully processed yfinance data for {ticker}")
        return {"info": info_dict, "current_price": current_price, "company_name": company_name}
    except Exception as e:
        logging.error(f"Error fetching yfinance data for {ticker}: {e}", exc_info=True)
        return None

def fetch_full_article_text_newspaper(url):
    if not url: return None
    try:
        logging.debug(f"Newspaper3k: Attempting to fetch full text for: {url}")
        article = Article(url, language='en', fetch_images=False, memoize_articles=True) # memoize_articles can speed up repeated calls to same URL
        article.download()
        # time.sleep(0.5) # Small delay, Newspaper might have internal ones
        article.parse()
        logging.debug(f"Newspaper3k: Successfully parsed: {url}")
        return article.text
    except ArticleException as e:
        logging.warning(f"Newspaper3k failed for URL {url}: {e}")
        return None
    except Exception as e: # Catch any other unexpected errors
        logging.error(f"Newspaper3k: Unexpected error fetching article {url}: {e}", exc_info=False)
        return None

# --- Main Data Fetching Functions ---
def get_us_news(ticker_symbol, company_name, articles_count=NEWS_ARTICLE_COUNT):
    """Fetches news from NewsAPI and enriches with full text."""
    if not newsapi_client:
        logging.error("Cannot fetch US news: NewsAPI client not available.")
        return []

    # Use company name for broader search, add ticker for specificity
    query = f'"{company_name}" OR "{ticker_symbol}"'
    logging.info(f"Fetching {articles_count} US news for query: '{query}'")
    
    try:
        api_response = newsapi_client.get_everything(
            q=query, language='en', sort_by='publishedAt',
            page_size=min(articles_count, 100), page=1
        )
        articles_metadata = api_response.get('articles', [])
    except Exception as e:
        logging.error(f"NewsAPI error for query '{query}': {e}", exc_info=True)
        return []

    enriched_articles = []
    processed_urls = set()
    for meta in articles_metadata:
        title = meta.get('title')
        url = meta.get('url')
        published_at_str = meta.get('publishedAt')
        source_info = meta.get('source', {})
        source_name = source_info.get('name', 'Unknown News Source')

        if not title or title == '[Removed]' or not url or not published_at_str:
            continue
        processed_urls.add(url)
        # <<< START RELEVANCE FILTERING (BLACKLISTING) >>>
        # 1. Domain blacklisting (extract domain from URL)
        try:
            domain = url.split('/')[2].replace('www.', '')
            if domain in NEWS_DOMAIN_BLACKLIST:
                logging.debug(f"Skipping blacklisted domain: {domain} for article: {url}")
                continue
        except IndexError:
            logging.warning(f"Could not parse domain from URL: {url}")
            # Decide whether to continue or skip if domain parsing fails

        # 2. Source Name blacklisting
        if source_name in NEWS_SOURCE_NAME_BLACKLIST:
            logging.debug(f"Skipping blacklisted source name: {source_name} for article: {url}")
            continue
        # <<< END RELEVANCE FILTERING (BLACKLISTING) >>>
        # Fetch full text (this can be slow)
        full_text_content = fetch_full_article_text_newspaper(url)

        if not full_text_content or len(full_text_content) < MIN_ARTICLE_LENGTH_FOR_ANALYSIS:
            # If full text is too short or unavailable, use description if available, else just title
            full_text_content = meta.get('description', title) 
            if not full_text_content: full_text_content = title


        if is_article_relevant(full_text_content, ticker_symbol, company_name):
            enriched_articles.append({
                'headline': title,
                'full_text': full_text_content,
                'url': url,
                'publishedAt': published_at_str, # Keep as string, parsing done in sentiment analyzer or DB
                'source_name': meta.get('source', {}).get('name', 'Unknown News Source'),
                'source_type': 'news'
            })
            if len(enriched_articles) >= articles_count : # Stop if we have enough relevant articles
                break
    
    logging.info(f"Fetched and processed {len(enriched_articles)} relevant news articles.")
    return enriched_articles


def fetch_reddit_data(ticker_symbol, company_name, **kwargs): # Added **kwargs for perform_analysis compatibility
    if not reddit_praw_client:
        logging.warning("Reddit client not available for fetching data.")
        return []

    search_terms = [company_name, ticker_symbol]
    if company_name.lower() != ticker_symbol.lower(): # Avoid duplicate if they are same
        search_query = f'"{company_name}" OR "{ticker_symbol}" OR "{ticker_symbol.replace("$","")}"' # search for $TICKER and TICKER
    else:
        search_query = f'"{company_name}" OR "{ticker_symbol.replace("$","")}"'

    logging.info(f"Fetching Reddit data for query: '{search_query}' across subreddits.")
    reddit_content = []
    processed_ids = set() # To avoid processing same post/comment multiple times if found via different paths

    for sub_name in RELEVANT_SUBREDDITS:
        if len(reddit_content) >= REDDIT_POST_LIMIT_PER_SUBREDDIT * len(RELEVANT_SUBREDDITS) / 2 : # Soft overall limit
            break
        try:
            subreddit = reddit_praw_client.subreddit(sub_name)
            logging.debug(f"Searching r/{sub_name} for '{search_query}' (limit {REDDIT_POST_LIMIT_PER_SUBREDDIT})")
            
            for submission in subreddit.search(search_query, sort='new', time_filter=REDDIT_SEARCH_TIMESPAN, limit=REDDIT_POST_LIMIT_PER_SUBREDDIT):
                if submission.id in processed_ids: continue
                processed_ids.add(submission.id)

                post_title = submission.title
                post_body = submission.selftext if submission.selftext else ""
                combined_text = f"{post_title}. {post_body}"

                if is_article_relevant(combined_text, ticker_symbol, company_name):
                    reddit_content.append({
                        'headline': post_title[:250],
                        'full_text': combined_text,
                        'url': f"https://reddit.com{submission.permalink}",
                        'publishedAt': datetime.fromtimestamp(submission.created_utc, timezone.utc).isoformat(),
                        'source_name': f"r/{sub_name}",
                        'source_type': 'reddit_post',
                        'id': submission.id # For DB if needed
                    })

                    # Fetch comments for this relevant post
                    comment_fetch_count = 0
                    try:
                        submission.comments.replace_more(limit=0) # Expand top comments
                        for comment in submission.comments.list():
                            if comment.id in processed_ids: continue
                            if comment_fetch_count >= REDDIT_COMMENT_LIMIT_PER_POST: break
                            if isinstance(comment, praw.models.MoreComments): continue
                            
                            processed_ids.add(comment.id)
                            if is_article_relevant(comment.body, ticker_symbol, company_name):
                                reddit_content.append({
                                    'headline': f"Comment on: {post_title[:100]}...",
                                    'full_text': comment.body,
                                    'url': f"https://reddit.com{comment.permalink}",
                                    'publishedAt': datetime.fromtimestamp(comment.created_utc, timezone.utc).isoformat(),
                                    'source_name': f"r/{sub_name} comment",
                                    'source_type': 'reddit_comment',
                                    'id': comment.id
                                })
                                comment_fetch_count += 1
                    except Exception as ce:
                        logging.warning(f"Could not process comments for post {submission.id} in r/{sub_name}: {ce}")
                if len(reddit_content) >= REDDIT_POST_LIMIT_PER_SUBREDDIT * 3: # Harder overall limit
                    break
        except Exception as e:
            logging.error(f"Error fetching data from subreddit r/{sub_name}: {e}")
            time.sleep(0.5) # Brief pause

    logging.info(f"Fetched {len(reddit_content)} items from Reddit.")
    return reddit_content



def scrape_indian_news(ticker_symbol, company_name, **kwargs): # Added for consistency
    logging.warning(f"Indian news scraping for {ticker_symbol} is not implemented.")
    return []