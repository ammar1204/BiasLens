from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from .utils import _model_cache


class BiasDetector:
    def __init__(self, model_name="martin-ha/toxic-comment-model", threshold=0.6):
        if model_name not in _model_cache:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            pipe = pipeline("text-classification", model=model, tokenizer=tokenizer)
            _model_cache[model_name] = {
                "tokenizer": tokenizer,
                "model": model,
                "pipeline": pipe
            }
        self.pipeline = _model_cache[model_name]["pipeline"]
        self.threshold = threshold

    def detect(self, text):
        try:
            result = self.pipeline(text)[0]

            # Handle different model outputs - some return TOXIC/NOT_TOXIC, others return scores
            if hasattr(result, 'label'):
                if result['label'] in ['TOXIC', 'BIASED', '1']:
                    bias_score = result['score']
                else:
                    bias_score = 1 - result['score']  # Invert if label is negative
            else:
                bias_score = result['score']

            if bias_score >= self.threshold:
                confidence_level = "High" if bias_score >= 0.8 else "Medium"
                return True, f"Potentially Biased - {confidence_level} Confidence ({bias_score:.3f})"
            else:
                return False, f"Likely Neutral (confidence: {1 - bias_score:.3f})"

        except Exception as e:
            # Fallback in case of model errors
            return False, f"Analysis Error: {str(e)}"


class BiasTypeClassifier:
    def __init__(self, model_name="facebook/bart-large-mnli"):
        if model_name not in _model_cache:
            _model_cache[model_name] = pipeline("zero-shot-classification", model=model_name)
        self.classifier = _model_cache[model_name]

    def predict(self, text):
        try:
            labels = [
                "political bias",
                "ethnic bias",
                "religious bias",
                "gender bias",
                "economic bias",
                "social bias",
                "no bias"
            ]

            result = self.classifier(text, labels)

            # Get top prediction
            top_type = result['labels'][0]
            top_confidence = round(result['scores'][0] * 100, 2)

            # If "no bias" is the top prediction with high confidence, mark as neutral
            if top_type == "no bias" and top_confidence > 70:
                bias_type = "neutral"
            else:
                bias_type = top_type

            return {
                "type": bias_type,
                "confidence": top_confidence,
                "all_predictions": [
                    {
                        "type": label,
                        "confidence": round(score * 100, 2)
                    }
                    for label, score in zip(result['labels'][:3], result['scores'][:3])  # Top 3 only
                ]
            }

        except Exception as e:
            return {
                "type": "analysis_error",
                "confidence": 0,
                "error": str(e),
                "all_predictions": []
            }