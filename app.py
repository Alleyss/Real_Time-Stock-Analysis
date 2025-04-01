# main.py (Streamlit Application)
import streamlit as st
import logging
import pandas as pd # For potential dataframe display
from datetime import datetime, timedelta

# Import functions from other modules
from config import DEFAULT_SENTIMENT_MODEL
from database import create_tables, save_stock_info, save_news_articles
from data_fetcher import get_stock_info, get_us_news, scrape_indian_news
from sentiment_analyzer import (
    get_sentiment_pipeline, # Import the loader helper
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
    st.error(f"Fatal Error: Failed to initialize database: {e}")
    logging.error(f"Database initialization failed: {e}", exc_info=True)
    st.stop() # Stop the app if DB setup fails

# --- Model Loading (Cached) ---
# Use Streamlit's caching to load the model only once
@st.cache_resource # Caches the actual pipeline object
def load_model(model_name=DEFAULT_SENTIMENT_MODEL):
    """Loads and caches the sentiment analysis pipeline."""
    logging.info(f"Attempting to load/cache sentiment model: {model_name}")
    pipeline_instance = get_sentiment_pipeline(model_name)
    if pipeline_instance is None:
         logging.error(f"Failed to load sentiment model {model_name} in load_model function.")
    return pipeline_instance

sentiment_pipeline = load_model()

# Check if model loading failed after attempting to cache
if sentiment_pipeline is None:
     st.error(f"Fatal Error: Failed to load sentiment model '{DEFAULT_SENTIMENT_MODEL}'. Cannot perform analysis.")
     logging.critical(f"Sentiment model '{DEFAULT_SENTIMENT_MODEL}' failed to load. Application might not function correctly.")
     st.stop() # Stop if model is essential and failed loading

# --- Streamlit App Layout ---
st.set_page_config(layout="wide")
st.title("📊 Real-Time Stock Analysis using Sentiment (MVP)")
st.caption("Enter a US stock ticker (e.g., AAPL, MSFT, GOOG) to get sentiment analysis based on recent news.")

# --- Input Section ---
ticker_input = st.text_input("Enter US Stock Ticker:", "AAPL").upper()
analyze_button = st.button("Analyze Sentiment ✨")

# --- Analysis Execution ---
if analyze_button and ticker_input:
    with st.spinner(f"Analyzing {ticker_input}... Fetching data and running analysis..."):
        analysis_successful = False
        try:
            # 1. Fetch Stock Info (Error handled in function)
            logging.info(f"[Workflow] Fetching stock info for {ticker_input}")
            stock_data = get_stock_info(ticker_input)
            if not stock_data:
                st.error(f"Could not retrieve valid stock information for {ticker_input}. Please check the ticker.")
                st.stop() # Stop processing if basic info fails

            company_name = stock_data.get("company_name", ticker_input)

            # (Optional but good practice) Save/Update stock info in DB
            save_stock_info(ticker_input, company_name)

            # 2. Fetch News (US Only for Phase 1)
            logging.info(f"[Workflow] Fetching US news for {company_name} (query based on ticker/name)")
            # Use company name for better query results if available
            news_articles = get_us_news(company_name)

            if not news_articles:
                st.warning(f"No recent news articles found for {company_name} ({ticker_input}) via NewsAPI. Sentiment analysis may be based on limited data or unavailable.")
                # Decide if you want to stop or proceed with score 0
                # For MVP, let's proceed but it will likely result in 'Hold'
                aggregated_score = 0.0
                analyzed_details = []
            else:
                # 3. (Optional) Save Fetched News Articles to DB
                logging.info(f"[Workflow] Saving {len(news_articles)} fetched articles to database.")
                save_news_articles(ticker_input, news_articles)

                # 4. Analyze Sentiment
                logging.info(f"[Workflow] Running sentiment analysis...")
                aggregated_score, analyzed_details = analyze_sentiment_for_ticker(news_articles, sentiment_pipeline)

            # 5. Get Suggestion
            logging.info(f"[Workflow] Generating suggestion...")
            suggestion = get_suggestion(aggregated_score)

            # 6. Get Validation Points
            logging.info(f"[Workflow] Extracting validation points...")
            validation_points = get_validation_points(analyzed_details) # Pass detailed results

            analysis_successful = True # Mark as successful if we got this far

        except Exception as e:
            st.error(f"An unexpected error occurred during the analysis process for {ticker_input}:")
            st.exception(e) # Show detailed error in Streamlit app for debugging
            logging.error(f"Analysis workflow failed for {ticker_input}: {e}", exc_info=True)

    # --- Display Results (Only if analysis was attempted) ---
    if 'stock_data' in locals() and stock_data: # Check if stock_data was fetched
        st.subheader(f"Analysis Results for {company_name} ({ticker_input})")
        col1, col2 = st.columns([1, 2]) # Adjust ratio as needed

        with col1:
            # Display Stock Price and Info
            current_price = stock_data.get('current_price', 'N/A')
            price_display = f"${current_price:.2f}" if isinstance(current_price, (int, float)) else "N/A"
            st.metric(label="Last Price", value=price_display)

            # Add other key info if available
            info = stock_data.get('info', {})
            st.markdown(f"**Sector:** {info.get('sector', 'N/A')}")
            st.markdown(f"**Industry:** {info.get('industry', 'N/A')}")
            market_cap = info.get('marketCap')
            if market_cap:
                 st.markdown(f"**Market Cap:** ${market_cap:,}") # Format with commas

            # Display Suggestion and Validation (if analysis ran)
            if analysis_successful:
                 st.markdown("---")
                 st.subheader("AI Suggestion:")
                 score_display = f"(Score: {aggregated_score:.3f})"
                 if suggestion == "Strong Buy": st.success(f"**{suggestion}** {score_display}")
                 elif suggestion == "Buy": st.success(f"**{suggestion}** {score_display}")
                 elif suggestion == "Hold": st.info(f"**{suggestion}** {score_display}")
                 elif suggestion == "Sell": st.error(f"**{suggestion}** {score_display}")
                 elif suggestion == "Strong Sell": st.error(f"**{suggestion}** {score_display}")

                 st.markdown("**Justification based on news:**")
                 if validation_points:
                     for point in validation_points:
                         st.markdown(point, unsafe_allow_html=True) # Allow markdown links
                 else:
                      st.write("Could not extract specific validation points.")
            elif not analysis_successful and 'aggregated_score' not in locals():
                 # Handle case where analysis block failed before setting score
                 st.warning("Analysis could not be completed due to an error.")

        with col2:
            st.subheader("Recent News Headlines Analyzed:")
            if analysis_successful and analyzed_details:
                 # Create a small dataframe for better display? Or just list.
                 news_display = []
                 for item in analyzed_details:
                     # Simple display for MVP
                     label_emoji = "🟢" if item['label'] == 'positive' else "🔴" if item['label'] == 'negative' else "⚪️"
                     news_display.append(f"{label_emoji} [{item['headline']}]({item['url']})")

                 if news_display:
                     st.markdown("\n".join(f"- {line}" for line in news_display), unsafe_allow_html=True)
                 else:
                      st.write("No headlines were successfully analyzed.")

            elif 'news_articles' in locals() and news_articles:
                 # Display fetched headlines even if analysis part failed
                 st.write("(Displaying fetched headlines as analysis may have failed)")
                 for article in news_articles:
                      st.markdown(f"- [{article.get('title', 'No Title')}]({article.get('url', '#')}) ({article.get('source',{}).get('name', 'Unknown Source')})")
            else:
                 st.write("No news headlines were found or processed.")

elif not ticker_input and analyze_button:
    st.warning("Please enter a stock ticker.")
else:
    # Initial state message
    st.info("Enter a US stock ticker and click 'Analyze Sentiment ✨'.")

# --- Footer ---
st.markdown("---")
st.caption("Disclaimer: This tool provides AI-generated sentiment analysis based on public news data for informational purposes only. It is NOT financial advice. Verify information and conduct your own research before making any investment decisions.")