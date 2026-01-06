"""
Clause Pydantic schemas for API response.
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class ClauseResponse(BaseModel):
    """Schema for clause response."""
    clause_id: UUID
    doc_id: UUID
    text: str
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    clause_type: Optional[str] = None
    
    class Config:
        from_attributes = True
