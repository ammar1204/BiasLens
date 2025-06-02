import unittest
from unittest.mock import patch, MagicMock
from biaslens.analyzer import BiasLensAnalyzer, analyze, quick_analyze
from biaslens.bias import NigerianBiasEnhancer
from biaslens.trust import TrustScoreCalculator # Added for DID_YOU_KNOW_TIPS

class TestNigerianBiasEnhancer(unittest.TestCase):
    def setUp(self):
        self.enhancer = NigerianBiasEnhancer()

    def test_lightweight_no_nigerian_keywords(self):
        text = "This is a generic sentence about global news."
        expected = {
            "inferred_bias_type": "No specific patterns detected",
            "bias_category": None,
            "bias_target": None,
            "matched_keywords": []
        }
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
        text = "Peter Obi is a candidate." # No strong sentiment words
        result = self.enhancer.get_lightweight_bias_assessment(text)
        self.assertEqual(result["inferred_bias_type"], "Peter Obi political bias") # Default from map
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
        # Assuming "Anti-Hausa ethnic bias" is the default for "hausa"
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
        self.patcher_enhancer = patch('biaslens.analyzer._global_analyzer._nigerian_bias_enhancer')
        self.mock_enhancer_for_quick_analyze = self.patcher_enhancer.start()
        
        self.mock_enhancer_for_quick_analyze.get_lightweight_bias_assessment.return_value = {
            "inferred_bias_type": "No specific patterns detected",
            "bias_category": None, "bias_target": None, "matched_keywords": []
        }

    def tearDown(self):
        self.patcher_enhancer.stop()

    def test_quick_analyze_empty_text(self):
        results = quick_analyze("")
        self.assertIsNotNone(results)
        self.assertIsNone(results.get('score'))
        self.assertEqual(results.get('indicator'), 'Error')
        self.assertEqual(results.get('explanation'), "Empty text provided.")
        self.assertEqual(results.get('tip'), "No text was provided. Please input text for analysis. For a detailed breakdown of potential biases and manipulation, use the full analyze() function once text is provided.")
        self.assertIsNone(results.get('inferred_bias_type'))
        self.assertIsNone(results.get('bias_category'))
        self.assertIsNone(results.get('bias_target'))
        self.assertEqual(results.get('matched_keywords'), [])

    def test_analyze_empty_text(self):
        """Test analyze with empty string input - check new tip."""
        analysis = analyze("")
        self.assertIsNotNone(analysis)
        self.assertIsNone(analysis['trust_score'])
        self.assertEqual(analysis['indicator'], 'Error')
        self.assertEqual(analysis['explanation'], ["Empty or invalid text provided"])
        self.assertEqual(analysis['tip'], "Analysis failed: No text was provided. Please input text for analysis.")

    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
    @patch('biaslens.analyzer.NigerianPatterns.analyze_patterns')
    @patch('biaslens.analyzer.FakeNewsDetector.detect')
    def test_quick_analyze_valid_text_random_tip(self,
                                               mock_fake_news_detect,
                                               mock_nigerian_patterns,
                                               mock_sentiment_safe):
        
        mock_sentiment_safe.return_value = {'label': 'neutral', 'confidence': 0.9, 'all_scores': {}, 'bias_indicator': False}
        mock_nigerian_patterns.return_value = {'has_triggers': False, 'has_clickbait': False, 'trigger_score':0, 'clickbait_score':0, 'total_flags':0}
        mock_fake_news_detect.return_value = (False, {'fake_matches':[], 'credibility_flags':[], 'fake_score':0, 'credibility_score':0, 'risk_level':'minimal', 'total_flags':0})
        
        # Default mock from setUp for get_lightweight_bias_assessment is "No specific patterns detected"
        
        results = quick_analyze("This is a test sentence for random tip.")
        self.assertIsNotNone(results)
        self.assertIn('score', results)
        self.assertIn('indicator', results)
        self.assertIn('explanation', results)
        self.assertIsInstance(results['explanation'], str)
        self.assertIn('tip', results)
        self.assertIsInstance(results['tip'], str)
        self.assertIn(results['tip'], TrustScoreCalculator.DID_YOU_KNOW_TIPS) # Key assertion for random tip
        
        self.assertEqual(results['inferred_bias_type'], "No specific patterns detected")

    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
    @patch('biaslens.analyzer.NigerianPatterns.analyze_patterns')
    @patch('biaslens.analyzer.FakeNewsDetector.detect')
    def test_quick_analyze_with_specific_nigerian_bias_and_random_tip(self,
                                               mock_fake_news_detect,
                                               mock_nigerian_patterns,
                                               mock_sentiment_safe):
        mock_sentiment_safe.return_value = {'label': 'neutral', 'confidence': 0.9, 'all_scores': {}, 'bias_indicator': False}
        mock_nigerian_patterns.return_value = {'has_triggers': False, 'has_clickbait': False}
        mock_fake_news_detect.return_value = (False, {})

        specific_bias_info = {
            "inferred_bias_type": "Anti-Igbo ethnic bias",
            "bias_category": "ethnic", "bias_target": "Igbo", "matched_keywords": ["nyamiri", "igbo"]
        }
        self.mock_enhancer_for_quick_analyze.get_lightweight_bias_assessment.return_value = specific_bias_info

        results = quick_analyze("Some text containing nyamiri.")
        self.assertEqual(results['inferred_bias_type'], "Anti-Igbo ethnic bias")
        self.assertIn(results['tip'], TrustScoreCalculator.DID_YOU_KNOW_TIPS) # Check tip is from the list
        expected_explanation = "Quick check found no immediate high-risk patterns. Specific patterns suggest: Anti-Igbo ethnic bias."
        self.assertEqual(results['explanation'], expected_explanation)

    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_emotion_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_bias_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_patterns_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._calculate_trust_score_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._generate_overall_assessment') 
    @patch('biaslens.analyzer.BiasLensAnalyzer._nigerian_bias_enhancer') 
    def test_analyze_successful_run_tip_check(self,
                                         mock_analyzer_enhancer_instance,
                                         mock_generate_overall_assessment,
                                         mock_calculate_trust_score_safe,
                                         mock_analyze_patterns_safe,
                                         mock_analyze_bias_safe,
                                         mock_analyze_emotion_safe,
                                         mock_analyze_sentiment_safe):
        
        mock_analyze_sentiment_safe.return_value = {'label': 'neutral', 'confidence': 0.9}
        mock_analyze_emotion_safe.return_value = {'label': 'neutral', 'confidence': 0.8}
        mock_analyze_bias_safe.return_value = {'flag': False, 'type_analysis': {'type': 'neutral'}}
        mock_analyze_patterns_safe.return_value = {}
        mock_analyzer_enhancer_instance.get_lightweight_bias_assessment.return_value = {"inferred_bias_type": "No specific patterns detected"}
        
        # Mock the output of _calculate_trust_score_safe, which includes the tip
        expected_tip = "This is a specific tip from TrustScoreCalculator for analyze."
        mock_calculate_trust_score_safe.return_value = {
            'score': 80, 'indicator': '🟢 Trusted', 'explanation': ['Test explanation'], 
            'tip': expected_tip, 'trust_level': 'highly_trusted', 'risk_factors': [], 
            'summary': 'Test summary', 'pattern_analysis': {}
        }
        # _generate_overall_assessment's return doesn't directly set the final 'tip'
        mock_generate_overall_assessment.return_value = {} 

        analysis_result = analyze("This is a comprehensive test sentence.")
        self.assertIsNotNone(analysis_result)
        self.assertIn('tip', analysis_result)
        self.assertEqual(analysis_result['tip'], expected_tip) # Tip should be from calculate_trust_score_safe

    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe') # Patching a method called early in 'analyze'
    def test_analyze_general_exception_tip(self, mock_sentiment_analysis_safe):
        """Test analyze returns the correct tip on general exception."""
        mock_sentiment_analysis_safe.side_effect = Exception("Simulated component failure")
        
        analysis_result = analyze("Some text that will cause an error.")
        self.assertIsNotNone(analysis_result)
        self.assertEqual(analysis_result.get('indicator'), 'Error')
        self.assertEqual(analysis_result.get('tip'), "Analysis failed due to an unexpected error. Please try again later or contact support.")

if __name__ == '__main__':
    unittest.main()
