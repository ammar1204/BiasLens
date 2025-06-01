from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
from .utils import _model_cache


class SentimentAnalyzer:
    def __init__(self, model_name="cardiffnlp/twitter-roberta-base-sentiment-latest"):
        if model_name not in _model_cache:
            try:
                # Try without from_tf first (newer models don't need it)
                tokenizer = AutoTokenizer.from_pretrained(model_name)
            except:
                # Fallback to from_tf if needed
                tokenizer = AutoTokenizer.from_pretrained(model_name, from_tf=True)

            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            _model_cache[model_name] = {
                "tokenizer": tokenizer,
                "model": model,
            }

        self.tokenizer = _model_cache[model_name]["tokenizer"]
        self.model = _model_cache[model_name]["model"]
        self.labels = ['negative', 'neutral', 'positive']

    def analyze(self, text):
        try:
            # Handle empty or very short text
            if not text or len(text.strip()) < 3:
                return {
                    'label': 'neutral',
                    'confidence': 0.5,
                    'all_scores': {'negative': 0.33, 'neutral': 0.5, 'positive': 0.17},
                    'sentiment_strength': 'weak',
                    'bias_indicator': False
                }

            # Preprocess text (remove excessive whitespace, handle mentions/hashtags)
            cleaned_text = self._preprocess_text(text)

            # Tokenize with proper truncation
            encoded_input = self.tokenizer(
                cleaned_text,
                return_tensors='pt',
                truncation=True,
                max_length=512,
                padding=True
            )

            with torch.no_grad():
                output = self.model(**encoded_input)

            # Convert to probabilities
            scores = output.logits[0]
            probs = F.softmax(scores, dim=0)

            # Get predictions
            top_class = torch.argmax(probs).item()
            confidence = probs[top_class].item()

            # Create score dictionary
            all_scores = {}
            for i, label in enumerate(self.labels):
                all_scores[label] = round(probs[i].item(), 3)

            # Determine sentiment strength
            sentiment_strength = self._calculate_sentiment_strength(confidence, all_scores)

            # Check for bias indicators (extreme sentiment with high confidence)
            bias_indicator = self._check_bias_indicator(self.labels[top_class], confidence, all_scores)

            # Calculate polarization score (how far from neutral)
            polarization = abs(all_scores['positive'] - all_scores['negative'])

            return {
                'label': self.labels[top_class],
                'confidence': round(confidence, 3),
                'all_scores': all_scores,
                'sentiment_strength': sentiment_strength,
                'bias_indicator': bias_indicator,
                'polarization_score': round(polarization, 3),
                'is_polarized': polarization > 0.6,  # Highly polarized content
                'emotional_tone': self._get_emotional_tone(all_scores)
            }

        except Exception as e:
            # Fallback response if analysis fails
            return {
                'label': 'neutral',
                'confidence': 0.0,
                'all_scores': {'negative': 0.33, 'neutral': 0.34, 'positive': 0.33},
                'sentiment_strength': 'unknown',
                'bias_indicator': False,
                'polarization_score': 0.0,
                'is_polarized': False,
                'emotional_tone': 'neutral',
                'error': str(e)
            }

    def _preprocess_text(self, text):
        """Clean and preprocess text for better sentiment analysis"""
        import re

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Handle Twitter-specific elements (keep context but normalize)
        text = re.sub(r'@\w+', '@USER', text)  # Replace mentions
        text = re.sub(r'http\S+|www\S+', 'URL', text)  # Replace URLs

        # Handle excessive punctuation
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[.]{3,}', '...', text)

        return text

    def _calculate_sentiment_strength(self, confidence, scores):
        """Determine how strong the sentiment is"""
        if confidence < 0.4:
            return 'weak'
        elif confidence < 0.7:
            return 'moderate'
        else:
            return 'strong'

    def _check_bias_indicator(self, predicted_label, confidence, scores):
        """Check if sentiment indicates potential bias"""
        # Strong negative sentiment with high confidence often indicates bias
        if predicted_label == 'negative' and confidence > 0.8:
            return True

        # Very polarized content (very high positive or negative, very low neutral)
        if scores['neutral'] < 0.2 and confidence > 0.7:
            return True

        return False

    def _get_emotional_tone(self, scores):
        """Categorize the emotional tone for easier interpretation"""
        neg_score = scores['negative']
        pos_score = scores['positive']
        neu_score = scores['neutral']

        if neg_score > 0.6:
            return 'highly_negative'
        elif pos_score > 0.6:
            return 'highly_positive'
        elif neu_score > 0.6:
            return 'neutral'
        elif neg_score > pos_score:
            return 'negative_leaning'
        elif pos_score > neg_score:
            return 'positive_leaning'
        else:
            return 'balanced'

    def analyze_headline_vs_content(self, headline, content):
        """Compare sentiment between headline and content to detect clickbait"""
        try:
            headline_sentiment = self.analyze(headline)
            content_sentiment = self.analyze(content)

            # Calculate sentiment mismatch
            headline_score = headline_sentiment['all_scores']
            content_score = content_sentiment['all_scores']

            mismatch_score = 0
            for label in self.labels:
                mismatch_score += abs(headline_score[label] - content_score[label])

            mismatch_score = round(mismatch_score / len(self.labels), 3)

            return {
                'headline_sentiment': headline_sentiment,
                'content_sentiment': content_sentiment,
                'mismatch_score': mismatch_score,
                'is_clickbait_likely': mismatch_score > 0.3,  # Significant mismatch
                'mismatch_level': 'high' if mismatch_score > 0.5 else 'medium' if mismatch_score > 0.3 else 'low'
            }

        except Exception as e:
            return {
                'headline_sentiment': None,
                'content_sentiment': None,
                'mismatch_score': 0,
                'is_clickbait_likely': False,
                'mismatch_level': 'unknown',
                'error': str(e)
            }