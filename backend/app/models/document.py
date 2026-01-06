"""
Document model for storing uploaded documents.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class DocumentStatus(str, enum.Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    """Document table model."""
    
    __tablename__ = "documents"
    
    doc_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(String(50), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    user_id = Column(String(100), nullable=True)  # For future auth
    doc_metadata = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    clauses = relationship("Clause", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document {self.filename}>"
