# model/encoder.py
import torch
import torch.nn as nn

from .attention import MultiHeadAttention


class PositionwiseFeedForward(nn.Module):
    """
    Position-wise Feed-Forward Network as described in "Attention is All You Need"
    """

    def __init__(self, d_model, d_ff, dropout=0.1):
        super().__init__()
        self.fc1 = nn.Linear(d_model, d_ff)
        self.fc2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(d_model)
        self.activation = nn.GELU()  # Using GELU activation, common in modern transformers

    def forward(self, x):
        """
        Arguments:
            x: torch.Tensor (batch_size, seq_length, d_model)

        Returns:
            output: torch.Tensor (batch_size, seq_length, d_model)
        """
        residual = x

        # Apply feed-forward network
        x = self.fc1(x)
        x = self.activation(x)
        x = self.dropout(x)
        x = self.fc2(x)
        x = self.dropout(x)

        # Add residual connection and apply layer normalization
        output = self.layer_norm(residual + x)

        return output


class EncoderLayer(nn.Module):
    """
    Transformer Encoder Layer as described in "Attention is All You Need"
    """

    def __init__(self, d_model, n_heads, d_ff, dropout=0.1):
        super().__init__()
        self.self_attention = MultiHeadAttention(d_model, n_heads, dropout)
        self.feed_forward = PositionwiseFeedForward(d_model, d_ff, dropout)

    def forward(self, x, mask=None):
        """
        Arguments:
            x: torch.Tensor (batch_size, seq_length, d_model)
            mask: torch.Tensor (batch_size, 1, seq_length)
                  or (batch_size, seq_length, seq_length)

        Returns:
            output: torch.Tensor (batch_size, seq_length, d_model)
            attention: torch.Tensor (batch_size, n_heads, seq_length, seq_length)
        """
        # Self-attention block
        attn_output, attention = self.self_attention(x, x, x, mask)

        # Feed-forward block
        output = self.feed_forward(attn_output)

        return output, attention


class TransformerEncoder(nn.Module):
    """
    Transformer Encoder as described in "Attention is All You Need"
    """

    def __init__(self, n_layers, d_model, n_heads, d_ff, dropout=0.1):
        super().__init__()
        self.layers = nn.ModuleList(
            [EncoderLayer(d_model, n_heads, d_ff, dropout) for _ in range(n_layers)]
        )

    def forward(self, x, mask=None):
        """
        Arguments:
            x: torch.Tensor (batch_size, seq_length, d_model)
            mask: torch.Tensor (batch_size, 1, seq_length)
                  or (batch_size, seq_length, seq_length)

        Returns:
            output: torch.Tensor (batch_size, seq_length, d_model)
            attentions: list of torch.Tensor (batch_size, n_heads, seq_length, seq_length)
        """
        attentions = []

        for layer in self.layers:
            x, attention = layer(x, mask)
            attentions.append(attention)

        return x, attentions
