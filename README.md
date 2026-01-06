# 📄 AI-Based Policy & T&C Summarization System

An intelligent document analysis platform that transforms complex insurance policies and Terms & Conditions into clear, actionable summaries with risk assessment and full traceability.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- **📤 Multi-format Upload**: Support for PDF, TXT, HTML, and image files (with OCR)
- **🔍 Automatic Clause Detection**: AI-powered segmentation of document sections
- **🏷️ Entity Extraction**: Identifies coverage items, exclusions, monetary amounts, dates, parties
- **📝 Smart Summarization**: CPU-optimized transformer model (DistilBART) generates concise summaries
- **⚠️ Risk Scoring**: 4-level risk classification (Critical, High, Medium, Low) with indicators
- **🔗 Full Traceability**: Link every summary back to its original source text
- **💾 Export Options**: Download analysis as PDF, JSON, or CSV

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, SQLAlchemy, Pydantic |
| **Frontend** | Streamlit |
| **Database** | PostgreSQL |
| **Cache** | Redis |
| **NLP** | HuggingFace Transformers, spaCy |
| **Text Extraction** | pdfplumber, pytesseract, BeautifulSoup |
| **Containerization** | Docker Compose |

## 📁 Project Structure

```
Insurance Policy Summarizer/
├── backend/
│   ├── app/
│   │   ├── api/                 # REST API endpoints
│   │   │   ├── documents.py     # Document upload/management
│   │   │   ├── summaries.py     # Summary retrieval & filtering
│   │   │   ├── export.py        # PDF/JSON/CSV export
│   │   │   └── feedback.py      # User feedback
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── document.py      # Document table
│   │   │   ├── clause.py        # Clause table
│   │   │   ├── entity.py        # Entity table
│   │   │   ├── summary.py       # Summary table
│   │   │   └── feedback.py      # Feedback table
│   │   ├── nlp/                 # NLP processing pipeline
│   │   │   ├── text_extractor.py    # PDF, OCR, HTML extraction
│   │   │   ├── clause_segmenter.py  # Section detection
│   │   │   ├── ner_extractor.py     # Entity recognition
│   │   │   ├── summarizer.py        # Text summarization
│   │   │   ├── risk_scorer.py       # Risk assessment
│   │   │   └── pipeline.py          # Pipeline orchestrator
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database connection
│   │   └── main.py              # FastAPI application
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── pages/
│   │   ├── 1_Upload.py          # Document upload
│   │   ├── 2_Documents.py       # Document list
│   │   ├── 3_Summary.py         # Summary view with filtering
│   │   └── 4_Export.py          # Export downloads
│   ├── app.py                   # Main Streamlit app
│   ├── requirements.txt
│   └── .env
├── docker-compose.yml           # PostgreSQL + Redis
├── .env.example
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Docker Desktop** (for PostgreSQL and Redis)
- **Git**

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Insurance Policy Summarizer"
   ```

2. **Start Docker services**
   ```bash
   docker-compose up -d
   ```
   This starts PostgreSQL (port 5432) and Redis (port 6379).

3. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. **Set up the frontend**
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

### Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
streamlit run app.py
```

**Access the application:**
- 🎨 **Frontend**: http://localhost:8501
- 📚 **API Docs**: http://localhost:8000/docs
- 📖 **ReDoc**: http://localhost:8000/redoc

## 📡 API Endpoints

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/documents/upload` | Upload a document |
| `GET` | `/api/documents` | List all documents |
| `GET` | `/api/documents/{doc_id}` | Get document details |
| `DELETE` | `/api/documents/{doc_id}` | Delete a document |
| `POST` | `/api/documents/{doc_id}/reprocess` | Reprocess a document |

### Summaries

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/summaries/{doc_id}` | Get document summaries |
| `GET` | `/api/summaries/{doc_id}/clauses` | Get raw clauses |
| `GET` | `/api/summaries/{doc_id}/entities` | Get extracted entities |

**Query Parameters for filtering:**
- `risk_level`: Filter by risk (critical, high, medium, low)
- `clause_type`: Filter by type (coverage, exclusion, condition, etc.)
- `entity_type`: Filter by entity (monetary_amount, date, etc.)

### Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/export/{doc_id}/pdf` | Export as PDF report |
| `GET` | `/api/export/{doc_id}/json` | Export as JSON |
| `GET` | `/api/export/{doc_id}/csv` | Export as CSV |

### Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/feedback` | Submit feedback for a summary |
| `GET` | `/api/feedback/summary/{summary_id}` | Get feedback for a summary |

## 🧠 NLP Pipeline

The document processing pipeline consists of 5 stages:

```
┌─────────────┐    ┌───────────────┐    ┌──────────────┐
│   Upload    │───▶│ Text Extract  │───▶│   Segment    │
│  PDF/TXT/   │    │ pdfplumber/   │    │  Clauses     │
│  HTML/IMG   │    │ OCR/BS4       │    │              │
└─────────────┘    └───────────────┘    └──────────────┘
                                               │
       ┌───────────────────────────────────────┘
       ▼
┌──────────────┐    ┌───────────────┐    ┌──────────────┐
│     NER      │───▶│  Summarize    │───▶│ Risk Score   │
│   spaCy +    │    │  DistilBART   │    │  Keyword +   │
│   Regex      │    │  (CPU)        │    │  Rules       │
└──────────────┘    └───────────────┘    └──────────────┘
```

### Extracted Entity Types

| Entity Type | Description | Example |
|-------------|-------------|---------|
| `monetary_amount` | Dollar/currency values | $10,000, €500 |
| `percentage` | Percentage values | 20%, 0.5% |
| `date` | Specific dates | January 1, 2024 |
| `time_period` | Duration | 30 days, 12 months |
| `coverage_item` | What is covered | hospitalization, collision |
| `exclusion` | What is excluded | pre-existing conditions |
| `condition` | Requirements | must notify within 24 hours |
| `deductible` | Deductible amounts | $500 deductible |
| `limit` | Coverage limits | maximum $100,000 |
| `party` | Named parties | Policyholder, Insurer |

### Risk Levels

| Level | Color | Indicators |
|-------|-------|------------|
| 🔴 **Critical** | Red | void, forfeiture, no coverage, waive all rights |
| 🟠 **High** | Orange | excluded, terminate, penalty, breach, fraud |
| 🟡 **Medium** | Yellow | limit, deductible, condition, waiting period |
| 🟢 **Low** | Green | covered, includes, protection, benefit |

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/policy_summarizer

# Redis  
REDIS_URL=redis://localhost:6379/0

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=25

# NLP Models
SUMMARIZATION_MODEL=sshleifer/distilbart-cnn-12-6
NER_MODEL=en_core_web_sm

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

Create a `.env` file in the `frontend/` directory:

```env
BACKEND_URL=http://localhost:8000
```

## 🐳 Docker Compose Services

```yaml
services:
  db:
    image: postgres:15
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: policy_summarizer
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    volumes:
      - redis_data:/data
```

## 📊 Database Schema

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  documents   │       │   clauses    │       │   entities   │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ doc_id (PK)  │──┐    │ clause_id(PK)│──┐    │ entity_id(PK)│
│ filename     │  │    │ doc_id (FK)  │  │    │ clause_id(FK)│
│ file_path    │  └───▶│ text         │  └───▶│ entity_type  │
│ status       │       │ section_no   │       │ value        │
│ uploaded_at  │       │ clause_type  │       │ confidence   │
│ processed_at │       │ page_number  │       └──────────────┘
│ doc_metadata │       └──────────────┘
└──────────────┘              │
                              ▼
                       ┌──────────────┐       ┌──────────────┐
                       │  summaries   │       │  feedbacks   │
                       ├──────────────┤       ├──────────────┤
                       │ summary_id   │──────▶│ feedback_id  │
                       │ clause_id(FK)│       │ summary_id   │
                       │ summary_text │       │ rating       │
                       │ risk_level   │       │ comment      │
                       │ risk_indic.  │       │ created_at   │
                       │ model_version│       └──────────────┘
                       │ confidence   │
                       └──────────────┘
```

## 🔧 Troubleshooting

### Common Issues

**1. Docker containers not starting**
```bash
# Check if Docker Desktop is running
docker info

# Restart containers
docker-compose down
docker-compose up -d
```

**2. Backend won't start - Database connection error**
```bash
# Verify PostgreSQL is running
docker ps | grep postgres

# Check connection
psql -h localhost -U postgres -d policy_summarizer
```

**3. First upload is slow**
- This is normal! The first upload downloads and loads ML models (~1GB)
- Subsequent uploads will be much faster

**4. OCR not working for images**
- Install Tesseract OCR:
  - Windows: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
  - Add to PATH

## 📈 Future Enhancements

- [ ] JWT Authentication & User Management
- [ ] Celery for distributed task processing
- [ ] Fine-tuned domain-specific summarization model
- [ ] MLflow for model versioning
- [ ] Admin dashboard
- [ ] Batch document processing
- [ ] Comparison mode for multiple documents

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

**Built with ❤️ using FastAPI, Streamlit, and HuggingFace Transformers**
