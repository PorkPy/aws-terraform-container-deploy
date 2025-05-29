# src/streamlit/app.py
import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_ENDPOINT = os.getenv('API_ENDPOINT')

def transformer_demo_page():
    st.title("Transformer Model Demo")
    st.markdown("This demo is powered by a transformer model deployed on AWS using Terraform")
    
    # Model parameters
    prompt = st.text_area("Enter prompt:", "Once upon a time")
    
    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider("Temperature", 0.1, 2.0, 1.0, 0.1)
    with col2:
        max_tokens = st.slider("Max tokens to generate", 10, 100, 50, 5)
    
    if st.button("Generate Text"):
        with st.spinner("Generating..."):
            try:
                # Call API
                response = requests.post(
                    f"{API_ENDPOINT}/generate",
                    json={
                        "prompt": prompt,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display generated text
                    st.subheader("Generated Text")
                    st.text_area("Output:", result["generated_text"], height=150)
                    
                    # Get visualization
                    viz_response = requests.post(
                        f"{API_ENDPOINT}/visualize",
                        json={"prompt": prompt}
                    )
                    
                    if viz_response.status_code == 200:
                        viz_result = viz_response.json()
                        
                        # Display attention visualization
                        st.subheader("Attention Visualization")
                        st.image(viz_result["visualization_url"])
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # AWS architecture explanation
    with st.expander("AWS Architecture"):
        st.image("assets/aws_architecture.png")
        st.markdown("""
        This demo uses a complete AWS architecture deployed with Terraform:
        
        1. **AWS Lambda** functions process your text generation requests
        2. **API Gateway** provides secure HTTP endpoints
        3. **Amazon S3** stores the model weights and visualizations
        4. **CloudWatch** monitors performance and costs
        5. **IAM** manages secure access between services
        
        The entire infrastructure is defined as code using Terraform, demonstrating 
        a production-ready MLOps approach.
        """)