import base64
import json
import threading
import time
from io import BytesIO

import requests

# Import monitoring dashboard
from monitoring_dashboard import main_monitoring
from PIL import Image

import streamlit as st

# Page config
st.set_page_config(
    page_title="Custom ML Model Production",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern sidebar
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

# Modern sidebar navigation with buttons
st.sidebar.markdown("# 🤖 **Custom ML Production**")
st.sidebar.markdown("---")

# Initialize session state for navigation
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Home & Overview"

# Navigation buttons
nav_options = [
    "🏠 Home & Overview",
    "🚀 Text Generation",
    "👁️ Attention Visualisation",
    "🔍 System Monitoring",
]

st.sidebar.markdown("**Navigate to:**")
for option in nav_options:
    button_class = "nav-button active" if st.session_state.current_page == option else "nav-button"
    if st.sidebar.button(option, key=f"nav_{option}", use_container_width=True):
        st.session_state.current_page = option
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
<div style='text-align: center; colour: #888; font-size: 0.8rem;'>
    <p>Built with Streamlit<br>
    Powered by AWS Lambda<br>
    Infrastructure as Code</p>
</div>
""",
    unsafe_allow_html=True,
)

# API Configuration
API_BASE_URL = "https://0fc0dgwg69.execute-api.eu-west-2.amazonaws.com"
GENERATE_ENDPOINT = f"{API_BASE_URL}/generate"
VISUALISE_ENDPOINT = f"{API_BASE_URL}/visualize"

# S3 URLs for diagrams
ASSETS_BASE_URL = (
    "https://transformer-model-artifacts-q3ukv7.s3.eu-west-2.amazonaws.com/static-assets/"
)


def check_models_health():
    """Quick health check without warming up"""
    try:
        # Minimal health check payload
        health_payload = {"prompt": "test", "max_length": 1}

        response = requests.post(
            GENERATE_ENDPOINT,
            json=health_payload,
            headers={"Content-Type": "application/json"},
            timeout=8,  # Reasonable timeout for health check
        )

        if response.status_code == 200:
            return True, "Models are ready and responsive"
        else:
            return False, f"Models returned status {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "Models are cold and need spinning up"
    except Exception as e:
        return False, f"Models unavailable: {str(e)}"


def warm_up_lambdas():
    """Warm up both Lambda functions"""
    endpoints = [
        {"url": GENERATE_ENDPOINT, "payload": {"prompt": "warmup", "max_length": 10}},
        {"url": VISUALISE_ENDPOINT, "payload": {"text": "warmup", "layer": 0, "head": 0}},
    ]

    for endpoint in endpoints:
        try:
            requests.post(
                endpoint["url"],
                json=endpoint["payload"],
                timeout=30,
                headers={"Content-Type": "application/json"},
            )
        except:
            pass


def check_warmup_status():
    """Automatic model availability check with proper status flow"""
    if "models_status_checked" not in st.session_state:
        st.session_state.models_status_checked = False
        st.session_state.models_ready = False

    if not st.session_state.models_status_checked:
        # Step 1: Initial availability check
        with st.spinner("🔍 **Initiating model availability check...**"):
            time.sleep(1)  # Brief pause for UX
            models_ready, status_msg = check_models_health()

        if models_ready:
            # Step 2a: Models are ready
            st.success("✅ **Check passed - Models ready**")
            st.session_state.models_ready = True
            st.session_state.models_status_checked = True
            time.sleep(1)
            st.rerun()
        else:
            # Step 2b: Models need spinning up
            st.warning("🟡 **Models are cold - Spinning up models. Stand by...**")

            with st.spinner("⚡ **Models spinning up... This may take 30-60 seconds**"):
                start_time = time.time()
                warm_up_lambdas()
                spin_time = time.time() - start_time

                # Verify they're now ready
                models_ready_after, _ = check_models_health()

            if models_ready_after:
                st.success(f"🟢 **Models ready** - Spun up in {spin_time:.0f} seconds")
                st.session_state.models_ready = True
            else:
                st.error("❌ **Models failed to spin up** - Some features may be slower")
                st.session_state.models_ready = False

            st.session_state.models_status_checked = True
            time.sleep(2)  # Let user read the message
            st.rerun()

    else:
        # Already checked - show current status
        if st.session_state.models_ready:
            st.success("🟢 **Models Ready** - All systems operational")
        else:
            st.info("🟡 **Models Status** - First requests may take longer")

    return st.session_state.models_ready


def call_api(endpoint, payload):
    """Make API call with error handling"""
    try:
        response = requests.post(
            endpoint, json=payload, headers={"Content-Type": "application/json"}, timeout=120
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


def show_home_page():
    """Home page with project overview"""
    st.markdown(
        """
    <div class="main-header">
        <h1>Custom ML Model Productionisation</h1>
        <p>Complete end-to-end machine learning pipeline automated on GitHub using Terraform IaC and hosted on AWS serverless infrastructure feeding a Streamlit app front-end</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Project Overview
    st.header("📋 Project Overview")

    st.markdown(
        """
    This project demonstrates a **complete machine learning production pipeline** showcasing the full journey from model development to scalable deployment. 
    
    At its core is a **custom transformer language model trained from scratch** using only Jane Austen's "Pride and Prejudice" as the training corpus. 
    Whilst this creates a deliberately limited vocabulary model, it serves as an ideal demonstration piece showing that I can:
    
    - **Build neural networks from first principles** - implementing transformer architecture, attention mechanisms, and training loops
    - **Deploy models at scale** - containerising PyTorch models and orchestrating AWS infrastructure 
    - **Automate entire pipelines** - from code push through GitHub Actions to live AWS deployment
    - **Optimise for cost and performance** - using serverless architecture with real-time monitoring
    
    The emphasis here isn't on creating the world's best language model, but rather demonstrating **production ML engineering capabilities** 
    that translate to any model architecture or business domain. The monitoring dashboard shows real AWS costs and performance metrics, 
    proving this isn't just a toy project but a genuinely deployed production system.
    """
    )

    # Architecture Diagrams
    st.header("🏗️ System Architecture")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📊 Complete System Overview")
        st.image(
            f"{ASSETS_BASE_URL}AWS_1.png",
            caption="Complete AWS serverless infrastructure with all components",
            use_container_width=True,
        )

        st.markdown(
            """
        **What you're seeing:** End-to-end system architecture showing how the Streamlit app 
        connects through API Gateway to Lambda containers, with S3 storage and monitoring. 
        Perfect for understanding the complete production infrastructure.
        """
        )

    with col2:
        st.markdown("### 🔄 Request Flow & Execution")
        st.image(
            f"{ASSETS_BASE_URL}AWS_2.png",
            caption="Detailed request flow showing cold start and warm execution paths",
            use_container_width=True,
        )

        st.markdown(
            """
        **What you're seeing:** Step-by-step request flow from user interaction to model inference. 
        Shows both cold start (first request) and warm execution paths, plus VPC security boundaries.
        Technical teams love this level of detail.
        """
        )

    st.markdown("---")

    # Model Architecture Section
    st.header("🧠 Model Architecture & Attention Mechanism")

    st.markdown("### 🏗️ Transformer Architecture")
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        st.image(
            "https://jalammar.github.io/images/t/transformer_resideual_layer_norm_3.png",
            caption="Multi-layer transformer with residual connections - Source: The Illustrated Transformer",
            use_container_width=True,
        )

    st.markdown(
        """
    **What you're seeing:** This transformer architecture is very similar to what I built, 
    showing the key components: multi-head attention, feed-forward networks, and residual 
    connections. The main differences from my implementation are:

    - **Layers:** This shows 2 layers vs my 4-layer model
    - **Dimensions:** Standard 512d vs my 256d embeddings  
    - **Architecture:** This is encoder-decoder vs my encoder-only design
    - **Training:** Standard pre-training vs my Pride and Prejudice corpus

    The core concepts (attention, residuals, layer norms) are identical.
    """
    )

    st.markdown("### 👁️ Attention Mechanism Detail")
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        st.image(
            f"{ASSETS_BASE_URL}attention_1.png",
            caption="How transformer attention works - Created with Sora AI",
            use_container_width=True,
        )

    st.markdown(
        """
    **What you're seeing:** Detailed breakdown of transformer attention mechanisms, from 
    input tokens through Q/K/V computation to final attention heatmaps. This diagram was 
    created using Sora AI to illustrate the concepts clearly.

    **Technical Accuracy Notes:**
    - The core attention flow and mathematical formulas are correct
    - Shows the right tensor dimensions and multi-head structure
    - Some visual artifacts (unusual symbols, formatting) are AI-generated quirks
    - The essential concepts match my implementation: 8 heads, matrix operations, softmax attention

    **Key Components Explained:**
    - **Single Attention Head:** Shows Q, K, V matrix creation and scaled dot-product
    - **Multi-Head Attention:** Demonstrates parallel processing across 8 heads
    - **Heatmap Visualisation:** How attention weights create the patterns you see in the demo

    This illustrates the same attention mechanism implemented in my model, scaled to show 
    the mathematical operations clearly.
    """
    )

    st.markdown("---")

    # Pipeline Diagram Section
    st.header("🔄 Complete MLOps Pipeline")

    # Use columns to constrain width
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        st.image(
            f"{ASSETS_BASE_URL}pipeline_1.png",
            caption="End-to-end machine learning pipeline from development to production",
            use_container_width=True,
        )

    st.markdown(
        """
    **What you're seeing:** The complete MLOps pipeline demonstrating modern **FinOps** practices. 
    Shows how code moves from local development through automated CI/CD to cost-optimised production infrastructure.

    **Key Highlights:**
    - **🏦 FinOps Integration:** Real-time cost monitoring and optimisation throughout the pipeline
    - **⚡ Automation Flow:** GitHub Actions → Docker → ECR → Terraform → AWS Lambda  
    - **💰 Cost Efficiency:** Serverless architecture minimises idle costs, with monitoring and alerts
    - **🔄 Feedback Loop:** Performance and cost metrics inform continuous optimisation
    - **⏱️ Speed:** Most deployments complete in under an hour with zero downtime

    **FinOps Benefits:**
    - Pay-per-request Lambda pricing (no idle costs)
    - Real-time cost tracking and budget alerts  
    - Infrastructure as Code enables cost predictability
    - Automated scaling prevents over-provisioning
    """
    )

    st.markdown(
        """
    ### What You Can Explore:
    
    **🚀 Text Generation**: Generate creative text continuations using the transformer model trained on Pride and Prejudice
    
    **👁️ Attention Visualisation**: Explore how the model "pays attention" to different words across multiple heads and layers
    
    **🔍 System Monitoring**: View real-time performance metrics and AWS costs for the production deployment
    """
    )

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown(
            """
        <div class="metric-card">
            <h3>⚡ Performance</h3>
            <p>Real-time metrics</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="metric-card">
            <h3>💰 Cost</h3>
            <p>Live AWS billing</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
        <div class="metric-card">
            <h3>🔧 Monitoring</h3>
            <p>CloudWatch integration</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Technical Architecture
    st.header("🏗️ Technical Implementation")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        <div class="feature-card">
            <h4>🧠 ML Model</h4>
            <ul>
                <li>Custom transformer architecture</li>
                <li>4 layers, 8 attention heads</li>
                <li>256-dimensional embeddings</li>
                <li>Trained on Pride and Prejudice</li>
                <li>Built with PyTorch from scratch</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="feature-card">
            <h4>☁️ AWS Infrastructure</h4>
            <ul>
                <li>Lambda containers (PyTorch)</li>
                <li>API Gateway endpoints</li>
                <li>S3 model storage</li>
                <li>CloudWatch monitoring</li>
                <li>ECR container registry</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
        <div class="feature-card">
            <h4>🔧 DevOps Pipeline</h4>
            <ul>
                <li>Terraform Infrastructure as Code</li>
                <li>GitHub Actions CI/CD</li>
                <li>Automated deployments</li>
                <li>Change detection</li>
                <li>Cost optimisation</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Model warmup status
    st.markdown("---")
    st.header("🔥 System Status")
    # check_warmup_status()


def show_text_generation_page():
    """Text generation page"""
    st.markdown(
        """
    <div class="main-header">
        <h1>🚀 Text Generation</h1>
        <p>Generate creative text continuations using a custom transformer model</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # How it works section
    how_it_works = st.expander("🧠 **How Transformer Text Generation Works**", expanded=False)
    with how_it_works:
        st.markdown(
            """
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
        """
        )

    st.markdown("---")

    # Check warmup status
    models_ready = True  # check_warmup_status()

    if models_ready:
        # Text generation interface
        st.header("✍️ Generate Text")

        col1, col2 = st.columns([2, 1])

        with col1:
            prompt = st.text_area(
                "Enter your prompt:",
                value="The future of artificial intelligence is",
                height=100,
                help="Enter a starting phrase and the model will continue the text",
            )

        with col2:
            max_length = st.slider(
                "Maximum length:",
                min_value=10,
                max_value=100,
                value=50,
                help="Maximum number of tokens to generate",
            )

            temperature = st.slider(
                "Temperature:",
                min_value=0.1,
                max_value=2.0,
                value=0.8,
                step=0.1,
                help="Controls randomness: lower = more focused, higher = more creative",
            )

            top_p = st.slider(
                "Top-p (nucleus sampling):",
                min_value=0.1,
                max_value=1.0,
                value=0.9,
                step=0.05,
                help="Considers tokens with cumulative probability up to p",
            )

            top_k = st.slider(
                "Top-k sampling:",
                min_value=1,
                max_value=100,
                value=50,
                help="Consider only the k most likely next tokens",
            )

        if st.button("🚀 Generate Text", type="primary", use_container_width=True):
            if prompt.strip():
                with st.spinner("🤖 Generating text..."):
                    start_time = time.time()
                    payload = {
                        "prompt": prompt,
                        "max_length": max_length,
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k,
                    }
                    result, error = call_api(GENERATE_ENDPOINT, payload)
                    response_time = time.time() - start_time

                    if result:
                        st.success("✅ Generation Complete!")

                        # Display results
                        st.markdown("### 📝 Generated Text:")
                        st.markdown(f"**Input:** {prompt}")
                        st.markdown(
                            f"**Generated:** {result.get('generated_text', 'No text generated')}"
                        )

                        # Metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("⚡ Response Time", f"{response_time:.1f}s")
                        with col2:
                            if "tokens_generated" in result:
                                st.metric("🔢 Tokens Generated", result["tokens_generated"])
                        with col3:
                            if result.get("tokens_generated", 0) > 0:
                                tokens_per_sec = result["tokens_generated"] / response_time
                                st.metric("🚀 Tokens/Second", f"{tokens_per_sec:.1f}")
                    else:
                        st.error(f"❌ {error}")
            else:
                st.warning("⚠️ Please enter a prompt")


def show_attention_visualisation_page():
    """Attention visualisation page"""
    st.markdown(
        """
    <div class="main-header">
        <h1>👁️ Attention Visualisation</h1>
        <p>Explore how the transformer model pays attention to different words</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # How it works section
    how_it_works = st.expander("🧠 **Understanding Attention Mechanisms**", expanded=False)
    with how_it_works:
        st.markdown(
            """
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
        """
        )

    st.markdown("---")

    # Check warmup status
    models_ready = True  # check_warmup_status()

    if models_ready:
        # Attention visualisation interface
        st.header("🔍 Visualise Attention")

        col1, col2 = st.columns([2, 1])

        with col1:
            text_input = st.text_area(
                "Enter text to analyse:",
                value="The cat sat on the mat and looked around",
                height=100,
                help="Enter text to see how the model pays attention to different words",
            )

        with col2:
            layer = st.selectbox(
                "🏗️ Layer:",
                options=list(range(4)),
                index=2,
                help="Deeper layers capture more complex patterns",
                format_func=lambda x: f"Layer {x+1} {'(Deep)' if x >= 2 else '(Shallow)'}",
            )

            # Multi-head selection options
            head_mode = st.radio(
                "👁️ Attention Heads:",
                ["Single Head", "Multiple Heads (2x2)", "All Heads (4x2)"],
                help="Choose how many attention heads to visualise simultaneously",
            )

            if head_mode == "Single Head":
                head = st.selectbox(
                    "Select Head:",
                    options=list(range(8)),
                    index=0,
                    format_func=lambda x: f"Head {x+1}",
                )
                heads_to_show = [head]
            elif head_mode == "Multiple Heads (2x2)":
                heads_to_show = [0, 1, 2, 3]  # First 4 heads
            else:  # All Heads
                heads_to_show = list(range(8))  # All 8 heads

            st.info(f"💡 Analysing **Layer {layer+1}**, showing {len(heads_to_show)} head(s)")

        if st.button("🔍 Visualise Attention", type="primary", use_container_width=True):
            if text_input.strip():
                with st.spinner("🧠 Analysing attention patterns..."):
                    start_time = time.time()
                    payload = {
                        "text": text_input,
                        "layer": layer,
                        "heads": heads_to_show,  # Send multiple heads
                    }
                    result, error = call_api(VISUALISE_ENDPOINT, payload)
                    response_time = time.time() - start_time

                    # DEBUG: Check what the Lambda actually returned
                    st.write(
                        "**DEBUG - API Response Keys:**",
                        list(result.keys()) if result else "No result",
                    )
                    if result:
                        st.write("**DEBUG - Has attention_image:**", "attention_image" in result)
                        st.write("**DEBUG - Has attention_images:**", "attention_images" in result)
                        st.write("**DEBUG - Payload sent:**", payload)

                    if result:
                        st.success("✅ Analysis Complete!")

                        try:
                            if "attention_images" in result:  # Multiple images
                                st.markdown("### 🎨 Attention Heatmaps:")

                                images = []
                                for img_b64 in result["attention_images"]:
                                    image_data = base64.b64decode(img_b64)
                                    images.append(Image.open(BytesIO(image_data)))

                                # Display in grid
                                if len(images) == 4:  # 2x2 grid
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.image(
                                            images[0], caption="Head 1", use_container_width=True
                                        )
                                        st.image(
                                            images[2], caption="Head 3", use_container_width=True
                                        )
                                    with col2:
                                        st.image(
                                            images[1], caption="Head 2", use_container_width=True
                                        )
                                        st.image(
                                            images[3], caption="Head 4", use_container_width=True
                                        )
                                elif len(images) == 8:  # 4x2 grid (if you want all 8)
                                    for i in range(0, 8, 2):
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.image(
                                                images[i],
                                                caption=f"Head {i+1}",
                                                use_container_width=True,
                                            )
                                        with col2:
                                            if i + 1 < len(images):
                                                st.image(
                                                    images[i + 1],
                                                    caption=f"Head {i+2}",
                                                    use_container_width=True,
                                                )

                            elif "attention_image" in result:  # Single image
                                st.markdown("### 🎨 Attention Heatmap:")
                                image_data = base64.b64decode(result["attention_image"])
                                image = Image.open(BytesIO(image_data))
                                st.image(
                                    image,
                                    use_container_width=True,
                                    caption=f"Attention patterns for Layer {layer+1}, {len(heads_to_show)} head(s)",
                                )

                            # Analysis info (keep your existing metrics)
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("⚡ Analysis Time", f"{response_time:.1f}s")
                            with col2:
                                if "tokens" in result:
                                    st.metric("🔤 Tokens Analysed", len(result["tokens"]))
                            with col3:
                                st.metric("🎯 Layer/Heads", f"{layer+1}/{len(heads_to_show)}")

                            # Show tokenisation with explanation (keep your existing code)
                            if "tokens" in result:
                                st.markdown("### 🔤 Tokenisation Analysis:")
                                # ... rest of your tokenization code

                        except Exception as e:
                            st.error(f"Error displaying visualisation: {str(e)}")
                    else:
                        st.error(f"❌ {error or 'No visualisation generated'}")
            else:
                st.warning("⚠️ Please enter text to analyse")


# Main app routing
page = st.session_state.current_page

if page == "🏠 Home & Overview":
    show_home_page()
elif page == "🚀 Text Generation":
    show_text_generation_page()
elif page == "👁️ Attention Visualisation":
    show_attention_visualisation_page()
elif page == "🔍 System Monitoring":
    main_monitoring()
