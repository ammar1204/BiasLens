# BiasLens

## Description
BiasLens is a Python library designed to detect and analyze various types of bias in text. This project was developed for a hackathon.

## Features
- Detects potential bias in text using a pre-trained model.
- Classifies the type of bias (e.g., political, gender, ethnic).
- Provides a trust score for the analyzed text.
- Offers quick analysis and comprehensive analysis options.

## Installation
To use BiasLens, clone the repository and install the necessary dependencies:
```bash
git clone https://github.com/your-username/biaslens.git  # Replace with the actual URL
cd biaslens
pip install -r requirements.txt
```
*(Note: `requirements.txt` was created in a previous step)*

## Usage
Here's how you can use BiasLens to analyze text:

### Quick Analysis
The `quick_analyze` function provides a fast assessment of bias.

```python
from biaslens.analyzer import quick_analyze

text_to_analyze = "This is a sample text to check for bias."
results = quick_analyze(text_to_analyze)

print("Quick Analysis Results:")
for result in results:
    print(f"- {result['label']}: {result['score']:.4f}")
```

**Example Output (Quick Analysis):**
```
Quick Analysis Results:
{
    'score': 75,
    'indicator': '🟡 Caution',
    'explanation': ['Contains suspicious Nigerian expressions', 'Contains clickbait patterns'],
    'tip': 'For a more comprehensive analysis, use the full analyze function.'
}
```

### Comprehensive Analysis
The `analyze` function performs a more in-depth analysis, including bias classification and trust score.

```python
from biaslens.analyzer import analyze

text_to_analyze = "This is another sample text which might contain some subtle biases."
analysis = analyze(text_to_analyze)

print("\nComprehensive Analysis Results:")
print(f"Text: {analysis['text']}")
print(f"Trust Score: {analysis['trust_score']:.4f}")
if analysis['bias_classification']:
    print("Bias Classification:")
    for category, score in analysis['bias_classification'].items():
        print(f"- {category.replace('_', ' ').title()}: {score:.4f}")
else:
    print("Bias Classification: No significant bias detected.")
```

**Example Output (Comprehensive Analysis):**
```
Comprehensive Analysis Results:
{
    'trust_score': 65,
    'indicator': '🟡 Caution',
    'explanation': [
        'Potential bias detected in language patterns.',
        'Content is emotionally charged.',
        'Contains Nigerian expressions commonly used in misleading content.'
    ],
    'tip': 'Verify this content from additional sources before trusting it fully.',
    'metadata': {
        'component_processing_times': {
            'sentiment_analysis': 0.0123,
            'emotion_analysis': 0.0456,
            'bias_analysis': 0.0789,
            'pattern_analysis': 0.0012,
            'trust_score_calculation': 0.0034,
            'overall_assessment_generation': 0.0005
        },
        'overall_processing_time_seconds': 0.1420,
        'text_length': 120,
        'initialized_components': ['sentiment', 'emotion', 'bias_detection', 'bias_classification'],
        'analysis_timestamp': 1678886400.0
    }
}
```
*(Note: The example outputs are illustrative and may vary based on the models and text.)*

## Project Structure
```
biaslens/
├── biaslens/
│   ├── __init__.py      # Makes 'biaslens' a Python package
│   ├── analyzer.py      # Core analysis functions (quick_analyze, analyze)
│   ├── bias.py          # Defines bias categories and related logic
│   ├── emotion.py       # Functions for emotion detection (if applicable)
│   ├── models.py        # Handles loading and interaction with Hugging Face models
│   ├── patterns.py      # Pattern matching utilities for text analysis
│   ├── sentiment.py     # Functions for sentiment analysis
│   ├── trust.py         # Logic for calculating trust scores
│   └── utils.py         # Utility functions for the biaslens package
├── tests/
│   ├── __init__.py      # Makes 'tests' a Python package
│   └── test_analyzer.py # Unit tests for the analyzer
├── .idea/                 # IDE-specific settings (usually ignored)
├── requirements.txt     # Project dependencies
├── test.py                # Root level test script (potentially for integration or older tests)
└── README.md            # This file
```
- **`biaslens/`**: The main package directory.
    - **`__init__.py`**: Initializes the `biaslens` package.
    - **`analyzer.py`**: Contains the core logic for text analysis, including the `quick_analyze` and `analyze` functions.
    - **`bias.py`**: Defines different bias categories (e.g., political, gender, ethnic) and any specific logic related to them.
    - **`emotion.py`**: Contains functions related to detecting emotions in text.
    - **`models.py`**: Manages the loading and interaction with the pre-trained Hugging Face models.
    - **`patterns.py`**: Includes utilities for pattern-based text analysis.
    - **`sentiment.py`**: Provides functions for sentiment analysis of text.
    - **`trust.py`**: Contains logic related to the calculation of trust scores for analyzed text.
    - **`utils.py`**: Helper functions used across the `biaslens` package.
- **`tests/`**: Contains unit tests for the project.
    - **`__init__.py`**: Initializes the `tests` package.
    - **`test_analyzer.py`**: Includes tests specifically for the functions in `analyzer.py`.
- **`requirements.txt`**: Lists all Python dependencies required to run the project.
- **`test.py`**: A script in the root directory, possibly used for running integration tests or as an older testing file.
- **`README.md`**: Provides an overview of the project, installation instructions, usage examples, and other relevant information.

## Models Used
BiasLens utilizes the following Hugging Face models:
- **Toxicity Detection:** `martin-ha/toxic-comment-model`
- **Bias Classification (Zero-Shot):** `facebook/bart-large-mnli`

## Future Improvements (Optional)
- Support for more languages beyond English.
- Detection and classification of a wider range of bias types (e.g., ageism, religious bias).
- Integration with social media platforms for real-time bias analysis.
- Customizable bias thresholds.

## License
This project is currently unlicensed. Please consider adding an open-source license if you plan to share or distribute this code.

## Hackathon Project
This library was developed as part of a hackathon. We aimed to create a simple yet effective tool for identifying potential bias in textual content.
