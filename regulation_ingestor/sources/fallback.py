"""Fallback orchestration for HTML → PDF → manual extraction pipeline."""

from typing import Optional
from pathlib import Path
from .fetcher import Fetcher
from .html_parser import HTMLParser
from .pdf_parser import PDFParser


class Scraper:
    """Orchestrates content fetching with fallback strategy."""
    
    def __init__(self):
        """Initialize scraper with fetcher and parsers."""
        self.fetcher = Fetcher()
        self.html_parser = HTMLParser()
        self.pdf_parser = PDFParser()
    
    def scrape(self, region_id: str, regulation_id: str, sources: list[str]) -> str:
        """
        Scrape content from sources with fallback strategy.
        
        Strategy:
        1. Try HTML sources first
        2. Try PDF sources if HTML fails
        3. If all fail, provide instructions for manual placement
        
        Args:
            region_id: Region identifier
            regulation_id: Regulation identifier
            sources: List of source URLs or file paths
            
        Returns:
            Extracted raw text content
            
        Raises:
            Exception: If all sources fail and manual placement is needed
        """
        html_sources = []
        pdf_sources = []
        
        # Categorize sources
        for source in sources:
            if self._is_pdf_source(source):
                pdf_sources.append(source)
            else:
                html_sources.append(source)
        
        # Try HTML sources first
        for source in html_sources:
            try:
                content, content_type = self.fetcher.fetch(source)
                if "html" in content_type.lower():
                    text = self.html_parser.parse(content)
                    if text and len(text.strip()) > 100:  # Minimum content check
                        return text
            except Exception as e:
                continue
        
        # Try PDF sources
        for source in pdf_sources:
            try:
                content, content_type = self.fetcher.fetch(source)
                if "pdf" in content_type.lower():
                    text = self.pdf_parser.parse(content)
                    if text and len(text.strip()) > 100:  # Minimum content check
                        return text
            except Exception as e:
                continue
        
        # Also try HTML sources as PDF (in case of misdetection)
        for source in html_sources:
            try:
                content, content_type = self.fetcher.fetch(source)
                if "pdf" in content_type.lower():
                    text = self.pdf_parser.parse(content)
                    if text and len(text.strip()) > 100:
                        return text
            except Exception:
                pass
        
        # All sources failed - provide manual instructions
        self._print_manual_instructions(region_id, regulation_id, sources)
        raise Exception(
            f"Failed to extract content from all sources for {region_id}/{regulation_id}. "
            f"See instructions above for manual placement."
        )
    
    def _is_pdf_source(self, source: str) -> bool:
        """Check if source is likely a PDF."""
        source_lower = source.lower()
        return (
            source_lower.endswith(".pdf") or
            ".pdf" in source_lower or
            "/pdf" in source_lower
        )
    
    def _print_manual_instructions(self, region_id: str, regulation_id: str, sources: list[str]):
        """Print instructions for manual PDF placement."""
        print("\n" + "=" * 70)
        print(f"MANUAL PLACEMENT REQUIRED: {region_id}/{regulation_id}")
        print("=" * 70)
        print("\nAll automated extraction methods failed.")
        print("\nSource URLs:")
        for i, source in enumerate(sources, 1):
            print(f"  {i}. {source}")
        print("\nPlease manually download the PDF and place it at:")
        print(f"  ./manual/{region_id}/{regulation_id}.pdf")
        print("\nThen re-run the scraper.")
        print("=" * 70 + "\n")


