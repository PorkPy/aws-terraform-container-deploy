# scripts/setup_custom_metrics.py
"""Setup custom CloudWatch metrics for the ML pipeline"""

import boto3
import json
from datetime import datetime

def setup_custom_metrics():
    """Configure custom CloudWatch metrics"""
    cloudwatch = boto3.client('cloudwatch', region_name='eu-west-2')
    
    print("🔧 Setting up custom CloudWatch metrics...")
    
    # Custom metrics to track
    custom_metrics = [
        {
            'MetricName': 'ModelInferenceLatency',
            'Namespace': 'TransformerModel/Performance',
            'Dimensions': [
                {'Name': 'FunctionType', 'Value': 'TextGeneration'},
                {'Name': 'Environment', 'Value': 'Production'}
            ],
            'Unit': 'Milliseconds',
            'Value': 0  # Initial value
        },
        {
            'MetricName': 'AttentionVisualizationLatency', 
            'Namespace': 'TransformerModel/Performance',
            'Dimensions': [
                {'Name': 'FunctionType', 'Value': 'AttentionVisualization'},
                {'Name': 'Environment', 'Value': 'Production'}
            ],
            'Unit': 'Milliseconds',
            'Value': 0
        },
        {
            'MetricName': 'ModelLoadTime',
            'Namespace': 'TransformerModel/ColdStart',
            'Dimensions': [
                {'Name': 'ModelType', 'Value': 'Transformer'},
                {'Name': 'Environment', 'Value': 'Production'}
            ],
            'Unit': 'Seconds',
            'Value': 0
        },
        {
            'MetricName': 'TokensGenerated',
            'Namespace': 'TransformerModel/Usage',
            'Dimensions': [
                {'Name': 'FunctionType', 'Value': 'TextGeneration'},
                {'Name': 'Environment', 'Value': 'Production'}
            ],
            'Unit': 'Count',
            'Value': 0
        }
    ]
    
    # Put initial metric data
    for metric in custom_metrics:
        try:
            cloudwatch.put_metric_data(
                Namespace=metric['Namespace'],
                MetricData=[
                    {
                        'MetricName': metric['MetricName'],
                        'Dimensions': metric['Dimensions'],
                        'Unit': metric['Unit'],
                        'Value': metric['Value'],
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
            print(f"✅ Created metric: {metric['MetricName']}")
            
        except Exception as e:
            print(f"❌ Failed to create metric {metric['MetricName']}: {e}")
    
    print("✅ Custom metrics setup completed!")

def create_metric_filters():
    """Create CloudWatch Log metric filters"""
    logs_client = boto3.client('logs', region_name='eu-west-2')
    
    print("🔍 Setting up CloudWatch log metric filters...")
    
    # Metric filters for Lambda function logs
    metric_filters = [
        {
            'log_group': '/aws/lambda/transformer-model-generate-text',
            'filter_name': 'GenerationErrors',
            'filter_pattern': '[timestamp, requestId, "ERROR"]',
            'metric_namespace': 'TransformerModel/Errors',
            'metric_name': 'GenerationErrors',
            'metric_value': '1'
        },
        {
            'log_group': '/aws/lambda/transformer-model-visualize-attention',
            'filter_name': 'VisualizationErrors', 
            'filter_pattern': '[timestamp, requestId, "ERROR"]',
            'metric_namespace': 'TransformerModel/Errors',
            'metric_name': 'VisualizationErrors',
            'metric_value': '1'
        },
        {
            'log_group': '/aws/lambda/transformer-model-generate-text',
            'filter_name': 'ModelLoadTime',
            'filter_pattern': '[timestamp, requestId, "Model loaded successfully"]',
            'metric_namespace': 'TransformerModel/Performance',
            'metric_name': 'ModelLoads',
            'metric_value': '1'
        }
    ]
    
    for filter_config in metric_filters:
        try:
            logs_client.put_metric_filter(
                logGroupName=filter_config['log_group'],
                filterName=filter_config['filter_name'],
                filterPattern=filter_config['filter_pattern'],
                metricTransformations=[
                    {
                        'metricName': filter_config['metric_name'],
                        'metricNamespace': filter_config['metric_namespace'],
                        'metricValue': filter_config['metric_value']
                    }
                ]
            )
            print(f"✅ Created metric filter: {filter_config['filter_name']}")
            
        except logs_client.exceptions.ResourceAlreadyExistsException:
            print(f"⚠️ Metric filter already exists: {filter_config['filter_name']}")
        except Exception as e:
            print(f"❌ Failed to create metric filter {filter_config['filter_name']}: {e}")
    
    print("✅ Metric filters setup completed!")

if __name__ == "__main__":
    setup_custom_metrics()
    create_metric_filters()