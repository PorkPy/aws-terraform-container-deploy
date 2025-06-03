# model/embedding.py
import torch
import torch.nn as nn
import math

class PositionalEncoding(nn.Module):
    """
    Positional Encoding as described in "Attention is All You Need"
    """
    def __init__(self, d_model, max_seq_length=5000, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        # Create positional encoding matrix
        pe = torch.zeros(max_seq_length, d_model)
        position = torch.arange(0, max_seq_length, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        
        # Apply sine to even indices
        pe[:, 0::2] = torch.sin(position * div_term)
        # Apply cosine to odd indices
        pe[:, 1::2] = torch.cos(position * div_term)
        
        # Add batch dimension and register as buffer (not model parameter)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)
        
    def forward(self, x):
        """
        Arguments:
            x: torch.Tensor (batch_size, seq_length, d_model)
        
        Returns:
            x: torch.Tensor (batch_size, seq_length, d_model)
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)

class TransformerEmbedding(nn.Module):
    """
    Token embedding with positional encoding for transformer models
    """
    def __init__(self, vocab_size, d_model, max_seq_length=5000, dropout=0.1):
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.positional_encoding = PositionalEncoding(d_model, max_seq_length, dropout)
        self.d_model = d_model
        
    def forward(self, x):
        """
        Arguments:
            x: torch.Tensor (batch_size, seq_length) of token indices
        
        Returns:
            embeddings: torch.Tensor (batch_size, seq_length, d_model)
        """
        # Token embeddings scaled by sqrt(d_model)
        token_embeddings = self.token_embedding(x) * math.sqrt(self.d_model)
        
        # Add positional encoding
        embeddings = self.positional_encoding(token_embeddings)
        
        return embeddings