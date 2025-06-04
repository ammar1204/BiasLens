import unittest
from unittest.mock import patch, MagicMock
from biaslens.analyzer import BiasLensAnalyzer, analyse
# Removed: from biaslens.bias import NigerianBiasEnhancer
from biaslens.trust import TrustScoreCalculator

# Removed TestNigerianBiasEnhancer class

class TestBiasLensAnalyzer(unittest.TestCase):

    def setUp(self):
        # Mocks for BiasLensAnalyzer instance methods (used by 'analyze' instance method)
        self.patcher_analyzer_sentiment = patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
        self.mock_analyzer_sentiment = self.patcher_analyzer_sentiment.start()

        self.patcher_analyzer_emotion = patch('biaslens.analyzer.BiasLensAnalyzer._analyze_emotion_safe')
        self.mock_analyzer_emotion = self.patcher_analyzer_emotion.start()

        # Changed: Patching new_bias_analyzer.analyze instead of _analyze_bias_safe
        self.patcher_new_bias_analyzer_analyze = patch('biaslens.analyzer.BiasLensAnalyzer.new_bias_analyzer.analyze')
        self.mock_new_bias_analyzer_analyze = self.patcher_new_bias_analyzer_analyze.start()

        self.patcher_analyzer_patterns = patch('biaslens.analyzer.BiasLensAnalyzer._analyze_patterns_safe')
        self.mock_analyzer_patterns = self.patcher_analyzer_patterns.start()

        # Removed: patcher_analyzer_lw_enhancer_for_analyze

        self.patcher_analyzer_trust_calc = patch('biaslens.analyzer.BiasLensAnalyzer._calculate_trust_score_safe')
        self.mock_analyzer_trust_calc = self.patcher_analyzer_trust_calc.start()

        # Removed: patcher_enhancer_quick and mock_enhancer_for_quick_analyze as quick_analyze no longer uses it directly for bias info.
        # NigerianPatterns.analyze_patterns is mocked directly in its test.

        # Default mock returns for 'analyze' dependencies (can be overridden in specific tests)
        self.mock_analyzer_sentiment.return_value = {'label': 'neutral', 'confidence': 0.9}
        self.mock_analyzer_emotion.return_value = {'label': 'neutral', 'confidence': 0.8, 'is_emotionally_charged': False, 'manipulation_risk': 'low'}

        # Updated default return_value for the new bias analyzer mock
        self.mock_new_bias_analyzer_analyze.return_value = {
            "text": "Test text",
            "timestamp": "some_timestamp",
            "overall_bias": {"is_biased": False, "confidence": 0.1, "level": "minimal"}, # 'minimal' to match _analyze_bias_safe's label construction
            "bias_details": {"type": "neutral", "type_confidence": 0.95, "nigerian_context": False, "specific_detections": []},
            "clickbait": {"is_clickbait": False, "confidence": 0.1, "level": "low", "detected_patterns": [], "explanation": ""},
            "recommendations": [],
            "technical_details": {"base_model_score": 0.1, "explanation": "Base model analysis"}
        }

        self.mock_analyzer_patterns.return_value = {
            'nigerian_patterns': {'has_triggers': False, 'has_clickbait': False, 'trigger_matches': []}, # Added trigger_matches
            'fake_news': {'detected': False, 'details': {'risk_level': 'low', 'matched_phrases': [], 'is_clickbait': False, 'fake_matches': []}},
            'viral_manipulation': {'is_potentially_viral': False, 'engagement_bait_score': 0.1, 'sensationalism_score': 0.1}
        }

        self.mock_analyzer_trust_calc.return_value = {
            'score': 80, 'indicator': '🟢 Trusted',
            'explanation': ['Generally trustworthy.'], 'tip': 'A general tip.'
        }
        # Note: _generate_overall_assessment is not directly mocked anymore, as its inputs are derived from other mocks.
        # Its functionality is tested implicitly via the main 'analyze' method tests.


    def tearDown(self):
        # Removed: self.patcher_enhancer_quick.stop()
        self.patcher_analyzer_sentiment.stop()
        self.patcher_analyzer_emotion.stop()
        self.patcher_new_bias_analyzer_analyze.stop() # Updated
        self.patcher_analyzer_patterns.stop()
        # Removed: self.patcher_analyzer_lw_enhancer_for_analyze.stop()
        self.patcher_analyzer_trust_calc.stop()
        # Removed: self.patcher_analyzer_overall_assessment.stop() # This was not started in setUp in this version

    # ... (analyze method tests remain unchanged from previous step) ...
    def test_analyze_empty_text_core_solution_structure(self):
        analysis_result = analyse("")
        self.assertEqual(analysis_result['indicator'], 'Error')
        self.assertEqual(analysis_result['explanation'], ["Empty or invalid text provided."]) # Corrected typo
        self.assertEqual(analysis_result['tip'], "Analysis failed: No text was provided. Please input text for analysis.")
        self.assertIsNone(analysis_result['trust_score'])
        self.assertIsNone(analysis_result['tone_analysis'])
        self.assertIsNone(analysis_result['bias_analysis'])
        self.assertIsNone(analysis_result['manipulation_analysis'])
        self.assertIsNone(analysis_result['veracity_signals'])
        self.assertIsNone(analysis_result['lightweight_nigerian_bias_assessment'])
        self.assertIsNone(analysis_result.get('detailed_sub_analyses'))

    def test_analyze_core_solution_structure_success(self):
        self.mock_analyzer_sentiment.return_value = {'label': 'negative', 'confidence': 0.88}
        self.mock_analyzer_emotion.return_value = {'label': 'anger', 'confidence': 0.75, 'is_emotionally_charged': True, 'manipulation_risk': 'medium'}

        # Updated mock for new_bias_analyzer.analyze
        self.mock_new_bias_analyzer_analyze.return_value = {
            "overall_bias": {"is_biased": True, "confidence": 0.85, "level": "high"},
            "bias_details": {
                "type": "political bias", "type_confidence": 0.92, "nigerian_context": True,
                "specific_detections": [
                    {"term": "pdp", "category": "political", "bias_level": "high", "confidence": 0.9, "direction": "negative", "explanation": "Explicitly biased", "context": "pdp is bad"}
                ]
            },
            "clickbait": {"is_clickbait": True, "confidence": 0.7, "level": "medium", "detected_patterns": [], "explanation": ""}, # For manipulation_analysis
            "recommendations": [], "technical_details": {}
        }

        self.mock_analyzer_patterns.return_value = {
            'nigerian_patterns': {'has_triggers': True, 'has_clickbait': True, 'trigger_matches': ['pdp']}, # For manipulation_analysis and LW assessment consistency
            'fake_news': {'detected': True, 'details': {'risk_level': 'high', 'matched_phrases': ['breaking!'], 'is_clickbait': True, 'fake_matches':['breaking!']}},
            'viral_manipulation': {'is_potentially_viral': True, 'engagement_bait_score': 0.8, 'sensationalism_score': 0.7} # For manipulation_analysis
        }
        self.mock_analyzer_trust_calc.return_value = {'score': 25, 'indicator': '🔴 Risky', 'explanation': ['Risky content.'], 'tip': 'Verify carefully.'}

        result = analyse("Test text for core solution structure", include_patterns=True, include_detailed_results=False)
        self.assertEqual(result['trust_score'], 25)

        # Updated assertion for lightweight_nigerian_bias_assessment
        expected_lw_assessment = {
            "count": 1,
            "inferred_bias_type": "political",
            "has_specific_nigerian_bias": True,
            "matched_keywords": ["pdp"]
            # "categories_present" was removed in the previous step's implementation of lightweight_nigerian_bias_info
            # Let's re-add it to the prompt's spec for lightweight_nigerian_bias_info if it's desired.
            # For now, I'll match the implementation from Step 1's prompt (which didn't have categories_present)
            # If it IS desired, the implementation in analyzer.py needs:
            # "categories_present": list(set(d.get('category') for d in nd if isinstance(d, dict) and d.get('category'))),
        }
        # Current implementation of lightweight_nigerian_bias_info in analyzer.py (from previous steps):
        # nd = bias_result_ml.get('nigerian_detections', [])
        # lightweight_nigerian_bias_info = {
        #     "count": len(nd),
        #     "inferred_bias_type": nd[0]['category'] if nd and isinstance(nd, list) and len(nd) > 0 and isinstance(nd[0], dict) else "No specific patterns detected",
        #     "matched_keywords": list(set(d.get('term') for d in nd if isinstance(d, dict) and d.get('term')))[:3],
        #     "has_specific_nigerian_bias": bool(nd)
        # }
        # To include "categories_present", it should be:
        # lightweight_nigerian_bias_info = {
        #     "count": len(nd),
        #     "inferred_bias_type": nd[0]['category'] if nd and isinstance(nd, list) and len(nd) > 0 and isinstance(nd[0], dict) else "No specific patterns detected",
        #     "categories_present": list(set(d.get('category') for d in nd if isinstance(d, dict) and d.get('category'))), # ADDED
        #     "matched_keywords": list(set(d.get('term') for d in nd if isinstance(d, dict) and d.get('term')))[:3],
        #     "has_specific_nigerian_bias": bool(nd)
        # }
        # Assuming the prompt for THIS step implies categories_present should be there, I'll adjust the expected.
        # And will need a follow-up to adjust analyzer.py if this test fails.
        # The prompt for *this* test step (Step 4) *does* include categories_present in its example.
        expected_lw_assessment_updated = {
            "count": 1,
            "inferred_bias_type": "political",
            "categories_present": ["political"], # This is in the prompt for this test
            "has_specific_nigerian_bias": True,
            "matched_keywords": ["pdp"]
        }
        self.assertEqual(result['lightweight_nigerian_bias_assessment'], expected_lw_assessment_updated)

        self.assertEqual(result['tone_analysis'], {'primary_tone': 'anger', 'is_emotionally_charged': True, 'emotional_manipulation_risk': 'medium', 'sentiment_label': 'negative', 'sentiment_confidence': 0.88})

        # Updated assertions for bias_analysis
        self.assertEqual(result['bias_analysis']['primary_bias_type'], 'political bias') # from bias_details.type
        self.assertEqual(result['bias_analysis']['bias_strength_label'], 'high') # from overall_bias.level
        self.assertEqual(result['bias_analysis']['ml_model_confidence'], 0.92) # from bias_details.type_confidence
        # Source logic: ml_bias_is_specific is True. lw_bias_is_specific is True (due to nigerian_detections).
        # ml_detected_bias_type = "political bias". lw_inferred_bias_type = "political"
        # These are not exactly equal ("political bias" vs "political").
        # The logic is: `if lw_bias_is_specific and primary_bias_type == lw_inferred_bias_type.strip().lower():`
        # "political bias" == "political" is False. So source should be "ML Model".
        self.assertEqual(result['bias_analysis']['source_of_primary_bias'], 'ML Model')

        self.assertEqual(result['manipulation_analysis'], {'is_clickbait': True, 'engagement_bait_score': 0.8, 'sensationalism_score': 0.7})
        self.assertEqual(result['veracity_signals'], {'fake_news_risk_level': 'high', 'matched_suspicious_phrases': ['breaking!']})
        self.assertNotIn('detailed_sub_analyses', result)

    def test_bias_analysis_source_of_primary_bias(self):
        self.mock_analyzer_sentiment.return_value = {}
        self.mock_analyzer_emotion.return_value = {}
        self.mock_analyzer_patterns.return_value = {'nigerian_patterns': {}, 'fake_news': {'details': {}}, 'viral_manipulation': {}} # No pattern influence for these sub-tests
        self.mock_analyzer_trust_calc.return_value = {'tip': 'A tip'}

        # Scenario 1: ML specific, Pattern (Nigerian Detections) not
        self.mock_new_bias_analyzer_analyze.return_value = {
            "overall_bias": {"is_biased": True, "confidence": 0.8, "level": "medium"},
            "bias_details": {"type": "political", "type_confidence": 0.8, "nigerian_context": False, "specific_detections": []},
            "clickbait": {}, "recommendations": [], "technical_details": {}
        }
        result = analyse("Text", include_patterns=True) # include_patterns=True to activate lw_bias_is_specific logic path
        self.assertEqual(result['bias_analysis']['source_of_primary_bias'], 'ML Model')
        self.assertEqual(result['bias_analysis']['primary_bias_type'], 'political')

        # Scenario 2: ML neutral, Pattern (Nigerian Detections) specific
        self.mock_new_bias_analyzer_analyze.return_value = {
            "overall_bias": {"is_biased": False, "confidence": 0.9, "level": "low"}, # ML says no bias
            "bias_details": {"type": "neutral", "type_confidence": 0.9, "nigerian_context": True,
                             "specific_detections": [{"term": "igbo", "category": "ethnic", "bias_level": "medium"}]},
            "clickbait": {}, "recommendations": [], "technical_details": {}
        }
        result = analyse("Text", include_patterns=True)
        self.assertEqual(result['bias_analysis']['source_of_primary_bias'], 'Pattern Analysis (Nigerian Context)')
        self.assertEqual(result['bias_analysis']['primary_bias_type'], 'ethnic') # from specific_detections[0]['category']

        # Scenario 4: Both ML and Pattern are specific and same
        # For "ML Model and Pattern Analysis", ml_bias_details.type should match category from nigerian_detections
        self.mock_new_bias_analyzer_analyze.return_value = {
            "overall_bias": {"is_biased": True, "confidence": 0.85, "level": "high"},
            "bias_details": {"type": "ethnic bias", "type_confidence": 0.85, "nigerian_context": True, # type is "ethnic bias"
                             "specific_detections": [{"term": "igbo", "category": "ethnic bias", "bias_level": "high"}]}, # category is "ethnic bias"
            "clickbait": {}, "recommendations": [], "technical_details": {}
        }
        result = analyse("Text", include_patterns=True)
        self.assertEqual(result['bias_analysis']['source_of_primary_bias'], 'ML Model and Pattern Analysis')
        self.assertEqual(result['bias_analysis']['primary_bias_type'], 'ethnic bias')

    def test_analyze_detailed_results_core_solution(self):
        # Reset to default neutral mocks for this test by calling setUp's defaults again if necessary, or ensure defaults are neutral
        self.mock_new_bias_analyzer_analyze.return_value = { # Default neutral from setUp
            "text": "Test text", "timestamp": "some_timestamp",
            "overall_bias": {"is_biased": False, "confidence": 0.1, "level": "minimal"},
            "bias_details": {"type": "neutral", "type_confidence": 0.95, "nigerian_context": False, "specific_detections": []},
            "clickbait": {"is_clickbait": False, "confidence": 0.1, "level": "low", "detected_patterns": [], "explanation": ""},
            "recommendations": [], "technical_details": {"base_model_score": 0.1, "explanation": "Base model analysis"}
        }
        self.mock_analyzer_patterns.return_value = { # Default neutral patterns
            'nigerian_patterns': {'has_triggers': False, 'has_clickbait': False, 'trigger_matches': []},
            'fake_news': {'detected': False, 'details': {'risk_level': 'low', 'matched_phrases': [], 'is_clickbait': False, 'fake_matches': []}},
            'viral_manipulation': {'is_potentially_viral': False, 'engagement_bait_score': 0.1, 'sensationalism_score': 0.1}
        }


        result = analyse("Test for detailed results", include_patterns=True, include_detailed_results=True)
        self.assertIn('detailed_sub_analyses', result)
        self.assertIn('bias', result['detailed_sub_analyses'])
        # The content of 'bias' is the output of _analyze_bias_safe, which now includes 'raw_new_analyzer_result'
        self.assertIn('raw_new_analyzer_result', result['detailed_sub_analyses']['bias'])
        self.assertEqual(result['detailed_sub_analyses']['bias']['raw_new_analyzer_result']['overall_bias']['level'], 'minimal')
        self.assertIn('lightweight_nigerian_bias', result['detailed_sub_analyses'])
        expected_lw_assessment_detailed = { # Based on no nigerian_detections from the mock
            "count": 0, "inferred_bias_type": "No specific patterns detected",
            "has_specific_nigerian_bias": False, "matched_keywords": []
            # "categories_present": [] # This would be added if the analyzer.py is updated
        }
        # Re-evaluating the "categories_present" for detailed view, it should be present if the main one is.
        expected_lw_assessment_detailed_updated = {
            "count": 0, "inferred_bias_type": "No specific patterns detected",
            "categories_present": [], # Adding for consistency with the other test
            "has_specific_nigerian_bias": False, "matched_keywords": []
        }
        self.assertEqual(result['detailed_sub_analyses']['lightweight_nigerian_bias'], expected_lw_assessment_detailed_updated)


    def test_analyze_general_exception_core_solution_structure(self):
        self.mock_analyzer_sentiment.side_effect = Exception("Simulated component failure") # This mock is still fine
        analysis_result = analyse("Some text that will cause an error.")
        self.assertEqual(analysis_result.get('indicator'), 'Error')
        self.assertIsNone(analysis_result['tone_analysis'])
        self.assertIsNone(analysis_result['bias_analysis'])
        self.assertIsNone(analysis_result['manipulation_analysis'])
        self.assertIsNone(analysis_result['veracity_signals'])


    # Removed test_quick_analyze_core_solution_structure

    @patch('biaslens.patterns.ViralityDetector.analyze_virality')
    @patch('biaslens.patterns.NigerianPatterns.analyze_patterns')
    def test_analyze_with_problematic_fake_news_patterns_no_typeerror(self, mock_nigerian_patterns, mock_virality_detector):
        """
        Tests that analyze() completes without TypeError when FakeNewsDetector processes patterns
        that previously caused issues (due to list of tuples/strings).
        This test allows the actual FakeNewsDetector.detect() and TrustScoreCalculator.calculate() to run.
        """
        test_text_with_fake_patterns = "breaking news: secret plan exposed. what they don't want you to know"

        # Setup mocks for components not directly under test for this specific scenario
        # Use class-level mocks for sentiment, emotion, new_bias_analyzer - they are set up to be neutral
        self.mock_analyzer_sentiment.return_value = {'label': 'neutral', 'confidence': 0.9}
        self.mock_analyzer_emotion.return_value = {'label': 'neutral', 'confidence': 0.8, 'is_emotionally_charged': False, 'manipulation_risk': 'low'}
        self.mock_new_bias_analyzer_analyze.return_value = { # Neutral bias result
            "overall_bias": {"is_biased": False, "confidence": 0.1, "level": "minimal"},
            "bias_details": {"type": "neutral", "type_confidence": 0.95, "nigerian_context": False, "specific_detections": []},
            "clickbait": {}, "recommendations": [], "technical_details": {}
        }

        # Mock sub-components of _analyze_patterns_safe, allowing FakeNewsDetector.detect to run
        mock_nigerian_patterns.return_value = {'has_triggers': False, 'has_clickbait': False, 'trigger_matches': []}
        mock_virality_detector.return_value = {'has_viral_patterns': False, 'viral_matches': [], 'viral_score': 0, 'manipulation_level': 'low'}

        # Crucially, self.mock_analyzer_patterns (which mocks _analyze_patterns_safe) needs to be bypassed for FakeNewsDetector
        # The patches above handle its sub-components.
        # We also need _calculate_trust_score_safe to run its actual logic.
        # So, we temporarily stop its mock from setUp and restore it later.
        self.patcher_analyzer_trust_calc.stop() # Stop the mock for _calculate_trust_score_safe
        self.patcher_analyzer_patterns.stop() # Stop the mock for _analyze_patterns_safe

        try:
            # Analyze the text
            # The global analyse() function creates its own BiasLensAnalyzer instance.
            # To test the instance methods with specific unmocked parts, we need to call it on self.analyzer or ensure global uses the same patches.
            # For simplicity here, and since analyse() is a convenience wrapper, we'll test it directly.
            # The patches on staticmethods (NigerianPatterns.analyze_patterns etc.) will apply regardless of instance.

            result = analyse(test_text_with_fake_patterns, include_patterns=True, include_detailed_results=False)

            # Primary assertion: No TypeError should have occurred. If it did, the test would fail before this.
            self.assertIsNotNone(result, "Analysis result should not be None.")
            self.assertNotEqual(result.get('indicator'), 'Error', f"Analysis returned an error: {result.get('explanation')}")

            self.assertIsInstance(result.get('explanation'), list, "Explanation should be a list.")

            # Check for expected fake news matches in the explanation (TrustScoreCalculator adds this)
            # Expected matches from "breaking news: secret plan exposed. what they don't want you to know":
            # "Breaking", "secret plan", "what they don't want you to know"
            # The explanation formatting might vary, so check for key phrases.
            explanation_text = " ".join(result.get('explanation', [])).lower()
            self.assertIn("suspicious phrases", explanation_text, "Explanation should mention suspicious phrases.")
            self.assertIn("breaking", explanation_text, "Explanation should contain 'breaking'.")
            self.assertIn("secret plan", explanation_text, "Explanation should contain 'secret plan'.")
            self.assertIn("what they don't want you to know", explanation_text, "Explanation should contain 'what they don't want you to know'.")

            # Check that fake_matches in detailed_results (if requested) would be a list of strings
            # This part requires include_detailed_results=True
            detailed_result = analyse(test_text_with_fake_patterns, include_patterns=True, include_detailed_results=True)
            self.assertIn('detailed_sub_analyses', detailed_result)
            self.assertIn('patterns', detailed_result['detailed_sub_analyses'])
            self.assertIn('fake_news', detailed_result['detailed_sub_analyses']['patterns'])
            fake_news_details = detailed_result['detailed_sub_analyses']['patterns']['fake_news']
            self.assertIn('fake_matches', fake_news_details)
            self.assertIsInstance(fake_news_details['fake_matches'], list, "fake_matches should be a list.")
            if fake_news_details['fake_matches']:
                self.assertTrue(all(isinstance(match, str) for match in fake_news_details['fake_matches']), "All items in fake_matches should be strings.")

            # Example: Check actual content of fake_matches if needed
            expected_matches = ["Breaking", "secret plan", "what they don't want you to know"]
            # Sort both for comparison if order doesn't matter, or check for subset/superset
            self.assertTrue(set(expected_matches).issubset(set(fake_news_details['fake_matches'])))


        finally:
            # Restore the mocks
            self.patcher_analyzer_trust_calc.start()
            self.patcher_analyzer_patterns.start()


if __name__ == '__main__':
    unittest.main()
