import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from biaslens.analyzer import BiasLensAnalyzer, analyze, quick_analyze # Assuming global functions use a global analyzer instance
from biaslens.utils import _model_cache

# Path to modules that BiasLensAnalyzer initializes internally
PATH_SENTIMENT = 'biaslens.analyzer.SentimentAnalyzer'
PATH_EMOTION = 'biaslens.analyzer.EmotionClassifier'
PATH_BIAS_DETECTOR = 'biaslens.analyzer.BiasDetector'
PATH_BIAS_CLASSIFIER = 'biaslens.analyzer.BiasTypeClassifier'
PATH_TRUST_CALCULATOR = 'biaslens.analyzer.TrustScoreCalculator'
PATH_NIGERIAN_PATTERNS = 'biaslens.analyzer.NigerianPatterns'
PATH_FAKE_NEWS_DETECTOR = 'biaslens.analyzer.FakeNewsDetector'
PATH_VIRALITY_DETECTOR = 'biaslens.analyzer.ViralityDetector'


class TestBiasLensAnalyzer(unittest.TestCase):
    def setUp(self):
        _model_cache.clear() # Clear cache to avoid interference between tests

        # Default mock return values for sub-analyzers
        self.mock_sentiment_data = {'label': 'neutral', 'confidence': 0.9, 'all_scores': {}, 'bias_indicator': False, 'is_polarized': False, 'polarization_score': 0.1}
        self.mock_emotion_data = {'label': 'neutral', 'confidence': 0.9, 'manipulation_risk': 'minimal', 'is_emotionally_charged': False, 'top_emotions':[]}
        self.mock_bias_detection_data = {'flag': False, 'label': 'Neutral', 'type_analysis': {'type': 'neutral', 'confidence': 0.9}, 'detected': False}
        # Note: BiasTypeClassifier is part of BiasDetector's output structure if called internally by it,
        # or BiasLensAnalyzer might call it separately. The current BiasLensAnalyzer calls them separately via properties.
        # So, BiasDetector's mock should return its own part, and BiasTypeClassifier its own.
        # The mock_bias_detection_data above is more for the _analyze_bias_safe wrapper.

        self.mock_pattern_data = {
            'nigerian_patterns': {'has_triggers': False, 'has_clickbait': False},
            'fake_news': {'detected': False, 'details': {}},
            'viral_manipulation': {'score': 0, 'indicators': []}
        }
        self.mock_trust_score_data = {'score': 80, 'indicator': "🟢 Trusted", 'explanation': ["Generally good."], 'tip': "Be critical."}

    # Patch all the properties that lazy-load the analyzers
    @patch(f"{PATH_SENTIMENT}", new_callable=MagicMock)
    @patch(f"{PATH_EMOTION}", new_callable=MagicMock)
    @patch(f"{PATH_BIAS_DETECTOR}", new_callable=MagicMock)
    @patch(f"{PATH_BIAS_CLASSIFIER}", new_callable=MagicMock)
    # Patch the static methods of pattern detectors if they are called directly by analyzer
    @patch(f"{PATH_NIGERIAN_PATTERNS}.analyze_patterns")
    @patch(f"{PATH_FAKE_NEWS_DETECTOR}.detect")
    @patch(f"{PATH_VIRALITY_DETECTOR}.analyze_virality")
    # Patch TrustScoreCalculator if its static calculate method is used
    @patch(f"{PATH_TRUST_CALCULATOR}.calculate")
    def test_analyze_successful_run(self, mock_trust_calculate, mock_virality_analyze, mock_fake_detect,
                                    mock_nigerian_analyze, mock_bias_type_classifier_class, mock_bias_detector_class,
                                    mock_emotion_classifier_class, mock_sentiment_analyzer_class):

        verbosities = ["compact", "default", "full"]
        text_to_analyze = "This is a neutral and factual statement."

        # Common mock configurations
        mock_sentiment_analyzer_instance = mock_sentiment_analyzer_class.return_value
        mock_sentiment_analyzer_instance.analyze.return_value = self.mock_sentiment_data

        mock_emotion_classifier_instance = mock_emotion_classifier_class.return_value
        mock_emotion_classifier_instance.classify.return_value = self.mock_emotion_data

        mock_bias_detector_instance = mock_bias_detector_class.return_value
        mock_bias_detector_instance.detect.return_value = (False, "Neutral")

        mock_bias_type_classifier_instance = mock_bias_type_classifier_class.return_value
        mock_bias_type_classifier_instance.predict.return_value = {'type': 'neutral', 'confidence': 0.9}

        mock_nigerian_analyze.return_value = self.mock_pattern_data['nigerian_patterns']
        mock_fake_detect.return_value = (False, self.mock_pattern_data['fake_news']['details']) # Returns tuple
        mock_virality_analyze.return_value = self.mock_pattern_data['viral_manipulation']

        mock_trust_calculate.return_value = (
            self.mock_trust_score_data['score'],
            self.mock_trust_score_data['indicator'],
            self.mock_trust_score_data['explanation'],
            self.mock_trust_score_data['tip'],
            {'trust_level': 'highly_trusted', 'risk_factors': [], 'summary': 'Good summary.', 'pattern_analysis': {}}
        )

        analyzer = BiasLensAnalyzer()

        for verbosity in verbosities:
            with self.subTest(verbosity=verbosity):
                # Reset mocks that are called in a loop or whose call counts are asserted per subtest
                mock_sentiment_analyzer_instance.analyze.reset_mock()
                mock_emotion_classifier_instance.classify.reset_mock()
                mock_bias_detector_instance.detect.reset_mock()
                mock_bias_type_classifier_instance.predict.reset_mock()
                mock_nigerian_analyze.reset_mock()
                mock_fake_detect.reset_mock()
                mock_virality_analyze.reset_mock()
                mock_trust_calculate.reset_mock()

                result = analyzer.analyze(text_to_analyze, verbosity=verbosity)

                self.assertEqual(result["status"], "success")
                self.assertEqual(result['trust_score'], self.mock_trust_score_data['score'])
                self.assertEqual(result['indicator'], self.mock_trust_score_data['indicator'])

                if verbosity == "compact":
                    self.assertIn("summary_assessment", result)
                    self.assertEqual(result["summary_assessment"], "Good summary.")
                    expected_keys = {"status", "trust_score", "indicator", "summary_assessment"}
                    self.assertEqual(set(result.keys()), expected_keys)
                elif verbosity == "default":
                    self.assertIn("explanation", result)
                    self.assertIn("tip", result)
                    self.assertIn("metadata", result)
                    self.assertEqual(result["explanation"], self.mock_trust_score_data['explanation'])
                    self.assertEqual(result["tip"], self.mock_trust_score_data['tip'])
                    expected_keys = {"status", "trust_score", "indicator", "explanation", "tip", "metadata"}
                    self.assertEqual(set(result.keys()), expected_keys)
                elif verbosity == "full":
                    self.assertIn("explanation", result)
                    self.assertIn("tip", result)
                    self.assertIn("metadata", result)
                    self.assertIn("detailed_analyses", result)
                    self.assertEqual(result["detailed_analyses"]["sentiment"], self.mock_sentiment_data)
                    self.assertEqual(result["detailed_analyses"]["emotion"], self.mock_emotion_data)
                    # For bias, the result is constructed inside _run_bias_analysis
                    self.assertEqual(result["detailed_analyses"]["bias"]['flag'], False)
                    self.assertEqual(result["detailed_analyses"]["bias"]['label'], "Neutral")
                    self.assertEqual(result["detailed_analyses"]["patterns"]["nigerian_patterns"], self.mock_pattern_data['nigerian_patterns'])
                    expected_keys = {"status", "trust_score", "indicator", "explanation", "tip", "detailed_analyses", "metadata"}
                    self.assertEqual(set(result.keys()), expected_keys)

                # Assert that core components were called (these are reset per subtest)
                mock_sentiment_analyzer_instance.analyze.assert_called_once_with(text_to_analyze)
                mock_emotion_classifier_instance.classify.assert_called_once_with(text_to_analyze)
                mock_bias_detector_instance.detect.assert_called_once_with(text_to_analyze)
                mock_bias_type_classifier_instance.predict.assert_called_once_with(text_to_analyze)
                mock_nigerian_analyze.assert_called_once()
                mock_fake_detect.assert_called_once()
                mock_virality_analyze.assert_called_once()
                mock_trust_calculate.assert_called_once()


    def test_analyze_empty_text(self):
        analyzer = BiasLensAnalyzer()
        verbosities = ["compact", "default", "full"]
        error_msg_expected = "Empty or invalid text provided for analysis."

        for verbosity in verbosities:
            with self.subTest(verbosity=verbosity):
                result = analyzer.analyze("", verbosity=verbosity)
                self.assertEqual(result["status"], "error")
                self.assertIsNone(result['trust_score'])
                self.assertEqual(result['indicator'], 'Error')

                if verbosity == "compact":
                    self.assertIn("summary_assessment", result)
                    self.assertEqual(result["summary_assessment"], error_msg_expected)
                    self.assertEqual(len(result.keys()), 4)
                else: # default & full
                    self.assertIn("explanation", result)
                    self.assertEqual(result["explanation"], [error_msg_expected])
                    self.assertIn("tip", result)
                    self.assertIn("metadata", result)
                    self.assertIn("error_message", result["metadata"])

    @patch(f"{PATH_SENTIMENT}", new_callable=MagicMock) # Mock the class being instantiated by BiasLensAnalyzer
    def test_analyze_critical_error_during_analysis(self, mock_sentiment_analyzer_class):
        # This test simulates an error in the main try-except block of BiasLensAnalyzer.analyze
        # For example, if TrustScoreCalculator.calculate itself raises an unexpected error.
        # Errors from sub-components are handled by the decorator and return default dicts.

        mock_sentiment_analyzer_class.return_value.analyze.return_value = self.mock_sentiment_data # Sentiment is fine

        analyzer = BiasLensAnalyzer()
        verbosities = ["compact", "default", "full"]
        simulated_error_message = "Critical calculation error"

        # Mock a later stage, e.g., TrustScoreCalculator, to raise an exception
        with patch(PATH_TRUST_CALCULATOR + '.calculate', side_effect=Exception(simulated_error_message)):
            for verbosity in verbosities:
                with self.subTest(verbosity=verbosity):
                    result = analyzer.analyze("Test critical error.", verbosity=verbosity)

                    self.assertEqual(result["status"], "error")
                    self.assertIsNone(result['trust_score'])
                    self.assertEqual(result['indicator'], 'Error')

                    if verbosity == "compact":
                        self.assertIn("summary_assessment", result)
                        self.assertTrue(simulated_error_message in result["summary_assessment"])
                        self.assertEqual(len(result.keys()), 4)
                    else: # default & full
                        self.assertIn("explanation", result)
                        self.assertTrue(any(simulated_error_message in expl for expl in result["explanation"]))
                        self.assertIn("tip", result)
                        self.assertIn("metadata", result)
                        self.assertIn("error_message", result["metadata"])
                        self.assertEqual(result["metadata"]["error_message"], simulated_error_message)


    @patch(f"{PATH_NIGERIAN_PATTERNS}.analyze_patterns") # For quick_analyze
    @patch(f"{PATH_FAKE_NEWS_DETECTOR}.detect")
    @patch(f"{PATH_SENTIMENT}", new_callable=MagicMock) # For quick_analyze, only sentiment and patterns are used
    def test_quick_analyze_successful_run(self, mock_sentiment_analyzer_class, mock_fake_detect, mock_nigerian_analyze):
        mock_sentiment_instance = mock_sentiment_analyzer_class.return_value
        mock_sentiment_instance.analyze.return_value = self.mock_sentiment_data

        mock_nigerian_analyze.return_value = self.mock_pattern_data['nigerian_patterns']
        mock_fake_detect.return_value = (False, self.mock_pattern_data['fake_news']['details'])

        analyzer = BiasLensAnalyzer()
        result = analyzer.quick_analyze("Quick test this.")

        self.assertIn('score', result)
        self.assertIn('indicator', result)
        self.assertIsNotNone(result['score']) # Should have a score from _calculate_basic_trust_score

        mock_sentiment_instance.analyze.assert_called_once_with("Quick test this.")
        mock_nigerian_analyze.assert_called_once_with("Quick test this.")
        mock_fake_detect.assert_called_once_with("Quick test this.")

    def test_quick_analyze_empty_text(self):
        analyzer = BiasLensAnalyzer()
        # This should use the _get_empty_analysis_result method.
        # The structure of that method's return is different from the main analyze.
        # Based on current analyzer.py, it returns a dict with 'status':'error' and 'overall_assessment'.
        result = analyzer.quick_analyze("")
        self.assertEqual(result.get('status'), 'error') # As per _get_empty_analysis_result
        self.assertIn("Empty or invalid text", result.get('error', ""))


    @patch.object(BiasLensAnalyzer, 'analyze', new_callable=MagicMock) # Mocking its own full analyze method
    @patch(f"{PATH_SENTIMENT}", new_callable=MagicMock) # Still need to mock SentimentAnalyzer for analyze_headline_vs_content
    def test_analyze_headline_content_mismatch(self, mock_sentiment_analyzer_class_prop, mock_full_analyze_method):

        # Mock for the SentimentAnalyzer instance used by analyze_headline_vs_content for direct sentiment comparison
        mock_sentiment_analyzer_instance = MagicMock()
        mock_sentiment_analyzer_instance.analyze_headline_vs_content.return_value = {
            'is_clickbait_likely': True,
            'headline_sentiment_label': 'positive',
            'content_sentiment_label': 'negative'
        }

        # Mock the property to return our sentiment analyzer instance
        # This requires patching the property on the class for all instances, or on the instance.
        # Easier to patch where it's instantiated if it's direct, or its .sentiment_analyzer property.

        analyzer = BiasLensAnalyzer()

        # We need to control what the internal calls to `self.analyze` (mocked by mock_full_analyze_method) return.
        # And what `self.sentiment_analyzer.analyze_headline_vs_content` returns.

        # Mocking the full 'analyze' calls for headline and content
        headline_analysis_mock = {'trust_score': 80, 'detailed_analysis': {'emotion': {'is_emotionally_charged': False}, 'sentiment': self.mock_sentiment_data}}
        content_analysis_mock = {'trust_score': 30, 'detailed_analysis': {'emotion': {'is_emotionally_charged': True}, 'sentiment': self.mock_sentiment_data}}
        mock_full_analyze_method.side_effect = [headline_analysis_mock, content_analysis_mock]

        # To properly mock the self.sentiment_analyzer property when it's accessed:
        with patch.object(BiasLensAnalyzer, 'sentiment_analyzer', new_callable=PropertyMock) as mock_sa_prop:
            mock_sa_prop.return_value = mock_sentiment_analyzer_instance # The sentiment_analyzer property returns our mock

            result = analyzer.analyze_headline_content_mismatch("Great News!", "Actually, it's terrible.")

            self.assertEqual(result['status'], 'success')
            self.assertIsNotNone(result['mismatch_analysis'])
            self.assertTrue(result['mismatch_analysis']['is_likely_clickbait'])

            mock_full_analyze_method.assert_any_call("Great News!", include_patterns=False)
            mock_full_analyze_method.assert_any_call("Actually, it's terrible.", include_patterns=False)
            mock_sentiment_analyzer_instance.analyze_headline_vs_content.assert_called_once_with("Great News!", "Actually, it's terrible.")


# Tests for global functions (if they use a global analyzer instance)
# These tests assume that `analyze` and `quick_analyze` are thin wrappers around
# a global BiasLensAnalyzer instance's methods.
# We need to patch the global instance or the methods on the class BiasLensAnalyzer if that's what's used.

@patch('biaslens.analyzer._global_analyzer', new_callable=MagicMock) # Path to the global instance
class TestGlobalAnalyzerFunctions(unittest.TestCase):

    def test_global_analyze_calls_instance_method(self, mock_global_analyzer_instance):
        verbosities = ["compact", "default", "full"]
        text = "Test global analyze"
        headline_text = "H"
        include_patterns_flag = False

        for verbosity_level in verbosities:
            with self.subTest(verbosity=verbosity_level):
                mock_global_analyzer_instance.analyze.reset_mock() # Reset for each subtest
                expected_return = {"status": f"mocked_analyze_{verbosity_level}"}
                mock_global_analyzer_instance.analyze.return_value = expected_return

                result = analyze(
                    text,
                    include_patterns=include_patterns_flag,
                    headline=headline_text,
                    verbosity=verbosity_level
                )

                mock_global_analyzer_instance.analyze.assert_called_once_with(
                    text,
                    include_patterns=include_patterns_flag,
                    headline=headline_text,
                    verbosity=verbosity_level
                )
                self.assertEqual(result, expected_return)

    def test_global_quick_analyze_calls_instance_method(self, mock_global_analyzer_instance):
        mock_global_analyzer_instance.quick_analyze.return_value = {"status": "mocked_quick_analyze"}
        text = "Test global quick_analyze"
        result = quick_analyze(text)

        mock_global_analyzer_instance.quick_analyze.assert_called_once_with(text)
        self.assertEqual(result, {"status": "mocked_quick_analyze"})


if __name__ == '__main__':
    unittest.main()
