import json
import os
import boto3
import torch
import tempfile
import sys
import io
import base64
import uuid
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your model and tokenizer classes
from transformer import SimpleTransformer
from tokenizer import SimpleTokenizer

# Initialize S3 client
s3 = boto3.client('s3')

# Get environment variables
MODEL_BUCKET = os.environ['MODEL_BUCKET']
MODEL_KEY = os.environ['MODEL_KEY']
TOKENIZER_KEY = os.environ['TOKENIZER_KEY']
VISUALIZATION_BUCKET = os.environ['VISUALIZATION_BUCKET']
VISUALIZATION_PREFIX = os.environ['VISUALIZATION_PREFIX']

# Create global variables for model and tokenizer
model = None
tokenizer = None

def load_model():
    """Load model and tokenizer from S3"""
    global model, tokenizer
    
    print(f"Loading model from s3://{MODEL_BUCKET}/{MODEL_KEY}")
    print(f"Loading tokenizer from s3://{MODEL_BUCKET}/{TOKENIZER_KEY}")
    
    # Create temp directory for downloads
    tmp_dir = "/tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    
    model_path = f"{tmp_dir}/model.pt"
    tokenizer_path = f"{tmp_dir}/tokenizer.json"
    
    # Download files from S3
    s3.download_file(MODEL_BUCKET, MODEL_KEY, model_path)
    s3.download_file(MODEL_BUCKET, TOKENIZER_KEY, tokenizer_path)
    
    # Load model
    print("Loading model into memory...")
    checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
    
    # Check if checkpoint contains state_dict or is the full model
    if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
        # Create model with same parameters as during training
        model = SimpleTransformer(
            vocab_size=7100,  # Update this to match your model
            d_model=256,
            n_layers=4,
            n_heads=8,
            d_ff=1024,
            max_seq_length=128,
            dropout=0.1
        )
        model.load_state_dict(checkpoint['model_state_dict'])
    else:
        # If it's the full model
        model = checkpoint
    
    model.eval()
    print("Model loaded successfully")
    
    # Load tokenizer
    print("Loading tokenizer...")
    tokenizer = SimpleTokenizer.load(tokenizer_path)
    print("Tokenizer loaded successfully")

def visualize_attention(text, layer_idx=0, head_idx=None):
    """
    Generate attention visualization for the given text
    """
    # Tokenize input
    input_ids = tokenizer.encode(text)
    input_tensor = torch.tensor([input_ids])
    
    # Get attention weights
    with torch.no_grad():
        _, attentions = model(input_tensor)
    
    # Get tokens
    tokens = [tokenizer.idx_to_word.get(idx, '<UNK>') for idx in input_ids]
    
    # Get attention weights for specified layer
    attn = attentions[layer_idx].detach().cpu().numpy()
    
    # Create figure
    if head_idx is not None:
        # Visualize a single head
        fig, ax = plt.subplots(figsize=(10, 8))
        attention_weights = attn[0, head_idx]
        im = ax.imshow(attention_weights, cmap='viridis')
        ax.set_title(f"Layer {layer_idx+1}, Head {head_idx+1}")
        
        # Set axis labels
        ax.set_xticks(range(len(tokens)))
        ax.set_yticks(range(len(tokens)))
        ax.set_xticklabels(tokens, rotation=45, ha='right')
        ax.set_yticklabels(tokens)
        
        # Add colorbar
        plt.colorbar(im, ax=ax)
    else:
        # Create a grid of attention heads
        n_heads = attn.shape[1]
        n_cols = min(4, n_heads)
        n_rows = (n_heads + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 3 * n_rows))
        
        for i, ax in enumerate(axes.flat):
            if i < n_heads:
                attention_weights = attn[0, i]
                im = ax.imshow(attention_weights, cmap='viridis')
                ax.set_title(f"Head {i+1}")
                
                # Set axis labels if it's the first column
                if i % n_cols == 0:
                    ax.set_yticks(range(len(tokens)))
                    ax.set_yticklabels(tokens)
                else:
                    ax.set_yticks([])
                
                # Set axis labels if it's the last row
                if i >= n_heads - n_cols:
                    ax.set_xticks(range(len(tokens)))
                    ax.set_xticklabels(tokens, rotation=45, ha='right')
                else:
                    ax.set_xticks([])
            else:
                ax.axis('off')
        
        # Add colorbar
        fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.6)
    
    plt.tight_layout()
    
    # Save figure to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Generate a unique filename
    filename = f"{VISUALIZATION_PREFIX}{uuid.uuid4()}.png"
    
    # Upload to S3
    s3.upload_fileobj(buf, VISUALIZATION_BUCKET, filename, ExtraArgs={'ContentType': 'image/png', 'ACL': 'public-read'})
    
    # Generate URL
    url = f"https://{VISUALIZATION_BUCKET}.s3.amazonaws.com/{filename}"
    
    plt.close(fig)  # Close the figure to free memory
    
    return tokens, url

def lambda_handler(event, context):
    """
    Lambda handler function
    """
    # Load model if not already loaded
    if model is None or tokenizer is None:
        try:
            load_model()
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f"Failed to load model: {str(e)}"
                })
            }
    
    # Parse request
    try:
        body = json.loads(event.get('body', '{}'))
        text = body.get('text', 'The quick brown fox jumps over the lazy dog.')
        layer_idx = int(body.get('layer_idx', 0))
        head_idx = body.get('head_idx', None)
        if head_idx is not None:
            head_idx = int(head_idx)
        
        print(f"Visualizing attention for text: '{text}'")
    except Exception as e:
        print(f"Error parsing request: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f"Invalid request: {str(e)}"
            })
        }
    
    # Generate visualization
    try:
        tokens, visualization_url = visualize_attention(text, layer_idx, head_idx)
        
        # Return result
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'tokens': tokens,
                'visualization_url': visualization_url
            })
        }
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Error during visualization: {str(e)}")
        print(traceback_str)
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f"Visualization failed: {str(e)}",
                'traceback': traceback_str
            })
        }