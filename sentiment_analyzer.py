# sentiment_analyzer.py
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import logging
from config import DEFAULT_SENTIMENT_MODEL
import torch # Or tensorflow if using TF models

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# NOTE: The actual model loading and caching happens in main.py using @st.cache_resource.
# This file defines the logic that USES the loaded model.

def get_sentiment_pipeline(model_name=DEFAULT_SENTIMENT_MODEL):
    """
    Helper function to load the sentiment analysis pipeline.
    This function itself isn't cached here, but called by the cached function in main.py.
    """
    logging.info(f"Attempting to initialize sentiment pipeline with model: {model_name}")
    try:
        # Check for GPU availability, use it if possible
        device = 0 if torch.cuda.is_available() else -1 # 0 for CUDA GPU, -1 for CPU
        # For TensorFlow: device = 0 if tf.config.list_physical_devices('GPU') else -1
        logging.info(f"Using device: {'GPU' if device == 0 else 'CPU'}")

        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=model_name,
            tokenizer=model_name, # Explicitly pass tokenizer
            device=device # Specify CPU or GPU
            # Add truncation=True if headlines might exceed model limits, though less likely for headlines
        )
        logging.info(f"Sentiment analysis pipeline loaded successfully for model '{model_name}'.")
        return sentiment_pipeline
    except Exception as e:
        logging.error(f"Error loading sentiment model '{model_name}': {e}", exc_info=True)
        return None


def analyze_sentiment_for_ticker(news_articles, sentiment_pipeline):
    """
    Analyzes sentiment for a list of news articles (headlines initially)
    using the provided (and cached) sentiment pipeline.
    """
    if not news_articles:
        logging.warning("No news articles provided for sentiment analysis.")
        return 0.0, [] # Return neutral score and empty details

    if sentiment_pipeline is None:
        logging.error("Sentiment pipeline is not available. Cannot analyze.")
        return 0.0, []

    logging.info(f"Analyzing sentiment for {len(news_articles)} articles...")
    analyzed_results = []
    total_score = 0.0
    analyzed_count = 0

    headlines = [article.get('title', '') for article in news_articles if article.get('title')]
    urls = [article.get('url', '') for article in news_articles if article.get('title')] # Keep track of urls

    if not headlines:
        logging.warning("No valid headlines found in the provided articles.")
        return 0.0, []

    try:
        # Process headlines in batches for potentially better performance
        # The pipeline handles batching internally if you pass a list
        results = sentiment_pipeline(headlines, truncation=True, max_length=512) # Add truncation

        for i, result in enumerate(results):
            score = result['score']
            label = result['label']
            headline = headlines[i]
            url = urls[i]

            # --- Score Normalization ---
            # Convert label/score to a single score in range [-1, 1]
            # Assumes 'POSITIVE'/'NEGATIVE' labels from distilbert-sst2
            # Adjust if using a model with different labels (e.g., POSITIVE/NEGATIVE/NEUTRAL or numeric labels)
            if label == 'POSITIVE':
                normalized_score = score
            elif label == 'NEGATIVE':
                normalized_score = -score
            else: # Handle potential 'NEUTRAL' or other labels if model changes
                 logging.warning(f"Unexpected sentiment label '{label}' for model. Treating as neutral (0.0).")
                 normalized_score = 0.0

            analyzed_results.append({
                'headline': headline,
                'url': url, # Include URL for linking
                'score': normalized_score, # Store the [-1, 1] score
                'label': label # Store the original label
            })
            total_score += normalized_score
            analyzed_count += 1

    except Exception as e:
        logging.error(f"Error during batch sentiment analysis: {e}", exc_info=True)
        # Fallback to individual analysis if batch fails (optional)
        # ... (implement fallback loop here if needed) ...

    if analyzed_count > 0:
        aggregated_score = total_score / analyzed_count
        logging.info(f"Sentiment analysis complete. Aggregated score: {aggregated_score:.4f} from {analyzed_count} articles.")
    else:
        aggregated_score = 0.0
        logging.warning("No articles were successfully analyzed.")

    return aggregated_score, analyzed_results


def get_suggestion(aggregated_sentiment_score):
    """
    Maps aggregated sentiment score to a Buy/Sell/Hold suggestion (5 levels).
    """
    logging.info(f"Generating suggestion based on aggregated score: {aggregated_sentiment_score:.4f}")
    # --- Simple Threshold Logic (Tune these values based on testing!) ---
    if aggregated_sentiment_score > 0.6:
        return "Strong Buy"
    elif aggregated_sentiment_score > 0.2: # Adjusted threshold
        return "Buy"
    elif aggregated_sentiment_score >= -0.2: # Adjusted threshold for hold range
        return "Hold"
    elif aggregated_sentiment_score >= -0.6:
        return "Sell"
    else: # score < -0.6
        return "Strong Sell"


def get_validation_points(analyzed_results):
    """
    Selects key news headlines (most positive/negative) to justify the suggestion.
    """
    if not analyzed_results:
        logging.info("No analyzed results to generate validation points.")
        return ["No news data available for justification."]

    # Sort by score: descending for positive, ascending for negative
    sorted_results = sorted(analyzed_results, key=lambda x: x['score'], reverse=True)

    points = []
    # Get top positive driver
    if sorted_results and sorted_results[0]['score'] > 0.05: # Add small threshold to avoid near-zero positives
        top_pos = sorted_results[0]
        points.append(f"🟢 **Positive:** [{top_pos['headline']}]({top_pos['url']}) (Score: {top_pos['score']:.2f})")

    # Get top negative driver (from the end of the sorted list)
    if sorted_results and sorted_results[-1]['score'] < -0.05: # Add small threshold
        top_neg = sorted_results[-1]
        # Prepend to list so negative appears first if selling
        points.insert(0, f"🔴 **Negative:** [{top_neg['headline']}]({top_neg['url']}) (Score: {top_neg['score']:.2f})")

    # If still need more points (e.g., only one strong driver found), add the next most relevant
    if len(points) < 2 and len(sorted_results) > 1:
         if points and points[0].startswith("🟢"): # If only positive found, look for second positive
             if sorted_results[1]['score'] > 0.05:
                 second_pos = sorted_results[1]
                 points.append(f"🟢 **Positive:** [{second_pos['headline']}]({second_pos['url']}) (Score: {second_pos['score']:.2f})")
         elif points and points[0].startswith("🔴"): # If only negative found, look for second negative
             if sorted_results[-2]['score'] < -0.05:
                 second_neg = sorted_results[-2]
                 points.append(f"🔴 **Negative:** [{second_neg['headline']}]({second_neg['url']}) (Score: {second_neg['score']:.2f})")

    if not points:
         points.append("⚪️ **Neutral:** News sentiment appears balanced or neutral.")

    logging.info(f"Generated {len(points)} validation points.")
    return points[:3] # Return max 3 points