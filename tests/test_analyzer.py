import unittest
from unittest.mock import patch, MagicMock
from biaslens.analyzer import BiasLensAnalyzer, analyze, quick_analyze
from biaslens.bias import NigerianBiasEnhancer
from biaslens.trust import TrustScoreCalculator

class TestNigerianBiasEnhancer(unittest.TestCase):
    # This class remains unchanged
    def setUp(self):
        self.enhancer = NigerianBiasEnhancer()
    def test_lightweight_no_nigerian_keywords(self):
        text = "This is a generic sentence about global news."
        expected = {"inferred_bias_type": "No specific patterns detected", "bias_category": None, "bias_target": None, "matched_keywords": []}
        self.assertEqual(self.enhancer.get_lightweight_bias_assessment(text), expected)
    def test_lightweight_political_bias_apc_pro(self):
        text = "APC is doing a great job, they are the best for Nigeria."
        result = self.enhancer.get_lightweight_bias_assessment(text)
        self.assertEqual(result["inferred_bias_type"], "Pro-APC political bias")
        self.assertEqual(result["bias_category"], "political")
        self.assertEqual(result["bias_target"], "APC")
        self.assertIn("apc", result["matched_keywords"])
    def test_lightweight_political_bias_pdp_anti(self):
        text = "The PDP party is so corrupt and bad for the country."
        result = self.enhancer.get_lightweight_bias_assessment(text)
        self.assertEqual(result["inferred_bias_type"], "Anti-PDP political bias")
        self.assertEqual(result["bias_category"], "political")
        self.assertEqual(result["bias_target"], "PDP")
        self.assertIn("pdp", result["matched_keywords"])
    def test_lightweight_political_bias_obi_neutral_mention(self):
        text = "Peter Obi is a candidate."
        result = self.enhancer.get_lightweight_bias_assessment(text)
        self.assertEqual(result["inferred_bias_type"], "Peter Obi political bias")
        self.assertEqual(result["bias_category"], "political")
        self.assertEqual(result["bias_target"], "Peter Obi")
        self.assertIn("obi", result["matched_keywords"])
    def test_lightweight_ethnic_bias_igbo_derogatory(self):
        text = "These nyamiri people are everywhere."
        result = self.enhancer.get_lightweight_bias_assessment(text)
        self.assertEqual(result["inferred_bias_type"], "Anti-Igbo ethnic bias")
        self.assertEqual(result["bias_category"], "ethnic")
        self.assertEqual(result["bias_target"], "Igbo")
        self.assertIn("nyamiri", result["matched_keywords"])
    def test_lightweight_ethnic_bias_hausa_general_anti(self):
        text = "The Hausa are too dominating."
        result = self.enhancer.get_lightweight_bias_assessment(text)
        self.assertEqual(result["inferred_bias_type"], "Anti-Hausa ethnic bias")
        self.assertEqual(result["bias_category"], "ethnic")
        self.assertEqual(result["bias_target"], "Hausa")
        self.assertIn("hausa", result["matched_keywords"])
    def test_lightweight_religious_bias_anti_muslim_jihad(self):
        text = "Their jihad is bad."
        result = self.enhancer.get_lightweight_bias_assessment(text)
        self.assertEqual(result["inferred_bias_type"], "Anti-Islamic religious bias")
        self.assertEqual(result["bias_category"], "religious")
        self.assertEqual(result["bias_target"], "Jihad")
        self.assertIn("jihad", result["matched_keywords"])
    def test_lightweight_regional_bias_arewa_pro(self):
        text = "Arewa is the future, all good things come from Arewa."
        result = self.enhancer.get_lightweight_bias_assessment(text)
        self.assertEqual(result["inferred_bias_type"], "Pro-Northern regional bias")
        self.assertEqual(result["bias_category"], "regional")
        self.assertEqual(result["bias_target"], "Arewa")
        self.assertIn("arewa", result["matched_keywords"])
    def test_lightweight_nigerian_context_no_specific_bias(self):
        text_with_context = "The yoruba culture is interesting. Many igbo people live in Lagos."
        result_with_context = self.enhancer.get_lightweight_bias_assessment(text_with_context)
        self.assertEqual(result_with_context["inferred_bias_type"], "Anti-Yoruba ethnic bias")
        self.assertEqual(result_with_context["bias_category"], "ethnic")
        self.assertEqual(result_with_context["bias_target"], "Yoruba")
        self.assertTrue(all(k in result_with_context["matched_keywords"] for k in ["yoruba", "igbo"]))
    def test_lightweight_multiple_keywords_one_triggers_specific_bias(self):
        text = "PDP is bad, and by the way, the north is cold."
        result = self.enhancer.get_lightweight_bias_assessment(text)
        self.assertEqual(result["inferred_bias_type"], "Anti-PDP political bias")
        self.assertEqual(result["bias_category"], "political")
        self.assertEqual(result["bias_target"], "PDP")
        self.assertIn("pdp", result["matched_keywords"])
        self.assertIn("north", result["matched_keywords"])
    def test_lightweight_context_detected_unclear_bias(self):
        text = "Some people are lazy in Nigeria."
        result = self.enhancer.get_lightweight_bias_assessment(text)
        self.assertEqual(result["inferred_bias_type"], "Nigerian context detected, specific bias type unclear from patterns")
        self.assertEqual(result["bias_category"], "ethnic")
        self.assertIsNone(result["bias_target"])
        self.assertIn("lazy", result["matched_keywords"])

class TestBiasLensAnalyzer(unittest.TestCase):

    def setUp(self):
        # Mock for quick_analyze's LWB enhancer (on global_analyzer)
        self.patcher_enhancer_quick = patch('biaslens.analyzer._global_analyzer._nigerian_bias_enhancer')
        self.mock_enhancer_for_quick_analyze = self.patcher_enhancer_quick.start()

        # Default for quick_analyze LWB
        self.mock_enhancer_for_quick_analyze.get_lightweight_bias_assessment.return_value = {
            "inferred_bias_type": "No specific patterns detected",
            "bias_category": None, "bias_target": None, "matched_keywords": []
        }

        # Mocks for BiasLensAnalyzer instance methods (used by 'analyze' instance method)
        self.patcher_analyzer_sentiment = patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
        self.mock_analyzer_sentiment = self.patcher_analyzer_sentiment.start()

        self.patcher_analyzer_emotion = patch('biaslens.analyzer.BiasLensAnalyzer._analyze_emotion_safe')
        self.mock_analyzer_emotion = self.patcher_analyzer_emotion.start()

        self.patcher_analyzer_bias_ml = patch('biaslens.analyzer.BiasLensAnalyzer._analyze_bias_safe')
        self.mock_analyzer_bias_ml = self.patcher_analyzer_bias_ml.start()

        self.patcher_analyzer_patterns = patch('biaslens.analyzer.BiasLensAnalyzer._analyze_patterns_safe')
        self.mock_analyzer_patterns = self.patcher_analyzer_patterns.start()

        self.patcher_analyzer_lw_enhancer_for_analyze = patch('biaslens.analyzer.BiasLensAnalyzer._nigerian_bias_enhancer')
        self.mock_analyzer_lw_enhancer_for_analyze = self.patcher_analyzer_lw_enhancer_for_analyze.start()

        self.patcher_analyzer_trust_calc = patch('biaslens.analyzer.BiasLensAnalyzer._calculate_trust_score_safe')
        self.mock_analyzer_trust_calc = self.patcher_analyzer_trust_calc.start()

        self.patcher_analyzer_overall_assessment = patch('biaslens.analyzer.BiasLensAnalyzer._generate_overall_assessment')
        self.mock_analyzer_overall_assessment = self.patcher_analyzer_overall_assessment.start()

        # Default mock returns for 'analyze' dependencies (can be overridden in specific tests)
        self.mock_analyzer_sentiment.return_value = {'label': 'neutral', 'confidence': 0.9}
        self.mock_analyzer_emotion.return_value = {'label': 'neutral', 'confidence': 0.8, 'is_emotionally_charged': False, 'manipulation_risk': 'low'}
        self.mock_analyzer_bias_ml.return_value = {'flag': False, 'label': 'Neutral', 'type_analysis': {'type': 'neutral', 'confidence': 0.95}}
        self.mock_analyzer_patterns.return_value = {
            'nigerian_patterns': {'has_triggers': False, 'has_clickbait': False},
            'fake_news': {'detected': False, 'details': {'risk_level': 'low', 'matched_phrases': [], 'is_clickbait': False, 'fake_matches': []}}, # Added fake_matches
            'viral_manipulation': {'is_potentially_viral': False, 'engagement_bait_score': 0.1, 'sensationalism_score': 0.1}
        }
        self.mock_analyzer_lw_enhancer_for_analyze.get_lightweight_bias_assessment.return_value = {
            "inferred_bias_type": "No specific patterns detected", "bias_category": None,
            "bias_target": None, "matched_keywords": []
        }
        self.mock_analyzer_trust_calc.return_value = {
            'score': 80, 'indicator': '🟢 Trusted',
            'explanation': ['Generally trustworthy.'], 'tip': 'A general tip.'
        }
        self.mock_analyzer_overall_assessment.return_value = {}


    def tearDown(self):
        self.patcher_enhancer_quick.stop()
        self.patcher_analyzer_sentiment.stop()
        self.patcher_analyzer_emotion.stop()
        self.patcher_analyzer_bias_ml.stop()
        self.patcher_analyzer_patterns.stop()
        self.patcher_analyzer_lw_enhancer_for_analyze.stop()
        self.patcher_analyzer_trust_calc.stop()
        self.patcher_analyzer_overall_assessment.stop()

    def test_quick_analyze_empty_text_core_solution_structure(self):
        results = quick_analyze("")
        self.assertEqual(results.get('indicator'), 'Error')
        self.assertEqual(results.get('explanation'), "Empty text provided.")
        self.assertEqual(results.get('tip'), "No text was provided. Please input text for analysis. For a detailed breakdown of potential biases and manipulation, use the full analyze() function once text is provided.")
        self.assertIsNone(results.get('score'))
        self.assertIsNone(results.get('tone_analysis'))
        self.assertIsNone(results.get('bias_analysis'))
        self.assertIsNone(results.get('manipulation_analysis'))
        self.assertIsNone(results.get('veracity_signals'))
        # Old direct fields should not be present
        self.assertNotIn('inferred_bias_type', results)

    # ... (analyze method tests remain unchanged from previous step) ...
    def test_analyze_empty_text_core_solution_structure(self):
        analysis_result = analyze("")
        self.assertEqual(analysis_result['indicator'], 'Error')
        self.assertEqual(analysis_result['explanation'], ["Empty or invalid text provided"])
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
        self.mock_analyzer_bias_ml.return_value = {'flag': True, 'label': 'Strong Bias Detected', 'type_analysis': {'type': 'confirmation_bias', 'confidence': 0.92}}
        self.mock_analyzer_patterns.return_value = {
            'nigerian_patterns': {'has_triggers': True, 'has_clickbait': True},
            'fake_news': {'detected': True, 'details': {'risk_level': 'high', 'matched_phrases': ['breaking!'], 'is_clickbait': True, 'fake_matches':['breaking!']}},
            'viral_manipulation': {'is_potentially_viral': True, 'engagement_bait_score': 0.8, 'sensationalism_score': 0.7}
        }
        mock_lw_assessment_for_analyze = {"inferred_bias_type": "Anti-PDP political bias", "bias_category": "political", "bias_target": "PDP", "matched_keywords": ["pdp", "bad"]}
        self.mock_analyzer_lw_enhancer_for_analyze.get_lightweight_bias_assessment.return_value = mock_lw_assessment_for_analyze
        self.mock_analyzer_trust_calc.return_value = {'score': 25, 'indicator': '🔴 Risky', 'explanation': ['Risky content.'], 'tip': 'Verify carefully.'}

        result = analyze("Test text for core solution structure", include_patterns=True, include_detailed_results=False)
        self.assertEqual(result['trust_score'], 25)
        self.assertEqual(result['lightweight_nigerian_bias_assessment'], mock_lw_assessment_for_analyze)
        self.assertEqual(result['tone_analysis'], {'primary_tone': 'anger', 'is_emotionally_charged': True, 'emotional_manipulation_risk': 'medium', 'sentiment_label': 'negative', 'sentiment_confidence': 0.88})
        self.assertEqual(result['bias_analysis']['primary_bias_type'], 'confirmation_bias')
        self.assertEqual(result['bias_analysis']['bias_strength_label'], 'Strong Bias Detected')
        self.assertEqual(result['bias_analysis']['ml_model_confidence'], 0.92)
        self.assertEqual(result['bias_analysis']['source_of_primary_bias'], 'ML Model')
        self.assertEqual(result['manipulation_analysis'], {'is_clickbait': True, 'engagement_bait_score': 0.8, 'sensationalism_score': 0.7})
        self.assertEqual(result['veracity_signals'], {'fake_news_risk_level': 'high', 'matched_suspicious_phrases': ['breaking!']})
        self.assertNotIn('detailed_sub_analyses', result)

    def test_bias_analysis_source_of_primary_bias(self):
        # ... (This test remains largely the same, checking result['bias_analysis']['source_of_primary_bias']) ...
        self.mock_analyzer_sentiment.return_value = {} # Ensure other mocks are set
        self.mock_analyzer_emotion.return_value = {}
        self.mock_analyzer_patterns.return_value = {'nigerian_patterns': {}, 'fake_news': {'details': {}}, 'viral_manipulation': {}}
        self.mock_analyzer_trust_calc.return_value = {'tip': 'A tip'}


        # Scenario 1: ML Model is specific
        self.mock_analyzer_bias_ml.return_value = {'flag': True, 'label': 'Biased', 'type_analysis': {'type': 'political', 'confidence': 0.8}}
        self.mock_analyzer_lw_enhancer_for_analyze.get_lightweight_bias_assessment.return_value = {"inferred_bias_type": "No specific patterns detected"}
        result = analyze("Text", include_patterns=True)
        self.assertEqual(result['bias_analysis']['source_of_primary_bias'], 'ML Model')
        self.assertEqual(result['bias_analysis']['primary_bias_type'], 'political')

        # Scenario 2: ML Model is neutral, Pattern is specific
        self.mock_analyzer_bias_ml.return_value = {'flag': False, 'label': 'Neutral', 'type_analysis': {'type': 'neutral', 'confidence': 0.9}}
        self.mock_analyzer_lw_enhancer_for_analyze.get_lightweight_bias_assessment.return_value = {"inferred_bias_type": "Anti-Igbo ethnic bias", "bias_category": "ethnic"}
        result = analyze("Text", include_patterns=True)
        self.assertEqual(result['bias_analysis']['source_of_primary_bias'], 'Pattern Analysis (Nigerian Context)')
        self.assertEqual(result['bias_analysis']['primary_bias_type'], 'anti-igbo ethnic bias')

        # Scenario 4: Both ML and Pattern are specific and same
        self.mock_analyzer_bias_ml.return_value = {'flag': True, 'label': 'Biased', 'type_analysis': {'type': 'anti-igbo ethnic bias', 'confidence': 0.85}}
        self.mock_analyzer_lw_enhancer_for_analyze.get_lightweight_bias_assessment.return_value = {"inferred_bias_type": "Anti-Igbo ethnic bias", "bias_category": "ethnic"}
        result = analyze("Text", include_patterns=True)
        self.assertEqual(result['bias_analysis']['source_of_primary_bias'], 'ML Model and Pattern Analysis')
        self.assertEqual(result['bias_analysis']['primary_bias_type'], 'anti-igbo ethnic bias')

    def test_analyze_detailed_results_core_solution(self):
        # Using default mocks from setUp which represent a neutral case
        result = analyze("Test for detailed results", include_patterns=True, include_detailed_results=True)
        self.assertIn('detailed_sub_analyses', result)
        # ... (assertions for content of detailed_sub_analyses remain same) ...

    def test_analyze_general_exception_core_solution_structure(self):
        self.mock_analyzer_sentiment.side_effect = Exception("Simulated component failure")
        analysis_result = analyze("Some text that will cause an error.")
        self.assertEqual(analysis_result.get('indicator'), 'Error')
        # ... (assertions for None fields remain same for new structure) ...
        self.assertIsNone(analysis_result['tone_analysis'])
        self.assertIsNone(analysis_result['bias_analysis'])
        self.assertIsNone(analysis_result['manipulation_analysis'])
        self.assertIsNone(analysis_result['veracity_signals'])


    # --- Tests for quick_analyze with new Core Solution structure ---
    @patch('biaslens.analyzer.NigerianPatterns.analyze_patterns')
    @patch('biaslens.analyzer.FakeNewsDetector.detect')
    def test_quick_analyze_core_solution_structure(self, mock_fake_news_detect, mock_nigerian_patterns):
        with patch('biaslens.analyzer._global_analyzer._analyze_sentiment_safe') as mock_sentiment_quick:
            # Setup mocks for quick_analyze components
            mock_sentiment_quick.return_value = {'label': 'positive', 'confidence': 0.95}
            mock_nigerian_patterns.return_value = {'has_triggers': False, 'has_clickbait': True} # Clickbait detected
            mock_fake_news_detect.return_value = (True, {'risk_level': 'medium', 'fake_matches': ['fake news phrase']})

            lwb_info_mock = {
                "inferred_bias_type": "Pro-Test Party", "bias_category": "political",
                "bias_target": "Test Party", "matched_keywords": ["test party", "best"]
            }
            self.mock_enhancer_for_quick_analyze.get_lightweight_bias_assessment.return_value = lwb_info_mock

            results = quick_analyze("This is a quick test with findings.")

            # Standard top-level fields
            self.assertIn('score', results)
            self.assertIn('indicator', results)
            self.assertIn('explanation', results)
            self.assertIsInstance(results['explanation'], str)
            self.assertTrue("Specific patterns suggest: Pro-Test Party." in results['explanation'])
            self.assertIn(results['tip'], TrustScoreCalculator.DID_YOU_KNOW_TIPS)

            # New structured fields
            self.assertIn('tone_analysis', results)
            self.assertEqual(results['tone_analysis'], {'sentiment_label': 'positive', 'sentiment_confidence': 0.95})

            self.assertIn('bias_analysis', results)
            expected_bias_analysis = {
                "primary_bias_type": "Pro-Test Party", "bias_category": "political",
                "bias_target": "Test Party", "matched_keywords": ["test party", "best"]
            }
            self.assertEqual(results['bias_analysis'], expected_bias_analysis)

            self.assertIn('manipulation_analysis', results)
            self.assertEqual(results['manipulation_analysis'], {'is_clickbait': True})

            self.assertIn('veracity_signals', results)
            expected_veracity = {'fake_news_risk_level': 'medium', 'matched_suspicious_phrases': ['fake news phrase']}
            self.assertEqual(results['veracity_signals'], expected_veracity)

            # Ensure old flat keys are not present
            self.assertNotIn('inferred_bias_type', results)
            self.assertNotIn('bias_category', results)
            self.assertNotIn('bias_target', results)
            self.assertNotIn('matched_keywords', results)


if __name__ == '__main__':
    unittest.main()
