import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
import time
import os


# AWS Configuration
AWS_REGION = "eu-west-2"
FUNCTION_NAMES = [
    "transformer-model-generate-text-q3ukv7",
    "transformer-model-visualize-attention-q3ukv7"
]

def get_aws_client(service):
    """Get AWS client with error handling"""
    try:
        import boto3
        return boto3.client(service, region_name=AWS_REGION)
    except Exception:
        return None

def check_aws_credentials():
    """Check if AWS credentials are properly configured"""
    try:
        import boto3
        client = boto3.client('lambda', region_name=AWS_REGION)
        response = client.list_functions(MaxItems=1)
        return True, "AWS credentials configured successfully"
    except Exception as e:
        return False, f"AWS credentials error: {str(e)}"

def get_lambda_info():
    """Get Lambda function information"""
    lambda_client = get_aws_client('lambda')
    if not lambda_client:
        # Return demo data when AWS credentials aren't available
        st.info("📍 **Demo Mode**: Showing sample data (AWS credentials not configured)")
        return {
            'transformer-model-generate-text-q3ukv7': {
                'timeout': 900,
                'memory': 3008,
                'last_modified': '2025-06-13T10:00:00.000+0000',
                'runtime': 'Image',
                'state': 'Active',
                'code_size': 256000000
            },
            'transformer-model-visualize-attention-q3ukv7': {
                'timeout': 900,
                'memory': 3008,
                'last_modified': '2025-06-13T10:00:00.000+0000',
                'runtime': 'Image',
                'state': 'Active',
                'code_size': 278000000
            }
        }
    
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
    """Get CloudWatch metrics for Lambda functions with proper period handling"""
    cloudwatch = get_aws_client('cloudwatch')
    if not cloudwatch:
        st.error("CloudWatch client failed to initialize")
        return {}
    
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=24)
    
    metrics_data = {}
    
    for function_name in FUNCTION_NAMES:
        try:
            # Get invocation metrics - using 1 hour periods to reduce noise
            invocations = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
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
        # Return demo logs
        demo_logs = {}
        for function_name in FUNCTION_NAMES:
            demo_logs[function_name] = [
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=5),
                    'message': 'Model loaded successfully!'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=10),
                    'message': 'Downloading model from S3...'
                },
                {
                    'timestamp': datetime.utcnow() - timedelta(minutes=15),
                    'message': 'Lambda function initialised'
                }
            ]
        return demo_logs
    
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
    
    # Check AWS credentials first
    creds_ok, creds_msg = check_aws_credentials()
    if creds_ok:
        st.success(f"✅ {creds_msg}")
    else:
        st.warning(f"⚠️ {creds_msg}")
    
    # Get Lambda info
    lambda_info = get_lambda_info()
    
    if lambda_info:
        cols = st.columns(len(FUNCTION_NAMES))
        
        for i, (func_name, info) in enumerate(lambda_info.items()):
            with cols[i]:
                short_name = func_name.split('-')[-2]  # get 'generate' or 'visualise'
                
                if 'error' in info:
                    st.error(f"❌ {short_name.title()}")
                    st.write(f"Error: {info['error']}")
                else:
                    st.success(f"✅ {short_name.title()}")
                    st.metric("Memory", f"{info['memory']} MB")
                    st.metric("Timeout", f"{info['timeout']} sec")
                    st.metric("State", info['state'])
                    
                    # Last modified
                    try:
                        last_mod = datetime.fromisoformat(info['last_modified'].replace('Z', '+00:00'))
                        time_ago = datetime.now(last_mod.tzinfo) - last_mod
                        st.caption(f"Updated {time_ago.days}d {time_ago.seconds//3600}h ago")
                    except:
                        st.caption("Recently updated")

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
        st.subheader("Function Invocations (Hourly)")
        st.markdown("*Note: Data points shown are hourly totals. Zero values indicate no requests during that hour.*")
        
        for func_name, data in metrics_data.items():
            if 'error' not in data and data['invocations']:
                df = pd.DataFrame(data['invocations'])
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df = df.sort_values('Timestamp')
                
                # Create a more informative chart
                fig = px.bar(df, x='Timestamp', y='Sum', 
                            title=f"{func_name.split('-')[-2].title()} Function - Hourly Invocations")
                fig.update_layout(
                    xaxis_title="Time (UTC)",
                    yaxis_title="Number of Invocations",
                    showlegend=False
                )
                fig.update_traces(marker_color='lightblue')
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculate statistics
                total_invocations = df['Sum'].sum()
                max_hourly = df['Sum'].max()
                avg_hourly = df['Sum'].mean()
                active_hours = (df['Sum'] > 0).sum()
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Invocations (24h)", int(total_invocations))
                col2.metric("Peak Hourly", int(max_hourly))
                col3.metric("Average/Hour", f"{avg_hourly:.1f}")
                col4.metric("Active Hours", f"{active_hours}/24")
    
    with tab2:
        st.subheader("Execution Duration")
        st.markdown("*Duration metrics only shown for hours with actual invocations.*")
        
        for func_name, data in metrics_data.items():
            if 'error' not in data and data['duration']:
                df = pd.DataFrame(data['duration'])
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df = df.sort_values('Timestamp')
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Average'], 
                                       name='Average', mode='lines+markers',
                                       line=dict(color='blue')))
                fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['Maximum'], 
                                       name='Maximum', mode='lines+markers',
                                       line=dict(color='red')))
                fig.update_layout(
                    title=f"{func_name.split('-')[-2].title()} Function - Execution Duration",
                    xaxis_title="Time (UTC)", 
                    yaxis_title="Duration (ms)"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                if not df.empty:
                    avg_duration = df['Average'].mean()
                    max_duration = df['Maximum'].max()
                    min_duration = df['Average'].min()
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Average Duration", f"{avg_duration:.0f}ms")
                    col2.metric("Peak Duration", f"{max_duration:.0f}ms")
                    col3.metric("Best Duration", f"{min_duration:.0f}ms")
    
    with tab3:
        st.subheader("Error Count")
        error_found = False
        
        for func_name, data in metrics_data.items():
            if 'error' not in data:
                if data['errors']:
                    df = pd.DataFrame(data['errors'])
                    if not df.empty and df['Sum'].sum() > 0:
                        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                        df = df.sort_values('Timestamp')
                        
                        fig = px.bar(df, x='Timestamp', y='Sum', 
                                   title=f"{func_name.split('-')[-2].title()} Function - Errors")
                        fig.update_traces(marker_color='red')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        total_errors = df['Sum'].sum()
                        st.error(f"Total Errors (24h): {int(total_errors)}")
                        error_found = True
        
        if not error_found:
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
            if logs:
                st.error(f"Error fetching logs: {logs[0].get('error', 'Unknown error')}")
            else:
                st.info("No logs available")

def get_cost_data():
    """Get AWS cost data for current and previous month"""
    cost_client = get_aws_client('ce')  # Cost Explorer
    if not cost_client:
        # Return demo cost data
        import random
        current_month_costs = {
            'AWS Lambda': round(random.uniform(2.50, 8.30), 2),
            'Amazon API Gateway': round(random.uniform(0.15, 0.45), 2),
            'Amazon S3': round(random.uniform(0.05, 0.25), 2),
            'Amazon CloudWatch': round(random.uniform(0.10, 0.35), 2),
            'Amazon ECR': round(random.uniform(0.02, 0.08), 2),
            'AWS Key Management Service': round(random.uniform(0.01, 0.03), 2)
        }
        
        previous_month_costs = {
            service: round(cost * random.uniform(0.7, 1.3), 2) 
            for service, cost in current_month_costs.items()
        }
        
        return {
            'current_month': current_month_costs,
            'previous_month': previous_month_costs,
            'total_current': sum(current_month_costs.values()),
            'total_previous': sum(previous_month_costs.values())
        }
    
    try:
        from datetime import datetime, timedelta
        import calendar
        
        # Get current month dates
        now = datetime.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_end = now
        
        # Get previous month dates
        if current_month_start.month == 1:
            prev_month_start = current_month_start.replace(year=current_month_start.year - 1, month=12)
        else:
            prev_month_start = current_month_start.replace(month=current_month_start.month - 1)
        
        prev_month_end = current_month_start - timedelta(days=1)
        
        # Get current month costs
        current_response = cost_client.get_cost_and_usage(
            TimePeriod={
                'Start': current_month_start.strftime('%Y-%m-%d'),
                'End': current_month_end.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        # Get previous month costs
        previous_response = cost_client.get_cost_and_usage(
            TimePeriod={
                'Start': prev_month_start.strftime('%Y-%m-%d'),
                'End': prev_month_end.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        def parse_costs(response):
            costs = {}
            if response['ResultsByTime']:
                for group in response['ResultsByTime'][0]['Groups']:
                    service = group['Keys'][0]
                    amount = float(group['Metrics']['BlendedCost']['Amount'])
                    if amount > 0:  # Only include services with actual costs
                        costs[service] = round(amount, 2)
            return costs
        
        current_costs = parse_costs(current_response)
        previous_costs = parse_costs(previous_response)
        
        return {
            'current_month': current_costs,
            'previous_month': previous_costs,
            'total_current': sum(current_costs.values()),
            'total_previous': sum(previous_costs.values())
        }
        
    except Exception as e:
        st.error(f"Error fetching cost data: {str(e)}")
        return None

def display_cost_analysis():
    """Display comprehensive cost analysis"""
    st.header("💰 AWS Cost Analysis")
    
    cost_data = get_cost_data()
    if not cost_data:
        st.warning("Unable to fetch cost data")
        return
    
    # Check if this is demo data
    cost_client = get_aws_client('ce')
    if not cost_client:
        st.info("📍 **Demo Mode**: Showing sample cost data (AWS credentials not configured)")
    
    # Top-level metrics with explicit time periods
    st.subheader(f"Cost Overview - {datetime.now().strftime('%B %Y')}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_current = cost_data['total_current']
    total_previous = cost_data['total_previous']
    cost_change = total_current - total_previous
    cost_change_pct = (cost_change / total_previous * 100) if total_previous > 0 else 0
    
    with col1:
        st.metric(
            f"Current Month ({datetime.now().strftime('%b %Y')})", 
            f"${total_current:.2f}",
            help=f"Total AWS costs from {datetime.now().strftime('%B 1')} to today"
        )
    
    with col2:
        prev_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime('%b %Y')
        st.metric(
            f"Previous Month ({prev_month})", 
            f"${total_previous:.2f}",
            help=f"Total AWS costs for {prev_month}"
        )
    
    with col3:
        st.metric(
            "Month-on-Month Change", 
            f"${cost_change:+.2f}", 
            delta=f"{cost_change_pct:+.1f}%",
            help="Comparison between current and previous month"
        )
    
    with col4:
        # Projected monthly cost based on current daily average
        days_elapsed = datetime.now().day
        daily_average = total_current / days_elapsed if days_elapsed > 0 else 0
        days_in_month = 30  # Approximate
        projected = daily_average * days_in_month
        st.metric(
            "Projected Month", 
            f"${projected:.2f}",
            help=f"Estimated monthly cost based on {days_elapsed} days of data"
        )
    
    st.markdown("---")
    
    # Service breakdown tabs
    tab1, tab2, tab3 = st.tabs(["Service Breakdown", "Cost Comparison", "Trends & Insights"])
    
    with tab1:
        st.subheader("Current Month Costs by Service")
        
        if cost_data['current_month']:
            # Create DataFrame for better display
            service_costs = []
            for service, cost in sorted(cost_data['current_month'].items(), key=lambda x: x[1], reverse=True):
                percentage = (cost / total_current * 100) if total_current > 0 else 0
                service_costs.append({
                    'Service': service,
                    'Cost': f"${cost:.2f}",
                    'Percentage': f"{percentage:.1f}%"
                })
            
            df = pd.DataFrame(service_costs)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Pie chart
            fig_pie = px.pie(
                values=list(cost_data['current_month'].values()),
                names=list(cost_data['current_month'].keys()),
                title="Cost Distribution by Service"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No cost data available for current month")
    
    with tab2:
        st.subheader("Month-over-Month Comparison")
        
        # Prepare comparison data
        all_services = set(cost_data['current_month'].keys()) | set(cost_data['previous_month'].keys())
        comparison_data = []
        
        for service in all_services:
            current = cost_data['current_month'].get(service, 0)
            previous = cost_data['previous_month'].get(service, 0)
            change = current - previous
            change_pct = (change / previous * 100) if previous > 0 else (100 if current > 0 else 0)
            
            comparison_data.append({
                'Service': service,
                'Current': current,
                'Previous': previous,
                'Change': change,
                'Change_Pct': change_pct
            })
        
        if comparison_data:
            df_comparison = pd.DataFrame(comparison_data)
            df_comparison = df_comparison.sort_values('Current', ascending=False)
            
            # Bar chart comparison
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name='Current Month',
                x=df_comparison['Service'],
                y=df_comparison['Current'],
                marker_color='lightblue'
            ))
            fig_bar.add_trace(go.Bar(
                name='Previous Month',
                x=df_comparison['Service'],
                y=df_comparison['Previous'],
                marker_color='lightcoral'
            ))
            
            fig_bar.update_layout(
                title='Monthly Cost Comparison by Service',
                xaxis_title='Service',
                yaxis_title='Cost ($)',
                barmode='group'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Detailed comparison table
            display_comparison = []
            for _, row in df_comparison.iterrows():
                display_comparison.append({
                    'Service': row['Service'],
                    'Current': f"${row['Current']:.2f}",
                    'Previous': f"${row['Previous']:.2f}",
                    'Change': f"${row['Change']:+.2f}",
                    'Change %': f"{row['Change_Pct']:+.1f}%"
                })
            
            df_display = pd.DataFrame(display_comparison)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    with tab3:
        st.subheader("Trends & Optimisation Insights")
        
        # Cost efficiency metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **💡 Cost Optimisation Insights:**
            
            🔍 **Top Cost Drivers:**
            """)
            
            # Show top 3 services by cost
            top_services = sorted(cost_data['current_month'].items(), key=lambda x: x[1], reverse=True)[:3]
            for i, (service, cost) in enumerate(top_services, 1):
                percentage = (cost / total_current * 100) if total_current > 0 else 0
                st.write(f"{i}. **{service}**: ${cost:.2f} ({percentage:.1f}%)")
        
        with col2:
            st.markdown("""
            **📈 Growth Analysis:**
            """)
            
            if cost_change_pct > 10:
                st.warning(f"⚠️ Costs increased by {cost_change_pct:.1f}% this month")
            elif cost_change_pct > 0:
                st.info(f"📊 Costs increased by {cost_change_pct:.1f}% this month")
            else:
                st.success(f"✅ Costs decreased by {abs(cost_change_pct):.1f}% this month")
            
            # Daily burn rate
            days_elapsed = datetime.now().day
            daily_rate = total_current / days_elapsed if days_elapsed > 0 else 0
            st.metric("Daily Burn Rate", f"${daily_rate:.2f}")
        
        # Cost predictions and recommendations
        st.markdown("---")
        st.markdown("**🎯 Recommendations:**")
        
        recommendations = []
        
        # Lambda-specific recommendations
        lambda_cost = cost_data['current_month'].get('AWS Lambda', 0)
        if lambda_cost > 5:
            recommendations.append("Consider optimising Lambda memory allocation and execution time")
        
        # API Gateway recommendations
        api_cost = cost_data['current_month'].get('Amazon API Gateway', 0)
        if api_cost > 1:
            recommendations.append("Monitor API Gateway request patterns for optimisation opportunities")
        
        # General recommendations
        if total_current > 10:
            recommendations.append("Set up AWS Budgets and alerts for cost monitoring")
        
        if not recommendations:
            recommendations.append("Costs are well-optimised for current usage patterns")
        
        for rec in recommendations:
            st.write(f"• {rec}")

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
    
    display_cost_analysis()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; colour: #666;'>
        <p>📊 Monitoring Dashboard • Built with Streamlit • AWS CloudWatch Integration</p>
    </div>
    """, unsafe_allow_html=True)