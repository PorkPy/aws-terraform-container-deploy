import boto3
import json
import os
import torch
import tempfile
from tokenizer import Tokenizer

# Initialize S3 client
s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda handler for text generation using a transformer model.
    The model is downloaded from S3 at runtime.
    """
    try:
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
            
        prompt = body.get('prompt', 'Hello, world!')
        max_tokens = int(body.get('max_tokens', 50))
        temperature = float(body.get('temperature', 1.0))
        
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
            
            # Load tokenizer
            tokenizer = Tokenizer(tokenizer_path)
            
            # Load model
            model = torch.load(model_path, map_location=torch.device('cpu'))
            model.eval()
            
            # Tokenize prompt
            input_ids = tokenizer.encode(prompt)
            
            # Generate text
            with torch.no_grad():
                output_ids = model.generate(
                    input_ids=torch.tensor([input_ids]), 
                    max_length=len(input_ids) + max_tokens,
                    temperature=temperature
                )[0].tolist()
            
            # Decode output
            generated_text = tokenizer.decode(output_ids)
            
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