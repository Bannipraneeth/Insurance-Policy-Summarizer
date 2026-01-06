"""
Risk Scoring Module.
Analyzes clauses and assigns risk levels based on content.
"""
import re
from typing import Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk level classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RiskAssessment:
    """Risk assessment result."""
    level: RiskLevel
    score: float  # 0.0 to 1.0
    indicators: list[str]
    explanation: str


class RiskScorer:
    """Analyze and score risk levels in insurance/legal clauses."""
    
    # Risk keywords by severity
    CRITICAL_KEYWORDS = [
        'void', 'null and void', 'forfeiture', 'forfeit',
        'immediately terminate', 'no coverage', 'no liability',
        'absolve', 'waive all rights', 'irrevocable',
        'complete exclusion', 'never', 'under no circumstances'
    ]
    
    HIGH_RISK_KEYWORDS = [
        'not covered', 'excluded', 'does not cover', 'will not pay',
        'denied', 'rejection', 'refuse', 'decline',
        'terminate', 'cancel', 'suspend', 'revoke',
        'penalty', 'surcharge', 'additional charge',
        'reduced', 'reduction', 'decrease', 'diminish',
        'breach', 'violation', 'non-compliance',
        'material misrepresentation', 'fraud'
    ]
    
    MEDIUM_RISK_KEYWORDS = [
        'limit', 'limitation', 'maximum', 'cap', 'ceiling',
        'deductible', 'co-pay', 'co-payment', 'excess',
        'condition', 'conditional', 'subject to',
        'provided that', 'only if', 'unless',
        'waiting period', 'probation', 'delay',
        'pre-existing', 'prior', 'previous'
    ]
    
    LOW_RISK_KEYWORDS = [
        'coverage', 'covered', 'includes', 'included',
        'protection', 'protected', 'benefit', 'entitled',
        'guarantee', 'assured', 'warrant',
        'full', 'complete', 'comprehensive'
    ]
    
    # Negation patterns that may flip meaning
    NEGATION_PATTERNS = [
        r'not\s+', r'no\s+', r'never\s+', r"n't\s+", r'without\s+',
        r'except\s+', r'unless\s+', r'excluding\s+'
    ]
    
    # High-impact clause indicators
    HIGH_IMPACT_PHRASES = [
        'claim denial', 'policy cancellation', 'coverage termination',
        'benefit reduction', 'premium increase', 'rate hike',
        'coverage limit', 'annual maximum', 'lifetime maximum',
        'pre-authorization required', 'prior approval',
        'acts of god', 'force majeure', 'war exclusion'
    ]
    
    def __init__(self):
        # Compile patterns for efficiency
        self.critical_pattern = re.compile(
            '|'.join(re.escape(kw) for kw in self.CRITICAL_KEYWORDS),
            re.IGNORECASE
        )
        self.high_pattern = re.compile(
            '|'.join(re.escape(kw) for kw in self.HIGH_RISK_KEYWORDS),
            re.IGNORECASE
        )
        self.medium_pattern = re.compile(
            '|'.join(re.escape(kw) for kw in self.MEDIUM_RISK_KEYWORDS),
            re.IGNORECASE
        )
        self.low_pattern = re.compile(
            '|'.join(re.escape(kw) for kw in self.LOW_RISK_KEYWORDS),
            re.IGNORECASE
        )
        self.negation_pattern = re.compile(
            '|'.join(self.NEGATION_PATTERNS),
            re.IGNORECASE
        )
        self.high_impact_pattern = re.compile(
            '|'.join(re.escape(phrase) for phrase in self.HIGH_IMPACT_PHRASES),
            re.IGNORECASE
        )
    
    def assess(self, text: str, entities: list = None, clause_type: str = None) -> RiskAssessment:
        """
        Assess the risk level of a clause.
        
        Args:
            text: Clause text to analyze
            entities: Optional list of extracted entities
            clause_type: Optional clause type classification
            
        Returns:
            RiskAssessment with level, score, and indicators
        """
        if not text:
            return RiskAssessment(
                level=RiskLevel.LOW,
                score=0.0,
                indicators=[],
                explanation="Empty text"
            )
        
        text_lower = text.lower()
        indicators = []
        
        # Count keyword matches by severity
        critical_matches = self.critical_pattern.findall(text_lower)
        high_matches = self.high_pattern.findall(text_lower)
        medium_matches = self.medium_pattern.findall(text_lower)
        low_matches = self.low_pattern.findall(text_lower)
        high_impact_matches = self.high_impact_pattern.findall(text_lower)
        
        # Check for negations that might affect meaning
        negation_count = len(self.negation_pattern.findall(text_lower))
        
        # Collect unique indicators
        indicators.extend(list(set(critical_matches)))
        indicators.extend(list(set(high_matches)))
        indicators.extend(list(set(high_impact_matches)))
        
        # Calculate base score
        score = 0.0
        
        # Critical keywords: heavy weight
        if critical_matches:
            score += 0.4 * min(len(critical_matches), 3)
            
        # High-risk keywords
        if high_matches:
            score += 0.2 * min(len(high_matches), 5)
            
        # High-impact phrases
        if high_impact_matches:
            score += 0.15 * min(len(high_impact_matches), 3)
            
        # Medium-risk keywords
        if medium_matches:
            score += 0.08 * min(len(medium_matches), 5)
            
        # Adjust for clause type
        if clause_type:
            if clause_type == 'exclusion':
                score += 0.2
            elif clause_type == 'limitation':
                score += 0.15
            elif clause_type == 'condition':
                score += 0.1
            elif clause_type == 'coverage':
                score -= 0.1
        
        # Adjust for negations (could indicate restrictions)
        if negation_count > 2:
            score += 0.1
        
        # Check entities for monetary limits
        if entities:
            for entity in entities:
                if hasattr(entity, 'entity_type'):
                    if entity.entity_type in ['limit', 'deductible', 'exclusion']:
                        score += 0.05
        
        # Cap score at 1.0
        score = min(score, 1.0)
        
        # Determine level from score
        if score >= 0.7 or critical_matches:
            level = RiskLevel.CRITICAL
        elif score >= 0.4 or len(high_matches) >= 3:
            level = RiskLevel.HIGH
        elif score >= 0.2 or medium_matches:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        
        # Generate explanation
        explanation = self._generate_explanation(
            level, critical_matches, high_matches, 
            high_impact_matches, clause_type
        )
        
        return RiskAssessment(
            level=level,
            score=round(score, 3),
            indicators=indicators[:10],  # Limit to top 10
            explanation=explanation
        )
    
    def _generate_explanation(
        self,
        level: RiskLevel,
        critical_matches: list,
        high_matches: list,
        high_impact_matches: list,
        clause_type: str
    ) -> str:
        """Generate a human-readable explanation of the risk assessment."""
        parts = []
        
        if level == RiskLevel.CRITICAL:
            parts.append("This clause contains critical risk indicators")
        elif level == RiskLevel.HIGH:
            parts.append("This clause contains significant risk factors")
        elif level == RiskLevel.MEDIUM:
            parts.append("This clause contains moderate limitations or conditions")
        else:
            parts.append("This clause appears to be low risk")
        
        if clause_type:
            parts.append(f"classified as {clause_type}")
        
        if critical_matches:
            parts.append(f"with critical terms: {', '.join(list(set(critical_matches))[:3])}")
        elif high_matches:
            parts.append(f"including: {', '.join(list(set(high_matches))[:3])}")
        
        return ". ".join(parts) + "."
    
    def get_risk_color(self, level: RiskLevel) -> str:
        """Get color code for risk level (for UI display)."""
        colors = {
            RiskLevel.CRITICAL: "#FF0000",  # Red
            RiskLevel.HIGH: "#FF6600",      # Orange
            RiskLevel.MEDIUM: "#FFCC00",    # Yellow
            RiskLevel.LOW: "#00CC00"        # Green
        }
        return colors.get(level, "#808080")
