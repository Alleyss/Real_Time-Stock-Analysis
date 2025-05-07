# app/api/routers/stocks.py
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List
import logging

# Import services and schemas
from app.services import data_fetcher_service, sentiment_service
from app.schemas import stock as stock_schemas
from app.core.config import settings
# Import the Enum if created separately
from app.schemas.common import SentimentDataSource # Assuming you created common.py

log = logging.getLogger(__name__)

router = APIRouter()

# --- /info endpoint remains the same ---
@router.get("/{ticker_symbol}/info", response_model=stock_schemas.StockInfo)
async def get_stock_information(ticker_symbol: str):
    """
    Retrieve basic stock information for a given ticker symbol using yfinance.
    """
    log.info(f"Received request for stock info: {ticker_symbol}")
    stock_data = data_fetcher_service.fetch_stock_info(ticker_symbol.upper())
    if not stock_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not retrieve stock information for ticker '{ticker_symbol}'. Please check the symbol."
        )
    return stock_data

# --- Modified /sentiment endpoint ---
@router.get("/{ticker_symbol}/sentiment", response_model=stock_schemas.SentimentAnalysisResult)
async def get_stock_sentiment(
    ticker_symbol: str,
    # Use Query parameter with Enum for validation
    source: SentimentDataSource = Query(
        ..., # Ellipsis makes it a required parameter
        description="Specify the data source to analyze ('news' or 'reddit')."
    )
):
    """
    Fetch content for a specific source (News or Reddit), analyze sentiment,
    and return results for the given ticker.
    """
    ticker_upper = ticker_symbol.upper()
    log.info(f"Received request for '{source.value}' sentiment analysis: {ticker_upper}") # Use source.value

    # 1. Get Company Name (use stock info or fallback)
    stock_info = data_fetcher_service.fetch_stock_info(ticker_upper)
    if not stock_info or not stock_info.get("company_name"):
        log.warning(f"Could not get company name for {ticker_upper}. Using ticker.")
        company_name = ticker_upper
    else:
        company_name = stock_info["company_name"]

    # 2. Fetch Content based on the 'source' parameter
    fetched_content = []
    data_source_description = "" # For the response object

    if source == SentimentDataSource.NEWS:
        data_source_description = "News"
        log.info(f"Fetching news data for {ticker_upper}...")
        fetched_content = data_fetcher_service.fetch_news_data_service(ticker_upper, company_name)
    elif source == SentimentDataSource.REDDIT:
        data_source_description = "Reddit"
        log.info(f"Fetching reddit data for {ticker_upper}...")
        fetched_content = data_fetcher_service.fetch_reddit_data_service(ticker_upper, company_name)
    else:
        # Should not happen if Enum is used correctly, but good practice
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data source specified: {source}. Use 'news' or 'reddit'."
        )

    if not fetched_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No relevant content found for ticker '{ticker_upper}' from source '{data_source_description}'."
        )

    # 3. Analyze Sentiment (Service is the same)
    log.info(f"Analyzing sentiment for {len(fetched_content)} items from {data_source_description} for {ticker_upper}...")
    analyzed_details = sentiment_service.analyze_content_sentiment(fetched_content)
    if not analyzed_details:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis failed to produce results for '{ticker_upper}' from source '{data_source_description}'."
        )

    # 4. Calculate Final Score, Suggestion, Validation Points (Services are the same)
    final_score = sentiment_service.calculate_final_sentiment_score(analyzed_details)
    suggestion = sentiment_service.get_sentiment_suggestion(final_score)
    validation_points_raw = sentiment_service.extract_validation_points(analyzed_details)
    validation_points_schema = [stock_schemas.JustificationPoint(**point) for point in validation_points_raw]

    # 5. Prepare Response
    response = stock_schemas.SentimentAnalysisResult(
        ticker=ticker_upper,
        company_name=company_name,
        data_source=data_source_description, # <<< Use the specific source description
        aggregated_score=final_score,
        suggestion=suggestion,
        analyzed_articles_count=len(analyzed_details),
        justification_points=validation_points_schema,
        top_analyzed_items=analyzed_details[:15] # Return top 15 analyzed items
    )

    return response