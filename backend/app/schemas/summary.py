"""
Summary Pydantic schemas for API response.
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SummaryResponse(BaseModel):
    """Schema for summary response with full details."""
    summary_id: UUID
    clause_id: UUID
    summary_text: str
    risk_level: RiskLevel
    risk_indicators: Optional[str] = None
    model_version: Optional[str] = None
    confidence_score: float = 1.0
    created_at: datetime
    
    # Include related data
    original_text: Optional[str] = None
    section_number: Optional[str] = None
    entities: Optional[list] = None
    
    class Config:
        from_attributes = True


class SummaryFilter(BaseModel):
    """Schema for filtering summaries."""
    risk_levels: Optional[list[RiskLevel]] = None
    entity_types: Optional[list[str]] = None
    clause_types: Optional[list[str]] = None
    search_text: Optional[str] = None
