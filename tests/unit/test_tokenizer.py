# tests/unit/test_tokenizer.py
"""Unit tests for the SimpleTokenizer class"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch

# Import the actual tokenizer (adjust path as needed)
import sys
sys.path.append('src/lambda_functions/generate_text')
from tokenizer import SimpleTokenizer

class TestSimpleTokenizer:
    
    def test_tokenizer_initialization(self):
        """Test tokenizer initializes with correct special tokens"""
        tokenizer = SimpleTokenizer(vocab_size=1000)
        
        assert tokenizer.vocab_size == 1000
        assert tokenizer.special_tokens['<PAD>'] == 0
        assert tokenizer.special_tokens['<UNK>'] == 1
        assert tokenizer.special_tokens['<BOS>'] == 2
        assert tokenizer.special_tokens['<EOS>'] == 3
        
        # Check special tokens are in vocab
        assert '<PAD>' in tokenizer.word_to_idx
        assert '<UNK>' in tokenizer.word_to_idx
        assert '<BOS>' in tokenizer.word_to_idx
        assert '<EOS>' in tokenizer.word_to_idx

    def test_tokenize_method(self, sample_pride_prejudice_text):
        """Test the internal tokenization method"""
        tokenizer = SimpleTokenizer()
        tokens = tokenizer._tokenize(sample_pride_prejudice_text)
        
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert 'it' in tokens
        assert 'truth' in tokens
        assert 'universally' in tokens

    def test_build_vocab(self, sample_pride_prejudice_text):
        """Test vocabulary building from text"""
        tokenizer = SimpleTokenizer(vocab_size=100)
        texts = [sample_pride_prejudice_text]
        
        tokenizer.build_vocab(texts)
        
        # Should have special tokens + words from text
        assert len(tokenizer.word_to_idx) > 4
        assert 'it' in tokenizer.word_to_idx
        assert 'truth' in tokenizer.word_to_idx
        assert 'universally' in tokenizer.word_to_idx

    def test_encode_decode_symmetry(self):
        """Test encoding and decoding are symmetric"""
        tokenizer = SimpleTokenizer(vocab_size=1000)
        text = "it is a truth universally acknowledged"
        tokenizer.build_vocab([text])
        
        # Test with special tokens
        encoded = tokenizer.encode(text, add_special_tokens=True)
        decoded = tokenizer.decode(encoded, skip_special_tokens=True)
        
        assert decoded == text
        
        # Test without special tokens
        encoded_no_special = tokenizer.encode(text, add_special_tokens=False)
        decoded_no_special = tokenizer.decode(encoded_no_special, skip_special_tokens=False)
        
        assert decoded_no_special == text

    def test_unknown_token_handling(self):
        """Test handling of unknown tokens"""
        tokenizer = SimpleTokenizer(vocab_size=10)
        tokenizer.build_vocab(["known word"])
        
        # Test encoding unknown words
        encoded = tokenizer.encode("unknown mysterious words", add_special_tokens=False)
        
        # Should contain UNK tokens
        assert tokenizer.unk_token_id in encoded

    def test_save_and_load_tokenizer(self):
        """Test saving and loading tokenizer"""
        tokenizer = SimpleTokenizer(vocab_size=100)
        tokenizer.build_vocab(["test sentence for vocabulary"])
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = os.path.join(tmp_dir, "tokenizer.json")
            
            # Save tokenizer
            tokenizer.save(save_path)
            assert os.path.exists(save_path)
            
            # Load tokenizer
            loaded_tokenizer = SimpleTokenizer.load(save_path)
            
            # Check loaded tokenizer matches original
            assert loaded_tokenizer.vocab_size == tokenizer.vocab_size
            assert loaded_tokenizer.word_to_idx == tokenizer.word_to_idx
            assert loaded_tokenizer.idx_to_word == tokenizer.idx_to_word
