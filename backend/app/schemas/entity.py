"""
Entity Pydantic schemas for API response.
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class EntityResponse(BaseModel):
    """Schema for entity response."""
    entity_id: UUID
    clause_id: UUID
    entity_type: str
    value: str
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    confidence: float = 1.0
    
    class Config:
        from_attributes = True
