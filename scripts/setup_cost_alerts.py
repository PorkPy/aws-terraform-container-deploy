# scripts/setup_cost_alerts.py
"""Setup cost monitoring and alerts for the ML pipeline"""

import boto3
import json
import argparse
from datetime import datetime, timedelta

def setup_budget_alerts(threshold_amount, notification_email):
    """Setup AWS Budget alerts for cost monitoring"""
    budgets_client = boto3.client('budgets', region_name='us-east-1')  # Budgets API only in us-east-1
    account_id = boto3.client('sts').get_caller_identity()['Account']
    
    print(f"💰 Setting up budget alerts (Threshold: ${threshold_amount})")
    
    # Create budget for transformer model resources
    budget_name = "transformer-model-monthly-budget"
    
    budget = {
        'BudgetName': budget_name,
        'BudgetLimit': {
            'Amount': str(threshold_amount),
            'Unit': 'USD'
        },
        'TimeUnit': 'MONTHLY',
        'BudgetType': 'COST',
        'CostFilters': {
            'TagKey': ['Project'],
            'TagValue': ['TransformerModel']
        },
        'TimePeriod': {
            'Start': datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            'End': datetime(2025, 12, 31)
        }
    }
    
    # Notification for 80% of budget
    notifications = [
        {
            'Notification': {
                'NotificationType': 'ACTUAL',
                'ComparisonOperator': 'GREATER_THAN',
                'Threshold': 80.0,
                'ThresholdType': 'PERCENTAGE'
            },
            'Subscribers': [
                {
                    'SubscriptionType': 'EMAIL',
                    'Address': notification_email
                }
            ]
        },
        {
            'Notification': {
                'NotificationType': 'FORECASTED',
                'ComparisonOperator': 'GREATER_THAN', 
                'Threshold': 100.0,
                'ThresholdType': 'PERCENTAGE'
            },
            'Subscribers': [
                {
                    'SubscriptionType': 'EMAIL',
                    'Address': notification_email
                }
            ]
        }
    ]
    
    try:
        # Create budget
        budgets_client.create_budget(
            AccountId=account_id,
            Budget=budget,
            NotificationsWithSubscribers=notifications
        )
        print(f"✅ Created budget: {budget_name}")
        
    except budgets_client.exceptions.DuplicateRecordException:
        print(f"⚠️ Budget already exists: {budget_name}")
        
        # Update existing budget
        try:
            budgets_client.update_budget(
                AccountId=account_id,
                NewBudget=budget
            )
            print(f"✅ Updated existing budget: {budget_name}")
        except Exception as e:
            print(f"❌ Failed to update budget: {e}")
            
    except Exception as e:
        print(f"❌ Failed to create budget: {e}")

def setup_cloudwatch_cost_alarms():
    """Setup CloudWatch alarms for cost anomalies"""
    cloudwatch = boto3.client('cloudwatch', region_name='eu-west-2')
    
    print("⚠️ Setting up CloudWatch cost alarms...")
    
    # Alarm for Lambda invocation spikes
    lambda_alarm = {
        'AlarmName': 'TransformerModel-HighInvocationCount',
        'ComparisonOperator': 'GreaterThanThreshold',
        'EvaluationPeriods': 2,
        'MetricName': 'Invocations',
        'Namespace': 'AWS/Lambda',
        'Period': 300,  # 5 minutes
        'Statistic': 'Sum',
        'Threshold': 100.0,  # More than 100 invocations in 5 minutes
        'ActionsEnabled': True,
        'AlarmDescription': 'Alarm when Lambda invocations are unusually high',
        'Dimensions': [
            {
                'Name': 'FunctionName',
                'Value': 'transformer-model-generate-text'
            }
        ],
        'Unit': 'Count'
    }
    
    # Alarm for API Gateway request spikes
    api_alarm = {
        'AlarmName': 'TransformerModel-HighAPIRequestCount',
        'ComparisonOperator': 'GreaterThanThreshold',
        'EvaluationPeriods': 2,
        'MetricName': 'Count',
        'Namespace': 'AWS/ApiGateway',
        'Period': 300,
        'Statistic': 'Sum',
        'Threshold': 150.0,  # More than 150 API requests in 5 minutes
        'ActionsEnabled': True,
        'AlarmDescription': 'Alarm when API Gateway requests are unusually high'
    }
    
    alarms = [lambda_alarm, api_alarm]
    
    for alarm in alarms:
        try:
            cloudwatch.put_metric_alarm(**alarm)
            print(f"✅ Created alarm: {alarm['AlarmName']}")
        except Exception as e:
            print(f"❌ Failed to create alarm {alarm['AlarmName']}: {e}")
    
    print("✅ CloudWatch cost alarms setup completed!")

def main():
    """Main function for setting up cost alerts"""
    parser = argparse.ArgumentParser(description='Setup Cost Monitoring & Alerts')
    parser.add_argument('--threshold', type=float, default=10.0, help='Monthly budget threshold in USD')
    parser.add_argument('--email', required=True, help='Email address for notifications')
    
    args = parser.parse_args()
    
    print(f"💰 Setting up cost monitoring with ${args.threshold} threshold")
    print(f"📧 Notifications will be sent to: {args.email}")
    
    try:
        setup_budget_alerts(args.threshold, args.email)
        setup_cloudwatch_cost_alarms()
        print(f"\n✅ Cost monitoring setup completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Cost monitoring setup failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()