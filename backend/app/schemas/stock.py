# app/schemas/stock.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict # Use Optional or | None

# --- Stock Info Schemas ---
class StockInfoBase(BaseModel):
    symbol: str
    company_name: str
    current_price: float | str | None # Allow float, string "N/A", or None
    currency: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[int] = None
    error: Optional[str] = None # For returning info about data issues

class StockInfo(StockInfoBase):
    # Potentially add more fields or the raw yfinance info if needed
    # info_raw: Optional[Dict[str, Any]] = None
    pass

# --- Sentiment Analysis Schemas ---
class AnalyzedItem(BaseModel):
    headline: Optional[str] = None
    url: Optional[str] = None
    score: float
    label: str
    publishedAt: Optional[str] = None # Keep as string from source
    source_name: Optional[str] = None
    source_type: Optional[str] = None

class JustificationPoint(BaseModel):
    type: str # 'positive', 'negative', 'neutral'
    headline: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    score: Optional[float] = None

class SentimentAnalysisResult(BaseModel):
    ticker: str
    company_name: str
    data_source: str # e.g., "News", "Reddit", "Combined"
    aggregated_score: float
    suggestion: str
    analyzed_articles_count: int
    justification_points: List[JustificationPoint] = []
    # Optionally include top N analyzed articles details
    top_analyzed_items: List[AnalyzedItem] = []