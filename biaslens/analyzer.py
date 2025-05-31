
from flask import Flask, request, jsonify
from .sentiment import SentimentAnalyzer
from .emotion import EmotionClassifier
from .bias import BiasDetector, BiasTypeClassifier
from .patterns import NigerianPatterns, FakeNewsDetector, ViralityDetector
from .trust import TrustScoreCalculator
import time
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Create Flask app instance
app = Flask(__name__)

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
            logger.info("Initializing SentimentAnalyzer...")
            self._sentiment_analyzer = SentimentAnalyzer()
            self._initialized_components.add('sentiment')
        return self._sentiment_analyzer

    @property
    def emotion_classifier(self):
        """Lazy load emotion classifier"""
        if self._emotion_classifier is None:
            logger.info("Initializing EmotionClassifier...")
            self._emotion_classifier = EmotionClassifier()
            self._initialized_components.add('emotion')
        return self._emotion_classifier

    @property
    def bias_detector(self):
        """Lazy load bias detector"""
        if self._bias_detector is None:
            logger.info("Initializing BiasDetector...")
            self._bias_detector = BiasDetector()
            self._initialized_components.add('bias_detection')
        return self._bias_detector

    @property
    def bias_type_classifier(self):
        """Lazy load bias type classifier"""
        if self._bias_type_classifier is None:
            logger.info("Initializing BiasTypeClassifier...")
            self._bias_type_classifier = BiasTypeClassifier()
            self._initialized_components.add('bias_classification')
        return self._bias_type_classifier

    def analyze(self, text: str, include_patterns: bool = True,
                headline: Optional[str] = None, include_detailed_results: bool = False) -> Dict:
        """
        Comprehensive analysis of text for bias, manipulation, and trustworthiness.

        Args:
            text: The main text to analyze
            include_patterns: Whether to include Nigerian-specific pattern analysis
            headline: Optional headline for headline vs content comparison
            include_detailed_results: If True, includes raw results from sub-analyzers.

        Returns:
            Dict containing all analysis results and overall assessment
        """

        if not text or not text.strip():
            # Even for empty/invalid text, if we need to conform to a structure that might include metadata:
            # However, the original _get_empty_analysis_result doesn't fit the new primary output.
            # For now, let's keep error handling for empty text simple as per previous changes.
            # If metadata is strictly required even for this case, this would need adjustment.
            return {
                'trust_score': None,
                'indicator': 'Error',
                'explanation': ["Empty or invalid text provided"],
                'tip': 'Analysis failed',
                'metadata': {
                    'component_processing_times': {},
                    'overall_processing_time_seconds': 0
                }
            }

        overall_start_time = time.time()
        component_processing_times = {}

        try:
            # Core ML Analysis
            step_start_time = time.time()
            sentiment_result = self._analyze_sentiment_safe(text, headline)
            component_processing_times['sentiment_analysis'] = round(time.time() - step_start_time, 4)

            step_start_time = time.time()
            emotion_result = self._analyze_emotion_safe(text)
            component_processing_times['emotion_analysis'] = round(time.time() - step_start_time, 4)

            step_start_time = time.time()
            bias_result = self._analyze_bias_safe(text)
            component_processing_times['bias_analysis'] = round(time.time() - step_start_time, 4)

            # Pattern Analysis (Nigerian-specific)
            step_start_time = time.time()
            pattern_result = self._analyze_patterns_safe(text) if include_patterns else {}
            component_processing_times['pattern_analysis'] = round(time.time() - step_start_time, 4)

            # Calculate Trust Score
            step_start_time = time.time()
            trust_result = self._calculate_trust_score_safe(
                text, sentiment_result, emotion_result, bias_result
            )
            component_processing_times['trust_score_calculation'] = round(time.time() - step_start_time, 4)

            # Generate Overall Assessment (even if not all parts are in final dict, it's a step)
            step_start_time = time.time()
            overall_assessment = self._generate_overall_assessment(
                sentiment_result, emotion_result, bias_result, trust_result
            )
            component_processing_times['overall_assessment_generation'] = round(time.time() - step_start_time, 4)

            overall_processing_time = round(time.time() - overall_start_time, 4)

            primary_bias_type_value = None # Default
            if bias_result.get('flag'):
                bias_type_info = bias_result.get('type_analysis', {})
                detected_type = bias_type_info.get('type')
                if detected_type and detected_type not in ['neutral', 'no bias', 'analysis_error']:
                    primary_bias_type_value = detected_type
                elif detected_type in ['neutral', 'no bias']:
                    primary_bias_type_value = "neutral"
                # if 'analysis_error' or None, it remains None or its previous default

            final_result = {
                'trust_score': trust_result.get('score'),
                'indicator': trust_result.get('indicator'),
                'explanation': trust_result.get('explanation'),
                'tip': trust_result.get('tip'),
                'primary_bias_type': primary_bias_type_value, # New key
                'metadata': {
                    'component_processing_times': component_processing_times,
                    'overall_processing_time_seconds': overall_processing_time,
                    'text_length': len(text),
                    'initialized_components': list(self._initialized_components),
                    'analysis_timestamp': time.time()
                }
            }

            if include_detailed_results:
                final_result['detailed_sub_analyses'] = {
                    'sentiment': sentiment_result,
                    'emotion': emotion_result,
                    'bias': bias_result
                }
                if include_patterns and pattern_result: # pattern_result might be {}
                    final_result['detailed_sub_analyses']['patterns'] = pattern_result
                elif include_patterns: # if include_patterns is True but pattern_result is empty (e.g. error)
                     final_result['detailed_sub_analyses']['patterns'] = {}

            return final_result

        except Exception as e:
            overall_processing_time = round(time.time() - overall_start_time, 4)
            logger.error(f"Analysis failed due to an unexpected error: {str(e)}", exc_info=True)
            return {
                'trust_score': None,
                'indicator': 'Error',
                'explanation': [f"An error occurred: {str(e)}"],
                'tip': 'Analysis failed',
                'metadata': {
                    'component_processing_times': component_processing_times, # partial times if error occurred mid-way
                    'overall_processing_time_seconds': overall_processing_time,
                    'error_message': str(e)
                }
            }

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
                'score': basic_trust_score.get('score'),
                'indicator': basic_trust_score.get('indicator'),
                'explanation': basic_trust_score.get('explanation'),
                'tip': "For a more comprehensive analysis, use the full analyze function."
            }

        except Exception as e:
            return {
                'score': None,
                'indicator': 'Error',
                'explanation': [f"An error occurred during quick analysis: {str(e)}"],
                'tip': "For a more comprehensive analysis, use the full analyze function."
            }

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


# Global instance of the analyzer
_global_analyzer = BiasLensAnalyzer()


# Convenience function for direct usage
def analyze(text: str, include_patterns: bool = True, headline: Optional[str] = None, include_detailed_results: bool = False) -> Dict:
    """
    Direct analysis function - uses a global analyzer instance to run analysis.

    Args:
        text: Text to analyze
        include_patterns: Whether to include Nigerian pattern analysis
        headline: Optional headline for comparison
        include_detailed_results: If True, includes raw results from sub-analyzers.

    Returns:
        Complete analysis results
    """
    # Uses the global analyzer instance
    return _global_analyzer.analyze(text, include_patterns, headline, include_detailed_results)


# Quick analysis function
def quick_analyze(text: str) -> Dict:
    """
    Quick analysis function for lightweight processing - uses a global analyzer instance.

    Args:
        text: Text to analyze

    Returns:
        Basic analysis results (sentiment + patterns only)
    """
    # Uses the global analyzer instance
    return _global_analyzer.quick_analyze(text)


@app.route("/api/analyze", methods=["POST"])
def handle_analyze():
    print("[Python Flask App] Request received for /api/analyze")
    try:
        data = request.get_json()
        print(f"[Python Flask App /api/analyze] Received text (first 50 chars): {data.get('text', '')[:50]}")
    except Exception as e:
        print(f"[Python Flask App /api/analyze] Error getting JSON: {e}")
        # Still proceed to return error for missing text, or let the original check handle it.
        # The original check is fine.

    data = request.get_json() # This might be redundant if already called in try-except, but safe.
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' in request body"}), 400

    text_to_analyze = data["text"]
    # TODO: Consider making include_patterns, headline, include_detailed_results configurable via API
    # For now, using defaults for the global analyze function:
    # analyze(text: str, include_patterns: bool = True, headline: Optional[str] = None, include_detailed_results: bool = False)
    # result = analyze(text_to_analyze, include_patterns=True, headline=None, include_detailed_results=False) # Commented out for testing
    return jsonify({"message": "Python /api/analyze test successful", "status": "ok", "source": "simplified_python_test"})

@app.route("/api/quick_analyze", methods=["POST"])
def handle_quick_analyze():
    print("[Python Flask App] Request received for /api/quick_analyze")
    try:
        data = request.get_json()
        print(f"[Python Flask App /api/quick_analyze] Received text (first 50 chars): {data.get('text', '')[:50]}")
    except Exception as e:
        print(f"[Python Flask App /api/quick_analyze] Error getting JSON: {e}")

    data = request.get_json() # Redundant if already called, but safe.
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' in request body"}), 400

    # text_to_analyze = data["text"] # Can be commented if not used for static response
    # result = quick_analyze(text_to_analyze) # Commented out for testing
    return jsonify({"message": "Python /api/quick_analyze test successful", "status": "ok", "source": "simplified_python_test"})

# The old if __name__ == "__main__": block is removed as Vercel will use the 'app' object.
# if __name__ == "__main__":
#     import sys
#     import json
#
#     if len(sys.argv) != 3:
#         print("Usage: python analyzer.py <analyze|quick_analyze> <text_to_analyze>", file=sys.stderr)
#         sys.exit(1)
#
#     function_to_call = sys.argv[1]
#     text_input = sys.argv[2]
#
#     result = None
#     if function_to_call == "analyze":
#         result = analyze(text_input)
#     elif function_to_call == "quick_analyze":
#         result = quick_analyze(text_input)
#     else:
#         print(f"Unknown function: {function_to_call}. Choose 'analyze' or 'quick_analyze'.", file=sys.stderr)
#         sys.exit(1)
#
#     print(json.dumps(result))
