# tests/regression/test_daily_health_checks.py
"""Daily health checks for production system"""

import pytest
import requests
import json
import time

class TestDailyHealthChecks:
    """Daily health monitoring for the production ML system"""
    
    def __init__(self):
        self.api_base = None
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup API base URL"""
        self.api_base = request.config.getoption("--api-base", default="https://0fc0dgwg69.execute-api.eu-west-2.amazonaws.com")
        self.generate_endpoint = f"{self.api_base}/generate"
        self.visualize_endpoint = f"{self.api_base}/visualize"

    def test_api_endpoints_are_reachable(self):
        """Test that both API endpoints are reachable"""
        endpoints = [
            ("Generate Text", self.generate_endpoint),
            ("Visualize Attention", self.visualize_endpoint)
        ]
        
        for name, endpoint in endpoints:
            try:
                # Simple health check with minimal payload
                if "generate" in endpoint:
                    payload = {"prompt": "health", "max_tokens": 1, "temperature": 1.0, "top_k": 50}
                else:
                    payload = {"text": "warmup", "layer": 0, "head": 0}
                
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                assert response.status_code == 200, f"{name} endpoint unreachable: {response.status_code}"
                print(f"✅ {name} endpoint is healthy")
                
            except requests.exceptions.Timeout:
                pytest.fail(f"{name} endpoint timed out - may indicate cold start issues")
            except Exception as e:
                pytest.fail(f"{name} endpoint failed: {str(e)}")

    def test_basic_text_generation_functionality(self):
        """Test basic text generation is working"""
        payload = {
            "prompt": "Daily health check test",
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
        
        assert response.status_code == 200
        data = response.json()
        
        assert "generated_text" in data
        assert "prompt" in data
        assert payload["prompt"] in data["generated_text"]
        
        print(f"✅ Text generation is working: '{data['generated_text'][:50]}...'")

    def test_basic_attention_visualization_functionality(self):
        """Test basic attention visualization is working"""
        payload = {
            "text": "Health check visualization test",
            "layer": 1,
            "heads": [0]
        }
        
        response = requests.post(
            self.visualize_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "attention_image" in data or "attention_images" in data
        assert "tokens" in data
        
        print(f"✅ Attention visualization is working: {len(data['tokens'])} tokens processed")

    def test_response_times_are_reasonable(self):
        """Test that response times are within acceptable bounds"""
        # Test text generation response time
        start_time = time.time()
        payload = {"prompt": "Response time test", "max_tokens": 5, "temperature": 1.0, "top_k": 50}
        
        response = requests.post(
            self.generate_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        generation_time = time.time() - start_time
        
        assert response.status_code == 200
        assert generation_time < 30, f"Text generation too slow: {generation_time:.2f}s"
        
        print(f"✅ Text generation response time: {generation_time:.2f}s")
        
        # Test attention visualization response time  
        start_time = time.time()
        payload = {"text": "Response time test", "layer": 0, "heads": [0]}
        
        response = requests.post(
            self.visualize_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        visualization_time = time.time() - start_time
        
        assert response.status_code == 200
        assert visualization_time < 60, f"Attention visualization too slow: {visualization_time:.2f}s"
        
        print(f"✅ Attention visualization response time: {visualization_time:.2f}s")

    def test_error_handling_is_graceful(self):
        """Test that invalid requests are handled gracefully"""
        invalid_requests = [
            # Invalid text generation request
            {
                "endpoint": self.generate_endpoint,
                "payload": {"prompt": "", "max_tokens": -1, "temperature": -1, "top_k": 0}
            },
            # Invalid attention visualization request
            {
                "endpoint": self.visualize_endpoint,
                "payload": {"text": "", "layer": 100, "heads": [100]}
            }
        ]
        
        for request_data in invalid_requests:
            response = requests.post(
                request_data["endpoint"],
                json=request_data["payload"],
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            # Should return 4xx or 5xx, but not crash
            assert response.status_code >= 400, f"Invalid request should return error status"
            
            # Response should be valid JSON
            try:
                response.json()
                print(f"✅ Error handling is graceful for {request_data['endpoint']}")
            except json.JSONDecodeError:
                pytest.fail(f"Error response is not valid JSON for {request_data['endpoint']}")
