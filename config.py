# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API Keys ---
# Load NewsAPI key from environment variable
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')

# Check if the API key is loaded, raise error if not (optional but good practice)
if not NEWSAPI_KEY:
    print("Warning: NEWSAPI_KEY not found in environment variables. Please set it in your .env file.")
    # Consider raising an error if the key is absolutely essential for startup
    # raise ValueError("NEWSAPI_KEY not found. Please set it in your .env file.")

# --- Database Configuration ---
DB_NAME = "stocks_analysis.db"

# --- Model Configuration (Placeholder for later) ---
# Example: Using a general-purpose model initially
DEFAULT_SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
# Example alternative: FinBERT (if installed and preferred later)
# DEFAULT_SENTIMENT_MODEL = "ProsusAI/finbert"

# --- Other Constants ---
# Add any other project-wide constants here if needed