"""
Document Service.
Handles document CRUD operations.
"""
import os
import uuid
import shutil
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile
import logging

from app.models.document import Document, DocumentStatus
from app.models.clause import Clause
from app.models.entity import Entity
from app.models.summary import Summary
from app.schemas.document import DocumentResponse
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DocumentService:
    """Service for document operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def upload_document(self, file: UploadFile, user_id: Optional[str] = None) -> Document:
        """
        Upload and save a document.
        
        Args:
            file: Uploaded file
            user_id: Optional user ID
            
        Returns:
            Created Document instance
        """
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(settings.upload_dir, unique_filename)
        
        # Save file
        os.makedirs(settings.upload_dir, exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        file_size_str = self._format_file_size(file_size)
        
        # Create document record
        document = Document(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_type=file_ext,
            file_size=file_size_str,
            status=DocumentStatus.PENDING,
            user_id=user_id
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        logger.info(f"Document uploaded: {document.doc_id}")
        return document
    
    def get_document(self, doc_id: uuid.UUID) -> Optional[Document]:
        """Get document by ID."""
        return self.db.query(Document).filter(Document.doc_id == doc_id).first()
    
    def get_documents(
        self, 
        page: int = 1, 
        page_size: int = 10,
        user_id: Optional[str] = None
    ) -> tuple[list[Document], int]:
        """
        Get paginated list of documents.
        
        Returns:
            Tuple of (documents, total_count)
        """
        query = self.db.query(Document)
        
        if user_id:
            query = query.filter(Document.user_id == user_id)
        
        total = query.count()
        documents = (
            query
            .order_by(Document.uploaded_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        return documents, total
    
    def update_document_status(
        self, 
        doc_id: uuid.UUID, 
        status: DocumentStatus,
        error_message: Optional[str] = None
    ) -> Optional[Document]:
        """Update document processing status."""
        document = self.get_document(doc_id)
        if document:
            document.status = status
            if status == DocumentStatus.COMPLETED:
                document.processed_at = datetime.utcnow()
            if error_message:
                document.error_message = error_message
            self.db.commit()
            self.db.refresh(document)
        return document
    
    def delete_document(self, doc_id: uuid.UUID) -> bool:
        """Delete document and associated file."""
        document = self.get_document(doc_id)
        if not document:
            return False
        
        # Delete file
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete from database (cascades to clauses, entities, summaries)
        self.db.delete(document)
        self.db.commit()
        
        logger.info(f"Document deleted: {doc_id}")
        return True
    
    def get_document_with_clauses(self, doc_id: uuid.UUID) -> Optional[Document]:
        """Get document with all related data."""
        return (
            self.db.query(Document)
            .filter(Document.doc_id == doc_id)
            .first()
        )
    
    def get_clause_count(self, doc_id: uuid.UUID) -> int:
        """Get number of clauses for a document."""
        return self.db.query(Clause).filter(Clause.doc_id == doc_id).count()
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
