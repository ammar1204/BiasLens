"""
Sentiment Analysis Module for BiasLens.

This module provides the `SentimentAnalyzer` class for performing sentiment
analysis on text. It uses a pre-trained model from Hugging Face Transformers
and includes functionalities for:
- Basic sentiment classification (positive, negative, neutral).
- Text preprocessing tailored for sentiment analysis (e.g., handling social media elements).
- Calculating sentiment strength.
- Identifying potential bias indicators based on sentiment extremity.
- Measuring sentiment polarization.
- Comparing sentiment between headline and content to detect clickbait.
"""
import re
from typing import Dict, Any, List
# from transformers import AutoTokenizer, AutoModelForSequenceClassification # Handled by models module
import torch
import torch.nn.functional as F
# from .utils import _model_cache # Used by models module
from . import models


# Threshold for determining if sentiment is highly polarized.
# If the absolute difference between positive and negative scores exceeds this,
# it's considered polarized.
POLARIZATION_THRESHOLD = 0.6

# Threshold for headline vs. content sentiment mismatch score to be considered clickbait.
# If the normalized mismatch score is above this, it's flagged as likely clickbait.
CLICKBAIT_MISMATCH_THRESHOLD = 0.35

# Thresholds for categorizing headline-content mismatch level based on normalized score.
MISMATCH_LEVEL_HIGH_THRESHOLD = 0.5
MISMATCH_LEVEL_MEDIUM_THRESHOLD = 0.25


class SentimentAnalyzer:
    """
    Analyzes the sentiment of a given text.

    This class utilizes a pre-trained Transformer model, defaulting to
    "cardiffnlp/twitter-roberta-base-sentiment-latest", which is specialized
    for sentiment analysis on social media text but works well on general text too.
    It outputs labels like 'positive', 'negative', or 'neutral' along with
    confidence scores and other derived metrics.

    Attributes:
        tokenizer: Hugging Face tokenizer instance.
        model: Hugging Face sequence classification model instance.
        labels (List[str]): The sentiment labels the model predicts (typically
                            ['negative', 'neutral', 'positive']).
    """
    def __init__(self, model_name: str = models.DEFAULT_SENTIMENT_MODEL) -> None:
        """
        Initializes the SentimentAnalyzer.

        Args:
            model_name (str): The name of the Hugging Face model to use.
                              Defaults to models.DEFAULT_SENTIMENT_MODEL.
        """
        # Use the centralized model loading function.
        # SentimentAnalyzer often uses models like 'cardiffnlp/twitter-roberta-base-sentiment-latest'
        # which might have TF origins, so from_tf_fallback=True is important.
        self.tokenizer, self.model = models.get_tokenizer_and_model(model_name, from_tf_fallback=True)
        self.model_name = model_name # Store for reference

        # Standard labels for this type of sentiment model
        self.labels: List[str] = ['negative', 'neutral', 'positive']

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Performs sentiment analysis on the input text.

        Args:
            text (str): The text to analyze.

        Returns:
            Dict[str, Any]: A dictionary containing the sentiment analysis results:
                - "label" (str): Predicted sentiment label ('negative', 'neutral', 'positive').
                - "confidence" (float): Confidence score (0.0-1.0) for the predicted label.
                - "all_scores" (Dict[str, float]): Scores for all sentiment labels.
                - "sentiment_strength" (str): Qualitative strength ('weak', 'moderate', 'strong').
                - "bias_indicator" (bool): True if sentiment suggests potential bias.
                - "polarization_score" (float): Score indicating how polarized the sentiment is
                                               (0.0 to 1.0, difference between positive and negative).
                - "is_polarized" (bool): True if polarization_score is high.
                - "emotional_tone" (str): Qualitative description of the emotional tone.
                - "error" (str, optional): Error message if analysis failed.
        """
        try:
            # Handle empty or very short text to avoid model errors or meaningless results
            if not text or len(text.strip()) < 3: # Arbitrary minimum length
                return {
                    'label': 'neutral',
                    'confidence': 0.5, # Default confidence for ambiguous short text
                    'all_scores': {'negative': 0.33, 'neutral': 0.50, 'positive': 0.17}, # Balanced default
                    'sentiment_strength': 'weak',
                    'bias_indicator': False,
                    'polarization_score': 0.16, # abs(0.17-0.33)
                    'is_polarized': False,
                    'emotional_tone': 'neutral'
                }

            # Preprocess text for better model performance
            cleaned_text = self._preprocess_text(text)

            # Tokenize the cleaned text
            encoded_input = self.tokenizer(
                cleaned_text,
                return_tensors='pt', # PyTorch tensors
                truncation=True,    # Truncate if longer than max_length
                max_length=self.tokenizer.model_max_length if hasattr(self.tokenizer, 'model_max_length') else 512,
                padding=True        # Pad to max_length (or max in batch if dynamic)
            )

            # Perform inference
            with torch.no_grad(): # Disable gradient calculations
                output = self.model(**encoded_input)

            # Convert logits to probabilities using softmax
            scores = output.logits[0] # Get logits for the first (and only) item in batch
            probs = F.softmax(scores, dim=0) # Apply softmax along the class dimension

            # Get the predicted class index and its confidence
            top_class_idx = torch.argmax(probs).item()
            confidence = probs[top_class_idx].item()

            # Map scores to labels
            all_label_scores: Dict[str, float] = {}
            for i, label_name in enumerate(self.labels):
                all_label_scores[label_name] = round(probs[i].item(), 3)

            predicted_label = self.labels[top_class_idx]

            # Calculate additional metrics
            sentiment_strength = self._calculate_sentiment_strength(confidence, all_label_scores)
            bias_indicator = self._check_bias_indicator(predicted_label, confidence, all_label_scores)
            polarization = abs(all_label_scores.get('positive', 0.0) - all_label_scores.get('negative', 0.0))

            return {
                'label': predicted_label,
                'confidence': round(confidence, 3),
                'all_scores': all_label_scores,
                'sentiment_strength': sentiment_strength,
                'bias_indicator': bias_indicator,
                'polarization_score': round(polarization, 3),
                'is_polarized': polarization > POLARIZATION_THRESHOLD,
                'emotional_tone': self._get_emotional_tone(all_label_scores)
            }

        except Exception as e:
            # Fallback response in case of any error during analysis
            # print(f"Error during sentiment analysis: {e}") # Optional: log error
            return {
                'label': 'neutral', # Default to neutral on error
                'confidence': 0.0,
                'all_scores': {'negative': 0.33, 'neutral': 0.34, 'positive': 0.33}, # Default scores
                'sentiment_strength': 'unknown',
                'bias_indicator': False,
                'polarization_score': 0.0,
                'is_polarized': False,
                'emotional_tone': 'neutral',
                'error': str(e)
            }

    def _preprocess_text(self, text: str) -> str:
        """
        Cleans and preprocesses text for optimal sentiment analysis.

        Steps include:
        - Removing excessive whitespace.
        - Normalizing user mentions (e.g., @username to @USER).
        - Replacing URLs with a placeholder "URL".
        - Normalizing repeated punctuation marks.

        Args:
            text (str): The input text.

        Returns:
            str: The cleaned text.
        """
        # Remove excessive whitespace (leading, trailing, multiple spaces)
        processed_text = re.sub(r'\s+', ' ', text.strip())

        # Normalize Twitter-style mentions to a generic token @USER
        processed_text = re.sub(r'@\w+', '@USER', processed_text)
        # Replace URLs with a generic token URL
        processed_text = re.sub(r'http\S+|www\S+', 'URL', processed_text)

        # Normalize excessive punctuation to avoid model misinterpretations
        # e.g., "!!!" becomes "!", "???" becomes "?", "...." becomes "..."
        processed_text = re.sub(r'([!?.]){2,}', r'\1', processed_text) # More general: replaces 2+ with one
        processed_text = re.sub(r'\.{3,}', '...', processed_text) # Specifically handle ellipses if previous rule is too aggressive

        return processed_text

    def _calculate_sentiment_strength(self, confidence: float, scores: Dict[str, float]) -> str:
        """
        Determines the strength of the detected sentiment based on confidence.

        Args:
            confidence (float): The confidence score (0.0-1.0) of the primary sentiment.
            scores (Dict[str, float]): A dictionary of scores for all sentiment labels.
                                       (Currently unused in this specific strength logic but passed for potential future use).

        Returns:
            str: Sentiment strength ('weak', 'moderate', 'strong').
        """
        # Thresholds (0.4 for weak/moderate, 0.7 for moderate/strong) are heuristic and can be tuned.
        if confidence < 0.4: # Low confidence suggests weak sentiment
            return 'weak'
        elif confidence < 0.7: # Moderate confidence
            return 'moderate'
        else: # High confidence suggests strong sentiment
            return 'strong'

    def _check_bias_indicator(self, predicted_label: str, confidence: float, scores: Dict[str, float]) -> bool:
        """
        Checks if the sentiment characteristics suggest a potential bias in the text.

        Indications of bias can include:
        - Very strong negative sentiment expressed with high confidence.
        - Highly polarized content (very high positive or negative score, with a very low neutral score).

        Args:
            predicted_label (str): The primary predicted sentiment label.
            confidence (float): The confidence score for the predicted_label.
            scores (Dict[str, float]): Scores for all sentiment labels.

        Returns:
            bool: True if sentiment patterns indicate potential bias, False otherwise.
        """
        # Strong negative sentiment with high confidence can be an indicator of biased language.
        # Threshold (0.8 for confidence) is heuristic.
        if predicted_label == 'negative' and confidence > 0.8: # Heuristic threshold
            return True

        # Very polarized content: if neutral score is very low and overall confidence in non-neutral is high.
        # This suggests the text strongly leans one way or another, potentially ignoring neutrality.
        # Thresholds (0.2 for neutral score, 0.7 for confidence) are heuristic.
        if scores.get('neutral', 1.0) < 0.2 and confidence > 0.7: # Heuristic thresholds
            return True

        return False

    def _get_emotional_tone(self, scores: Dict[str, float]) -> str:
        """
        Categorizes the overall emotional tone based on sentiment scores.

        Provides a more nuanced qualitative description than just the primary label.

        Args:
            scores (Dict[str, float]): Scores for 'negative', 'positive', 'neutral' sentiments.

        Returns:
            str: A string describing the emotional tone (e.g., "highly_negative",
                 "positive_leaning", "neutral").
        """
        neg_score = scores.get('negative', 0.0) # Use .get for safety if a score is missing
        pos_score = scores.get('positive', 0.0)
        neu_score = scores.get('neutral', 0.0)

        # Thresholds (e.g., 0.6 for 'highly', 0.2 for score difference checks) are heuristic.
        if neg_score > 0.6 and neg_score > pos_score + 0.2: # Significantly more negative
            return 'highly_negative'
        elif pos_score > 0.6 and pos_score > neg_score + 0.2: # Significantly more positive
            return 'highly_positive'
        elif neu_score > 0.6: # Clearly neutral
            return 'neutral'
        elif neg_score > pos_score and neg_score > neu_score: # Leaning negative
            return 'negative_leaning'
        elif pos_score > neg_score and pos_score > neu_score: # Leaning positive
            return 'positive_leaning'
        elif abs(pos_score - neg_score) < 0.15 and neu_score < 0.5 : # Similar positive and negative scores, and not strongly neutral
            return 'mixed'
        else: # Default or primarily neutral but not strongly so
            return 'balanced_or_neutral'


    def analyze_headline_vs_content(self, headline: str, content: str) -> Dict[str, Any]:
        """
        Compares sentiment between a headline and its corresponding content.

        This can help detect clickbait, where headlines might use sensational
        sentiment not reflected in the content.

        Args:
            headline (str): The headline text.
            content (str): The main content text.

        Returns:
            Dict[str, Any]: A dictionary with sentiment analysis for both headline
                            and content, plus mismatch scores and clickbait likelihood:
                            - "headline_sentiment" (Dict): Full sentiment analysis of the headline.
                            - "content_sentiment" (Dict): Full sentiment analysis of the content.
                            - "mismatch_score" (float): Average absolute difference in sentiment
                                                        scores across labels (0.0-1.0).
                            - "is_clickbait_likely" (bool): True if mismatch_score is high.
                            - "mismatch_level" (str): Qualitative mismatch level ('high', 'medium', 'low').
                            - "error" (str, optional): Error message if analysis failed.
        """
        try:
            headline_sentiment_result = self.analyze(headline)
            content_sentiment_result = self.analyze(content)

            # Ensure 'all_scores' is present before proceeding
            if 'error' in headline_sentiment_result or 'error' in content_sentiment_result:
                error_msg = headline_sentiment_result.get('error') or content_sentiment_result.get('error')
                raise Exception(f"Sentiment analysis failed for headline or content: {error_msg}")

            headline_all_scores = headline_sentiment_result['all_scores']
            content_all_scores = content_sentiment_result['all_scores']

            # Calculate sentiment mismatch score: average absolute difference across sentiment dimensions
            # This score ranges from 0 (no mismatch) to approx 0.66 for max theoretical mismatch
            # (e.g. one is 100% pos, other is 100% neg).
            # A more practical max might be around 1.0 if one is (1,0,0) and other is (0,0,1) for (pos,neu,neg)
            # Normalizing by len(self.labels) is effectively (sum_abs_diff / 3) * (2/2) to scale it.
            # A simpler sum of absolute differences might range 0-2.
            # Let's use sum of absolute differences for now, max value 2.0

            current_mismatch_score = 0.0
            num_labels = 0
            for label in self.labels: # Iterate over 'negative', 'neutral', 'positive'
                score_headline = headline_all_scores.get(label, 0.0) # Default to 0 if label missing
                score_content = content_all_scores.get(label, 0.0)
                current_mismatch_score += abs(score_headline - score_content)
                num_labels +=1

            # Normalize the mismatch score to be roughly between 0 and 1.
            # Max possible sum_abs_diff is 2.0 (e.g. H: (1,0,0), C: (0,0,1) -> |1-0|+|0-0|+|0-1| = 2)
            # Or H: (1,0,0), C: (0,1,0) -> |1-0|+|0-1|+|0-0| = 2
            # Dividing by num_labels (3) makes it average diff per label (0 to ~0.67)
            # Dividing by 2 (max possible diff) normalizes to 0-1.
            normalized_mismatch_score = round(current_mismatch_score / 2.0, 3) if num_labels > 0 else 0.0


            # Determine clickbait likelihood and mismatch level based on the normalized score.
            is_likely_clickbait = normalized_mismatch_score > CLICKBAIT_MISMATCH_THRESHOLD

            # Thresholds for mismatch_level are heuristic.
            if normalized_mismatch_score > MISMATCH_LEVEL_HIGH_THRESHOLD:
                mismatch_level_qualitative = 'high'
            elif normalized_mismatch_score > MISMATCH_LEVEL_MEDIUM_THRESHOLD:
                mismatch_level_qualitative = 'medium'
            else:
                mismatch_level_qualitative = 'low'

            return {
                'headline_sentiment': headline_sentiment_result,
                'content_sentiment': content_sentiment_result,
                'mismatch_score': normalized_mismatch_score,
                'is_clickbait_likely': is_likely_clickbait,
                'mismatch_level': mismatch_level_qualitative
            }

        except Exception as e:
            # print(f"Error in analyze_headline_vs_content: {e}") # Optional: log error
            return {
                'headline_sentiment': None,
                'content_sentiment': None,
                'mismatch_score': 0.0,
                'is_clickbait_likely': False,
                'mismatch_level': 'unknown',
                'error': str(e)
            }