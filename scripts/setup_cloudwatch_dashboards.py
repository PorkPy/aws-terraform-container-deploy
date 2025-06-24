# scripts/setup_cloudwatch_dashboards.py
"""Setup CloudWatch dashboards for monitoring the ML pipeline"""

import boto3
import json
import argparse

def create_performance_dashboard(project_name):
    """Create CloudWatch dashboard for performance monitoring"""
    cloudwatch = boto3.client('cloudwatch', region_name='eu-west-2')
    
    dashboard_name = f"{project_name}-performance-dashboard"
    
    # Dashboard configuration
    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Duration", "FunctionName", f"{project_name}-generate-text"],
                        [".", ".", ".", f"{project_name}-visualize-attention"],
                        ["AWS/Lambda", "Invocations", "FunctionName", f"{project_name}-generate-text"],
                        [".", ".", ".", f"{project_name}-visualize-attention"]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "eu-west-2",
                    "title": "Lambda Function Performance",
                    "period": 300,
                    "stat": "Average"
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Errors", "FunctionName", f"{project_name}-generate-text"],
                        [".", ".", ".", f"{project_name}-visualize-attention"],
                        ["AWS/Lambda", "Throttles", "FunctionName", f"{project_name}-generate-text"],
                        [".", ".", ".", f"{project_name}-visualize-attention"]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "eu-west-2",
                    "title": "Lambda Function Errors & Throttles",
                    "period": 300,
                    "stat": "Sum"
                }
            },
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/ApiGateway", "Count", "ApiName", "transformer-model-api"],
                        ["AWS/ApiGateway", "Latency", "ApiName", "transformer-model-api"],
                        ["AWS/ApiGateway", "4XXError", "ApiName", "transformer-model-api"],
                        ["AWS/ApiGateway", "5XXError", "ApiName", "transformer-model-api"]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "eu-west-2",
                    "title": "API Gateway Metrics",
                    "period": 300,
                    "stat": "Average"
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["TransformerModel/Performance", "ModelInferenceLatency", "FunctionType", "TextGeneration"],
                        [".", "AttentionVisualizationLatency", ".", "AttentionVisualization"],
                        ["TransformerModel/ColdStart", "ModelLoadTime", "ModelType", "Transformer"]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "eu-west-2",
                    "title": "Custom ML Metrics",
                    "period": 300,
                    "stat": "Average"
                }
            },
            {
                "type": "log",
                "x": 0,
                "y": 12,
                "width": 24,
                "height": 6,
                "properties": {
                    "query": f"SOURCE '/aws/lambda/{project_name}-generate-text' | SOURCE '/aws/lambda/{project_name}-visualize-attention'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20",
                    "region": "eu-west-2",
                    "title": "Recent Errors",
                    "view": "table"
                }
            }
        ]
    }
    
    try:
        cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
        print(f"✅ Created performance dashboard: {dashboard_name}")
        
    except Exception as e:
        print(f"❌ Failed to create performance dashboard: {e}")

def create_cost_dashboard(project_name):
    """Create CloudWatch dashboard for cost monitoring"""
    cloudwatch = boto3.client('cloudwatch', region_name='eu-west-2')
    
    dashboard_name = f"{project_name}-cost-dashboard"
    
    # Cost dashboard configuration
    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Invocations", "FunctionName", f"{project_name}-generate-text"],
                        [".", ".", ".", f"{project_name}-visualize-attention"],
                        ["AWS/Lambda", "Duration", "FunctionName", f"{project_name}-generate-text"],
                        [".", ".", ".", f"{project_name}-visualize-attention"]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "eu-west-2",
                    "title": "Lambda Usage (Cost Drivers)",
                    "period": 3600,  # 1 hour
                    "stat": "Sum"
                }
            },
            {
                "type": "metric", 
                "x": 12,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/ApiGateway", "Count", "ApiName", "transformer-model-api"],
                        ["AWS/S3", "NumberOfObjects", "BucketName", f"{project_name}-artifacts", "StorageType", "AllStorageTypes"]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "eu-west-2", 
                    "title": "API & Storage Usage",
                    "period": 3600,
                    "stat": "Sum"
                }
            },
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 24,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["TransformerModel/Usage", "TokensGenerated", "FunctionType", "TextGeneration"],
                        ["TransformerModel/Performance", "ModelInferenceLatency", "FunctionType", "TextGeneration"],
                        [".", "AttentionVisualizationLatency", ".", "AttentionVisualization"]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "eu-west-2",
                    "title": "Usage Metrics (Business Logic)",
                    "period": 3600,
                    "stat": "Sum"
                }
            }
        ]
    }
    
    try:
        cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
        print(f"✅ Created cost dashboard: {dashboard_name}")
        
    except Exception as e:
        print(f"❌ Failed to create cost dashboard: {e}")

def main():
    """Main function for setting up CloudWatch dashboards"""
    parser = argparse.ArgumentParser(description='Setup CloudWatch Dashboards')
    parser.add_argument('--project-name', default='transformer-model', help='Project name for dashboard')
    
    args = parser.parse_args()
    
    print(f"📊 Setting up CloudWatch dashboards for project: {args.project_name}")
    
    try:
        create_performance_dashboard(args.project_name)
        create_cost_dashboard(args.project_name)
        
        print(f"\n✅ CloudWatch dashboards setup completed!")
        print(f"🔗 View dashboards in AWS Console: https://eu-west-2.console.aws.amazon.com/cloudwatch/home?region=eu-west-2#dashboards:")
        
    except Exception as e:
        print(f"\n❌ Dashboard setup failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()