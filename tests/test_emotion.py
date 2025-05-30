import unittest
from unittest.mock import MagicMock, patch
import torch
import torch.nn.functional as F
from biaslens.emotion import EmotionClassifier
from biaslens.utils import _model_cache

class TestEmotionClassifier(unittest.TestCase):
    def setUp(self):
        _model_cache.clear()
        self.default_model_name = "bhadresh-savani/distilbert-base-uncased-emotion"
        # These labels align with j-hartmann/emotion-english-distilroberta-base or similar
        self.classifier_labels = [
            'admiration', 'amusement', 'anger', 'annoyance', 'approval', 'caring',
            'confusion', 'curiosity', 'desire', 'disappointment', 'disapproval',
            'disgust', 'embarrassment', 'excitement', 'fear', 'gratitude', 'grief',
            'joy', 'love', 'nervousness', 'optimism', 'pride', 'realization',
            'relief', 'remorse', 'sadness', 'surprise', 'neutral'
        ]

    @patch('biaslens.models.get_tokenizer_and_model')
    def test_classify_primary_emotion_joy(self, mock_get_tokenizer_and_model):
        # Mock tokenizer
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.return_value = {
            "input_ids": torch.tensor([[101, 102]]),
            "attention_mask": torch.tensor([[1, 1]])
        }

        # Mock model
        mock_model_instance = MagicMock()
        dummy_logits = torch.zeros(1, len(self.classifier_labels))
        joy_index = self.classifier_labels.index('joy')
        dummy_logits[0, joy_index] = 3.0
        dummy_logits[0, self.classifier_labels.index('sadness')] = -1.0
        mock_model_instance.return_value = MagicMock(logits=dummy_logits)

        # Configure mock_get_tokenizer_and_model to return our instances
        mock_get_tokenizer_and_model.return_value = (mock_tokenizer_instance, mock_model_instance)

        classifier = EmotionClassifier(model_name=self.default_model_name)
        classifier.labels = self.classifier_labels

        result = classifier.classify("This is a joyful statement!")

        self.assertEqual(result['label'], 'joy')
        self.assertGreater(result['confidence'], 50.0)
        self.assertIn('joy', [e['emotion'] for e in result['top_emotions']])
        self.assertEqual(result['intensity_category'], 'positive')
        self.assertEqual(result['manipulation_risk'], 'minimal')
        self.assertFalse(result['is_emotionally_charged'])

        mock_get_tokenizer_and_model.assert_called_once_with(self.default_model_name, from_tf_fallback=False)
        mock_tokenizer_instance.assert_called_once_with("This is a joyful statement!", return_tensors="pt", truncation=True, max_length=512)
        mock_model_instance.assert_called_once()


    @patch('biaslens.models.get_tokenizer_and_model')
    def test_classify_top_k_emotions(self, mock_get_tokenizer_and_model):
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.return_value = {"input_ids": torch.tensor([[1,2]]), "attention_mask": torch.tensor([[1,1]])}

        mock_model_instance = MagicMock()
        dummy_logits = torch.rand(1, len(self.classifier_labels))
        mock_model_instance.return_value = MagicMock(logits=dummy_logits)

        mock_get_tokenizer_and_model.return_value = (mock_tokenizer_instance, mock_model_instance)

        classifier = EmotionClassifier(model_name=self.default_model_name)
        classifier.labels = self.classifier_labels

        result = classifier.classify("Some text.", top_k=3)
        self.assertEqual(len(result['top_emotions']), 3)

        result_top_1 = classifier.classify("Some text.", top_k=1)
        self.assertEqual(len(result_top_1['top_emotions']), 1)

    @patch('biaslens.models.get_tokenizer_and_model')
    def test_emotion_intensity_and_manipulation(self, mock_get_tokenizer_and_model):
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.return_value = {"input_ids": torch.tensor([[1,2]]), "attention_mask": torch.tensor([[1,1]])}
        mock_model_instance = MagicMock()
        mock_get_tokenizer_and_model.return_value = (mock_tokenizer_instance, mock_model_instance)

        classifier = EmotionClassifier(model_name=self.default_model_name)
        classifier.labels = self.classifier_labels

        # Test high intensity, high manipulation risk (e.g. anger with high confidence)
        anger_index = self.classifier_labels.index('anger')
        logits_anger = torch.zeros(1, len(self.classifier_labels))
        logits_anger[0, anger_index] = 5.0
        mock_model_instance.return_value = MagicMock(logits=logits_anger)
        result_anger = classifier.classify("I am very angry!")
        self.assertEqual(result_anger['label'], 'anger')
        self.assertEqual(result_anger['intensity_category'], 'high_intensity')
        self.assertEqual(result_anger['manipulation_risk'], 'high')
        self.assertTrue(result_anger['is_emotionally_charged'])

        # Test medium intensity, medium manipulation risk (e.g. annoyance with moderate confidence)
        annoyance_index = self.classifier_labels.index('annoyance')
        logits_annoyance = torch.zeros(1, len(self.classifier_labels))
        logits_annoyance[0, annoyance_index] = 2.0
        mock_model_instance.return_value = MagicMock(logits=logits_annoyance)

        with patch('torch.nn.functional.softmax', return_value=torch.tensor([[0.01] * annoyance_index + [0.65] + [0.01] * (len(self.classifier_labels) - annoyance_index -1)])):
             result_annoyance = classifier.classify("This is annoying.")
        self.assertEqual(result_annoyance['label'], 'annoyance')
        self.assertEqual(result_annoyance['intensity_category'], 'medium_intensity')
        self.assertEqual(result_annoyance['manipulation_risk'], 'medium')
        self.assertFalse(result_annoyance['is_emotionally_charged'])

    @patch('biaslens.models.get_tokenizer_and_model')
    def test_is_emotionally_charged(self, mock_get_tokenizer_and_model):
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.return_value = {"input_ids": torch.tensor([[1,2]]), "attention_mask": torch.tensor([[1,1]])}
        mock_model_instance = MagicMock()
        mock_get_tokenizer_and_model.return_value = (mock_tokenizer_instance, mock_model_instance)

        classifier = EmotionClassifier(model_name=self.default_model_name)
        classifier.labels = self.classifier_labels

        fear_index = self.classifier_labels.index('fear')
        logits_fear_high_conf = torch.zeros(1, len(self.classifier_labels))
        logits_fear_high_conf[0, fear_index] = 3.0
        mock_model_instance.return_value = MagicMock(logits=logits_fear_high_conf)
        result_fear_high = classifier.classify("This is terrifying!")
        self.assertTrue(result_fear_high['is_emotionally_charged'])

        confusion_index = self.classifier_labels.index('confusion')
        logits_confusion_high_conf = torch.zeros(1, len(self.classifier_labels))
        logits_confusion_high_conf[0, confusion_index] = 3.0
        mock_model_instance.return_value = MagicMock(logits=logits_confusion_high_conf)
        result_confusion_high = classifier.classify("I am confused.")
        self.assertFalse(result_confusion_high['is_emotionally_charged'])

    @patch('biaslens.models.get_tokenizer_and_model')
    def test_classify_error_handling(self, mock_get_tokenizer_and_model):
        mock_get_tokenizer_and_model.side_effect = Exception("Model loading failed")

        # Instantiation will fail if get_tokenizer_and_model fails
        with self.assertRaises(Exception): # Check if the constructor raises the error
             EmotionClassifier(model_name="failing_model")

        # To test error during classify (e.g. tokenizer call fails after successful init)
        _model_cache.clear() # Ensure it tries to load
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.side_effect = Exception("Tokenizer call failed")
        mock_model_instance = MagicMock()
        mock_get_tokenizer_and_model.side_effect = None # Reset side effect for this part
        mock_get_tokenizer_and_model.return_value = (mock_tokenizer_instance, mock_model_instance)

        classifier = EmotionClassifier(model_name=self.default_model_name)
        classifier.labels = self.classifier_labels
        result = classifier.classify("Some text.")

        self.assertEqual(result['label'], 'analysis_error')
        self.assertEqual(result['confidence'], 0.0)
        self.assertIn("Emotion classification failed: Tokenizer call failed", result['error'])


if __name__ == '__main__':
    unittest.main()
