# src/lambda_functions/generate_text/main.py
import json
import os
import boto3
import torch
import tempfile

# Initialize S3 client
s3 = boto3.client('s3')

# Get environment variables
MODEL_BUCKET = os.environ['MODEL_BUCKET']
MODEL_KEY = os.environ['MODEL_KEY']
TOKENIZER_KEY = os.environ['TOKENIZER_KEY']

# Create a global variable for model and tokenizer
model = None
tokenizer = None

def load_model():
    global model, tokenizer
    
    # Download model and tokenizer from S3
    with tempfile.NamedTemporaryFile() as model_file, tempfile.NamedTemporaryFile() as tokenizer_file:
        s3.download_file(MODEL_BUCKET, MODEL_KEY, model_file.name)
        s3.download_file(MODEL_BUCKET, TOKENIZER_KEY, tokenizer_file.name)
        
        # Load model
        model = torch.load(model_file.name, map_location=torch.device('cpu'))
        model.eval()
        
        # Load tokenizer
        with open(tokenizer_file.name, 'r') as f:
            tokenizer_data = json.load(f)
            
        # Initialize tokenizer from JSON data
        # This depends on your specific tokenizer implementation
        from tokenizer import SimpleTokenizer
        tokenizer = SimpleTokenizer.from_json(tokenizer_data)

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
        
        # Generate with the model
        with torch.no_grad():
            # Modified to use your specific model's generate method
            output_ids = model.generate(
                input_tensor, 
                max_length=max_tokens,
                temperature=temperature,
                top_k=50
            )
        
        # Decode output
        generated_text = tokenizer.decode(output_ids[0].tolist())
        
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