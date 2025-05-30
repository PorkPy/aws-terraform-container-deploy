# src/lambda_functions/visualize_attention/main.py
import json

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    text = body.get('text', 'The quick brown fox jumps over the lazy dog.')
    
    # Mock response
    tokens = text.split()
    visualization_url = "https://example.com/mock-visualization.png"
    
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