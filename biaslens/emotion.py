from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
from .utils import _model_cache


class EmotionClassifier:
    def __init__(self, model_name="bhadresh-savani/distilbert-base-uncased-emotion"):
        if model_name not in _model_cache:
            _model_cache[model_name] = {
                "tokenizer": AutoTokenizer.from_pretrained(model_name),
                "model": AutoModelForSequenceClassification.from_pretrained(model_name),
            }
        self.tokenizer = _model_cache[model_name]["tokenizer"]
        self.model = _model_cache[model_name]["model"]
        self.labels = [
            'admiration', 'amusement', 'anger', 'annoyance', 'approval', 'caring',
            'confusion', 'curiosity', 'desire', 'disappointment', 'disapproval',
            'disgust', 'embarrassment', 'excitement', 'fear', 'gratitude', 'grief',
            'joy', 'love', 'nervousness', 'optimism', 'pride', 'realization',
            'relief', 'remorse', 'sadness', 'surprise', 'neutral'
        ]

        # Emotion intensity grouping for bias analysis
        self.emotion_intensity = {
            'high_intensity': ['anger', 'fear', 'disgust', 'grief', 'excitement'],
            'medium_intensity': ['annoyance', 'disappointment', 'disapproval', 'nervousness', 'surprise'],
            'low_intensity': ['confusion', 'curiosity', 'realization', 'neutral'],
            'positive': ['admiration', 'amusement', 'approval', 'caring', 'gratitude', 'joy', 'love', 'optimism',
                         'pride', 'relief']
        }

    def classify(self, text, top_k=3):
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

            with torch.no_grad():
                outputs = self.model(**inputs)
                scores = F.softmax(outputs.logits, dim=1)

            # Get top prediction
            predicted_class = torch.argmax(scores).item()
            confidence = torch.max(scores).item()
            primary_emotion = self.labels[predicted_class]

            # Get top-k emotions for more detailed analysis
            top_k_indices = torch.topk(scores, k=min(top_k, len(self.labels))).indices[0]
            top_k_scores = torch.topk(scores, k=min(top_k, len(self.labels))).values[0]

            top_emotions = []
            for idx, score in zip(top_k_indices, top_k_scores):
                top_emotions.append({
                    "emotion": self.labels[idx.item()],
                    "confidence": round(score.item() * 100, 2)
                })

            # Determine emotion intensity category
            intensity_category = self._get_intensity_category(primary_emotion)

            # Calculate emotional manipulation risk
            manipulation_risk = self._calculate_manipulation_risk(primary_emotion, confidence)

            return {
                "label": primary_emotion,
                "confidence": round(confidence * 100, 2),
                "intensity_category": intensity_category,
                "manipulation_risk": manipulation_risk,
                "top_emotions": top_emotions,
                "is_emotionally_charged": confidence > 0.7 and intensity_category in ['high_intensity',
                                                                                      'medium_intensity']
            }

        except Exception as e:
            return {
                "label": "analysis_error",
                "confidence": 0,
                "intensity_category": "unknown",
                "manipulation_risk": "unknown",
                "top_emotions": [],
                "is_emotionally_charged": False,
                "error": str(e)
            }

    def _get_intensity_category(self, emotion):
        """Categorize emotion by intensity level"""
        for category, emotions in self.emotion_intensity.items():
            if emotion in emotions:
                return category
        return "unknown"

    def _calculate_manipulation_risk(self, emotion, confidence):
        """Calculate risk of emotional manipulation based on emotion type and confidence"""
        high_risk_emotions = ['anger', 'fear', 'disgust', 'grief']
        medium_risk_emotions = ['annoyance', 'disappointment', 'disapproval', 'excitement']

        if emotion in high_risk_emotions and confidence > 0.7:
            return "high"
        elif emotion in medium_risk_emotions and confidence > 0.6:
            return "medium"
        elif emotion in high_risk_emotions or (emotion in medium_risk_emotions and confidence > 0.4):
            return "low"
        else:
            return "minimal"