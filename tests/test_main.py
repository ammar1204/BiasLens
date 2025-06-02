import unittest
from fastapi.testclient import TestClient
from main import app # Assuming your FastAPI app instance is named 'app' in main.py

# Expected top-level keys from AnalyzeResponseModel (excluding detailed_sub_analyses for this check)
# This list should match the fields in AnalyzeResponseModel in main.py
EXPECTED_ANALYZE_RESPONSE_KEYS = [
    "trust_score",
    "indicator",
    "explanation",
    "tip",
    "primary_bias_type",
    "bias_details",
    "sentiment_details",
    "emotion_details",
    "pattern_highlights",
    "lightweight_nigerian_bias_assessment",
    # "detailed_sub_analyses" # Optional, so not checking for its presence by default in all responses
]

class TestMainApp(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_read_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to the BiasLens API!"})

    def test_analyze_endpoint_success_structure(self):
        """
        Test the /analyze endpoint for a successful response and basic structure.
        This test implicitly checks if Pydantic model validation is working.
        """
        response = self.client.post("/analyze", json={
            "text": "This is a test sentence for analysis.",
            "include_patterns": True, # Ensure pattern_highlights and lightweight_bias_assessment are populated
            "include_detailed_results": False # Keep response smaller for this structure check
        })
        self.assertEqual(response.status_code, 200)
        
        response_json = response.json()
        
        for key in EXPECTED_ANALYZE_RESPONSE_KEYS:
            self.assertIn(key, response_json, f"Key '{key}' missing from /analyze response")
        
        # Check that metadata is NOT present
        self.assertNotIn("metadata", response_json, "'metadata' field should be removed")

        # Basic type checks for nested models (existence implies Pydantic model was applied)
        self.assertIsInstance(response_json.get("sentiment_details"), dict)
        self.assertIsInstance(response_json.get("emotion_details"), dict)
        self.assertIsInstance(response_json.get("bias_details"), dict)
        self.assertIsInstance(response_json.get("pattern_highlights"), dict)
        
        # lightweight_nigerian_bias_assessment can be None if no patterns included,
        # but with include_patterns=True, it should be a dict (even if fields inside are None)
        if response_json.get("lightweight_nigerian_bias_assessment") is not None: # It can be None if patterns are off
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
        self.assertIn("lightweight_nigerian_bias", response_json["detailed_sub_analyses"])


    def test_quick_analyze_endpoint_success(self):
        """Test the /quick_analyze endpoint for a successful response."""
        response = self.client.post("/quick_analyze", json={"text": "Quick test."})
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        # Check for some expected keys in quick_analyze response
        self.assertIn("score", response_json)
        self.assertIn("indicator", response_json)
        self.assertIn("explanation", response_json)
        self.assertIn("tip", response_json)
        self.assertIn("inferred_bias_type", response_json) # From LightweightNigerianBias


if __name__ == "__main__":
    unittest.main()
