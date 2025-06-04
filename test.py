from biaslens.analyzer import quick_analyze, analyze

# Test for quick_analyze
print("Testing quick_analyze...")
quick_result = quick_analyze("BREAKING: THE WORLD ENDS IN TWO WEEKS")
print(f"quick_analyze output: {quick_result}")

assert 'score' in quick_result, "quick_analyze output missing 'score'"
assert 'indicator' in quick_result, "quick_analyze output missing 'indicator'"
assert 'explanation' in quick_result, "quick_analyze output missing 'explanation'"
assert isinstance(quick_result['explanation'], list), "quick_analyze 'explanation' should be a list"
assert 'tip' in quick_result, "quick_analyze output missing 'tip'"
assert quick_result['tip'] == "For a more comprehensive analysis, use the full analyze function.", "Incorrect tip in quick_analyze"

print("quick_analyze tests passed!")
print("-" * 20)

# Test for analyze
print("Testing analyze...")
analyze_result = analyze("The government announced new policies today regarding renewable energy. Some say this is a great step, while others are concerned about the economic impact.")
print(f"analyze output: {analyze_result}")

assert 'trust_score' in analyze_result, "analyze output missing 'trust_score'"
assert 'indicator' in analyze_result, "analyze output missing 'indicator'"
assert 'explanation' in analyze_result, "analyze output missing 'explanation'"
assert isinstance(analyze_result['explanation'], list), "analyze 'explanation' should be a list"
assert 'tip' in analyze_result, "analyze output missing 'tip'"

# Verify metadata and component_processing_times
assert 'metadata' in analyze_result, "analyze output missing 'metadata'"
assert isinstance(analyze_result.get('metadata'), dict), "analyze 'metadata' should be a dictionary"
assert 'component_processing_times' in analyze_result['metadata'], "metadata missing 'component_processing_times'"
assert isinstance(analyze_result['metadata'].get('component_processing_times'), dict), "'component_processing_times' should be a dictionary"
# Optionally, check for a few expected keys in component_processing_times if they are always present
expected_time_keys = [
    'sentiment_analysis', 'emotion_analysis', 'bias_analysis',
    'pattern_analysis', 'trust_score_calculation', 'overall_assessment_generation'
]
if isinstance(analyze_result['metadata'].get('component_processing_times'), dict):
    for key in expected_time_keys:
        assert key in analyze_result['metadata']['component_processing_times'], f"'{key}' missing from component_processing_times"

print("analyze tests passed!")
print("-" * 20)

print("All tests in test.py passed!")