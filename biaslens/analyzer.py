
"""
Core Text Analysis Orchestration for BiasLens.

This module provides the `BiasLensAnalyzer` class, which integrates various
sub-modules (sentiment, emotion, bias detection, pattern matching, trust scoring)
to perform comprehensive analysis of text. It offers both detailed and quick
analysis methods.
"""
import time
from typing import Dict, Optional, Any, List, Set

from .sentiment import SentimentAnalyzer
from .emotion import EmotionClassifier
from .bias import BiasDetector, BiasTypeClassifier
from .patterns import NigerianPatterns, FakeNewsDetector, ViralityDetector
from .trust import TrustScoreCalculator
import functools # Added for @functools.wraps


# Decorator and default error factories
def _get_default_sentiment_error_factory() -> Dict[str, Any]:
    """Returns a default error structure for sentiment analysis failures."""
    return {'label': 'neutral', 'confidence': 0.0, 'error': '', 'all_scores': {'negative': 0.33, 'neutral': 0.34, 'positive': 0.33}}

def _get_default_emotion_error_factory() -> Dict[str, Any]:
    """Returns a default error structure for emotion analysis failures."""
    return {'label': 'neutral', 'confidence': 0.0, 'error': '', 'manipulation_risk': 'unknown', 'is_emotionally_charged': False}

def _get_default_bias_error_factory() -> Dict[str, Any]:
    """Returns a default error structure for bias analysis failures."""
    return {'flag': False, 'label': 'analysis_error', 'type_analysis': {'type': 'analysis_error', 'confidence': 0.0}, 'detected': False, 'error': ''}

def _get_default_patterns_error_factory() -> Dict[str, Any]:
    """Returns a default error structure for pattern analysis failures."""
    # Ensure default structure matches what _analyze_patterns_safe would return on success (keys-wise)
    return {
        'error': '',
        'nigerian_patterns': {'has_triggers': False, 'has_clickbait': False, 'trigger_matches':[], 'clickbait_matches':[], 'trigger_score':0,'clickbait_score':0, 'total_flags':0},
        'fake_news': {'detected': False, 'details': {}, 'fake_matches':[], 'credibility_flags':[], 'fake_score':0, 'credibility_score':0, 'risk_level':'minimal', 'total_flags':0},
        'viral_manipulation': {'has_viral_patterns':False, 'viral_matches':[], 'viral_score':0, 'manipulation_level':'minimal'}
    }

def _handle_analysis_errors(default_error_factory_func, component_name: str):
    """
    Decorator to handle exceptions in analysis component calls.
    It uses a factory function to generate a default error dictionary structure.
    """
    def decorator(func_to_wrap):
        @functools.wraps(func_to_wrap)
        def wrapper(analyzer_instance, *args, **kwargs): # 'analyzer_instance' is 'self'
            try:
                return func_to_wrap(analyzer_instance, *args, **kwargs)
            except Exception as e:
                # print(f"Error in {component_name} analysis: {e}") # Optional: for logging
                error_result = default_error_factory_func()
                error_result['error'] = f"{component_name} analysis failed: {str(e)}"
                return error_result
        return wrapper
    return decorator


class BiasLensAnalyzer:
    """
    Main BiasLens analyzer that orchestrates all analysis components.

    This class provides a unified interface for comprehensive text analysis,
    focusing on bias, emotional content, sentiment, and trustworthiness.
    It lazy-loads its components to optimize startup time.

    Attributes:
        _sentiment_analyzer (Optional[SentimentAnalyzer]): Instance for sentiment analysis.
        _emotion_classifier (Optional[EmotionClassifier]): Instance for emotion classification.
        _bias_detector (Optional[BiasDetector]): Instance for bias detection.
        _bias_type_classifier (Optional[BiasTypeClassifier]): Instance for classifying bias types.
        _initialized_components (Set[str]): Tracks which components have been initialized.
    """

    def __init__(self) -> None:
        """
        Initializes the BiasLensAnalyzer with all components set for lazy loading.
        """
        self._sentiment_analyzer: Optional[SentimentAnalyzer] = None
        self._emotion_classifier: Optional[EmotionClassifier] = None
        self._bias_detector: Optional[BiasDetector] = None
        self._bias_type_classifier: Optional[BiasTypeClassifier] = None

        # Track initialization status for performance monitoring and debugging
        self._initialized_components: Set[str] = set()

    @property
    def sentiment_analyzer(self) -> SentimentAnalyzer:
        """
        Lazy loads and returns the SentimentAnalyzer instance.
        """
        if self._sentiment_analyzer is None:
            # Log initialization for monitoring or debugging purposes if needed
            print("[BiasLensAnalyzer] Initializing SentimentAnalyzer...")
            self._sentiment_analyzer = SentimentAnalyzer()
            self._initialized_components.add('sentiment')
        return self._sentiment_analyzer

    @property
    def emotion_classifier(self) -> EmotionClassifier:
        """
        Lazy loads and returns the EmotionClassifier instance.
        """
        if self._emotion_classifier is None:
            print("[BiasLensAnalyzer] Initializing EmotionClassifier...")
            self._emotion_classifier = EmotionClassifier()
            self._initialized_components.add('emotion')
        return self._emotion_classifier

    @property
    def bias_detector(self) -> BiasDetector:
        """
        Lazy loads and returns the BiasDetector instance.
        """
        if self._bias_detector is None:
            print("[BiasLensAnalyzer] Initializing BiasDetector...")
            self._bias_detector = BiasDetector()
            self._initialized_components.add('bias_detection')
        return self._bias_detector

    @property
    def bias_type_classifier(self) -> BiasTypeClassifier:
        """
        Lazy loads and returns the BiasTypeClassifier instance.
        """
        if self._bias_type_classifier is None:
            print("[BiasLensAnalyzer] Initializing BiasTypeClassifier...")
            self._bias_type_classifier = BiasTypeClassifier()
            self._initialized_components.add('bias_classification')
        return self._bias_type_classifier

    def analyze(self, text: str, include_patterns: bool = True,
                headline: Optional[str] = None, verbosity: str = "default") -> Dict[str, Any]:
        """
        Performs a comprehensive analysis of the given text.

        This method integrates sentiment analysis, emotion classification, bias detection,
        pattern matching (optional), and trust score calculation.

        Args:
            text (str): The main text content to analyze.
            include_patterns (bool, optional): Whether to include Nigerian-specific pattern analysis.
                                     Defaults to True.
            headline (Optional[str], optional): An optional headline associated with the text,
                                      used for headline-content consistency checks.
                                      Defaults to None.
            verbosity (str, optional): Controls the detail level of the output dictionary.
                Possible values:
                - "compact": Minimal output with status, trust score, indicator, and summary.
                - "default": Standard output with status, trust score, indicator, explanation,
                             tip, and metadata. (This is the default if verbosity is invalid).
                - "full": Includes all details from "default" plus raw outputs from
                          all sub-analyzers under a 'detailed_analyses' key.
                Defaults to "default".

        Returns:
            Dict[str, Any]: A dictionary containing the analysis results.
            The structure depends on the 'verbosity' level:

            - If verbosity="compact":
                {
                    "status": str,  # "success" or "error"
                    "trust_score": Optional[int],
                    "indicator": str,
                    "summary_assessment": Optional[str] # Summary if success, error message if error
                }
            - If verbosity="default":
                {
                    "status": str,
                    "trust_score": Optional[int],
                    "indicator": str,
                    "explanation": List[str], # Error message(s) if status is "error"
                    "tip": str,
                    "metadata": Dict[str, Any] # Includes error details if status is "error"
                }
            - If verbosity="full":
                {
                    "status": str,
                    "trust_score": Optional[int],
                    "indicator": str,
                    "explanation": List[str],
                    "tip": str,
                    "detailed_analyses": Optional[Dict[str, Dict[str, Any]]], # Present if status="success"
                        # Contains keys like "sentiment", "emotion", "bias", "patterns"
                        # with their respective full analysis outputs.
                    "metadata": Dict[str, Any]
                }

            If an error occurs (either in input validation or during analysis pipeline),
            'status' will be 'error', and other fields will be structured accordingly
            based on the verbosity level, often including error messages in 'summary_assessment'
            or 'explanation' and 'metadata'.
        """
        VALID_VERBOSITY_LEVELS = ["compact", "default", "full"]
        if verbosity not in VALID_VERBOSITY_LEVELS:
            verbosity = "default"

        # Input validation
        if not text or not text.strip():
            error_message = "Empty or invalid text provided for analysis."
            if verbosity == "compact":
                return {"status": "error", "trust_score": None, "indicator": "Error", "summary_assessment": error_message}
            else: # default or full
                return {
                    "status": "error",
                    'trust_score': None,
                    'indicator': 'Error',
                    'explanation': [error_message],
                    'tip': 'Analysis failed due to empty input.',
                    'metadata': {
                        'component_processing_times': {},
                        'overall_processing_time_seconds': 0,
                        'error_message': error_message
                    }
                }

        overall_start_time = time.time()
        component_processing_times: Dict[str, float] = {}

        try:
            # Step 1: Core ML-based Analysis (Sentiment, Emotion, Bias)
            step_start_time = time.time()
            sentiment_result = self._run_sentiment_analysis(text, headline)
            component_processing_times['sentiment_analysis'] = round(time.time() - step_start_time, 4)

            step_start_time = time.time()
            emotion_result = self._run_emotion_classification(text)
            component_processing_times['emotion_analysis'] = round(time.time() - step_start_time, 4)

            step_start_time = time.time()
            bias_result = self._run_bias_analysis(text)
            component_processing_times['bias_analysis'] = round(time.time() - step_start_time, 4)

            # Step 2: Pattern Analysis (e.g., Nigerian-specific, Fake News, Virality)
            # This step is conditional based on `include_patterns`.
            pattern_result: Dict[str, Any] = _get_default_patterns_error_factory() # Initialize with default structure
            step_start_time = time.time()
            if include_patterns:
                pattern_result = self._run_pattern_analysis(text)
            component_processing_times['pattern_analysis'] = round(time.time() - step_start_time, 4)

            # Step 3: Calculate Trust Score
            # This aggregates findings from previous steps.
            step_start_time = time.time()
            trust_result = self._calculate_trust_score_safe(
                text, sentiment_result, emotion_result, bias_result, pattern_result
            )
            component_processing_times['trust_score_calculation'] = round(time.time() - step_start_time, 4)

            # Step 4: Generate Overall Assessment (potentially for future use or internal logging)
            # Although not directly returned in the main keys, this can inform parts of `trust_result`.
            step_start_time = time.time()
            # overall_assessment = self._generate_overall_assessment(
            #     sentiment_result, emotion_result, bias_result, trust_result
            # )
            # component_processing_times['overall_assessment_generation'] = round(time.time() - step_start_time, 4)
            # Currently, trust_result contains the human-readable parts.

            overall_processing_time = round(time.time() - overall_start_time, 4)

            # Construct the final result dictionary based on verbosity

            metadata_dict = {
                'component_processing_times': component_processing_times,
                'overall_processing_time_seconds': overall_processing_time,
                'text_length': len(text),
                'initialized_components': list(self._initialized_components),
                'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            }

            if verbosity == "compact":
                return {
                    "status": "success",
                    "trust_score": trust_result.get('score'),
                    "indicator": trust_result.get('indicator'),
                    "summary_assessment": trust_result.get('summary')
                }
            elif verbosity == "default":
                return {
                    "status": "success",
                    "trust_score": trust_result.get('score'),
                    "indicator": trust_result.get('indicator'),
                    "explanation": trust_result.get('explanation'),
                    "tip": trust_result.get('tip'),
                    "metadata": metadata_dict
                }
            else: # verbosity == "full"
                return {
                    "status": "success",
                    "trust_score": trust_result.get('score'),
                    "indicator": trust_result.get('indicator'),
                    "explanation": trust_result.get('explanation'),
                    "tip": trust_result.get('tip'),
                    "detailed_analyses": {
                        "sentiment": sentiment_result,
                        "emotion": emotion_result,
                        "bias": bias_result,
                        "patterns": pattern_result if include_patterns else "Not performed"
                    },
                    "metadata": metadata_dict
                }

        except Exception as e:
            # Catch any unexpected errors during the analysis pipeline
            overall_processing_time = round(time.time() - overall_start_time, 4)
            error_message = f"A critical error occurred during analysis: {str(e)}"

            if verbosity == "compact":
                return {"status": "error", "trust_score": None, "indicator": "Error", "summary_assessment": error_message}
            else: # default or full
                return {
                    "status": "error",
                    'trust_score': None,
                    'indicator': 'Error',
                    'explanation': [error_message],
                    'tip': 'Analysis failed. Please try again or check the input text.',
                    'metadata': {
                        'component_processing_times': component_processing_times, # May have partial times
                        'overall_processing_time_seconds': overall_processing_time,
                        'error_message': str(e), # Original error for debugging
                        'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
                    }
                }

    def quick_analyze(self, text: str) -> Dict[str, Any]:
        """
        Performs a lightweight analysis for quick checks.

        This method typically includes sentiment analysis and basic pattern matching,
        omitting more computationally intensive ML models for speed. Useful for
        real-time feedback or high-volume processing where a full analysis is not required.

        Args:
            text (str): The text to analyze.

        Returns:
            Dict[str, Any]: A dictionary with basic analysis results, including:
                            - 'score': A simplified trust or risk score.
                            - 'indicator': A textual indicator.
                            - 'explanation': Brief explanation of the score.
                            - 'tip': A relevant tip.
        """
        if not text or not text.strip():
            # Using a dedicated helper for empty results for consistency
            return self._get_empty_analysis_result("Empty or invalid text provided for quick analysis.")

        # Quick analysis focuses on speed, using fewer components.
        try:
            # Perform quick sentiment analysis (using the new decorated method)
            sentiment_result = self._run_sentiment_analysis(text)

            # Perform basic pattern analysis (non-ML based for speed)
            # These are direct calls to static methods, assumed to be lightweight and less prone to external errors
            # than ML model inferences. If they could also fail, they'd need their own error handling or wrapping.
            nigerian_patterns = NigerianPatterns.analyze_patterns(text) # Assumes this is lightweight
            fake_detected, fake_details = FakeNewsDetector.detect(text) # Assumes this is lightweight

            # Calculate a simplified trust score based on the limited data
            basic_trust_score_result = self._calculate_basic_trust_score(
                sentiment_result, nigerian_patterns, fake_detected, fake_details
            )

            return {
                'score': basic_trust_score_result.get('score'),
                'indicator': basic_trust_score_result.get('indicator'),
                'explanation': basic_trust_score_result.get('explanation'),
                'tip': "This is a quick assessment. For a detailed understanding, use the full 'analyze' function.",
                'details': { # Optional: include raw data from quick checks
                    'sentiment': sentiment_result,
                    'nigerian_patterns': nigerian_patterns,
                    'fake_news_detection': {'detected': fake_detected, 'details': fake_details}
                }
            }

        except Exception as e:
            # Handle errors specific to the quick analysis path
            return {
                'score': None,
                'indicator': 'Error',
                'explanation': [f"An error occurred during quick analysis: {str(e)}"],
                'tip': "Quick analysis failed. You might want to try the full 'analyze' function."
            }

    def analyze_headline_content_mismatch(self, headline: str, content: str) -> Dict[str, Any]:
        """
        Specialized analysis to detect clickbait through headline-content mismatch.

        Compares analyses of the headline and the main content to identify discrepancies
        in sentiment, emotional charge, or topic, which can be indicative of clickbait.

        Args:
            headline (str): The headline of the article/text.
            content (str): The main body of the article/text.

        Returns:
            Dict[str, Any]: A dictionary containing:
                            - 'status': 'success' or 'error'.
                            - 'mismatch_analysis': Detailed mismatch indicators and score.
                            - 'headline_analysis': Full analysis of the headline (excluding patterns).
                            - 'content_analysis': Full analysis of the content (excluding patterns).
                            - 'sentiment_comparison': Specific sentiment comparison metrics.
                            - 'error' (str, optional): Error message if status is 'error'.
        """
        if not headline or not headline.strip() or not content or not content.strip():
            return {
                'status': 'error',
                'error': "Headline or content is empty or invalid.",
                'mismatch_analysis': None
            }

        try:
            # Analyze both headline and content, excluding deeper pattern analysis for this specific task
            # to focus on semantic and emotional congruence.
            headline_analysis_full = self.analyze(headline, include_patterns=False)
            content_analysis_full = self.analyze(content, include_patterns=False)

            # Perform detailed sentiment comparison between headline and content
            # This might involve checking if sentiment polarities align or diverge significantly.
            sentiment_comparison_details = self.sentiment_analyzer.analyze_headline_vs_content(
                headline, content
            )

            # Calculate mismatch indicators based on the analyses
            mismatch_assessment = self._calculate_content_mismatch(
                headline_analysis_full, content_analysis_full, sentiment_comparison_details
            )

            return {
                'status': 'success',
                'mismatch_analysis': mismatch_assessment,
                'headline_analysis': headline_analysis_full, # Full analysis for context
                'content_analysis': content_analysis_full,   # Full analysis for context
                'sentiment_comparison': sentiment_comparison_details
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': f"Error during headline-content mismatch analysis: {str(e)}",
                'mismatch_analysis': None
            }

    # === Decorated Analysis Execution Methods ===

    @_handle_analysis_errors(_get_default_sentiment_error_factory, "Sentiment")
    def _run_sentiment_analysis(self, text: str, headline: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs sentiment analysis using the sentiment_analyzer component.
        Error handling is managed by the decorator.
        """
        result = self.sentiment_analyzer.analyze(text)
        if headline: # specific logic for sentiment if headline present
            # This call might also need error handling if it can fail independently,
            # or assume analyze_headline_vs_content is robust.
            # For now, keeping it as is, assuming analyze_headline_vs_content has its own error handling.
            headline_comparison = self.sentiment_analyzer.analyze_headline_vs_content(headline, text)
            result['headline_comparison'] = headline_comparison
        return result

    @_handle_analysis_errors(_get_default_emotion_error_factory, "Emotion")
    def _run_emotion_classification(self, text: str) -> Dict[str, Any]:
        """
        Runs emotion classification using the emotion_classifier component.
        Error handling is managed by the decorator.
        """
        return self.emotion_classifier.classify(text)

    @_handle_analysis_errors(_get_default_bias_error_factory, "Bias")
    def _run_bias_analysis(self, text: str) -> Dict[str, Any]:
        """
        Runs bias detection and type classification.
        Error handling is managed by the decorator.
        """
        bias_flag, bias_label = self.bias_detector.detect(text)
        bias_type_result = self.bias_type_classifier.predict(text)
        return {
            'flag': bias_flag,
            'label': bias_label,
            'type_analysis': bias_type_result,
            'detected': bias_flag
        }

    @_handle_analysis_errors(_get_default_patterns_error_factory, "Patterns")
    def _run_pattern_analysis(self, text: str) -> Dict[str, Any]:
        """
        Runs various pattern detection analyses.
        Error handling is managed by the decorator.
        """
        nigerian_patterns = NigerianPatterns.analyze_patterns(text)
        fake_detected, fake_details = FakeNewsDetector.detect(text)
        viral_analysis = ViralityDetector.analyze_virality(text)
        return {
            'nigerian_patterns': nigerian_patterns,
            'fake_news': {'detected': fake_detected, 'details': fake_details},
            'viral_manipulation': viral_analysis
        }

    # _calculate_trust_score_safe remains as is, its error handling is specific and robust
    def _calculate_trust_score_safe(self, text: str, sentiment_result: Dict[str, Any],
                                    emotion_result: Dict[str, Any], bias_result: Dict[str, Any],
                                    pattern_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wraps trust score calculation with error handling.

        This method aggregates various analysis outputs to compute a holistic trust score.

        Args:
            text (str): The original text (can be used for length or other direct features).
            sentiment_result (Dict[str, Any]): Output from sentiment analysis.
            emotion_result (Dict[str, Any]): Output from emotion analysis.
            bias_result (Dict[str, Any]): Output from bias analysis.
            pattern_result (Dict[str, Any]): Output from pattern analysis.

        Returns:
            Dict[str, Any]: The trust score calculation result or an error dictionary.
                            Result includes 'score', 'indicator', 'explanation', 'tip', etc.
                            Error dict includes 'error'.
        """
        try:
            # Legacy value extraction for compatibility if TrustScoreCalculator expects them.
            # These should ideally be phased out or handled within TrustScoreCalculator.
            bias_score_legacy = 0.5 if bias_result.get('flag', False) else 0.2 # Example: map flag to a numeric score
            emotion_score_legacy = emotion_result.get('confidence', 0.0) if emotion_result.get('is_emotionally_charged', False) else 0.3
            sentiment_label_legacy = sentiment_result.get('label', 'neutral')

            # Call the main TrustScoreCalculator
            score, indicator, explanation, tip, extras = TrustScoreCalculator.calculate(
                bias_score=bias_score_legacy, # Passing legacy value
                emotion_score=emotion_score_legacy, # Passing legacy value
                sentiment_label=sentiment_label_legacy, # Passing legacy value
                text=text,
                # Pass full modern dictionaries for more granular calculation if TrustScoreCalculator supports it
                emotion_data=emotion_result,
                sentiment_data=sentiment_result,
                bias_data=bias_result,
                pattern_data=pattern_result # Pass pattern data as well
            )

            return {
                'score': score,
                'indicator': indicator,
                'explanation': explanation,
                'tip': tip,
                # Additional details from TrustScoreCalculator's 'extras'
                'trust_level': extras.get('trust_level', 'unknown'),
                'risk_factors': extras.get('risk_factors', []),
                'summary': extras.get('summary', ''),
                'pattern_analysis_summary': extras.get('pattern_analysis', {}) # Summary from patterns
            }
        except Exception as e:
            # Fallback for trust score calculation
            return {
                'score': 50, # Default neutral score
                'indicator': "🟡 Caution",
                'explanation': [f"Trust score calculation failed: {str(e)}"],
                'tip': "Unable to calculate trust score due to an error. Please verify content manually.",
                'error': str(e)
            }

    def _calculate_basic_trust_score(self, sentiment_result: Dict[str, Any],
                                     nigerian_patterns: Dict[str, Any],
                                     fake_detected: bool, fake_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates a basic trust score for the `quick_analyze` method.

        This score is based on a simplified set of inputs: sentiment and basic patterns.

        Args:
            sentiment_result (Dict[str, Any]): Result from sentiment analysis.
            nigerian_patterns (Dict[str, Any]): Result from Nigerian pattern analysis.
            fake_detected (bool): Boolean indicating if fake news patterns were detected.
            fake_details (Dict[str, Any]): Details about the fake news detection.

        Returns:
            Dict[str, Any]: A dictionary containing the 'score', 'indicator',
                            'explanation', and 'mode'.
        """
        score = 80  # Start with a relatively high baseline score for quick analysis
        explanation: List[str] = []

        # Penalize based on sentiment indicators (if any defined for bias)
        if sentiment_result.get('bias_indicator', False): # Assuming 'bias_indicator' exists
            score -= 15
            explanation.append("Sentiment analysis suggests potential bias.")

        # Penalize for Nigerian-specific trigger patterns
        if nigerian_patterns.get('has_triggers', False):
            score -= 20
            explanation.append("Contains linguistic patterns sometimes found in Nigerian scam messages.")
        if nigerian_patterns.get('has_clickbait', False):
            score -= 15
            explanation.append("Contains clickbait-like phrases.")

        # Penalize if fake news patterns are detected
        if fake_detected:
            risk_level = fake_details.get('risk_level', 'medium') # e.g., 'low', 'medium', 'high'
            penalty = {'high': 30, 'medium': 20, 'low': 10}.get(risk_level.lower(), 15)
            score -= penalty
            explanation.append(f"Detected patterns associated with {risk_level} risk of misinformation.")

        # Ensure score is within bounds [0, 100]
        score = max(0, min(score, 100))

        if not explanation:
            explanation.append("Basic checks found no immediate strong negative indicators.")

        return {
            'score': score,
            'indicator': TrustScoreCalculator.get_trust_indicator(score), # Reuse indicator logic
            'explanation': explanation,
            'mode': 'basic_calculation' # Indicate that this is a simplified score
        }

    def _calculate_content_mismatch(self, headline_analysis: Dict[str, Any],
                                    content_analysis: Dict[str, Any],
                                    sentiment_comparison: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates indicators of mismatch between headline and content.

        This is used in `analyze_headline_content_mismatch` to detect clickbait.

        Args:
            headline_analysis (Dict[str, Any]): Full analysis result for the headline.
            content_analysis (Dict[str, Any]): Full analysis result for the content.
            sentiment_comparison (Dict[str, Any]): Result from direct sentiment comparison.

        Returns:
            Dict[str, Any]: A dictionary containing mismatch scores, likelihood of clickbait,
                            and specific mismatch indicators.
        """
        mismatch_indicators: List[str] = []
        mismatch_score = 0  # Score from 0-100, higher means more mismatch

        # 1. Sentiment Mismatch (based on direct comparison)
        if sentiment_comparison.get('is_clickbait_likely', False):
            mismatch_score += 30
            mismatch_indicators.append(
                f"Significant sentiment mismatch: Headline '{sentiment_comparison.get('headline_sentiment_label')}' "
                f"vs Content '{sentiment_comparison.get('content_sentiment_label')}'."
            )

        # 2. Trust Score Difference
        # Ensure trust_score and its 'score' key exist, default to a neutral 50 if not.
        headline_trust_val = headline_analysis.get('trust_score', 50) # Direct score if new structure
        content_trust_val = content_analysis.get('trust_score', 50)   # Direct score if new structure

        trust_difference = abs(headline_trust_val - content_trust_val)
        if trust_difference > 30: # Threshold for significant difference
            mismatch_score += 25
            mismatch_indicators.append(
                f"Large trust score difference: Headline ({headline_trust_val}) vs Content ({content_trust_val})."
            )

        # 3. Emotional Charge Mismatch
        # Accessing emotion data from the new 'detailed_analysis' structure
        headline_emotion_data = headline_analysis.get('detailed_analysis', {}).get('emotion', {})
        content_emotion_data = content_analysis.get('detailed_analysis', {}).get('emotion', {})

        headline_is_charged = headline_emotion_data.get('is_emotionally_charged', False)
        content_is_charged = content_emotion_data.get('is_emotionally_charged', False)

        if headline_is_charged and not content_is_charged:
            mismatch_score += 25
            mismatch_indicators.append(
                "Headline is emotionally charged, but the content is relatively neutral."
            )
        elif not headline_is_charged and content_is_charged:
            mismatch_score += 10 # Less of a clickbait indicator, but still a mismatch
            mismatch_indicators.append(
                "Content is emotionally charged, but the headline is neutral."
            )

        # Normalize mismatch_score to be within 0-100
        mismatch_score = max(0, min(mismatch_score, 100))

        # Determine qualitative assessment of mismatch
        if mismatch_score > 65:
            mismatch_level = 'high'
            is_likely_clickbait = True
        elif mismatch_score > 35:
            mismatch_level = 'medium'
            is_likely_clickbait = True # Medium can also be clickbait
        else:
            mismatch_level = 'low'
            is_likely_clickbait = False

        if not mismatch_indicators:
            mismatch_indicators.append("No significant mismatches detected between headline and content.")

        return {
            'mismatch_score': mismatch_score,
            'is_likely_clickbait': is_likely_clickbait,
            'mismatch_level': mismatch_level, # 'low', 'medium', 'high'
            'indicators': mismatch_indicators,
            'trust_score_difference': trust_difference,
            'sentiment_comparison_details': sentiment_comparison # Include the raw comparison
        }

    def _generate_overall_assessment(self, sentiment_result: Dict[str, Any],
                                     emotion_result: Dict[str, Any],
                                     bias_result: Dict[str, Any],
                                     trust_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a human-readable overall assessment based on analysis results.

        Note: Much of this logic is now integrated into `TrustScoreCalculator.calculate`
        and its 'explanation', 'tip', and 'summary' fields. This method can be
        simplified or used to augment those findings if needed.

        Args:
            sentiment_result (Dict[str, Any]): Result from sentiment analysis.
            emotion_result (Dict[str, Any]): Result from emotion analysis.
            bias_result (Dict[str, Any]): Result from bias analysis.
            trust_result (Dict[str, Any]): Result from trust score calculation.

        Returns:
            Dict[str, Any]: A dictionary with 'trust_score', 'risk_level',
                            'primary_concerns', 'recommendation', 'summary',
                            and 'educational_tip'.
        """
        trust_score_val = trust_result.get('score', 50) # Default to neutral if not found
        risk_factors: List[str] = trust_result.get('risk_factors', [])
        primary_concerns: List[str] = []

        # Example: Augmenting primary concerns based on direct analysis results
        # This might be redundant if TrustScoreCalculator already incorporates these.
        if bias_result.get('detected', False):
            bias_type = bias_result.get('type_analysis', {}).get('type', 'unspecified')
            if bias_type not in ['neutral', 'analysis_error', 'unspecified']:
                concern = f"Potential presence of {bias_type.lower()} bias."
                if concern not in primary_concerns and concern not in risk_factors: # Avoid duplicates
                    primary_concerns.append(concern)

        if emotion_result.get('manipulation_risk', 'minimal').lower() in ['high', 'medium']:
            concern = "Text exhibits emotionally manipulative language patterns."
            if concern not in primary_concerns and concern not in risk_factors:
                primary_concerns.append(concern)

        # Combine with risk factors from trust_result, avoiding duplicates
        for factor in risk_factors:
            if factor not in primary_concerns:
                primary_concerns.append(factor)


        # Determine overall risk level and recommendation based on the trust score
        if trust_score_val >= 70:
            risk_level = "Low"
            recommendation = "Content appears generally trustworthy. Standard critical engagement is advised."
        elif trust_score_val >= 40:
            risk_level = "Medium"
            recommendation = "Content shows some indicators of concern. Cross-verify with other sources."
        else:
            risk_level = "High"
            recommendation = "Content exhibits multiple red flags. Approach with significant caution and skepticism."

        return {
            'trust_score': trust_score_val,
            'risk_level': risk_level,
            'primary_concerns': primary_concerns if primary_concerns else ["No major concerns identified by this assessment."],
            'recommendation': recommendation,
            'summary': trust_result.get('summary', "No detailed summary available."), # From TrustScoreCalculator
            'educational_tip': trust_result.get('tip', "Always critically evaluate information.") # From TrustScoreCalculator
        }

    def _get_empty_analysis_result(self, message: str) -> Dict[str, Any]:
        """
        Returns a structured dictionary for cases where input text is empty or invalid.

        Args:
            message (str): A specific message explaining why the analysis could not proceed.

        Returns:
            Dict[str, Any]: A standardized error structure for empty inputs.
        """
        return {
            'trust_score': None, # Or a default low score like 0
            'indicator': 'Error',
            'explanation': [message],
            'tip': 'Provide valid text content for analysis.',
            'metadata': {
                'component_processing_times': {},
                'overall_processing_time_seconds': 0,
                'error_message': message,
                'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            }
            # Removed 'status' and 'overall_assessment' to match 'analyze' output structure better
        }

    def _get_error_analysis_result(self, error_message: str,
                                   component_times: Dict[str, float],
                                   overall_time: float) -> Dict[str, Any]:
        """
        Returns a structured dictionary for critical errors during the analysis pipeline.

        Args:
            error_message (str): The error message captured.
            component_times (Dict[str, float]): Processing times for components that ran before the error.
            overall_time (float): Total processing time until the error.

        Returns:
            Dict[str, Any]: A standardized error structure.
        """
        return {
            'trust_score': None, # Or a default low score
            'indicator': 'Critical Error',
            'explanation': [f"Analysis halted due to a critical error: {error_message}"],
            'tip': 'The analysis could not be completed. Please try again or check the input.',
            'metadata': {
                'component_processing_times': component_times,
                'overall_processing_time_seconds': round(overall_time, 4),
                'error_message': error_message,
                'error_occurred': True, # Explicit flag
                'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            }
        }


# --- Global Analyzer Instance and Convenience Functions ---

# A single, global instance of the BiasLensAnalyzer.
# This is created when the module is first imported.
# It allows users to call `analyze()` and `quick_analyze()` directly
# without needing to instantiate `BiasLensAnalyzer` themselves.
_global_analyzer = BiasLensAnalyzer()


def analyze(text: str, include_patterns: bool = True, headline: Optional[str] = None, verbosity: str = "default") -> Dict[str, Any]:
    """
    Directly analyzes text using a global `BiasLensAnalyzer` instance.

    This convenience function provides easy access to the comprehensive analysis
    capabilities of BiasLens.

    Args:
        text (str): The main text content to analyze.
        include_patterns (bool, optional): Whether to include Nigerian-specific pattern analysis.
                                 Defaults to True.
        headline (Optional[str], optional): An optional headline for headline-content comparison.
                                  Defaults to None.
        verbosity (str, optional): Controls the detail level of the output dictionary.
            Possible values:
            - "compact": Minimal output with status, trust score, indicator, and summary.
            - "default": Standard output with status, trust score, indicator, explanation,
                         tip, and metadata.
            - "full": Includes all details from "default" plus raw outputs from
                      all sub-analyzers under a 'detailed_analyses' key.
            Defaults to "default".

    Returns:
        Dict[str, Any]: A dictionary containing analysis results, structured according to verbosity.
                        Refer to `BiasLensAnalyzer.analyze` for the detailed structure.
    """
    # Delegates the call to the global analyzer instance.
    return _global_analyzer.analyze(text, include_patterns=include_patterns, headline=headline, verbosity=verbosity)


def quick_analyze(text: str) -> Dict[str, Any]:
    """
    Performs a quick, lightweight analysis using a global `BiasLensAnalyzer` instance.

    Ideal for scenarios requiring rapid feedback, focusing on sentiment and basic patterns.

    Args:
        text (str): The text to analyze.

    Returns:
        Dict[str, Any]: A dictionary with basic analysis results.
                        Refer to `BiasLensAnalyzer.quick_analyze` for the structure.
    """
    # Delegates the call to the global analyzer instance.
    return _global_analyzer.quick_analyze(text)