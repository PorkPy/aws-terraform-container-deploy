# tests/unit/test_tokenizer.py
import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/lambda_functions/generate_text'))

def test_basic_tokenization():
    """Test basic string operations (placeholder for actual tokenizer)"""
    text = "Hello, world!"
    tokens = text.split()
    assert len(tokens) == 2
    assert tokens[0] == "Hello,"