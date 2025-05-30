"""
Model Management Module for BiasLens.

This module centralizes the loading, caching, and management of
various Hugging Face Transformer models used throughout the BiasLens application.
It uses a shared cache (`_model_cache` from `biaslens.utils`) to avoid
redundant model loading.
"""

from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline as hf_pipeline
from .utils import _model_cache # Corrected import path for sibling module

# Define constants for default model names
# These can be imported by other modules if they need to refer to these defaults.
DEFAULT_TOXIC_COMMENT_MODEL = "martin-ha/toxic-comment-model"
DEFAULT_ZERO_SHOT_CLASSIFICATION_MODEL = "facebook/bart-large-mnli"
DEFAULT_EMOTION_MODEL = "bhadresh-savani/distilbert-base-uncased-emotion" # As used in EmotionClassifier
DEFAULT_SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"

def get_text_classification_pipeline(model_name: str, tokenizer_name: str = None):
    """
    Loads or retrieves a cached Hugging Face text-classification pipeline.

    Args:
        model_name (str): The Hugging Face model identifier.
        tokenizer_name (str, optional): The Hugging Face tokenizer identifier.
                                        If None, `model_name` is used for tokenizer.
                                        Defaults to None.

    Returns:
        A Hugging Face text-classification pipeline instance.
    """
    # Use model_name as the primary key for the pipeline, as it defines the core component.
    # If a specific tokenizer_name is provided that differs from model_name,
    # the current caching strategy might not distinguish it if another call uses
    # model_name for both. For simplicity, we assume model_name is unique enough for pipeline caching.
    cache_key = f"pipeline_{model_name}_{tokenizer_name if tokenizer_name else model_name}"

    if cache_key not in _model_cache:
        effective_tokenizer_name = tokenizer_name if tokenizer_name else model_name
        try:
            tokenizer = AutoTokenizer.from_pretrained(effective_tokenizer_name)
        except Exception as e: # Fallback for older models if needed, though less common for pipelines
            print(f"Standard tokenizer loading failed for {effective_tokenizer_name}, trying with from_tf=True. Error: {e}")
            tokenizer = AutoTokenizer.from_pretrained(effective_tokenizer_name, from_tf=True)

        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        pipe = hf_pipeline("text-classification", model=model, tokenizer=tokenizer)
        _model_cache[cache_key] = pipe
        print(f"Loaded and cached pipeline: {cache_key}") # For verification
    return _model_cache[cache_key]

def get_zero_shot_classification_pipeline(model_name: str):
    """
    Loads or retrieves a cached Hugging Face zero-shot-classification pipeline.

    Args:
        model_name (str): The Hugging Face model identifier.

    Returns:
        A Hugging Face zero-shot-classification pipeline instance.
    """
    cache_key = f"pipeline_{model_name}" # Simpler key as model usually dictates tokenizer for these pipelines
    if cache_key not in _model_cache:
        # Zero-shot pipelines typically handle their tokenizers internally based on the model.
        pipe = hf_pipeline("zero-shot-classification", model=model_name)
        _model_cache[cache_key] = pipe
        print(f"Loaded and cached pipeline: {cache_key}") # For verification
    return _model_cache[cache_key]

def get_tokenizer_and_model(model_name: str, tokenizer_name: str = None, from_tf_fallback: bool = False):
    """
    Loads or retrieves a cached Hugging Face tokenizer and a sequence classification model.

    This is for components that use the tokenizer and model separately, not as a pipeline.

    Args:
        model_name (str): The Hugging Face model identifier.
        tokenizer_name (str, optional): The Hugging Face tokenizer identifier.
                                        If None, `model_name` is used. Defaults to None.
        from_tf_fallback (bool): If True, attempts to load tokenizer with `from_tf=True`
                                 on initial failure. Defaults to False.

    Returns:
        Tuple[AutoTokenizer, AutoModelForSequenceClassification]: A tuple containing
                                                                  the tokenizer and model.
    """
    effective_tokenizer_name = tokenizer_name if tokenizer_name else model_name
    tokenizer_cache_key = f"tokenizer_{effective_tokenizer_name}"
    model_cache_key = f"model_{model_name}"

    if tokenizer_cache_key not in _model_cache:
        try:
            tokenizer = AutoTokenizer.from_pretrained(effective_tokenizer_name)
        except Exception as e: # Catch a broad exception for initial attempt
            if from_tf_fallback:
                print(f"Standard tokenizer loading failed for {effective_tokenizer_name}, trying with from_tf=True. Error: {e}")
                tokenizer = AutoTokenizer.from_pretrained(effective_tokenizer_name, from_tf=True)
            else:
                # If no fallback, or fallback also fails (though not explicitly caught here), re-raise.
                # For simplicity, the original exception 'e' is more informative here.
                raise e
        _model_cache[tokenizer_cache_key] = tokenizer
        print(f"Loaded and cached tokenizer: {tokenizer_cache_key}")

    if model_cache_key not in _model_cache:
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        _model_cache[model_cache_key] = model
        print(f"Loaded and cached model: {model_cache_key}")

    return _model_cache[tokenizer_cache_key], _model_cache[model_cache_key]

# Placeholder for other model types if needed in the future
# e.g., for specific tasks like NER, Question Answering, etc.
