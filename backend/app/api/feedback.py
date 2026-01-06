"""
Feedback API endpoints.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.feedback import Feedback
from app.models.summary import Summary
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """Submit feedback for a summary."""
    # Verify summary exists
    summary = db.query(Summary).filter(Summary.summary_id == feedback.summary_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    # Create feedback
    db_feedback = Feedback(
        summary_id=feedback.summary_id,
        user_id=feedback.user_id,
        rating=feedback.rating,
        comment=feedback.comment
    )
    
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback


@router.get("/summary/{summary_id}")
async def get_summary_feedback(
    summary_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all feedback for a summary."""
    feedbacks = (
        db.query(Feedback)
        .filter(Feedback.summary_id == summary_id)
        .order_by(Feedback.created_at.desc())
        .all()
    )
    
    avg_rating = 0
    if feedbacks:
        avg_rating = sum(f.rating for f in feedbacks) / len(feedbacks)
    
    return {
        "summary_id": str(summary_id),
        "total_feedbacks": len(feedbacks),
        "average_rating": round(avg_rating, 2),
        "feedbacks": [FeedbackResponse.model_validate(f) for f in feedbacks]
    }
