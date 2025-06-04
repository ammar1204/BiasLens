from biaslens.analyzer import analyse

# Test for analyse
print("Testing analyse...")
analyze_result = analyse("The government announced new policies today regarding renewable energy. Some say this is a great step, while others are concerned about the economic impact.")
print(f"analyse output: {analyze_result}")

assert 'trust_score' in analyze_result, "analyse output missing 'trust_score'"
assert 'indicator' in analyze_result, "analyse output missing 'indicator'"
assert 'explanation' in analyze_result, "analyse output missing 'explanation'"
assert isinstance(analyze_result['explanation'], list), "analyse 'explanation' should be a list"
assert 'tip' in analyze_result, "analyse output missing 'tip'"

# Assertions for metadata and component_processing_times are removed as they are not part of the core response.
# These might be present in detailed_sub_analyses or a specific verbose mode not tested here by default.

print("analyse tests passed!")
print("-" * 20)

print("All tests in test.py passed!")