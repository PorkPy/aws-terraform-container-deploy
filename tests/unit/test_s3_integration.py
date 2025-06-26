# tests/unit/test_s3_integration.py
"""Unit tests for S3 model loading functionality"""

import pytest
import boto3
import tempfile
import torch
import json
from moto import mock_s3
from unittest.mock import patch

class TestS3ModelLoading:
    """Test S3 model and tokenizer loading"""
    
    @mock_s3
    def test_s3_model_download(self):
        """Test downloading model from S3"""
        # Create mock S3 environment
        s3_client = boto3.client('s3', region_name='eu-west-2')
        bucket_name = 'test-transformer-model-bucket'
        
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'}
        )
        
        # Create and upload mock model
        with tempfile.NamedTemporaryFile() as tmp_file:
            mock_model_data = {
                'model_state_dict': {
                    'embedding.weight': torch.randn(1000, 256),
                    'transformer_blocks.0.self_attention.w_q.weight': torch.randn(256, 256)
                },
                'epoch': 10,
                'loss': 2.5
            }
            torch.save(mock_model_data, tmp_file.name)
            tmp_file.seek(0)
            
            s3_client.upload_file(tmp_file.name, bucket_name, 'model/transformer_model.pt')
        
        # Test download
        with tempfile.TemporaryDirectory() as tmp_dir:
            download_path = f"{tmp_dir}/downloaded_model.pt"
            s3_client.download_file(bucket_name, 'model/transformer_model.pt', download_path)
            
            # Verify downloaded model
            loaded_model = torch.load(download_path, map_location='cpu')
            assert 'model_state_dict' in loaded_model
            assert 'epoch' in loaded_model
            assert loaded_model['epoch'] == 10

    @mock_s3  
    def test_s3_tokenizer_download(self):
        """Test downloading tokenizer from S3"""
        # Create mock S3 environment
        s3_client = boto3.client('s3', region_name='eu-west-2')
        bucket_name = 'test-transformer-model-bucket'
        
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'}
        )
        
        # Create and upload mock tokenizer
        mock_tokenizer_data = {
            'vocab_size': 1000,
            'word_to_idx': {
                '<PAD>': 0, '<UNK>': 1, '<BOS>': 2, '<EOS>': 3,
                'it': 4, 'is': 5, 'a': 6, 'truth': 7
            },
            'idx_to_word': {
                0: '<PAD>', 1: '<UNK>', 2: '<BOS>', 3: '<EOS>',
                4: 'it', 5: 'is', 6: 'a', 7: 'truth'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as tmp_file:
            json.dump(mock_tokenizer_data, tmp_file)
            tmp_file.flush()
            s3_client.upload_file(tmp_file.name, bucket_name, 'model/tokenizer.json')
        
        # Test download
        with tempfile.TemporaryDirectory() as tmp_dir:
            download_path = f"{tmp_dir}/downloaded_tokenizer.json"
            s3_client.download_file(bucket_name, 'model/tokenizer.json', download_path)
            
            # Verify downloaded tokenizer
            with open(download_path, 'r') as f:
                loaded_tokenizer_data = json.load(f)
            
            assert loaded_tokenizer_data['vocab_size'] == 1000
            assert 'word_to_idx' in loaded_tokenizer_data
            assert 'idx_to_word' in loaded_tokenizer_data

    def test_s3_error_handling(self):
        """Test S3 error handling"""
        s3_client = boto3.client('s3', region_name='eu-west-2')
        
        # Test downloading from non-existent bucket
        with pytest.raises(Exception):
            with tempfile.TemporaryDirectory() as tmp_dir:
                download_path = f"{tmp_dir}/model.pt"
                s3_client.download_file('non-existent-bucket', 'model.pt', download_path)

    @mock_s3
    def test_model_loading_integration(self, mock_s3_client):
        """Test complete model loading integration"""
        # This would test the actual model loading code from your Lambda functions
        # Import the model loading functions
        
        with patch.dict('os.environ', {
            'MODEL_BUCKET': 'test-model-bucket',
            'MODEL_KEY': 'model/transformer_model.pt',
            'TOKENIZER_KEY': 'model/tokenizer.json'
        }):
            # Test the model loading process
            # This would call your actual model loading code
            pass