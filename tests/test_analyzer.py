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
        self.assertEqual(results.get('status'), 'error', "Status should be 'error'.")
        self.assertEqual(results.get('error'), 'Empty text', "Error message for empty input is incorrect.")
        self.assertIn('overall_assessment', results)
        self.assertEqual(results['overall_assessment'].get('recommendation'), 'No text provided for analysis')


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
        # Configure mocks to return basic valid structures
        mock_sentiment_safe.return_value = {'label': 'neutral', 'confidence': 0.9, 'all_scores': {}, 'bias_indicator': False}
        mock_nigerian_patterns.return_value = {'has_triggers': False, 'has_clickbait': False, 'trigger_score':0, 'clickbait_score':0, 'total_flags':0}
        mock_fake_news_detect.return_value = (False, {'fake_matches':[], 'credibility_flags':[], 'fake_score':0, 'credibility_score':0, 'risk_level':'minimal', 'total_flags':0})

        results = quick_analyze("This is a test sentence.")
        self.assertIsNotNone(results)
        self.assertIn('score', results)
        self.assertIn('indicator', results)
        self.assertIn('explanation', results)
        self.assertIsInstance(results['explanation'], list)
        self.assertIn('tip', results)
        self.assertEqual(results['tip'], "For a more comprehensive analysis, use the full analyze function.")

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
        mock_analyze_bias_safe.return_value = {'flag': False, 'label': 'Likely Neutral', 'type_analysis': {'type': 'neutral', 'confidence': 90}}
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
        self.assertIn('metadata', analysis)
        self.assertIn('component_processing_times', analysis['metadata'])
        self.assertIn('overall_processing_time_seconds', analysis['metadata'])
        self.assertIn('text_length', analysis['metadata'])
        self.assertIn('initialized_components', analysis['metadata'])
        self.assertIn('analysis_timestamp', analysis['metadata'])

if __name__ == '__main__':
    unittest.main()
