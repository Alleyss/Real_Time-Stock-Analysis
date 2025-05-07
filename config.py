# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API Keys ---
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')

if not NEWSAPI_KEY:
    print("Warning: NEWSAPI_KEY not found in environment variables. Please set it in your .env file.")

# --- Database Configuration ---
DB_NAME = "stocks_analysis.db"

# --- Model Configuration ---
# Using DistilBERT fine-tuned on SST-2 (a common sentiment task) as a starting point.
# It's smaller and faster than BERT/RoBERTa, good for MVP. Outputs 'POSITIVE'/'NEGATIVE'.
DEFAULT_SENTIMENT_MODEL = "ProsusAI/finbert"
# Alternative options for later:
# DEFAULT_SENTIMENT_MODEL = "ProsusAI/finbert" # Financial specific, outputs Positive/Negative/Neutral
# DEFAULT_SENTIMENT_MODEL = "roberta-base" # Powerful, needs fine-tuning or use a fine-tuned version

# --- Other Constants ---
# Number of news articles to fetch/analyze
NEWS_ARTICLE_COUNT = 20 # Adjust as needed (consider NewsAPI limits)
MIN_ARTICLE_LENGTH_FOR_ANALYSIS = 200 # Min characters for full_text to be considered substantial
MIN_TICKER_MENTIONS_FOR_RELEVANCE = 2 # Min times ticker/company name should appear in full_text
RECENCY_DECAY_HALF_LIFE_HOURS = 24.0
# Intensity boost: score_weight = 1 + abs(sentiment_score) * INTENSITY_BOOST_FACTOR
INTENSITY_BOOST_FACTOR = 0.2