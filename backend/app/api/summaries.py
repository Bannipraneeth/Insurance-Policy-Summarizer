"""
Summary API endpoints.
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.document_service import DocumentService
from app.services.processing_service import ProcessingService
from app.models.summary import RiskLevel

router = APIRouter(prefix="/api/summaries", tags=["summaries"])


@router.get("/{doc_id}")
async def get_document_summaries(
    doc_id: UUID,
    risk_level: Optional[list[str]] = Query(None),
    entity_type: Optional[list[str]] = Query(None),
    clause_type: Optional[list[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get all summaries for a document.
    
    Optionally filter by:
    - risk_level: critical, high, medium, low
    - entity_type: coverage_item, exclusion, monetary_amount, etc.
    - clause_type: coverage, exclusion, condition, etc.
    """
    # Verify document exists
    document_service = DocumentService(db)
    document = document_service.get_document(doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get summaries with filters
    processing_service = ProcessingService(db)
    summaries = processing_service.get_summaries(
        doc_id,
        risk_levels=risk_level,
        entity_types=entity_type,
        clause_types=clause_type
    )
    
    # Get risk level counts for stats
    all_summaries = processing_service.get_summaries(doc_id)
    stats = {
        "total": len(all_summaries),
        "critical": sum(1 for s in all_summaries if s["risk_level"] == "critical"),
        "high": sum(1 for s in all_summaries if s["risk_level"] == "high"),
        "medium": sum(1 for s in all_summaries if s["risk_level"] == "medium"),
        "low": sum(1 for s in all_summaries if s["risk_level"] == "low")
    }
    
    return {
        "doc_id": str(doc_id),
        "document_name": document.original_filename,
        "status": document.status.value,
        "stats": stats,
        "filtered_count": len(summaries),
        "summaries": summaries
    }


@router.get("/{doc_id}/clauses")
async def get_document_clauses(
    doc_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all clauses for a document (without summaries)."""
    from app.models.clause import Clause
    
    document_service = DocumentService(db)
    document = document_service.get_document(doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    clauses = (
        db.query(Clause)
        .filter(Clause.doc_id == doc_id)
        .order_by(Clause.start_offset)
        .all()
    )
    
    return {
        "doc_id": str(doc_id),
        "total": len(clauses),
        "clauses": [
            {
                "clause_id": str(c.clause_id),
                "text": c.text,
                "section_number": c.section_number,
                "section_title": c.section_title,
                "page_number": c.page_number,
                "clause_type": c.clause_type
            }
            for c in clauses
        ]
    }


@router.get("/{doc_id}/entities")
async def get_document_entities(
    doc_id: UUID,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all entities extracted from a document."""
    from app.models.clause import Clause
    from app.models.entity import Entity
    
    document_service = DocumentService(db)
    document = document_service.get_document(doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    query = (
        db.query(Entity, Clause)
        .join(Clause, Entity.clause_id == Clause.clause_id)
        .filter(Clause.doc_id == doc_id)
    )
    
    if entity_type:
        query = query.filter(Entity.entity_type == entity_type)
    
    results = query.order_by(Entity.entity_type).all()
    
    # Group by entity type
    grouped = {}
    for entity, clause in results:
        if entity.entity_type not in grouped:
            grouped[entity.entity_type] = []
        grouped[entity.entity_type].append({
            "entity_id": str(entity.entity_id),
            "value": entity.value,
            "confidence": entity.confidence,
            "clause_id": str(clause.clause_id),
            "section_number": clause.section_number
        })
    
    return {
        "doc_id": str(doc_id),
        "total": len(results),
        "entity_types": list(grouped.keys()),
        "entities": grouped
    }
