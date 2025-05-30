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

print("analyze tests passed!")
print("-" * 20)

print("All tests in test.py passed!")