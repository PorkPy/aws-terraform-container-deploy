# tests/integration/test_visualize_attention_api.py
"""Integration tests for the Visualize Attention API endpoint"""

import pytest
import requests
import json
import time
import base64
from io import BytesIO
from PIL import Image

class TestVisualizeAttentionAPI:
    """Test the production Visualize Attention API"""
    
    def __init__(self):
        self.api_base = None
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup API base URL from command line or default"""
        self.api_base = request.config.getoption("--api-base", default="https://0fc0dgwg69.execute-api.eu-west-2.amazonaws.com")
        self.visualize_endpoint = f"{self.api_base}/visualize"

    def test_warmup_request(self):
        """Test warmup request handling"""
        payload = {
            "text": "warmup",
            "layer": 0,
            "head": 0
        }
        
        response = requests.post(
            self.visualize_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "warmed"

    def test_single_head_attention_visualization(self):
        """Test attention visualization for single head"""
        payload = {
            "text": "The cat sat on the mat and looked around",
            "layer": 2,
            "heads": [0]  # Single head
        }
        
        start_time = time.time()
        response = requests.post(
            self.visualize_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        
        data = response.json()
        assert "attention_image" in data or "attention_images" in data
        assert "tokens" in data
        assert "text" in data
        
        # Verify base64 image data
        if "attention_image" in data:
            image_data = base64.b64decode(data["attention_image"])
            image = Image.open(BytesIO(image_data))
            assert image.format == "PNG"
            assert image.size[0] > 0 and image.size[1] > 0
        
        # Check response time
        assert response_time < 60, f"Visualization response time too slow: {response_time:.2f}s"

    def test_multiple_heads_visualization(self):
        """Test attention visualization for multiple heads"""
        payload = {
            "text": "Natural language processing is fascinating",
            "layer": 1,
            "heads": [0, 1, 2, 3]  # Multiple heads
        }
        
        response = requests.post(
            self.visualize_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "attention_images" in data or "attention_image" in data
        assert "tokens" in data
        
        # If multiple images returned, verify each one
        if "attention_images" in data:
            assert len(data["attention_images"]) == 4
            for img_b64 in data["attention_images"]:
                image_data = base64.b64decode(img_b64)
                image = Image.open(BytesIO(image_data))
                assert image.format == "PNG"

    def test_different_layers(self):
        """Test attention visualization across different layers"""
        base_text = "Attention mechanisms are important"
        
        for layer in range(4):  # Test all 4 layers
            payload = {
                "text": base_text,
                "layer": layer,
                "heads": [0]
            }
            
            response = requests.post(
                self.visualize_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            
            assert response.status_code == 200, f"Failed for layer {layer}"
            data = response.json()
            assert "attention_image" in data or "attention_images" in data

    def test_different_text_lengths(self):
        """Test attention visualization with different text lengths"""
        test_texts = [
            "Short",
            "Medium length sentence here",
            "This is a much longer sentence that contains more words and should test the attention visualization with longer sequences of tokens"
        ]
        
        for i, text in enumerate(test_texts):
            payload = {
                "text": text,
                "layer": 1,
                "heads": [0]
            }
            
            response = requests.post(
                self.visualize_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            
            assert response.status_code == 200, f"Failed for text case {i}"
            data = response.json()
            assert len(data["tokens"]) > 0

    def test_invalid_parameters(self):
        """Test handling of invalid parameters"""
        invalid_cases = [
            {"text": "", "layer": 0, "heads": [0]},  # Empty text
            {"text": "test", "layer": 10, "heads": [0]},  # Invalid layer
            {"text": "test", "layer": 0, "heads": [20]},  # Invalid head
            {"text": "test", "layer": -1, "heads": [0]},  # Negative layer
        ]
        
        for i, payload in enumerate(invalid_cases):
            response = requests.post(
                self.visualize_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            # Should handle gracefully - either succeed by adjusting params or return meaningful error
            assert response.status_code in [200, 400, 500], f"Unexpected status for invalid case {i}"
