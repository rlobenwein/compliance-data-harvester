"""PDF parser for extracting text content from PDF documents."""

from pypdf import PdfReader
from io import BytesIO
from typing import Optional


class PDFParser:
    """Extracts text content from PDF documents."""
    
    def __init__(self):
        """Initialize PDF parser."""
        pass
    
    def parse(self, pdf_content: bytes) -> str:
        """
        Parse PDF and extract text content.
        
        Args:
            pdf_content: Raw PDF bytes
            
        Returns:
            Extracted text content
            
        Raises:
            Exception: If PDF cannot be parsed (encrypted, corrupted, etc.)
        """
        try:
            pdf_file = BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            
            # Check if PDF is encrypted
            if reader.is_encrypted:
                raise Exception("PDF is encrypted and cannot be extracted without password")
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    # Skip pages that fail to extract
                    continue
            
            # Join all pages
            full_text = "\n\n".join(text_parts)
            
            # Clean up text
            full_text = self._clean_text(full_text)
            
            if not full_text.strip():
                raise Exception("No text content extracted from PDF")
            
            return full_text
            
        except Exception as e:
            raise Exception(f"Failed to parse PDF: {e}")
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted PDF text."""
        lines = []
        for line in text.split("\n"):
            line = line.strip()
            if line:
                lines.append(line)
        
        # Join lines
        text = "\n".join(lines)
        
        # Remove excessive newlines (more than 2 consecutive)
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
        
        # Normalize whitespace
        text = " ".join(text.split())  # Replace all whitespace with single space
        # But preserve paragraph breaks
        text = text.replace("  ", " ")  # Remove double spaces
        
        return text.strip()


