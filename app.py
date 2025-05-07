# app.py (Streamlit Application)
import streamlit as st
import logging
# Ensure all necessary imports from config are present if used directly in this file
from config import DEFAULT_SENTIMENT_MODEL, RECENCY_DECAY_HALF_LIFE_HOURS, INTENSITY_BOOST_FACTOR
from database import create_tables, save_stock_info, save_content_items, update_sentiment_for_items
from data_fetcher import get_stock_info, get_us_news, fetch_reddit_data,  scrape_indian_news # scrape_indian_news is placeholder
from sentiment_analyzer import (
    get_sentiment_pipeline,
    analyze_sentiment_for_ticker,
    calculate_weighted_sentiment,
    get_suggestion,
    get_validation_points
)

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)

# --- Database Initialization ---
try:
    logging.info("Initializing database schema...")
    create_tables()
    logging.info("Database schema initialization complete.")
except Exception as e:
    st.error(f"Fatal Error: Failed to initialize database: {e}")
    logging.error(f"Database initialization failed: {e}", exc_info=True)
    st.stop()

# --- Model Loading (Cached) ---
@st.cache_resource
def load_model(model_name=DEFAULT_SENTIMENT_MODEL):
    logging.info(f"Attempting to load/cache sentiment model: {model_name}")
    pipeline_instance = get_sentiment_pipeline(model_name)
    if pipeline_instance is None:
         logging.error(f"Failed to load sentiment model {model_name} in load_model function.")
    return pipeline_instance

sentiment_pipeline = load_model()

if sentiment_pipeline is None:
     st.error(f"Fatal Error: Failed to load sentiment model '{DEFAULT_SENTIMENT_MODEL}'. Check logs. Analysis disabled.")
     logging.critical(f"Sentiment model '{DEFAULT_SENTIMENT_MODEL}' failed to load.")
     st.stop()

# --- UI Helper ---
def display_analysis_output(stock_data, company_name_disp, ticker_disp,
                            final_weighted_score, analyzed_details_disp, suggestion_disp,
                            validation_points_disp, source_desc):
    st.subheader(f"Results for {company_name_disp} ({ticker_disp}) from {source_desc}")
    
    try:
        score_val = float(final_weighted_score)
    except (ValueError, TypeError):
        score_val = 0.0
        st.warning("Could not determine a valid final sentiment score.")

    col1, col2 = st.columns([1, 2])
    with col1:
        if stock_data:
            price = stock_data.get('current_price', 'N/A')
            price_str = f"${price:.2f}" if isinstance(price, (int, float)) else "N/A"
            st.metric(label="Last Price", value=price_str)
            st.markdown(f"**Sector:** {stock_data.get('info', {}).get('sector', 'N/A')}")
            st.markdown(f"**Industry:** {stock_data.get('info', {}).get('industry', 'N/A')}")

        st.markdown("---")
        st.subheader("AI Suggestion:")
        st.caption(f"(Based on {source_desc.lower()} content analysis)")
        score_display = f"(Score: {score_val:.3f})"
        
        if suggestion_disp == "Strong Buy": st.success(f"**{suggestion_disp}** {score_display}")
        elif suggestion_disp == "Buy": st.success(f"**{suggestion_disp}** {score_display}")
        elif suggestion_disp == "Hold": st.info(f"**{suggestion_disp}** {score_display}")
        elif suggestion_disp == "Sell": st.error(f"**{suggestion_disp}** {score_display}")
        elif suggestion_disp == "Strong Sell": st.error(f"**{suggestion_disp}** {score_display}")
        else: st.write(f"{suggestion_disp} {score_display}")

        st.markdown("**Justification based on content:**")
        if validation_points_disp:
            for point in validation_points_disp:
                st.markdown(point, unsafe_allow_html=True)
        else:
            st.write("Sentiment appears balanced or lacks strong drivers for justification.")

    with col2:
        st.subheader(f"Top {source_desc} Content Analyzed:")
        if analyzed_details_disp:
            display_items = []
            # Sort details by recency before displaying if publishedAt is reliable
            # For now, just take the first 15 as returned by sentiment_analyzer
            for item in analyzed_details_disp[:15]:
                emoji = "🟢" if item['label'] == 'positive' else "🔴" if item['label'] == 'negative' else "⚪️"
                display_items.append(f"{emoji} [{item.get('headline','No Headline')}]({item.get('url','#')}) - *{item.get('source_name','Unknown')}* (Score: {item.get('score',0):.2f})")
            if display_items:
                st.markdown("\n".join(f"- {line}" for line in display_items), unsafe_allow_html=True)
            else:
                st.write("No content details to display.")
        else:
            st.write(f"No {source_desc.lower()} content was found or processed successfully.")

# --- App Layout ---
st.set_page_config(layout="wide")
st.title("📊 Multi-Source Stock Sentiment Analyzer (MVP)")
st.caption("Enter a US stock ticker and choose a data source for sentiment analysis.")

ticker_input = st.text_input("Enter US Stock Ticker:", "AAPL").upper() # Default to AAPL for example
st.markdown("---")

# Session state for results
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None

# --- Generic Analysis Function (Corrected) ---
def perform_analysis(fetch_function_to_call, current_ticker_sym, current_company_name, source_description_name, **additional_fetch_kwargs):
    """
    Performs fetching, analysis, and DB operations for a given data source.
    Args:
        fetch_function_to_call: The data fetching function (e.g., get_us_news).
        current_ticker_sym: The stock ticker symbol.
        current_company_name: The company name.
        source_description_name: String describing the source (e.g., "News", "Reddit").
        **additional_fetch_kwargs: Additional keyword arguments for the fetch_function_to_call.
    """
    st.session_state.analysis_data = None # Clear previous results for a new analysis run
    
    fetched_content = []
    with st.spinner(f"Fetching {source_description_name} data for {current_ticker_sym}..."):
        # CORRECTED CALL to fetch_function_to_call:
        # Pass ticker_symbol and company_name as keyword arguments.
        fetched_content = fetch_function_to_call(
            ticker_symbol=current_ticker_sym,
            company_name=current_company_name,
            **additional_fetch_kwargs # Pass along any other specific args (like articles_count for news)
        )

    if not fetched_content:
        st.warning(f"No relevant {source_description_name} content found for {current_ticker_sym} / {current_company_name}.")
        return None # Indicate failure

    saved_db_count = save_content_items(current_ticker_sym, fetched_content)
    # Logging of saved_db_count is now handled within save_content_items or its sub-functions

    analyzed_item_details = []
    with st.spinner(f"Analyzing {source_description_name} sentiment for {current_ticker_sym}..."):
        analyzed_item_details = analyze_sentiment_for_ticker(fetched_content, sentiment_pipeline)

    if not analyzed_item_details:
        st.warning(f"Sentiment analysis failed to produce results for {source_description_name} content.")
        return None

    updated_db_sentiment_count = update_sentiment_for_items(analyzed_item_details)
    # Logging of updated_db_sentiment_count is now handled within update_sentiment_for_items

    final_weighted_score_for_source = calculate_weighted_sentiment(
        analyzed_item_details,
        RECENCY_DECAY_HALF_LIFE_HOURS,
        INTENSITY_BOOST_FACTOR
    )

    current_suggestion = get_suggestion(final_weighted_score_for_source)
    current_validation_points = get_validation_points(analyzed_item_details)

    logging.info(f"[{source_description_name.upper()}_LOG] Ticker: {current_ticker_sym}, Final Score: {final_weighted_score_for_source:.4f}, Items: {len(analyzed_item_details)}")

    # Store results in session state for display
    # Note: 'ticker' and 'company_name' in this dict are the ones used for THIS analysis run.
    analysis_result_dict = {
        'final_score': final_weighted_score_for_source,
        'analyzed_details': analyzed_item_details,
        'suggestion': current_suggestion,
        'validation_points': current_validation_points,
        'source_description': source_description_name,
        'ticker': current_ticker_sym,
        'company_name': current_company_name
    }
    st.session_state.analysis_data = analysis_result_dict
    return analysis_result_dict # Also return for direct use if needed

# --- Buttons for different sources ---
col_buttons1, col_buttons2 = st.columns(2)
analysis_was_triggered_this_run = False # To help with initial message display

# Global variables to store fetched stock info for the current ticker
# These are fetched once if any analysis button is pressed.
g_stock_data = None
g_company_name = ticker_input # Default to ticker_input if stock info fetch fails

if ticker_input: # Only attempt to get stock info if a ticker is provided
    # This get_stock_info is cached by Streamlit if called with the same ticker
    g_stock_data = get_stock_info(ticker_input)
    if g_stock_data:
        g_company_name = g_stock_data.get("company_name", ticker_input)
        # Save/update stock info in DB (idempotent operation)
        save_stock_info(ticker_input, g_company_name)
    else:
        # Display error only once if it persists, not on every Streamlit rerun without button press
        if 'stock_info_error_shown' not in st.session_state or st.session_state.stock_info_error_ticker != ticker_input:
            st.error(f"Could not retrieve fundamental stock information for {ticker_input}. Please check the ticker. Analysis buttons disabled.")
            st.session_state.stock_info_error_shown = True
            st.session_state.stock_info_error_ticker = ticker_input
        # Keep g_stock_data as None, buttons will be disabled.
elif 'stock_info_error_shown' in st.session_state: # Clear error if ticker input is cleared
    del st.session_state.stock_info_error_shown
    if 'stock_info_error_ticker' in st.session_state:
        del st.session_state.stock_info_error_ticker


# --- Button Logic ---
# The `disabled` state of buttons now depends on `g_stock_data` being successfully fetched.
with col_buttons1:
    if st.button("Analyze News Sentiment 📰", key="news_btn", use_container_width=True, disabled=not g_stock_data):
        if ticker_input and g_stock_data: # Double check, though disabled should prevent
            perform_analysis(get_us_news, ticker_input, g_company_name, "News") # articles_count will use default from get_us_news
            analysis_was_triggered_this_run = True
        elif not ticker_input: st.warning("Please enter a stock ticker.")
        # else: g_stock_data was None, button was disabled, this branch shouldn't be hit.
with col_buttons2:
    if st.button("Analyze Reddit Sentiment 👽", key="reddit_btn", use_container_width=True, disabled=not g_stock_data):
        if ticker_input and g_stock_data:
            perform_analysis(fetch_reddit_data, ticker_input, g_company_name, "Reddit")
            analysis_was_triggered_this_run = True
        elif not ticker_input: st.warning("Please enter a stock ticker.")

st.markdown("---")

# --- Display results from session state ---
if st.session_state.analysis_data:
    res = st.session_state.analysis_data
    # Use g_stock_data if available (it should be if analysis ran successfully for the current ticker)
    # The 'ticker' and 'company_name' in 'res' are from the analysis run.
    # g_stock_data is for the *current* ticker_input.
    stock_data_for_display = g_stock_data if g_stock_data and res['ticker'] == ticker_input else get_stock_info(res['ticker'])

    display_analysis_output(
        stock_data_for_display, res['company_name'], res['ticker'],
        res['final_score'], res['analyzed_details'],
        res['suggestion'], res['validation_points'], res['source_description']
    )
elif not analysis_was_triggered_this_run and not any(st.session_state.get(f"{key}_btn_was_clicked", False) for key in ["news", "reddit"]):
    # A more robust check if any analysis button was *ever* clicked could involve storing a flag in session_state on button press
    st.info("Enter a stock ticker and select a data source (News, Reddit) to analyze sentiment.")
    # To make the above condition more robust:
    # At the end of each button's if block, set st.session_state[f"{source}_btn_was_clicked"] = True

# --- Footer ---
st.markdown("---")
st.caption("Disclaimer: This tool provides AI-generated sentiment analysis based on public data for informational purposes only. It is NOT financial advice. Verify information and conduct your own research before making any investment decisions.")