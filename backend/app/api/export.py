"""
Export API endpoints.
"""
import io
import json
import csv
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.document_service import DocumentService
from app.services.processing_service import ProcessingService

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/{doc_id}/json")
async def export_json(doc_id: UUID, db: Session = Depends(get_db)):
    """Export document analysis as JSON."""
    document_service = DocumentService(db)
    document = document_service.get_document(doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    processing_service = ProcessingService(db)
    summaries = processing_service.get_summaries(doc_id)
    
    export_data = {
        "document": {
            "doc_id": str(document.doc_id),
            "filename": document.original_filename,
            "file_type": document.file_type,
            "uploaded_at": document.uploaded_at.isoformat(),
            "processed_at": document.processed_at.isoformat() if document.processed_at else None,
            "metadata": document.doc_metadata
        },
        "statistics": {
            "total_clauses": len(summaries),
            "risk_summary": {
                "critical": sum(1 for s in summaries if s["risk_level"] == "critical"),
                "high": sum(1 for s in summaries if s["risk_level"] == "high"),
                "medium": sum(1 for s in summaries if s["risk_level"] == "medium"),
                "low": sum(1 for s in summaries if s["risk_level"] == "low")
            }
        },
        "summaries": summaries
    }
    
    json_str = json.dumps(export_data, indent=2, default=str)
    
    return StreamingResponse(
        io.BytesIO(json_str.encode()),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{document.original_filename}_analysis.json"'
        }
    )


@router.get("/{doc_id}/csv")
async def export_csv(doc_id: UUID, db: Session = Depends(get_db)):
    """Export document analysis as CSV."""
    document_service = DocumentService(db)
    document = document_service.get_document(doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    processing_service = ProcessingService(db)
    summaries = processing_service.get_summaries(doc_id)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        "Section", "Clause Type", "Summary", "Risk Level", 
        "Original Text", "Entities", "Confidence Score"
    ])
    
    # Data rows
    for s in summaries:
        entities_str = "; ".join(
            f"{e['entity_type']}: {e['value']}" 
            for e in s.get("entities", [])
        )
        writer.writerow([
            s.get("section_number", ""),
            s.get("clause_type", ""),
            s.get("summary_text", ""),
            s.get("risk_level", ""),
            s.get("original_text", "")[:500],  # Truncate long text
            entities_str,
            s.get("confidence_score", "")
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{document.original_filename}_analysis.csv"'
        }
    )


@router.get("/{doc_id}/pdf")
async def export_pdf(doc_id: UUID, db: Session = Depends(get_db)):
    """Export document analysis as PDF."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    
    document_service = DocumentService(db)
    document = document_service.get_document(doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    processing_service = ProcessingService(db)
    summaries = processing_service.get_summaries(doc_id)
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20
    )
    story.append(Paragraph(f"Analysis Report: {document.original_filename}", title_style))
    
    # Summary statistics
    stats = {
        "Total Clauses": len(summaries),
        "Critical Risk": sum(1 for s in summaries if s["risk_level"] == "critical"),
        "High Risk": sum(1 for s in summaries if s["risk_level"] == "high"),
        "Medium Risk": sum(1 for s in summaries if s["risk_level"] == "medium"),
        "Low Risk": sum(1 for s in summaries if s["risk_level"] == "low")
    }
    
    stats_data = [["Metric", "Value"]] + [[k, str(v)] for k, v in stats.items()]
    stats_table = Table(stats_data, colWidths=[2*inch, 1*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 20))
    
    # Risk color mapping
    risk_colors = {
        "critical": colors.red,
        "high": colors.orange,
        "medium": colors.yellow,
        "low": colors.green
    }
    
    # Clause summaries
    story.append(Paragraph("Clause Summaries", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    for s in summaries[:50]:  # Limit to 50 for PDF size
        # Section header
        section = s.get("section_number", "")
        clause_type = s.get("clause_type", "General")
        risk = s.get("risk_level", "low")
        
        header_text = f"<b>{section}</b> ({clause_type}) - Risk: <font color='{risk_colors.get(risk, colors.grey)}'>{risk.upper()}</font>"
        story.append(Paragraph(header_text, styles['Heading4']))
        
        # Summary text
        summary_text = s.get("summary_text", "No summary available")
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 10))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{document.original_filename}_analysis.pdf"'
        }
    )
