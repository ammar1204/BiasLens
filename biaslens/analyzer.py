
from .sentiment import SentimentAnalyzer
from .emotion import EmotionClassifier
from .bias import BiasDetector, BiasTypeClassifier
from .patterns import NigerianPatterns, FakeNewsDetector, ViralityDetector
from .trust import TrustScoreCalculator
import time
from typing import Dict, Optional


class BiasLensAnalyzer:
    """
    Main BiasLens analyzer that orchestrates all analysis components.
    Provides a unified interface for comprehensive news bias and manipulation detection.
    """

    def __init__(self):
        """Initialize all analysis components with lazy loading"""
        self._sentiment_analyzer = None
        self._emotion_classifier = None
        self._bias_detector = None
        self._bias_type_classifier = None

        # Track initialization status for performance monitoring
        self._initialized_components = set()

    @property
    def sentiment_analyzer(self):
        """Lazy load sentiment analyzer"""
        if self._sentiment_analyzer is None:
            self._sentiment_analyzer = SentimentAnalyzer()
            self._initialized_components.add('sentiment')
        return self._sentiment_analyzer

    @property
    def emotion_classifier(self):
        """Lazy load emotion classifier"""
        if self._emotion_classifier is None:
            self._emotion_classifier = EmotionClassifier()
            self._initialized_components.add('emotion')
        return self._emotion_classifier

    @property
    def bias_detector(self):
        """Lazy load bias detector"""
        if self._bias_detector is None:
            self._bias_detector = BiasDetector()
            self._initialized_components.add('bias_detection')
        return self._bias_detector

    @property
    def bias_type_classifier(self):
        """Lazy load bias type classifier"""
        if self._bias_type_classifier is None:
            self._bias_type_classifier = BiasTypeClassifier()
            self._initialized_components.add('bias_classification')
        return self._bias_type_classifier

    def analyze(self, text: str, include_patterns: bool = True,
                headline: Optional[str] = None) -> Dict:
        """
        Comprehensive analysis of text for bias, manipulation, and trustworthiness.

        Args:
            text: The main text to analyze
            include_patterns: Whether to include Nigerian-specific pattern analysis
            headline: Optional headline for headline vs content comparison

        Returns:
            Dict containing all analysis results and overall assessment
        """

        if not text or not text.strip():
            return self._get_empty_analysis_result("Empty or invalid text provided")

        start_time = time.time()

        try:
            # Core ML Analysis
            sentiment_result = self._analyze_sentiment_safe(text, headline)
            emotion_result = self._analyze_emotion_safe(text)
            bias_result = self._analyze_bias_safe(text)

            # Pattern Analysis (Nigerian-specific)
            pattern_result = self._analyze_patterns_safe(text) if include_patterns else {}

            # Calculate Trust Score
            trust_result = self._calculate_trust_score_safe(
                text, sentiment_result, emotion_result, bias_result
            )

            # Generate Overall Assessment
            overall_assessment = self._generate_overall_assessment(
                sentiment_result, emotion_result, bias_result, trust_result
            )

            # Performance metrics
            processing_time = round(time.time() - start_time, 3)

            return {
                'status': 'success',
                'overall_assessment': overall_assessment,
                'trust_score': trust_result,
                'analysis': {
                    'sentiment': sentiment_result,
                    'emotion': emotion_result,
                    'bias': bias_result,
                    'patterns': pattern_result
                },
                'metadata': {
                    'processing_time_seconds': processing_time,
                    'text_length': len(text),
                    'initialized_components': list(self._initialized_components),
                    'analysis_timestamp': time.time()
                }
            }

        except Exception as e:
            return self._get_error_analysis_result(str(e), time.time() - start_time)

    def quick_analyze(self, text: str) -> Dict:
        """
        Lightweight analysis for quick checks (sentiment + basic patterns only).
        Useful for real-time analysis or high-volume processing.
        """

        if not text or not text.strip():
            return self._get_empty_analysis_result("Empty text")

        start_time = time.time()

        try:
            # Quick sentiment analysis
            sentiment_result = self._analyze_sentiment_safe(text)

            # Basic pattern analysis (no ML models)
            nigerian_patterns = NigerianPatterns.analyze_patterns(text)
            fake_detected, fake_details = FakeNewsDetector.detect(text)

            # Simple trust score based on available data
            basic_trust_score = self._calculate_basic_trust_score(
                sentiment_result, nigerian_patterns, fake_detected, fake_details
            )

            return {
                'status': 'success',
                'mode': 'quick_analysis',
                'trust_score': basic_trust_score,
                'sentiment': sentiment_result,
                'patterns': {
                    'nigerian_patterns': nigerian_patterns,
                    'fake_news_risk': fake_details if fake_detected else None
                },
                'metadata': {
                    'processing_time_seconds': round(time.time() - start_time, 3),
                    'text_length': len(text)
                }
            }

        except Exception as e:
            return self._get_error_analysis_result(str(e), time.time() - start_time)

    def analyze_headline_content_mismatch(self, headline: str, content: str) -> Dict:
        """
        Specialized analysis for detecting clickbait through headline-content mismatch.
        """

        try:
            # Analyze both headline and content
            headline_analysis = self.analyze(headline, include_patterns=False)
            content_analysis = self.analyze(content, include_patterns=False)

            # Detailed sentiment comparison
            sentiment_comparison = self.sentiment_analyzer.analyze_headline_vs_content(
                headline, content
            )

            # Calculate mismatch indicators
            mismatch_analysis = self._calculate_content_mismatch(
                headline_analysis, content_analysis, sentiment_comparison
            )

            return {
                'status': 'success',
                'mismatch_analysis': mismatch_analysis,
                'headline_analysis': headline_analysis,
                'content_analysis': content_analysis,
                'sentiment_comparison': sentiment_comparison
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'mismatch_analysis': None
            }

    # === SAFE ANALYSIS METHODS (with error handling) ===

    def _analyze_sentiment_safe(self, text: str, headline: Optional[str] = None) -> Dict:
        """Sentiment analysis with error handling"""
        try:
            result = self.sentiment_analyzer.analyze(text)

            # Add headline comparison if provided
            if headline:
                headline_comparison = self.sentiment_analyzer.analyze_headline_vs_content(
                    headline, text
                )
                result['headline_comparison'] = headline_comparison

            return result

        except Exception as e:
            return {
                'label': 'neutral',
                'confidence': 0.0,
                'error': f"Sentiment analysis failed: {str(e)}",
                'all_scores': {'negative': 0.33, 'neutral': 0.34, 'positive': 0.33}
            }

    def _analyze_emotion_safe(self, text: str) -> Dict:
        """Emotion analysis with error handling"""
        try:
            return self.emotion_classifier.classify(text)
        except Exception as e:
            return {
                'label': 'neutral',
                'confidence': 0.0,
                'error': f"Emotion analysis failed: {str(e)}",
                'manipulation_risk': 'unknown',
                'is_emotionally_charged': False
            }

    def _analyze_bias_safe(self, text: str) -> Dict:
        """Bias analysis with error handling"""
        try:
            # Bias detection
            bias_flag, bias_label = self.bias_detector.detect(text)

            # Bias type classification
            bias_type_result = self.bias_type_classifier.predict(text)

            return {
                'flag': bias_flag,
                'label': bias_label,
                'type_analysis': bias_type_result,
                'detected': bias_flag
            }

        except Exception as e:
            return {
                'flag': False,
                'label': f"Bias analysis failed: {str(e)}",
                'type_analysis': {'type': 'analysis_error', 'confidence': 0},
                'detected': False,
                'error': str(e)
            }

    def _analyze_patterns_safe(self, text: str) -> Dict:
        """Pattern analysis with error handling"""
        try:
            nigerian_patterns = NigerianPatterns.analyze_patterns(text)
            fake_detected, fake_details = FakeNewsDetector.detect(text)
            viral_analysis = ViralityDetector.analyze_virality(text)

            return {
                'nigerian_patterns': nigerian_patterns,
                'fake_news': {
                    'detected': fake_detected,
                    'details': fake_details
                },
                'viral_manipulation': viral_analysis
            }

        except Exception as e:
            return {
                'error': f"Pattern analysis failed: {str(e)}",
                'nigerian_patterns': {'has_triggers': False, 'has_clickbait': False},
                'fake_news': {'detected': False}
            }

    def _calculate_trust_score_safe(self, text: str, sentiment_result: Dict,
                                    emotion_result: Dict, bias_result: Dict) -> Dict:
        """Trust score calculation with error handling"""
        try:
            # Extract legacy values for backward compatibility
            bias_score = 0.5 if bias_result.get('flag', False) else 0.2
            emotion_score = emotion_result.get('confidence', 0) / 100 if emotion_result.get('is_emotionally_charged',
                                                                                            False) else 0.3
            sentiment_label = sentiment_result.get('label', 'neutral')

            # Calculate comprehensive trust score
            score, indicator, explanation, tip, extras = TrustScoreCalculator.calculate(
                bias_score=bias_score,
                emotion_score=emotion_score,
                sentiment_label=sentiment_label,
                text=text,
                emotion_data=emotion_result,
                sentiment_data=sentiment_result,
                bias_data=bias_result
            )

            return {
                'score': score,
                'indicator': indicator,
                'explanation': explanation,
                'tip': tip,
                'trust_level': extras.get('trust_level', 'unknown'),
                'risk_factors': extras.get('risk_factors', []),
                'summary': extras.get('summary', ''),
                'pattern_analysis': extras.get('pattern_analysis', {})
            }

        except Exception as e:
            return {
                'score': 50,
                'indicator': "🟡 Caution",
                'explanation': [f"Trust calculation failed: {str(e)}"],
                'tip': "Unable to calculate trust score - verify this content manually.",
                'error': str(e)
            }

    def _calculate_basic_trust_score(self, sentiment_result: Dict, nigerian_patterns: Dict,
                                     fake_detected: bool, fake_details: Dict) -> Dict:
        """Calculate basic trust score for quick analysis"""
        score = 80  # Start with neutral trust
        explanation = []

        # Sentiment penalties
        if sentiment_result.get('bias_indicator', False):
            score -= 15
            explanation.append("Sentiment indicates potential bias")

        # Pattern penalties
        if nigerian_patterns.get('has_triggers', False):
            score -= 20
            explanation.append("Contains suspicious Nigerian expressions")

        if nigerian_patterns.get('has_clickbait', False):
            score -= 15
            explanation.append("Contains clickbait patterns")

        if fake_detected:
            risk_level = fake_details.get('risk_level', 'medium')
            penalty = {'high': 25, 'medium': 15, 'low': 8}.get(risk_level, 10)
            score -= penalty
            explanation.append(f"Fake news risk detected ({risk_level})")

        score = max(0, min(score, 100))

        return {
            'score': score,
            'indicator': TrustScoreCalculator.get_trust_indicator(score),
            'explanation': explanation,
            'mode': 'basic_calculation'
        }

    def _calculate_content_mismatch(self, headline_analysis: Dict, content_analysis: Dict,
                                    sentiment_comparison: Dict) -> Dict:
        """Calculate headline-content mismatch indicators"""

        mismatch_indicators = []
        mismatch_score = 0

        # Sentiment mismatch
        if sentiment_comparison.get('is_clickbait_likely', False):
            mismatch_score += 30
            mismatch_indicators.append("Significant sentiment mismatch between headline and content")

        # Trust score difference
        headline_trust = headline_analysis.get('trust_score', {}).get('score', 50)
        content_trust = content_analysis.get('trust_score', {}).get('score', 50)
        trust_difference = abs(headline_trust - content_trust)

        if trust_difference > 30:
            mismatch_score += 20
            mismatch_indicators.append("Large trust score difference between headline and content")

        # Emotion intensity mismatch
        headline_emotion = headline_analysis.get('analysis', {}).get('emotion', {})
        content_emotion = content_analysis.get('analysis', {}).get('emotion', {})

        if (headline_emotion.get('is_emotionally_charged', False) and
                not content_emotion.get('is_emotionally_charged', False)):
            mismatch_score += 25
            mismatch_indicators.append("Headline is emotionally charged but content is neutral")

        return {
            'mismatch_score': min(mismatch_score, 100),
            'is_likely_clickbait': mismatch_score > 40,
            'mismatch_level': 'high' if mismatch_score > 60 else 'medium' if mismatch_score > 30 else 'low',
            'indicators': mismatch_indicators,
            'trust_score_difference': trust_difference,
            'sentiment_comparison': sentiment_comparison
        }

    def _generate_overall_assessment(self, sentiment_result: Dict, emotion_result: Dict,
                                     bias_result: Dict, trust_result: Dict) -> Dict:
        """Generate human-readable overall assessment"""

        trust_score = trust_result.get('score', 50)
        risk_factors = trust_result.get('risk_factors', [])

        # Determine primary concerns
        primary_concerns = []

        if bias_result.get('flag', False):
            bias_type = bias_result.get('type_analysis', {}).get('type', 'unknown')
            if bias_type != 'neutral':
                primary_concerns.append(f"Contains {bias_type} bias")

        if emotion_result.get('manipulation_risk', 'minimal') in ['high', 'medium']:
            primary_concerns.append("Uses emotionally manipulative language")

        if 'clickbait' in risk_factors:
            primary_concerns.append("Contains clickbait patterns")

        if 'fake_risk' in str(risk_factors):
            primary_concerns.append("Shows signs of misinformation")

        # Generate recommendation
        if trust_score >= 70:
            recommendation = "This content appears generally trustworthy. Exercise normal critical thinking."
        elif trust_score >= 40:
            recommendation = "This content has some concerning patterns. Verify from additional sources."
        else:
            recommendation = "This content shows multiple red flags. Approach with significant caution."

        # Risk level
        if trust_score >= 70:
            risk_level = "low"
        elif trust_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "high"

        return {
            'trust_score': trust_score,
            'risk_level': risk_level,
            'primary_concerns': primary_concerns,
            'recommendation': recommendation,
            'summary': trust_result.get('summary', ''),
            'educational_tip': trust_result.get('tip', '')
        }

    def _get_empty_analysis_result(self, message: str) -> Dict:
        """Return structured result for empty/invalid input"""
        return {
            'status': 'error',
            'error': message,
            'overall_assessment': {
                'trust_score': 0,
                'risk_level': 'unknown',
                'recommendation': 'No text provided for analysis'
            }
        }

    def _get_error_analysis_result(self, error_message: str, processing_time: float) -> Dict:
        """Return structured result for analysis errors"""
        return {
            'status': 'error',
            'error': error_message,
            'overall_assessment': {
                'trust_score': 0,
                'risk_level': 'unknown',
                'recommendation': 'Analysis failed - verify content manually'
            },
            'metadata': {
                'processing_time_seconds': round(processing_time, 3),
                'error_occurred': True
            }
        }


# Convenience function for direct usage
def analyze(text: str, include_patterns: bool = True, headline: Optional[str] = None) -> Dict:
    """
    Direct analysis function - creates analyzer instance and runs analysis.

    Args:
        text: Text to analyze
        include_patterns: Whether to include Nigerian pattern analysis
        headline: Optional headline for comparison

    Returns:
        Complete analysis results
    """
    analyzer = BiasLensAnalyzer()
    return analyzer.analyze(text, include_patterns, headline)


# Quick analysis function
def quick_analyze(text: str) -> Dict:
    """
    Quick analysis function for lightweight processing.

    Args:
        text: Text to analyze

    Returns:
        Basic analysis results (sentiment + patterns only)
    """
    analyzer = BiasLensAnalyzer()
    return analyzer.quick_analyze(text)