"""
Emotion Classification Module for BiasLens.

This module provides the `EmotionClassifier` class to classify text into various
emotional categories. It uses a pre-trained model from Hugging Face Transformers
and provides additional logic to assess emotional intensity and potential for
manipulation based on the detected emotions.
"""
from typing import Dict, Any, List
# from transformers import AutoTokenizer, AutoModelForSequenceClassification # Handled by models module
import torch
import torch.nn.functional as F
# from .utils import _model_cache # _model_cache is used by models module
from . import models

# Confidence threshold above which a high/medium intensity emotion is considered "emotionally charged".
EMOTIONALLY_CHARGED_CONFIDENCE_THRESHOLD = 0.7


class EmotionClassifier:
    """
    Classifies the emotional content of a given text.

    This classifier uses a pre-trained sequence classification model. While the
    default `model_name` parameter in `__init__` might point to a general emotion
    model (e.g., "bhadresh-savani/distilbert-base-uncased-emotion" with ~6-7 labels),
    the internal `self.labels` list is configured for a more fine-grained set of 28 emotions,
    implying compatibility with models like "j-hartmann/emotion-english-distilroberta-base"
    or a custom model fine-tuned for these specific labels. The class maps these
    emotions to intensity levels and assesses manipulation risk.

    Attributes:
        tokenizer: Hugging Face tokenizer instance.
        model: Hugging Face sequence classification model instance.
        labels (List[str]): List of emotion labels the model is expected to predict.
        emotion_intensity (Dict[str, List[str]]): Mapping of intensity categories
                                                  (high, medium, low, positive) to emotions.
    """
    def __init__(self, model_name: str = models.DEFAULT_EMOTION_MODEL) -> None:
        """
        Initializes the EmotionClassifier.

        Args:
            model_name (str): The name of the Hugging Face model to use.
                              Defaults to models.DEFAULT_EMOTION_MODEL.
                              Note: The `self.labels` attribute suggests a model capable of
                              predicting a more extensive set of 28 emotions. For this to work,
                              the specified `model_name` should align with these labels.
        """
        # Use the centralized model loading function.
        # The EmotionClassifier typically doesn't need the from_tf_fallback for common emotion models.
        self.tokenizer, self.model = models.get_tokenizer_and_model(model_name, from_tf_fallback=False)
        self.model_name = model_name # Store for reference if needed

        # This list of 28 labels is characteristic of models like 'j-hartmann/emotion-english-distilroberta-base'.
        # It's crucial that the `model_name` passed (or the default) is compatible with these labels.
        self.labels: List[str] = [
            'admiration', 'amusement', 'anger', 'annoyance', 'approval', 'caring',
            'confusion', 'curiosity', 'desire', 'disappointment', 'disapproval',
            'disgust', 'embarrassment', 'excitement', 'fear', 'gratitude', 'grief',
            'joy', 'love', 'nervousness', 'optimism', 'pride', 'realization',
            'relief', 'remorse', 'sadness', 'surprise', 'neutral'
        ]

        # Defines how emotions are grouped by intensity for further analysis,
        # such as assessing manipulation risk or whether text is emotionally charged.
        self.emotion_intensity: Dict[str, List[str]] = {
            'high_intensity': ['anger', 'fear', 'disgust', 'grief', 'excitement'], # Strong, often negative, activating emotions
            'medium_intensity': ['annoyance', 'disappointment', 'disapproval', 'nervousness', 'surprise'], # Noticeable, can be negative or activating
            'low_intensity': ['confusion', 'curiosity', 'realization', 'neutral'], # Less impactful or more cognitive emotions
            'positive': ['admiration', 'amusement', 'approval', 'caring', 'gratitude', 'joy', 'love', 'optimism',
                         'pride', 'relief'] # Generally positive valence emotions
        }

    def classify(self, text: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Classifies the emotions in the given text.

        Args:
            text (str): The text to analyze.
            top_k (int): The number of top emotions to return in the 'top_emotions' list.
                         Defaults to 3.

        Returns:
            Dict[str, Any]: A dictionary containing the emotion analysis:
                - "label" (str): The primary (highest confidence) emotion detected.
                - "confidence" (float): Confidence score (0-100) for the primary emotion.
                - "intensity_category" (str): Category of emotional intensity
                  (e.g., "high_intensity", "positive").
                - "manipulation_risk" (str): Assessed risk of emotional manipulation
                  (e.g., "high", "minimal").
                - "top_emotions" (List[Dict]): List of top_k emotions, each with
                  "emotion" and "confidence".
                - "is_emotionally_charged" (bool): True if the text is considered
                  significantly emotionally charged.
                - "error" (str, optional): Error message if analysis failed.
        """
        try:
            # Tokenize the input text
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

            # Perform inference
            with torch.no_grad(): # Disable gradient calculations for inference
                outputs = self.model(**inputs)
                # Apply softmax to get probabilities
                scores = F.softmax(outputs.logits, dim=1)

            # Get the primary emotion (highest score)
            predicted_class_idx = torch.argmax(scores).item()
            confidence = torch.max(scores).item()
            primary_emotion = self.labels[predicted_class_idx] # Map index to label

            # Get top-k emotions for more detailed output
            actual_top_k = min(top_k, len(self.labels)) # Ensure k is not out of bounds
            top_k_scores, top_k_indices = torch.topk(scores, k=actual_top_k)

            top_emotions_list: List[Dict[str, Any]] = []
            for i in range(actual_top_k):
                emotion_label = self.labels[top_k_indices[0, i].item()]
                emotion_score = round(top_k_scores[0, i].item() * 100, 2)
                top_emotions_list.append({"emotion": emotion_label, "confidence": emotion_score})

            # Determine the intensity category of the primary emotion
            intensity_category = self._get_intensity_category(primary_emotion)

            # Calculate the risk of emotional manipulation
            manipulation_risk = self._calculate_manipulation_risk(primary_emotion, confidence)

            # Determine if the text is emotionally charged.
            # Considered charged if confidence is high (above EMOTIONALLY_CHARGED_CONFIDENCE_THRESHOLD)
            # and the emotion falls into 'high_intensity' or 'medium_intensity' categories.
            is_charged = confidence > EMOTIONALLY_CHARGED_CONFIDENCE_THRESHOLD and \
                         intensity_category in ['high_intensity', 'medium_intensity']

            return {
                "label": primary_emotion,
                "confidence": round(confidence * 100, 2),
                "intensity_category": intensity_category,
                "manipulation_risk": manipulation_risk,
                "top_emotions": top_emotions_list,
                "is_emotionally_charged": is_charged
            }

        except Exception as e:
            # Log error if logger is available
            # print(f"Error in EmotionClassifier.classify: {e}")
            return {
                "label": "analysis_error",
                "confidence": 0.0,
                "intensity_category": "unknown",
                "manipulation_risk": "unknown",
                "top_emotions": [],
                "is_emotionally_charged": False,
                "error": f"Emotion classification failed: {str(e)}"
            }

    def _get_intensity_category(self, emotion: str) -> str:
        """
        Categorizes a given emotion into an intensity level.

        The categorization is based on the `self.emotion_intensity` mapping.

        Args:
            emotion (str): The emotion label (e.g., "anger", "joy").

        Returns:
            str: The intensity category ("high_intensity", "medium_intensity",
                 "low_intensity", "positive", or "unknown" if not found).
        """
        for category, emotions_in_category in self.emotion_intensity.items():
            if emotion in emotions_in_category:
                return category
        return "unknown" # Default if emotion is not in any predefined category

    def _calculate_manipulation_risk(self, emotion: str, confidence: float) -> str:
        """
        Calculates the risk of emotional manipulation based on emotion type and confidence.

        Certain strong negative emotions, when expressed with high confidence, are
        considered to pose a higher risk of being used for manipulation.

        Args:
            emotion (str): The primary emotion detected.
            confidence (float): The confidence score (0.0 to 1.0) for the primary emotion.

        Returns:
            str: The assessed manipulation risk ("high", "medium", "low", "minimal").
        """
        # Emotions often associated with manipulative language if dominant and strong
        high_risk_emotions: List[str] = ['anger', 'fear', 'disgust', 'grief']
        # Emotions that can be manipulative but might also be common reactions
        medium_risk_emotions: List[str] = ['annoyance', 'disappointment', 'disapproval', 'excitement']

        # Emotions often associated with manipulative language if dominant and strong
        high_risk_emotions: List[str] = ['anger', 'fear', 'disgust', 'grief']
        # Emotions that can be manipulative but might also be common reactions
        medium_risk_emotions: List[str] = ['annoyance', 'disappointment', 'disapproval', 'excitement']

        # High risk: strong negative emotions with high confidence.
        # Threshold (0.7) is heuristic, indicating significant confidence in a high-risk emotion.
        if emotion in high_risk_emotions and confidence > 0.7: # Heuristic threshold
            return "high"
        # Medium risk: medium negative/activating emotions with moderate+ confidence.
        # Threshold (0.6) is heuristic.
        elif emotion in medium_risk_emotions and confidence > 0.6: # Heuristic threshold
            return "medium"
        # Low risk: strong negative emotions with lower confidence, or medium ones with some confidence.
        # Threshold (0.4) is heuristic, indicating some presence but not dominant with high confidence.
        elif emotion in high_risk_emotions or \
             (emotion in medium_risk_emotions and confidence > 0.4): # Heuristic threshold
            return "low"
        # Minimal risk: other emotions or low confidence for riskier ones.
        else:
            return "minimal"