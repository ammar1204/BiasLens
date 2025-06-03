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

# Expected top-level keys from the new "Core Solution" QuickAnalysisResponseModel
EXPECTED_QUICK_ANALYZE_RESPONSE_KEYS = [
    "score",
    "indicator",
    "explanation",
    "tip",
    "tone_analysis",
    "bias_analysis",
    "manipulation_analysis",
    "veracity_signals",
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

        self.assertNotIn("primary_bias_type", response_json, "'primary_bias_type' (old top-level) should be nested in 'bias_analysis' for /analyze")
        self.assertNotIn("sentiment_details", response_json)
        self.assertNotIn("emotion_details", response_json)
        self.assertNotIn("bias_details", response_json) # old structure
        self.assertNotIn("pattern_highlights", response_json)

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
        self.assertIn("sentiment", response_json["detailed_sub_analyses"])
        self.assertIn("emotion", response_json["detailed_sub_analyses"])
        self.assertIn("bias", response_json["detailed_sub_analyses"])
        self.assertIn("patterns", response_json["detailed_sub_analyses"])
        self.assertIn("lightweight_nigerian_bias", response_json["detailed_sub_analyses"])

    def test_quick_analyze_endpoint_success_core_solution_structure(self):
        """Test the /quick_analyze endpoint for a successful response and new Core Solution structure."""
        response = self.client.post("/quick_analyze", json={"text": "Quick test."})
        self.assertEqual(response.status_code, 200)
        response_json = response.json()

        for key in EXPECTED_QUICK_ANALYZE_RESPONSE_KEYS:
            self.assertIn(key, response_json, f"Key '{key}' missing from /quick_analyze response")

        # Ensure old flat bias keys are not at the top level
        self.assertNotIn("inferred_bias_type", response_json)
        self.assertNotIn("bias_category", response_json)
        self.assertNotIn("bias_target", response_json)
        self.assertNotIn("matched_keywords", response_json)

        # Basic type checks for new nested models
        self.assertIsInstance(response_json.get("tone_analysis"), dict, "'tone_analysis' should be a dict")
        self.assertIsInstance(response_json.get("bias_analysis"), dict, "'bias_analysis' should be a dict")
        self.assertIsInstance(response_json.get("manipulation_analysis"), dict, "'manipulation_analysis' should be a dict")
        self.assertIsInstance(response_json.get("veracity_signals"), dict, "'veracity_signals' should be a dict")

if __name__ == "__main__":
    unittest.main()
