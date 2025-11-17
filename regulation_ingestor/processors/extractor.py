"""Extracts structured content from normalized text."""

import re
from typing import List, Optional, Tuple


class Extractor:
    """Extracts articles, summaries, and guidance from text."""
    
    def __init__(self):
        """Initialize extractor."""
        # Patterns for article markers - must be at start of line or after newline
        # Capture lettered articles like 55-A, 55-B, etc.
        self.article_patterns = [
            r'^Art\.\s*(\d+[-\s]*[A-Z])',  # Art. 55-A (at start of line)
            r'\nArt\.\s*(\d+[-\s]*[A-Z])',  # Art. 55-A (after newline)
            r'^Article\s+(\d+[-\s]*[A-Z])',  # Article 55-A
            r'\nArticle\s+(\d+[-\s]*[A-Z])',  # Article 55-A (after newline)
            r'^ART\.\s*(\d+[-\s]*[A-Z])',  # ART. 55-A
            r'\nART\.\s*(\d+[-\s]*[A-Z])',  # ART. 55-A (after newline)
            # Also capture regular numbered articles
            r'^Art\.\s*(\d+)',  # Art. 32 (at start of line)
            r'\nArt\.\s*(\d+)(?:\s|\.|$)',  # Art. 32 (after newline, not followed by letter)
            r'^Article\s+(\d+)',  # Article 32
            r'\nArticle\s+(\d+)(?:\s|\.|$)',  # Article 32 (after newline)
            r'^ART\.\s*(\d+)',  # ART. 32
            r'\nART\.\s*(\d+)(?:\s|\.|$)',  # ART. 32 (after newline)
            r'^Section\s+(\d+)',  # Section 32
            r'\nSection\s+(\d+)(?:\s|\.|$)',  # Section 32 (after newline)
        ]
        
        # Pattern to identify paragraph markers (should NOT be treated as articles)
        self.paragraph_pattern = r'^§\s*\d+[ºª]?'
        
        # Pattern to identify article references within text (should be ignored)
        # These typically appear in lowercase and within sentences
        self.reference_patterns = [
            r'[a-z]\s+art\.\s*\d+',  # lowercase "art." after lowercase letter
            r'do\s+art\.\s*\d+',  # "do art." (Portuguese: "of article")
            r'da\s+art\.\s*\d+',  # "da art." (Portuguese: "of article")
            r'nos\s+termos\s+do\s+art\.',  # "nos termos do art." (Portuguese: "in terms of article")
        ]
    
    def _is_article_reference(self, text: str, pos: int) -> bool:
        """
        Check if an article marker is actually a reference within text.
        
        Args:
            text: Full text
            pos: Position of the match
            
        Returns:
            True if this is a reference, False if it's an article header
        """
        # Check context before the match
        if pos > 0:
            before = text[max(0, pos-50):pos].lower()
            # If preceded by lowercase text or common reference phrases, it's likely a reference
            for ref_pattern in self.reference_patterns:
                if re.search(ref_pattern, before):
                    return True
            # If preceded by lowercase letter (not newline/start), likely a reference
            if pos > 0 and text[pos-1].islower():
                return True
        
        # Check if it's at start of line (more likely to be a header)
        line_start = text.rfind('\n', 0, pos) + 1
        if pos == line_start or pos == line_start + 1:  # Allow for one space
            return False
        
        # Check if preceded by sentence-ending punctuation followed by space
        if pos > 2:
            before_chars = text[max(0, pos-3):pos]
            if re.match(r'[.!?]\s+$', before_chars):
                return False
        
        # Default: if not clearly a header, be conservative and treat as reference
        return False
    
    def _normalize_article_number(self, article_num: str) -> str:
        """
        Normalize article number format.
        
        Args:
            article_num: Raw article number from regex
            
        Returns:
            Normalized article number (e.g., "55-A", "55 A" -> "55-A")
        """
        # Remove extra spaces and normalize hyphens
        article_num = re.sub(r'\s+', ' ', article_num.strip())
        article_num = re.sub(r'\s*-\s*', '-', article_num)
        article_num = re.sub(r'\s+([A-Z])', r'-\1', article_num)
        return article_num
    
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
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                article_num = match.group(1)
                start_pos = match.start()
                
                # Skip if this is actually a paragraph marker
                line_start = text.rfind('\n', 0, start_pos) + 1
                line_text = text[line_start:start_pos + 50]
                if re.match(self.paragraph_pattern, line_text, re.IGNORECASE):
                    continue
                
                # Skip if this is an article reference within text
                if self._is_article_reference(text, start_pos):
                    continue
                
                # Normalize article number
                article_num = self._normalize_article_number(article_num)
                
                article_positions.append((start_pos, article_num, match))
        
        # Remove duplicates (same position, same article number)
        seen = set()
        unique_positions = []
        for pos, article_num, match in article_positions:
            key = (pos, article_num)
            if key not in seen:
                seen.add(key)
                unique_positions.append((pos, article_num, match))
        
        # Sort by position
        unique_positions.sort(key=lambda x: x[0])
        
        # Extract content for each article
        for i, (pos, article_num, match) in enumerate(unique_positions):
            # Find the end of this article (start of next article or end of text)
            if i + 1 < len(unique_positions):
                end_pos = unique_positions[i + 1][0]
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
        # Look for title patterns - handle lettered articles
        # Escape the article number but handle hyphens
        escaped_num = re.escape(article_num).replace(r'\-', r'[-\s]*')
        title_patterns = [
            rf'Art\.\s*{escaped_num}\.?\s*([^\n]+)',
            rf'Article\s+{escaped_num}\.?\s*([^\n]+)',
            rf'Section\s+{escaped_num}\.?\s*([^\n]+)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, article_text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Clean up title (remove extra punctuation, normalize)
                title = re.sub(r'^[:\-\s]+', '', title)
                title = re.sub(r'[:\-\s]+$', '', title)
                # Remove metadata like "(Incluído pela Lei...)"
                title = re.sub(r'\s*\([^)]*\)\s*$', '', title)
                if title and len(title) > 3:
                    return title
        
        # Fallback: use first sentence or first line
        lines = article_text.split('\n')
        for line in lines[:5]:  # Check more lines for lettered articles
            line = line.strip()
            # Skip article header, paragraph markers, and empty lines
            if (line and len(line) > 10 and 
                not re.match(r'^(Article|Art\.|Section|ART\.)\s+\d+', line, re.IGNORECASE) and
                not re.match(r'^§\s*\d+', line)):
                # Take first reasonable line as title
                # Remove trailing metadata
                title = re.sub(r'\s*\([^)]*\)\s*$', '', line)
                if len(title) < 200 and len(title) > 3:  # Not too long, not too short
                    return title
        
        return f"Article {article_num}"
    
    def _extract_summary(self, article_text: str) -> str:
        """Extract summary from article text."""
        # Remove article header
        lines = article_text.split('\n')
        content_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip article header lines and paragraph markers
            if re.match(r'^(Article|Art\.|Section|ART\.)\s+\d+', line, re.IGNORECASE):
                continue
            if re.match(r'^§\s*\d+', line):
                continue
            if line:
                content_lines.append(line)
        
        # Take first paragraph or first 500 characters
        content = ' '.join(content_lines)
        
        # Remove metadata in parentheses at the end of sentences
        content = re.sub(r'\s*\([^)]*\)\s*', ' ', content)
        content = re.sub(r'\s+', ' ', content).strip()
        
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


