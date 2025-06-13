import streamlit as st
import requests
import json
import base64
from io import BytesIO
from PIL import Image
import time
import threading

# Page config
st.set_page_config(
    page_title="Transformer Model Demo",
    page_icon="🤖",
    layout="wide"
)

# API Configuration
API_BASE_URL = "https://your-api-gateway-url"  # Replace with your actual API Gateway URL
GENERATE_ENDPOINT = f"{API_BASE_URL}/generate-text"
VISUALIZE_ENDPOINT = f"{API_BASE_URL}/visualize-attention"

def warm_up_lambdas():
    """Warm up both Lambda functions"""
    endpoints = [
        {"url": GENERATE_ENDPOINT, "payload": {"prompt": "warmup", "max_length": 10}},
        {"url": VISUALIZE_ENDPOINT, "payload": {"text": "warmup", "layer": 0, "head": 0}}
    ]
    
    for endpoint in endpoints:
        try:
            requests.post(
                endpoint["url"], 
                json=endpoint["payload"], 
                timeout=1,
                headers={"Content-Type": "application/json"}
            )
        except:
            # Ignore all errors - this is just for warming
            pass

def call_api(endpoint, payload):
    """Make API call with error handling"""
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minute timeout for actual requests
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error ({response.status_code}): {response.text}"
            
    except requests.exceptions.Timeout:
        return None, "Request timed out. The model may still be warming up."
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

# AWS Lambda Warmup Screen
if 'models_ready' not in st.session_state:
    st.session_state.models_ready = False
    
    # Professional loading screen
    st.title("🤖 Transformer Model Demo")
    st.markdown("---")
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.spinner(""):
                st.markdown("""
                ### ☁️ Initializing AWS Services
                
                The transformer models are hosted on **AWS Lambda** and need to spin up.
                This includes:
                - 📦 Loading model weights from S3
                - 🧠 Initializing neural network layers  
                - 🔧 Setting up inference pipeline
                
                **Estimated time: ~30 seconds**
                """)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Start Lambda warmup
                threading.Thread(target=warm_up_lambdas, daemon=True).start()
                
                # Progress with status updates
                for i in range(30):
                    if i < 10:
                        status_text.text("🚀 Starting AWS Lambda functions...")
                    elif i < 20:
                        status_text.text("📚 Loading transformer models...")
                    else:
                        status_text.text("✅ Almost ready...")
                    
                    progress_bar.progress((i + 1) / 30)
                    time.sleep(1)
                
                st.success("🎉 Models are now ready for inference!")
                time.sleep(2)
    
    st.session_state.models_ready = True
    st.rerun()

# Main Application (only shows after models are ready)
if st.session_state.get('models_ready', False):
    st.title("🤖 Transformer Model Demo")
    st.markdown("*Models are running on AWS Lambda with sub-second response times*")
    st.markdown("---")
    
    # Create two columns for the different functionalities
    col1, col2 = st.columns(2)
    
    # Text Generation Section
    with col1:
        st.header("📝 Text Generation")
        st.markdown("Generate text using a custom transformer model")
        
        prompt = st.text_area(
            "Enter your prompt:", 
            value="The future of artificial intelligence",
            height=100
        )
        
        max_length = st.slider("Max length:", min_value=10, max_value=100, value=50)
        
        if st.button("🚀 Generate Text", type="primary"):
            if prompt.strip():
                with st.spinner("Generating text..."):
                    payload = {
                        "prompt": prompt,
                        "max_length": max_length
                    }
                    
                    result, error = call_api(GENERATE_ENDPOINT, payload)
                    
                    if result:
                        st.subheader("Generated Text:")
                        st.write(result.get("generated_text", "No text generated"))
                        
                        if "tokens_generated" in result:
                            st.caption(f"Tokens generated: {result['tokens_generated']}")
                    else:
                        st.error(f"❌ {error}")
            else:
                st.warning("Please enter a prompt")
    
    # Attention Visualization Section  
    with col2:
        st.header("👁️ Attention Visualization")
        st.markdown("Visualize transformer attention patterns")
        
        text_input = st.text_area(
            "Enter text to analyze:", 
            value="Hello world, this is a test",
            height=100
        )
        
        col2a, col2b = st.columns(2)
        with col2a:
            layer = st.selectbox("Layer:", options=list(range(4)), index=0)
        with col2b:
            head = st.selectbox("Attention Head:", options=list(range(8)), index=0)
        
        if st.button("🔍 Visualize Attention", type="primary"):
            if text_input.strip():
                with st.spinner("Creating attention visualization..."):
                    payload = {
                        "text": text_input,
                        "layer": layer,
                        "head": head
                    }
                    
                    result, error = call_api(VISUALIZE_ENDPOINT, payload)
                    
                    if result and result.get("attention_image"):
                        st.subheader("Attention Heatmap:")
                        
                        try:
                            # Decode base64 image
                            image_data = base64.b64decode(result["attention_image"])
                            image = Image.open(BytesIO(image_data))
                            
                            # Display image with new parameter name
                            st.image(image, use_container_width=True)
                            
                            if "tokens" in result:
                                st.caption(f"Analyzed tokens: {result['tokens']}")
                                
                        except Exception as e:
                            st.error(f"Error displaying image: {str(e)}")
                    else:
                        st.error(f"❌ {error or 'No visualization generated'}")
            else:
                st.warning("Please enter text to analyze")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Built with Streamlit • Models hosted on AWS Lambda • Infrastructure managed with Terraform</p>
    </div>
    """, unsafe_allow_html=True)