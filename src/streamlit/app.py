# aws_app.py (Cloud-compatible version)
import streamlit as st
import requests
import json
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

# Load environment variables (API_ENDPOINT)
load_dotenv()
API_ENDPOINT = os.getenv('API_ENDPOINT', 'http://localhost:8000')  # Default for local testing

# Set page config
st.set_page_config(
    page_title="Transformer Demo - Cloud Version",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🤖 Transformer from Scratch - Cloud Edition")
    st.markdown("""
    This app demonstrates a transformer model built from scratch with PyTorch.
    The model is hosted on AWS Lambda and accessed via API Gateway.
    """)
    
    # Sidebar
    st.sidebar.header("AWS Cloud Deployment")
    st.sidebar.success(f"Connected to API: {API_ENDPOINT}")
    
    # Generation settings
    st.sidebar.subheader("Generation Settings")
    temperature = st.sidebar.slider("Temperature", min_value=0.1, max_value=2.0, value=1.0, step=0.1,
                                  help="Higher values produce more diverse text, lower values are more deterministic")
    top_k = st.sidebar.slider("Top-k", min_value=1, max_value=100, value=50, step=1,
                            help="Sample from top k most probable tokens")
    max_tokens = st.sidebar.slider("Max Tokens", min_value=10, max_value=100, value=50, step=10,
                                 help="Maximum number of tokens to generate")
    
    # Main content
    tabs = st.tabs(["Text Generation", "Attention Visualization", "Model Architecture", "AWS Architecture"])
    
    # Text Generation Tab
    with tabs[0]:
        st.header("Text Generation")
        
        prompt = st.text_area("Enter a prompt", "Once upon a time", height=100)
        
        if st.button("Generate"):
            with st.spinner("Generating text..."):
                try:
                    # Call the API
                    response = requests.post(
                        f"{API_ENDPOINT}/generate",
                        json={
                            "prompt": prompt,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "top_k": top_k
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display generated text
                        st.subheader("Generated Text")
                        st.write(result["generated_text"])
                    else:
                        st.error(f"Error from API: {response.text}")
                except Exception as e:
                    st.error(f"Error connecting to API: {str(e)}")
    
    # Attention Visualization Tab
    with tabs[1]:
        st.header("Attention Visualization")
        
        viz_text = st.text_area("Enter text to visualize attention", "The quick brown fox jumps over the lazy dog.", height=100)
        
        if st.button("Visualize Attention"):
            with st.spinner("Generating attention visualization..."):
                try:
                    # Call the API
                    response = requests.post(
                        f"{API_ENDPOINT}/visualize",
                        json={
                            "text": viz_text
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display tokens
                        st.subheader("Tokens")
                        st.write(" ".join(result["tokens"]))
                        
                        # Display visualization
                        st.subheader("Attention Patterns")
                        st.image(result["visualization_url"])
                        
                        # Explanation
                        st.subheader("What am I looking at?")
                        st.markdown("""
                        These heatmaps show the attention patterns of the transformer model. Each cell represents how much 
                        a token (row) attends to another token (column) when processing the input. Brighter colors indicate 
                        stronger attention weights.
                        
                        - **Multiple heads**: Transformers use multiple attention heads in parallel, each potentially focusing on different aspects of the relationships between tokens.
                        - **Layers**: The model has multiple layers, with each layer's attention building on the previous layer's representations.
                        """)
                    else:
                        st.error(f"Error from API: {response.text}")
                except Exception as e:
                    st.error(f"Error connecting to API: {str(e)}")
    
    # Model Architecture Tab
    with tabs[2]:
        st.header("Model Architecture")
        
        st.subheader("Transformer Architecture")
        st.markdown("""
        This demo implements a simplified transformer model as described in the paper "Attention is All You Need" by Vaswani et al.
        
        Key components:
        
        1. **Token Embeddings**: Convert tokens to vectors
        2. **Positional Encoding**: Add position information
        3. **Multi-Head Attention**: Process relationships between tokens
           - Multiple attention heads learn different relationship patterns
           - Each head uses scaled dot-product attention
        4. **Feed-Forward Networks**: Process token representations
        5. **Layer Normalization**: Stabilize learning
        6. **Residual Connections**: Help with gradient flow
        
        The model for this demo includes:
        - 4 transformer encoder layers
        - 8 attention heads per layer
        - 256-dimensional embeddings
        - 1024-dimensional feed-forward networks
        """)
    
    # AWS Architecture Tab
    with tabs[3]:
        st.header("AWS Architecture")
        
        st.markdown("""
        This demo is deployed using a serverless architecture on AWS:
        
        1. **AWS Lambda** - Runs the transformer model for inference
           - Handles text generation and attention visualization
           - Automatically scales based on usage
        
        2. **API Gateway** - Provides HTTP endpoints to access the model
           - RESTful API with JSON request/response
           - Handles authentication and rate limiting
        
        3. **Amazon S3** - Stores model artifacts and visualizations
           - Model weights and tokenizer
           - Generated attention visualizations
        
        4. **CloudWatch** - Monitors performance and logs
           - Tracks Lambda execution metrics
           - Stores logs for debugging
        
        The entire infrastructure is defined as code using Terraform, demonstrating a complete MLOps approach.
        """)
        
        # Display architecture diagram
        st.image("https://raw.githubusercontent.com/yourusername/your-repo/main/assets/aws_architecture.png", 
                 caption="AWS Architecture Diagram")

if __name__ == "__main__":
    main()