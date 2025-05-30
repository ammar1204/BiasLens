import unittest
from unittest.mock import MagicMock, patch
from biaslens.bias import BiasDetector, BiasTypeClassifier
from biaslens.utils import _model_cache # To clear cache between tests if necessary

class TestBiasDetector(unittest.TestCase):
    def setUp(self):
        # Clear model cache before each test to ensure mocks are fresh
        _model_cache.clear()

    @patch('biaslens.models.get_text_classification_pipeline')
    def test_detect_toxic_comment_above_threshold(self, mock_get_pipeline):
        # Mock the pipeline creation and its return value
        mock_hf_pipeline = MagicMock(return_value=[{'label': 'TOXIC', 'score': 0.9}])
        mock_get_pipeline.return_value = mock_hf_pipeline

        detector = BiasDetector(model_name="test_model", threshold=0.8) # model_name will be passed to mock
        is_biased, message = detector.detect("This is a toxic comment.")

        self.assertTrue(is_biased)
        self.assertIn("Potentially Biased - High Confidence", message)
        self.assertIn("0.900", message)
        mock_get_pipeline.assert_called_once_with("test_model")
        mock_hf_pipeline.assert_called_once_with("This is a toxic comment.")

    @patch('biaslens.models.get_text_classification_pipeline')
    def test_detect_neutral_comment_below_threshold(self, mock_get_pipeline):
        mock_hf_pipeline = MagicMock(return_value=[{'label': 'NOT_TOXIC', 'score': 0.9}])
        mock_get_pipeline.return_value = mock_hf_pipeline

        detector = BiasDetector(model_name="test_model", threshold=0.5)
        is_biased, message = detector.detect("This is a neutral comment.")

        self.assertFalse(is_biased)
        self.assertIn("Likely Neutral", message)
        self.assertIn("0.900", message)
        mock_hf_pipeline.assert_called_once_with("This is a neutral comment.")

    @patch('biaslens.models.get_text_classification_pipeline')
    def test_detect_model_without_explicit_labels(self, mock_get_pipeline):
        mock_hf_pipeline = MagicMock(return_value=[{'score': 0.75}])
        mock_get_pipeline.return_value = mock_hf_pipeline

        detector = BiasDetector(model_name="test_model", threshold=0.7)
        is_biased, message = detector.detect("Some comment.")
        self.assertTrue(is_biased)
        self.assertIn("Potentially Biased - Medium Confidence", message)
        self.assertIn("0.750", message)

    @patch('biaslens.models.get_text_classification_pipeline')
    def test_detect_error_handling(self, mock_get_pipeline):
        # Simulate error at the pipeline function level (e.g. model load fails in reality)
        mock_get_pipeline.return_value = MagicMock(side_effect=Exception("Model loading failed"))

        # Or simulate error at pipeline call level
        # mock_hf_pipeline = MagicMock(side_effect=Exception("Model inference failed"))
        # mock_get_pipeline.return_value = mock_hf_pipeline

        detector = BiasDetector(model_name="test_model_error")
        is_biased, message = detector.detect("Error test.")

        self.assertFalse(is_biased)
        # The error message now comes from the .detect method's try-except block
        self.assertIn("Bias detection analysis failed: Model loading failed", message)


    @patch('biaslens.models.get_text_classification_pipeline')
    def test_label_variation_label_1(self, mock_get_pipeline):
        mock_hf_pipeline = MagicMock(return_value=[{'label': 'LABEL_1', 'score': 0.95}])
        mock_get_pipeline.return_value = mock_hf_pipeline
        detector = BiasDetector(model_name="test_model", threshold=0.9)
        is_biased, message = detector.detect("Test LABEL_1")
        self.assertTrue(is_biased)
        self.assertIn("High Confidence", message)

    @patch('biaslens.models.get_text_classification_pipeline')
    def test_label_variation_label_0(self, mock_get_pipeline):
        mock_hf_pipeline = MagicMock(return_value=[{'label': 'LABEL_0', 'score': 0.95}])
        mock_get_pipeline.return_value = mock_hf_pipeline
        detector = BiasDetector(model_name="test_model", threshold=0.1)
        is_biased, message = detector.detect("Test LABEL_0")
        self.assertFalse(is_biased)
        self.assertIn("Likely Neutral", message)


class TestBiasTypeClassifier(unittest.TestCase):
    def setUp(self):
        _model_cache.clear()
        self.classifier_labels = [
            "political bias", "ethnic bias", "religious bias", "gender bias",
            "economic bias", "social bias", "ageism", "disability bias", "no bias"
        ]

    @patch('biaslens.models.get_zero_shot_classification_pipeline')
    def test_predict_political_bias(self, mock_get_pipeline):
        mock_hf_pipeline = MagicMock(return_value={
            'labels': ['political bias', 'gender bias', 'no bias'],
            'scores': [0.9, 0.05, 0.05]
        })
        mock_get_pipeline.return_value = mock_hf_pipeline

        # Pass a model_name, it will be used by the mock_get_pipeline call
        classifier = BiasTypeClassifier(model_name="test_zero_shot_model")
        result = classifier.predict("This is a political statement.")

        self.assertEqual(result['type'], 'political bias')
        self.assertEqual(result['confidence'], 90.0)
        self.assertEqual(len(result['all_predictions']), 3)
        mock_get_pipeline.assert_called_once_with("test_zero_shot_model")
        mock_hf_pipeline.assert_called_once_with("This is a political statement.", self.classifier_labels, multi_label=False)

    @patch('biaslens.models.get_zero_shot_classification_pipeline')
    def test_predict_no_bias_high_confidence(self, mock_get_pipeline):
        mock_hf_pipeline = MagicMock(return_value={
            'labels': ['no bias', 'political bias', 'gender bias'],
            'scores': [0.8, 0.1, 0.1]
        })
        mock_get_pipeline.return_value = mock_hf_pipeline

        classifier = BiasTypeClassifier(model_name="test_zero_shot_model")
        result = classifier.predict("This statement is perfectly neutral.")

        self.assertEqual(result['type'], 'neutral')
        self.assertEqual(result['confidence'], 80.0)

    @patch('biaslens.models.get_zero_shot_classification_pipeline')
    def test_predict_no_bias_low_confidence_chooses_next_best(self, mock_get_pipeline):
        mock_hf_pipeline = MagicMock(return_value={
            'labels': ['ethnic bias', 'no bias', 'gender bias'],
            'scores': [0.5, 0.4, 0.1]
        })
        mock_get_pipeline.return_value = mock_hf_pipeline

        classifier = BiasTypeClassifier(model_name="test_zero_shot_model")
        result = classifier.predict("A statement that could be ethnic, or maybe not.")
        self.assertEqual(result['type'], 'ethnic bias')
        self.assertEqual(result['confidence'], 50.0)

    @patch('biaslens.models.get_zero_shot_classification_pipeline')
    def test_predict_no_bias_low_confidence_and_other_bias_low_too(self, mock_get_pipeline):
        mock_hf_pipeline = MagicMock(return_value={
            'labels': ['no bias', 'political bias', 'gender bias'],
            'scores': [0.3, 0.1, 0.05]
        })
        mock_get_pipeline.return_value = mock_hf_pipeline
        classifier = BiasTypeClassifier(model_name="test_zero_shot_model")
        result = classifier.predict("A very ambiguous statement.")

        self.assertEqual(result['type'], 'political bias')
        self.assertEqual(result['confidence'], 10.0)


    @patch('biaslens.models.get_zero_shot_classification_pipeline')
    def test_predict_error_handling(self, mock_get_pipeline):
        mock_get_pipeline.return_value = MagicMock(side_effect=Exception("Classification failed"))

        classifier = BiasTypeClassifier(model_name="test_zero_shot_model_error")
        result = classifier.predict("Error test.")

        self.assertEqual(result['type'], 'analysis_error')
        self.assertEqual(result['confidence'], 0.0)
        self.assertIn("Bias type classification failed: Classification failed", result['error'])

if __name__ == '__main__':
    unittest.main()
