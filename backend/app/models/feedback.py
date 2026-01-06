"""
Feedback model for storing user feedback on summaries.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Feedback(Base):
    """Feedback table model."""
    
    __tablename__ = "feedbacks"
    
    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    summary_id = Column(UUID(as_uuid=True), ForeignKey("summaries.summary_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(100), nullable=True)  # For future auth
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    summary = relationship("Summary", back_populates="feedbacks")
    
    def __repr__(self):
        return f"<Feedback {self.rating}/5>"
