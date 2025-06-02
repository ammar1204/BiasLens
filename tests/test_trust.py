import unittest
import random
from unittest.mock import patch
from biaslens.trust import TrustScoreCalculator

# The expected new list of DID_YOU_KNOW_TIPS
EXPECTED_DID_YOU_KNOW_TIPS = [
    "Verify information before sharing. Check multiple reputable sources to confirm a story's accuracy.",
    "Be wary of headlines designed to provoke strong emotions. They might prioritize clicks over facts.",
    "Look for bylines and author credentials. Anonymous sources can be a red flag for misinformation.",
    "Check the publication date. Old news can be re-shared out of context to mislead.",
    "Examine the 'About Us' page of a source to understand its mission, ownership, and potential biases.",
    "Distinguish between news reporting, opinion pieces, and sponsored content. Each has a different purpose.",
    "Cross-reference claims with fact-checking websites like Snopes, PolitiFact, or Africa Check.",
    "Be skeptical of content that claims to have 'secret' or 'exclusive' information without evidence.",
    "Consider the images and videos used. Are they original, or are they altered or taken from unrelated events?",
    "Understand that all sources can have some level of bias. Seek diverse perspectives to get a fuller picture.",
    "Pay attention to the language used. Loaded words, stereotypes, and generalizations can indicate bias.",
    "If a story sounds too good or too outrageous to be true, it often is. Investigate further.",
    "Support responsible journalism. Reliable news gathering requires resources and ethical standards.",
    "Media literacy is a key skill in the digital age. Continuously question and evaluate the information you consume.",
    "Look for corrections and clarifications. Reputable news organizations admit and fix their mistakes.",
    "Beware of echo chambers and filter bubbles. Actively seek out viewpoints that challenge your own.",
    "Check if statistical claims are backed by clear data sources and methodologies.",
    "Recognize that headlines don't always tell the full story. Read the article thoroughly.",
    "Be cautious with user-generated content (comments, social media posts) as it's often unverified.",
    "Understand the difference between correlation and causation when interpreting data or events."
]

UPDATED_CONTEXTUAL_TIPS = {
    'high_bias': "Examine if the content fairly represents different viewpoints or oversimplifies complex issues. Look for balanced reporting.",
    'emotional_manipulation': "Identify emotionally charged words. Question if the emotion is justified by evidence or used to cloud judgment.",
    'nigerian_triggers': "Local expressions can be used to make fake news seem more authentic and relatable.",
    'clickbait': "Clickbait headlines often exaggerate or omit crucial details. Compare headlines with article content critically.",
    'viral_manipulation': "Be skeptical of posts urging immediate sharing. Verify content before amplifying it, especially if it seems designed to go viral.",
    'fake_risk': "Verify information using the 'SIFT' method: Stop, Investigate the source, Find better coverage, Trace claims to the original context."
}

class TestTrustScoreCalculator(unittest.TestCase):

    def test_did_you_know_tips_content(self):
        """Verify that DID_YOU_KNOW_TIPS has been updated correctly."""
        self.assertEqual(TrustScoreCalculator.DID_YOU_KNOW_TIPS, EXPECTED_DID_YOU_KNOW_TIPS)
        self.assertEqual(len(TrustScoreCalculator.DID_YOU_KNOW_TIPS), 20)

    def test_get_contextual_tip_specific_risks(self):
        """Test that _get_contextual_tip returns correct specific tips for given risk factors."""
        test_cases = [
            (['high_bias_detected', 'other_risk'], UPDATED_CONTEXTUAL_TIPS['high_bias']),
            (['emotional_manipulation_high', 'clickbait'], UPDATED_CONTEXTUAL_TIPS['emotional_manipulation']), # Emotion should take precedence
            (['nigerian_triggers_found'], UPDATED_CONTEXTUAL_TIPS['nigerian_triggers']),
            (['clickbait_headline'], UPDATED_CONTEXTUAL_TIPS['clickbait']),
            (['viral_manipulation_suspected', 'low_fake_risk'], UPDATED_CONTEXTUAL_TIPS['viral_manipulation']), # Viral before fake
            (['high_fake_risk_pattern'], UPDATED_CONTEXTUAL_TIPS['fake_risk']),
            (['medium_fake_risk'], UPDATED_CONTEXTUAL_TIPS['fake_risk']),
        ]

        for risk_factors, expected_tip in test_cases:
            with self.subTest(risk_factors=risk_factors):
                tip = TrustScoreCalculator._get_contextual_tip(risk_factors)
                self.assertEqual(tip, expected_tip)
    
    def test_get_contextual_tip_priority(self):
        """Test priority of contextual tips."""
        # fake_risk should be prioritized over nigerian_triggers if both are present in some form
        risk_factors = ['high_fake_risk', 'nigerian_triggers']
        tip = TrustScoreCalculator._get_contextual_tip(risk_factors)
        self.assertEqual(tip, UPDATED_CONTEXTUAL_TIPS['fake_risk'])

        # emotional_manipulation should be prioritized over clickbait
        risk_factors = ['emotional_manipulation_medium', 'clickbait_pattern']
        tip = TrustScoreCalculator._get_contextual_tip(risk_factors)
        self.assertEqual(tip, UPDATED_CONTEXTUAL_TIPS['emotional_manipulation'])


    def test_get_contextual_tip_fallback_to_random(self):
        """Test that _get_contextual_tip falls back to DID_YOU_KNOW_TIPS for unknown risks."""
        risk_factors = ['unknown_risk_factor', 'another_unmapped_risk']
        # Mock random.choice to check if it's called from the correct list
        with patch('random.choice', side_effect=lambda x: x[0]) as mock_random_choice:
            tip = TrustScoreCalculator._get_contextual_tip(risk_factors)
            mock_random_choice.assert_called_once_with(EXPECTED_DID_YOU_KNOW_TIPS)
            self.assertIn(tip, EXPECTED_DID_YOU_KNOW_TIPS) # Checks if the first item was returned by side_effect

    def test_get_contextual_tip_empty_risks_fallback_to_random(self):
        """Test that _get_contextual_tip falls back to DID_YOU_KNOW_TIPS for empty risk factors."""
        risk_factors = []
        with patch('random.choice', side_effect=lambda x: x[0]) as mock_random_choice:
            tip = TrustScoreCalculator._get_contextual_tip(risk_factors)
            mock_random_choice.assert_called_once_with(EXPECTED_DID_YOU_KNOW_TIPS)
            self.assertIn(tip, EXPECTED_DID_YOU_KNOW_TIPS)

    @patch('biaslens.trust.NigerianPatterns.analyze_patterns')
    @patch('biaslens.trust.FakeNewsDetector.detect')
    @patch('biaslens.trust.ViralityDetector.analyze_virality')
    @patch('biaslens.trust.TrustScoreCalculator._get_contextual_tip')
    def test_calculate_tip_generation(self, mock_get_contextual_tip, mock_virality, mock_fake_news, mock_nigerian_patterns):
        """Test that calculate method correctly uses _get_contextual_tip for its tip output."""
        # Setup mocks for pattern analyzers
        mock_nigerian_patterns.return_value = {'has_triggers': False, 'has_clickbait': False, 'trigger_score':0, 'clickbait_score':0}
        mock_fake_news.return_value = (False, {'risk_level': 'low'})
        mock_virality.return_value = {'has_viral_patterns': False}

        # Configure _get_contextual_tip to return a specific tip
        expected_tip_from_contextual = "This is a controlled contextual tip."
        mock_get_contextual_tip.return_value = expected_tip_from_contextual

        # Call calculate with minimal data, focusing on the tip
        # Bias data, emotion data, sentiment data are mocked as neutral or not present to simplify
        bias_data_mock = {'flag': False, 'type_analysis': {'type': 'neutral'}}
        emotion_data_mock = {'manipulation_risk': 'minimal', 'is_emotionally_charged': False}
        sentiment_data_mock = {'label': 'neutral', 'bias_indicator': False, 'is_polarized': False, 'polarization_score': 0}
        
        score, indicator, explanation, tip, extras = TrustScoreCalculator.calculate(
            bias_score=0.2, emotion_score=0.1, sentiment_label='neutral', text="Neutral text.",
            emotion_data=emotion_data_mock, sentiment_data=sentiment_data_mock, bias_data=bias_data_mock
        )
        
        # Assert that _get_contextual_tip was called (implicitly, by checking its return value is used)
        self.assertEqual(tip, expected_tip_from_contextual)
        # We can also check that it was called with the generated risk_factors if we want more detail
        # For this, we'd need to know what risk_factors are generated by the inputs above.
        # In this case, risk_factors would likely be empty or minimal.
        mock_get_contextual_tip.assert_called_once()
        # Example: mock_get_contextual_tip.assert_called_once_with([]) # if no risk factors generated

if __name__ == '__main__':
    unittest.main()
