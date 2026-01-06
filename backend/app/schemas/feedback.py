"""
Feedback Pydantic schemas for API request/response.
"""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""
    summary_id: UUID
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = None
    user_id: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    feedback_id: UUID
    summary_id: UUID
    user_id: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
