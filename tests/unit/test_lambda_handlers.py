# tests/unit/test_lambda_handlers.py
"""Unit tests for Lambda handler functions"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock

class TestGenerateTextLambda:
    """Test the generate text Lambda handler"""
    
    @patch.dict(os.environ, {
        'MODEL_BUCKET': 'test-model-bucket',
        'MODEL_KEY': 'model/transformer_model.pt',
        'TOKENIZER_KEY': 'model/tokenizer.json'
    })
    @patch('boto3.client')
    def test_lambda_handler_success(self, mock_boto3, lambda_event_generate_text, 
                                  lambda_context, mock_tokenizer, mock_transformer_model):
        """Test successful text generation"""
        # Setup mocks
        mock_s3_client = Mock()
        mock_boto3.return_value = mock_s3_client
        
        with patch('tokenizer.SimpleTokenizer') as mock_tokenizer_class, \
             patch('tempfile.TemporaryDirectory') as mock_temp_dir, \
             patch('torch.load') as mock_torch_load:
            
            # Configure mocks
            mock_tokenizer_class.load.return_value = mock_tokenizer
            mock_temp_dir.return_value.__enter__.return_value = '/tmp/test'
            mock_torch_load.return_value = {'model_state_dict': {}}
            
            # Import and test the lambda handler
            sys.path.append('src/lambda_functions/generate_text')
            from main import lambda_handler
            
            # Mock the model import and creation
            with patch('main.SimpleTransformer') as mock_model_class:
                mock_model_class.return_value = mock_transformer_model
                
                response = lambda_handler(lambda_event_generate_text, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 200
        assert 'body' in response
        
        body = json.loads(response['body'])
        assert 'generated_text' in body
        assert 'prompt' in body
        assert 'settings' in body

    @patch.dict(os.environ, {
        'MODEL_BUCKET': 'test-model-bucket',
        'MODEL_KEY': 'model/transformer_model.pt',
        'TOKENIZER_KEY': 'model/tokenizer.json'
    })
    @patch('boto3.client')
    def test_lambda_handler_s3_error(self, mock_boto3, lambda_event_generate_text, lambda_context):
        """Test Lambda handler with S3 download error"""
        # Setup S3 client to raise exception
        mock_s3_client = Mock()
        mock_s3_client.download_file.side_effect = Exception("S3 download failed")
        mock_boto3.return_value = mock_s3_client
        
        sys.path.append('src/lambda_functions/generate_text')
        from main import lambda_handler
        
        response = lambda_handler(lambda_event_generate_text, lambda_context)
        
        # Should return error response
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body

    def test_lambda_handler_invalid_input(self, lambda_context):
        """Test Lambda handler with invalid input"""
        invalid_event = {
            'body': json.dumps({
                'prompt': '',  # Empty prompt
                'max_tokens': -5,  # Invalid token count
                'temperature': 5.0  # Invalid temperature
            })
        }
        
        sys.path.append('src/lambda_functions/generate_text')
        from main import lambda_handler
        
        # Should handle gracefully or validate input
        response = lambda_handler(invalid_event, lambda_context)
        assert 'statusCode' in response

class TestVisualizeAttentionLambda:
    """Test the visualize attention Lambda handler"""
    
    @patch.dict(os.environ, {
        'MODEL_BUCKET': 'test-model-bucket',
        'MODEL_KEY': 'model/transformer_model.pt',
        'TOKENIZER_KEY': 'model/tokenizer.json'
    })
    @patch('boto3.client')
    def test_warmup_request(self, mock_boto3, lambda_context):
        """Test warmup request handling"""
        warmup_event = {
            'body': json.dumps({
                'text': 'warmup',
                'layer': 0,
                'head': 0
            })
        }
        
        sys.path.append('src/lambda_functions/visualize_attention')
        from main import lambda_handler
        
        response = lambda_handler(warmup_event, lambda_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'warmed'

    @patch.dict(os.environ, {
        'MODEL_BUCKET': 'test-model-bucket',
        'MODEL_KEY': 'model/transformer_model.pt',
        'TOKENIZER_KEY': 'model/tokenizer.json'
    })
    @patch('boto3.client')
    def test_attention_visualization_success(self, mock_boto3, lambda_event_visualize_attention,
                                           lambda_context, mock_tokenizer, mock_transformer_model):
        """Test successful attention visualization"""
        # Setup mocks
        mock_s3_client = Mock()
        mock_boto3.return_value = mock_s3_client
        
        with patch('tokenizer.SimpleTokenizer') as mock_tokenizer_class, \
             patch('tempfile.TemporaryDirectory') as mock_temp_dir, \
             patch('torch.load') as mock_torch_load, \
             patch('matplotlib.pyplot.savefig') as mock_savefig, \
             patch('base64.b64encode') as mock_b64encode:
            
            # Configure mocks
            mock_tokenizer_class.load.return_value = mock_tokenizer
            mock_temp_dir.return_value.__enter__.return_value = '/tmp/test'
            mock_torch_load.return_value = {'model_state_dict': {}}
            mock_b64encode.return_value = b'fake_base64_image_data'
            
            sys.path.append('src/lambda_functions/visualize_attention')
            from main import lambda_handler
            
            with patch('main.SimpleTransformer') as mock_model_class:
                mock_model_class.return_value = mock_transformer_model
                
                response = lambda_handler(lambda_event_visualize_attention, lambda_context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'attention_image' in body or 'attention_images' in body
        assert 'tokens' in body
