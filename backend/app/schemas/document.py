"""
Document Pydantic schemas for API request/response.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentCreate(BaseModel):
    """Schema for document creation (from upload)."""
    filename: str
    file_type: str
    

class DocumentResponse(BaseModel):
    """Schema for document response."""
    doc_id: UUID
    filename: str
    original_filename: str
    file_type: str
    file_size: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    status: DocumentStatus
    error_message: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    clause_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for paginated document list."""
    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int
