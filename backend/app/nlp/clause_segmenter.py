"""
Clause Segmentation Module.
Detects and segments document text into individual clauses.
"""
import re
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClauseSegment:
    """Represents a detected clause."""
    text: str
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    start_offset: int = 0
    end_offset: int = 0
    clause_type: Optional[str] = None


class ClauseSegmenter:
    """Segment document text into clauses."""
    
    # Patterns for detecting section/clause boundaries
    SECTION_PATTERNS = [
        # Numbered sections: "1.", "1.1", "1.1.1", "Section 1", "Article 1"
        r'^(?:Section|Article|Clause|Part)\s*(\d+(?:\.\d+)*)',
        r'^(\d+(?:\.\d+)*)\s*[.:\-]\s*([A-Z][^.\n]*)',
        r'^(\d+(?:\.\d+)*)\s+([A-Z][^.\n]*)',
        
        # Lettered sections: "A.", "(a)", "a)"
        r'^([A-Z])\s*[.:\-]\s*([A-Z][^.\n]*)',
        r'^\(([a-z])\)\s*([A-Z][^.\n]*)',
        
        # Roman numerals: "I.", "II.", "(i)", "(ii)"
        r'^([IVX]+)\s*[.:\-]\s*([A-Z][^.\n]*)',
        r'^\(([ivx]+)\)\s*',
        
        # ALL CAPS headers
        r'^([A-Z][A-Z\s]{5,}[A-Z])\s*$',
    ]
    
    # Keywords that often start important clauses
    CLAUSE_KEYWORDS = [
        'coverage', 'exclusion', 'limitation', 'condition', 'definition',
        'obligation', 'warranty', 'indemnity', 'liability', 'termination',
        'cancellation', 'renewal', 'premium', 'deductible', 'claim',
        'notice', 'dispute', 'arbitration', 'governing law', 'amendment'
    ]
    
    # Keywords that indicate clause types
    CLAUSE_TYPE_INDICATORS = {
        'coverage': ['covers', 'coverage', 'included', 'protected', 'insured'],
        'exclusion': ['excludes', 'exclusion', 'not covered', 'except', 'excluding', 'does not cover'],
        'condition': ['condition', 'subject to', 'provided that', 'if', 'when'],
        'limitation': ['limit', 'limitation', 'maximum', 'cap', 'up to'],
        'obligation': ['must', 'shall', 'required', 'obligation', 'duty'],
        'definition': ['means', 'defined as', 'definition', 'refers to'],
        'termination': ['terminate', 'termination', 'cancel', 'end', 'expire'],
        'claim': ['claim', 'claims', 'notify', 'report', 'file']
    }
    
    def __init__(self, min_clause_length: int = 50, max_clause_length: int = 5000):
        self.min_clause_length = min_clause_length
        self.max_clause_length = max_clause_length
        self.compiled_patterns = [re.compile(p, re.MULTILINE | re.IGNORECASE) for p in self.SECTION_PATTERNS]
    
    def segment(self, text: str, pages: list[dict] = None) -> list[ClauseSegment]:
        """
        Segment text into clauses.
        
        Args:
            text: Full document text
            pages: Optional page information for tracking page numbers
            
        Returns:
            List of ClauseSegment objects
        """
        if not text or len(text.strip()) < self.min_clause_length:
            return []
        
        # Try structured segmentation first
        clauses = self._segment_by_structure(text)
        
        # If no structure found, use paragraph-based segmentation
        if len(clauses) < 2:
            clauses = self._segment_by_paragraphs(text)
        
        # Assign page numbers if page info available
        if pages:
            clauses = self._assign_page_numbers(clauses, pages)
        
        # Classify clause types
        for clause in clauses:
            clause.clause_type = self._classify_clause_type(clause.text)
        
        return clauses
    
    def _segment_by_structure(self, text: str) -> list[ClauseSegment]:
        """Segment by detecting numbered sections and headers."""
        clauses = []
        boundaries = []
        
        # Find all potential section boundaries
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                boundaries.append({
                    'start': match.start(),
                    'end': match.end(),
                    'section_number': match.group(1) if match.lastindex >= 1 else None,
                    'section_title': match.group(2) if match.lastindex >= 2 else None
                })
        
        if not boundaries:
            return []
        
        # Sort by position
        boundaries.sort(key=lambda x: x['start'])
        
        # Remove overlapping boundaries (keep the first one)
        filtered_boundaries = []
        last_end = -1
        for b in boundaries:
            if b['start'] >= last_end:
                filtered_boundaries.append(b)
                last_end = b['end']
        
        # Create clauses from boundaries
        for i, boundary in enumerate(filtered_boundaries):
            start = boundary['start']
            end = filtered_boundaries[i + 1]['start'] if i < len(filtered_boundaries) - 1 else len(text)
            
            clause_text = text[start:end].strip()
            
            if len(clause_text) >= self.min_clause_length:
                # Truncate if too long
                if len(clause_text) > self.max_clause_length:
                    clause_text = clause_text[:self.max_clause_length] + "..."
                
                clauses.append(ClauseSegment(
                    text=clause_text,
                    section_number=boundary['section_number'],
                    section_title=boundary['section_title'],
                    start_offset=start,
                    end_offset=end
                ))
        
        return clauses
    
    def _segment_by_paragraphs(self, text: str) -> list[ClauseSegment]:
        """Fallback: segment by paragraphs."""
        clauses = []
        
        # Split by double newlines
        paragraphs = re.split(r'\n\s*\n', text)
        
        offset = 0
        for para in paragraphs:
            para = para.strip()
            
            if len(para) >= self.min_clause_length:
                # Truncate if too long
                if len(para) > self.max_clause_length:
                    para = para[:self.max_clause_length] + "..."
                
                clauses.append(ClauseSegment(
                    text=para,
                    start_offset=offset,
                    end_offset=offset + len(para)
                ))
            
            offset += len(para) + 2  # Account for newlines
        
        return clauses
    
    def _assign_page_numbers(self, clauses: list[ClauseSegment], pages: list[dict]) -> list[ClauseSegment]:
        """Assign page numbers to clauses based on offset positions."""
        # Build cumulative offset map
        page_offsets = []
        cumulative = 0
        for page in pages:
            page_offsets.append({
                'page_number': page['page_number'],
                'start': cumulative,
                'end': cumulative + page.get('char_count', len(page.get('text', '')))
            })
            cumulative = page_offsets[-1]['end'] + 2  # Account for page separator
        
        # Assign pages to clauses
        for clause in clauses:
            for page_info in page_offsets:
                if page_info['start'] <= clause.start_offset < page_info['end']:
                    clause.page_number = page_info['page_number']
                    break
        
        return clauses
    
    def _classify_clause_type(self, text: str) -> Optional[str]:
        """Classify the type of clause based on keywords."""
        text_lower = text.lower()
        
        type_scores = {}
        for clause_type, keywords in self.CLAUSE_TYPE_INDICATORS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                type_scores[clause_type] = score
        
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        
        return None
