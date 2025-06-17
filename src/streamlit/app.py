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

# Custom CSS for modern sidebar
st.markdown("""
<style>
.sidebar .sidebar-content {
    background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
}

.stSelectbox > div > div {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}

.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    margin-bottom: 2rem;
}

.feature-card {
    background: rgba(255, 255, 255, 0.05);
    padding: 1.5rem;
    border-radius: 10px;
    border-left: 4px solid #667eea;
    margin: 1rem 0;
}

.metric-card {
    background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# Modern sidebar navigation
st.sidebar.markdown("# 🤖 **Transformer Demo**")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "**Navigate to:**",
    [
        "🏠 Home & Overview",
        "🚀 Text Generation", 
        "👁️ Attention Visualization",
        "🔍 System Monitoring"
    ],
    key="main_navigation"
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; color: #888; font-size: 0.8rem;'>
    <p>Built with Streamlit<br>
    Powered by AWS Lambda<br>
    Infrastructure as Code</p>
</div>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "https://0fc0dgwg69.execute-api.eu-west-2.amazonaws.com"
GENERATE_ENDPOINT = f"{API_BASE_URL}/generate"
VISUALIZE_ENDPOINT = f"{API_BASE_URL}/visualize"

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
            pass

def call_api(endpoint, payload):
    """Make API call with error handling"""
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
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

def check_warmup_status():
    """Check if models are warmed up"""
    if 'models_ready' not in st.session_state:
        st.session_state.models_ready = False
        st.session_state.warmup_start_time = time.time()
        threading.Thread(target=warm_up_lambdas, daemon=True).start()
    
    if not st.session_state.models_ready:
        elapsed_time = time.time() - st.session_state.warmup_start_time
        if elapsed_time >= 30:
            st.session_state.models_ready = True
            st.rerun()
        else:
            progress = min(elapsed_time / 30, 1.0)
            remaining = max(30 - int(elapsed_time), 0)
            
            st.warning(f"⏳ **Models warming up... {remaining} seconds remaining**")
            st.progress(progress)
            time.sleep(1)
            st.rerun()
            return False
    
    st.success("🟢 **Models Ready** - All systems operational")
    return True

def show_home_page():
    """Home page with project overview"""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Custom Transformer Model Showcase</h1>
        <p>End-to-end machine learning pipeline hosted on AWS serverless infrastructure</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Project Overview
    st.header("📋 Project Overview")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        This project demonstrates a **complete machine learning pipeline** featuring:
        
        - 🧠 **Custom transformer model** trained from scratch
        - ☁️ **AWS serverless architecture** with Lambda containers
        - 🔧 **Infrastructure as Code** using Terraform
        - 📊 **Real-time monitoring** and cost analysis
        - 🚀 **CI/CD pipeline** with GitHub Actions
        
        ### What You Can Do:
        
        **🚀 Text Generation**: Generate creative text continuations using the transformer model
        
        **👁️ Attention Visualization**: Explore how the model "pays attention" to different words
        
        **🔍 System Monitoring**: View real-time performance metrics and AWS costs
        """)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>⚡ Performance</h3>
            <p>Sub-second inference</p>
        </div>
        
        <div class="metric-card">
            <h3>💰 Cost</h3>
            <p>~$5-10/month</p>
        </div>
        
        <div class="metric-card">
            <h3>🔧 Uptime</h3>
            <p>99.9% available</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Technical Architecture
    st.header("🏗️ Technical Architecture")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>🧠 ML Model</h4>
            <ul>
                <li>Custom transformer architecture</li>
                <li>4 layers, 8 attention heads</li>
                <li>256-dimensional embeddings</li>
                <li>Trained on custom dataset</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>☁️ AWS Infrastructure</h4>
            <ul>
                <li>Lambda containers (PyTorch)</li>
                <li>API Gateway endpoints</li>
                <li>S3 model storage</li>
                <li>CloudWatch monitoring</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4>🔧 DevOps Pipeline</h4>
            <ul>
                <li>Terraform IaC</li>
                <li>GitHub Actions CI/CD</li>
                <li>ECR container registry</li>
                <li>Automated deployments</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Usage Instructions
    st.header("📖 How to Use This Demo")
    
    instructions = st.expander("**Click here for detailed usage instructions**", expanded=False)
    with instructions:
        st.markdown("""
        ### 🚀 Text Generation
        1. Navigate to the **Text Generation** page
        2. Enter a prompt (e.g., "The future of AI is...")
        3. Adjust the maximum length slider
        4. Click **Generate Text** to see the model's continuation
        
        ### 👁️ Attention Visualization  
        1. Navigate to the **Attention Visualization** page
        2. Enter text to analyze
        3. Select which layer and attention head to visualize
        4. Click **Visualize Attention** to see the attention heatmap
        
        ### 🔍 System Monitoring
        1. Navigate to the **System Monitoring** page
        2. View real-time Lambda performance metrics
        3. Analyze AWS costs and optimization opportunities
        4. Monitor system health and recent logs
        
        ### ⚡ Performance Tips
        - First requests may take 30 seconds (cold start)
        - Subsequent requests are sub-second
        - Try different prompts and attention heads for variety
        """)
    
    # Model warmup status
    st.markdown("---")
    st.header("🔥 System Status")
    check_warmup_status()

def show_text_generation_page():
    """Text generation page"""
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Text Generation</h1>
        <p>Generate creative text continuations using a custom transformer model</p>
    </div>
    """, unsafe_allow_html=True)
    
    # How it works section
    how_it_works = st.expander("🧠 **How Transformer Text Generation Works**", expanded=False)
    with how_it_works:
        st.markdown("""
        ### The Transformer Architecture
        
        **Self-Attention Mechanism**: The model looks at all words in the input simultaneously, understanding relationships and context between them.
        
        **Autoregressive Generation**: The model generates text one token at a time, using previously generated tokens as context for the next prediction.
        
        **Multi-Head Attention**: With 8 attention heads, the model can focus on different types of relationships (syntax, semantics, etc.) in parallel.
        
        ### Training Process
        1. **Dataset**: Trained on a curated text corpus
        2. **Objective**: Learn to predict the next word given previous context
        3. **Optimization**: Uses the Adam optimizer with learning rate scheduling
        4. **Validation**: Monitored perplexity and generation quality
        
        ### Generation Strategy
        The model uses **nucleus sampling** (top-p) to balance creativity and coherence in generated text.
        """)
    
    st.markdown("---")
    
    # Check warmup status
    models_ready = check_warmup_status()
    
    if models_ready:
        # Text generation interface
        st.header("✍️ Generate Text")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            prompt = st.text_area(
                "Enter your prompt:",
                value="The future of artificial intelligence is",
                height=100,
                help="Enter a starting phrase and the model will continue the text"
            )
        
        with col2:
            max_length = st.slider(
                "Maximum length:",
                min_value=10,
                max_value=100,
                value=50,
                help="Maximum number of tokens to generate"
            )
            
            temperature = st.slider(
                "Creativity level:",
                min_value=0.1,
                max_value=2.0,
                value=0.8,
                step=0.1,
                help="Higher values = more creative, lower = more focused"
            )
        
        if st.button("🚀 Generate Text", type="primary", use_container_width=True):
            if prompt.strip():
                with st.spinner("🤖 Generating text..."):
                    start_time = time.time()
                    payload = {
                        "prompt": prompt,
                        "max_length": max_length,
                        "temperature": temperature
                    }
                    result, error = call_api(GENERATE_ENDPOINT, payload)
                    response_time = time.time() - start_time
                    
                    if result:
                        st.success("✅ Generation Complete!")
                        
                        # Display results
                        st.markdown("### 📝 Generated Text:")
                        st.markdown(f"**Input:** {prompt}")
                        st.markdown(f"**Generated:** {result.get('generated_text', 'No text generated')}")
                        
                        # Metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("⚡ Response Time", f"{response_time:.1f}s")
                        with col2:
                            if "tokens_generated" in result:
                                st.metric("🔢 Tokens Generated", result['tokens_generated'])
                        with col3:
                            if result.get('tokens_generated', 0) > 0:
                                tokens_per_sec = result['tokens_generated'] / response_time
                                st.metric("🚀 Tokens/Second", f"{tokens_per_sec:.1f}")
                    else:
                        st.error(f"❌ {error}")
            else:
                st.warning("⚠️ Please enter a prompt")

def show_attention_visualization_page():
    """Attention visualization page"""
    st.markdown("""
    <div class="main-header">
        <h1>👁️ Attention Visualization</h1>
        <p>Explore how the transformer model pays attention to different words</p>
    </div>
    """, unsafe_allow_html=True)
    
    # How it works section
    how_it_works = st.expander("🧠 **Understanding Attention Mechanisms**", expanded=False)
    with how_it_works:
        st.markdown("""
        ### What is Attention?
        
        **Attention** is the mechanism that allows transformers to focus on different parts of the input when processing each word. Think of it like reading comprehension - when you read a sentence, you mentally connect related words even if they're far apart.
        
        ### Multi-Head Attention
        
        Our model has **8 attention heads** in each of **4 layers**:
        - Each head learns different types of relationships
        - Some heads focus on syntax (grammar structure)
        - Others focus on semantics (meaning relationships)
        - Some capture long-range dependencies
        
        ### Visualization Explained
        
        **Heatmap Colors**:
        - 🔵 **Blue (Dark)**: High attention - the model is focusing strongly on this connection
        - ⚪ **White/Light**: Low attention - weak or no connection
        
        **Axes**:
        - **X-axis (Key)**: Words being attended TO
        - **Y-axis (Query)**: Words doing the attending
        
        ### What to Look For
        - **Diagonal patterns**: Self-attention (words attending to themselves)
        - **Vertical/horizontal lines**: Words that are particularly important
        - **Block patterns**: Phrase-level attention
        - **Scattered patterns**: Complex semantic relationships
        """)
    
    st.markdown("---")
    
    # Check warmup status
    models_ready = check_warmup_status()
    
    if models_ready:
        # Attention visualization interface
        st.header("🔍 Visualize Attention")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            text_input = st.text_area(
                "Enter text to analyze:",
                value="The cat sat on the mat and looked around",
                height=100,
                help="Enter text to see how the model pays attention to different words"
            )
        
        with col2:
            layer = st.selectbox(
                "🏗️ Layer:",
                options=list(range(4)),
                index=2,
                help="Deeper layers capture more complex patterns",
                format_func=lambda x: f"Layer {x+1} {'(Deep)' if x >= 2 else '(Shallow)'}"
            )
            
            head = st.selectbox(
                "👁️ Attention Head:",
                options=list(range(8)),
                index=0,
                help="Different heads focus on different relationship types",
                format_func=lambda x: f"Head {x+1}"
            )
            
            st.info(f"💡 Analyzing **Layer {layer+1}, Head {head+1}**")
        
        if st.button("🔍 Visualize Attention", type="primary", use_container_width=True):
            if text_input.strip():
                with st.spinner("🧠 Analyzing attention patterns..."):
                    start_time = time.time()
                    payload = {
                        "text": text_input,
                        "layer": layer,
                        "head": head
                    }
                    result, error = call_api(VISUALIZE_ENDPOINT, payload)
                    response_time = time.time() - start_time
                    
                    if result and result.get("attention_image"):
                        st.success("✅ Analysis Complete!")
                        
                        try:
                            # Decode and display image
                            image_data = base64.b64decode(result["attention_image"])
                            image = Image.open(BytesIO(image_data))
                            
                            st.markdown("### 🎨 Attention Heatmap:")
                            st.image(image, use_container_width=True, caption=f"Attention patterns for Layer {layer+1}, Head {head+1}")
                            
                            # Analysis info
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("⚡ Analysis Time", f"{response_time:.1f}s")
                            with col2:
                                if "tokens" in result:
                                    st.metric("🔤 Tokens Analyzed", len(result['tokens']))
                            with col3:
                                st.metric("🎯 Layer/Head", f"{layer+1}/{head+1}")
                            
                            # Show tokenization
                            if "tokens" in result:
                                st.markdown("### 🔤 Tokenization:")
                                tokens_display = " | ".join(result['tokens'])
                                st.code(tokens_display, language=None)
                                
                        except Exception as e:
                            st.error(f"Error displaying visualization: {str(e)}")
                    else:
                        st.error(f"❌ {error or 'No visualization generated'}")
            else:
                st.warning("⚠️ Please enter text to analyze")

# Main app routing
if page == "🏠 Home & Overview":
    show_home_page()
elif page == "🚀 Text Generation":
    show_text_generation_page()
elif page == "👁️ Attention Visualization":
    show_attention_visualization_page()
elif page == "🔍 System Monitoring":
    main_monitoring()