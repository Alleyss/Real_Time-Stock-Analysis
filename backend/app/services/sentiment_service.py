# app/services/sentiment_service.py
import logging
import math
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.core.config import settings # Use backend settings
# Import the getter for the loaded pipeline
from app.sentiment_model_loader import get_sentiment_pipeline

log = logging.getLogger(__name__)

# --- Sentiment Analysis Core Logic ---
def analyze_content_sentiment(content_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyzes sentiment for a list of fetched content items using the loaded pipeline."""
    if not content_list:
        log.warning("No content provided for sentiment analysis service.")
        return []

    try:
        sentiment_pipeline = get_sentiment_pipeline() # Get the globally loaded pipeline
    except RuntimeError as e:
        log.error(f"Sentiment pipeline unavailable: {e}")
        return [] # Cannot proceed without the model

    log.info(f"Analyzing sentiment for {len(content_list)} items in service...")
    analyzed_details_list = []
    texts_for_analysis = []
    original_items_map = []

    for item in content_list:
        text = item.get('full_text', item.get('headline'))
        if text:
            texts_for_analysis.append(text)
            original_items_map.append(item)
        else:
            log.warning(f"Skipping item due to missing text: {item.get('url', item.get('id', 'N/A'))}")

    if not texts_for_analysis:
        log.warning("No valid text found in content items to analyze.")
        return []

    try:
        # Perform analysis in batches
        results = sentiment_pipeline(texts_for_analysis) # truncation=True is set during pipeline load

        for i, result in enumerate(results):
            original_item = original_items_map[i]
            model_score = result['score']
            model_label = result['label'].lower()

            normalized_score = 0.0
            if model_label == 'positive': normalized_score = model_score
            elif model_label == 'negative': normalized_score = -model_score
            # Neutral label maps to 0.0

            # Prepare result, include identifier for potential DB updates later
            item_id_for_update = original_item.get('id') # Reddit ID or News URL

            analyzed_details_list.append({
                'headline': original_item.get('headline', 'N/A'),
                'url': original_item.get('url'),
                'score': normalized_score,
                'label': model_label,
                'publishedAt': original_item.get('publishedAt'),
                'source_name': original_item.get('source_name', 'Unknown'),
                'source_type': original_item.get('source_type', 'unknown'),
                'source_specific_id': item_id_for_update # ID for potential later use
            })
    except Exception as e:
        log.error(f"Error during batch sentiment analysis in service: {e}", exc_info=True)
        # Depending on policy, might return partial results or empty list
        return [] # Return empty on error for now

    log.info(f"Sentiment service produced details for {len(analyzed_details_list)} items.")
    return analyzed_details_list

# --- Weighted Score, Suggestion, Validation Points Logic (Adapted from Streamlit version) ---
def calculate_final_sentiment_score(analyzed_details: List[Dict[str, Any]]) -> float:
    """Calculates the final weighted sentiment score."""
    if not analyzed_details: return 0.0

    total_weighted_score = 0.0
    total_weight = 0.0
    now_utc = datetime.now(timezone.utc)
    half_life_hours = getattr(settings, "RECENCY_DECAY_HALF_LIFE_HOURS", 72.0)
    intensity_boost = getattr(settings, "INTENSITY_BOOST_FACTOR", 0.15)

    for item in analyzed_details:
        score = item.get('score', 0.0)
        pub_str = item.get('publishedAt')
        recency_weight = 0.1 # Default low weight

        if pub_str:
            try:
                # Use the same parsing logic as database.py's _parse_datetime
                if isinstance(pub_str, datetime): dt = pub_str
                else:
                     if pub_str.endswith('Z'): pub_str = pub_str[:-1] + '+00:00'
                     dt = datetime.fromisoformat(pub_str)
                
                if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                else: dt = dt.astimezone(timezone.utc)
                
                age_hours = max(0, (now_utc - dt).total_seconds() / 3600.0)
                recency_weight = math.exp(-math.log(2) * age_hours / half_life_hours)
            except (ValueError, TypeError):
                log.warning(f"Could not parse timestamp '{pub_str}' for recency weight.")

        intensity_weight = 1.0 + (abs(score) * intensity_boost)
        item_weight = recency_weight * intensity_weight

        total_weighted_score += score * item_weight
        total_weight += item_weight

    if total_weight == 0: return 0.0
    return total_weighted_score / total_weight

def get_sentiment_suggestion(score: float) -> str:
    """Maps score to suggestion."""
    # Use thresholds (consider making these configurable via settings)
    if score > 0.25: return "Strong Buy"
    elif score > 0.05: return "Buy"
    elif score >= -0.05: return "Hold"
    elif score >= -0.25: return "Sell"
    else: return "Strong Sell"

def extract_validation_points(analyzed_details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Selects key positive/negative items for justification."""
    if not analyzed_details: return []

    # Sort by score (descending)
    sorted_results = sorted(analyzed_details, key=lambda x: x.get('score', 0.0), reverse=True)
    
    points = []
    POS_THRESHOLD = 0.1
    NEG_THRESHOLD = -0.1

    # Top positive
    if sorted_results and sorted_results[0].get('score', 0.0) > POS_THRESHOLD:
        points.append({
            "type": "positive",
            "headline": sorted_results[0].get('headline'),
            "url": sorted_results[0].get('url'),
            "source": sorted_results[0].get('source_name'),
            "score": sorted_results[0].get('score')
        })

    # Top negative
    if sorted_results and sorted_results[-1].get('score', 0.0) < NEG_THRESHOLD:
         points.append({
            "type": "negative",
            "headline": sorted_results[-1].get('headline'),
            "url": sorted_results[-1].get('url'),
            "source": sorted_results[-1].get('source_name'),
            "score": sorted_results[-1].get('score')
        })

    # Add neutral/mixed example if few strong points
    if len(points) < 2:
         closest_neutral = min(analyzed_details, key=lambda x: abs(x.get('score', 0.0)), default=None)
         if closest_neutral and closest_neutral not in [p.get('headline') for p in points if 'headline' in p]: # Avoid duplicates
              points.append({
                "type": "neutral",
                "headline": closest_neutral.get('headline'),
                "url": closest_neutral.get('url'),
                "source": closest_neutral.get('source_name'),
                "score": closest_neutral.get('score')
              })

    return points[:3] # Return top 3 justification points