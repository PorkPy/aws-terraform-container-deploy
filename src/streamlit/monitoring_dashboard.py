import streamlit as st
import boto3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time

# AWS Configuration
AWS_REGION = "eu-west-2"
FUNCTION_NAMES = [
    "transformer-model-generate-text-q3ukv7",
    "transformer-model-visualize-attention-q3ukv7"
]

def get_aws_client(service):
    """Get AWS client with error handling"""
    try:
        return boto3.client(service, region_name=AWS_REGION)
    except Exception as e:
        st.error(f"Failed to connect to AWS {service}: {str(e)}")
        return None

def get_lambda_info():
    """Get Lambda function information"""
    lambda_client = get_aws_client('lambda')
    if not lambda_client:
        return {}
    
    functions_info = {}
    for function_name in FUNCTION_NAMES:
        try:
            response = lambda_client.get_function_configuration(FunctionName=function_name)
            functions_info[function_name] = {
                'timeout': response['Timeout'],
                'memory': response['MemorySize'],
                'last_modified': response['LastModified'],
                'runtime': response.get('PackageType', 'Unknown'),
                'state': response['State'],
                'code_size': response['CodeSize'],
                'environment': response.get('Environment', {}).get('Variables', {})
            }
        except Exception as e:
            st.error(f"Error getting info for {function_name}: {str(e)}")
            functions_info[function_name] = {'error': str(e)}
    
    return functions_info

def get_cloudwatch_metrics():
    """Get CloudWatch metrics for Lambda functions"""
    cloudwatch = get_aws_client('cloudwatch')
    if not cloudwatch:
        return {}
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    
    metrics_data = {}
    
    for function_name in FUNCTION_NAMES:
        try:
            # Get invocation metrics
            invocations = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Sum']
            )
            
            # Get duration metrics
            duration = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            # Get error metrics
            errors = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            metrics_data[function_name] = {
                'invocations': invocations['Datapoints'],
                'duration': duration['Datapoints'],
                'errors': errors['Datapoints']
            }
            
        except Exception as e:
            st.error(f"Error getting metrics for {function_name}: {str(e)}")
            metrics_data[function_name] = {'error': str(e)}
    
    return metrics_data

def get_recent_logs():
    """Get recent CloudWatch logs"""
    logs_client = get_aws_client('logs')
    if not logs_client:
        return {}
    
    recent_logs = {}
    start_time = int((datetime.utcnow() - timedelta(hours=1)).timestamp() * 1000)
    
    for function_name in FUNCTION_NAMES:
        log_group = f"/aws/lambda/{function_name}"
        try:
            response = logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=start_time,
                limit=20
            )
            
            logs = []
            for event in response['events']:
                logs.append({
                    'timestamp': datetime.fromtimestamp(event['timestamp']/1000),
                    'message': event['message'].strip()
                })
            
            recent_logs[function_name] = sorted(logs, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            recent_logs[function_name] = [{'error': str(e)}]
    
    return recent_logs

def display_system_health():
    """Display system health overview"""
    st.header("🏥 System Health Overview")
    
    # Get Lambda info
    lambda_info = get_lambda_info()
    
    if lambda_info:
        cols = st.columns(len(FUNCTION_NAMES))
        
        for i, (func_name, info) in enumerate(lambda_info.items()):
            with cols[i]:
                short_name = func_name.split('-')[-2]  # get 'generate' or 'visualize'
                
                if 'error' in info:
                    st.error(f"❌ {short_name.title()}")
                    st.write(f"Error: {info['error']}")
                else:
                    st.success(f"✅ {short_name.title()}")
                    st.metric("Memory", f"{info['memory']} MB")
                    st.metric("Timeout", f"{info['timeout']} sec")
                    st.metric("State", info['state'])
                    
                    # Last modified
                    last_mod = datetime.fromisoformat(info['last_modified'].replace('Z', '+00:00'))
                    time_ago = datetime.now(last_mod.tzinfo) - last_mod
                    st.caption(f"Updated {time_ago.days}d {time_ago.seconds//3600}h ago")

def display_performance_metrics():
    """Display performance metrics and charts"""
    st.header("📊 Performance Metrics (Last 24 Hours)")
    
    metrics_data = get_cloudwatch_metrics()
    
    if not metrics_data:
        st.warning("No metrics data available")
        return
    
    # Create tabs for different metrics
    tab1, tab2, tab3 = st.tabs(["Invocations", "Duration", "Errors"])
    
    with tab1:
        st.subheader("Function Invocations")
        for func_name, data in metrics_data.items():
            if 'error' not in data and data['invocations']:
                df = pd.DataFrame(data['invocations'])
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df = df.sort_values('Timestamp')
                
                fig = px.line(df, x='Timestamp', y='Sum', 
                             title=f"{func_name.split('-')[-2].title()} Invocations")
                st.plotly_chart(fig, use_container_width=True)
                
                total_invocations = df['Sum'].sum()
                st.metric(f"Total Invocations", int(total_invocations))
    
    with tab2:
        st.subheader("Execution Duration")
        for func_name, data in metrics_data.items():
            if 'error' not in data and data['duration']:
                df = pd.DataFrame(data['duration'])
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df = df.sort_values('Timestamp')
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Average'], 
                                       name='Average', mode='lines+markers'))
                fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Maximum'], 
                                       name='Maximum', mode='lines+markers'))
                fig.update_layout(title=f"{func_name.split('-')[-2].title()} Duration (ms)",
                                 xaxis_title="Time", yaxis_title="Duration (ms)")
                st.plotly_chart(fig, use_container_width=True)
                
                if not df.empty:
                    avg_duration = df['Average'].mean()
                    max_duration = df['Maximum'].max()
                    col1, col2 = st.columns(2)
                    col1.metric("Avg Duration", f"{avg_duration:.0f}ms")
                    col2.metric("Max Duration", f"{max_duration:.0f}ms")
    
    with tab3:
        st.subheader("Error Count")
        for func_name, data in metrics_data.items():
            if 'error' not in data and data['errors']:
                df = pd.DataFrame(data['errors'])
                if not df.empty:
                    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                    df = df.sort_values('Timestamp')
                    
                    fig = px.bar(df, x='Timestamp', y='Sum', 
                               title=f"{func_name.split('-')[-2].title()} Errors")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    total_errors = df['Sum'].sum()
                    if total_errors > 0:
                        st.error(f"Total Errors: {int(total_errors)}")
                    else:
                        st.success("No errors in the last 24 hours! 🎉")
                else:
                    st.success("No errors in the last 24 hours! 🎉")

def display_recent_logs():
    """Display recent logs"""
    st.header("📝 Recent Logs (Last Hour)")
    
    recent_logs = get_recent_logs()
    
    for func_name, logs in recent_logs.items():
        st.subheader(f"{func_name.split('-')[-2].title()} Function Logs")
        
        if logs and 'error' not in logs[0]:
            # Create a DataFrame for better display
            log_data = []
            for log in logs[:10]:  # Show last 10 logs
                log_data.append({
                    'Time': log['timestamp'].strftime('%H:%M:%S'),
                    'Message': log['message'][:100] + '...' if len(log['message']) > 100 else log['message']
                })
            
            if log_data:
                df = pd.DataFrame(log_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No recent logs found")
        else:
            st.error(f"Error fetching logs: {logs[0].get('error', 'Unknown error')}")

def display_cost_monitoring():
    """Display cost monitoring estimates"""
    st.header("💰 Cost Monitoring")
    
    # This would require AWS Cost Explorer API or CloudWatch billing metrics
    # For demo purposes, we'll show estimated costs based on invocations
    
    st.info("💡 **Cost Optimization Tips:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Current Configuration:**
        - Memory: 3008 MB
        - Timeout: 900 seconds
        - Reserved Concurrency: 1
        
        **Estimated Costs:**
        - ~$0.20 per 1000 invocations
        - ~$0.0167 per GB-second
        """)
    
    with col2:
        st.markdown("""
        **Optimization Opportunities:**
        - Monitor cold start frequency
        - Adjust memory based on actual usage
        - Consider provisioned concurrency for production
        - Implement caching strategies
        """)

def main_monitoring():
    """Main monitoring dashboard"""
    st.title("🔍 AWS Lambda Monitoring Dashboard")
    st.markdown("*Real-time monitoring of transformer model infrastructure*")
    st.markdown("---")
    
    # Auto-refresh option
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("**Live Dashboard** - Monitor your AWS Lambda functions")
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (30s)")
    with col3:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Display sections
    display_system_health()
    st.markdown("---")
    
    display_performance_metrics() 
    st.markdown("---")
    
    display_recent_logs()
    st.markdown("---")
    
    display_cost_monitoring()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>📊 Monitoring Dashboard • Built with Streamlit • AWS CloudWatch Integration</p>
    </div>
    """, unsafe_allow_html=True)