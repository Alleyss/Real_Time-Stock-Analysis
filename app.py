# main.py (Streamlit Application)
import streamlit as st
import logging

# Import functions from other modules
from config import DEFAULT_SENTIMENT_MODEL
from database import create_tables # Import the setup function
from data_fetcher import get_stock_info, get_us_news, scrape_indian_news
from sentiment_analyzer import (
    load_sentiment_model,
    analyze_sentiment_for_ticker,
    get_suggestion,
    get_validation_points
)

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Database Initialization ---
# Run this once when the script starts to ensure tables exist
try:
    logging.info("Initializing database schema...")
    create_tables()
    logging.info("Database schema initialization complete.")
except Exception as e:
    st.error(f"Failed to initialize database: {e}")
    logging.error(f"Database initialization failed: {e}")
    st.stop() # Stop the app if DB setup fails

# --- Model Loading (Cached) ---
# Use Streamlit's caching to load the model only once
@st.cache_resource
def load_model(model_name=DEFAULT_SENTIMENT_MODEL):
    """Loads and caches the sentiment analysis pipeline."""
    logging.info(f"Attempting to load sentiment model: {model_name}")
    # In Phase 0, this uses the dummy loader from sentiment_analyzer
    # In Phase 1+, it will load the actual Hugging Face model
    return load_sentiment_model(model_name)

sentiment_pipeline = load_model()

if sentiment_pipeline is None and DEFAULT_SENTIMENT_MODEL != "distilbert-base-uncased-finetuned-sst-2-english": # Check if actual model loading failed
     st.error(f"Failed to load sentiment model: {DEFAULT_SENTIMENT_MODEL}. Sentiment analysis disabled.")
     # Optionally disable the analysis button or parts of the UI

# --- Streamlit App Layout ---
st.set_page_config(layout="wide") # Use wider layout
st.title("📊 Real-Time Stock Analysis using Sentiment")
st.caption("Enter a US or Indian stock ticker to get started.")

# --- Input Section ---
ticker_input = st.text_input("Enter Stock Ticker (e.g., AAPL, RELIANCE.NS):", "AAPL").upper()
analyze_button = st.button("Analyze Sentiment")

# --- Analysis Execution ---
if analyze_button and ticker_input:
    if not sentiment_pipeline:
         st.warning("Sentiment model not loaded. Cannot perform analysis.")
    else:
        with st.spinner(f"Analyzing {ticker_input}... Fetching data and running sentiment analysis..."):
            try:
                # 1. Fetch Stock Info
                logging.info(f"Fetching stock info for {ticker_input}")
                stock_data = get_stock_info(ticker_input)

                # 2. Fetch News (Determine US vs Indian based on ticker maybe?)
                # Basic check: .NS or .BO suffix implies Indian stock for yfinance/scraping
                if ".NS" in ticker_input or ".BO" in ticker_input:
                    logging.info(f"Fetching Indian news for {ticker_input}")
                    news_articles = scrape_indian_news(ticker_input) # Placeholder for now
                    if not news_articles: # Fallback or alternative needed?
                        st.warning(f"Indian news scraping not fully implemented or returned no results for {ticker_input}.")
                        # Optionally try NewsAPI as a fallback? Depends on coverage.
                        # news_articles = get_us_news(ticker_input)
                else:
                    # Assume US stock for NewsAPI
                    logging.info(f"Fetching US news for {ticker_input}")
                    # Use company name if available for potentially better NewsAPI results
                    company_name = stock_data.get('info', {}).get('longName', ticker_input)
                    news_articles = get_us_news(company_name) # Pass name or ticker

                # Basic check if news was found
                if not news_articles:
                    st.warning(f"No recent news articles found for {ticker_input}. Sentiment analysis might be unreliable.")

                # 3. Analyze Sentiment
                logging.info(f"Running sentiment analysis for {ticker_input}")
                # Pass the loaded pipeline
                aggregated_score, analyzed_details = analyze_sentiment_for_ticker(ticker_input, news_articles, sentiment_pipeline)

                # 4. Get Suggestion
                logging.info(f"Generating suggestion based on score: {aggregated_score:.4f}")
                suggestion = get_suggestion(aggregated_score)

                # 5. Get Validation Points
                logging.info("Extracting validation points.")
                validation_points = get_validation_points(analyzed_details) # Pass detailed results

                # --- Display Results ---
                st.subheader(f"Analysis Results for {ticker_input}")
                col1, col2 = st.columns([1, 2]) # Ratio for columns

                with col1:
                    st.metric(label="Current Price", value=f"${stock_data.get('current_price', 'N/A'):.2f}" if isinstance(stock_data.get('current_price'), (int,float)) else "N/A")
                    st.write(f"**Company:** {stock_data.get('info', {}).get('longName', 'N/A')}")
                    # Add more stock info from stock_data['info'] if needed

                    st.markdown("---")
                    st.subheader("AI Suggestion:")
                    # Use different colors based on suggestion
                    if suggestion in ["Strong Buy", "Buy"]:
                        st.success(f"**{suggestion}** (Score: {aggregated_score:.3f})")
                    elif suggestion == "Hold":
                        st.info(f"**{suggestion}** (Score: {aggregated_score:.3f})")
                    else: # Sell, Strong Sell
                        st.error(f"**{suggestion}** (Score: {aggregated_score:.3f})")

                    st.markdown("**Justification based on news:**")
                    for point in validation_points:
                        st.markdown(point) # Display bullet points

                with col2:
                    st.subheader("Recent News Headlines Analyzed:")
                    if news_articles:
                        # Display headlines (and maybe sentiment label/score per headline later)
                        for article in news_articles:
                             st.markdown(f"- [{article.get('title', 'No Title')}]({article.get('url', '#')}) ({article.get('source',{}).get('name', 'Unknown Source')})")
                    else:
                        st.write("No headlines were processed.")

                # Optionally display detailed sentiment per article (for debugging/interest)
                # with st.expander("Show Detailed Sentiment Scores per Headline"):
                #     st.dataframe(analyzed_details)

            except Exception as e:
                st.error(f"An error occurred during analysis for {ticker_input}:")
                st.exception(e) # Show detailed error in Streamlit app
                logging.error(f"Analysis failed for {ticker_input}: {e}", exc_info=True)

else:
    st.info("Enter a stock ticker and click 'Analyze Sentiment'.")

# Add footer or other static elements if desired
st.markdown("---")
st.caption("Disclaimer: This is an AI-driven sentiment analysis based on public news data. It is NOT financial advice. Always do your own research.")