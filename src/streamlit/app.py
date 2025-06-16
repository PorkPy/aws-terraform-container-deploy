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
    
    # SHARED INPUT SECTION - NEW!
    st.header("📝 Input Text")
    shared_text = st.text_area(
        "Enter your text:", 
        value="The future of artificial intelligence is bright and full of possibilities",
        height=100,
        disabled=not st.session_state.models_ready,
        help="This text will be used for both generation and visualization"
    )
    
    st.markdown("---")
    
    # Create two columns for the different functionalities
    col1, col2 = st.columns(2)
    
    # INITIALIZE SESSION STATE FOR PERSISTENT RESULTS - NEW!
    if 'generation_result' not in st.session_state:
        st.session_state.generation_result = None
    if 'visualization_result' not in st.session_state:
        st.session_state.visualization_result = None
    
    # Determine if buttons should be disabled
    buttons_disabled = not st.session_state.models_ready
    
    # Text Generation Section
    with col1:
        st.header("🚀 Text Generation")
        st.markdown("Generate text continuation using transformer model")
        
        max_length = st.slider(
            "Max length:", 
            min_value=10, 
            max_value=100, 
            value=50,
            disabled=buttons_disabled,
            help="Maximum number of tokens to generate"
        )
        
        # Button with conditional styling and disabled state
        button_text = "⏳ Warming Up..." if buttons_disabled else "🚀 Generate Text"
        
        if st.button(button_text, type="primary", disabled=buttons_disabled, key="gen_button"):
            if shared_text.strip():  # CHANGED: use shared_text instead of prompt
                with st.spinner("Generating text..."):
                    start_time = time.time()
                    payload = {"prompt": shared_text, "max_length": max_length}  # CHANGED: use shared_text
                    result, error = call_api(GENERATE_ENDPOINT, payload)
                    response_time = time.time() - start_time
                    
                    if result:
                        # STORE RESULT IN SESSION STATE - NEW!
                        st.session_state.generation_result = {
                            'text': result.get("generated_text", "No text generated"),
                            'tokens': result.get("tokens_generated"),
                            'time': response_time,
                            'prompt': shared_text
                        }
                    else:
                        st.session_state.generation_result = {'error': error}
            else:
                st.warning("Please enter some text")
        
        # DISPLAY STORED GENERATION RESULT - NEW!
        if st.session_state.generation_result:
            if 'error' in st.session_state.generation_result:
                st.error(f"❌ {st.session_state.generation_result['error']}")
            else:
                st.subheader("Generated Text:")
                st.write(st.session_state.generation_result['text'])
                st.caption(f"⚡ Generated in {st.session_state.generation_result['time']:.1f}s")
                
                if st.session_state.generation_result.get('tokens'):
                    st.caption(f"Tokens generated: {st.session_state.generation_result['tokens']}")
        
        # Show help text when disabled
        if buttons_disabled:
            st.caption("🔄 Button will be enabled once models finish warming up")
    
    # Attention Visualization Section  
    with col2:
        st.header("👁️ Attention Visualization")
        st.markdown("Visualize transformer attention patterns")
        
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
            if shared_text.strip():  # CHANGED: use shared_text instead of text_input
                with st.spinner("Creating attention visualization..."):
                    start_time = time.time()
                    payload = {"text": shared_text, "layer": layer, "head": head}  # CHANGED: use shared_text
                    result, error = call_api(VISUALIZE_ENDPOINT, payload)
                    response_time = time.time() - start_time
                    
                    if result and result.get("attention_image"):
                        try:
                            # Decode base64 image
                            image_data = base64.b64decode(result["attention_image"])
                            image = Image.open(BytesIO(image_data))
                            
                            # STORE RESULT IN SESSION STATE - NEW!
                            st.session_state.visualization_result = {
                                'image': image,
                                'tokens': result.get("tokens", []),
                                'time': response_time,
                                'text': shared_text,
                                'layer': layer,
                                'head': head
                            }
                            
                        except Exception as e:
                            st.session_state.visualization_result = {'error': f"Error displaying image: {str(e)}"}
                    else:
                        st.session_state.visualization_result = {'error': error or 'No visualization generated'}
            else:
                st.warning("Please enter some text")
        
        # DISPLAY STORED VISUALIZATION RESULT - NEW!
        if st.session_state.visualization_result:
            if 'error' in st.session_state.visualization_result:
                st.error(f"❌ {st.session_state.visualization_result['error']}")
            else:
                st.subheader("Attention Heatmap:")
                
                # Display image with response time
                st.image(st.session_state.visualization_result['image'], use_container_width=True)
                st.caption(f"⚡ Visualization created in {st.session_state.visualization_result['time']:.1f}s")
                
                if st.session_state.visualization_result.get('tokens'):
                    st.caption(f"Analyzed tokens: {st.session_state.visualization_result['tokens']}")
                
                st.caption(f"Layer {st.session_state.visualization_result['layer']+1}, Head {st.session_state.visualization_result['head']+1}")
        
        # Show help text when disabled
        if buttons_disabled:
            st.caption("🔄 Button will be enabled once models finish warming up")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Built with Streamlit • Models hosted on AWS Lambda • Infrastructure managed with Terraform</p>
    </div>
    """, unsafe_allow_html=True)