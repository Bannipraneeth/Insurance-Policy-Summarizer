"""
Entity model for storing NER-extracted entities.
"""
import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Entity(Base):
    """Entity table model for NER results."""
    
    __tablename__ = "entities"
    
    entity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clause_id = Column(UUID(as_uuid=True), ForeignKey("clauses.clause_id", ondelete="CASCADE"), nullable=False)
    entity_type = Column(String(100), nullable=False)  # coverage, exclusion, amount, date, party, etc.
    value = Column(String(500), nullable=False)
    start_pos = Column(Integer, nullable=True)
    end_pos = Column(Integer, nullable=True)
    confidence = Column(Float, default=1.0)
    
    # Relationships
    clause = relationship("Clause", back_populates="entities")
    
    def __repr__(self):
        return f"<Entity {self.entity_type}: {self.value[:30]}>"
