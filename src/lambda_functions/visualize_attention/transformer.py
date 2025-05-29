# model/transformer.py
import torch
import torch.nn as nn
from .embedding import TransformerEmbedding
from .encoder import TransformerEncoder

class LanguageModelingHead(nn.Module):
    """
    Simple language modeling head for next token prediction
    """
    def __init__(self, d_model, vocab_size):
        super().__init__()
        self.fc = nn.Linear(d_model, vocab_size)
        
    def forward(self, x):
        """
        Arguments:
            x: torch.Tensor (batch_size, seq_length, d_model)
        
        Returns:
            logits: torch.Tensor (batch_size, seq_length, vocab_size)
        """
        return self.fc(x)

class SimpleTransformer(nn.Module):
    """
    A simple transformer model for language modeling
    """
    def __init__(
        self,
        vocab_size,
        d_model=256,
        n_layers=4,
        n_heads=8,
        d_ff=1024,
        max_seq_length=512,
        dropout=0.1
    ):
        super().__init__()
        
        self.embedding = TransformerEmbedding(vocab_size, d_model, max_seq_length, dropout)
        self.encoder = TransformerEncoder(n_layers, d_model, n_heads, d_ff, dropout)
        self.lm_head = LanguageModelingHead(d_model, vocab_size)
        
        # Initialize parameters
        self._init_parameters()
        
    def _init_parameters(self):
        """
        Initialize the parameters using a normal distribution
        with mean 0 and std 0.02, which is a common practice for transformers
        """
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.normal_(p, mean=0.0, std=0.02)
        
    def forward(self, x, mask=None):
        """
        Arguments:
            x: torch.Tensor (batch_size, seq_length) of token indices
            mask: torch.Tensor (batch_size, 1, seq_length)
                  or (batch_size, seq_length, seq_length)
        
        Returns:
            logits: torch.Tensor (batch_size, seq_length, vocab_size)
            attentions: list of torch.Tensor (batch_size, n_heads, seq_length, seq_length)
        """
        # Generate mask for padding tokens if not provided
        if mask is None:
            mask = (x != 0).unsqueeze(1).unsqueeze(2)  # Assuming 0 is the padding token
        
        # Generate causal mask for auto-regressive training
        seq_length = x.size(1)
        causal_mask = torch.triu(torch.ones((seq_length, seq_length), device=x.device), diagonal=1).bool()
        causal_mask = causal_mask.unsqueeze(0).unsqueeze(1)  # (1, 1, seq_length, seq_length)
        
        # Combine padding mask with causal mask
        if mask.dim() == 3:  # (batch_size, 1, seq_length)
            mask = mask.unsqueeze(-1) & ~causal_mask
        else:  # (batch_size, 1, seq_length, seq_length)
            mask = mask & ~causal_mask
        
        # Apply embedding layer
        embedded = self.embedding(x)
        
        # Apply encoder
        encoded, attentions = self.encoder(embedded, mask)
        
        # Apply language modeling head
        logits = self.lm_head(encoded)
        
        return logits, attentions
    
    def generate(self, prompt, max_length, temperature=1.0, top_k=50, tokenizer=None):
        """
        Generate text auto-regressively
        
        Arguments:
            prompt: List of token ids or string if tokenizer provided
            max_length: Maximum sequence length to generate
            temperature: Sampling temperature
            top_k: Sample from top k most probable tokens
            tokenizer: Optional tokenizer for string input/output
        
        Returns:
            generated_sequence: List of token ids or string if tokenizer provided
        """
        self.eval()
        
        # Convert string to token ids if tokenizer provided
        if isinstance(prompt, str) and tokenizer is not None:
            prompt = tokenizer.encode(prompt)
        
        # Convert to tensor
        if not isinstance(prompt, torch.Tensor):
            prompt = torch.tensor(prompt).unsqueeze(0)
            
        # Make sure prompt is on the correct device
        prompt = prompt.to(next(self.parameters()).device)
        
        with torch.no_grad():
            for _ in range(max_length):
                # Get the predictions
                logits, _ = self.forward(prompt)
                
                # Focus on the last token predictions
                next_token_logits = logits[:, -1, :] / temperature
                
                # Apply top-k filtering
                if top_k > 0:
                    indices_to_remove = next_token_logits < torch.topk(next_token_logits, top_k)[0][..., -1, None]
                    next_token_logits[indices_to_remove] = -float('Inf')
                
                # Sample from the filtered distribution
                probabilities = torch.nn.functional.softmax(next_token_logits, dim=-1)
                next_token = torch.multinomial(probabilities, 1)
                
                # Append the new token to the prompt
                prompt = torch.cat((prompt, next_token), dim=1)
                
                # Break if we generate an EOS token
                # (assuming tokenizer has an EOS token and its ID is known)
                if tokenizer is not None and next_token.item() == tokenizer.eos_token_id:
                    break
        
        # Convert token ids back to string if tokenizer provided
        if tokenizer is not None:
            return tokenizer.decode(prompt[0].tolist())
        
        return prompt[0].tolist()