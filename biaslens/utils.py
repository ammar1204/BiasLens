"""
Utility Module for BiasLens.

This module provides shared utility functions, classes, or variables that are used
across different parts of the BiasLens package. This can include helper functions,
constants, or shared resources like model caches.
"""

# In-memory cache for Hugging Face models and pipelines.
# This dictionary stores loaded models/pipelines using their Hugging Face model name
# or a custom key as the dictionary key. The goal is to avoid reloading these
# potentially large objects multiple times during the application's lifecycle,
# speeding up repeated analyses.
#
# Example structure:
# _model_cache = {
#     "martin-ha/toxic-comment-model": {"tokenizer": tokenizer_obj, "model": model_obj, "pipeline": pipeline_obj},
#     "facebook/bart-large-mnli": pipeline_obj_bart
# }
#
# Note: This is a simple in-memory dictionary cache.
# - It is not persistent across application runs.
# - It is not thread-safe if BiasLens components are used in a concurrent environment
#   (e.g., a multi-threaded web server) without external locking mechanisms.
# - Memory usage can grow if many different models are loaded. Consider more
#   sophisticated caching strategies (e.g., LRU cache, disk caching) for
#   production environments with diverse model usage or memory constraints.
_model_cache = {}
