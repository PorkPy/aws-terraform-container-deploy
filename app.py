# app.py
import streamlit as st
import pandas as pd
from PIL import Image
import base64

# Page configuration
st.set_page_config(
    page_title="Dom McKean | Data Scientist & ML Engineer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Navigation and page management
def main():
    # Sidebar navigation
    with st.sidebar:
        st.image("assets/profile_photo.jpg", width=200)
        st.title("Dom McKean")
        st.subheader("Data Scientist & ML Engineer")
        
        # Navigation
        page = st.radio(
            "Navigate",
            ["Home", "Experience", "Projects", "Skills", "About Me", "Contact"]
        )
        
        # Social links
        st.write("---")
        cols = st.columns(3)
        with cols[0]:
            st.link_button("LinkedIn", "https://linkedin.com/in/dom-mckean")
        with cols[1]:
            st.link_button("GitHub", "https://github.com/yourusername")
        with cols[2]:
            st.link_button("CV (PDF)", "assets/Dom_McKean_CV.pdf")
    
    # Page content
    if page == "Home":
        home_page()
    elif page == "Experience":
        experience_page()
    elif page == "Projects":
        projects_page()
    elif page == "Skills":
        skills_page()
    elif page == "About Me":
        about_me_page()
    elif page == "Contact":
        contact_page()

# Define pages
def home_page():
    # Header
    st.title("Transforming Data into Intelligence")
    
    # Introduction
    st.markdown("""
    ## Welcome to my portfolio
    
    I'm a Data Scientist and ML Engineer who specializes in extracting meaningful signals from complex data. 
    With a unique background spanning engineering, robotics, and control systems, I bring a distinctive perspective 
    to data science challenges.
    
    > "The value lies not in how much data you process, but in what meaningful information you extract and apply."
    """)
    
    # Featured projects
    st.subheader("Featured Projects")
    
    col1, col2 = st.columns(2)
    with col1:
        st.image("assets/transformer_viz.jpg")
        st.markdown("### Transformer Architecture Implementation")
        st.markdown("Built a transformer model from scratch with interactive visualizations of attention mechanisms.")
        st.link_button("View Details", "?page=Projects#transformer")
    
    with col2:
        st.image("assets/research_assessment.jpg")
        st.markdown("### LLM-Based Research Assessment")
        st.markdown("Created an AI system to predict peer review outcomes with 85% accuracy.")
        st.link_button("View Details", "?page=Projects#research")
    
    # Featured skills
    st.subheader("Core Capabilities")
    
    capabilities = {
        "Signal Extraction": "Identifying meaningful patterns in noisy, high-dimensional data",
        "Intelligence Gap Analysis": "Detecting critical missing information and developing strategies to acquire it",
        "System Modeling": "Creating comprehensive mental models of complex systems and their interactions",
        "Information-Centric Design": "Building solutions around information needs rather than available datasets"
    }
    
    for capability, description in capabilities.items():
        st.markdown(f"**{capability}**: {description}")
    
    # Call to action
    st.write("---")
    st.markdown("### Let's Connect")
    st.markdown("I'm always interested in challenging problems and new opportunities. Feel free to reach out!")
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("View My Projects", "?page=Projects")
    with col2:
        st.link_button("Contact Me", "?page=Contact")

# Additional pages
def projects_page():
    st.title("Projects")
    
    # Project tabs
    project_tabs = st.tabs([
        "Transformer Model", 
        "Research Assessment", 
        "arXiv Blog Generator",
        "Psycholinguistic Analysis",
        "Educational Psychology Assistant"
    ])
    
    with project_tabs[0]:
        st.markdown('<a name="transformer"></a>', unsafe_allow_html=True)
        st.header("Transformer Architecture Implementation")
        st.image("assets/transformer_architecture.png", use_column_width=True)
        
        st.markdown("""
        ### Overview
        
        Developed a fully-functional transformer language model from scratch, implementing the complete architecture 
        that powers modern AI systems. Created an interactive visualization application that provides unprecedented 
        insight into how transformers learn language patterns through attention mechanisms.
        
        ### Key Features
        
        - Complete PyTorch implementation of transformer architecture including self-attention mechanisms, 
          positional encoding, and feed-forward networks
        - Interactive visualization of attention patterns across different heads and layers
        - Token probability distribution analysis
        - Training progression visualization showing model learning over time
        - Streamlit-based user interface for experimentation
        
        ### Technical Details
        
        - **Framework**: PyTorch for model implementation
        - **Architecture**: 4-layer transformer with 8 attention heads
        - **Training**: Adaptive learning rate scheduling with checkpointing
        - **Visualization**: Custom attention map rendering with Streamlit
        - **Dataset**: Trained on text corpus to demonstrate language modeling capabilities
        
        ### Impact & Outcomes
        
        This project provides a rare window into the inner workings of transformer models, allowing users to see 
        exactly how attention mechanisms focus on different aspects of language. It serves as both an educational 
        tool and a practical implementation reference.
        """)
        
        # Demo section
        st.subheader("Interactive Demo")
        st.video("assets/transformer_demo.mp4")
        
        col1, col2 = st.columns(2)
        with col1:
            st.link_button("Live Demo", "https://your-transformer-demo-url.streamlit.app")
        with col2:
            st.link_button("GitHub Repository", "https://github.com/yourusername/transformer-from-scratch")

    # Similar detailed sections for other projects...

# Additional page functions (experience_page, skills_page, etc.)

if __name__ == "__main__":
    main()