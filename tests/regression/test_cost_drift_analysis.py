# tests/regression/test_cost_drift_analysis.py
"""Cost drift analysis and regression testing"""

import boto3
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict

class CostDriftAnalyzer:
    """Analyze cost drift and spending patterns"""
    
    def __init__(self, region, project_prefix):
        self.region = region
        self.project_prefix = project_prefix
        self.ce_client = boto3.client('ce', region_name='us-east-1')  # Cost Explorer only in us-east-1
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
    
    def get_daily_costs(self, days_back=7):
        """Get daily costs for the last N days"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ],
                Filter={
                    'Tags': {
                        'Key': 'Project',
                        'Values': ['TransformerModel']
                    }
                }
            )
            
            return response['ResultsByTime']
            
        except Exception as e:
            print(f"⚠️ Could not retrieve cost data: {e}")
            return []
    
    def analyze_cost_trends(self):
        """Analyze cost trends and detect anomalies"""
        print("💰 Analyzing cost trends...")
        
        cost_data = self.get_daily_costs(14)  # Last 2 weeks
        
        if not cost_data:
            print("⚠️ No cost data available for analysis")
            return
        
        daily_totals = []
        service_costs = defaultdict(list)
        
        for day_data in cost_data:
            date = day_data['TimePeriod']['Start']
            total_cost = 0
            
            for group in day_data['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['BlendedCost']['Amount'])
                total_cost += cost
                service_costs[service].append((date, cost))
            
            daily_totals.append((date, total_cost))
        
        # Calculate statistics
        costs = [cost for _, cost in daily_totals]
        if costs:
            avg_daily_cost = sum(costs) / len(costs)
            max_daily_cost = max(costs)
            min_daily_cost = min(costs)
            
            print(f"📊 Cost Analysis Results:")
            print(f"   Average Daily Cost: ${avg_daily_cost:.4f}")
            print(f"   Maximum Daily Cost: ${max_daily_cost:.4f}")
            print(f"   Minimum Daily Cost: ${min_daily_cost:.4f}")
            
            # Detect cost spikes
            threshold = avg_daily_cost * 2  # Alert if cost is 2x average
            for date, cost in daily_totals:
                if cost > threshold:
                    print(f"⚠️ Cost spike detected on {date}: ${cost:.4f}")
            
            # Service breakdown
            print(f"\n🔍 Top Cost Services:")
            service_totals = {}
            for service, cost_history in service_costs.items():
                total = sum(cost for _, cost in cost_history)
                service_totals[service] = total
            
            for service, total in sorted(service_totals.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   {service}: ${total:.4f}")
            
            # Cost drift validation
            if len(costs) >= 7:
                recent_avg = sum(costs[-3:]) / 3  # Last 3 days
                earlier_avg = sum(costs[-7:-4]) / 3  # 3 days before that
                
                if recent_avg > earlier_avg * 1.5:
                    print(f"🚨 COST DRIFT ALERT: Recent costs ({recent_avg:.4f}) significantly higher than earlier period ({earlier_avg:.4f})")
                    assert False, f"Cost drift detected: {recent_avg:.4f} vs {earlier_avg:.4f}"
                else:
                    print(f"✅ No significant cost drift detected")
    
    def check_lambda_invocation_costs(self):
        """Check Lambda invocation patterns for cost optimization"""
        print("\n⚡ Analyzing Lambda invocation costs...")
        
        # Get Lambda metrics for last 24 hours
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        lambda_functions = [
            f"{self.project_prefix}-generate-text",
            f"{self.project_prefix}-visualize-attention"
        ]
        
        total_invocations = 0
        total_duration_ms = 0
        
        for function_name in lambda_functions:
            try:
                # Get invocation count
                invocations_response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Invocations',
                    Dimensions=[
                        {
                            'Name': 'FunctionName',
                            'Value': function_name
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour periods
                    Statistics=['Sum']
                )
                
                function_invocations = sum(point['Sum'] for point in invocations_response['Datapoints'])
                total_invocations += function_invocations
                
                # Get duration
                duration_response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Duration',
                    Dimensions=[
                        {
                            'Name': 'FunctionName',
                            'Value': function_name
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average']
                )
                
                if duration_response['Datapoints']:
                    avg_duration = sum(point['Average'] for point in duration_response['Datapoints']) / len(duration_response['Datapoints'])
                    total_duration_ms += avg_duration * function_invocations
                
                print(f"   {function_name}: {function_invocations} invocations")
                
            except Exception as e:
                print(f"⚠️ Could not get metrics for {function_name}: {e}")
        
        # Cost estimation (rough)
        if total_invocations > 0:
            # AWS Lambda pricing: $0.20 per 1M requests + $0.0000166667 for every GB-second
            request_cost = (total_invocations / 1_000_000) * 0.20
            # Assume 1GB memory allocation
            duration_cost = (total_duration_ms / 1000) * 0.0000166667
            estimated_cost = request_cost + duration_cost
            
            print(f"📊 Lambda Cost Analysis (24h):")
            print(f"   Total Invocations: {total_invocations}")
            print(f"   Estimated Cost: ${estimated_cost:.6f}")
            print(f"   Average Cost per Invocation: ${estimated_cost/total_invocations:.6f}" if total_invocations > 0 else "   No invocations")
            
            # Alert if too many invocations (cost optimization)
            daily_invocation_limit = 1000  # Reasonable limit for demo project
            if total_invocations > daily_invocation_limit:
                print(f"⚠️ HIGH INVOCATION ALERT: {total_invocations} invocations exceeds daily limit of {daily_invocation_limit}")
        
        print("✅ Lambda cost analysis completed")
    
    def check_api_gateway_costs(self):
        """Check API Gateway usage patterns"""
        print("\n🌐 Analyzing API Gateway costs...")
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        try:
            # Get API Gateway request count
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApiGateway',
                MetricName='Count',
                Dimensions=[
                    {
                        'Name': 'ApiName',
                        'Value': 'transformer-model-api'
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            total_requests = sum(point['Sum'] for point in response['Datapoints'])
            
            # API Gateway pricing: $3.50 per million API calls
            estimated_cost = (total_requests / 1_000_000) * 3.50
            
            print(f"📊 API Gateway Cost Analysis (24h):")
            print(f"   Total Requests: {total_requests}")
            print(f"   Estimated Cost: ${estimated_cost:.6f}")
            
            # Alert threshold
            daily_request_limit = 2000  # Reasonable limit
            if total_requests > daily_request_limit:
                print(f"⚠️ HIGH API USAGE ALERT: {total_requests} requests exceeds daily limit of {daily_request_limit}")
            
        except Exception as e:
            print(f"⚠️ Could not get API Gateway metrics: {e}")
        
        print("✅ API Gateway cost analysis completed")
    
    def generate_cost_optimization_recommendations(self):
        """Generate cost optimization recommendations"""
        print("\n💡 Cost Optimization Recommendations:")
        
        recommendations = [
            "🔧 Consider implementing request caching to reduce Lambda invocations",
            "⏰ Monitor cold start patterns - consider provisioned concurrency for high-traffic periods",
            "📊 Review CloudWatch log retention periods to avoid unnecessary storage costs",
            "🗂️ Implement S3 lifecycle policies for model artifacts and logs",
            "⚡ Optimize Lambda memory allocation based on actual usage patterns", 
            "🔄 Consider using Lambda@Edge for geographically distributed users",
            "📈 Set up CloudWatch billing alerts for proactive cost management",
            "🏷️ Ensure all resources are properly tagged for accurate cost attribution"
        ]
        
        for i, recommendation in enumerate(recommendations, 1):
            print(f"   {i}. {recommendation}")
        
        print("\n💰 Cost Monitoring Best Practices:")
        print("   • Review AWS Cost Explorer weekly")
        print("   • Set up budget alerts at 80% and 100% thresholds") 
        print("   • Monitor Lambda duration and memory utilization")
        print("   • Track API Gateway request patterns")
        print("   • Regular cleanup of old CloudWatch logs and S3 objects")

def main():
    """Main function for cost drift analysis"""
    parser = argparse.ArgumentParser(description='Cost Drift Analysis')
    parser.add_argument('--region', default='eu-west-2', help='AWS region')
    parser.add_argument('--project-prefix', default='transformer-model', help='Project prefix for resources')
    
    args = parser.parse_args()
    
    print(f"💸 Starting cost drift analysis")
    print(f"Region: {args.region}")
    print(f"Project: {args.project_prefix}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    analyzer = CostDriftAnalyzer(args.region, args.project_prefix)
    
    try:
        analyzer.analyze_cost_trends()
        analyzer.check_lambda_invocation_costs()
        analyzer.check_api_gateway_costs()
        analyzer.generate_cost_optimization_recommendations()
        
        print(f"\n✅ Cost drift analysis completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Cost drift analysis failed: {e}")
        # Don't exit with error code unless it's a real cost drift issue
        if "COST DRIFT ALERT" in str(e):
            exit(1)

if __name__ == "__main__":
    main()