# model/attention.py
import math

import torch
import torch.nn as nn
import torch.nn.functional as F


class ScaledDotProductAttention(nn.Module):
    """
    Scaled Dot-Product Attention mechanism as described in "Attention is All You Need"
    """

    def __init__(self, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

    def forward(self, query, key, value, mask=None):
        """
        Arguments:
            query: torch.Tensor (batch_size, n_heads, seq_length, d_k)
            key: torch.Tensor (batch_size, n_heads, seq_length, d_k)
            value: torch.Tensor (batch_size, n_heads, seq_length, d_v)
            mask: torch.Tensor (batch_size, 1, 1, seq_length)
                  or (batch_size, 1, seq_length, seq_length)

        Returns:
            output: torch.Tensor (batch_size, n_heads, seq_length, d_v)
            attention: torch.Tensor (batch_size, n_heads, seq_length, seq_length)
        """
        d_k = query.size(-1)

        # Scaled dot product attention
        scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(d_k)

        # Apply mask (if provided)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)

        # Apply softmax to get attention weights
        attention = F.softmax(scores, dim=-1)
        attention = self.dropout(attention)

        # Apply attention weights to values
        output = torch.matmul(attention, value)

        return output, attention


class MultiHeadAttention(nn.Module):
    """
    Multi-Head Attention module as described in "Attention is All You Need"
    """

    def __init__(self, d_model, n_heads, dropout=0.1):
        super().__init__()

        # Ensure d_model is divisible by n_heads
        if d_model % n_heads != 0:
            raise ValueError("d_model must be divisible by n_heads")
        
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads  # Dimension of each head's key/query
        self.d_v = d_model // n_heads  # Dimension of each head's value

        # Linear projections for Q, K, V for all heads (in a batch)
        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)

        self.attention = ScaledDotProductAttention(dropout)

        self.fc = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(d_model)

    def forward(self, q, k, v, mask=None):
        """
        Arguments:
            q: torch.Tensor (batch_size, seq_length, d_model)
            k: torch.Tensor (batch_size, seq_length, d_model)
            v: torch.Tensor (batch_size, seq_length, d_model)
            mask: torch.Tensor (batch_size, 1, seq_length)
                  or (batch_size, seq_length, seq_length)

        Returns:
            output: torch.Tensor (batch_size, seq_length, d_model)
            attention: torch.Tensor (batch_size, n_heads, seq_length, seq_length)
        """
        batch_size = q.size(0)
        seq_length = q.size(1)
        residual = q

        # Linear projections and split into n_heads
        q = self.w_q(q).view(batch_size, seq_length, self.n_heads, self.d_k).transpose(1, 2)
        k = self.w_k(k).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        v = self.w_v(v).view(batch_size, -1, self.n_heads, self.d_v).transpose(1, 2)

        # Adjust mask dimensions for multi-head attention
        if mask is not None:
            # Ensure mask has the right shape for multi-head attention
            if mask.dim() == 3:  # (batch_size, 1, seq_length)
                mask = mask.unsqueeze(1)  # (batch_size, 1, 1, seq_length)
            elif mask.dim() == 2:  # (batch_size, seq_length)
                mask = mask.unsqueeze(1).unsqueeze(1)  # (batch_size, 1, 1, seq_length)

        # Apply scaled dot product attention
        output, attention = self.attention(q, k, v, mask)

        # Concatenate heads and apply final linear projection
        output = output.transpose(1, 2).contiguous().view(batch_size, seq_length, self.d_model)
        output = self.fc(output)
        output = self.dropout(output)

        # Add residual connection and apply layer normalization
        output = self.layer_norm(residual + output)

        return output, attention
