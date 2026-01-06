"""
Processing Service.
Handles document processing through the NLP pipeline.
"""
import uuid
from typing import Optional
from sqlalchemy.orm import Session
import logging
import json

from app.models.document import Document, DocumentStatus
from app.models.clause import Clause
from app.models.entity import Entity
from app.models.summary import Summary, RiskLevel
from app.nlp.pipeline import NLPPipeline, ProcessedDocument
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)


class ProcessingService:
    """Service for document NLP processing."""
    
    def __init__(self, db: Session):
        self.db = db
        self.document_service = DocumentService(db)
        self._pipeline = None
    
    def _get_pipeline(self) -> NLPPipeline:
        """Lazy load the NLP pipeline."""
        if self._pipeline is None:
            self._pipeline = NLPPipeline()
        return self._pipeline
    
    def process_document(self, doc_id: uuid.UUID) -> bool:
        """
        Process a document through the NLP pipeline.
        
        Args:
            doc_id: Document ID to process
            
        Returns:
            True if successful, False otherwise
        """
        document = self.document_service.get_document(doc_id)
        if not document:
            logger.error(f"Document not found: {doc_id}")
            return False
        
        try:
            # Update status to processing
            self.document_service.update_document_status(doc_id, DocumentStatus.PROCESSING)
            
            # Run NLP pipeline
            logger.info(f"Starting NLP processing for document: {doc_id}")
            pipeline = self._get_pipeline()
            result = pipeline.process_file(document.file_path)
            
            # Save results to database
            self._save_processing_results(doc_id, result)
            
            # Update status to completed
            self.document_service.update_document_status(doc_id, DocumentStatus.COMPLETED)
            
            logger.info(f"Document processing completed: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document {doc_id}: {e}")
            self.document_service.update_document_status(
                doc_id, 
                DocumentStatus.FAILED,
                error_message=str(e)
            )
            return False
    
    def _save_processing_results(self, doc_id: uuid.UUID, result: ProcessedDocument):
        """Save NLP processing results to database."""
        # Update document metadata
        document = self.document_service.get_document(doc_id)
        if document:
            # Safely merge metadata
            extra_metadata = result.metadata if isinstance(result.metadata, dict) else {}
            document.doc_metadata = {
                "page_count": len(result.pages),
                "clause_count": len(result.clauses),
                "char_count": len(result.text),
                **extra_metadata
            }
        
        # Save clauses, entities, and summaries
        for processed_clause in result.clauses:
            # Create clause
            clause = Clause(
                doc_id=doc_id,
                text=processed_clause.text,
                section_number=processed_clause.section_number,
                section_title=processed_clause.section_title,
                page_number=processed_clause.page_number,
                start_offset=processed_clause.start_offset,
                end_offset=processed_clause.end_offset,
                clause_type=processed_clause.clause_type
            )
            self.db.add(clause)
            self.db.flush()  # Get clause_id
            
            # Create entities
            for entity in processed_clause.entities:
                db_entity = Entity(
                    clause_id=clause.clause_id,
                    entity_type=entity.entity_type,
                    value=entity.value,
                    start_pos=entity.start_pos,
                    end_pos=entity.end_pos,
                    confidence=entity.confidence
                )
                self.db.add(db_entity)
            
            # Create summary
            if processed_clause.summary:
                risk_level = RiskLevel.LOW
                risk_indicators = ""
                
                if processed_clause.risk_assessment:
                    risk_level = RiskLevel(processed_clause.risk_assessment.level.value)
                    risk_indicators = json.dumps({
                        "indicators": processed_clause.risk_assessment.indicators,
                        "score": processed_clause.risk_assessment.score,
                        "explanation": processed_clause.risk_assessment.explanation
                    })
                
                summary = Summary(
                    clause_id=clause.clause_id,
                    summary_text=processed_clause.summary.get("summary_text", ""),
                    risk_level=risk_level,
                    risk_indicators=risk_indicators,
                    model_version=processed_clause.summary.get("model_version", ""),
                    confidence_score=processed_clause.summary.get("confidence", 1.0)
                )
                self.db.add(summary)
        
        self.db.commit()
        logger.info(f"Saved {len(result.clauses)} clauses for document {doc_id}")
    
    def get_summaries(
        self, 
        doc_id: uuid.UUID,
        risk_levels: Optional[list[str]] = None,
        entity_types: Optional[list[str]] = None,
        clause_types: Optional[list[str]] = None
    ) -> list[dict]:
        """
        Get summaries for a document with optional filtering.
        
        Returns:
            List of summary dictionaries with related data
        """
        query = (
            self.db.query(Summary, Clause)
            .join(Clause, Summary.clause_id == Clause.clause_id)
            .filter(Clause.doc_id == doc_id)
        )
        
        # Apply filters
        if risk_levels:
            risk_level_enums = [RiskLevel(level) for level in risk_levels]
            query = query.filter(Summary.risk_level.in_(risk_level_enums))
        
        if clause_types:
            query = query.filter(Clause.clause_type.in_(clause_types))
        
        results = query.order_by(Clause.start_offset).all()
        
        summaries = []
        for summary, clause in results:
            # Get entities for this clause
            entities = (
                self.db.query(Entity)
                .filter(Entity.clause_id == clause.clause_id)
                .all()
            )
            
            # Apply entity type filter
            if entity_types:
                has_matching_entity = any(e.entity_type in entity_types for e in entities)
                if not has_matching_entity:
                    continue
            
            summaries.append({
                "summary_id": str(summary.summary_id),
                "clause_id": str(clause.clause_id),
                "summary_text": summary.summary_text,
                "risk_level": summary.risk_level.value,
                "risk_indicators": summary.risk_indicators,
                "model_version": summary.model_version,
                "confidence_score": summary.confidence_score,
                "original_text": clause.text,
                "section_number": clause.section_number,
                "section_title": clause.section_title,
                "page_number": clause.page_number,
                "clause_type": clause.clause_type,
                "entities": [
                    {
                        "entity_id": str(e.entity_id),
                        "entity_type": e.entity_type,
                        "value": e.value,
                        "confidence": e.confidence
                    }
                    for e in entities
                ]
            })
        
        return summaries
