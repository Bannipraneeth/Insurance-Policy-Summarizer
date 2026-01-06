"""
Clause model for storing extracted clauses from documents.
"""
import uuid
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Clause(Base):
    """Clause table model."""
    
    __tablename__ = "clauses"
    
    clause_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(UUID(as_uuid=True), ForeignKey("documents.doc_id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    section_number = Column(String(50), nullable=True)
    section_title = Column(String(255), nullable=True)
    page_number = Column(Integer, nullable=True)
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    clause_type = Column(String(100), nullable=True)  # e.g., "coverage", "exclusion", "condition"
    
    # Relationships
    document = relationship("Document", back_populates="clauses")
    entities = relationship("Entity", back_populates="clause", cascade="all, delete-orphan")
    summary = relationship("Summary", back_populates="clause", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Clause {self.section_number}>"
