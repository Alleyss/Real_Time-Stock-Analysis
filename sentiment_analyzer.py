# sentiment_analyzer.py
from transformers import pipeline
import logging
from config import DEFAULT_SENTIMENT_MODEL, RECENCY_DECAY_HALF_LIFE_HOURS, INTENSITY_BOOST_FACTOR
import torch
from datetime import datetime, timezone
import math

# Logging setup (main app.py usually handles this)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_sentiment_pipeline(model_name=DEFAULT_SENTIMENT_MODEL):
    logging.info(f"Attempting to initialize sentiment pipeline with model: {model_name}")
    try:
        device = 0 if torch.cuda.is_available() else -1
        logging.info(f"Using device: {'GPU' if device == 0 else 'CPU'} for Hugging Face pipeline.")
        sentiment_pipeline_instance = pipeline(
            "sentiment-analysis", model=model_name, tokenizer=model_name, device=device, truncation=True
        )
        logging.info(f"Sentiment analysis pipeline loaded successfully for model '{model_name}'.")
        return sentiment_pipeline_instance
    except Exception as e:
        logging.error(f"Error loading sentiment model '{model_name}': {e}", exc_info=True)
        return None

def analyze_sentiment_for_ticker(fetched_content_list, sentiment_pipeline_instance):
    """
    Analyzes sentiment for a list of fetched content items.
    Each item in fetched_content_list is a dict from data_fetcher.
    """
    if not fetched_content_list:
        logging.warning("No content provided for sentiment analysis.")
        return [] # Return empty list of details

    if sentiment_pipeline_instance is None:
        logging.error("Sentiment pipeline is not available. Cannot analyze.")
        return []

    logging.info(f"Analyzing sentiment for {len(fetched_content_list)} items...")
    analyzed_details_list = []

    # Prepare texts and keep track of original items
    texts_for_analysis = []
    original_items_map = [] # To map results back to original item data

    for i, item in enumerate(fetched_content_list):
        text_to_analyze = item.get('full_text', item.get('headline')) # Prioritize full_text
        if not text_to_analyze:
            logging.warning(f"Skipping item due to missing text content: {item.get('url', 'N/A')}")
            continue
        texts_for_analysis.append(text_to_analyze)
        original_items_map.append(item) # Store the whole original item

    if not texts_for_analysis:
        logging.warning("No valid text found in content items to analyze.")
        return []

    try:
        logging.info(f"Running HF pipeline on {len(texts_for_analysis)} text pieces...")
        # FinBERT's default max_length is 512. Truncation is important.
        results = sentiment_pipeline_instance(texts_for_analysis, truncation=True, max_length=512)
        logging.info("HF pipeline processing complete.")

        for i, result in enumerate(results):
            original_item = original_items_map[i]
            
            model_score = result['score']
            model_label = result['label'].lower()

            normalized_score = 0.0
            if model_label == 'positive':
                normalized_score = model_score
            elif model_label == 'negative':
                normalized_score = -model_score
            elif model_label == 'neutral':
                normalized_score = 0.0 
            else:
                 logging.warning(f"Unexpected sentiment label '{model_label}'. Treating as neutral.")
            
            analyzed_details_list.append({
                'headline': original_item.get('headline', 'N/A'), # For display
                'full_text_analyzed': texts_for_analysis[i][:100]+'...', # For debug, show what was analyzed
                'url': original_item.get('url'),
                'score': normalized_score, # Model's normalized score [-1, 1]
                'label': model_label,      # Model's label ('positive', 'negative', 'neutral')
                'publishedAt': original_item.get('publishedAt'), # Crucial for recency
                'source_name': original_item.get('source_name', 'Unknown'),
                'source_type': original_item.get('source_type', 'unknown')
            })

    except Exception as e:
        logging.error(f"Error during batch sentiment analysis: {e}", exc_info=True)

    logging.info(f"Sentiment analysis produced details for {len(analyzed_details_list)} items.")
    return analyzed_details_list


def calculate_weighted_sentiment(analyzed_details_list, 
                                 recency_half_life_hours=RECENCY_DECAY_HALF_LIFE_HOURS, 
                                 intensity_boost_factor=INTENSITY_BOOST_FACTOR):
    """
    Calculates a single weighted sentiment score from a list of analyzed items.
    Weights are based on recency and sentiment intensity.
    """
    if not analyzed_details_list:
        logging.warning("No analyzed details to calculate weighted sentiment from.")
        return 0.0

    total_weighted_score_sum = 0.0
    total_weight_sum = 0.0
    now_utc = datetime.now(timezone.utc)

    for item in analyzed_details_list:
        sentiment_score = item['score'] # This is the normalized score from the model
        published_at_str = item.get('publishedAt')

        # 1. Recency Weight
        recency_weight = 0.1 # Default small weight if no date
        if published_at_str:
            try:
                # Ensure 'Z' is handled for ISO format
                if published_at_str.endswith('Z'):
                    published_at_str = published_at_str[:-1] + '+00:00'
                published_dt = datetime.fromisoformat(published_at_str)
                # Ensure it's offset-aware UTC
                if published_dt.tzinfo is None or published_dt.tzinfo.utcoffset(published_dt) is None:
                    published_dt = published_dt.replace(tzinfo=timezone.utc) # Assume UTC if naive
                else:
                    published_dt = published_dt.astimezone(timezone.utc)

                age_hours = (now_utc - published_dt).total_seconds() / 3600.0
                if age_hours < 0: age_hours = 0 # Future posts get max recency
                
                # Exponential decay: weight = exp(-ln(2) * age / half_life)
                recency_weight = math.exp(-math.log(2) * age_hours / recency_half_life_hours)
            except ValueError:
                logging.warning(f"Could not parse 'publishedAt' timestamp: {published_at_str}. Using default recency weight.")
        
        # 2. Intensity Weight (based on the sentiment score magnitude)
        # Adds a bit more weight to stronger opinions (either positive or negative)
        intensity_weight_component = 1.0 + (abs(sentiment_score) * intensity_boost_factor)

        # Combine weights (multiplicative, or choose another strategy)
        combined_item_weight = recency_weight * intensity_weight_component
        
        total_weighted_score_sum += sentiment_score * combined_item_weight
        total_weight_sum += combined_item_weight

    if total_weight_sum == 0: # Avoid division by zero if no items or all weights are zero
        logging.warning("Total weight sum is zero in weighted sentiment calculation. Returning 0.0.")
        # Fallback: simple average if weights are zero but scores exist
        if analyzed_details_list:
            return sum(item['score'] for item in analyzed_details_list) / len(analyzed_details_list)
        return 0.0
    
    final_weighted_score = total_weighted_score_sum / total_weight_sum
    logging.info(f"Calculated final weighted sentiment: {final_weighted_score:.4f} from {len(analyzed_details_list)} items.")
    return final_weighted_score


def get_suggestion(aggregated_sentiment_score):
    logging.info(f"Generating suggestion based on aggregated score: {aggregated_sentiment_score:.4f}")
    if aggregated_sentiment_score > 0.25: return "Strong Buy" # Adjusted thresholds slightly
    elif aggregated_sentiment_score > 0.05: return "Buy"
    elif aggregated_sentiment_score >= -0.05: return "Hold"
    elif aggregated_sentiment_score >= -0.25: return "Sell"
    else: return "Strong Sell"

def get_validation_points(analyzed_results):
    if not analyzed_results:
        return ["⚪️ No content data available for justification."]

    sorted_results = sorted(analyzed_results, key=lambda x: x['score'], reverse=True)
    points = []
    POSITIVE_THRESHOLD = 0.1 # Slightly higher threshold for "significant"
    NEGATIVE_THRESHOLD = -0.1

    # Top positive
    if sorted_results and sorted_results[0]['score'] > POSITIVE_THRESHOLD:
        top_pos = sorted_results[0]
        points.append(f"🟢 **Positive ({top_pos['source_name']})**: [{top_pos['headline']}]({top_pos['url']}) (Score: {top_pos['score']:.2f})")

    # Top negative
    if sorted_results and sorted_results[-1]['score'] < NEGATIVE_THRESHOLD:
        top_neg = sorted_results[-1]
        points.append(f"🔴 **Negative ({top_neg['source_name']})**: [{top_neg['headline']}]({top_neg['url']}) (Score: {top_neg['score']:.2f})")
    
    # If only one strong point, try to add another less extreme one or a neutral one
    if len(points) < 2 and len(sorted_results) > (1 if points else 0) :
        if not points: # No strong points, pick most neutral or just top one
            item = min(sorted_results, key=lambda x: abs(x['score'])) if any(abs(x['score']) < 0.05 for x in sorted_results) else sorted_results[0]
            points.append(f"⚪️ **Neutral/Mix ({item['source_name']})**: [{item['headline']}]({item['url']}) (Score: {item['score']:.2f})")
        # Could add logic to pick second positive/negative if one already exists

    if not points: # Still no points (e.g., all very neutral)
         closest_neutral = min(analyzed_results, key=lambda x: abs(x['score']), default=None)
         if closest_neutral:
              points.append(f"⚪️ **Neutral ({closest_neutral['source_name']})**: [{closest_neutral['headline']}]({closest_neutral['url']}) (Score: {closest_neutral['score']:.2f})")
         else:
              points.append("⚪️ Sentiment appears balanced or lacks strong drivers.")

    logging.info(f"Generated {len(points)} validation points.")
    return points[:3]