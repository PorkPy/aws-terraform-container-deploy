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
    page_title="End-to-End Machine Learning Deployment — From Code to Live Production System",
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

.nav-button {
    display: block;
    width: 100%;
    padding: 0.75rem 1rem;
    margin: 0.25rem 0;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 8px;
    color: white;
    text-align: left;
    cursor: pointer;
    transition: all 0.3s ease;
}

.nav-button:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateX(5px);
}

.nav-button.active {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Modern sidebar navigation with buttons
st.sidebar.markdown("# **Custom ML Production**")
st.sidebar.markdown("---")

# Initialize session state for navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home & Overview"

# Navigation buttons
nav_options = [
    "Home & Overview",
    "Text Generation", 
    "Attention Visualisation",
    "System Monitoring"
]

st.sidebar.markdown("**Navigate to:**")
for option in nav_options:
    button_class = "nav-button active" if st.session_state.current_page == option else "nav-button"
    if st.sidebar.button(option, key=f"nav_{option}", use_container_width=True):
        st.session_state.current_page = option
        st.rerun()

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
VISUALISE_ENDPOINT = f"{API_BASE_URL}/visualize"

# S3 URLs for diagrams
ASSETS_BASE_URL = "https://transformer-model-artifacts-q3ukv7.s3.eu-west-2.amazonaws.com/static-assets/"

def warm_up_lambdas():
    """Warm up both Lambda functions"""
    endpoints = [
        {"url": GENERATE_ENDPOINT, "payload": {"prompt": "warmup", "max_length": 10}},
        {"url": VISUALISE_ENDPOINT, "payload": {"text": "warmup", "layer": 0, "head": 0}}
    ]
    
    for endpoint in endpoints:
        try:
            requests.post(
                endpoint["url"], 
                json=endpoint["payload"], 
                timeout=1,
                headers={"Content-Type": "application/json"}
            )
        except Exception:
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
        <h1>Custom ML Model Productionisation</h1>
        <p>Automated CI/CD pipeline · AWS serverless infrastructure · Terraform IaC · PyTorch transformer model</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Project Overview
    st.header("Project Overview")
    
    st.markdown("""
    This project is a deliberate showcase of production ML engineering, not model quality. The transformer language model at its core is intentionally simple — 
    built from scratch in pure PyTorch and trained only on Jane Austen's Pride and Prejudice — because keeping the model lightweight and transparent puts the 
    focus entirely where it belongs: on the deployment pipeline, infrastructure automation, performance monitoring, and cost analysis that make up real-world ML engineering.
    The same infrastructure would deploy any model. The point is that it's genuinely running in production — on AWS Lambda, behind API Gateway, provisioned by 
    Terraform, deployed automatically via GitHub Actions CI/CD, and monitored in real time through CloudWatch
        
       **What this demonstrates:**
    - **Production deployment** — containerised PyTorch model on AWS Lambda behind API Gateway
    - **Infrastructure as Code** — full Terraform provisioning, reproducible and version controlled  
    - **CI/CD automation** — code push to live deployment via GitHub Actions, no manual steps
    - **Observability** — real-time CloudWatch metrics for latency, cost, and errors surfaced in the app
    - **ML fundamentals** — transformer architecture, attention mechanisms, and training loops built from scratch in PyTorch
    """)
    
    # Architecture Diagrams
    st.header("System Architecture")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Complete System Overview")
        st.image(f"{ASSETS_BASE_URL}arch_aws_full_system_overview.png", 
                 caption="Runtime ML pipeline and CI/CD deployment pipeline on AWS serverless infrastructure",
                 use_container_width=True)
        
        st.markdown("""
        **What you're seeing:** End-to-end system architecture showing how the Streamlit app 
        connects through API Gateway to Lambda containers, with S3 storage and monitoring. 
        Perfect for understanding the complete production infrastructure.
        """)

    with col2:
        st.image(f"{ASSETS_BASE_URL}model_transformer_architecture.png", 
                caption="4-layer encoder-only transformer architecture trained on Pride and Prejudice",
                use_container_width=True)
                
        st.markdown("""
        **What you're seeing:** Transformer architecture — a 4-layer encoder-only model 
        with 256-dimensional embeddings and 8 attention heads, trained on Pride and Prejudice. 
        Every component shown — the multi-head self-attention, feed-forward layers, residual 
        connections, and layer normalisation — is implemented from scratch in PyTorch and 
        running live in this deployment.
        """)

    st.markdown("### Attention Mechanism Detail")
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        st.image(f"{ASSETS_BASE_URL}model_attention_mechanism.png", 
                caption="Attention mechanism: Q/K/V computation, multi-head attention, and token attention heatmap",
                use_container_width=True)
            
    st.markdown("""
    **What you're seeing:** The attention mechanism at the heart of the transformer — 
    showing how each token learns which other tokens to attend to when building its 
    contextual representation.
    
    The diagram shows three things:
    - **Single attention head** — how Query, K, and Value matrices are computed from the 
      input and combined via scaled dot-product attention
    - **Multi-head attention** — how 8 heads run in parallel, each learning different 
      relationship patterns, before being concatenated and projected
    - **Attention heatmap** — the actual weight matrix showing which token pairs attend 
      to each other most strongly
    
    This is the exact mechanism running in the live model. The heatmap in the 
    Attention Visualisation tab shows real weights from your input text.
    """)

    st.markdown("---")

    # Pipeline Diagram Section  
    st.header("Complete MLOps Pipeline")

    # Use columns to constrain width
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        st.image(f"{ASSETS_BASE_URL}cicd_deployment_pipeline.png", 
                caption="CI/CD deployment pipeline: from code push through GitHub Actions and Terraform to live AWS infrastructure",
                use_container_width=True)

    st.markdown("""
    **What you're seeing:** The complete MLOps pipeline demonstrating modern **FinOps** practices. 
    Shows how code moves from local development through automated CI/CD to cost-optimised production infrastructure.

    **Key Highlights:**
    - **FinOps Integration:** Real-time cost monitoring and optimisation throughout the pipeline
    - **Automation Flow:** GitHub Actions → Docker → ECR → Terraform → AWS Lambda  
    - **Cost Efficiency:** Serverless architecture minimises idle costs, with monitoring and alerts
    - **Feedback Loop:** Performance and cost metrics inform continuous optimisation
    - **Speed:** Most deployments complete in under an hour with zero downtime

    **FinOps Benefits:**
    - Pay-per-request Lambda pricing (no idle costs)
    - Real-time cost tracking and budget alerts  
    - Infrastructure as Code enables cost predictability
    - Automated scaling prevents over-provisioning
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### What You Can Explore:
        
        **Text Generation**: Generate creative text continuations using the transformer model trained on Pride and Prejudice
        
        **Attention Visualisation**: Explore how the model "pays attention" to different words across multiple heads and layers
        
        **System Monitoring**: View real-time performance metrics and AWS costs for the production deployment
        """)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3> Performance</h3>
            <p>Real-time metrics</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3> Cost</h3>
            <p>Live AWS billing</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3> Monitoring</h3>
            <p>CloudWatch integration</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Technical Architecture
    st.header(" Technical Implementation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4> ML Model</h4>
            <ul>
                <li>Custom transformer architecture</li>
                <li>4 layers, 8 attention heads</li>
                <li>256-dimensional embeddings</li>
                <li>Trained on Pride and Prejudice</li>
                <li>Built with PyTorch from scratch</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4> AWS Infrastructure</h4>
            <ul>
                <li>Lambda containers (PyTorch)</li>
                <li>API Gateway endpoints</li>
                <li>S3 model storage</li>
                <li>CloudWatch monitoring</li>
                <li>ECR container registry</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4> DevOps Pipeline</h4>
            <ul>
                <li>Terraform Infrastructure as Code</li>
                <li>GitHub Actions CI/CD</li>
                <li>Automated deployments</li>
                <li>Change detection</li>
                <li>Cost optimisation</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def show_text_generation_page():
    """Text generation page"""
    st.markdown("""
    <div class="main-header">
        <h1> Text Generation</h1>
        <p>Generate creative text continuations using a custom transformer model</p>
    </div>
    """, unsafe_allow_html=True)
    
    # How it works section
    how_it_works = st.expander(" **How Transformer Text Generation Works**", expanded=False)
    with how_it_works:
        st.markdown("""
        ### The Transformer Architecture
        
        **Self-Attention Mechanism**: The model looks at all words in the input simultaneously, understanding relationships and context between them.
        
        **Autoregressive Generation**: The model generates text one token at a time, using previously generated tokens as context for the next prediction.
        
        **Multi-Head Attention**: With 8 attention heads, the model can focus on different types of relationships (syntax, semantics, etc.) in parallel.
        
        ### Training Process
        1. **Dataset**: Trained exclusively on Jane Austen's "Pride and Prejudice"
        2. **Objective**: Learn to predict the next word given previous context
        3. **Optimisation**: Uses the Adam optimiser with learning rate scheduling
        4. **Validation**: Monitored perplexity and generation quality
        
        ### Generation Strategy
        The model uses configurable sampling strategies (temperature, top-p, top-k) to balance creativity and coherence in generated text.
        """)
    
    st.markdown("---")
    
    # Check warmup status
    models_ready = check_warmup_status()
    
    if models_ready:
        # Text generation interface
        st.header("Generate Text")
        
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
                "Temperature:",
                min_value=0.1,
                max_value=2.0,
                value=0.8,
                step=0.1,
                help="Controls randomness: lower = more focused, higher = more creative"
            )
            
            top_p = st.slider(
                "Top-p (nucleus sampling):",
                min_value=0.1,
                max_value=1.0,
                value=0.9,
                step=0.05,
                help="Considers tokens with cumulative probability up to p"
            )
            
            top_k = st.slider(
                "Top-k sampling:",
                min_value=1,
                max_value=100,
                value=50,
                help="Consider only the k most likely next tokens"
            )
        
        if st.button("Generate Text", type="primary", use_container_width=True):
            if prompt.strip():
                with st.spinner("Generating text..."):
                    start_time = time.time()
                    payload = {
                        "prompt": prompt,
                        "max_length": max_length,
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k
                    }
                    result, error = call_api(GENERATE_ENDPOINT, payload)
                    response_time = time.time() - start_time
                    
                    if result:
                        st.success("Generation Complete!")
                        
                        # Display results
                        st.markdown("### Generated Text:")
                        st.markdown(f"**Input:** {prompt}")
                        st.markdown(f"**Generated:** {result.get('generated_text', 'No text generated')}")
                        
                        # Metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Response Time", f"{response_time:.1f}s")
                        with col2:
                            if "tokens_generated" in result:
                                st.metric("Tokens Generated", result['tokens_generated'])
                        with col3:
                            if result.get('tokens_generated', 0) > 0:
                                tokens_per_sec = result['tokens_generated'] / response_time
                                st.metric("Tokens/Second", f"{tokens_per_sec:.1f}")
                    else:
                        st.error(f"❌ {error}")
            else:
                st.warning("⚠️ Please enter a prompt")

def show_attention_visualisation_page():
    """Attention visualisation page"""
    st.markdown("""
    <div class="main-header">
        <h1>Attention Visualisation</h1>
        <p>Explore how the transformer model pays attention to different words</p>
    </div>
    """, unsafe_allow_html=True)
    
    # How it works section
    how_it_works = st.expander("**Understanding Attention Mechanisms**", expanded=False)
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
        
        ### Visualisation Explained
        
        **Heatmap Colours**:
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
        # Attention visualisation interface
        st.header("Visualise Attention")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            text_input = st.text_area(
                "Enter text to analyse:",
                value="The cat sat on the mat and looked around",
                height=100,
                help="Enter text to see how the model pays attention to different words"
            )
        
        with col2:
            layer = st.selectbox(
                "Layer:",
                options=list(range(4)),
                index=2,
                help="Deeper layers capture more complex patterns",
                format_func=lambda x: f"Layer {x+1} {'(Deep)' if x >= 2 else '(Shallow)'}"
            )
            
            # Multi-head selection options
            head_mode = st.radio(
                "Attention Heads:",
                ["Single Head", "Multiple Heads (2x2)", "All Heads (4x2)"],
                help="Choose how many attention heads to visualise simultaneously"
            )
            
            if head_mode == "Single Head":
                head = st.selectbox(
                    "Select Head:",
                    options=list(range(8)),
                    index=0,
                    format_func=lambda x: f"Head {x+1}"
                )
                heads_to_show = [head]
            elif head_mode == "Multiple Heads (2x2)":
                heads_to_show = [0, 1, 2, 3]  # First 4 heads
            else:  # All Heads
                heads_to_show = list(range(8))  # All 8 heads
            
            st.info(f"Analysing **Layer {layer+1}**, showing {len(heads_to_show)} head(s)")
        
        if st.button("Visualise Attention", type="primary", use_container_width=True):
            if text_input.strip():
                with st.spinner("Analysing attention patterns..."):
                    start_time = time.time()
                    payload = {
                        "text": text_input,
                        "layer": layer,
                        "heads": heads_to_show  # Send multiple heads
                    }
                    result, error = call_api(VISUALISE_ENDPOINT, payload)
                    response_time = time.time() - start_time
                    
                    if result and result.get("attention_image"):
                        st.success("✅ Analysis Complete!")
                        
                        try:
                            # Decode and display image
                            image_data = base64.b64decode(result["attention_image"])
                            image = Image.open(BytesIO(image_data))
                            
                            st.markdown("### Attention Heatmap:")
                            st.image(image, use_container_width=True, 
                                   caption=f"Attention patterns for Layer {layer+1}, {len(heads_to_show)} head(s)")
                            
                            # Analysis info
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Analysis Time", f"{response_time:.1f}s")
                            with col2:
                                if "tokens" in result:
                                    st.metric("Tokens Analysed", len(result['tokens']))
                            with col3:
                                st.metric("Layer/Heads", f"{layer+1}/{len(heads_to_show)}")
                            
                            # Show tokenisation with explanation
                            if "tokens" in result:
                                st.markdown("### Tokenisation Analysis:")
                                
                                # Show tokens
                                tokens_display = " | ".join(result['tokens'])
                                st.code(tokens_display, language=None)
                                
                                # Explain tokenisation
                                st.markdown("""
                                **Understanding the Tokens:**
                                
                                - **`<BOS>`**: Beginning of Sequence - marks the start of input
                                - **`<EOS>`**: End of Sequence - marks the end of input  
                                - **`<UNK>`**: Unknown Token - words not in the training vocabulary (Pride and Prejudice)
                                - **Lowercase tokens**: Words that appeared in the training text
                                
                                Since this model was trained only on "Pride and Prejudice", modern words like "cat" 
                                might not be in the vocabulary and get replaced with `<UNK>` tokens. This demonstrates 
                                the limited but focused nature of the training corpus.
                                """)
                                
                        except Exception as e:
                            st.error(f"Error displaying visualisation: {str(e)}")
                    else:
                        st.error(f"❌ {error or 'No visualisation generated'}")
            else:
                st.warning("⚠️ Please enter text to analyse")

# Main app routing
page = st.session_state.current_page
if page == "Home & Overview":
    show_home_page()
elif page == "Text Generation":
    show_text_generation_page()
elif page == "Attention Visualisation":
    show_attention_visualisation_page()
elif page == "System Monitoring":
    try:
        main_monitoring()
    except Exception as e:
        st.error("⚠️ Monitoring dashboard failed to load.")
        st.markdown(f"**Error:** `{e}`")
        st.markdown("This is likely a temporary issue with the CloudWatch connection. Try refreshing the page.")
