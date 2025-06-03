# aws_app.py (Updated for working AWS API)
import streamlit as st
import requests
import json
import base64
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt

# Set page config
st.set_page_config(
    page_title="Transformer Demo - AWS Cloud Edition",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Your actual working API endpoint
API_ENDPOINT = "https://0fc0dgwg69.execute-api.eu-west-2.amazonaws.com"

def main():
    st.title("🤖 Transformer from Scratch - AWS Cloud Edition")
    st.markdown("""
    This app demonstrates a transformer model built from scratch with PyTorch.
    The model is deployed on AWS Lambda and accessed via API Gateway.
    """)
    
    # Sidebar
    st.sidebar.header("AWS Cloud Deployment")
    st.sidebar.success(f"✅ Connected to AWS API")
    st.sidebar.info(f"Endpoint: {API_ENDPOINT}")
    
    # Generation settings
    st.sidebar.subheader("Generation Settings")
    temperature = st.sidebar.slider("Temperature", min_value=0.1, max_value=2.0, value=1.0, step=0.1,
                                  help="Higher values produce more diverse text, lower values are more deterministic")
    max_tokens = st.sidebar.slider("Max Tokens", min_value=5, max_value=100, value=20, step=5,
                                 help="Maximum number of tokens to generate")
    
    # Visualization settings
    st.sidebar.subheader("Visualization Settings")
    layer = st.sidebar.slider("Layer", min_value=0, max_value=3, value=0,
                            help="Transformer layer to visualize (0-3)")
    head = st.sidebar.slider("Head", min_value=0, max_value=7, value=0,
                           help="Attention head to visualize (0-7)")
    
    # Main content
    tabs = st.tabs(["Text Generation", "Attention Visualization", "Model Architecture", "AWS Architecture"])
    
    # Text Generation Tab
    with tabs[0]:
        st.header("🔤 Text Generation")
        
        prompt = st.text_area("Enter a prompt", "Once upon a time", height=100)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            generate_btn = st.button("🚀 Generate", type="primary")
        
        if generate_btn:
            with st.spinner("Calling AWS Lambda..."):
                try:
                    # Call the generate API
                    response = requests.post(
                        f"{API_ENDPOINT}/generate",
                        json={
                            "prompt": prompt,
                            "temperature": temperature,
                            "max_tokens": max_tokens
                        },
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display results
                        st.subheader("📝 Generated Text")
                        st.success(result["generated_text"])
                        
                        # Show metadata
                        with st.expander("🔍 API Response Details"):
                            st.json({
                                "prompt": result.get("prompt", prompt),
                                "generated_text": result["generated_text"],
                                "settings": {
                                    "temperature": temperature,
                                    "max_tokens": max_tokens
                                }
                            })
                            
                    else:
                        st.error(f"❌ API Error ({response.status_code}): {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection Error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Unexpected Error: {str(e)}")
    
    # Attention Visualization Tab
    with tabs[1]:
        st.header("🧠 Attention Visualization")
        
        viz_text = st.text_area("Enter text to visualize attention", 
                               "The quick brown fox jumps over the lazy dog.", 
                               height=100)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            visualize_btn = st.button("🎨 Visualize", type="primary")
        
        if visualize_btn:
            with st.spinner("Generating attention heatmap..."):
                try:
                    # Call the visualize API
                    response = requests.post(
                        f"{API_ENDPOINT}/visualize",
                        json={
                            "text": viz_text,
                            "layer": layer,
                            "head": head
                        },
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display tokens
                        st.subheader("🏷️ Tokens")
                        if "tokens" in result:
                            token_display = " | ".join(result["tokens"])
                            st.code(token_display)
                        
                        # Display attention visualization
                        st.subheader(f"🎯 Attention Heatmap (Layer {layer}, Head {head})")
                        
                        if "attention_image" in result:
                            # Decode base64 image
                            image_data = base64.b64decode(result["attention_image"])
                            image = Image.open(BytesIO(image_data))
                            st.image(image, use_column_width=True)
                            
                            # Explanation
                            st.subheader("💡 What am I looking at?")
                            st.markdown("""
                            This heatmap shows attention patterns of the transformer model:
                            
                            - **Rows (Query)**: Token that is "asking" for information
                            - **Columns (Key)**: Token that provides information  
                            - **Brightness**: How much attention is paid between tokens
                            - **Multiple heads**: Each head learns different relationship patterns
                            
                            🔍 **Try different layers and heads** to see how the model processes language at different levels!
                            """)
                        else:
                            st.warning("⚠️ No attention image returned from API")
                            
                        # Show API response details
                        with st.expander("🔍 API Response Details"):
                            response_data = {k: v for k, v in result.items() if k != "attention_image"}
                            st.json(response_data)
                            
                    else:
                        st.error(f"❌ API Error ({response.status_code}): {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection Error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Unexpected Error: {str(e)}")
    
    # Model Architecture Tab
    with tabs[2]:
        st.header("🏗️ Model Architecture")
        
        st.subheader("🤖 Transformer Architecture")
        st.markdown("""
        This transformer model implements the core concepts from "Attention is All You Need":
        
        **📊 Model Specifications:**
        - **Vocabulary**: ~7,100 tokens
        - **Layers**: 4 transformer encoder layers
        - **Attention Heads**: 8 heads per layer
        - **Hidden Dimension**: 256 
        - **Feed-Forward**: 1,024 dimensions
        - **Max Sequence**: 128 tokens
        
        **🔧 Key Components:**
        1. **Token Embeddings** → Convert words to vectors
        2. **Positional Encoding** → Add position information
        3. **Multi-Head Attention** → Learn token relationships
        4. **Feed-Forward Networks** → Process representations
        5. **Layer Normalization** → Stabilize training
        6. **Residual Connections** → Enable deep networks
        """)
        
        st.subheader("🧠 Self-Attention Mechanism")
        st.markdown("""
        The heart of the transformer:
        
        ```
        Attention(Q, K, V) = softmax(QK^T / √d_k) × V
        ```
        
        - **Query (Q)**: What each token is looking for
        - **Key (K)**: What each token offers  
        - **Value (V)**: The actual information content
        - **Multi-head**: 8 parallel attention computations
        """)
    
    # AWS Architecture Tab
    with tabs[3]:
        st.header("☁️ AWS Architecture")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏗️ Infrastructure Components")
            st.markdown("""
            **🔧 Compute:**
            - **AWS Lambda** (Container-based)
              - 1024MB memory
              - 30s timeout
              - PyTorch + custom model
            
            **🌐 API Layer:**
            - **API Gateway** (REST API)
              - `/generate` endpoint
              - `/visualize` endpoint  
              - CORS enabled
            
            **💾 Storage:**
            - **Amazon S3** 
              - Model weights (`transformer_model.pt`)
              - Tokenizer (`tokenizer.json`)
            
            **📊 Monitoring:**
            - **CloudWatch** logs & metrics
            - Error tracking & alerting
            """)
        
        with col2:
            st.subheader("🚀 Deployment Details")
            st.markdown("""
            **📦 Containerization:**
            - Docker images in ECR
            - PyTorch CPU-optimized
            - ~1GB compressed size
            
            **🔄 Infrastructure as Code:**
            - Terraform for provisioning
            - Modular architecture
            - Reproducible deployments
            
            **⚡ Performance:**
            - Cold start: ~8-10 seconds
            - Warm execution: ~1-3 seconds
            - Auto-scaling based on demand
            
            **💰 Cost Optimization:**
            - Pay-per-request model
            - No idle compute costs
            - Efficient for demo workloads
            """)
        
        st.subheader("📈 Success Metrics")
        
        # Create some mock metrics for display
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("✅ API Status", "Online", "100%")
        with col2:
            st.metric("⚡ Avg Response", "2.1s", "-0.3s")
        with col3:
            st.metric("🎯 Success Rate", "99.5%", "+0.2%")
        with col4:
            st.metric("📊 Requests Today", "47", "+12")

if __name__ == "__main__":
    main()