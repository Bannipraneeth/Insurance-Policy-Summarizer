"""
Summary model for storing clause summaries and risk scores.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class RiskLevel(str, enum.Enum):
    """Risk level classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Summary(Base):
    """Summary table model."""
    
    __tablename__ = "summaries"
    
    summary_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clause_id = Column(UUID(as_uuid=True), ForeignKey("clauses.clause_id", ondelete="CASCADE"), nullable=False, unique=True)
    summary_text = Column(Text, nullable=False)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    risk_indicators = Column(Text, nullable=True)  # JSON string of indicators
    model_version = Column(String(100), nullable=True)
    confidence_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    clause = relationship("Clause", back_populates="summary")
    feedbacks = relationship("Feedback", back_populates="summary", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Summary {self.risk_level}: {self.summary_text[:50]}>"
