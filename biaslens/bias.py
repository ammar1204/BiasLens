from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from .utils import _model_cache
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class BiasLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BiasCategory(Enum):
    POLITICAL = "political"
    ETHNIC = "ethnic"
    RELIGIOUS = "religious"
    REGIONAL = "regional"
    GENDER = "gender"
    SOCIAL = "social"


@dataclass
class BiasDetection:
    term: str
    category: BiasCategory
    bias_level: BiasLevel
    confidence: float
    context: str
    bias_direction: str  # positive, negative, neutral
    explanation: str


@dataclass
class ContextualPattern:
    term: str
    neutral_contexts: List[str]
    biased_contexts: List[str]
    requires_context: bool = True


class NigerianContextAnalyzer:
    """Enhanced Nigerian context analyzer with false positive reduction"""
    
    def __init__(self):
        # Context-aware patterns to reduce false positives
        self.contextual_patterns = {
            BiasCategory.POLITICAL: {
                # Political parties - context matters
                "apc": ContextualPattern(
                    term="apc",
                    neutral_contexts=["apc government", "apc policy", "apc announced", "apc said"],
                    biased_contexts=["apc failure", "corrupt apc", "useless apc", "apc cabal"]
                ),
                "pdp": ContextualPattern(
                    term="pdp",
                    neutral_contexts=["pdp statement", "pdp candidate", "former pdp", "pdp government"],
                    biased_contexts=["failed pdp", "corrupt pdp", "pdp disaster", "evil pdp"]
                ),
                "labour party": ContextualPattern(
                    term="labour party",
                    neutral_contexts=["labour party candidate", "labour party rally", "lp spokesperson"],
                    biased_contexts=["fake labour party", "labour party lies", "deceptive labour"]
                ),
                # Politicians
                "tinubu": ContextualPattern(
                    term="tinubu",
                    neutral_contexts=["president tinubu", "tinubu administration", "tinubu announced"],
                    biased_contexts=["corrupt tinubu", "evil tinubu", "dictator tinubu", "failed tinubu"]
                ),
                "obi": ContextualPattern(
                    term="obi",
                    neutral_contexts=["peter obi", "obi campaign", "obi supporters", "mr obi"],
                    biased_contexts=["fake obi", "fraud obi", "liar obi", "deceiver obi"]
                ),
                "atiku": ContextualPattern(
                    term="atiku",
                    neutral_contexts=["atiku abubakar", "former vp atiku", "atiku campaign"],
                    biased_contexts=["corrupt atiku", "failed atiku", "evil atiku"]
                ),
                "buhari": ContextualPattern(
                    term="buhari",
                    neutral_contexts=["former president buhari", "buhari administration", "president buhari"],
                    biased_contexts=["failed buhari", "dictator buhari", "clueless buhari"]
                )
            },
            
            BiasCategory.ETHNIC: {
                # Ethnic groups - geographic context matters
                "yoruba": ContextualPattern(
                    term="yoruba",
                    neutral_contexts=["yoruba language", "yoruba culture", "yoruba people", "yoruba land", "yoruba history"],
                    biased_contexts=["yoruba domination", "yoruba agenda", "greedy yoruba", "cunning yoruba"]
                ),
                "igbo": ContextualPattern(
                    term="igbo",
                    neutral_contexts=["igbo language", "igbo culture", "igbo people", "igbo land", "ndi igbo"],
                    biased_contexts=["igbo agenda", "greedy igbo", "fraudulent igbo", "criminal igbo"]
                ),
                "hausa": ContextualPattern(
                    term="hausa",
                    neutral_contexts=["hausa language", "hausa culture", "hausa people", "hausa land"],
                    biased_contexts=["hausa domination", "violent hausa", "backward hausa", "primitive hausa"]
                ),
                "fulani": ContextualPattern(
                    term="fulani",
                    neutral_contexts=["fulani culture", "fulani people", "fulani community"],
                    biased_contexts=["fulani herdsmen terrorists", "killer fulani", "violent fulani", "fulani invasion"]
                ),
                # Highly derogatory terms - always biased
                "nyamiri": ContextualPattern(
                    term="nyamiri",
                    neutral_contexts=[],  # No neutral contexts for slurs
                    biased_contexts=["nyamiri"],
                    requires_context=False
                ),
                "aboki": ContextualPattern(
                    term="aboki",
                    neutral_contexts=["my aboki", "aboki friend"],  # Can be friendly in some contexts
                    biased_contexts=["stupid aboki", "illiterate aboki", "these aboki people"]
                ),
                "gambari": ContextualPattern(
                    term="gambari",
                    neutral_contexts=[],
                    biased_contexts=["gambari"],
                    requires_context=False
                )
            },
            
            BiasCategory.REGIONAL: {
                # Regional terms - geographic context is crucial
                "north": ContextualPattern(
                    term="north",
                    neutral_contexts=["north nigeria", "northern region", "north east", "north west", "north central", 
                                    "going north", "north of lagos", "northern states", "from the north"],
                    biased_contexts=["backward north", "primitive north", "north domination", "northern agenda",
                                   "lazy northerners", "illiterate north"]
                ),
                "south": ContextualPattern(
                    term="south",
                    neutral_contexts=["south nigeria", "southern region", "south east", "south west", "south south",
                                    "going south", "south of abuja", "southern states", "from the south"],
                    biased_contexts=["greedy south", "south domination", "southern agenda", "cunning southerners"]
                ),
                "arewa": ContextualPattern(
                    term="arewa",
                    neutral_contexts=["arewa community", "arewa youth", "arewa forum", "arewa consultative"],
                    biased_contexts=["arewa domination", "arewa supremacy", "arewa against others"]
                ),
                "biafra": ContextualPattern(
                    term="biafra",
                    neutral_contexts=["biafra history", "biafra war", "former biafra", "biafra memorial"],
                    biased_contexts=["biafra must go", "biafra terrorists", "illegal biafra", "biafra criminals"]
                )
            },
            
            BiasCategory.RELIGIOUS: {
                "christian": ContextualPattern(
                    term="christian",
                    neutral_contexts=["christian community", "christian faith", "christian church", "christian worship"],
                    biased_contexts=["christian domination", "fake christians", "christian agenda", "evil christians"]
                ),
                "muslim": ContextualPattern(
                    term="muslim",
                    neutral_contexts=["muslim community", "muslim faith", "muslim worship", "islamic prayer"],
                    biased_contexts=["muslim terrorists", "islamic agenda", "muslim domination", "violent muslims"]
                ),
                # Religious slurs - always biased
                "kafir": ContextualPattern(
                    term="kafir",
                    neutral_contexts=[],
                    biased_contexts=["kafir"],
                    requires_context=False
                ),
                "infidel": ContextualPattern(
                    term="infidel",
                    neutral_contexts=[],
                    biased_contexts=["infidel"],
                    requires_context=False
                )
            }
        }
        
        # Enhanced sentiment analysis with Nigerian context
        self.sentiment_indicators = {
            "strong_negative": ["corrupt", "evil", "terrorist", "criminal", "fraud", "useless", "disaster", 
                              "failure", "incompetent", "clueless", "dictator", "killer", "violent", "primitive", 
                              "backward", "illiterate", "lazy", "greedy", "cunning", "fake", "liar", "deceiver"],
            "moderate_negative": ["bad", "poor", "failed", "disappointing", "questionable", "problematic", 
                                "concerning", "divisive", "controversial", "wrong", "terrible"],
            "mild_negative": ["doubtful", "uncertain", "unclear", "confusing", "odd", "strange"],
            "neutral": ["said", "announced", "stated", "reported", "mentioned", "discussed", "explained"],
            "mild_positive": ["okay", "fine", "decent", "reasonable", "acceptable", "fair"],
            "moderate_positive": ["good", "nice", "solid", "reliable", "trustworthy", "capable", "competent"],
            "strong_positive": ["excellent", "amazing", "great", "wonderful", "brilliant", "outstanding", 
                              "exceptional", "perfect", "best", "love", "support"]
        }

    def analyze_text(self, text: str) -> List[BiasDetection]:
        """Main analysis method with comprehensive bias detection"""
        text_lower = text.lower()
        detections = []
        
        # Check each category
        for category, patterns in self.contextual_patterns.items():
            category_detections = self._analyze_category(text_lower, text, category, patterns)
            detections.extend(category_detections)
        
        # Remove duplicates and rank by confidence
        detections = self._deduplicate_and_rank(detections)
        
        return detections

    def _analyze_category(self, text_lower: str, original_text: str, category: BiasCategory, 
                         patterns: Dict[str, ContextualPattern]) -> List[BiasDetection]:
        """Analyze text for a specific bias category"""
        detections = []
        
        for term, pattern in patterns.items():
            if self._term_exists_in_text(text_lower, term):
                detection = self._analyze_term_context(
                    text_lower, original_text, term, pattern, category
                )
                if detection:
                    detections.append(detection)
        
        return detections

    def _term_exists_in_text(self, text: str, term: str) -> bool:
        """Check if term exists with word boundary consideration"""
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(term) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))

    def _analyze_term_context(self, text_lower: str, original_text: str, term: str, 
                            pattern: ContextualPattern, category: BiasCategory) -> Optional[BiasDetection]:
        """Analyze the context around a detected term"""
        
        # For terms that don't require context (slurs), always flag as biased
        if not pattern.requires_context:
            return BiasDetection(
                term=term,
                category=category,
                bias_level=BiasLevel.HIGH,
                confidence=0.95,
                context=self._extract_context(text_lower, term),
                bias_direction="negative",
                explanation=f"Contains derogatory term '{term}' which is inherently biased"
            )
        
        # Check for neutral contexts first
        for neutral_context in pattern.neutral_contexts:
            if neutral_context in text_lower:
                # Even in neutral context, check for bias indicators
                context_window = self._extract_context(text_lower, term, window_size=10)
                bias_score, direction = self._calculate_sentiment_score(context_window, term)
                
                if abs(bias_score) < 0.3:  # Truly neutral
                    return None
                elif abs(bias_score) < 0.6:  # Mild bias in neutral context
                    return BiasDetection(
                        term=term,
                        category=category,
                        bias_level=BiasLevel.LOW,
                        confidence=0.4,
                        context=context_window,
                        bias_direction=direction,
                        explanation=f"Mild bias detected around '{term}' despite neutral context"
                    )
        
        # Check for explicitly biased contexts
        for biased_context in pattern.biased_contexts:
            if biased_context in text_lower:
                return BiasDetection(
                    term=term,
                    category=category,
                    bias_level=BiasLevel.HIGH,
                    confidence=0.9,
                    context=self._extract_context(text_lower, term),
                    bias_direction="negative",
                    explanation=f"Explicitly biased language: '{biased_context}'"
                )
        
        # General context analysis
        context_window = self._extract_context(text_lower, term, window_size=8)
        bias_score, direction = self._calculate_sentiment_score(context_window, term)
        
        if abs(bias_score) >= 0.7:
            return BiasDetection(
                term=term,
                category=category,
                bias_level=BiasLevel.HIGH,
                confidence=min(abs(bias_score), 0.95),
                context=context_window,
                bias_direction=direction,
                explanation=f"Strong {direction} bias detected around '{term}'"
            )
        elif abs(bias_score) >= 0.4:
            return BiasDetection(
                term=term,
                category=category,
                bias_level=BiasLevel.MEDIUM,
                confidence=abs(bias_score),
                context=context_window,
                bias_direction=direction,
                explanation=f"Moderate {direction} bias detected around '{term}'"
            )
        
        return None

    def _extract_context(self, text: str, term: str, window_size: int = 6) -> str:
        """Extract context window around the term"""
        words = text.split()
        term_positions = [i for i, word in enumerate(words) if term in word.lower()]
        
        if not term_positions:
            return ""
        
        # Use the first occurrence for context
        pos = term_positions[0]
        start = max(0, pos - window_size)
        end = min(len(words), pos + window_size + 1)
        
        return " ".join(words[start:end])

    def _calculate_sentiment_score(self, context: str, target_term: str) -> Tuple[float, str]:
        """Calculate sentiment score for the context around target term"""
        words = context.lower().split()
        score = 0.0
        
        # Weight sentiment words by distance from target term
        target_positions = [i for i, word in enumerate(words) if target_term in word]
        
        if not target_positions:
            return 0.0, "neutral"
        
        target_pos = target_positions[0]
        
        for i, word in enumerate(words):
            distance = abs(i - target_pos)
            weight = max(0.1, 1.0 - (distance * 0.15))  # Closer words have higher weight
            
            # Clean word of punctuation
            clean_word = re.sub(r'[^\w]', '', word)
            
            if clean_word in self.sentiment_indicators["strong_negative"]:
                score -= 1.0 * weight
            elif clean_word in self.sentiment_indicators["moderate_negative"]:
                score -= 0.6 * weight
            elif clean_word in self.sentiment_indicators["mild_negative"]:
                score -= 0.3 * weight
            elif clean_word in self.sentiment_indicators["mild_positive"]:
                score += 0.3 * weight
            elif clean_word in self.sentiment_indicators["moderate_positive"]:
                score += 0.6 * weight
            elif clean_word in self.sentiment_indicators["strong_positive"]:
                score += 1.0 * weight
        
        # Normalize by context length
        normalized_score = score / max(len(words), 1)
        
        if normalized_score < -0.1:
            return normalized_score, "negative"
        elif normalized_score > 0.1:
            return normalized_score, "positive"
        else:
            return normalized_score, "neutral"

    def _deduplicate_and_rank(self, detections: List[BiasDetection]) -> List[BiasDetection]:
        """Remove duplicates and rank by confidence"""
        # Remove duplicates based on term and category
        seen = set()
        unique_detections = []
        
        for detection in detections:
            key = (detection.term, detection.category)
            if key not in seen:
                seen.add(key)
                unique_detections.append(detection)
        
        # Sort by confidence (highest first)
        return sorted(unique_detections, key=lambda x: x.confidence, reverse=True)


class EnhancedBiasDetector:
    """Enhanced bias detector with Nigerian context awareness"""
    
    def __init__(self, model_name="martin-ha/toxic-comment-model", threshold=0.5):
        # Load base model
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
        self.nigerian_analyzer = NigerianContextAnalyzer()

    def detect(self, text: str) -> Dict:
        """Main detection method with comprehensive analysis"""
        try:
            # Base model detection
            base_result = self.pipeline(text)[0]
            
            # Handle different model outputs
            if base_result['label'] in ['TOXIC', 'BIASED', '1']:
                base_score = base_result['score']
            else:
                base_score = 1 - base_result['score']
            
            # Nigerian context analysis
            nigerian_detections = self.nigerian_analyzer.analyze_text(text)
            
            # Combine scores intelligently
            final_score, explanation = self._combine_scores(base_score, nigerian_detections)
            
            # Generate comprehensive report
            return {
                "is_biased": final_score >= self.threshold,
                "confidence": final_score,
                "bias_level": self._determine_bias_level(final_score),
                "base_model_score": base_score,
                "nigerian_detections": [
                    {
                        "term": d.term,
                        "category": d.category.value,
                        "bias_level": d.bias_level.value,
                        "confidence": d.confidence,
                        "direction": d.bias_direction,
                        "explanation": d.explanation,
                        "context": d.context
                    }
                    for d in nigerian_detections
                ],
                "explanation": explanation,
                "recommendations": self._generate_recommendations(nigerian_detections)
            }
        
        except Exception as e:
            return {
                "is_biased": False,
                "confidence": 0.0,
                "error": f"Analysis failed: {str(e)}",
                "nigerian_detections": [],
                "explanation": "Technical error occurred during analysis"
            }

    def _combine_scores(self, base_score: float, detections: List[BiasDetection]) -> Tuple[float, str]:
        """Intelligently combine base model score with Nigerian detections"""
        if not detections:
            return base_score, f"Base model analysis (confidence: {base_score:.3f})"
        
        # Calculate enhancement from Nigerian context
        nigerian_boost = 0.0
        high_confidence_detections = []
        
        for detection in detections:
            if detection.confidence >= 0.7:
                high_confidence_detections.append(detection)
                if detection.bias_level == BiasLevel.HIGH:
                    nigerian_boost += 0.3
                elif detection.bias_level == BiasLevel.MEDIUM:
                    nigerian_boost += 0.2
                else:
                    nigerian_boost += 0.1
        
        # Cap the boost
        nigerian_boost = min(nigerian_boost, 0.4)
        
        # Combine scores with weighted average if both are significant
        if base_score >= 0.3 and nigerian_boost >= 0.1:
            # Both models agree on bias
            combined_score = min(base_score + nigerian_boost, 1.0)
            explanation = f"Both base model ({base_score:.3f}) and Nigerian context analysis agree on bias presence"
        elif nigerian_boost >= 0.3:
            # Strong Nigerian context bias, even if base model disagrees
            combined_score = max(base_score, 0.6 + nigerian_boost)
            explanation = f"Strong Nigerian context bias detected despite lower base model score"
        else:
            # Mild enhancement
            combined_score = base_score + (nigerian_boost * 0.5)
            explanation = f"Base model score enhanced by Nigerian context analysis"
        
        return min(combined_score, 1.0), explanation

    def _determine_bias_level(self, score: float) -> str:
        """Determine bias level from score"""
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.4:
            return "low"
        else:
            return "minimal"

    def _generate_recommendations(self, detections: List[BiasDetection]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if not detections:
            return ["Content appears neutral. Consider fact-checking sources for accuracy."]
        
        categories_found = set(d.category for d in detections)
        
        if BiasCategory.POLITICAL in categories_found:
            recommendations.append(
                "Consider presenting multiple political perspectives to provide balanced coverage"
            )
        
        if BiasCategory.ETHNIC in categories_found:
            recommendations.append(
                "Focus on individual actions rather than ethnic generalizations. Avoid stereotyping language."
            )
        
        if BiasCategory.RELIGIOUS in categories_found:
            recommendations.append(
                "Ensure religious discussions remain respectful and acknowledge diverse viewpoints"
            )
        
        if BiasCategory.REGIONAL in categories_found:
            recommendations.append(
                "Avoid regional stereotypes. Focus on specific issues rather than broad geographical generalizations."
            )
        
        # Check for high-confidence detections
        high_confidence = [d for d in detections if d.confidence >= 0.8]
        if high_confidence:
            recommendations.insert(0, 
                "Strong bias indicators detected. Consider revising language to be more neutral and factual."
            )
        
        return recommendations


class EnhancedBiasTypeClassifier:
    """Enhanced bias type classifier with Nigerian context"""
    
    def __init__(self, model_name="facebook/bart-large-mnli"):
        if model_name not in _model_cache:
            _model_cache[model_name] = pipeline("zero-shot-classification", model=model_name)
        self.classifier = _model_cache[model_name]
        self.nigerian_analyzer = NigerianContextAnalyzer()

    def predict(self, text: str) -> Dict:
        """Predict bias type with enhanced Nigerian context awareness"""
        try:
            # Analyze Nigerian context first
            nigerian_detections = self.nigerian_analyzer.analyze_text(text)
            
            if nigerian_detections:
                # Use Nigerian context for primary classification
                primary_detection = nigerian_detections[0]  # Highest confidence
                
                response = {
                    "type": self._format_bias_type(primary_detection),
                    "confidence": round(primary_detection.confidence * 100, 2),
                    "specific_target": primary_detection.term,
                    "bias_category": primary_detection.category.value,
                    "bias_direction": primary_detection.bias_direction,
                    "explanation": primary_detection.explanation,
                    "nigerian_context": True,
                    "all_detections": [
                        {
                            "type": self._format_bias_type(d),
                            "confidence": round(d.confidence * 100, 2),
                            "term": d.term,
                            "direction": d.bias_direction
                        }
                        for d in nigerian_detections[:3]  # Top 3
                    ]
                }
            else:
                # Fall back to general classification
                labels = [
                    "political bias", "ethnic bias", "religious bias", 
                    "gender bias", "social bias", "regional bias", "no bias"
                ]
                
                result = self.classifier(text, labels)
                top_type = result['labels'][0]
                top_confidence = round(result['scores'][0] * 100, 2)
                
                response = {
                    "type": "neutral" if top_type == "no bias" and top_confidence > 70 else top_type,
                    "confidence": top_confidence,
                    "nigerian_context": False,
                    "all_predictions": [
                        {
                            "type": label,
                            "confidence": round(score * 100, 2)
                        }
                        for label, score in zip(result['labels'][:3], result['scores'][:3])
                    ]
                }
            
            return response
        
        except Exception as e:
            return {
                "type": "analysis_error",
                "confidence": 0,
                "error": str(e),
                "nigerian_context": False,
                "all_predictions": []
            }

    def _format_bias_type(self, detection: BiasDetection) -> str:
        """Format bias type for display"""
        direction = detection.bias_direction.capitalize()
        category = detection.category.value.capitalize()
        term = detection.term.capitalize()
        
        if detection.bias_direction == "neutral":
            return f"{category} bias (regarding {term})"
        else:
            return f"{direction} {category} bias (targeting {term})"


# Clickbait detector as bonus feature
class ClickbaitDetector:
    """Detect clickbait patterns in Nigerian context"""
    
    def __init__(self):
        self.clickbait_patterns = [
            # Universal patterns
            r'\b(shocking|unbelievable|you won\'t believe|must see|amazing|incredible)\b',
            r'\b(breaking|urgent|just in|developing|alert)\b',
            r'\b(\d+\s+(reasons|ways|things|secrets|facts|tricks))\b',
            r'\b(this will|what happens next|the result will|you\'ll never guess)\b',
            r'\b(doctors hate|banks don\'t want|government hiding)\b',
            
            # Nigerian-specific clickbait
            r'\b(buhari finally|tinubu shock|obi reveals|atiku exposes)\b',
            r'\b(lagos residents|abuja people|kano citizens)\s+(shocked|surprised|amazed)\b',
            r'\b(see what|look what|check what)\s+(happened|occurs|occurs)\b',
            r'\b(nigerian|naija)\s+(secret|mystery|revelation)\b',
            r'\b(this nigerian|this naija)\s+(will|did|has)\b',
        ]
        
        self.clickbait_indicators = {
            "excessive_caps": r'[A-Z]{5,}',
            "excessive_punctuation": r'[!?]{2,}',
            "number_lists": r'\b\d+\s+(things|reasons|ways|secrets)\b',
            "superlatives": r'\b(best|worst|most|least|ultimate|perfect)\b',
            "urgency": r'\b(now|today|immediately|urgent|breaking|just in)\b'
        }

    def detect(self, text: str) -> Dict:
        """Detect clickbait patterns"""
        clickbait_score = 0.0
        detected_patterns = []
        
        text_lower = text.lower()
        
        # Check main patterns
        for pattern in self.clickbait_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                clickbait_score += 0.3
                detected_patterns.extend([m if isinstance(m, str) else ' '.join(m) for m in matches])
        
        # Check additional indicators
        for indicator, pattern in self.clickbait_indicators.items():
            if re.search(pattern, text, re.IGNORECASE):
                clickbait_score += 0.2
                detected_patterns.append(indicator.replace('_', ' '))
        
        # Cap the score
        clickbait_score = min(clickbait_score, 1.0)
        
        return {
            "is_clickbait": clickbait_score >= 0.4,
            "confidence": clickbait_score,
            "level": "high" if clickbait_score >= 0.7 else "medium" if clickbait_score >= 0.4 else "low",
            "detected_patterns": list(set(detected_patterns)),
            "explanation": f"Clickbait confidence: {clickbait_score:.2f} based on detected patterns"
        }


# Main integrated analyzer
class BiasLensAnalyzer:
    """Main analyzer combining all detection capabilities"""
    
    def __init__(self):
        self.bias_detector = EnhancedBiasDetector()
        self.bias_classifier = EnhancedBiasTypeClassifier()
        self.clickbait_detector = ClickbaitDetector()

    def analyze(self, text: str) -> Dict:
        """Comprehensive analysis of text"""
        bias_analysis = self.bias_detector.detect(text)
        type_analysis = self.bias_classifier.predict(text)
        clickbait_analysis = self.clickbait_detector.detect(text)
        
        # Combine into comprehensive report
        return {
            "text": text[:200] + "..." if len(text) > 200 else text,
            "timestamp": "placeholder_timestamp",
            
            # Overall assessment
            "overall_bias": {
                "is_biased": bias_analysis["is_biased"],
                "confidence": bias_analysis["confidence"],
                "level": bias_analysis["bias_level"]
            },
            
            # Detailed bias analysis
            "bias_details": {
                "type": type_analysis["type"],
                "type_confidence": type_analysis["confidence"],
                "nigerian_context": type_analysis.get("nigerian_context", False),
                "specific_detections": bias_analysis.get("nigerian_detections", [])
            },
            
            # Clickbait analysis
            "clickbait": clickbait_analysis,
            
            # Recommendations
            "recommendations": bias_analysis.get("recommendations", []),
            
            # Technical details
            "technical_details": {
                "base_model_score": bias_analysis.get("base_model_score", 0),
                "explanation": bias_analysis.get("explanation", ""),
                "error": bias_analysis.get("error")
            }
        }