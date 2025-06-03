import unittest
from fastapi.testclient import TestClient
from main import app # Assuming your FastAPI app instance is named 'app' in main.py

# Expected top-level keys from the new "Core Solution" AnalyzeResponseModel
EXPECTED_ANALYZE_RESPONSE_KEYS = [
    "trust_score",
    "indicator",
    "explanation",
    "tip",
    "tone_analysis",
    "bias_analysis",
    "manipulation_analysis",
    "veracity_signals",
    "lightweight_nigerian_bias_assessment",
    # "detailed_sub_analyses" is optional and checked in a separate test
]

class TestMainApp(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_read_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to the BiasLens API!"})

    def test_analyze_endpoint_success_core_solution_structure(self):
        """
        Test the /analyze endpoint for a successful response and the new "Core Solution" structure.
        This test implicitly checks if Pydantic model validation is working.
        """
        response = self.client.post("/analyze", json={
            "text": "This is a test sentence for analysis.",
            "include_patterns": True,
            "include_detailed_results": False
        })
        self.assertEqual(response.status_code, 200)

        response_json = response.json()

        for key in EXPECTED_ANALYZE_RESPONSE_KEYS:
            self.assertIn(key, response_json, f"Key '{key}' missing from /analyze response")

        # Check that old top-level summary keys are NOT present
        self.assertNotIn("primary_bias_type", response_json, "'primary_bias_type' should be nested in 'bias_analysis'")
        self.assertNotIn("sentiment_details", response_json, "'sentiment_details' should be nested in 'tone_analysis'")
        self.assertNotIn("emotion_details", response_json, "'emotion_details' should be nested in 'tone_analysis'")
        self.assertNotIn("bias_details", response_json, "'bias_details' (old structure) should be replaced by 'bias_analysis'")
        self.assertNotIn("pattern_highlights", response_json, "'pattern_highlights' (old structure) should be replaced by 'manipulation_analysis' and 'veracity_signals'")


        # Basic type checks for new nested models (existence implies Pydantic model was applied)
        self.assertIsInstance(response_json.get("tone_analysis"), dict)
        self.assertIsInstance(response_json.get("bias_analysis"), dict)
        self.assertIsInstance(response_json.get("manipulation_analysis"), dict)
        self.assertIsInstance(response_json.get("veracity_signals"), dict)

        if response_json.get("lightweight_nigerian_bias_assessment") is not None:
             self.assertIsInstance(response_json.get("lightweight_nigerian_bias_assessment"), dict)


    def test_analyze_endpoint_include_detailed_results(self):
        """Test /analyze with include_detailed_results=True."""
        response = self.client.post("/analyze", json={
            "text": "Detailed test.",
            "include_detailed_results": True,
            "include_patterns": True
        })
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertIn("detailed_sub_analyses", response_json)
        self.assertIsInstance(response_json["detailed_sub_analyses"], dict)
        self.assertIn("sentiment", response_json["detailed_sub_analyses"]) # Original full sentiment
        self.assertIn("emotion", response_json["detailed_sub_analyses"])   # Original full emotion
        self.assertIn("bias", response_json["detailed_sub_analyses"])      # Original full bias (ML)
        self.assertIn("patterns", response_json["detailed_sub_analyses"])  # Original full patterns
        self.assertIn("lightweight_nigerian_bias", response_json["detailed_sub_analyses"]) # Original full lightweight


    def test_quick_analyze_endpoint_success(self):
        """Test the /quick_analyze endpoint for a successful response."""
        response = self.client.post("/quick_analyze", json={"text": "Quick test."})
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertIn("score", response_json)
        self.assertIn("indicator", response_json)
        self.assertIn("explanation", response_json)
        self.assertIn("tip", response_json)
        self.assertIn("inferred_bias_type", response_json)


if __name__ == "__main__":
    unittest.main()
