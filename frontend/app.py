from flask import Flask, request, jsonify, render_template
import sys
import os

# Adjust the path to import BiasLensAnalyzer from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from biaslens.analyzer import BiasLensAnalyzer

app = Flask(__name__)
analyzer = BiasLensAnalyzer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_text():
    if request.method == 'POST':
        data = request.get_json()
        text_to_analyze = data.get('text')

        if not text_to_analyze:
            return jsonify({'error': 'No text provided'}), 400

        try:
            # Perform analysis using BiasLensAnalyzer
            # Using the comprehensive 'analyze' method
            analysis_results = analyzer.analyze(text_to_analyze)
            return jsonify(analysis_results)
        except Exception as e:
            # Log the exception for debugging
            app.logger.error(f"Error during analysis: {str(e)}")
            return jsonify({'error': f'An error occurred during analysis: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
