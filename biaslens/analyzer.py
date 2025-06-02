from .sentiment import SentimentAnalyzer
from .emotion import EmotionClassifier
from .bias import BiasDetector, BiasTypeClassifier, NigerianBiasEnhancer # Added NigerianBiasEnhancer
from .patterns import NigerianPatterns, FakeNewsDetector, ViralityDetector
from .trust import TrustScoreCalculator
import time
from typing import Dict, Optional
import logging
import random # Added for random tip selection

logger = logging.getLogger(__name__)


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
        self._nigerian_bias_enhancer = NigerianBiasEnhancer() # Added instance

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
            # FIXED: Consistent return structure with all required fields
            return {
                'trust_score': None, 'indicator': 'Error', 'explanation': ["Empty or invalid text provided."],
                'tip': "Analysis failed: No text was provided. Please input text for analysis.",
                'primary_bias_type': None,
                'sentiment_details': None, 'emotion_details': None, 'bias_details': None,
                'pattern_highlights': None, 'lightweight_nigerian_bias_assessment': None
                # Removed metadata
            }

        # Removed timing variables as metadata is removed

        try:
            sentiment_result = self._analyze_sentiment_safe(text, headline)
            emotion_result = self._analyze_emotion_safe(text)
            bias_result = self._analyze_bias_safe(text) 

            pattern_result = {}
            lightweight_nigerian_bias_info = {} 
            if include_patterns:
                pattern_result = self._analyze_patterns_safe(text)
                lightweight_nigerian_bias_info = self._nigerian_bias_enhancer.get_lightweight_bias_assessment(text)
            
            trust_result = self._calculate_trust_score_safe(
                text, sentiment_result, emotion_result, bias_result
            )
            
            # _generate_overall_assessment is called but its main output isn't directly part of final_result
            self._generate_overall_assessment(
                 sentiment_result, emotion_result, bias_result, trust_result
            )

            primary_bias_type_value = None
            if bias_result.get('flag', False): 
                bias_type_info_ml = bias_result.get('type_analysis', {})
                detected_type_ml = bias_type_info_ml.get('type')
                if detected_type_ml and isinstance(detected_type_ml, str) and detected_type_ml.strip():
                    detected_type_ml_lower = detected_type_ml.strip().lower()
                    if detected_type_ml_lower not in ['neutral', 'no bias', 'analysis_error', '']:
                        primary_bias_type_value = detected_type_ml_lower
                    elif detected_type_ml_lower in ['neutral', 'no bias']:
                         primary_bias_type_value = "neutral"
            
            if primary_bias_type_value is None or primary_bias_type_value == "neutral": 
                lw_bias_type = lightweight_nigerian_bias_info.get("inferred_bias_type")
                if lw_bias_type and lw_bias_type not in ["No specific patterns detected", "Nigerian context detected, specific bias type unclear from patterns"]:
                    primary_bias_type_value = lw_bias_type
            
            sentiment_details = {
                'label': sentiment_result.get('label'),
                'confidence': sentiment_result.get('confidence')
            }
            emotion_details = {
                'label': emotion_result.get('label'),
                'confidence': emotion_result.get('confidence'),
                'is_emotionally_charged': emotion_result.get('is_emotionally_charged', False),
                'manipulation_risk': emotion_result.get('manipulation_risk')
            }
            bias_details_payload = { 
                'detected': bias_result.get('flag', False),
                'label': bias_result.get('label'), 
                'confidence': bias_result.get('type_analysis', {}).get('confidence')
            }

            np_data = pattern_result.get('nigerian_patterns', {}) if isinstance(pattern_result.get('nigerian_patterns'), dict) else {}
            fn_data = pattern_result.get('fake_news', {}) if isinstance(pattern_result.get('fake_news'), dict) else {}
            vm_data = pattern_result.get('viral_manipulation', {}) if isinstance(pattern_result.get('viral_manipulation'), dict) else {}
            
            fn_details = fn_data.get('details', {}) if isinstance(fn_data.get('details'), dict) else {}

            pattern_highlights = {
                'nigerian_context_detected': bool(lightweight_nigerian_bias_info.get('matched_keywords')) or \
                                           np_data.get('has_triggers', False),
                'clickbait_detected': np_data.get('has_clickbait', False) or \
                                    fn_details.get('is_clickbait', False) or \
                                    vm_data.get('is_potentially_viral', False),
                'fake_news_risk': fn_details.get('risk_level')
            }

            final_result = {
                'trust_score': trust_result.get('score'),
                'indicator': trust_result.get('indicator'),
                'explanation': trust_result.get('explanation'),
                'tip': trust_result.get('tip'), 
                'primary_bias_type': primary_bias_type_value,
                'sentiment_details': sentiment_details,
                'emotion_details': emotion_details,
                'bias_details': bias_details_payload,
                'pattern_highlights': pattern_highlights,
                'lightweight_nigerian_bias_assessment': lightweight_nigerian_bias_info if include_patterns and lightweight_nigerian_bias_info else None,
            }
            
            if include_detailed_results:
                final_result['detailed_sub_analyses'] = {
                    'sentiment': sentiment_result, 
                    'emotion': emotion_result,     
                    'bias': bias_result,           
                }
                if include_patterns:
                    final_result['detailed_sub_analyses']['patterns'] = pattern_result 
                    if lightweight_nigerian_bias_info:
                        final_result['detailed_sub_analyses']['lightweight_nigerian_bias'] = lightweight_nigerian_bias_info
            
            return final_result

        except Exception as e:
            logger.error(f"Analysis failed due to an unexpected error: {str(e)}", exc_info=True)
            return {
                'trust_score': None, 'indicator': 'Error', 
                'explanation': [f"An error occurred during analysis: {str(e)}"],
                'tip': "Analysis failed due to an unexpected error. Please try again later or contact support.",
                'primary_bias_type': None,
                'sentiment_details': None, 'emotion_details': None, 'bias_details': None,
                'pattern_highlights': None, 'lightweight_nigerian_bias_assessment': None,
                # No 'metadata' field here
            }

    def quick_analyze(self, text: str) -> Dict:
        """
        Lightweight analysis for quick checks (sentiment + basic patterns + lightweight bias).
        Useful for real-time analysis or high-volume processing.
        """

        if not text or not text.strip():
            return {
                'score': None,
                'indicator': 'Error',
                'explanation': "Empty text provided.",
                'tip': "No text was provided. Please input text for analysis. For a detailed breakdown of potential biases and manipulation, use the full analyze() function once text is provided.",
                'inferred_bias_type': None,
                'bias_category': None,
                'bias_target': None,
                'matched_keywords': []
            }

        try:
            # Quick sentiment analysis
            sentiment_result = self._analyze_sentiment_safe(text)

            # Basic pattern analysis (no ML models)
            nigerian_patterns = NigerianPatterns.analyze_patterns(text) # This is existing
            fake_detected, fake_details = FakeNewsDetector.detect(text) # This is existing

            # New Lightweight Nigerian Bias Assessment
            lightweight_bias_info = self._nigerian_bias_enhancer.get_lightweight_bias_assessment(text)

            # Simple trust score based on available data
            basic_trust_score_results = self._calculate_basic_trust_score(
                sentiment_result, nigerian_patterns, fake_detected, fake_details
            )

            # Update explanation with lightweight bias info
            updated_explanation = basic_trust_score_results.get('explanation', "Quick check results.")
            if lightweight_bias_info.get("inferred_bias_type") and lightweight_bias_info["inferred_bias_type"] != "No specific patterns detected":
                if not updated_explanation.endswith("."):
                    updated_explanation += "."
                updated_explanation += f" Specific patterns suggest: {lightweight_bias_info['inferred_bias_type']}."
            
            # Construct the results dictionary
            results = {
                'score': basic_trust_score_results.get('score'),
                'indicator': basic_trust_score_results.get('indicator'),
                'explanation': updated_explanation,
                'tip': random.choice(TrustScoreCalculator.DID_YOU_KNOW_TIPS) # MODIFIED
            }
            
            # Add fields from lightweight_bias_info
            results.update(lightweight_bias_info) # This will add all keys from lightweight_bias_info

            return results

        except Exception as e:
            logger.error(f"Quick analysis failed: {str(e)}", exc_info=True)
            return {
                'score': None,
                'indicator': 'Error',
                'explanation': f"An error occurred during quick analysis: {str(e)}",
                'tip': "Quick analysis encountered an issue. For a comprehensive analysis including detailed bias types, emotional language, and a full trust assessment, try the full analyze() function.",
                'inferred_bias_type': None,
                'bias_category': None,
                'bias_target': None,
                'matched_keywords': []
            }

    def analyze_headline_content_mismatch(self, headline: str, content: str) -> Dict:
        """
        Specialized analysis for detecting clickbait through headline-content mismatch.
        """

        try:
            # FIXED: Added input validation
            if not headline or not headline.strip():
                return {
                    'status': 'error',
                    'error': 'Empty headline provided',
                    'mismatch_analysis': None
                }

            if not content or not content.strip():
                return {
                    'status': 'error',
                    'error': 'Empty content provided',
                    'mismatch_analysis': None
                }

            # Analyze both headline and content
            headline_analysis = self.analyze(headline, include_patterns=False)
            content_analysis = self.analyze(content, include_patterns=False)

            # FIXED: Added error checking before sentiment comparison
            if (headline_analysis.get('indicator') == 'Error' or
                    content_analysis.get('indicator') == 'Error'):
                return {
                    'status': 'error',
                    'error': 'Failed to analyze headline or content',
                    'mismatch_analysis': None,
                    'headline_analysis': headline_analysis,
                    'content_analysis': content_analysis
                }

            # Detailed sentiment comparison - with error handling
            try:
                sentiment_comparison = self.sentiment_analyzer.analyze_headline_vs_content(
                    headline, content
                )
            except Exception as e:
                logger.error(f"Sentiment comparison failed: {str(e)}")
                sentiment_comparison = {
                    'is_clickbait_likely': False,
                    'error': f"Sentiment comparison failed: {str(e)}"
                }

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
            logger.error(f"Headline-content mismatch analysis failed: {str(e)}")
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

            # Add headline comparison if provided - with error handling
            if headline and headline.strip():
                try:
                    headline_comparison = self.sentiment_analyzer.analyze_headline_vs_content(
                        headline, text
                    )
                    result['headline_comparison'] = headline_comparison
                except Exception as e:
                    logger.error(f"Headline comparison failed: {str(e)}")
                    result['headline_comparison'] = {
                        'error': f"Headline comparison failed: {str(e)}"
                    }

            return result

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
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
            logger.error(f"Emotion analysis failed: {str(e)}")
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
            logger.error(f"Bias analysis failed: {str(e)}")
            return {
                'flag': False,
                'label': f"Bias analysis failed: {str(e)}",
                'type_analysis': {'type': 'analysis_error', 'confidence': 0},
                'detected': False,
                'error': str(e)
            }

    def _analyze_patterns_safe(self, text: str) -> Dict:
        """Pattern analysis with error handling - IMPROVED"""
        result = {
            'nigerian_patterns': {'has_triggers': False, 'has_clickbait': False},
            'fake_news': {'detected': False, 'details': {}},
            'viral_manipulation': {}
        }

        # Individual pattern analysis with separate error handling
        try:
            result['nigerian_patterns'] = NigerianPatterns.analyze_patterns(text)
        except Exception as e:
            logger.error(f"Nigerian patterns analysis failed: {str(e)}")
            result['nigerian_patterns']['error'] = str(e)

        try:
            fake_detected, fake_details = FakeNewsDetector.detect(text)
            result['fake_news'] = {
                'detected': fake_detected,
                'details': fake_details
            }
        except Exception as e:
            logger.error(f"Fake news detection failed: {str(e)}")
            result['fake_news']['error'] = str(e)

        try:
            result['viral_manipulation'] = ViralityDetector.analyze_virality(text)
        except Exception as e:
            logger.error(f"Virality analysis failed: {str(e)}")
            result['viral_manipulation'] = {'error': str(e)}

        return result

    def _calculate_trust_score_safe(self, text: str, sentiment_result: Dict,
                                    emotion_result: Dict, bias_result: Dict) -> Dict:
        """Trust score calculation with error handling"""
        try:
            # Extract legacy values for backward compatibility
            bias_score = 0.5 if bias_result.get('flag', False) else 0.2

            # FIXED: Added bounds checking and validation
            emotion_confidence = emotion_result.get('confidence', 0)
            if isinstance(emotion_confidence, (int, float)) and emotion_confidence > 0:
                emotion_score = min(emotion_confidence / 100, 1.0) if emotion_result.get('is_emotionally_charged',
                                                                                         False) else 0.3
            else:
                emotion_score = 0.3

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
            logger.error(f"Trust score calculation failed: {str(e)}")
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
        findings = []

        # Sentiment penalties
        if sentiment_result.get('bias_indicator', False): # Assuming bias_indicator from sentiment_analyzer
            score -= 15
            findings.append("potential sentiment bias")
        elif sentiment_result.get('label') == 'negative' and sentiment_result.get('confidence', 0) > 0.7: # Strong negative
            score -=10
            findings.append("strong negative sentiment")


        # Pattern penalties
        if nigerian_patterns.get('has_triggers', False):
            score -= 20
            findings.append("suspicious Nigerian expressions")

        if nigerian_patterns.get('has_clickbait', False):
            score -= 15
            findings.append("clickbait patterns")

        if fake_detected:
            risk_level = fake_details.get('risk_level', 'medium')
            penalty = {'high': 25, 'medium': 15, 'low': 8}.get(risk_level, 10)
            score -= penalty
            findings.append(f"{risk_level} fake news risk")

        score = max(0, min(score, 100))

        explanation_str = "Quick check found: "
        if findings:
            if len(findings) == 1:
                explanation_str += findings[0] + "."
            elif len(findings) == 2:
                explanation_str += findings[0] + " and " + findings[1] + "."
            else: # More than 2
                explanation_str += ", ".join(findings[:-1]) + ", and " + findings[-1] + "."
        else:
            explanation_str = "Quick check found no immediate high-risk patterns."
            if score < 70 : # If score is still low due to very negative sentiment without specific flags
                 explanation_str = "Quick check found strongly negative sentiment that lowered the score."


        return {
            'score': score,
            'indicator': TrustScoreCalculator.get_trust_indicator(score),
            'explanation': explanation_str,
            'mode': 'basic_calculation'
        }

    def _calculate_content_mismatch(self, headline_analysis: Dict, content_analysis: Dict,
                                    sentiment_comparison: Dict) -> Dict:
        """Calculate headline-content mismatch indicators - FIXED"""

        mismatch_indicators = []
        mismatch_score = 0

        # Sentiment mismatch
        if sentiment_comparison.get('is_clickbait_likely', False):
            mismatch_score += 30
            mismatch_indicators.append("Significant sentiment mismatch between headline and content")

        # FIXED: Trust score access - these are direct values, not nested dicts
        headline_trust = headline_analysis.get('trust_score', 50)
        content_trust = content_analysis.get('trust_score', 50)

        # Handle None values
        if headline_trust is None:
            headline_trust = 50
        if content_trust is None:
            content_trust = 50

        trust_difference = abs(headline_trust - content_trust)

        if trust_difference > 30:
            mismatch_score += 20
            mismatch_indicators.append("Large trust score difference between headline and content")

        # FIXED: Emotion intensity mismatch - accessing from detailed_sub_analyses if available
        headline_emotion = {}
        content_emotion = {}

        if 'detailed_sub_analyses' in headline_analysis:
            headline_emotion = headline_analysis['detailed_sub_analyses'].get('emotion', {})
        if 'detailed_sub_analyses' in content_analysis:
            content_emotion = content_analysis['detailed_sub_analyses'].get('emotion', {})

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
        bias_type_detected = None

        if bias_result.get('flag', False):
            bias_type = bias_result.get('type_analysis', {}).get('type', 'unknown')
            if bias_type and bias_type.lower() not in ['neutral', 'no bias', 'unknown', 'analysis_error', '']:
                primary_concerns.append(f"Potential {bias_type.replace('_', ' ').title()} Bias detected.")
                bias_type_detected = bias_type.replace('_', ' ').title()
            elif bias_type == 'unknown':
                primary_concerns.append("Potential Unspecified Bias detected.")
                bias_type_detected = "Unspecified"


        is_emotionally_manipulative = emotion_result.get('manipulation_risk', 'minimal') in ['high', 'medium']
        if is_emotionally_manipulative:
            primary_concerns.append("Uses language that may be emotionally manipulative.")

        if 'clickbait' in str(risk_factors).lower(): # Ensure case-insensitivity
            primary_concerns.append("Shows characteristics of clickbait.")

        if 'fake_risk' in str(risk_factors).lower(): # Ensure case-insensitivity
            primary_concerns.append("Contains elements associated with misinformation.")

        # Consolidate if too many generic concerns, but for now, let's keep them distinct as requested.

        # Generate recommendation
        if trust_score >= 70:
            recommendation = "This content appears generally trustworthy. Always exercise critical thinking by considering the source and looking for supporting evidence on important topics."
        elif trust_score >= 40:
            recommendation = "This content has some concerning patterns. Cross-reference key claims with reputable news outlets or fact-checking websites (e.g., Snopes, PolitiFact, or local equivalents) before accepting them as true. Be mindful of the potential biases or manipulative language identified."
        else:
            recommendation = "This content shows multiple red flags. Be very skeptical of its claims and avoid sharing it until independently verified by trusted sources. Consider the potential intent behind the message and who might benefit from its spread."

        # Generate educational tip based on findings
        educational_tip = trust_result.get('tip', "Always critically evaluate information before accepting or sharing it.") # Default tip

        if bias_type_detected and bias_type_detected != "Unspecified":
            educational_tip = f"Learn more about {bias_type_detected} Bias: Understand its common characteristics and how it can influence perception. Look for signs like selective reporting or emotionally loaded framing related to this bias."
        elif is_emotionally_manipulative:
            educational_tip = "Recognize emotionally manipulative language: Pay attention to words designed to evoke strong emotional responses (e.g., 'outrageous,' 'shocking,' 'miraculous'). Such language can overshadow factual reporting. Question if the emotion is justified by the evidence."
        elif 'clickbait' in str(risk_factors).lower():
            educational_tip = "Identify clickbait: Watch out for sensationalized headlines or teasers that withhold key information to provoke clicks. Compare the headline with the actual content to see if it delivers on its promise."
        elif 'fake_risk' in str(risk_factors).lower():
            educational_tip = "Spotting misinformation: Look for unverifiable claims, anonymous sources, or a lack of credible evidence. Check if other reputable sources are reporting the same information."

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
            'primary_concerns': list(set(primary_concerns)), # Ensure distinct concerns
            'recommendation': recommendation,
            'summary': trust_result.get('summary', ''),
            'educational_tip': educational_tip
        }


# Global instance of the analyzer
_global_analyzer = BiasLensAnalyzer()


# Convenience function for direct usage
def analyze(text: str, include_patterns: bool = True, headline: Optional[str] = None,
            include_detailed_results: bool = False) -> Dict:
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