"""Extracts structured content from normalized text."""

import re
from typing import List, Optional


class Extractor:
    """Extracts articles, summaries, and guidance from text."""
    
    def __init__(self):
        """Initialize extractor."""
        # Common patterns for article markers
        self.article_patterns = [
            r'Article\s+(\d+)',  # Article 32
            r'Art\.\s*(\d+)',   # Art. 32
            r'ART\.\s*(\d+)',   # ART. 32
            r'Section\s+(\d+)',  # Section 32
            r'§\s*(\d+)',       # § 32
            r'Article\s+(\d+[a-z]?)',  # Article 32a
        ]
    
    def extract_articles(self, text: str) -> List[dict]:
        """
        Extract articles from text using regex patterns.
        
        Args:
            text: Normalized text content
            
        Returns:
            List of article dictionaries with article number, title, summary, and notes
        """
        articles = []
        
        # Find all article markers
        article_positions = []
        for pattern in self.article_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                article_num = match.group(1)
                start_pos = match.start()
                article_positions.append((start_pos, article_num, match))
        
        # Sort by position
        article_positions.sort(key=lambda x: x[0])
        
        # Extract content for each article
        for i, (pos, article_num, match) in enumerate(article_positions):
            # Find the end of this article (start of next article or end of text)
            if i + 1 < len(article_positions):
                end_pos = article_positions[i + 1][0]
            else:
                end_pos = len(text)
            
            # Extract article content
            article_text = text[pos:end_pos].strip()
            
            # Extract title (usually first line or sentence after article number)
            title = self._extract_title(article_text, article_num)
            
            # Extract summary (first paragraph or first few sentences)
            summary = self._extract_summary(article_text)
            
            articles.append({
                "article": article_num,
                "title": title,
                "summary": summary,
                "notes": None  # Can be populated later with LLM or manual input
            })
        
        return articles
    
    def _extract_title(self, article_text: str, article_num: str) -> str:
        """Extract article title from article text."""
        # Look for title patterns
        # Common: "Article 32. Security of Processing"
        title_patterns = [
            rf'Article\s+{re.escape(article_num)}\.?\s*([^\n]+)',
            rf'Art\.\s*{re.escape(article_num)}\.?\s*([^\n]+)',
            rf'Section\s+{re.escape(article_num)}\.?\s*([^\n]+)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, article_text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Clean up title (remove extra punctuation, normalize)
                title = re.sub(r'^[:\-\s]+', '', title)
                title = re.sub(r'[:\-\s]+$', '', title)
                if title and len(title) > 3:
                    return title
        
        # Fallback: use first sentence or first line
        lines = article_text.split('\n')
        for line in lines[:3]:
            line = line.strip()
            if line and len(line) > 10 and not line.startswith('Article'):
                # Take first reasonable line as title
                if len(line) < 200:  # Not too long
                    return line
        
        return f"Article {article_num}"
    
    def _extract_summary(self, article_text: str) -> str:
        """Extract summary from article text."""
        # Remove article header
        lines = article_text.split('\n')
        content_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip article header lines
            if re.match(r'^(Article|Art\.|Section)\s+\d+', line, re.IGNORECASE):
                continue
            if line:
                content_lines.append(line)
        
        # Take first paragraph or first 500 characters
        content = ' '.join(content_lines)
        
        # Try to find first sentence or paragraph
        sentences = re.split(r'[.!?]\s+', content)
        if sentences:
            summary = sentences[0]
            if len(summary) > 500:
                summary = summary[:500] + "..."
            return summary
        
        # Fallback: first 500 characters
        if len(content) > 500:
            return content[:500] + "..."
        return content
    
    def extract_summary(self, text: str, max_length: int = 500) -> str:
        """
        Extract overall summary from full text.
        
        Args:
            text: Full normalized text
            max_length: Maximum summary length
            
        Returns:
            Summary text
        """
        # Try to find introduction or preamble
        intro_patterns = [
            r'(?:introduction|preamble|overview|summary)[:\s]+(.+?)(?:\n\n|\n[A-Z])',
            r'^(.{100,500}?)(?:Article|Section|\n\n)',
        ]
        
        for pattern in intro_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                summary = match.group(1).strip()
                if len(summary) > 50:  # Minimum length
                    if len(summary) > max_length:
                        summary = summary[:max_length] + "..."
                    return summary
        
        # Fallback: first paragraph or first max_length characters
        paragraphs = text.split('\n\n')
        if paragraphs:
            summary = paragraphs[0].strip()
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
            return summary
        
        # Last resort: first max_length characters
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
    
    def extract_developer_guidance(self, text: str) -> List[str]:
        """
        Extract developer guidance points from text.
        
        For now, this is a placeholder that can be extended with:
        - LLM-based extraction
        - Keyword-based extraction
        - Manual configuration
        
        Args:
            text: Normalized text content
            
        Returns:
            List of guidance points
        """
        # Placeholder: return empty list
        # This can be extended with:
        # - LLM integration
        # - Keyword extraction (encrypt, access control, etc.)
        # - Manual configuration per regulation
        
        guidance = []
        
        # Basic keyword-based extraction (very simple)
        keywords = {
            "encrypt": "Encrypt sensitive data",
            "access control": "Enforce access control",
            "minimize": "Minimize personal data storage",
            "audit": "Maintain audit logs",
            "consent": "Obtain proper consent",
        }
        
        text_lower = text.lower()
        for keyword, guidance_text in keywords.items():
            if keyword in text_lower:
                if guidance_text not in guidance:
                    guidance.append(guidance_text)
        
        return guidance


