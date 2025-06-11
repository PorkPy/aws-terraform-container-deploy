# tests/unit/test_transformer.py
import pytest
import torch
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/lambda_functions/generate_text'))

def test_torch_import():
    """Test that PyTorch can be imported successfully"""
    assert torch.__version__ is not None
    assert torch.cuda.is_available() or not torch.cuda.is_available()  # Should not crash

def test_basic_tensor_operations():
    """Test basic PyTorch operations work"""
    x = torch.randn(2, 3)
    y = torch.randn(2, 3)
    z = x + y
    assert z.shape == (2, 3)