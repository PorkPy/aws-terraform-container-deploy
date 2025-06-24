# tests/performance/test_cold_start_analysis.py
"""Cold start performance analysis for Lambda functions"""

import requests
import json
import time
import argparse

class ColdStartAnalysis:
    """Analyze Lambda cold start performance"""
    
    def __init__(self, api_base):
        self.api_base = api_base
        self.generate_endpoint = f"{api_base}/generate"
        self.visualize_endpoint = f"{api_base}/visualize"
    
    def simulate_cold_start(self, endpoint, payload, endpoint_name):
        """Simulate and measure cold start"""
        print(f"\n❄️ Analyzing Cold Start for {endpoint_name}")
        
        # First request (likely cold start)
        print("Making first request (cold start)...")
        start_time = time.time()
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            cold_start_time = time.time() - start_time
            cold_start_success = response.status_code == 200
            
            print(f"Cold start time: {cold_start_time:.2f}s")
            print(f"Cold start success: {cold_start_success}")
            
        except Exception as e:
            print(f"Cold start failed: {e}")
            cold_start_time = None
            cold_start_success = False
        
        # Wait a moment, then make warm requests
        time.sleep(2)
        
        warm_times = []
        warm_successes = []
        
        print("Making warm requests...")
        for i in range(3):
            start_time = time.time()
            try:
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                warm_time = time.time() - start_time
                warm_success = response.status_code == 200
                
                warm_times.append(warm_time)
                warm_successes.append(warm_success)
                
                print(f"Warm request {i+1}: {warm_time:.2f}s, success: {warm_success}")
                
            except Exception as e:
                print(f"Warm request {i+1} failed: {e}")
                warm_successes.append(False)
            
            time.sleep(1)
        
        # Analysis
        if cold_start_time and warm_times:
            avg_warm_time = sum(warm_times) / len(warm_times)
            cold_start_overhead = cold_start_time - avg_warm_time
            
            print(f"\n📊 {endpoint_name} Cold Start Analysis:")
            print(f"   Cold Start Time: {cold_start_time:.2f}s")
            print(f"   Average Warm Time: {avg_warm_time:.2f}s")
            print(f"   Cold Start Overhead: {cold_start_overhead:.2f}s")
            print(f"   Cold Start Success: {cold_start_success}")
            print(f"   Warm Success Rate: {sum(warm_successes)}/{len(warm_successes)}")
            
            # Performance assertions
            assert cold_start_time < 60.0, f"{endpoint_name} cold start too slow: {cold_start_time:.2f}s"
            assert avg_warm_time < 10.0, f"{endpoint_name} warm requests too slow: {avg_warm_time:.2f}s"
            
            return {
                'cold_start_time': cold_start_time,
                'avg_warm_time': avg_warm_time,
                'cold_start_overhead': cold_start_overhead,
                'cold_start_success': cold_start_success,
                'warm_success_rate': sum(warm_successes) / len(warm_successes)
            }
        
        return None
    
    def analyze_both_functions(self):
        """Analyze cold starts for both Lambda functions"""
        print("🔬 Lambda Cold Start Performance Analysis")
        
        # Generate text cold start analysis
        generate_payload = {
            "prompt": "Cold start analysis test",
            "max_tokens": 15,
            "temperature": 0.8,
            "top_k": 50
        }
        
        generate_results = self.simulate_cold_start(
            self.generate_endpoint, 
            generate_payload, 
            "Text Generation"
        )
        
        # Wait between tests to ensure functions go cold again
        print("\n⏳ Waiting 60 seconds for functions to go cold...")
        time.sleep(60)
        
        # Visualize attention cold start analysis
        visualize_payload = {
            "text": "Cold start visualization test",
            "layer": 1,
            "heads": [0]
        }
        
        visualize_results = self.simulate_cold_start(
            self.visualize_endpoint,
            visualize_payload,
            "Attention Visualization"
        )
        
        # Summary
        print(f"\n📈 Cold Start Performance Summary:")
        if generate_results:
            print(f"   Text Generation Cold Start: {generate_results['cold_start_time']:.2f}s")
            print(f"   Text Generation Warm Average: {generate_results['avg_warm_time']:.2f}s")
        
        if visualize_results:
            print(f"   Visualization Cold Start: {visualize_results['cold_start_time']:.2f}s")
            print(f"   Visualization Warm Average: {visualize_results['avg_warm_time']:.2f}s")
        
        return generate_results, visualize_results

def main():
    """Main function for cold start analysis"""
    parser = argparse.ArgumentParser(description='Lambda Cold Start Analysis')
    parser.add_argument('--api-base', required=True, help='Base API URL')
    
    args = parser.parse_args()
    
    print(f"🥶 Starting Lambda Cold Start Analysis")
    print(f"API Base: {args.api_base}")
    
    analyzer = ColdStartAnalysis(args.api_base)
    
    try:
        generate_results, visualize_results = analyzer.analyze_both_functions()
        
        if generate_results and visualize_results:
            print(f"\n✅ Cold start analysis completed successfully!")
        else:
            print(f"\n⚠️ Cold start analysis completed with some failures")
        
    except Exception as e:
        print(f"\n❌ Cold start analysis failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()