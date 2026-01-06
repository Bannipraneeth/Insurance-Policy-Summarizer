"""
Document API endpoints.
"""
import os
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from app.services.document_service import DocumentService
from app.services.processing_service import ProcessingService
from app.schemas.document import DocumentResponse, DocumentListResponse

router = APIRouter(prefix="/api/documents", tags=["documents"])
settings = get_settings()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document for processing.
    
    Accepts PDF, TXT, HTML, JPG, PNG files up to 25MB.
    Processing starts automatically in the background.
    """
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not supported. Allowed: {settings.allowed_extensions}"
        )
    
    # Check file size (read in chunks to avoid memory issues)
    max_size = settings.max_file_size_mb * 1024 * 1024
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    
    # Reset file position
    await file.seek(0)
    while chunk := await file.read(chunk_size):
        file_size += len(chunk)
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
            )
    await file.seek(0)
    
    # Upload document
    document_service = DocumentService(db)
    document = await document_service.upload_document(file)
    
    # Start background processing
    processing_service = ProcessingService(db)
    background_tasks.add_task(processing_service.process_document, document.doc_id)
    
    return DocumentResponse(
        doc_id=document.doc_id,
        filename=document.filename,
        original_filename=document.original_filename,
        file_type=document.file_type,
        file_size=document.file_size,
        uploaded_at=document.uploaded_at,
        status=document.status,
        clause_count=0
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """Get paginated list of documents."""
    document_service = DocumentService(db)
    documents, total = document_service.get_documents(page, page_size)
    
    return DocumentListResponse(
        documents=[
            DocumentResponse(
                doc_id=doc.doc_id,
                filename=doc.filename,
                original_filename=doc.original_filename,
                file_type=doc.file_type,
                file_size=doc.file_size,
                uploaded_at=doc.uploaded_at,
                processed_at=doc.processed_at,
                status=doc.status,
                error_message=doc.error_message,
                clause_count=document_service.get_clause_count(doc.doc_id)
            )
            for doc in documents
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: UUID, db: Session = Depends(get_db)):
    """Get document details by ID."""
    document_service = DocumentService(db)
    document = document_service.get_document(doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        doc_id=document.doc_id,
        filename=document.filename,
        original_filename=document.original_filename,
        file_type=document.file_type,
        file_size=document.file_size,
        uploaded_at=document.uploaded_at,
        processed_at=document.processed_at,
        status=document.status,
        error_message=document.error_message,
        metadata=document.doc_metadata,
        clause_count=document_service.get_clause_count(document.doc_id)
    )


@router.delete("/{doc_id}")
async def delete_document(doc_id: UUID, db: Session = Depends(get_db)):
    """Delete a document and all associated data."""
    document_service = DocumentService(db)
    success = document_service.delete_document(doc_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}


@router.post("/{doc_id}/reprocess")
async def reprocess_document(
    doc_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Reprocess a document through the NLP pipeline."""
    document_service = DocumentService(db)
    document = document_service.get_document(doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Start background processing
    processing_service = ProcessingService(db)
    background_tasks.add_task(processing_service.process_document, doc_id)
    
    return {"message": "Reprocessing started", "doc_id": str(doc_id)}
