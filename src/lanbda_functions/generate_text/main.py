# lambda_functions/generate_text/main.py
import json
import os
import boto3
import torch
import tempfile
from tokenizer import SimpleTokenizer  # Import your tokenizer
from transformer import SimpleTransformer  # Import your model

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
    global model, tokenizer
    
    # Download model and tokenizer from S3
    with tempfile.NamedTemporaryFile() as model_file, tempfile.NamedTemporaryFile() as tokenizer_file:
        s3.download_file(MODEL_BUCKET, MODEL_KEY, model_file.name)
        s3.download_file(MODEL_BUCKET, TOKENIZER_KEY, tokenizer_file.name)
        
        # Load model - adjust based on your model format
        model = torch.load(model_file.name, map_location=torch.device('cpu'))
        model.eval()
        
        # Load tokenizer
        tokenizer = SimpleTokenizer.load(tokenizer_file.name)

def lambda_handler(event, context):
    # Load model if not already loaded
    if model is None or tokenizer is None:
        load_model()
    
    # Parse request
    try:
        body = json.loads(event['body'])
        prompt = body.get('prompt', 'Once upon a time')
        temperature = float(body.get('temperature', 1.0))
        max_tokens = int(body.get('max_tokens', 50))
        top_k = int(body.get('top_k', 50))
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Invalid request: {str(e)}'})
        }
    
    # Generate text
    try:
        # Tokenize input
        input_ids = tokenizer.encode(prompt)
        input_tensor = torch.tensor([input_ids])
        
        # Generate with the model - using the same generation logic from your app
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
        
        # Return result
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'generated_text': generated_text
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Generation failed: {str(e)}'})
        }