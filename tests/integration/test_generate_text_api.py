# tests/integration/test_generate_text_api.py
"""Integration tests for the Generate Text API endpoint"""

import pytest
import requests
import json
import time

class TestGenerateTextAPI:
    """Test the production Generate Text API"""
    
    def __init__(self):
        self.api_base = None
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup API base URL from command line or default"""
        self.api_base = request.config.getoption("--api-base", default="https://0fc0dgwg69.execute-api.eu-west-2.amazonaws.com")
        self.generate_endpoint = f"{self.api_base}/generate"

    def test_api_health_check(self):
        """Test basic API connectivity"""
        payload = {
            "prompt": "test",
            "max_tokens": 5,
            "temperature": 1.0,
            "top_k": 50
        }
        
        response = requests.post(
            self.generate_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        assert response.status_code == 200, f"API health check failed: {response.status_code}"

    def test_basic_text_generation(self):
        """Test basic text generation functionality"""
        payload = {
            "prompt": "It is a truth universally acknowledged",
            "max_tokens": 20,
            "temperature": 0.8,
            "top_k": 50
        }
        
        start_time = time.time()
        response = requests.post(
            self.generate_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        
        data = response.json()
        assert "generated_text" in data
        assert "prompt" in data
        assert "settings" in data
        
        # Verify generated text contains the prompt
        assert payload["prompt"] in data["generated_text"]
        
        # Check response time is reasonable
        assert response_time < 30, f"Response time too slow: {response_time:.2f}s"

    def test_different_temperature_settings(self):
        """Test text generation with different temperature settings"""
        base_prompt = "The future of artificial intelligence"
        temperatures = [0.1, 0.5, 1.0, 1.5]
        
        for temp in temperatures:
            payload = {
                "prompt": base_prompt,
                "max_tokens": 15,
                "temperature": temp,
                "top_k": 50
            }
            
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            assert response.status_code == 200, f"Failed for temperature {temp}"
            data = response.json()
            assert data["settings"]["temperature"] == temp

    def test_different_max_tokens(self):
        """Test text generation with different max token settings"""
        base_prompt = "In the beginning"
        max_tokens_list = [5, 15, 30, 50]
        
        for max_tokens in max_tokens_list:
            payload = {
                "prompt": base_prompt,
                "max_tokens": max_tokens,
                "temperature": 0.8,
                "top_k": 50
            }
            
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            assert response.status_code == 200, f"Failed for max_tokens {max_tokens}"
            data = response.json()
            assert data["settings"]["max_tokens"] == max_tokens

    def test_top_k_sampling(self):
        """Test text generation with different top-k values"""
        base_prompt = "Machine learning is"
        top_k_values = [1, 10, 25, 50, 100]
        
        for top_k in top_k_values:
            payload = {
                "prompt": base_prompt,
                "max_tokens": 10,
                "temperature": 1.0,
                "top_k": top_k
            }
            
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            assert response.status_code == 200, f"Failed for top_k {top_k}"
            data = response.json()
            assert data["settings"]["top_k"] == top_k

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        test_cases = [
            {"prompt": "", "max_tokens": 10, "temperature": 1.0, "top_k": 50},  # Empty prompt
            {"prompt": "A", "max_tokens": 1, "temperature": 1.0, "top_k": 50},  # Minimal generation
            {"prompt": "Very long prompt " * 20, "max_tokens": 10, "temperature": 1.0, "top_k": 50},  # Long prompt
        ]
        
        for i, payload in enumerate(test_cases):
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            # Should either succeed or fail gracefully
            assert response.status_code in [200, 400, 500], f"Unexpected status for test case {i}"

    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import concurrent.futures
        
        def make_request():
            payload = {
                "prompt": "Concurrent test prompt",
                "max_tokens": 10,
                "temperature": 0.8,
                "top_k": 50
            }
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            return response.status_code == 200
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Most requests should succeed (allowing for some cold starts)
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.6, f"Concurrent request success rate too low: {success_rate}"
