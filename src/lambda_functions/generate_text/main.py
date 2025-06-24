import boto3
import json
import os
import torch
import tempfile
from tokenizer import SimpleTokenizer as Tokenizer

print(f"=== INCOMING REQUEST DEBUG ===")
print(f"Event: {json.dumps(event, default=str)}")
print(f"Source IP: {event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'Unknown')}")
print(f"User Agent: {event.get('requestContext', {}).get('identity', {}).get('userAgent', 'Unknown')}")
print(f"=== END DEBUG ===")

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
        top_k = int(body.get('top_k', 50))  # Added top_k parameter
        
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
            tokenizer = Tokenizer.load(tokenizer_path)
            
            # Load model - EXACT SAME WAY AS WORKING GENERATE_TEXT
            print("Loading model...")
            from model.transformer import SimpleTransformer
            
            # Create model with the SAME parameters
            model = SimpleTransformer(
                vocab_size=len(tokenizer.word_to_idx),
                d_model=256,
                n_layers=4,
                n_heads=8,
                d_ff=1024,
                max_seq_length=128,
                dropout=0.1
            )
            
            # Load checkpoint - EXACTLY like working generate_text
            checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
            model.load_state_dict(checkpoint['model_state_dict'])
            model.eval()
            
            print("Model loaded successfully!")
            
            # Tokenize prompt
            input_ids = tokenizer.encode(prompt)
            
            # Generate text with top_k parameter
            print("Generating text...")
            with torch.no_grad():
                output_ids = model.generate(
                    prompt=input_ids,
                    max_length=len(input_ids) + max_tokens,
                    temperature=temperature,
                    top_k=top_k  # Added top_k parameter
                )
            
            # Decode output
            generated_text = tokenizer.decode(output_ids)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'generated_text': generated_text,
                    'prompt': prompt,
                    'settings': {
                        'temperature': temperature,
                        'max_tokens': max_tokens,
                        'top_k': top_k
                    }
                })
            }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
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