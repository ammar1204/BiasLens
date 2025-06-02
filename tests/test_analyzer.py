import unittest
from unittest.mock import patch, MagicMock
from biaslens.analyzer import BiasLensAnalyzer, analyze, quick_analyze
from biaslens.bias import NigerianBiasEnhancer
from biaslens.trust import TrustScoreCalculator

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
        self.patcher_enhancer_quick = patch('biaslens.analyzer._global_analyzer._nigerian_bias_enhancer')
        self.mock_enhancer_for_quick_analyze = self.patcher_enhancer_quick.start()
        self.mock_enhancer_for_quick_analyze.get_lightweight_bias_assessment.return_value = {
            "inferred_bias_type": "No specific patterns detected",
            "bias_category": None, "bias_target": None, "matched_keywords": []
        }

        # Mocks for BiasLensAnalyzer instance methods (used by 'analyze')
        self.patcher_analyzer_sentiment = patch('biaslens.analyzer.BiasLensAnalyzer._analyze_sentiment_safe')
        self.mock_analyzer_sentiment = self.patcher_analyzer_sentiment.start()

        self.patcher_analyzer_emotion = patch('biaslens.analyzer.BiasLensAnalyzer._analyze_emotion_safe')
        self.mock_analyzer_emotion = self.patcher_analyzer_emotion.start()

        self.patcher_analyzer_bias = patch('biaslens.analyzer.BiasLensAnalyzer._analyze_bias_safe')
        self.mock_analyzer_bias = self.patcher_analyzer_bias.start()

        self.patcher_analyzer_patterns = patch('biaslens.analyzer.BiasLensAnalyzer._analyze_patterns_safe')
        self.mock_analyzer_patterns = self.patcher_analyzer_patterns.start()

        self.patcher_analyzer_lw_enhancer = patch('biaslens.analyzer.BiasLensAnalyzer._nigerian_bias_enhancer')
        self.mock_analyzer_lw_enhancer = self.patcher_analyzer_lw_enhancer.start()
        
        self.patcher_analyzer_trust_calc = patch('biaslens.analyzer.BiasLensAnalyzer._calculate_trust_score_safe')
        self.mock_analyzer_trust_calc = self.patcher_analyzer_trust_calc.start()

        self.patcher_analyzer_overall_assessment = patch('biaslens.analyzer.BiasLensAnalyzer._generate_overall_assessment')
        self.mock_analyzer_overall_assessment = self.patcher_analyzer_overall_assessment.start()


    def tearDown(self):
        self.patcher_enhancer_quick.stop()
        self.patcher_analyzer_sentiment.stop()
        self.patcher_analyzer_emotion.stop()
        self.patcher_analyzer_bias.stop()
        self.patcher_analyzer_patterns.stop()
        self.patcher_analyzer_lw_enhancer.stop()
        self.patcher_analyzer_trust_calc.stop()
        self.patcher_analyzer_overall_assessment.stop()


    def test_quick_analyze_empty_text(self):
        results = quick_analyze("")
        # ... (assertions remain the same as they were already correct)
        self.assertEqual(results.get('tip'), "No text was provided. Please input text for analysis. For a detailed breakdown of potential biases and manipulation, use the full analyze() function once text is provided.")

    def test_analyze_empty_text(self):
        analysis_result = analyze("")
        self.assertEqual(analysis_result['indicator'], 'Error')
        self.assertEqual(analysis_result['explanation'], ["Empty or invalid text provided"])
        self.assertEqual(analysis_result['tip'], "Analysis failed: No text was provided. Please input text for analysis.")
        self.assertIsNone(analysis_result['trust_score'])
        self.assertIsNone(analysis_result['primary_bias_type'])
        self.assertIsNone(analysis_result['sentiment_details'])
        self.assertIsNone(analysis_result['emotion_details'])
        self.assertIsNone(analysis_result['bias_details'])
        self.assertIsNone(analysis_result['pattern_highlights'])
        self.assertIsNone(analysis_result['lightweight_nigerian_bias_assessment'])
        self.assertNotIn("metadata", analysis_result)


    @patch('biaslens.analyzer.NigerianPatterns.analyze_patterns') # This is used by quick_analyze directly
    @patch('biaslens.analyzer.FakeNewsDetector.detect')    # This is used by quick_analyze directly
    def test_quick_analyze_valid_text_random_tip(self, mock_fake_news_detect, mock_nigerian_patterns):
        # Mocking _analyze_sentiment_safe for quick_analyze as it's called on the global analyzer instance
        with patch('biaslens.analyzer._global_analyzer._analyze_sentiment_safe') as mock_sentiment_quick:
            mock_sentiment_quick.return_value = {'label': 'neutral', 'confidence': 0.9, 'all_scores': {}, 'bias_indicator': False}
            mock_nigerian_patterns.return_value = {'has_triggers': False, 'has_clickbait': False, 'trigger_score':0, 'clickbait_score':0, 'total_flags':0}
            mock_fake_news_detect.return_value = (False, {'fake_matches':[], 'credibility_flags':[], 'fake_score':0, 'credibility_score':0, 'risk_level':'minimal', 'total_flags':0})
            
            self.mock_enhancer_for_quick_analyze.get_lightweight_bias_assessment.return_value = {
                "inferred_bias_type": "No specific patterns detected", "bias_category": None, 
                "bias_target": None, "matched_keywords": []
            }
            
            results = quick_analyze("This is a test sentence for random tip.")
            self.assertIn(results['tip'], TrustScoreCalculator.DID_YOU_KNOW_TIPS)
            self.assertEqual(results['inferred_bias_type'], "No specific patterns detected")


    def test_analyze_new_structure_success(self):
        # Configure mocks for a successful run with diverse data
        self.mock_analyzer_sentiment.return_value = {'label': 'negative', 'confidence': 0.88}
        self.mock_analyzer_emotion.return_value = {'label': 'anger', 'confidence': 0.75, 'is_emotionally_charged': True, 'manipulation_risk': 'medium'}
        self.mock_analyzer_bias.return_value = {'flag': True, 'label': 'Strong Bias Detected', 'type_analysis': {'type': 'confirmation_bias', 'confidence': 0.92}}
        self.mock_analyzer_patterns.return_value = {
            'nigerian_patterns': {'has_triggers': True, 'has_clickbait': True, 'trigger_details': ['wahala']},
            'fake_news': {'detected': True, 'details': {'risk_level': 'high', 'is_clickbait': True, 'matched_phrases': ['breaking news']}},
            'viral_manipulation': {'is_potentially_viral': True, 'engagement_bait_score': 0.8}
        }
        mock_lw_assessment = {
            "inferred_bias_type": "Anti-PDP political bias", "bias_category": "political", 
            "bias_target": "PDP", "matched_keywords": ["pdp", "bad"]
        }
        self.mock_analyzer_lw_enhancer.get_lightweight_bias_assessment.return_value = mock_lw_assessment
        
        self.mock_analyzer_trust_calc.return_value = {
            'score': 30, 'indicator': '🔴 Risky', 
            'explanation': ['High bias.', 'Fake news risk.'], 'tip': 'Be very careful.'
        }
        self.mock_analyzer_overall_assessment.return_value = {} # Not directly used in final dict keys

        # Call analyze with include_patterns=True
        result = analyze("Test text for new structure", include_patterns=True, include_detailed_results=False)

        self.assertNotIn("metadata", result)
        self.assertEqual(result['trust_score'], 30)
        self.assertEqual(result['indicator'], '🔴 Risky')
        self.assertEqual(result['explanation'], ['High bias.', 'Fake news risk.'])
        self.assertEqual(result['tip'], 'Be very careful.')
        
        # primary_bias_type should be from ML model first
        self.assertEqual(result['primary_bias_type'], 'confirmation_bias') 

        self.assertEqual(result['sentiment_details'], {'label': 'negative', 'confidence': 0.88})
        self.assertEqual(result['emotion_details'], {'label': 'anger', 'confidence': 0.75, 'is_emotionally_charged': True, 'manipulation_risk': 'medium'})
        self.assertEqual(result['bias_details'], {'detected': True, 'label': 'Strong Bias Detected', 'confidence': 0.92})
        
        self.assertEqual(result['pattern_highlights']['nigerian_context_detected'], True)
        self.assertEqual(result['pattern_highlights']['clickbait_detected'], True) # from nigerian_patterns OR fake_news OR viral
        self.assertEqual(result['pattern_highlights']['fake_news_risk'], 'high')
        
        self.assertEqual(result['lightweight_nigerian_bias_assessment'], mock_lw_assessment)
        self.assertNotIn('detailed_sub_analyses', result) # include_detailed_results is False

    def test_analyze_primary_bias_type_fallback_to_lightweight(self):
        # ML bias is neutral, lightweight has specific
        self.mock_analyzer_bias.return_value = {'flag': False, 'label': 'Neutral', 'type_analysis': {'type': 'neutral', 'confidence': 0.9}}
        mock_lw_assessment = {"inferred_bias_type": "Pro-Arewa regional bias", "bias_category": "regional", "bias_target": "Arewa", "matched_keywords": ["arewa"]}
        self.mock_analyzer_lw_enhancer.get_lightweight_bias_assessment.return_value = mock_lw_assessment
        # Other mocks minimal
        self.mock_analyzer_sentiment.return_value = {}
        self.mock_analyzer_emotion.return_value = {}
        self.mock_analyzer_patterns.return_value = {}
        self.mock_analyzer_trust_calc.return_value = {'tip': 'A tip'}


        result = analyze("Test text", include_patterns=True)
        self.assertEqual(result['primary_bias_type'], "Pro-Arewa regional bias")


    def test_analyze_detailed_results_new_structure(self):
        # Configure mocks
        mock_sentiment = {'label': 'neutral', 'confidence': 0.9}
        mock_emotion = {'label': 'neutral', 'confidence': 0.8, 'is_emotionally_charged': False, 'manipulation_risk': 'low'}
        mock_bias = {'flag': False, 'label': 'Neutral', 'type_analysis': {'type': 'neutral'}}
        mock_patterns = {
            'nigerian_patterns': {'has_triggers': False, 'has_clickbait': False, 'error': None},
            'fake_news': {'detected': False, 'details': {}, 'error': None},
            'viral_manipulation': {'error': None}
        }
        mock_lw_assessment = {"inferred_bias_type": "No specific patterns detected", "matched_keywords": []}

        self.mock_analyzer_sentiment.return_value = mock_sentiment
        self.mock_analyzer_emotion.return_value = mock_emotion
        self.mock_analyzer_bias.return_value = mock_bias
        self.mock_analyzer_patterns.return_value = mock_patterns
        self.mock_analyzer_lw_enhancer.get_lightweight_bias_assessment.return_value = mock_lw_assessment
        self.mock_analyzer_trust_calc.return_value = {'tip': 'Detailed tip'}

        result = analyze("Test for detailed results", include_patterns=True, include_detailed_results=True)

        self.assertNotIn("metadata", result)
        self.assertIn('detailed_sub_analyses', result)
        sub_analyses = result['detailed_sub_analyses']
        
        self.assertEqual(sub_analyses['sentiment'], mock_sentiment)
        self.assertNotIn('metadata', sub_analyses['sentiment']) # Ensure no metadata creep
        
        self.assertEqual(sub_analyses['emotion'], mock_emotion)
        self.assertEqual(sub_analyses['bias'], mock_bias)
        self.assertEqual(sub_analyses['patterns'], mock_patterns)
        self.assertEqual(sub_analyses['lightweight_nigerian_bias'], mock_lw_assessment)


    def test_analyze_general_exception_new_structure(self):
        self.mock_analyzer_sentiment.side_effect = Exception("Simulated component failure")
        
        analysis_result = analyze("Some text that will cause an error.")
        self.assertEqual(analysis_result.get('indicator'), 'Error')
        self.assertEqual(analysis_result.get('tip'), "Analysis failed due to an unexpected error. Please try again later or contact support.")
        self.assertIsNone(analysis_result['trust_score'])
        self.assertIsNone(analysis_result['primary_bias_type'])
        self.assertIsNone(analysis_result['sentiment_details'])
        self.assertIsNone(analysis_result['emotion_details'])
        self.assertIsNone(analysis_result['bias_details'])
        self.assertIsNone(analysis_result['pattern_highlights'])
        self.assertIsNone(analysis_result['lightweight_nigerian_bias_assessment'])
        self.assertNotIn("metadata", analysis_result)


if __name__ == '__main__':
    unittest.main()
