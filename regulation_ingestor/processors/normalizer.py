"""Text normalization and cleaning."""

import re
from typing import Optional


class Normalizer:
    """Normalizes and cleans extracted text."""
    
    def __init__(self):
        """Initialize normalizer."""
        pass
    
    def normalize(self, text: str) -> str:
        """
        Normalize and clean text content.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Normalized text
        """
        # Remove excessive whitespace
        text = self._normalize_whitespace(text)
        
        # Normalize line breaks
        text = self._normalize_line_breaks(text)
        
        # Normalize quotes
        text = self._normalize_quotes(text)
        
        # Remove special characters that might interfere
        text = self._clean_special_chars(text)
        
        return text.strip()
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace characters."""
        # Replace various whitespace characters with standard space
        text = re.sub(r'[\t\r\f\v]+', ' ', text)
        
        # Remove excessive spaces (more than 2 consecutive)
        text = re.sub(r' {3,}', ' ', text)
        
        return text
    
    def _normalize_line_breaks(self, text: str) -> str:
        """Normalize line breaks."""
        # Normalize different line break styles
        text = text.replace('\r\n', '\n')  # Windows
        text = text.replace('\r', '\n')    # Old Mac
        
        # Remove excessive newlines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def _normalize_quotes(self, text: str) -> str:
        """Normalize quote characters."""
        # Replace smart quotes with straight quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text
    
    def _clean_special_chars(self, text: str) -> str:
        """Clean special characters that might interfere with parsing."""
        # Remove zero-width characters
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
        
        # Normalize non-breaking spaces
        text = text.replace('\u00a0', ' ')
        
        return text


