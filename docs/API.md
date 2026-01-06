# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, no authentication is required (JWT authentication is planned for future releases).

---

## Documents API

### Upload Document
Upload a document for AI processing.

**Endpoint:** `POST /api/documents/upload`

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (required) - The document file

**Supported File Types:**
- PDF (`.pdf`)
- Text (`.txt`)
- HTML (`.html`)
- Images (`.jpg`, `.jpeg`, `.png`) - processed with OCR

**Response:**
```json
{
  "doc_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "abc123.pdf",
  "original_filename": "insurance_policy.pdf",
  "file_type": ".pdf",
  "file_size": "2.5 MB",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "status": "pending",
  "clause_count": 0
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid file type or file too large
- `500`: Server error

---

### List Documents
Get a paginated list of all documents.

**Endpoint:** `GET /api/documents`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 10 | Items per page |

**Response:**
```json
{
  "documents": [
    {
      "doc_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "abc123.pdf",
      "original_filename": "insurance_policy.pdf",
      "file_type": ".pdf",
      "file_size": "2.5 MB",
      "uploaded_at": "2024-01-15T10:30:00Z",
      "processed_at": "2024-01-15T10:32:15Z",
      "status": "completed",
      "clause_count": 24
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

---

### Get Document
Get details of a specific document.

**Endpoint:** `GET /api/documents/{doc_id}`

**Path Parameters:**
- `doc_id` (UUID): Document ID

**Response:**
```json
{
  "doc_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "abc123.pdf",
  "original_filename": "insurance_policy.pdf",
  "file_type": ".pdf",
  "file_size": "2.5 MB",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "processed_at": "2024-01-15T10:32:15Z",
  "status": "completed",
  "metadata": {
    "page_count": 15,
    "clause_count": 24,
    "char_count": 45000
  },
  "clause_count": 24
}
```

---

### Delete Document
Delete a document and all associated data.

**Endpoint:** `DELETE /api/documents/{doc_id}`

**Response:**
```json
{
  "message": "Document deleted successfully"
}
```

---

### Reprocess Document
Trigger reprocessing of a document.

**Endpoint:** `POST /api/documents/{doc_id}/reprocess`

**Response:**
```json
{
  "message": "Reprocessing started",
  "doc_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Summaries API

### Get Document Summaries
Get all summaries for a document with optional filtering.

**Endpoint:** `GET /api/summaries/{doc_id}`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `risk_level` | array | Filter by risk levels: `critical`, `high`, `medium`, `low` |
| `clause_type` | array | Filter by clause types |
| `entity_type` | array | Filter by entity types |

**Example:**
```
GET /api/summaries/550e8400.../
    ?risk_level=critical&risk_level=high
    &clause_type=exclusion
```

**Response:**
```json
{
  "doc_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_name": "insurance_policy.pdf",
  "status": "completed",
  "stats": {
    "total": 24,
    "critical": 2,
    "high": 5,
    "medium": 10,
    "low": 7
  },
  "filtered_count": 7,
  "summaries": [
    {
      "summary_id": "660e8400-e29b-41d4-a716-446655440001",
      "clause_id": "770e8400-e29b-41d4-a716-446655440002",
      "summary_text": "This clause excludes coverage for pre-existing conditions diagnosed within 12 months prior to policy inception.",
      "risk_level": "high",
      "risk_indicators": "{\"indicators\": [\"excluded\", \"pre-existing\"], \"score\": 0.45}",
      "model_version": "sshleifer/distilbart-cnn-12-6",
      "confidence_score": 0.85,
      "original_text": "The Insurer shall not be liable for any claims arising from...",
      "section_number": "4.2",
      "section_title": "Exclusions",
      "page_number": 5,
      "clause_type": "exclusion",
      "entities": [
        {
          "entity_id": "880e8400-e29b-41d4-a716-446655440003",
          "entity_type": "exclusion",
          "value": "pre-existing conditions",
          "confidence": 0.92
        },
        {
          "entity_id": "990e8400-e29b-41d4-a716-446655440004",
          "entity_type": "time_period",
          "value": "12 months",
          "confidence": 0.95
        }
      ]
    }
  ]
}
```

---

### Get Document Clauses
Get raw clauses without summaries.

**Endpoint:** `GET /api/summaries/{doc_id}/clauses`

**Response:**
```json
{
  "doc_id": "550e8400-e29b-41d4-a716-446655440000",
  "total": 24,
  "clauses": [
    {
      "clause_id": "770e8400-e29b-41d4-a716-446655440002",
      "text": "The Insurer shall not be liable...",
      "section_number": "4.2",
      "section_title": "Exclusions",
      "page_number": 5,
      "clause_type": "exclusion"
    }
  ]
}
```

---

### Get Document Entities
Get all extracted entities from a document.

**Endpoint:** `GET /api/summaries/{doc_id}/entities`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_type` | string | Filter by entity type |

**Response:**
```json
{
  "doc_id": "550e8400-e29b-41d4-a716-446655440000",
  "total": 156,
  "entity_types": ["monetary_amount", "date", "coverage_item", "exclusion"],
  "entities": {
    "monetary_amount": [
      {
        "entity_id": "...",
        "value": "$50,000",
        "confidence": 0.98,
        "clause_id": "...",
        "section_number": "2.1"
      }
    ],
    "date": [...],
    "coverage_item": [...]
  }
}
```

---

## Export API

### Export as JSON
Download complete analysis as JSON.

**Endpoint:** `GET /api/export/{doc_id}/json`

**Response:** JSON file download

---

### Export as CSV
Download analysis as CSV spreadsheet.

**Endpoint:** `GET /api/export/{doc_id}/csv`

**Response:** CSV file download with columns:
- Section
- Clause Type
- Summary
- Risk Level
- Original Text
- Entities
- Confidence Score

---

### Export as PDF
Download formatted PDF report.

**Endpoint:** `GET /api/export/{doc_id}/pdf`

**Response:** PDF file download containing:
- Document information
- Risk statistics summary
- Color-coded clause summaries

---

## Feedback API

### Submit Feedback
Submit user feedback for a summary.

**Endpoint:** `POST /api/feedback`

**Request Body:**
```json
{
  "summary_id": "660e8400-e29b-41d4-a716-446655440001",
  "rating": 4,
  "comment": "Good summary but missed some details"
}
```

**Response:**
```json
{
  "feedback_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "summary_id": "660e8400-e29b-41d4-a716-446655440001",
  "rating": 4,
  "comment": "Good summary but missed some details",
  "created_at": "2024-01-15T11:00:00Z"
}
```

---

### Get Summary Feedback
Get all feedback for a specific summary.

**Endpoint:** `GET /api/feedback/summary/{summary_id}`

**Response:**
```json
{
  "summary_id": "660e8400-e29b-41d4-a716-446655440001",
  "total_feedbacks": 5,
  "average_rating": 4.2,
  "feedbacks": [
    {
      "feedback_id": "...",
      "rating": 4,
      "comment": "...",
      "created_at": "..."
    }
  ]
}
```

---

## Health Check

### Check API Health
**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

**Common Status Codes:**
- `400` - Bad Request (invalid input)
- `404` - Not Found
- `500` - Internal Server Error
