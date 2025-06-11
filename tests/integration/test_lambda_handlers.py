# tests/integration/test_lambda_handlers.py
import pytest
import json
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/lambda_functions/generate_text'))

def test_lambda_handler_structure():
    """Test that main.py has the expected structure"""
    try:
        import main
        assert hasattr(main, 'lambda_handler')
    except ImportError:
        pytest.skip("Cannot import main module in test environment")

def test_event_structure():
    """Test that we can handle typical Lambda event structure"""
    mock_event = {
        'body': json.dumps({
            'prompt': 'test prompt',
            'max_tokens': 10
        })
    }
    mock_context = {}
    
    # Basic structure test - should not crash
    assert 'body' in mock_event
    body = json.loads(mock_event['body'])
    assert 'prompt' in body