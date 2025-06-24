# tests/regression/test_model_performance_regression.py
"""Model performance regression testing"""

import pytest
import requests
import json
import argparse
import os
from typing import Dict, List

class TestModelPerformanceRegression:
    """Test for model performance regression"""
    
    def __init__(self):
        self.api_base = None
        self.baseline_file = None
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup test parameters"""
        self.api_base = request.config.getoption("--api-base", default="https://0fc0dgwg69.execute-api.eu-west-2.amazonaws.com")
        self.baseline_file = request.config.getoption("--baseline-file", default="tests/data/performance_baseline.json")
        self.generate_endpoint = f"{self.api_base}/generate"

    def load_baseline_performance(self) -> Dict:
        """Load baseline performance metrics"""
        if os.path.exists(self.baseline_file):
            with open(self.baseline_file, 'r') as f:
                return json.load(f)
        else:
            # Default baseline if file doesn't exist
            return {
                "text_quality": {
                    "min_coherence_score": 0.6,
                    "expected_patterns": ["pride", "prejudice", "truth", "acknowledged"]
                },
                "performance": {
                    "max_response_time": 30.0,
                    "min_success_rate": 0.9
                }
            }

    def test_text_generation_quality_regression(self):
        """Test that text generation quality hasn't degraded"""
        baseline = self.load_baseline_performance()
        
        # Test prompts that should produce consistent, quality responses
        test_prompts = [
            "It is a truth universally acknowledged",
            "Mr. Darcy was",
            "Elizabeth Bennet could not", 
            "The ball at Netherfield"
        ]
        
        successful_generations = 0
        quality_scores = []
        
        for prompt in test_prompts:
            payload = {
                "prompt": prompt,
                "max_tokens": 20,
                "temperature": 0.7,  # Lower temperature for more consistent output
                "top_k": 30
            }
            
            try:
                response = requests.post(
                    self.generate_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                
                if response.status_code == 200:
                    successful_generations += 1
                    data = response.json()
                    generated_text = data["generated_text"].lower()
                    
                    # Simple quality check: does it contain expected patterns?
                    quality_score = 0
                    for pattern in baseline["text_quality"]["expected_patterns"]:
                        if pattern in generated_text:
                            quality_score += 0.25
                    
                    # Coherence check: does output contain the original prompt?
                    if prompt.lower() in generated_text:
                        quality_score += 0.25
                    
                    quality_scores.append(quality_score)
                    print(f"✅ Generated for '{prompt}': {generated_text[:50]}...")
                
            except Exception as e:
                print(f"❌ Failed to generate for '{prompt}': {e}")
        
        # Evaluate performance
        success_rate = successful_generations / len(test_prompts)
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        print(f"📊 Performance Results:")
        print(f"   Success Rate: {success_rate:.2f}")
        print(f"   Average Quality Score: {avg_quality:.2f}")
        
        # Regression checks
        assert success_rate >= baseline["performance"]["min_success_rate"], \
            f"Success rate regression: {success_rate:.2f} < {baseline['performance']['min_success_rate']}"
        
        assert avg_quality >= baseline["text_quality"]["min_coherence_score"], \
            f"Quality regression: {avg_quality:.2f} < {baseline['text_quality']['min_coherence_score']}"

    def test_model_consistency_regression(self):
        """Test that model generates consistent outputs for same inputs"""
        # Test same prompt multiple times
        test_prompt = "The future of artificial intelligence"
        generations = []
        
        for i in range(3):
            payload = {
                "prompt": test_prompt,
                "max_tokens": 15,
                "temperature": 0.1,  # Very low temperature for consistency
                "top_k": 10
            }
            
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            assert response.status_code == 200
            data = response.json()
            generations.append(data["generated_text"])
        
        # Check for some consistency (shouldn't be completely random)
        # At minimum, all should start with the prompt
        for generation in generations:
            assert test_prompt in generation, f"Generated text doesn't contain prompt: {generation}"
        
        print(f"✅ Consistency test passed for prompt: '{test_prompt}'")
        for i, gen in enumerate(generations):
            print(f"   Generation {i+1}: {gen}")

def main():
    """Standalone script for model performance regression testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Model Performance Regression Test')
    parser.add_argument('--api-base', required=True, help='Base API URL')
    parser.add_argument('--baseline-file', default='tests/data/performance_baseline.json', help='Baseline performance file')
    
    args = parser.parse_args()
    
    print(f"🔍 Running model performance regression test")
    print(f"API Base: {args.api_base}")
    print(f"Baseline: {args.baseline_file}")
    
    # Create a mock request object for the test class
    class MockRequest:
        def __init__(self, api_base, baseline_file):
            self.api_base = api_base
            self.baseline_file = baseline_file
        
        class config:
            @staticmethod
            def getoption(option, default=None):
                if option == "--api-base":
                    return args.api_base
                elif option == "--baseline-file":
                    return args.baseline_file
                return default
    
    # Run the tests
    test_instance = TestModelPerformanceRegression()
    mock_request = MockRequest(args.api_base, args.baseline_file)
    test_instance.setup(mock_request)
    
    try:
        test_instance.test_text_generation_quality_regression()
        test_instance.test_model_consistency_regression()
        print(f"\n✅ Model performance regression test passed!")
        
    except Exception as e:
        print(f"\n❌ Model performance regression test failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
