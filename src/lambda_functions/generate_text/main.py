import json
import os
import boto3
import torch
import tempfile
import sys

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
        prompt = body.get('prompt', 'Once upon a time')
        temperature = float(body.get('temperature', 1.0))
        max_tokens = int(body.get('max_tokens', 50))
        top_k = int(body.get('top_k', 50))
        
        print(f"Generating text for prompt: '{prompt}'")
        print(f"Parameters: temp={temperature}, max_tokens={max_tokens}, top_k={top_k}")
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
    
    # Generate text
    try:
        # Tokenize input
        input_ids = tokenizer.encode(prompt)
        input_tensor = torch.tensor([input_ids])
        
        # Generate with the model
        with torch.no_grad():
            # Start with the input tensor
            output_tensor = input_tensor.clone()
            
            # Generate tokens one by one
            for _ in range(max_tokens):
                # Get model predictions
                logits, _ = model(output_tensor)
                
                # Get logits for the last token
                next_token_logits = logits[0, -1, :].clone()
                
                # Block UNK token
                next_token_logits[tokenizer.unk_token_id] = -float('inf')
                
                # Apply temperature
                next_token_logits = next_token_logits / temperature
                
                # Apply top-k filtering
                if top_k > 0:
                    values, _ = torch.topk(next_token_logits, top_k)
                    min_value = values[-1]
                    next_token_logits[next_token_logits < min_value] = -float('inf')
                
                # Sample from the filtered distribution
                probs = torch.nn.functional.softmax(next_token_logits, dim=-1)
                next_token = torch.multinomial(probs, 1).unsqueeze(0)
                
                # Add the sampled token to the sequence
                output_tensor = torch.cat((output_tensor, next_token), dim=1)
            
            # Decode generated text
            generated_text = tokenizer.decode(output_tensor[0].tolist())
            
            print(f"Generated text: '{generated_text}'")
        
        # Return result
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'generated_text': generated_text,
                'prompt': prompt
            })
        }
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Error during generation: {str(e)}")