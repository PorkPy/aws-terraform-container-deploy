# training/tokenizer.py
import re
import os
import json
import torch
from collections import Counter

class SimpleTokenizer:
    """
    A simple tokenizer that splits text into words/subwords
    """
    def __init__(self, vocab_size=10000):
        self.vocab_size = vocab_size
        self.word_to_idx = {}
        self.idx_to_word = {}
        self.special_tokens = {
            '<PAD>': 0,
            '<UNK>': 1,
            '<BOS>': 2,
            '<EOS>': 3
        }
        
        # Initialize with special tokens
        for token, idx in self.special_tokens.items():
            self.word_to_idx[token] = idx
            self.idx_to_word[idx] = token
            
        self.pad_token_id = self.special_tokens['<PAD>']
        self.unk_token_id = self.special_tokens['<UNK>']
        self.bos_token_id = self.special_tokens['<BOS>']
        self.eos_token_id = self.special_tokens['<EOS>']
        
    def _tokenize(self, text):
        """
        Split text into tokens (simple word-level tokenization)
        """
        # Clean text and convert to lowercase
        text = text.lower()
        # Split on whitespace and punctuation
        tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
        return tokens
        
    def build_vocab(self, texts):
        """
        Build vocabulary from a list of texts
        
        Arguments:
            texts: List of strings
        """
        # Tokenize texts
        all_words = []
        for text in texts:
            words = self._tokenize(text)
            all_words.extend(words)
            
        # Count word frequencies
        counter = Counter(all_words)
        
        # Sort by frequency and take most common
        words_and_frequencies = counter.most_common(self.vocab_size - len(self.special_tokens))
        
        # Add to vocabulary
        for word, _ in words_and_frequencies:
            idx = len(self.word_to_idx)
            self.word_to_idx[word] = idx
            self.idx_to_word[idx] = word
            
        print(f"Vocabulary built with {len(self.word_to_idx)} tokens")
            
    def encode(self, text, add_special_tokens=True):
        """
        Convert text to token ids
        
        Arguments:
            text: String to encode
            add_special_tokens: Whether to add BOS and EOS tokens
            
        Returns:
            List of token ids
        """
        tokens = self._tokenize(text)
        ids = []
        
        if add_special_tokens:
            ids.append(self.bos_token_id)
            
        for token in tokens:
            ids.append(self.word_to_idx.get(token, self.unk_token_id))
            
        if add_special_tokens:
            ids.append(self.eos_token_id)
            
        return ids
    
    def decode(self, ids, skip_special_tokens=True):
        """
        Convert token ids to text
        
        Arguments:
            ids: List of token ids
            skip_special_tokens: Whether to skip special tokens like PAD, BOS, EOS
            
        Returns:
            Decoded text string
        """
        tokens = []
        for idx in ids:
            if skip_special_tokens and idx in [self.pad_token_id, self.bos_token_id, self.eos_token_id]:
                continue
            tokens.append(self.idx_to_word.get(idx, '<UNK>'))
            
        return ' '.join(tokens)
    
    def save(self, path):
        """
        Save tokenizer vocabulary to a file
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        data = {
            'vocab_size': self.vocab_size,
            'word_to_idx': self.word_to_idx,
            'idx_to_word': {int(k): v for k, v in self.idx_to_word.items()}  # Convert keys to int for JSON
        }
        
        with open(path, 'w') as f:
            json.dump(data, f)
            
    @classmethod
    def load(cls, path):
        """
        Load tokenizer vocabulary from a file
        """
        with open(path, 'r') as f:
            data = json.load(f)
            
        tokenizer = cls(vocab_size=data['vocab_size'])
        tokenizer.word_to_idx = data['word_to_idx']
        tokenizer.idx_to_word = {int(k): v for k, v in data['idx_to_word'].items()}  # Convert keys back to int
        
        return tokenizer