# app/schemas/common.py (New file or existing)
from enum import Enum

class SentimentDataSource(str, Enum):
    NEWS = "news"
    REDDIT = "reddit"
    # Add other sources later if needed, e.g., ALL = "all"