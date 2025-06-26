# tests/regression/test_api_response_times.py
"""API response time monitoring and regression testing"""

import pytest
import requests
import time
import statistics
import argparse
from datetime import datetime

class TestAPIResponseTimes:
    """Monitor and test API response time performance"""
    
    def __init__(self):
        self.api_base = None
        self.max_cold_start = 30
        self.max_warm_response = 5
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup test parameters"""
        self.api_base = request.config.getoption("--api-base", default="https://0fc0dgwg69.execute-api.eu-west-2.amazonaws.com")
        self.max_cold_start = request.config.getoption("--max-cold-start", default=30)
        self.max_warm_response = request.config.getoption("--max-warm-response", default=5)
        self.generate_endpoint = f"{self.api_base}/generate"
        self.visualize_endpoint = f"{self.api_base}/visualize"

    def test_text_generation_response_times(self):
        """Test text generation API response times"""
        print("🚀 Testing text generation response times...")
        
        response_times = []
        success_count = 0
        
        # Make 5 requests to get average performance
        for i in range(5):
            payload = {
                "prompt": f"Response time test {i}",
                "max_tokens": 10,
                "temperature": 0.8,
                "top_k": 50
            }
            
            start_time = time.time()
            try:
                response = requests.post(
                    self.generate_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    success_count += 1
                    response_times.append(response_time)
                    print(f"   Request {i+1}: {response_time:.2f}s")
                else:
                    print(f"   Request {i+1}: Failed with status {response.status_code}")
                
            except Exception as e:
                print(f"   Request {i+1}: Exception - {e}")
            
            # Small delay between requests
            time.sleep(1)
        
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print(f"📊 Text Generation Response Time Analysis:")
            print(f"   Average: {avg_time:.2f}s")
            print(f"   Median: {median_time:.2f}s") 
            print(f"   Min: {min_time:.2f}s")
            print(f"   Max: {max_time:.2f}s")
            print(f"   Success Rate: {success_count}/5")
            
            # Performance assertions
            assert avg_time < self.max_warm_response * 2, f"Average response time too slow: {avg_time:.2f}s"
            assert max_time < self.max_cold_start, f"Maximum response time too slow: {max_time:.2f}s"
            assert success_count >= 4, f"Success rate too low: {success_count}/5"
        else:
            pytest.fail("No successful text generation requests")

    def test_attention_visualization_response_times(self):
        """Test attention visualization API response times"""
        print("👁️ Testing attention visualization response times...")
        
        response_times = []
        success_count = 0
        
        # Make 3 requests (fewer due to higher cost)
        for i in range(3):
            payload = {
                "text": f"Attention response time test {i}",
                "layer": i % 4,  # Rotate through layers
                "heads": [0]
            }
            
            start_time = time.time()
            try:
                response = requests.post(
                    self.visualize_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=120
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    success_count += 1
                    response_times.append(response_time)
                    print(f"   Request {i+1}: {response_time:.2f}s")
                else:
                    print(f"   Request {i+1}: Failed with status {response.status_code}")
                
            except Exception as e:
                print(f"   Request {i+1}: Exception - {e}")
            
            # Longer delay for visualization requests
            time.sleep(2)
        
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print(f"📊 Attention Visualization Response Time Analysis:")
            print(f"   Average: {avg_time:.2f}s")
            print(f"   Median: {median_time:.2f}s")
            print(f"   Min: {min_time:.2f}s")
            print(f"   Max: {max_time:.2f}s")
            print(f"   Success Rate: {success_count}/3")
            
            # Performance assertions (more lenient for visualization)
            assert avg_time < self.max_warm_response * 4, f"Average response time too slow: {avg_time:.2f}s"
            assert max_time < self.max_cold_start * 2, f"Maximum response time too slow: {max_time:.2f}s"
            assert success_count >= 2, f"Success rate too low: {success_count}/3"
        else:
            pytest.fail("No successful attention visualization requests")

    def test_cold_start_performance(self):
        """Test cold start performance by waiting and making a request"""
        print("❄️ Testing cold start performance...")
        
        # Wait to ensure functions go cold (30 seconds should be enough)
        print("   Waiting 30 seconds for functions to go cold...")
        time.sleep(30)
        
        # First request after cold period (likely cold start)
        payload = {
            "prompt": "Cold start performance test",
            "max_tokens": 5,
            "temperature": 1.0,
            "top_k": 50
        }
        
        start_time = time.time()
        response = requests.post(
            self.generate_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        cold_start_time = time.time() - start_time
        
        assert response.status_code == 200, f"Cold start request failed: {response.status_code}"
        
        print(f"   Cold start time: {cold_start_time:.2f}s")
        
        # Immediate follow-up request (should be warm)
        start_time = time.time()
        response = requests.post(
            self.generate_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        warm_time = time.time() - start_time
        
        assert response.status_code == 200, f"Warm request failed: {response.status_code}"
        
        print(f"   Warm request time: {warm_time:.2f}s")
        print(f"   Cold start overhead: {cold_start_time - warm_time:.2f}s")
        
        # Performance assertions
        assert cold_start_time < self.max_cold_start, f"Cold start too slow: {cold_start_time:.2f}s"
        assert warm_time < self.max_warm_response, f"Warm request too slow: {warm_time:.2f}s"

def main():
    """Standalone script for API response time monitoring"""
    parser = argparse.ArgumentParser(description='API Response Time Monitoring')
    parser.add_argument('--api-base', required=True, help='Base API URL')
    parser.add_argument('--max-cold-start', type=float, default=30, help='Maximum acceptable cold start time (seconds)')
    parser.add_argument('--max-warm-response', type=float, default=5, help='Maximum acceptable warm response time (seconds)')
    
    args = parser.parse_args()
    
    print(f"⏱️ Starting API response time monitoring")
    print(f"API Base: {args.api_base}")
    print(f"Max Cold Start: {args.max_cold_start}s")
    print(f"Max Warm Response: {args.max_warm_response}s")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Create mock request for test class
    class MockRequest:
        class config:
            @staticmethod
            def getoption(option, default=None):
                if option == "--api-base":
                    return args.api_base
                elif option == "--max-cold-start":
                    return args.max_cold_start
                elif option == "--max-warm-response":
                    return args.max_warm_response
                return default
    
    # Run the tests
    test_instance = TestAPIResponseTimes()
    test_instance.setup(MockRequest())
    
    try:
        test_instance.test_text_generation_response_times()
        test_instance.test_attention_visualization_response_times()
        test_instance.test_cold_start_performance()
        
        print(f"\n✅ API response time monitoring completed successfully!")
        
    except Exception as e:
        print(f"\n❌ API response time monitoring failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()