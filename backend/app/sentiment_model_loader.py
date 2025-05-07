# app/sentiment_model_loader.py
import logging
from transformers import pipeline, Pipeline # Pipeline type hint
from app.core.config import settings
import torch # Keep torch import for device check example

# Configure logging for this module
log = logging.getLogger(__name__)
# Use basicConfig here or rely on FastAPI's logging setup if configured later
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')

# Global variable to hold the pipeline
sentiment_pipeline_instance: Pipeline | None = None

def load_sentiment_model():
    """Loads the sentiment analysis model into the global instance."""
    global sentiment_pipeline_instance
    if sentiment_pipeline_instance is None:
        model_name = settings.DEFAULT_SENTIMENT_MODEL
        log.info(f"Attempting to load sentiment model: {model_name}")
        try:
            # Check for GPU availability explicitly if needed, otherwise pipeline auto-detects
            device_num = 0 if torch.cuda.is_available() else -1
            log.info(f"Using device: {'GPU 0' if device_num == 0 else 'CPU'} for Hugging Face pipeline.")

            sentiment_pipeline_instance = pipeline(
                "sentiment-analysis",
                model=model_name,
                # tokenizer=model_name, # Often optional
                device=device_num,
                truncation=True # Good default for potentially long texts
            )
            log.info(f"Sentiment analysis pipeline loaded successfully for model '{model_name}'.")
        except Exception as e:
            log.error(f"CRITICAL: Error loading sentiment model '{model_name}': {e}", exc_info=True)
            # Depending on requirements, you might want the app to fail startup
            # raise RuntimeError(f"Failed to load sentiment model: {e}") from e
            sentiment_pipeline_instance = None # Ensure it remains None if loading failed
    else:
        # This shouldn't ideally happen if loaded only on startup, but good for debug
        log.debug("Sentiment model already loaded.")

def get_sentiment_pipeline() -> Pipeline:
    """
    Returns the loaded pipeline instance.
    Raises RuntimeError if the pipeline hasn't been loaded successfully.
    """
    if sentiment_pipeline_instance is None:
        # This indicates an issue with application startup logic
        log.error("FATAL: get_sentiment_pipeline called before model was loaded!")
        raise RuntimeError("Sentiment analysis model is not available.")
    return sentiment_pipeline_instance

# NOTE: load_sentiment_model() will be called via a FastAPI startup event in main.py