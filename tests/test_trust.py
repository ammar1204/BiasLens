import unittest
from unittest.mock import MagicMock, patch
from biaslens.trust import TrustScoreCalculator
# Import pattern classes to mock their static methods
from biaslens.patterns import NigerianPatterns, FakeNewsDetector, ViralityDetector

class TestTrustScoreCalculator(unittest.TestCase):

    def test_get_trust_indicator(self):
        self.assertEqual(TrustScoreCalculator.get_trust_indicator(80), "🟢 Trusted")
        self.assertEqual(TrustScoreCalculator.get_trust_indicator(70), "🟢 Trusted")
        self.assertEqual(TrustScoreCalculator.get_trust_indicator(60), "🟡 Caution")
        self.assertEqual(TrustScoreCalculator.get_trust_indicator(40), "🟡 Caution")
        self.assertEqual(TrustScoreCalculator.get_trust_indicator(30), "🔴 Risky")
        self.assertEqual(TrustScoreCalculator.get_trust_indicator(0), "🔴 Risky")

    def test_get_detailed_trust_level(self):
        self.assertEqual(TrustScoreCalculator.get_detailed_trust_level(90), "highly_trusted")
        self.assertEqual(TrustScoreCalculator.get_detailed_trust_level(75), "trusted")
        self.assertEqual(TrustScoreCalculator.get_detailed_trust_level(60), "moderate_caution")
        self.assertEqual(TrustScoreCalculator.get_detailed_trust_level(45), "high_caution")
        self.assertEqual(TrustScoreCalculator.get_detailed_trust_level(30), "risky")
        self.assertEqual(TrustScoreCalculator.get_detailed_trust_level(10), "highly_risky")

    # Mock all external dependencies for the calculate method
    @patch.object(NigerianPatterns, 'analyze_patterns')
    @patch.object(FakeNewsDetector, 'detect')
    @patch.object(ViralityDetector, 'analyze_virality')
    def test_calculate_high_trust_scenario(self, mock_viral, mock_fake_news, mock_nigerian):
        # Configure mocks to return neutral/no-risk results
        mock_nigerian.return_value = {'has_triggers': False, 'has_clickbait': False, 'trigger_score': 0, 'clickbait_score': 0}
        mock_fake_news.return_value = (False, {'risk_level': 'minimal', 'fake_matches': [], 'credibility_flags': [], 'total_flags': 0})
        mock_viral.return_value = {'has_viral_patterns': False, 'manipulation_level': 'minimal', 'viral_score': 0}

        # Mock input data from other analyzers (neutral, no bias, calm emotion)
        bias_data_mock = {'flag': False, 'label': 'Neutral'}
        emotion_data_mock = {'manipulation_risk': 'minimal', 'is_emotionally_charged': False, 'confidence': 0.9} # high confidence neutral emotion
        sentiment_data_mock = {'label': 'neutral', 'confidence': 0.9, 'bias_indicator': False, 'is_polarized': False, 'polarization_score': 0.1}

        # Legacy scores also neutral
        legacy_bias_score = 0.1
        legacy_emotion_score = 0.1 # Corresponds to emotion_data['confidence'] for fallback if emotion_data not used
        legacy_sentiment_label = "neutral"

        text_input = "This is a very factual and neutral statement."

        score, indicator, explanation, tip, extras = TrustScoreCalculator.calculate(
            legacy_bias_score, legacy_emotion_score, legacy_sentiment_label, text_input,
            emotion_data=emotion_data_mock,
            sentiment_data=sentiment_data_mock,
            bias_data=bias_data_mock
        )

        self.assertGreaterEqual(score, 85) # Expect high score, potentially with bonus
        self.assertEqual(indicator, "🟢 Trusted")
        self.assertIn("Content appears balanced and factual", " ".join(explanation))
        self.assertEqual(extras['trust_level'], "highly_trusted")
        self.assertEqual(len(extras['risk_factors']), 0) # No risk factors

    @patch.object(NigerianPatterns, 'analyze_patterns')
    @patch.object(FakeNewsDetector, 'detect')
    @patch.object(ViralityDetector, 'analyze_virality')
    def test_calculate_low_trust_scenario_multiple_risks(self, mock_viral, mock_fake_news, mock_nigerian):
        # Configure mocks for high risk
        mock_nigerian.return_value = {'has_triggers': True, 'trigger_score': 30, 'has_clickbait': True, 'clickbait_score': 20}
        mock_fake_news.return_value = (True, {'risk_level': 'high', 'fake_matches': ['shocking truth'], 'credibility_flags':['experts say'], 'total_flags': 2})
        mock_viral.return_value = {'has_viral_patterns': True, 'manipulation_level': 'high', 'viral_score': 25}

        bias_data_mock = {'flag': True, 'label': 'Potentially Biased - High Confidence'}
        emotion_data_mock = {'manipulation_risk': 'high', 'is_emotionally_charged': True}
        sentiment_data_mock = {'label': 'negative', 'bias_indicator': True, 'is_polarized': True, 'polarization_score': 0.8}

        legacy_bias_score = 0.9
        legacy_emotion_score = 0.9
        legacy_sentiment_label = "negative"
        text_input = "SHOCKING! Experts say Nawa o, dem wan finish us, share now!"

        score, indicator, explanation, tip, extras = TrustScoreCalculator.calculate(
            legacy_bias_score, legacy_emotion_score, legacy_sentiment_label, text_input,
            emotion_data=emotion_data_mock,
            sentiment_data=sentiment_data_mock,
            bias_data=bias_data_mock
        )

        self.assertLessEqual(score, 30) # Expect very low score
        self.assertEqual(indicator, "🔴 Risky")
        self.assertIn("High confidence bias detected", " ".join(explanation))
        self.assertIn("highly manipulative emotional language", " ".join(explanation))
        self.assertIn("Sentiment analysis indicates potential bias", " ".join(explanation))
        self.assertIn("highly polarized sentiment", " ".join(explanation))
        self.assertIn("Nigerian expressions", " ".join(explanation))
        self.assertIn("clickbait patterns", " ".join(explanation))
        self.assertIn("High risk of fake news", " ".join(explanation))
        self.assertIn("manipulate viral sharing", " ".join(explanation))

        self.assertIn("high_bias_detected", extras['risk_factors'])
        self.assertIn("high_emotional_manipulation", extras['risk_factors'])
        self.assertIn("polarized_sentiment", extras['risk_factors'])

    @patch.object(NigerianPatterns, 'analyze_patterns')
    @patch.object(FakeNewsDetector, 'detect')
    @patch.object(ViralityDetector, 'analyze_virality')
    def test_calculate_specific_risk_factors_impact(self, mock_viral, mock_fake_news, mock_nigerian):
        # Test for emotional manipulation specifically
        mock_nigerian.return_value = {'has_triggers': False, 'has_clickbait': False, 'trigger_score': 0, 'clickbait_score': 0}
        mock_fake_news.return_value = (False, {'risk_level': 'minimal', 'fake_matches': [], 'credibility_flags':[], 'total_flags':0})
        mock_viral.return_value = {'has_viral_patterns': False, 'manipulation_level': 'minimal', 'viral_score':0}

        bias_data_mock = {'flag': False}
        emotion_data_mock = {'manipulation_risk': 'medium', 'is_emotionally_charged': True} # Medium manipulation
        sentiment_data_mock = {'label': 'neutral', 'bias_indicator': False, 'is_polarized': False, 'polarization_score': 0.1}

        score, _, explanation, _, extras = TrustScoreCalculator.calculate(
            0.2, 0.5, "neutral", "Text designed to test emotion.",
            emotion_data=emotion_data_mock, sentiment_data=sentiment_data_mock, bias_data=bias_data_mock
        )
        self.assertIn("signs of emotional manipulation", " ".join(explanation))
        self.assertIn("medium_emotional_manipulation", extras['risk_factors'])
        # Base score 100 - medium_emotional_manipulation (20) - emotionally_charged (15) = 65.
        # Small bonus might apply if other legacy scores are low.
        # Expected range: 60-70
        self.assertTrue(55 <= score <= 75, f"Score {score} out of expected range for medium emotional risk.")

    def test_get_contextual_tip(self):
        tip_bias = TrustScoreCalculator._get_contextual_tip(["high_bias_detected"])
        self.assertIn("multiple perspectives", tip_bias)

        tip_emotion = TrustScoreCalculator._get_contextual_tip(["high_emotional_manipulation"])
        self.assertIn("strong emotions", tip_emotion)

        tip_fake = TrustScoreCalculator._get_contextual_tip(["high_fake_news_risk"])
        self.assertIn("verifiable facts", tip_fake)

        # Test with a risk factor that might have a more general match
        tip_polarized = TrustScoreCalculator._get_contextual_tip(["polarized_sentiment"])
        self.assertIn("neutral viewpoints", tip_polarized) # Check if it maps to the 'polarized' key in contextual_tips_map

        tip_random = TrustScoreCalculator._get_contextual_tip(["unknown_risk_factor"])
        self.assertTrue(any(tip_random == general_tip for general_tip in TrustScoreCalculator.DID_YOU_KNOW_TIPS))

    def test_generate_summary(self):
        self.assertIn("highly trustworthy", TrustScoreCalculator._generate_summary(90, []))
        self.assertIn("generally trustworthy", TrustScoreCalculator._generate_summary(75, []))
        self.assertIn("some concerning patterns", TrustScoreCalculator._generate_summary(60, ["mild_bias"]))
        self.assertIn("multiple red flags", TrustScoreCalculator._generate_summary(45, ["high_bias"]))
        self.assertIn("risky", TrustScoreCalculator._generate_summary(30, ["fake_news"]))
        self.assertIn("strong signs of bias", TrustScoreCalculator._generate_summary(10, ["extreme_emotion"]))

if __name__ == '__main__':
    unittest.main()
