import unittest
from unittest.mock import patch, MagicMock
from biaslens.analyzer import BiasLensAnalyzer, analyze, quick_analyze
from biaslens.bias import NigerianBiasEnhancer

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
        # This depends on "jihad" mapping and context.
        # The current lightweight model might not pick up "bad" if it's not close enough or if "jihad" itself has a direct mapping.
        # "jihad" maps to "Anti-Islamic religious bias"
        text = "Their jihad is bad."
        result = self.enhancer.get_lightweight_bias_assessment(text)
        self.assertEqual(result["inferred_bias_type"], "Anti-Islamic religious bias")
        self.assertEqual(result["bias_category"], "religious")
        self.assertEqual(result["bias_target"], "Jihad") # As per current logic, it capitalizes the term
        self.assertIn("jihad", result["matched_keywords"])

    def test_lightweight_regional_bias_arewa_pro(self):
        text = "Arewa is the future, all good things come from Arewa."
        # "arewa" maps to "Pro-Northern regional bias"
        # The _determine_bias_direction_lightweight is primarily for political terms in the current setup.
        # So, for "arewa", it should directly use the mapping.
        result = self.enhancer.get_lightweight_bias_assessment(text)
        self.assertEqual(result["inferred_bias_type"], "Pro-Northern regional bias")
        self.assertEqual(result["bias_category"], "regional")
        self.assertEqual(result["bias_target"], "Arewa")
        self.assertIn("arewa", result["matched_keywords"])

    def test_lightweight_nigerian_context_no_specific_bias(self):
        text = "News from Lagos today, also something about Abuja. People are talking about a new policy."
        result = self.enhancer.get_lightweight_bias_assessment(text)
        # "lagos" and "abuja" are not in the patterns by default. Let's use a general ethnic term without strong bias context.
        text_with_context = "The yoruba culture is interesting. Many igbo people live in Lagos."
        result_with_context = self.enhancer.get_lightweight_bias_assessment(text_with_context)
        
        # This will pick the first term "yoruba" and its default mapping
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
        self.assertIn("north", result["matched_keywords"]) # Check that all detected keywords are included

    def test_lightweight_context_detected_unclear_bias(self):
        # Use a term that is in `nigerian_patterns` but not in the specific maps of `_generate_specific_bias_type_lightweight`
        # For example, a stereotype word if it's not directly mapped to a bias type.
        # 'lazy' is a stereotype under 'ethnic'.
        text = "Some people are lazy in Nigeria."
        result = self.enhancer.get_lightweight_bias_assessment(text)
        self.assertEqual(result["inferred_bias_type"], "Nigerian context detected, specific bias type unclear from patterns")
        self.assertEqual(result["bias_category"], "ethnic") # Category of the first match ('lazy' -> 'ethnic')
        self.assertIsNone(result["bias_target"])
        self.assertIn("lazy", result["matched_keywords"])


class TestBiasLensAnalyzer(unittest.TestCase):

    def setUp(self):
        # self.analyzer_instance = BiasLensAnalyzer()
        # Patch NigerianBiasEnhancer on the global analyzer instance for quick_analyze tests
        self.patcher_enhancer = patch('biaslens.analyzer._global_analyzer._nigerian_bias_enhancer')
        self.mock_enhancer = self.patcher_enhancer.start()
        
        # Default mock for get_lightweight_bias_assessment
        self.mock_enhancer.get_lightweight_bias_assessment.return_value = {
            "inferred_bias_type": "No specific patterns detected",
            "bias_category": None,
            "bias_target": None,
            "matched_keywords": []
        }
        # Keep a reference to the original _nigerian_bias_enhancer if needed, though not typical for these tests
        # self.original_enhancer = biaslens.analyzer._global_analyzer._nigerian_bias_enhancer
        # biaslens.analyzer._global_analyzer._nigerian_bias_enhancer = self.mock_enhancer


    def tearDown(self):
        self.patcher_enhancer.stop()
        # If you re-assigned the global analyzer's enhancer:
        # biaslens.analyzer._global_analyzer._nigerian_bias_enhancer = self.original_enhancer


    def test_quick_analyze_empty_text(self):
        results = quick_analyze("")
        self.assertIsNotNone(results)
        self.assertIsNone(results.get('score'))
        self.assertEqual(results.get('indicator'), 'Error')
        self.assertEqual(results.get('explanation'), "Empty text provided.")
        self.assertEqual(results.get('tip'), "No text was provided. Please input text for analysis. For a detailed breakdown of potential biases and manipulation, use the full analyze() function once text is provided.")
        # Assert new fields for empty result
        self.assertIsNone(results.get('inferred_bias_type'))
        self.assertIsNone(results.get('bias_category'))
        self.assertIsNone(results.get('bias_target'))
        self.assertEqual(results.get('matched_keywords'), [])


    def test_analyze_empty_text(self):
        analysis = analyze("")
        self.assertIsNotNone(analysis)
        self.assertIsNone(analysis['trust_score'])
        self.assertEqual(analysis['indicator'], 'Error')
        self.assertEqual(analysis['explanation'], ["Empty or invalid text provided"])


    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
    @patch('biaslens.analyzer.NigerianPatterns.analyze_patterns')
    @patch('biaslens.analyzer.FakeNewsDetector.detect')
    # Patching the get_lightweight_bias_assessment on the _global_analyzer's instance
    # @patch('biaslens.analyzer._global_analyzer._nigerian_bias_enhancer.get_lightweight_bias_assessment') # Already handled by setUp/tearDown
    def test_quick_analyze_valid_text_structure_no_specific_bias_pattern(self,
                                               mock_fake_news_detect,
                                               mock_nigerian_patterns,
                                               mock_sentiment_safe):
        
        default_sentiment = {'label': 'neutral', 'confidence': 0.9, 'all_scores': {}, 'bias_indicator': False}
        default_nigerian_patterns = {'has_triggers': False, 'has_clickbait': False, 'trigger_score':0, 'clickbait_score':0, 'total_flags':0}
        default_fake_news_detect = (False, {'fake_matches':[], 'credibility_flags':[], 'fake_score':0, 'credibility_score':0, 'risk_level':'minimal', 'total_flags':0})
        
        # Default mock from setUp: no specific patterns detected
        # self.mock_enhancer.get_lightweight_bias_assessment.return_value = {
        #     "inferred_bias_type": "No specific patterns detected", ...
        # }

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
        
        # Assert new fields - default values
        self.assertEqual(results['inferred_bias_type'], "No specific patterns detected")
        self.assertIsNone(results['bias_category'])
        self.assertIsNone(results['bias_target'])
        self.assertEqual(results['matched_keywords'], [])

    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
    @patch('biaslens.analyzer.NigerianPatterns.analyze_patterns')
    @patch('biaslens.analyzer.FakeNewsDetector.detect')
    # @patch('biaslens.analyzer._global_analyzer._nigerian_bias_enhancer.get_lightweight_bias_assessment') # Handled by setUp
    def test_quick_analyze_with_specific_nigerian_bias(self,
                                               mock_fake_news_detect,
                                               mock_nigerian_patterns,
                                               mock_sentiment_safe):
        mock_sentiment_safe.return_value = {'label': 'neutral', 'confidence': 0.9, 'all_scores': {}, 'bias_indicator': False}
        mock_nigerian_patterns.return_value = {'has_triggers': False, 'has_clickbait': False}
        mock_fake_news_detect.return_value = (False, {})

        # Configure mock for get_lightweight_bias_assessment to return a specific bias
        specific_bias_info = {
            "inferred_bias_type": "Anti-Igbo ethnic bias",
            "bias_category": "ethnic",
            "bias_target": "Igbo",
            "matched_keywords": ["nyamiri", "igbo"]
        }
        self.mock_enhancer.get_lightweight_bias_assessment.return_value = specific_bias_info

        results = quick_analyze("Some text containing nyamiri.")
        self.assertIsNotNone(results)
        self.assertEqual(results['inferred_bias_type'], "Anti-Igbo ethnic bias")
        self.assertEqual(results['bias_category'], "ethnic")
        self.assertEqual(results['bias_target'], "Igbo")
        self.assertEqual(sorted(results['matched_keywords']), sorted(["nyamiri", "igbo"]))
        
        expected_explanation = "Quick check found no immediate high-risk patterns. Specific patterns suggest: Anti-Igbo ethnic bias."
        self.assertEqual(results['explanation'], expected_explanation)

    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
    @patch('biaslens.analyzer.NigerianPatterns.analyze_patterns')
    @patch('biaslens.analyzer.FakeNewsDetector.detect')
    # @patch('biaslens.analyzer._global_analyzer._nigerian_bias_enhancer.get_lightweight_bias_assessment') # Handled by setUp
    def test_quick_analyze_with_sentiment_and_nigerian_bias(self,
                                               mock_fake_news_detect,
                                               mock_nigerian_patterns,
                                               mock_sentiment_safe):
        # Sentiment bias detected
        mock_sentiment_safe.return_value = {'label': 'negative', 'confidence': 0.95, 'all_scores': {}, 'bias_indicator': True}
        # No other basic patterns
        mock_nigerian_patterns.return_value = {'has_triggers': False, 'has_clickbait': False}
        mock_fake_news_detect.return_value = (False, {})

        # Configure mock for get_lightweight_bias_assessment for a specific political bias
        specific_bias_info = {
            "inferred_bias_type": "Pro-APC political bias",
            "bias_category": "political",
            "bias_target": "APC",
            "matched_keywords": ["apc", "best"]
        }
        self.mock_enhancer.get_lightweight_bias_assessment.return_value = specific_bias_info

        results = quick_analyze("APC is the best party ever.")
        self.assertIsNotNone(results)
        self.assertEqual(results['inferred_bias_type'], "Pro-APC political bias")
        self.assertEqual(results['bias_category'], "political")
        self.assertEqual(results['bias_target'], "APC")
        self.assertEqual(sorted(results['matched_keywords']), sorted(["apc", "best"]))
        
        # Explanation should reflect both sentiment and pattern bias
        expected_explanation = "Quick check found: potential sentiment bias. Specific patterns suggest: Pro-APC political bias."
        self.assertEqual(results['explanation'], expected_explanation)
        # Also check that score is affected by sentiment bias (will be lower than default 80)
        self.assertTrue(results['score'] < 80)


    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_emotion_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_bias_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_patterns_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._calculate_trust_score_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._generate_overall_assessment') 
    @patch('biaslens.analyzer.BiasLensAnalyzer._nigerian_bias_enhancer') # Patching the one on the class for full analyze
    def test_analyze_valid_text_structure(self,
                                         mock_analyzer_enhancer_instance, # For full 'analyze'
                                         mock_generate_overall_assessment,
                                         mock_calculate_trust_score_safe,
                                         mock_analyze_patterns_safe,
                                         mock_analyze_bias_safe,
                                         mock_analyze_emotion_safe,
                                         mock_analyze_sentiment_safe):
        
        mock_analyze_sentiment_safe.return_value = {'label': 'neutral', 'confidence': 0.9, 'all_scores': {}, 'bias_indicator': False}
        mock_analyze_emotion_safe.return_value = {'label': 'neutral', 'confidence': 0.8, 'manipulation_risk': 'minimal', 'is_emotionally_charged': False}
        mock_analyze_bias_safe.return_value = {'flag': False, 'label': 'Likely Neutral', 'type_analysis': {'type': 'neutral', 'confidence': 90.0}}
        mock_analyze_patterns_safe.return_value = {'nigerian_patterns': {}, 'fake_news': {'detected': False}, 'viral_manipulation': {}}
        
        # Mock for lightweight assessment in full analyze
        mock_analyzer_enhancer_instance.get_lightweight_bias_assessment.return_value = {
            "inferred_bias_type": "No specific patterns detected", "bias_category": None, "bias_target": None, "matched_keywords": []
        }
        
        mock_calculate_trust_score_safe.return_value = {
            'score': 80, 'indicator': '🟢 Trusted', 'explanation': ['Test explanation'], 'tip': 'Test tip',
        }
        mock_generate_overall_assessment.return_value = {} 

        analysis_result = analyze("This is a comprehensive test sentence.") # Renamed variable to avoid conflict
        self.assertIsNotNone(analysis_result)
        self.assertIn('trust_score', analysis_result)
        self.assertIn('primary_bias_type', analysis_result) 
        self.assertIsNone(analysis_result['primary_bias_type']) 
        self.assertIn('lightweight_nigerian_bias_assessment', analysis_result)
        self.assertEqual(analysis_result['lightweight_nigerian_bias_assessment']['inferred_bias_type'], "No specific patterns detected")


    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_emotion_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_bias_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._analyze_patterns_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._calculate_trust_score_safe')
    @patch('biaslens.analyzer.BiasLensAnalyzer._generate_overall_assessment')
    @patch('biaslens.analyzer.BiasLensAnalyzer._nigerian_bias_enhancer') # Patching the one on the class for full analyze
    def test_analyze_primary_bias_type_from_lightweight(self,
                                         mock_analyzer_enhancer_instance,
                                         mock_generate_overall_assessment,
                                         mock_calculate_trust_score_safe,
                                         mock_analyze_patterns_safe,
                                         mock_analyze_bias_safe,
                                         mock_analyze_emotion_safe,
                                         mock_analyze_sentiment_safe):
        # ML bias detection returns neutral
        mock_analyze_bias_safe.return_value = {'flag': False, 'label': 'Likely Neutral', 'type_analysis': {'type': 'neutral', 'confidence': 90.0}}
        # Other mocks
        mock_analyze_sentiment_safe.return_value = {'label': 'neutral', 'confidence': 0.9, 'all_scores': {}}
        mock_analyze_emotion_safe.return_value = {'label': 'neutral', 'confidence': 0.8, 'manipulation_risk': 'minimal'}
        mock_analyze_patterns_safe.return_value = {}
        mock_calculate_trust_score_safe.return_value = {'score': 70, 'indicator': '🟢 Trusted', 'explanation': ['Neutral.']}
        mock_generate_overall_assessment.return_value = {}

        # Lightweight assessment detects a bias
        lightweight_bias = {
            "inferred_bias_type": "Anti-Fulani ethnic bias",
            "bias_category": "ethnic",
            "bias_target": "Fulani",
            "matched_keywords": ["fulani"]
        }
        mock_analyzer_enhancer_instance.get_lightweight_bias_assessment.return_value = lightweight_bias

        analysis_result = analyze("Some text about Fulani people.")
        self.assertEqual(analysis_result.get('primary_bias_type'), "Anti-Fulani ethnic bias")
        self.assertEqual(analysis_result.get('lightweight_nigerian_bias_assessment'), lightweight_bias)


if __name__ == '__main__':
    unittest.main()
