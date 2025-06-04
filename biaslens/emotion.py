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
        self.labels = ['sadness', 'joy', 'love', 'anger', 'fear', 'surprise']

        # Emotion intensity grouping for bias analysis
        # 'neutral' is not a direct output of the bhadresh-savani model with 6 labels.
        # We will define intensity based on the 6 emotions.
        self.emotion_intensity = {
            'high_intensity': ['anger', 'fear', 'sadness'], # Typically strong negative emotions
            'positive_intensity': ['joy', 'love'], # Typically strong positive emotions
            'surprise_intensity': ['surprise'], # Surprise can be strong but is valence-ambiguous
            # No 'low_intensity' or 'medium_intensity' explicitly defined here unless mapped from the above
            # For 'is_emotionally_charged', we'll focus on high_intensity and positive_intensity.
        }
        # For _calculate_manipulation_risk, we will use these definitions:
        self.positive_emotions_for_risk = ['joy', 'love'] # Surprise is less about manipulation risk here
        self.negative_emotions_for_risk = ['sadness', 'anger', 'fear']


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
            intensity_category = self._get_intensity_category(primary_emotion) # This will use the updated self.emotion_intensity

            # Calculate emotional manipulation risk
            manipulation_risk = self._calculate_manipulation_risk(primary_emotion, confidence) # This will use updated positive/negative lists

            # Moderate intensity threshold for being charged (example, can be tuned)
            moderate_intensity_threshold = 0.6 # Using confidence directly as a proxy for intensity strength

            return {
                "label": primary_emotion,
                "confidence": round(confidence * 100, 2),
                "intensity_category": intensity_category,
                "manipulation_risk": manipulation_risk,
                "top_emotions": top_emotions,
                "is_emotionally_charged": confidence >= moderate_intensity_threshold # Updated logic
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
        # Adjusted to use the new 6-label system
        for category, emotions_list in self.emotion_intensity.items():
            if emotion in emotions_list:
                return category
        # Fallback if an emotion (somehow) isn't in the new intensity map
        if emotion in self.negative_emotions_for_risk: return 'high_intensity' # Default for known negative
        if emotion in self.positive_emotions_for_risk: return 'positive_intensity' # Default for known positive
        return "unknown"

    def _calculate_manipulation_risk(self, emotion, confidence):
        """Calculate risk of emotional manipulation based on emotion type and confidence,
           adapted for 6 labels.
        """
        # Using negative_emotions_for_risk for high manipulation potential
        # Joy/Love (positive_emotions_for_risk) could also be manipulative if confidence is very high,
        # but typically less so than fear/anger. Surprise is neutral in this context.

        if emotion in self.negative_emotions_for_risk and confidence > 0.7: # e.g. fear, anger
            return "high"
        elif emotion in self.negative_emotions_for_risk and confidence > 0.5: # e.g. sadness
            return "medium"
        # Consider very high confidence positive emotions as potentially manipulative (e.g. excessive hype)
        elif emotion in self.positive_emotions_for_risk and confidence > 0.85:
            return "medium"
        elif emotion in self.negative_emotions_for_risk and confidence > 0.3: # Lower confidence negative
            return "low"
        elif emotion in self.positive_emotions_for_risk and confidence > 0.6: # Moderate positive
            return "low"
        else: # Includes 'surprise' and low confidence positive/negative emotions
            return "minimal"