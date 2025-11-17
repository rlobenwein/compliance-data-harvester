"""HTTP client for fetching HTML and PDF content."""

import requests
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse


class Fetcher:
    """Fetches content from URLs or local files."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize fetcher.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def fetch(self, source: str) -> Tuple[bytes, str]:
        """
        Fetch content from URL or local file.
        
        Args:
            source: URL or local file path
            
        Returns:
            Tuple of (content_bytes, content_type)
            
        Raises:
            FileNotFoundError: If local file doesn't exist
            requests.RequestException: If URL fetch fails
        """
        # Check if it's a local file
        if Path(source).exists():
            return self._fetch_local(source)
        
        # Fetch from URL
        return self._fetch_url(source)
    
    def _fetch_local(self, file_path: str) -> Tuple[bytes, str]:
        """Fetch content from local file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Local file not found: {file_path}")
        
        content = path.read_bytes()
        content_type = self._detect_content_type(path.suffix, content)
        return content, content_type
    
    def _fetch_url(self, url: str) -> Tuple[bytes, str]:
        """Fetch content from URL."""
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            content_type = self._detect_content_type_from_response(url, response)
            return response.content, content_type
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch {url}: {e}")
    
    def _detect_content_type_from_response(self, url: str, response: requests.Response) -> str:
        """Detect content type from HTTP response."""
        # Check Content-Type header
        content_type = response.headers.get("Content-Type", "").lower()
        
        if "application/pdf" in content_type or "pdf" in content_type:
            return "application/pdf"
        if "text/html" in content_type or "html" in content_type:
            return "text/html"
        
        # Fallback to URL extension
        return self._detect_content_type_from_url(url)
    
    def _detect_content_type_from_url(self, url: str) -> str:
        """Detect content type from URL extension."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if path.endswith(".pdf"):
            return "application/pdf"
        if path.endswith((".html", ".htm")):
            return "text/html"
        
        # Default to HTML for web URLs
        return "text/html"
    
    def _detect_content_type(self, extension: str, content: bytes) -> str:
        """Detect content type from file extension and content."""
        ext = extension.lower()
        
        if ext == ".pdf":
            return "application/pdf"
        if ext in (".html", ".htm"):
            return "text/html"
        
        # Try to detect from content
        if content.startswith(b"%PDF"):
            return "application/pdf"
        if b"<html" in content[:1024].lower() or b"<!doctype" in content[:1024].lower():
            return "text/html"
        
        # Default
        return "text/plain"


