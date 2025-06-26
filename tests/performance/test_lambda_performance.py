# tests/performance/test_lambda_performance.py
"""Performance benchmark tests for Lambda functions"""

import requests
import json
import time
import statistics
import argparse

class LambdaPerformanceBenchmarks:
    """Performance benchmarking for Lambda functions"""
    
    def __init__(self, api_base):
        self.api_base = api_base
        self.generate_endpoint = f"{api_base}/generate"
        self.visualize_endpoint = f"{api_base}/visualize"
        
    def benchmark_text_generation(self, num_requests=10):
        """Benchmark text generation performance"""
        print(f"\n🚀 Benchmarking Text Generation ({num_requests} requests)")
        
        response_times = []
        success_count = 0
        
        for i in range(num_requests):
            payload = {
                "prompt": f"Performance test {i}: The future of AI",
                "max_tokens": 20,
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
                
                if response.status_code == 200:
                    success_count += 1
                    response_times.append(time.time() - start_time)
                
            except Exception as e:
                print(f"Request {i} failed: {e}")
            
            # Add small delay between requests
            time.sleep(0.5)
        
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            print(f"✅ Text Generation Performance Results:")
            print(f"   Success Rate: {success_count}/{num_requests} ({success_count/num_requests*100:.1f}%)")
            print(f"   Average Response Time: {avg_time:.2f}s")
            print(f"   Median Response Time: {median_time:.2f}s")
            print(f"   Min Response Time: {min_time:.2f}s")
            print(f"   Max Response Time: {max_time:.2f}s")
            
            # Performance assertions
            assert avg_time < 15.0, f"Average response time too slow: {avg_time:.2f}s"
            assert success_count/num_requests >= 0.8, f"Success rate too low: {success_count/num_requests*100:.1f}%"
        else:
            print("❌ No successful requests for text generation benchmark")
            assert False, "Text generation benchmark failed completely"
    
    def benchmark_attention_visualization(self, num_requests=5):
        """Benchmark attention visualization performance"""
        print(f"\n👁️ Benchmarking Attention Visualization ({num_requests} requests)")
        
        response_times = []
        success_count = 0
        
        for i in range(num_requests):
            payload = {
                "text": f"Attention performance test {i}: Machine learning models",
                "layer": i % 4,  # Rotate through layers
                "heads": [0] if i % 2 == 0 else [0, 1]  # Alternate single/multiple heads
            }
            
            start_time = time.time()
            try:
                response = requests.post(
                    self.visualize_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=120
                )
                
                if response.status_code == 200:
                    success_count += 1
                    response_times.append(time.time() - start_time)
                
            except Exception as e:
                print(f"Request {i} failed: {e}")
            
            # Add delay between requests (visualization is more resource intensive)
            time.sleep(1.0)
        
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            print(f"✅ Attention Visualization Performance Results:")
            print(f"   Success Rate: {success_count}/{num_requests} ({success_count/num_requests*100:.1f}%)")
            print(f"   Average Response Time: {avg_time:.2f}s")
            print(f"   Median Response Time: {median_time:.2f}s")
            print(f"   Min Response Time: {min_time:.2f}s")
            print(f"   Max Response Time: {max_time:.2f}s")
            
            # Performance assertions (more lenient for visualization)
            assert avg_time < 30.0, f"Average response time too slow: {avg_time:.2f}s"
            assert success_count/num_requests >= 0.6, f"Success rate too low: {success_count/num_requests*100:.1f}%"
        else:
            print("❌ No successful requests for attention visualization benchmark")
            assert False, "Attention visualization benchmark failed completely"
    
    def benchmark_concurrent_load(self):
        """Benchmark concurrent request handling"""
        import concurrent.futures
        
        print(f"\n⚡ Benchmarking Concurrent Load")
        
        def make_generate_request():
            payload = {
                "prompt": "Concurrent load test prompt",
                "max_tokens": 10,
                "temperature": 1.0,
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
                return response.status_code == 200, time.time() - start_time
            except:
                return False, 0
        
        # Test with 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            start_time = time.time()
            futures = [executor.submit(make_generate_request) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            total_time = time.time() - start_time
        
        successful_requests = [r for r in results if r[0]]
        success_rate = len(successful_requests) / len(results)
        
        if successful_requests:
            response_times = [r[1] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)
            
            print(f"✅ Concurrent Load Test Results:")
            print(f"   Total Time: {total_time:.2f}s")
            print(f"   Success Rate: {len(successful_requests)}/5 ({success_rate*100:.1f}%)")
            print(f"   Average Response Time: {avg_response_time:.2f}s")
            
            # Concurrent performance assertions
            assert success_rate >= 0.6, f"Concurrent success rate too low: {success_rate*100:.1f}%"
        else:
            print("❌ Concurrent load test failed completely")

def main():
    """Main function for running performance benchmarks"""
    parser = argparse.ArgumentParser(description='Lambda Performance Benchmarks')
    parser.add_argument('--api-base', required=True, help='Base API URL')
    parser.add_argument('--requests', type=int, default=10, help='Number of requests for benchmarks')
    
    args = parser.parse_args()
    
    print(f"🏁 Starting Lambda Performance Benchmarks")
    print(f"API Base: {args.api_base}")
    print(f"Test Requests: {args.requests}")
    
    benchmarks = LambdaPerformanceBenchmarks(args.api_base)
    
    try:
        benchmarks.benchmark_text_generation(args.requests)
        benchmarks.benchmark_attention_visualization(max(args.requests // 2, 3))
        benchmarks.benchmark_concurrent_load()
        
        print(f"\n✅ All performance benchmarks completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Performance benchmark failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()