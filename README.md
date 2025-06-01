# BiasLens

## Description
BiasLens is a project featuring a Python library and a FastAPI backend designed to detect and analyze various types of bias, emotional tone, and other characteristics in text. It provides both quick and comprehensive analysis options. This project was initially developed for a hackathon and has been expanded to include an API and a frontend interface.
Live link: https://bias-lens-n86a-ntc5pvio7-ammars-projects-7c463369.vercel.app/

## Features
- Analyzes text for potential bias using pre-trained Hugging Face models.
- Classifies the type of bias (e.g., political, ethnic, religious).
- Detects emotional tone and sentiment.
- Identifies Nigerian-specific patterns, clickbait, and potential fake news indicators.
- Calculates a trust score for the analyzed text.
- Offers API endpoints for `quick_analyze` and `analyze` functionalities.
- Includes a Next.js frontend for user interaction (under the `FRONTEND/` directory).

## Project Structure

```
.
├── FRONTEND/                 # Next.js frontend application
├── biaslens/                 # Core Python library for text analysis
│   ├── __init__.py           # Initializes the 'biaslens' package
│   ├── analyzer.py           # Orchestrates analysis components (quick_analyze, analyze)
│   ├── bias.py               # Bias detection and classification logic
│   ├── emotion.py            # Emotion detection logic
│   ├── models.py             # Placeholder for future model management
│   ├── patterns.py           # Pattern matching for Nigerian context, fake news, etc.
│   ├── sentiment.py          # Sentiment analysis logic
│   ├── trust.py              # Trust score calculation logic
│   └── utils.py              # Shared utilities (e.g., model cache)
├── tests/                    # Unit tests for the Python backend
│   ├── __init__.py           # Initializes the 'tests' package
│   └── test_analyzer.py      # Tests for the analyzer module
├── .gitignore                # Specifies intentionally untracked files
├── main.py                   # FastAPI application exposing the BiasLens API
├── requirements.txt          # Python dependencies for the backend/API
├── test.py                   # Script for testing biaslens library (legacy/integration)
└── README.md                 # This file
```

## Backend Setup and API

### Installation
1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url> # Replace with the actual URL
    cd <repository-folder>
    ```
2.  **Install Python dependencies:**
    Ensure you have Python 3.8+ installed. Then, install the required packages using the root `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
    This will install FastAPI, Uvicorn, Transformers, PyTorch, and other necessary libraries.

### Running the API
1.  Use Uvicorn to run the FastAPI application located in `main.py`:
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
2.  The API will be available at `http://127.0.0.1:8000` (or your local IP if accessed from another device on the network).
3.  Interactive API documentation (Swagger UI) can be accessed at `http://127.0.0.1:8000/docs`.
4.  A simple health check endpoint is available at `GET /`.

### API Endpoints

The API expects JSON requests and returns JSON responses.

1.  **Quick Analysis**
    *   **Endpoint:** `POST /quick_analyze`
    *   **Request Body:**
        ```json
        {
          "text": "Your text to analyze here."
        }
        ```
    *   **Description:** Performs a faster, more lightweight analysis focusing on sentiment and basic patterns.
    *   **Example Response (Illustrative):**
        ```json
        {
          "score": 60,
          "indicator": "🟡 Caution",
          "explanation": ["Contains clickbait patterns"],
          "tip": "For a more comprehensive analysis, use the full analyze function."
        }
        ```

2.  **Comprehensive Analysis**
    *   **Endpoint:** `POST /analyze`
    *   **Request Body:**
        ```json
        {
          "text": "Your text to analyze here.",
          "headline": "Optional: Headline of the article.",
          "include_patterns": true,
          "include_detailed_results": true
        }
        ```
    *   **Description:** Performs a full, in-depth analysis including bias type classification, emotional analysis, detailed pattern matching, and trust score calculation.
        The request body can also include `headline` (string, optional), `include_patterns` (boolean, defaults to `true` in the core analyzer), and `include_detailed_results` (boolean, defaults to `false` in the core analyzer) to customize the analysis. The `detailed_sub_analyses` field in the response will only be populated if `include_detailed_results` is set to `true`. The `patterns` sub-field within `detailed_sub_analyses` depends on `include_patterns` being `true`.
    *   **Example Response (Illustrative, with `include_detailed_results=True` and `include_patterns=True`):**
        ```json
        {
          "trust_score": 75,
          "indicator": "🟢 Generally Trustworthy",
          "explanation": [
            "The content appears largely objective with neutral sentiment.",
            "No significant emotional manipulation tactics identified.",
            "Bias analysis did not flag strong indications of specific bias types."
          ],
          "tip": "While generally trustworthy, always consider the source and context. For critical information, seek diverse perspectives.",
          "primary_bias_type": null,
          "metadata": {
            "component_processing_times": {
              "sentiment_analysis": 0.0152,
              "emotion_analysis": 0.0521,
              "bias_analysis": 0.0803,
              "pattern_analysis": 0.0025,
              "trust_score_calculation": 0.0030,
              "overall_assessment_generation": 0.0006
            },
            "overall_processing_time_seconds": 0.1537,
            "text_length": 180,
            "initialized_components": ["sentiment", "emotion", "bias_detection", "bias_classification"],
            "analysis_timestamp": 1678886400.123456
          },
          "detailed_sub_analyses": {
            "sentiment": {
              "label": "neutral",
              "confidence": 0.85,
              "all_scores": {
                "negative": 0.05,
                "neutral": 0.85,
                "positive": 0.10
              }
            },
            "emotion": {
              "label": "neutral",
              "confidence": 0.90,
              "is_emotionally_charged": false,
              "manipulation_risk": "low"
            },
            "bias": {
              "flag": false,
              "label": "No significant bias detected.",
              "type_analysis": {
                "type": "neutral",
                "confidence": 0.95
              },
              "detected": false
            },
            "patterns": {
              "nigerian_patterns": {
                "has_triggers": false,
                "has_clickbait": false,
                "trigger_details": [],
                "clickbait_details": []
              },
              "fake_news": {
                "detected": false,
                "details": {
                  "risk_level": "low",
                  "matched_phrases": []
                }
              },
              "viral_manipulation": {
                "engagement_bait_score": 0.1,
                "sensationalism_score": 0.05,
                "is_potentially_viral": false
              }
            }
          }
        }
        ```

**Note on API Usage Examples:**
The example responses above are illustrative. The actual structure and content can vary based on the input text and analysis parameters. The full structure can be explored via the `/docs` endpoint when the API is running. You can use tools like `curl` or Postman, or Python's `requests` library to interact with these endpoints.

For example, using `curl`:
```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{"text": "This is a test sentence for the BiasLens API."}'
```

## Frontend Application
The `FRONTEND/` directory contains a Next.js application that provides a user interface for interacting with the BiasLens API. Please refer to `FRONTEND/README.md` for instructions on how to set up and run the frontend.

The frontend makes calls to the backend API. Note that the `FRONTEND/app/analyze/page.tsx` file currently uses `/api/analyze` for deep analysis. If you are running the frontend and backend separately without a proxy, ensure the API endpoint URLs in the frontend configuration match the running backend address (e.g., `http://localhost:8000/analyze`). The `userId` field sent by the frontend is not currently used by the backend Pydantic model.

## Models Used
The `biaslens` Python library utilizes the following Hugging Face models by default:

-   **Bias Detection (Toxicity):** `martin-ha/toxic-comment-model` (used in `biaslens/bias.py` within `BiasDetector`)
-   **Bias Type Classification (Zero-Shot):** `facebook/bart-large-mnli` (used in `biaslens/bias.py` within `BiasTypeClassifier`)
-   **Emotion Classification:** `bhadresh-savani/distilbert-base-uncased-emotion` (used in `biaslens/emotion.py` within `EmotionClassifier`)
-   **Sentiment Analysis:** `cardiffnlp/twitter-roberta-base-sentiment-latest` (used in `biaslens/sentiment.py` within `SentimentAnalyzer`)

These models are downloaded and cached by the `transformers` library upon first use.

## Using the `biaslens` Library Directly (Python)
While the primary way to use this project is through the API, the `biaslens` Python library can also be used directly.

```python
from biaslens.analyzer import quick_analyze, analyze

# Quick Analysis
text_to_analyze_quick = "This is a sample text to check for bias quickly."
quick_results = quick_analyze(text_to_analyze_quick)
print("Quick Analysis Results:")
print(quick_results)

# Comprehensive Analysis
text_to_analyze_full = "This is another sample text which might contain some subtle biases that require a deeper look."
full_analysis = analyze(text_to_analyze_full)
print("\nComprehensive Analysis Results:")
print(full_analysis)
```
Refer to the example outputs under the "API Endpoints" section for an idea of the structure of the returned dictionaries.

## Future Improvements
-   Support for more languages beyond English.
-   Fine-tuning models for Nigerian-specific contexts for better accuracy.
-   More sophisticated handling of nuanced and coded language.
-   Integration with social media platforms for real-time analysis.
-   User accounts and history for API usage.
-   Full implementation of `biaslens/models.py` for centralized model management.

## Contributing
Contributions are welcome! Please follow these general steps:
1.  Fork the repository.
2.  Create a new branch (`git checkout -b your-feature-name`).
3.  Make your changes and commit them.
4.  Ensure your changes are well-tested. Add tests if applicable.
5.  Open a pull request against the main branch.

## License
This project is currently unlicensed. Consider adding an open-source license (e.g., MIT, Apache 2.0) if you plan to share or distribute this code widely.

## Hackathon Project
This project was initiated as part of a hackathon, aiming to create a tool for identifying potential bias in textual content, and has since evolved.
