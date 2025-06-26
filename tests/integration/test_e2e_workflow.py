# tests/integration/test_e2e_workflow.py
"""End-to-end workflow integration tests"""

import pytest
import requests
import json
import time

class TestEndToEndWorkflow:
    """Test complete end-to-end workflows using both APIs"""
    
    def __init__(self):
        self.api_base = None
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup API endpoints"""
        self.api_base = request.config.getoption("--api-base", default="https://0fc0dgwg69.execute-api.eu-west-2.amazonaws.com")
        self.generate_endpoint = f"{self.api_base}/generate"
        self.visualize_endpoint = f"{self.api_base}/visualize"

    def test_generate_then_visualize_workflow(self):
        """Test generating text then visualizing attention for the same input"""
        prompt = "It is a truth universally acknowledged"
        
        # Step 1: Generate text
        generate_payload = {
            "prompt": prompt,
            "max_tokens": 20,
            "temperature": 0.8,
            "top_k": 50
        }
        
        generate_response = requests.post(
            self.generate_endpoint,
            json=generate_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        assert generate_response.status_code == 200
        generated_data = generate_response.json()
        generated_text = generated_data["generated_text"]
        
        # Step 2: Visualize attention for the generated text
        visualize_payload = {
            "text": generated_text,
            "layer": 2,
            "heads": [0, 1]
        }
        
        visualize_response = requests.post(
            self.visualize_endpoint,
            json=visualize_payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        assert visualize_response.status_code == 200
        visualize_data = visualize_response.json()
        
        # Verify the workflow completed successfully
        assert "attention_image" in visualize_data or "attention_images" in visualize_data
        assert visualize_data["text"] == generated_text

    def test_pride_prejudice_themed_workflow(self):
        """Test workflow with Pride and Prejudice themed content"""
        pride_prejudice_prompts = [
            "Mr. Darcy was",
            "Elizabeth Bennet could not",
            "The ball at Netherfield was",
            "Mrs. Bennet's greatest wish"
        ]
        
        for prompt in pride_prejudice_prompts:
            # Generate text
            generate_payload = {
                "prompt": prompt,
                "max_tokens": 15,
                "temperature": 0.7,
                "top_k": 40
            }
            
            generate_response = requests.post(
                self.generate_endpoint,
                json=generate_payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            assert generate_response.status_code == 200
            
            # Visualize attention for original prompt
            visualize_payload = {
                "text": prompt,
                "layer": 3,
                "heads": [0]
            }
            
            visualize_response = requests.post(
                self.visualize_endpoint,
                json=visualize_payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            
            assert visualize_response.status_code == 200

    def test_stress_test_workflow(self):
        """Test system under moderate stress"""
        import concurrent.futures
        
        def run_workflow():
            try:
                # Generate text
                generate_payload = {
                    "prompt": "Test prompt for stress testing",
                    "max_tokens": 10,
                    "temperature": 1.0,
                    "top_k": 50
                }
                
                generate_response = requests.post(
                    self.generate_endpoint,
                    json=generate_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                
                if generate_response.status_code != 200:
                    return False
                
                # Visualize attention
                visualize_payload = {
                    "text": "Test visualization text",
                    "layer": 1,
                    "heads": [0]
                }
                
                visualize_response = requests.post(
                    self.visualize_endpoint,
                    json=visualize_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=120
                )
                
                return visualize_response.status_code == 200
                
            except Exception:
                return False
        
        # Run 3 concurrent workflows
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_workflow) for _ in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # At least 60% should succeed (accounting for cold starts)
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.6, f"Stress test success rate too low: {success_rate}"
