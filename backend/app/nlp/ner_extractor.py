"""
Named Entity Recognition Module.
Extracts domain-specific entities from insurance/legal text.
"""
import re
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """Represents an extracted entity."""
    entity_type: str
    value: str
    start_pos: int
    end_pos: int
    confidence: float = 1.0


class NERExtractor:
    """Extract named entities from insurance/legal text."""
    
    # Entity patterns for insurance domain
    ENTITY_PATTERNS = {
        'monetary_amount': [
            r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|M|B|K))?',
            r'(?:USD|EUR|GBP|INR)\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*(?:dollars|euros|pounds|rupees)',
        ],
        'percentage': [
            r'\d+(?:\.\d+)?\s*%',
            r'\d+(?:\.\d+)?\s*percent',
        ],
        'date': [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
        ],
        'time_period': [
            r'\d+\s*(?:day|days|week|weeks|month|months|year|years)',
            r'(?:annual|monthly|weekly|daily|quarterly)',
            r'within\s+\d+\s*(?:day|days|week|weeks|month|months|year|years)',
        ],
        'coverage_item': [
            r'(?:covers?|covered|coverage\s+(?:for|of))\s+([^,.]+)',
            r'(?:protection\s+(?:for|against))\s+([^,.]+)',
            r'insured\s+(?:for|against)\s+([^,.]+)',
        ],
        'exclusion': [
            r'(?:exclud(?:es?|ing|ed)|not\s+cover(?:ed)?|except(?:ing)?)\s+([^,.]+)',
            r'(?:does\s+not\s+(?:cover|include|apply))\s+([^,.]+)',
            r'exclusion[s]?\s*(?:for|of|:)\s*([^,.]+)',
        ],
        'condition': [
            r'(?:subject\s+to|provided\s+that|on\s+condition\s+that)\s+([^,.]+)',
            r'(?:if|when|unless)\s+([^,.]+)',
        ],
        'deductible': [
            r'deductible\s*(?:of|:)?\s*\$?[\d,]+(?:\.\d{2})?',
            r'\$?[\d,]+(?:\.\d{2})?\s*deductible',
        ],
        'limit': [
            r'(?:limit|maximum|cap)\s*(?:of|:)?\s*\$?[\d,]+(?:\.\d{2})?',
            r'up\s+to\s+\$?[\d,]+(?:\.\d{2})?',
            r'\$?[\d,]+(?:\.\d{2})?\s*(?:limit|maximum|cap)',
        ],
        'party': [
            r'(?:insurer|insurance\s+company|policyholder|insured|beneficiary|claimant)',
            r'(?:first|second|third)\s+party',
        ],
    }
    
    # Risk indicator patterns
    RISK_INDICATORS = [
        r'not\s+covered',
        r'will\s+not\s+pay',
        r'claim\s+(?:may\s+be\s+)?denied',
        r'policy\s+(?:may\s+be\s+)?(?:cancelled|terminated|voided)',
        r'forfeit',
        r'void(?:able)?',
        r'null\s+and\s+void',
        r'waive[sd]?\s+(?:right|claim)',
        r'penalty',
        r'surcharge',
        r'reduction\s+(?:in|of)\s+(?:coverage|benefits)',
    ]
    
    def __init__(self, use_spacy: bool = True):
        self.use_spacy = use_spacy
        self._nlp = None
        
        # Compile patterns
        self.compiled_patterns = {}
        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            self.compiled_patterns[entity_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
        
        self.risk_patterns = [re.compile(p, re.IGNORECASE) for p in self.RISK_INDICATORS]
    
    def _lazy_load_spacy(self):
        """Lazy load spaCy model."""
        if self._nlp is None and self.use_spacy:
            try:
                import spacy
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
                self.use_spacy = False
        return self._nlp
    
    def extract(self, text: str) -> list[ExtractedEntity]:
        """
        Extract all entities from text.
        
        Args:
            text: Input text to extract entities from
            
        Returns:
            List of ExtractedEntity objects
        """
        entities = []
        
        # Pattern-based extraction
        entities.extend(self._extract_by_patterns(text))
        
        # spaCy-based extraction for standard NER
        if self.use_spacy:
            entities.extend(self._extract_by_spacy(text))
        
        # Remove duplicates (same value and type)
        seen = set()
        unique_entities = []
        for entity in entities:
            key = (entity.entity_type, entity.value.lower().strip()[:50])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _extract_by_patterns(self, text: str) -> list[ExtractedEntity]:
        """Extract entities using regex patterns."""
        entities = []
        
        for entity_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    value = match.group(1) if match.lastindex and match.lastindex >= 1 else match.group(0)
                    value = value.strip()
                    
                    if len(value) > 2:  # Filter out very short matches
                        entities.append(ExtractedEntity(
                            entity_type=entity_type,
                            value=value[:200],  # Limit length
                            start_pos=match.start(),
                            end_pos=match.end(),
                            confidence=0.9
                        ))
        
        return entities
    
    def _extract_by_spacy(self, text: str) -> list[ExtractedEntity]:
        """Extract standard NER entities using spaCy."""
        nlp = self._lazy_load_spacy()
        if not nlp:
            return []
        
        entities = []
        
        # Process text in chunks if too long
        max_length = 100000
        if len(text) > max_length:
            text = text[:max_length]
        
        try:
            doc = nlp(text)
            
            for ent in doc.ents:
                # Map spaCy labels to our entity types
                entity_type = self._map_spacy_label(ent.label_)
                if entity_type:
                    entities.append(ExtractedEntity(
                        entity_type=entity_type,
                        value=ent.text.strip()[:200],
                        start_pos=ent.start_char,
                        end_pos=ent.end_char,
                        confidence=0.85
                    ))
        except Exception as e:
            logger.error(f"spaCy extraction error: {e}")
        
        return entities
    
    def _map_spacy_label(self, label: str) -> Optional[str]:
        """Map spaCy entity labels to our domain types."""
        mapping = {
            'MONEY': 'monetary_amount',
            'PERCENT': 'percentage',
            'DATE': 'date',
            'TIME': 'time_period',
            'ORG': 'party',
            'PERSON': 'party',
            'LAW': 'legal_reference',
            'CARDINAL': 'number',
        }
        return mapping.get(label)
    
    def extract_risk_indicators(self, text: str) -> list[str]:
        """Extract risk indicators from text."""
        indicators = []
        
        for pattern in self.risk_patterns:
            for match in pattern.finditer(text):
                indicator = match.group(0).strip()
                if indicator and indicator not in indicators:
                    indicators.append(indicator)
        
        return indicators
