from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from .utils import _model_cache


class NigerianBiasEnhancer:
    def __init__(self):
        # Nigerian-specific bias indicators
        self.nigerian_patterns = {
            "political": {
                "parties": ["apc", "pdp", "labour party", "nnpp", "apga", "buhari", "tinubu", "atiku", "obi"],
                "regions": ["north", "south", "middle belt", "core north", "arewa", "biafra"],
                "bias_terms": ["northerner", "southerner", "cabals", "fulani agenda", "igbo agenda", "yoruba agenda"]
            },
            "ethnic": {
                "groups": ["yoruba", "igbo", "hausa", "fulani", "ijaw", "kanuri", "tiv", "edo", "efik"],
                "stereotypes": ["lazy", "greedy", "violent", "dominating", "cunning", "fraudulent"],
                "derogatory": ["aboki", "nyamiri", "gambari", "omo ale", "kafir"]
            },
            "religious": {
                "groups": ["christian", "muslim", "catholic", "pentecostal", "orthodox", "sunni", "shia"],
                "bias_terms": ["infidel", "kafir", "pagan", "fundamentalist", "jihadist", "crusader"],
                "contexts": ["sharia", "christmas", "eid", "crusade", "jihad", "persecution"]
            }
        }

    def detect_nigerian_context(self, text):
        """Quick Nigerian context detection"""
        text_lower = text.lower()
        matches = []

        for category, subcategories in self.nigerian_patterns.items():
            for subcat, terms in subcategories.items():
                for term in terms:
                    if term in text_lower:
                        matches.append({
                            "category": category,
                            "subcategory": subcat,
                            "term": term,
                            "bias_level": self._assess_bias_level(subcat)
                        })

        return matches

    def _assess_bias_level(self, subcategory):
        """Quick bias level assessment"""
        if subcategory in ["derogatory", "bias_terms"]:
            return "high"
        elif subcategory in ["stereotypes"]:
            return "medium"
        else:
            return "low"

    def enhance_bias_score(self, original_score, nigerian_matches):
        """Boost bias score if Nigerian context detected"""
        if not nigerian_matches:
            return original_score, []

        # Calculate boost based on matches
        boost = 0
        for match in nigerian_matches:
            if match["bias_level"] == "high":
                boost += 0.3
            elif match["bias_level"] == "medium":
                boost += 0.2
            else:
                boost += 0.1

        # Cap the boost and combine with original
        boost = min(boost, 0.5)
        enhanced_score = min(original_score + boost, 1.0)

        return enhanced_score, nigerian_matches


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
        self.nigerian_enhancer = NigerianBiasEnhancer()

    def detect(self, text):
        try:
            result = self.pipeline(text)[0]

            # Handle different model outputs - some return TOXIC/NOT_TOXIC, others return scores
            if result['label'] in ['TOXIC', 'BIASED', '1']:
                bias_score = result['score']
            else:
                bias_score = 1 - result['score']  # Invert if label is negative

            # Add Nigerian enhancement
            nigerian_matches = self.nigerian_enhancer.detect_nigerian_context(text)
            enhanced_score, _ = self.nigerian_enhancer.enhance_bias_score(bias_score, nigerian_matches)

            if enhanced_score >= self.threshold:
                confidence_level = "High" if enhanced_score >= 0.8 else "Medium"
                context_info = " (Nigerian context detected)" if nigerian_matches else ""
                return True, f"Potentially Biased - {confidence_level} Confidence ({enhanced_score:.3f}){context_info}"
            else:
                return False, f"Likely Neutral (confidence: {1 - enhanced_score:.3f})"

        except Exception as e:
            # Fallback in case of model errors
            return False, f"Analysis Error: {str(e)}"


class BiasTypeClassifier:
    def __init__(self, model_name="facebook/bart-large-mnli"):
        if model_name not in _model_cache:
            _model_cache[model_name] = pipeline("zero-shot-classification", model=model_name)
        self.classifier = _model_cache[model_name]
        self.nigerian_enhancer = NigerianBiasEnhancer()

    def predict(self, text):
        try:
            # Check for Nigerian context first
            nigerian_matches = self.nigerian_enhancer.detect_nigerian_context(text)

            # Generate specific bias labels based on detected context
            specific_bias_type = self._generate_specific_bias_type(nigerian_matches, text)

            if specific_bias_type:
                # Use the specific bias type we detected
                bias_type = specific_bias_type["type"]
                confidence = specific_bias_type["confidence"]

                response = {
                    "type": bias_type,
                    "confidence": confidence,
                    "specific_target": specific_bias_type["target"],
                    "bias_category": specific_bias_type["category"],
                    "all_predictions": [
                        {
                            "type": bias_type,
                            "confidence": confidence
                        }
                    ]
                }
            else:
                # Fall back to general classification
                labels = [
                    "political bias",
                    "ethnic bias",
                    "religious bias",
                    "gender bias",
                    "social bias",
                    "no bias"
                ]

                result = self.classifier(text, labels)
                top_type = result['labels'][0]
                top_confidence = round(result['scores'][0] * 100, 2)

                if top_type == "no bias" and top_confidence > 70:
                    bias_type = "neutral"
                else:
                    bias_type = top_type

                response = {
                    "type": bias_type,
                    "confidence": top_confidence,
                    "all_predictions": [
                        {
                            "type": label,
                            "confidence": round(score * 100, 2)
                        }
                        for label, score in zip(result['labels'][:3], result['scores'][:3])
                    ]
                }

            # Add detected context info
            if nigerian_matches:
                response["detected_terms"] = [match['term'] for match in nigerian_matches[:3]]

            return response

        except Exception as e:
            return {
                "type": "analysis_error",
                "confidence": 0,
                "error": str(e),
                "all_predictions": []
            }

    def _generate_specific_bias_type(self, nigerian_matches, text):
        """Generate specific bias type based on detected Nigerian context"""
        if not nigerian_matches:
            return None

        text_lower = text.lower()

        # Check for specific political party bias
        political_parties = {
            "apc": "APC political bias",
            "pdp": "PDP political bias",
            "labour party": "Labour Party political bias",
            "obi": "Peter Obi political bias",
            "tinubu": "Tinubu political bias",
            "atiku": "Atiku political bias",
            "buhari": "Buhari political bias"
        }

        # Check for specific ethnic bias
        ethnic_groups = {
            "yoruba": "Anti-Yoruba ethnic bias",
            "igbo": "Anti-Igbo ethnic bias",
            "hausa": "Anti-Hausa ethnic bias",
            "fulani": "Anti-Fulani ethnic bias",
            "ijaw": "Anti-Ijaw ethnic bias",
            "aboki": "Anti-Northern ethnic bias",
            "nyamiri": "Anti-Igbo ethnic bias",
            "gambari": "Anti-Hausa ethnic bias"
        }

        # Check for specific religious bias
        religious_groups = {
            "christian": "Anti-Christian religious bias",
            "muslim": "Anti-Muslim religious bias",
            "sharia": "Anti-Islamic religious bias",
            "jihad": "Anti-Islamic religious bias",
            "crusade": "Anti-Christian religious bias",
            "infidel": "Religious intolerance bias",
            "kafir": "Anti-Christian religious bias"
        }

        # Check for regional bias
        regional_terms = {
            "north": "Anti-Northern regional bias",
            "south": "Anti-Southern regional bias",
            "northerner": "Anti-Northern regional bias",
            "southerner": "Anti-Southern regional bias",
            "arewa": "Pro-Northern regional bias",
            "biafra": "Pro-Biafran regional bias"
        }

        # Look for specific matches and determine bias direction
        for match in nigerian_matches:
            term = match['term']

            # Check political bias
            if term in political_parties:
                bias_direction = self._determine_bias_direction(text_lower, term)
                specific_type = political_parties[term]
                if bias_direction == "negative":
                    specific_type = f"Anti-{term.upper()} political bias"
                elif bias_direction == "positive":
                    specific_type = f"Pro-{term.upper()} political bias"

                return {
                    "type": specific_type,
                    "confidence": 85,
                    "target": term.upper(),
                    "category": "political"
                }

            # Check ethnic bias
            if term in ethnic_groups:
                return {
                    "type": ethnic_groups[term],
                    "confidence": 90,
                    "target": term.capitalize(),
                    "category": "ethnic"
                }

            # Check religious bias
            if term in religious_groups:
                return {
                    "type": religious_groups[term],
                    "confidence": 88,
                    "target": term.capitalize(),
                    "category": "religious"
                }

            # Check regional bias
            if term in regional_terms:
                return {
                    "type": regional_terms[term],
                    "confidence": 82,
                    "target": term.capitalize(),
                    "category": "regional"
                }

        return None

    def _determine_bias_direction(self, text, term):
        """Determine if bias is positive or negative toward the term"""
        negative_indicators = ["bad", "terrible", "corrupt", "evil", "worst", "hate", "destroy", "useless",
                               "incompetent"]
        positive_indicators = ["good", "great", "best", "love", "excellent", "amazing", "support", "vote"]

        # Look for sentiment words near the term
        words = text.split()
        term_index = -1
        for i, word in enumerate(words):
            if term in word:
                term_index = i
                break

        if term_index == -1:
            return "neutral"

        # Check words around the term (±3 words)
        context_start = max(0, term_index - 3)
        context_end = min(len(words), term_index + 4)
        context_words = words[context_start:context_end]

        negative_count = sum(1 for word in context_words if any(neg in word for neg in negative_indicators))
        positive_count = sum(1 for word in context_words if any(pos in word for pos in positive_indicators))

        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        else:
            return "neutral"