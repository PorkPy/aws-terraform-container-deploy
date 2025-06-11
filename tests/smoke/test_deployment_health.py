# tests/smoke/test_deployment_health.py
import pytest
import requests
import os

def test_api_endpoint_reachable():
    """Test that the API endpoint is reachable"""
    api_endpoint = os.environ.get('API_ENDPOINT')
    if not api_endpoint:
        pytest.skip("API_ENDPOINT not set")
    
    # Test that the endpoint is reachable (even if it returns an error)
    try:
        response = requests.get(api_endpoint, timeout=10)
        # We just want to make sure it's reachable, status code doesn't matter
        assert response.status_code is not None
    except requests.exceptions.RequestException:
        pytest.fail("API endpoint is not reachable")

def test_generate_endpoint_exists():
    """Test that the generate endpoint exists"""
    api_endpoint = os.environ.get('API_ENDPOINT')
    if not api_endpoint:
        pytest.skip("API_ENDPOINT not set")
    
    try:
        response = requests.post(
            f"{api_endpoint}/generate",
            json={'prompt': 'test', 'max_tokens': 5},
            timeout=30
        )
        # Should get some response (200, 400, 500, etc. - just not connection error)
        assert response.status_code is not None
    except requests.exceptions.RequestException:
        pytest.fail("Generate endpoint is not reachable")