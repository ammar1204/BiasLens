# BiasLens

## Description
BiasLens is an open-source text analysis tool born out of a hackathon project and continuously evolving. It provides a Python library and a FastAPI backend to detect and analyze various textual characteristics, with a focus on identifying potential biases, emotional tones, and manipulative patterns. Offering both quick, pattern-based insights and comprehensive, model-driven analysis, BiasLens aims to promote media literacy by providing users with nuanced understanding of text. The project also includes a Next.js frontend for interactive use.

## Features
- **Comprehensive Analysis (Deep Dive):**
  - Utilizes pre-trained Hugging Face models to analyze text for potential bias.
  - Classifies bias by type (e.g., political, ethnic, religious) using ML models.
  - Detects detailed emotional tone and sentiment scores.
- **Quick Analysis (Pattern-Based):**
  - Provides rapid insights focusing on sentiment and basic textual patterns.
  - Includes lightweight, pattern-based detection of potential bias types, especially for Nigerian contexts.
- **Common Features:**
  - Identifies Nigerian-specific linguistic patterns, clickbait indicators, and potential fake news markers.
  - Calculates an overall trust score for the analyzed text.
  - Returns actionable, educational tips related to media literacy to help users interpret results and learn.
- **API & Frontend:**
  - Exposes functionalities via a FastAPI backend with `/quick_analyze` and `/analyze` endpoints.
  - Includes an interactive Next.js frontend for easy text submission and visualization of results.

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
│   ├── test_analyzer.py      # Tests for the analyzer module
│   ├── test_main.py          # Tests for the FastAPI app (API endpoints)
│   └── test_trust.py         # Tests for the trust score calculation
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

The API expects JSON requests and returns JSON responses. The structure of the responses is defined by Pydantic models in `main.py`, ensuring validated and consistent output.

1.  **Quick Analysis**
    *   **Endpoint:** `POST /quick_analyze`
    *   **Request Body:**
        ```json
        {
          "text": "Your text to analyze here."
        }
        ```
    *   **Description:** Performs a faster, more lightweight analysis focusing on sentiment and basic patterns, including pattern-based Nigerian bias detection.
    *   **Example Response:**
        ```json
        {
          "score": 65,
          "indicator": "🟡 Caution",
          "explanation": "Quick check found: potential sentiment bias. Specific patterns suggest: Anti-Labour Party political bias.",
          "tip": "Verify information before sharing. Check multiple reputable sources to confirm a story's accuracy.",
          "inferred_bias_type": "Anti-Labour Party political bias",
          "bias_category": "political",
          "bias_target": "Labour Party",
          "matched_keywords": ["labour party", "obi"]
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
    *   **Description:** Performs a full, in-depth analysis including ML-driven bias detection and type classification, emotional analysis, detailed pattern matching, and trust score calculation.
        The request body parameters `headline` (string, optional), `include_patterns` (boolean, defaults to `true`), and `include_detailed_results` (boolean, defaults to `false`) allow customization of the analysis. The `detailed_sub_analyses` field in the response is populated if `include_detailed_results` is `true`.
    *   **Example Response (with `include_detailed_results=true` and `include_patterns=true`):**
        ```json
        {
          "trust_score": 75,
          "indicator": "🟢 Generally Trustworthy",
          "explanation": [
            "The content appears largely objective with neutral sentiment.",
            "No significant emotional manipulation tactics identified.",
            "Bias analysis did not flag strong indications of specific bias types based on ML models."
          ],
          "tip": "Understand that all sources can have some level of bias. Seek diverse perspectives to get a fuller picture.",
          "primary_bias_type": "Neutral",
          "bias_details": {
            "detected": false,
            "label": "Likely Neutral (confidence: 0.880)",
            "confidence": 0.95
          },
          "sentiment_details": {
            "label": "neutral",
            "confidence": 0.85
          },
          "emotion_details": {
            "label": "neutral",
            "confidence": 0.90,
            "is_emotionally_charged": false,
            "manipulation_risk": "low"
          },
          "pattern_highlights": {
            "nigerian_context_detected": false,
            "clickbait_detected": false,
            "fake_news_risk": "low"
          },
          "lightweight_nigerian_bias_assessment": {
            "inferred_bias_type": "No specific patterns detected",
            "bias_category": null,
            "bias_target": null,
            "matched_keywords": []
          },
          "detailed_sub_analyses": {
            "sentiment": {
              "label": "neutral",
              "confidence": 0.85,
              "all_scores": { "negative": 0.05, "neutral": 0.85, "positive": 0.10 },
              "headline_comparison": null
            },
            "emotion": {
              "label": "neutral",
              "confidence": 0.90,
              "is_emotionally_charged": false,
              "manipulation_risk": "low"
              // ... further details like emotion_scores ...
            },
            "bias": {
              "flag": false,
              "label": "Likely Neutral (confidence: 0.880)",
              "type_analysis": { "type": "neutral", "confidence": 0.95 /*, ... all_predictions ... */ },
              "detected": false
            },
            "patterns": {
              "nigerian_patterns": { "has_triggers": false, "has_clickbait": false /*, ... trigger_details, clickbait_details ... */ },
              "fake_news": { "detected": false, "details": { "risk_level": "low" /*, ... matched_phrases ... */ } },
              "viral_manipulation": { "is_potentially_viral": false /*, ... other scores ... */ }
            },
            "lightweight_nigerian_bias": {
              "inferred_bias_type": "No specific patterns detected",
              "bias_category": null,
              "bias_target": null,
              "matched_keywords": []
            }
          }
        }
        ```

**Note on API Usage Examples:**
The example responses above are illustrative. The actual structure and content can vary based on the input text and analysis parameters. The full response structure is defined by Pydantic models in `main.py` and can be explored via the `/docs` endpoint when the API is running. You can use tools like `curl` or Postman, or Python's `requests` library to interact with these endpoints.

For example, using `curl`:
```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{"text": "This is a test sentence for the BiasLens API.", "include_detailed_results": false}'
```

## Frontend Application
The `FRONTEND/` directory contains a Next.js application that provides a user interface for interacting with the BiasLens API. Please refer to `FRONTEND/README.md` for instructions on how to set up and run the frontend.

The frontend is designed to interact with the Python/FastAPI backend described in this README. For local development, ensure `NEXT_PUBLIC_API_BASE_URL` in the frontend's environment variables (e.g., in `FRONTEND/.env.local`) is set to your running Python backend (e.g., `http://localhost:8000`).

*Alternative Analysis Route*: The frontend codebase also contains a Next.js API route at `FRONTEND/app/api/analyze/route.ts` which uses OpenAI's GPT models for analysis and logs to a Supabase database (requiring separate Supabase environment variables). If `NEXT_PUBLIC_API_BASE_URL` is not set or points to the frontend itself, the "Deep Analysis" feature on the example UI may call this route instead of the Python backend. The `userId` field, for instance, is used by this Next.js/OpenAI route, not by the main Python/FastAPI backend. For the custom model analysis detailed here, ensure you are targeting the Python backend.

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
# Example with all parameters for the core analyze function
full_analysis = analyze(
    text=text_to_analyze_full,
    headline="Optional Headline Here",
    include_patterns=True,
    include_detailed_results=True
)
print("\nComprehensive Analysis Results:")
print(full_analysis)
```
Refer to the example outputs under the "API Endpoints" section for an idea of the structure of the returned dictionaries.
The dictionaries returned by direct Python calls to `analyze()` and `quick_analyze()` will have the same structure as the JSON responses shown in the API Endpoints section (e.g., no `metadata` field in `analyze()`'s output, new top-level fields like `sentiment_details`, etc.).

## Our Journey: From Hackathon Spark to Evolving Tool
BiasLens began its journey as a hackathon project, driven by the goal of creating a simple yet effective tool for uncovering bias in text. The initial version laid the groundwork for what has become a more nuanced and feature-rich analyzer. This evolution highlights our commitment to iterative development and the potential for hackathon ideas to mature into robust open-source solutions. We continue to explore new ways to enhance its capabilities.

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
