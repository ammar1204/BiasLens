import unittest
from unittest.mock import patch, MagicMock
from biaslens.analyzer import BiasLensAnalyzer, analyze, quick_analyze

class TestBiasLensAnalyzer(unittest.TestCase):

    def setUp(self):
        # This setup will be used if we test BiasLensAnalyzer instances directly
        # For now, we are testing the module-level convenience functions primarily
        # self.analyzer_instance = BiasLensAnalyzer()
        pass

    def test_quick_analyze_empty_text(self):
        """Test quick_analyze with empty string input."""
        # The quick_analyze method in BiasLensAnalyzer uses _get_empty_analysis_result
        # which has a different structure than the main analyze method's empty result.
        results = quick_analyze("")
        self.assertIsNotNone(results, "Results should not be None for empty input.")
        self.assertIsNone(results.get('score'))
        self.assertEqual(results.get('indicator'), 'Error')
        self.assertEqual(results.get('explanation'), "Empty text provided.")
        self.assertEqual(results.get('tip'), "No text was provided. Please input text for analysis. For a detailed breakdown of potential biases and manipulation, use the full analyze() function once text is provided.")

    def test_analyze_empty_text(self):
        """Test analyze with empty string input."""
        analysis = analyze("")
        self.assertIsNotNone(analysis, "Analysis should not be None for empty input.")
        self.assertIn('trust_score', analysis, "Result should contain 'trust_score'.")
        self.assertIsNone(analysis['trust_score'], "Trust score should be None for empty input.")
        self.assertIn('indicator', analysis, "Result should contain 'indicator'.")
        self.assertEqual(analysis['indicator'], 'Error', "Indicator should be 'Error'.")
        self.assertIn('explanation', analysis, "Result should contain 'explanation'.")
        self.assertEqual(analysis['explanation'], ["Empty or invalid text provided"], "Explanation for empty input is incorrect.")
        self.assertIn('metadata', analysis, "Result should contain 'metadata'.")
        self.assertIn('overall_processing_time_seconds', analysis['metadata'], "Metadata should have overall processing time.")

    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
    @patch('biaslens.analyzer.NigerianPatterns.analyze_patterns')
    @patch('biaslens.analyzer.FakeNewsDetector.detect')
    def test_quick_analyze_valid_text_structure(self,
                                               mock_fake_news_detect,
                                               mock_nigerian_patterns,
                                               mock_sentiment_safe):
        """Test the basic structure of quick_analyze output with valid text, mocking sub-components."""
        # Common mock setups
        default_sentiment = {'label': 'neutral', 'confidence': 0.9, 'all_scores': {}, 'bias_indicator': False}
        default_nigerian_patterns = {'has_triggers': False, 'has_clickbait': False, 'trigger_score':0, 'clickbait_score':0, 'total_flags':0}
        default_fake_news_detect = (False, {'fake_matches':[], 'credibility_flags':[], 'fake_score':0, 'credibility_score':0, 'risk_level':'minimal', 'total_flags':0})

        # Scenario 1: No specific flagged patterns
        mock_sentiment_safe.return_value = default_sentiment
        mock_nigerian_patterns.return_value = default_nigerian_patterns
        mock_fake_news_detect.return_value = default_fake_news_detect
        results = quick_analyze("This is a test sentence.")
        self.assertIsNotNone(results)
        self.assertIn('score', results)
        self.assertIn('indicator', results)
        self.assertIn('explanation', results)
        self.assertIsInstance(results['explanation'], str)
        self.assertEqual(results['explanation'], "Quick check found no immediate high-risk patterns.")
        self.assertIn('tip', results)
        self.assertEqual(results['tip'], "This is a basic check. For a deeper analysis of bias types, emotional manipulation, and overall trust score, use the full analyze() function.")

        # Scenario 2: Only sentiment bias
        mock_sentiment_safe.return_value = {'label': 'negative', 'confidence': 0.9, 'all_scores': {}, 'bias_indicator': True}
        mock_nigerian_patterns.return_value = default_nigerian_patterns
        mock_fake_news_detect.return_value = default_fake_news_detect
        results = quick_analyze("This is a biased test sentence.")
        self.assertEqual(results['explanation'], "Quick check found: potential sentiment bias.")

        # Scenario 3: Only clickbait patterns
        mock_sentiment_safe.return_value = default_sentiment
        mock_nigerian_patterns.return_value = {'has_triggers': False, 'has_clickbait': True, 'trigger_score':0, 'clickbait_score':5, 'total_flags':1}
        mock_fake_news_detect.return_value = default_fake_news_detect
        results = quick_analyze("This is clickbait.")
        self.assertEqual(results['explanation'], "Quick check found: clickbait patterns.")

        # Scenario 4: Both sentiment bias and clickbait patterns
        mock_sentiment_safe.return_value = {'label': 'negative', 'confidence': 0.9, 'all_scores': {}, 'bias_indicator': True}
        mock_nigerian_patterns.return_value = {'has_triggers': False, 'has_clickbait': True, 'trigger_score':0, 'clickbait_score':5, 'total_flags':1}
        mock_fake_news_detect.return_value = default_fake_news_detect
        results = quick_analyze("This is biased clickbait.")
        self.assertEqual(results['explanation'], "Quick check found: potential sentiment bias and clickbait patterns.")

        # Scenario 5: Strongly negative sentiment but no specific "bias_indicator" flag, score still low
        # This tests the "Quick check found strongly negative sentiment." path
        # For this, we need to ensure bias_indicator is False, but the score calculation logic in _calculate_basic_trust_score
        # doesn't directly use sentiment score for penalty unless bias_indicator is true.
        # So, we'll rely on the default "no immediate high-risk patterns" if only sentiment is negative without the flag.
        # The logic `if score < 70 : explanation_str = "Quick check found strongly negative sentiment."`
        # might be tricky to hit precisely without also triggering other flags or knowing exact score impact of sentiment.
        # Let's assume for now that if no flags are present, it's "no immediate high-risk patterns".
        # If a specific test for "strongly negative sentiment" explanation is needed, _calculate_basic_trust_score mock might be better.

    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_emotion_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_bias_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_patterns_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._calculate_trust_score_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._generate_overall_assessment') # Also mock this as it's called
    def test_analyze_valid_text_structure(self,
                                         mock_generate_overall_assessment,
                                         mock_calculate_trust_score_safe,
                                         mock_analyze_patterns_safe,
                                         mock_analyze_bias_safe,
                                         mock_analyze_emotion_safe,
                                         mock_analyze_sentiment_safe):
        """Test the basic structure of analyze output with valid text, mocking sub-components."""
        # Configure mocks to return basic valid structures
        mock_analyze_sentiment_safe.return_value = {'label': 'neutral', 'confidence': 0.9, 'all_scores': {}, 'bias_indicator': False}
        mock_analyze_emotion_safe.return_value = {'label': 'neutral', 'confidence': 0.8, 'manipulation_risk': 'minimal', 'is_emotionally_charged': False}
        # For a general valid text, assume no bias flag, leading to primary_bias_type being None
        mock_analyze_bias_safe.return_value = {'flag': False, 'label': 'Likely Neutral', 'type_analysis': {'type': 'neutral', 'confidence': 90.0}}
        mock_analyze_patterns_safe.return_value = {'nigerian_patterns': {}, 'fake_news': {'detected': False}, 'viral_manipulation': {}}
        # Mock the trust score calculation to return a predictable structure
        mock_calculate_trust_score_safe.return_value = {
            'score': 80,
            'indicator': '🟢 Trusted',
            'explanation': ['Test explanation'],
            'tip': 'Test tip',
            'trust_level': 'highly_trusted',
            'risk_factors': [],
            'summary': 'Test summary',
            'pattern_analysis': {}
        }
        mock_generate_overall_assessment.return_value = {} # Content doesn't matter much as its parts are taken by analyze

        analysis = analyze("This is a comprehensive test sentence.")
        self.assertIsNotNone(analysis)
        self.assertIn('trust_score', analysis)
        self.assertIn('indicator', analysis)
        self.assertIn('explanation', analysis)
        self.assertIsInstance(analysis['explanation'], list)
        self.assertIn('tip', analysis)
        self.assertIn('primary_bias_type', analysis) # Check for the new key
        self.assertIsNone(analysis['primary_bias_type']) # Expect None when bias_result['flag'] is False
        self.assertIn('metadata', analysis)
        self.assertIn('component_processing_times', analysis['metadata'])
        self.assertIn('overall_processing_time_seconds', analysis['metadata'])
        self.assertIn('text_length', analysis['metadata'])
        self.assertIn('initialized_components', analysis['metadata'])
        self.assertIn('analysis_timestamp', analysis['metadata'])

    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_emotion_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_bias_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_patterns_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._calculate_trust_score_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._generate_overall_assessment')
    def test_analyze_specific_bias_type_detected(self,
                                                 mock_generate_overall_assessment,
                                                 mock_calculate_trust_score_safe,
                                                 mock_analyze_patterns_safe,
                                                 mock_analyze_bias_safe,
                                                 mock_analyze_emotion_safe,
                                                 mock_analyze_sentiment_safe):
        """Test analyze output when a specific bias type is detected and explained."""
        # Configure mocks
        mock_analyze_sentiment_safe.return_value = {'label': 'neutral', 'confidence': 0.9, 'all_scores': {}, 'bias_indicator': False}
        mock_analyze_emotion_safe.return_value = {'label': 'neutral', 'confidence': 0.8, 'manipulation_risk': 'minimal', 'is_emotionally_charged': False}

        # Mock bias detection to indicate a specific bias
        mock_bias_type = "political_bias" # Use underscore version as it comes from model/classification
        mock_analyze_bias_safe.return_value = {
            'flag': True,
            'label': 'Potentially Biased - High Confidence',
            'type_analysis': {'type': mock_bias_type, 'confidence': 95.0, 'all_predictions': []}
        }

        mock_analyze_patterns_safe.return_value = {'nigerian_patterns': {}, 'fake_news': {'detected': False}, 'viral_manipulation': {}}

        # Mock trust score to include the specific bias explanation from TrustScoreCalculator
        # This part assumes TrustScoreCalculator correctly formats the bias type in its explanation
        expected_explanation_fragment = f"Dominant bias type identified: {mock_bias_type.replace('_', ' ').title()}."
        mock_calculate_trust_score_safe.return_value = {
            'score': 40,
            'indicator': '🟡 Caution',
            'explanation': ['High confidence bias detected in language patterns.', expected_explanation_fragment],
            'tip': 'Verify this content.',
            'trust_level': 'high_caution', 'risk_factors': ['high_bias'], 'summary': 'Concerning.', 'pattern_analysis': {}
        }
        mock_generate_overall_assessment.return_value = {}

        analysis = analyze("This text has clear political bias.")

        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.get('primary_bias_type'), mock_bias_type)
        # The explanation in the final result comes from trust_result.get('explanation')
        # So we check if the mock_calculate_trust_score_safe's explanation is passed through.
        self.assertIn(expected_explanation_fragment, analysis.get('explanation', []))
        self.assertIn('High confidence bias detected in language patterns.', analysis.get('explanation', []))


    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_emotion_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_bias_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._calculate_trust_score_safe') # patterns mock not needed if not primary
    def test_analyze_recommendations_and_educational_tips(self,
                                                            mock_calculate_trust_score_safe,
                                                            mock_analyze_bias_safe,
                                                            mock_analyze_emotion_safe,
                                                            mock_analyze_sentiment_safe):
        """
        Test that analyze() output reflects different recommendations and educational tips
        based on mocked inputs to _calculate_trust_score_safe, which internally depends on
        _generate_overall_assessment logic.
        """
        # Common mocks for sub-analyzers not directly affecting the specific tested aspect in each sub-case
        mock_analyze_sentiment_safe.return_value = {'label': 'neutral', 'confidence': 0.9}
        mock_analyze_emotion_safe.return_value = {'label': 'neutral', 'confidence': 0.8, 'manipulation_risk': 'minimal', 'is_emotionally_charged': False}
        mock_analyze_bias_safe.return_value = {'flag': False, 'type_analysis': {'type': 'neutral'}}

        # --- Test Recommendations based on Trust Score ---
        # High score
        mock_calculate_trust_score_safe.return_value = {
            'score': 80, 'indicator': '🟢 Trusted', 'explanation': ['Seems okay.'],
            'tip': "Always critically evaluate information before accepting or sharing it.", # Default educational tip
            'summary': "This content appears generally trustworthy. Always exercise critical thinking by considering the source and looking for supporting evidence on important topics.", # Contains recommendation
            'risk_factors': [], 'trust_level': 'high'
        }
        result = analyze("High score text")
        self.assertIn("This content appears generally trustworthy", result['summary'])

        # Medium score
        mock_calculate_trust_score_safe.return_value = {
            'score': 50, 'indicator': '🟡 Caution', 'explanation': ['Some concerns.'],
            'tip': "Always critically evaluate information before accepting or sharing it.",
            'summary': "This content has some concerning patterns. Cross-reference key claims with reputable news outlets or fact-checking websites (e.g., Snopes, PolitiFact, or local equivalents) before accepting them as true. Be mindful of the potential biases or manipulative language identified.",
            'risk_factors': ['bias'], 'trust_level': 'medium'
        }
        result = analyze("Medium score text")
        self.assertIn("Cross-reference key claims", result['summary'])

        # Low score
        mock_calculate_trust_score_safe.return_value = {
            'score': 20, 'indicator': '🔴 Untrustworthy', 'explanation': ['Many concerns.'],
            'tip': "Always critically evaluate information before accepting or sharing it.",
            'summary': "This content shows multiple red flags. Be very skeptical of its claims and avoid sharing it until independently verified by trusted sources. Consider the potential intent behind the message and who might benefit from its spread.",
            'risk_factors': ['bias', 'emotion'], 'trust_level': 'low'
        }
        result = analyze("Low score text")
        self.assertIn("Be very skeptical of its claims", result['summary'])

        # --- Test Educational Tips ---
        # Tip for specific bias type (Political Bias)
        # We need to ensure the mock_calculate_trust_score_safe reflects a state where bias was the primary reason for the tip
        mock_analyze_bias_safe.return_value = {'flag': True, 'type_analysis': {'type': 'political_bias'}}
        mock_calculate_trust_score_safe.return_value = {
            'score': 50, 'indicator': '🟡 Caution', 'explanation': ['Bias found.'],
            'tip': "Learn more about Political Bias: Understand its common characteristics and how it can influence perception. Look for signs like selective reporting or emotionally loaded framing related to this bias.",
            'summary': "Concern: Potential Political Bias detected.", 'risk_factors': ['bias_political_bias'], 'trust_level': 'medium'
        }
        result = analyze("Text with political bias")
        self.assertIn("Learn more about Political Bias", result['tip'])
        mock_analyze_bias_safe.return_value = {'flag': False, 'type_analysis': {'type': 'neutral'}} # Reset

        # Tip for emotional manipulation
        mock_analyze_emotion_safe.return_value = {'label': 'anger', 'confidence': 0.9, 'manipulation_risk': 'high', 'is_emotionally_charged': True}
        mock_calculate_trust_score_safe.return_value = {
            'score': 45, 'indicator': '🟡 Caution', 'explanation': ['Emotionally charged.'],
            'tip': "Recognize emotionally manipulative language: Pay attention to words designed to evoke strong emotional responses (e.g., 'outrageous,' 'shocking,' 'miraculous'). Such language can overshadow factual reporting. Question if the emotion is justified by the evidence.",
            'summary': "Concern: Uses language that may be emotionally manipulative.", 'risk_factors': ['emotion_high_risk'], 'trust_level': 'medium'
        }
        result = analyze("Text with emotional manipulation")
        self.assertIn("Recognize emotionally manipulative language", result['tip'])
        mock_analyze_emotion_safe.return_value = {'label': 'neutral', 'confidence': 0.8, 'manipulation_risk': 'minimal', 'is_emotionally_charged': False} # Reset

        # Tip for clickbait (simulated by risk_factors in trust_result)
        # _generate_overall_assessment checks for 'clickbait' in risk_factors string
        mock_calculate_trust_score_safe.return_value = {
            'score': 55, 'indicator': '🟡 Caution', 'explanation': ['Clickbaity.'],
            'tip': "Identify clickbait: Watch out for sensationalized headlines or teasers that withhold key information to provoke clicks. Compare the headline with the actual content to see if it delivers on its promise.",
            'summary': "Concern: Shows characteristics of clickbait.", 'risk_factors': ['clickbait_detected_pattern'], 'trust_level': 'medium'
        }
        result = analyze("Text with clickbait patterns")
        self.assertIn("Identify clickbait", result['tip'])

        # Tip for misinformation (simulated by risk_factors in trust_result)
        # _generate_overall_assessment checks for 'fake_risk' in risk_factors string
        mock_calculate_trust_score_safe.return_value = {
            'score': 30, 'indicator': '🔴 Untrustworthy', 'explanation': ['Misinformation signs.'],
            'tip': "Spotting misinformation: Look for unverifiable claims, anonymous sources, or a lack of credible evidence. Check if other reputable sources are reporting the same information.",
            'summary': "Concern: Contains elements associated with misinformation.", 'risk_factors': ['fake_risk_high'], 'trust_level': 'low'
        }
        result = analyze("Text with misinformation signs")
        self.assertIn("Spotting misinformation", result['tip'])

        # Default educational tip (no specific major concern triggering a specialized tip)
        mock_calculate_trust_score_safe.return_value = {
            'score': 75, 'indicator': '🟢 Trusted', 'explanation': ['Generally okay.'],
            'tip': "Always critically evaluate information before accepting or sharing it.", # Default
            'summary': "This content appears generally trustworthy.", 'risk_factors': [], 'trust_level': 'high'
        }
        result = analyze("Generally okay text")
        self.assertEqual("Always critically evaluate information before accepting or sharing it.", result['tip'])


    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_emotion_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_bias_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._calculate_trust_score_safe')
    def test_analyze_primary_concerns(self,
                                     mock_calculate_trust_score_safe,
                                     mock_analyze_bias_safe,
                                     mock_analyze_emotion_safe,
                                     mock_analyze_sentiment_safe):
        """
        Test that analyze() output reflects different primary concerns based on mocked inputs.
        Primary concerns are usually part of the 'summary' or 'explanation' from trust_result.
        """
        mock_analyze_sentiment_safe.return_value = {'label': 'neutral', 'confidence': 0.9}

        # Concern: Bias Type
        mock_analyze_bias_safe.return_value = {'flag': True, 'type_analysis': {'type': 'confirmation_bias'}}
        mock_analyze_emotion_safe.return_value = {'manipulation_risk': 'minimal'}
        mock_calculate_trust_score_safe.return_value = {
            'score': 50, 'indicator': '🟡 Caution', 'explanation': ['Bias.'], 'tip': 'Tip.',
            'summary': "Primary Concern: Potential Confirmation Bias detected. Recommendation: Verify.",
            'risk_factors': ['bias_confirmation_bias'], 'trust_level': 'medium'
        }
        result = analyze("Text with confirmation bias")
        self.assertIn("Potential Confirmation Bias detected", result['summary'])
        mock_analyze_bias_safe.return_value = {'flag': False, 'type_analysis': {'type': 'neutral'}} # Reset

        # Concern: Emotional Manipulation
        mock_analyze_emotion_safe.return_value = {'manipulation_risk': 'high', 'is_emotionally_charged': True}
        mock_calculate_trust_score_safe.return_value = {
            'score': 45, 'indicator': '🟡 Caution', 'explanation': ['Emotion.'], 'tip': 'Tip.',
            'summary': "Primary Concern: Uses language that may be emotionally manipulative. Recommendation: Be wary.",
            'risk_factors': ['emotion_high_risk'], 'trust_level': 'medium'
        }
        result = analyze("Text with high emotional manipulation")
        self.assertIn("Uses language that may be emotionally manipulative", result['summary'])
        mock_analyze_emotion_safe.return_value = {'manipulation_risk': 'minimal', 'is_emotionally_charged': False} # Reset

        # Concern: Clickbait (via risk_factors)
        mock_calculate_trust_score_safe.return_value = {
            'score': 55, 'indicator': '🟡 Caution', 'explanation': ['Clickbait.'], 'tip': 'Tip.',
            'summary': "Primary Concern: Shows characteristics of clickbait. Recommendation: Check content.",
            'risk_factors': ['has_clickbait_pattern'], 'trust_level': 'medium'
        }
        result = analyze("Text with clickbait")
        self.assertIn("Shows characteristics of clickbait", result['summary'])

        # Concern: Misinformation/Fake News (via risk_factors)
        mock_calculate_trust_score_safe.return_value = {
            'score': 30, 'indicator': '🔴 Untrustworthy', 'explanation': ['Fake.'], 'tip': 'Tip.',
            'summary': "Primary Concern: Contains elements associated with misinformation. Recommendation: Do not trust.",
            'risk_factors': ['fake_news_risk_high'], 'trust_level': 'low'
        }
        result = analyze("Text with fake news indicators")
        self.assertIn("Contains elements associated with misinformation", result['summary'])

        # Multiple Concerns
        mock_analyze_bias_safe.return_value = {'flag': True, 'type_analysis': {'type': 'sensationalism_bias'}}
        mock_analyze_emotion_safe.return_value = {'manipulation_risk': 'medium', 'is_emotionally_charged': True}
        mock_calculate_trust_score_safe.return_value = {
            'score': 35, 'indicator': '🔴 Untrustworthy', 'explanation': ['Multiple issues.'], 'tip': 'Tip.',
            'summary': "Primary Concerns: Potential Sensationalism Bias detected. Uses language that may be emotionally manipulative. Recommendation: Extreme caution.",
            'risk_factors': ['bias_sensationalism', 'emotion_medium_risk'], 'trust_level': 'low'
        }
        result = analyze("Text with multiple issues")
        self.assertIn("Potential Sensationalism Bias detected", result['summary'])
        self.assertIn("Uses language that may be emotionally manipulative", result['summary'])


if __name__ == '__main__':
    unittest.main()
