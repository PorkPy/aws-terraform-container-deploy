# src/lambda_functions/generate_text/main.py
import json

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    prompt = body.get('prompt', 'Once upon a time')
    
    # Mock response
    generated_text = f"{prompt} in a land far away, there was a princess named Elizabeth..."
    
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