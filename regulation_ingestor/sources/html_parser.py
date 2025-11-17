"""HTML parser for extracting text content from web pages."""

from bs4 import BeautifulSoup
from typing import Optional


class HTMLParser:
    """Extracts main text content from HTML documents."""
    
    def __init__(self):
        """Initialize HTML parser."""
        pass
    
    def parse(self, html_content: bytes, encoding: Optional[str] = None) -> str:
        """
        Parse HTML and extract main text content.
        
        Args:
            html_content: Raw HTML bytes
            encoding: Optional encoding (auto-detected if not provided)
            
        Returns:
            Extracted text content
        """
        # Try to detect encoding
        if encoding is None:
            encoding = self._detect_encoding(html_content)
        
        # Decode HTML
        try:
            html_text = html_content.decode(encoding)
        except UnicodeDecodeError:
            # Fallback to UTF-8
            html_text = html_content.decode("utf-8", errors="ignore")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_text, "html.parser")
        
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
        
        # Try to find main content area
        main_content = self._find_main_content(soup)
        
        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            # Fallback to body text
            body = soup.find("body")
            if body:
                text = body.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)
        
        # Clean up text
        text = self._clean_text(text)
        return text
    
    def _find_main_content(self, soup: BeautifulSoup) -> Optional:
        """Find the main content area of the page."""
        # Common selectors for main content
        selectors = [
            "main",
            "article",
            '[role="main"]',
            ".content",
            "#content",
            ".main-content",
            "#main-content",
            ".regulation-content",
            "#regulation-content",
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        lines = []
        for line in text.split("\n"):
            line = line.strip()
            if line and len(line) > 2:  # Filter out very short lines
                lines.append(line)
        
        # Join lines and normalize whitespace
        text = "\n".join(lines)
        
        # Remove excessive newlines (more than 2 consecutive)
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
        
        return text.strip()
    
    def _detect_encoding(self, content: bytes) -> str:
        """Detect encoding from HTML content."""
        # Check for charset in first 1024 bytes
        sample = content[:1024].decode("latin-1", errors="ignore")
        
        # Look for charset declaration
        if "charset=" in sample.lower():
            import re
            match = re.search(r'charset=["\']?([^"\'\s>]+)', sample, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        
        # Default to UTF-8
        return "utf-8"


