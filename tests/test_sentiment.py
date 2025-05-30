import unittest
from unittest.mock import MagicMock, patch
import torch
import torch.nn.functional as F
from biaslens.sentiment import SentimentAnalyzer
from biaslens.utils import _model_cache

class TestSentimentAnalyzer(unittest.TestCase):
    def setUp(self):
        _model_cache.clear()
        self.default_model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        self.sentiment_labels = ['negative', 'neutral', 'positive']

    @patch('biaslens.models.get_tokenizer_and_model')
    def test_analyze_positive_sentiment(self, mock_get_tokenizer_and_model):
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.model_max_length = 512
        mock_tokenizer_instance.return_value = {"input_ids": torch.tensor([[1,2]]), "attention_mask": torch.tensor([[1,1]])}

        mock_model_instance = MagicMock()
        dummy_logits = torch.tensor([[-1.0, 0.5, 2.5]])
        mock_model_instance.return_value = MagicMock(logits=dummy_logits)

        mock_get_tokenizer_and_model.return_value = (mock_tokenizer_instance, mock_model_instance)

        analyzer = SentimentAnalyzer(model_name=self.default_model_name)
        result = analyzer.analyze("This is a wonderful day!")

        self.assertEqual(result['label'], 'positive')
        self.assertGreater(result['confidence'], 0.5)
        self.assertEqual(result['sentiment_strength'], 'strong')
        self.assertFalse(result['bias_indicator'])
        self.assertGreater(result['polarization_score'], 0.5)
        self.assertTrue(result['is_polarized'])
        self.assertEqual(result['emotional_tone'], 'highly_positive')

        mock_get_tokenizer_and_model.assert_called_once_with(self.default_model_name, from_tf_fallback=True)

    @patch('biaslens.models.get_tokenizer_and_model')
    def test_analyze_negative_sentiment_with_bias_indicator(self, mock_get_tokenizer_and_model):
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.model_max_length = 512
        mock_tokenizer_instance.return_value = {"input_ids": torch.tensor([[1,2]]), "attention_mask": torch.tensor([[1,1]])}

        mock_model_instance = MagicMock()
        dummy_logits = torch.tensor([[3.0, -2.0, -3.0]])
        mock_model_instance.return_value = MagicMock(logits=dummy_logits)

        mock_get_tokenizer_and_model.return_value = (mock_tokenizer_instance, mock_model_instance)

        analyzer = SentimentAnalyzer(model_name=self.default_model_name)
        result = analyzer.analyze("This is terrible and unacceptable!")

        self.assertEqual(result['label'], 'negative')
        self.assertGreaterEqual(result['confidence'], 0.8)
        self.assertEqual(result['sentiment_strength'], 'strong')
        self.assertTrue(result['bias_indicator'])

    @patch('biaslens.models.get_tokenizer_and_model') # Still need to mock for __init__
    def test_analyze_empty_or_short_text(self, mock_get_tokenizer_and_model):
        # Configure mock to return dummy tokenizer/model for __init__ to pass
        mock_get_tokenizer_and_model.return_value = (MagicMock(), MagicMock())
        analyzer = SentimentAnalyzer(model_name=self.default_model_name)

        # Test empty string
        result_empty = analyzer.analyze("")
        self.assertEqual(result_empty['label'], 'neutral')
        self.assertEqual(result_empty['confidence'], 0.5) # Default from empty text handling
        self.assertEqual(result_empty['sentiment_strength'], 'weak')

        # Test short string
        result_short = analyzer.analyze("ok") # Should also hit the empty/short text condition
        self.assertEqual(result_short['label'], 'neutral')
        self.assertEqual(result_short['confidence'], 0.5) # Default from empty text handling

    @patch('biaslens.models.get_tokenizer_and_model') # Mock for __init__
    def test_preprocess_text(self, mock_get_tokenizer_and_model):
        mock_get_tokenizer_and_model.return_value = (MagicMock(), MagicMock())
        analyzer = SentimentAnalyzer(model_name=self.default_model_name)
        text = "  @user1 check this out http://example.com/page   !!! ?? .... "
        expected = "@USER check this out URL ! ? ..." # Based on current _preprocess_text logic
        self.assertEqual(analyzer._preprocess_text(text), expected)

        text_no_change = "Normal text."
        self.assertEqual(analyzer._preprocess_text(text_no_change), "Normal text.")

    @patch('biaslens.models.get_tokenizer_and_model') # Mock for __init__
    def test_calculate_sentiment_strength(self, mock_get_tokenizer_and_model):
        mock_get_tokenizer_and_model.return_value = (MagicMock(), MagicMock())
        analyzer = SentimentAnalyzer() # __init__ needs to resolve
        self.assertEqual(analyzer._calculate_sentiment_strength(0.3, {}), 'weak')
        self.assertEqual(analyzer._calculate_sentiment_strength(0.6, {}), 'moderate')
        self.assertEqual(analyzer._calculate_sentiment_strength(0.8, {}), 'strong')

    @patch('biaslens.models.get_tokenizer_and_model') # Mock for __init__
    def test_check_bias_indicator(self, mock_get_tokenizer_and_model):
        mock_get_tokenizer_and_model.return_value = (MagicMock(), MagicMock())
        analyzer = SentimentAnalyzer() # __init__ needs to resolve
        # Strong negative
        self.assertTrue(analyzer._check_bias_indicator('negative', 0.85, {'negative': 0.85, 'neutral': 0.1, 'positive': 0.05}))
        # Polarized (low neutral, high confidence in non-neutral)
        self.assertTrue(analyzer._check_bias_indicator('positive', 0.75, {'negative': 0.1, 'neutral': 0.15, 'positive': 0.75}))
        # Not biased
        self.assertFalse(analyzer._check_bias_indicator('neutral', 0.9, {'negative': 0.05, 'neutral': 0.9, 'positive': 0.05}))
        self.assertFalse(analyzer._check_bias_indicator('positive', 0.6, {'negative': 0.1, 'neutral': 0.3, 'positive': 0.6}))


    @patch('biaslens.models.get_tokenizer_and_model') # Mock for __init__
    def test_get_emotional_tone(self, mock_get_tokenizer_and_model):
        mock_get_tokenizer_and_model.return_value = (MagicMock(), MagicMock())
        analyzer = SentimentAnalyzer() # __init__ needs to resolve
        self.assertEqual(analyzer._get_emotional_tone({'negative': 0.7, 'positive': 0.1, 'neutral': 0.2}), 'highly_negative')
        self.assertEqual(analyzer._get_emotional_tone({'negative': 0.1, 'positive': 0.7, 'neutral': 0.2}), 'highly_positive')
        self.assertEqual(analyzer._get_emotional_tone({'negative': 0.1, 'positive': 0.2, 'neutral': 0.7}), 'neutral')
        self.assertEqual(analyzer._get_emotional_tone({'negative': 0.4, 'positive': 0.2, 'neutral': 0.4}), 'negative_leaning')
        self.assertEqual(analyzer._get_emotional_tone({'negative': 0.2, 'positive': 0.4, 'neutral': 0.4}), 'positive_leaning')
        self.assertEqual(analyzer._get_emotional_tone({'negative': 0.4, 'positive': 0.45, 'neutral': 0.15}), 'mixed') # Example of mixed
        self.assertEqual(analyzer._get_emotional_tone({'negative': 0.3, 'positive': 0.3, 'neutral': 0.4}), 'balanced_or_neutral')


    @patch('biaslens.models.get_tokenizer_and_model') # Mock for __init__ of SentimentAnalyzer
    @patch.object(SentimentAnalyzer, 'analyze') # Mocking its own analyze method for sub-calls
    def test_analyze_headline_vs_content(self, mock_self_analyze, mock_get_tokenizer_and_model_init):
        # Mock for the __init__ call
        mock_get_tokenizer_and_model_init.return_value = (MagicMock(), MagicMock())
        analyzer = SentimentAnalyzer()

        # Case 1: Matching sentiments (both positive)
        # mock_self_analyze is the mock for analyzer.analyze called by analyze_headline_vs_content
        mock_self_analyze.side_effect = [
            { # Headline
                'label': 'positive', 'confidence': 0.9,
                'all_scores': {'negative': 0.05, 'neutral': 0.05, 'positive': 0.9},
            },
            { # Content
                'label': 'positive', 'confidence': 0.8,
                'all_scores': {'negative': 0.1, 'neutral': 0.1, 'positive': 0.8}
            }
        ]
        result_match = analyzer.analyze_headline_vs_content("Great news!", "The event was a success.")
        self.assertFalse(result_match['is_clickbait_likely'])
        self.assertEqual(result_match['mismatch_level'], 'low')
        self.assertLess(result_match['mismatch_score'], 0.2)

        # Case 2: Mismatching sentiments (headline positive, content negative)
        mock_self_analyze.reset_mock()
        mock_self_analyze.side_effect = [
            { # Headline
                'label': 'positive', 'confidence': 0.95,
                'all_scores': {'negative': 0.02, 'neutral': 0.03, 'positive': 0.95},
            },
            { # Content
                'label': 'negative', 'confidence': 0.9,
                'all_scores': {'negative': 0.9, 'neutral': 0.05, 'positive': 0.05}
            }
        ]
        result_mismatch = analyzer.analyze_headline_vs_content("You won't believe this!", "It was a total disaster.")
        self.assertTrue(result_mismatch['is_clickbait_likely'])
        self.assertIn(result_mismatch['mismatch_level'], ['high', 'medium'])
        self.assertAlmostEqual(result_mismatch['mismatch_score'], 0.9, places=2)


    @patch('biaslens.models.get_tokenizer_and_model')
    def test_analyze_error_handling(self, mock_get_tokenizer_and_model):
        # Scenario 1: Error during model loading (in __init__)
        _model_cache.clear()
        mock_get_tokenizer_and_model.side_effect = Exception("Model loading failed in __init__")
        with self.assertRaisesRegex(Exception, "Model loading failed in __init__"):
            SentimentAnalyzer(model_name="failing_model_init")

        # Scenario 2: Error during model inference (in analyze method)
        _model_cache.clear()
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.model_max_length = 512
        mock_model_instance = MagicMock()
        mock_model_instance.side_effect = Exception("Inference failed") # model(**encoded_input) fails

        mock_get_tokenizer_and_model.side_effect = None # Reset side effect for successful init
        mock_get_tokenizer_and_model.return_value = (mock_tokenizer_instance, mock_model_instance)

        analyzer = SentimentAnalyzer(model_name="error_model_inference")
        result = analyzer.analyze("Some text")

        self.assertEqual(result['label'], 'neutral')
        self.assertEqual(result['confidence'], 0.0)
        self.assertIn("error", result)
        self.assertIn("Inference failed", result['error'])


if __name__ == '__main__':
    unittest.main()
