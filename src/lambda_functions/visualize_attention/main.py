import boto3
import json
import os
import torch
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
from tokenizer import Tokenizer

# Initialize S3 client
s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda handler for visualizing transformer attention.
    The model is downloaded from S3 at runtime.
    """
    try:
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
            
        text = body.get('text', 'Hello, world!')
        
        # Get environment variables
        model_bucket = os.environ['MODEL_BUCKET']
        model_key = os.environ['MODEL_KEY']
        tokenizer_key = os.environ['TOKENIZER_KEY']
        
        # Create temp directory for downloads
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Download model and tokenizer
            model_path = f"{tmp_dir}/model.pt"
            tokenizer_path = f"{tmp_dir}/tokenizer.json"
            
            print(f"Downloading model from s3://{model_bucket}/{model_key}")
            s3.download_file(model_bucket, model_key, model_path)
            
            print(f"Downloading tokenizer from s3://{model_bucket}/{tokenizer_key}")
            s3.download_file(model_bucket, tokenizer_key, tokenizer_path)
            
            # Load tokenizer and model
            tokenizer = Tokenizer(tokenizer_path)
            model = torch.load(model_path, map_location=torch.device('cpu'))
            model.eval()
            
            # Tokenize input
            input_ids = tokenizer.encode(text)
            tokens = tokenizer.convert_ids_to_tokens(input_ids)
            
            # Get attention weights
            with torch.no_grad():
                outputs = model(torch.tensor([input_ids]), output_attentions=True)
                
            attentions = outputs.attentions
            
            # Create visualization
            attention_image = visualize_attention(tokens, attentions)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'attention_image': attention_image
                })
            }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }

def visualize_attention(tokens, attentions, layer=0, head=0):
    """Create an attention visualization image as a base64 string."""
    attention = attentions[layer][0, head].cpu().numpy()
    
    fig, ax = plt.subplots(figsize=(10, 10))
    im = ax.imshow(attention, cmap='viridis')
    
    # Set ticks and labels
    ax.set_xticks(range(len(tokens)))
    ax.set_yticks(range(len(tokens)))
    ax.set_xticklabels(tokens, rotation=90)
    ax.set_yticklabels(tokens)
    
    ax.set_title(f"Attention Layer {layer+1}, Head {head+1}")
    fig.colorbar(im)
    
    # Convert plot to base64 string
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)
    
    return image_base64