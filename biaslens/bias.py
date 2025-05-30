"""
Bias Detection and Classification Module for BiasLens.

This module provides classes to:
1. Detect the presence of potential bias in text using a pre-trained text classification model.
2. Classify the type of detected bias (e.g., political, gender) using a zero-shot
   classification model.

It utilizes Hugging Face Transformers for model loading and inference, and includes
a simple caching mechanism for models.
"""
from typing import Tuple, Dict, Any, List
# Remove direct Hugging Face imports if they are fully handled by biaslens.models
# from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from . import models # Import the new models module
# _model_cache is now used by biaslens.models, so direct import here might not be needed unless for other reasons.
# from .utils import _model_cache


# Default threshold for considering a text as potentially biased in BiasDetector.
DEFAULT_BIAS_DETECTION_THRESHOLD = 0.6

# Default confidence threshold (percentage) for accepting "no bias" as the primary label in BiasTypeClassifier.
# If "no bias" is predicted with confidence below this, the next best actual bias type might be chosen.
DEFAULT_NO_BIAS_CONFIDENCE_THRESHOLD = 60.0


class BiasDetector:
    """
    Detects the presence of potential bias in text.

    This class uses a text classification model (e.g., a toxicity detection model)
    to determine if a given text likely contains biased language. The default model
    is "martin-ha/toxic-comment-model", which is a general toxicity detection model.
    The interpretation of "toxicity" is used here as a proxy for potential bias.

    Attributes:
        pipeline: The Hugging Face text classification pipeline instance.
        threshold (float): The confidence score threshold above which text is
                           considered potentially biased.
    """
    def __init__(self, model_name: str = models.DEFAULT_TOXIC_COMMENT_MODEL, threshold: float = DEFAULT_BIAS_DETECTION_THRESHOLD) -> None:
        """
        Initializes the BiasDetector.

        Args:
            model_name (str): The name of the Hugging Face model to use for bias detection.
                              Defaults to models.DEFAULT_TOXIC_COMMENT_MODEL.
            threshold (float): The confidence score threshold (0.0 to 1.0) for classifying
                               text as biased. Defaults to DEFAULT_BIAS_DETECTION_THRESHOLD.
        """
        # Use the centralized model loading function
        self.pipeline = models.get_text_classification_pipeline(model_name)
        self.model_name = model_name # Keep model_name if needed for debugging or other logic
        self.threshold: float = threshold

    def detect(self, text: str) -> Tuple[bool, str]:
        """
        Detects potential bias in the given text.

        Args:
            text (str): The text to analyze.

        Returns:
            Tuple[bool, str]: A tuple where:
                - The first element (bool) is True if potential bias is detected, False otherwise.
                - The second element (str) is a message describing the result, including
                  confidence if bias is detected, or neutrality confidence.
                  In case of an error, the bool is False and the message contains the error.
        """
        try:
            # Perform inference using the pipeline
            result = self.pipeline(text)[0] # result is usually a list with one dict

            bias_score: float
            # Model outputs can vary. Some models output 'TOXIC'/'NOT_TOXIC', 'BIASED'/'NEUTRAL',
            # or numerical labels like 'LABEL_1'/'LABEL_0'.
            # We try to infer the score for the "biased" or "toxic" class.
            if 'label' in result and isinstance(result['label'], str):
                # Check if the label indicates toxicity/bias directly
                if result['label'].upper() in ['TOXIC', 'BIASED', 'LABEL_1', '1']:
                    bias_score = result['score']
                # If the label indicates neutrality, the bias_score is 1 minus its confidence
                elif result['label'].upper() in ['NOT_TOXIC', 'NEUTRAL', 'LABEL_0', '0']:
                    bias_score = 1.0 - result['score']
                else:
                    # Default to the returned score if label is unrecognized, assuming it's for the positive/toxic class
                    bias_score = result['score']
            else:
                # If no label or unrecognized label format, assume the score is for the positive/toxic class
                bias_score = result['score']

            # Compare the derived bias_score against the threshold
            if bias_score >= self.threshold:
                confidence_level = "High" if bias_score >= 0.8 else "Medium" # Qualitative confidence
                return True, f"Potentially Biased - {confidence_level} Confidence ({bias_score:.3f})"
            else:
                # If below threshold, it's considered likely neutral.
                # Confidence of neutrality is 1 - bias_score.
                return False, f"Likely Neutral (confidence of neutrality: {1.0 - bias_score:.3f})"

        except Exception as e:
            # Log the error for debugging if a logger is available
            # print(f"Error in BiasDetector.detect: {e}") # Basic print for now
            return False, f"Bias detection analysis failed: {str(e)}"


class BiasTypeClassifier:
    """
    Classifies the type of bias present in a given text.

    This class uses a zero-shot classification model from Hugging Face (default is
    "facebook/bart-large-mnli") to categorize text into predefined bias types
    such as political, gender, ethnic, etc., or "no bias".

    Attributes:
        classifier: The Hugging Face zero-shot classification pipeline instance.
        labels (List[str]): The list of candidate bias type labels for classification.
    """
    def __init__(self, model_name: str = models.DEFAULT_ZERO_SHOT_CLASSIFICATION_MODEL) -> None:
        """
        Initializes the BiasTypeClassifier.

        Args:
            model_name (str): The name of the Hugging Face zero-shot classification model.
                              Defaults to models.DEFAULT_ZERO_SHOT_CLASSIFICATION_MODEL.
        """
        # Use the centralized model loading function
        self.classifier = models.get_zero_shot_classification_pipeline(model_name)
        self.model_name = model_name
        self.labels: List[str] = [
            "political bias", "ethnic bias", "religious bias", "gender bias",
            "economic bias", "social bias", "ageism", "disability bias", "no bias"
        ] # Added more common bias types

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predicts the type of bias in the given text.

        Args:
            text (str): The text to classify.

        Returns:
            Dict[str, Any]: A dictionary containing the classification results:
                - "type" (str): The predicted bias type (e.g., "political bias", "neutral").
                - "confidence" (float): The confidence score (0-100) for the predicted type.
                - "all_predictions" (List[Dict]): A list of the top 3 predictions,
                  each with "type" and "confidence".
                - "error" (str, optional): An error message if analysis failed.
        """
        try:
            # Perform zero-shot classification
            result = self.classifier(text, self.labels, multi_label=False) # Assuming single primary bias type

            # Extract the top prediction (highest score)
            top_label_idx = result['scores'].index(max(result['scores']))
            top_type = result['labels'][top_label_idx]
            top_confidence = round(result['scores'][top_label_idx] * 100, 2)

            # Determine the final bias type.
            # If "no bias" is the top prediction with reasonably high confidence,
            # classify as neutral. Otherwise, use the predicted bias type.
            # The threshold for "no bias" can be adjusted based on model performance.
            if top_type == "no bias" and top_confidence > DEFAULT_NO_BIAS_CONFIDENCE_THRESHOLD: # Use constant
                bias_type_final = "neutral"
                # Ensure confidence for "neutral" reflects the "no bias" score
                final_confidence = top_confidence
            elif top_type == "no bias" and top_confidence <= DEFAULT_NO_BIAS_CONFIDENCE_THRESHOLD: # Use constant
                # If "no bias" has low confidence, pick the next best actual bias type
                # This requires sorting or checking secondary labels if the model isn't already sorted by score
                # For simplicity, if "no bias" is not confident, we might take the top actual bias type.
                # This part might need more sophisticated logic if the primary result is a low-confidence "no bias".
                # For now, let's find the highest scoring actual bias type if "no bias" is not confident.
                best_actual_bias_type = "unknown"
                best_actual_bias_confidence = 0.0
                for label, score in zip(result['labels'], result['scores']):
                    if label != "no bias" and (score * 100) > best_actual_bias_confidence:
                        best_actual_bias_type = label
                        best_actual_bias_confidence = round(score * 100, 2)

                if best_actual_bias_confidence > 0: # Check if any actual bias was found
                    bias_type_final = best_actual_bias_type
                    final_confidence = best_actual_bias_confidence
                else: # Default if no other bias type stands out
                    bias_type_final = "neutral" # Or "undetermined"
                    final_confidence = 100.0 - top_confidence # Confidence in *not* being the low-score "no bias"
            else:
                bias_type_final = top_type
                final_confidence = top_confidence


            # Prepare the top N predictions for output (e.g., top 3)
            # The pipeline already returns sorted labels by score.
            top_n_predictions = []
            for i in range(min(3, len(result['labels']))):
                top_n_predictions.append({
                    "type": result['labels'][i],
                    "confidence": round(result['scores'][i] * 100, 2)
                })

            return {
                "type": bias_type_final,
                "confidence": final_confidence,
                "all_predictions": top_n_predictions
            }

        except Exception as e:
            # Log the error
            # print(f"Error in BiasTypeClassifier.predict: {e}")
            return {
                "type": "analysis_error",
                "confidence": 0.0, # Confidence is 0 in case of error
                "error": f"Bias type classification failed: {str(e)}",
                "all_predictions": []
            }