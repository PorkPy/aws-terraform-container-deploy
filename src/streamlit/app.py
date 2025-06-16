import streamlit as st
import requests
import json
import base64
from io import BytesIO
from PIL import Image
import time
import threading

# Import monitoring dashboard
from monitoring_dashboard import main_monitoring

# Page config
st.set_page_config(
    page_title="Transformer Model Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("🤖 Navigation")
page = st.sidebar.selectbox(
    "Choose a page:",
    ["🏠 Main Demo", "🔍 Monitoring Dashboard"]
)

# API Configuration
API_BASE_URL = "https://0fc0dgwg69.execute-api.eu-west-2.amazonaws.com"
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

def main_demo():
    """Main demo application"""
    # Initialize warmup state
    if 'models_ready' not in st.session_state:
        st.session_state.models_ready = False
        st.session_state.warmup_start_time = time.time()
        
        # Start Lambda warmup immediately
        threading.Thread(target=warm_up_lambdas, daemon=True).start()
    
    # Check if enough time has passed for warmup
    if not st.session_state.models_ready:
        elapsed_time = time.time() - st.session_state.warmup_start_time
        
        if elapsed_time >= 30:  # Warmup complete
            st.session_state.models_ready = True
            st.rerun()

    # Always show the main app, but disable buttons if not ready
    st.title("🤖 Transformer Model Demo")
    
    # Show warmup status
    if not st.session_state.models_ready:
        elapsed_time = time.time() - st.session_state.warmup_start_time
        progress = min(elapsed_time / 30, 1.0)
        remaining = max(30 - int(elapsed_time), 0)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.warning(f"⏳ **Models warming up... {remaining} seconds remaining**")
        with col2:
            st.progress(progress)
        
        # Auto-refresh during warmup
        time.sleep(1)
        st.rerun()
    else:
        # Show ready status
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("*Models are running on AWS Lambda with sub-second response times*")
        with col2:
            st.success("🟢 **Models Ready**")
    
    st.markdown("---")
    
    # Create two columns for the different functionalities
    col1, col2 = st.columns(2)
    
    # Determine if buttons should be disabled
    buttons_disabled = not st.session_state.models_ready
    
    # Text Generation Section
    with col1:
        st.header("📝 Text Generation")
        st.markdown("Generate text using a custom transformer model")
        
        prompt = st.text_area(
            "Enter your prompt:", 
            value="The future of artificial intelligence",
            height=100,
            disabled=buttons_disabled
        )
        
        max_length = st.slider(
            "Max length:", 
            min_value=10, 
            max_value=100, 
            value=50,
            disabled=buttons_disabled
        )
        
        # Button with conditional styling and disabled state
        button_text = "⏳ Warming Up..." if buttons_disabled else "🚀 Generate Text"
        
        if st.button(button_text, type="primary", disabled=buttons_disabled):
            if prompt.strip():
                with st.spinner("Generating text..."):
                    start_time = time.time()
                    payload = {"prompt": prompt, "max_length": max_length}
                    result, error = call_api(GENERATE_ENDPOINT, payload)
                    response_time = time.time() - start_time
                    
                    if result:
                        st.subheader("Generated Text:")
                        st.write(result.get("generated_text", "No text generated"))
                        st.caption(f"⚡ Generated in {response_time:.1f}s")
                        
                        if "tokens_generated" in result:
                            st.caption(f"Tokens generated: {result['tokens_generated']}")
                    else:
                        st.error(f"❌ {error}")
            else:
                st.warning("Please enter a prompt")
        
        # Show help text when disabled
        if buttons_disabled:
            st.caption("🔄 Buttons will be enabled once models finish warming up")
    
    # Attention Visualization Section  
    with col2:
        st.header("👁️ Attention Visualization")
        st.markdown("Visualize transformer attention patterns")
        
        text_input = st.text_area(
            "Enter text to analyze:", 
            value="Hello world, this is a test",
            height=100,
            disabled=buttons_disabled
        )
        
        col2a, col2b = st.columns(2)
        with col2a:
            layer = st.selectbox(
                "Layer:", 
                options=list(range(4)), 
                index=0,
                disabled=buttons_disabled
            )
        with col2b:
            head = st.selectbox(
                "Attention Head:", 
                options=list(range(8)), 
                index=0,
                disabled=buttons_disabled
            )
        
        # Button with conditional styling and disabled state
        button_text = "⏳ Warming Up..." if buttons_disabled else "🔍 Visualize Attention"
        
        if st.button(button_text, type="primary", disabled=buttons_disabled, key="viz_button"):
            if text_input.strip():
                with st.spinner("Creating attention visualization..."):
                    start_time = time.time()
                    payload = {"text": text_input, "layer": layer, "head": head}
                    result, error = call_api(VISUALIZE_ENDPOINT, payload)
                    response_time = time.time() - start_time
                    
                    if result and result.get("attention_image"):
                        st.subheader("Attention Heatmap:")
                        
                        try:
                            # Decode base64 image
                            image_data = base64.b64decode(result["attention_image"])
                            image = Image.open(BytesIO(image_data))
                            
                            # Display image with response time
                            st.image(image, use_container_width=True)
                            st.caption(f"⚡ Visualization created in {response_time:.1f}s")
                            
                            if "tokens" in result:
                                st.caption(f"Analyzed tokens: {result['tokens']}")
                                
                        except Exception as e:
                            st.error(f"Error displaying image: {str(e)}")
                    else:
                        st.error(f"❌ {error or 'No visualization generated'}")
            else:
                st.warning("Please enter text to analyze")
        
        # Show help text when disabled
        if buttons_disabled:
            st.caption("🔄 Buttons will be enabled once models finish warming up")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Built with Streamlit • Models hosted on AWS Lambda • Infrastructure managed with Terraform</p>
    </div>
    """, unsafe_allow_html=True)

# Main app logic
if page == "🏠 Main Demo":
    main_demo()
elif page == "🔍 Monitoring Dashboard":
    main_monitoring()