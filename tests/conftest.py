# tests/conftest.py
"""Shared pytest configuration and fixtures for the transformer ML pipeline"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import torch
import boto3
from moto.s3 import mock_s3

@pytest.fixture
def sample_pride_prejudice_text():
    """Sample text from Pride and Prejudice for testing"""
    return """It is a truth universally acknowledged, that a single man in possession 
    of a good fortune, must be in want of a wife. However little known the feelings 
    or views of such a man may be on his first entering a neighbourhood, this truth 
    is so well fixed in the minds of the surrounding families, that he is considered 
    the rightful property of some one or other of their daughters."""

@pytest.fixture
def mock_tokenizer():
    """Mock tokenizer matching your SimpleTokenizer interface"""
    tokenizer = Mock()
    tokenizer.word_to_idx = {
        '<PAD>': 0, '<UNK>': 1, '<BOS>': 2, '<EOS>': 3,
        'it': 4, 'is': 5, 'a': 6, 'truth': 7, 'universally': 8,
        'acknowledged': 9, 'that': 10, 'single': 11, 'man': 12
    }
    tokenizer.idx_to_word = {v: k for k, v in tokenizer.word_to_idx.items()}
    tokenizer.encode.return_value = [2, 4, 5, 6, 7, 8, 9, 3]  # <BOS> it is a truth universally acknowledged <EOS>
    tokenizer.decode.return_value = "it is a truth universally acknowledged"
    return tokenizer

@pytest.fixture
def mock_transformer_model():
    """Mock transformer model matching your SimpleTransformer interface"""
    model = Mock()
    model.eval.return_value = None
    
    # Mock generate method
    def mock_generate(prompt, max_length=50, temperature=1.0, top_k=50):
        # Return input + some generated tokens
        return prompt + [7, 8, 9, 10, 11]  # Add some mock generated tokens
    
    model.generate = mock_generate
    
    # Mock forward pass for attention visualization
    mock_attention = torch.randn(1, 8, 10, 10)  # [batch, heads, seq, seq]
    model.return_value = (torch.randn(1, 10, 1000), [mock_attention] * 4)  # logits, attentions
    
    return model

@pytest.fixture
def mock_s3_client():
    """Mock S3 client for testing model downloads"""
    with mock_s3():
        # Create mock S3 client
        s3_client = boto3.client('s3', region_name='eu-west-2')
        
        # Create test bucket
        bucket_name = 'test-model-bucket'
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'}
        )
        
        # Upload mock model file
        with tempfile.NamedTemporaryFile() as tmp_file:
            # Create a mock PyTorch model checkpoint
            mock_checkpoint = {
                'model_state_dict': {'embedding.weight': torch.randn(1000, 256)},
                'epoch': 10,
                'loss': 0.5
            }
            torch.save(mock_checkpoint, tmp_file.name)
            tmp_file.seek(0)
            
            s3_client.upload_file(tmp_file.name, bucket_name, 'model/transformer_model.pt')
        
        # Upload mock tokenizer file
        mock_tokenizer_data = {
            'vocab_size': 1000,
            'word_to_idx': {'<PAD>': 0, '<UNK>': 1, '<BOS>': 2, '<EOS>': 3, 'test': 4},
            'idx_to_word': {0: '<PAD>', 1: '<UNK>', 2: '<BOS>', 3: '<EOS>', 4: 'test'}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as tmp_file:
            json.dump(mock_tokenizer_data, tmp_file)
            tmp_file.flush()
            s3_client.upload_file(tmp_file.name, bucket_name, 'model/tokenizer.json')
        
        yield s3_client

@pytest.fixture
def lambda_event_generate_text():
    """Mock Lambda event for text generation"""
    return {
        'body': json.dumps({
            'prompt': 'The future of artificial intelligence',
            'max_tokens': 50,
            'temperature': 0.8,
            'top_k': 50
        }),
        'requestContext': {
            'identity': {
                'sourceIp': '192.168.1.1',
                'userAgent': 'test-agent'
            }
        }
    }

@pytest.fixture
def lambda_event_visualize_attention():
    """Mock Lambda event for attention visualization"""
    return {
        'body': json.dumps({
            'text': 'The cat sat on the mat',
            'layer': 2,
            'heads': [0, 1, 2, 3]
        })
    }

@pytest.fixture
def lambda_context():
    """Mock Lambda context"""
    context = Mock()
    context.function_name = 'test-function'
    context.function_version = '1'
    context.invoked_function_arn = 'arn:aws:lambda:eu-west-2:123456789012:function:test-function'
    context.memory_limit_in_mb = 1024
    context.remaining_time_in_millis.return_value = 30000
    context.aws_request_id = 'test-request-id'
    return context
