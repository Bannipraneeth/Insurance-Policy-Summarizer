# Developer Setup Guide

This guide provides detailed instructions for setting up the development environment.

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Ubuntu 20.04+
- **CPU**: 4 cores (8 recommended for better NLP performance)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 5GB free space
- **Python**: 3.10 or higher

### Required Software
1. **Python 3.10+** - [Download](https://www.python.org/downloads/)
2. **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/)
3. **Git** - [Download](https://git-scm.com/downloads/)

### Optional Software
- **Tesseract OCR** (for image/scanned PDF processing)
  - Windows: [Download](https://github.com/UB-Mannheim/tesseract/wiki)
  - macOS: `brew install tesseract`
  - Ubuntu: `sudo apt install tesseract-ocr`

---

## Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd "Insurance Policy Summarizer"
```

### 2. Start Docker Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Verify containers are running
docker ps
```

Expected output:
```
CONTAINER ID   IMAGE            STATUS          PORTS
xxx            postgres:15      Up 10 seconds   0.0.0.0:5432->5432/tcp
yyy            redis:7-alpine   Up 10 seconds   0.0.0.0:6379->6379/tcp
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm

# Create .env file (copy from example)
copy ..\.env.example .env  # Windows
cp ../.env.example .env    # macOS/Linux
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "BACKEND_URL=http://localhost:8000" > .env
```

### 5. Verify Installation

```bash
# Test backend imports
cd backend
python -c "from app.main import app; print('Backend OK')"

# Test spaCy
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('spaCy OK')"

# Test database connection
python -c "from app.database import engine; print('Database OK')"
```

---

## Running the Application

### Development Mode

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

### Production Mode

**Backend:**
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Frontend:**
```bash
cd frontend
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

---

## Configuration Reference

### Backend Configuration (`backend/.env`)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | string | (required) | PostgreSQL connection string |
| `REDIS_URL` | string | redis://localhost:6379/0 | Redis connection string |
| `UPLOAD_DIR` | string | ./uploads | Directory for uploaded files |
| `MAX_FILE_SIZE_MB` | int | 25 | Maximum upload file size (MB) |
| `SUMMARIZATION_MODEL` | string | sshleifer/distilbart-cnn-12-6 | HuggingFace model for summarization |
| `NER_MODEL` | string | en_core_web_sm | spaCy model for NER |
| `API_HOST` | string | 0.0.0.0 | API server host |
| `API_PORT` | int | 8000 | API server port |
| `DEBUG` | bool | True | Enable debug mode |

### Frontend Configuration (`frontend/.env`)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BACKEND_URL` | string | http://localhost:8000 | Backend API URL |

---

## Database Management

### View Database
```bash
# Connect to PostgreSQL
docker exec -it <container_id> psql -U postgres -d policy_summarizer

# List tables
\dt

# View documents
SELECT doc_id, filename, status FROM documents;
```

### Reset Database
```bash
# Stop and remove containers (data will be lost!)
docker-compose down -v

# Restart fresh
docker-compose up -d
```

### Backup Database
```bash
docker exec -t <container_id> pg_dump -U postgres policy_summarizer > backup.sql
```

---

## NLP Model Information

### Summarization Model
- **Model**: `sshleifer/distilbart-cnn-12-6`
- **Type**: DistilBART (distilled BART)
- **Size**: ~300MB
- **First load**: Downloads automatically (~1-2 minutes)
- **Memory**: ~1GB during inference

### NER Model
- **Model**: `en_core_web_sm`
- **Type**: spaCy English (small)
- **Size**: ~12MB
- **Installed via**: `python -m spacy download en_core_web_sm`

### Changing Models

To use a different summarization model, update `backend/.env`:
```env
SUMMARIZATION_MODEL=facebook/bart-large-cnn
```

**Note**: Larger models require more memory and are slower on CPU.

---

## Testing

### Run Manual Tests
```bash
cd backend

# Test text extraction
python -c "
from app.nlp.text_extractor import TextExtractor
extractor = TextExtractor()
result = extractor.extract('path/to/test.pdf')
print(f'Extracted {len(result[\"text\"])} characters')
"

# Test full pipeline
python -c "
from app.nlp.pipeline import NLPPipeline
pipeline = NLPPipeline()
result = pipeline.process_file('path/to/test.txt')
print(f'Found {len(result.clauses)} clauses')
"
```

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Upload document
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@test.pdf"

# List documents
curl http://localhost:8000/api/documents
```

---

## Troubleshooting

### Backend won't start

**Error:** `ModuleNotFoundError`
```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt
```

**Error:** `Connection refused` to database
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# If not, start it
docker-compose up -d
```

### Frontend shows "Cannot connect to backend"

1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `frontend/.env` has correct `BACKEND_URL`
3. Ensure no firewall blocking port 8000

### Document processing fails

**Error:** `'set' object is not subscriptable`
- This bug has been fixed in the latest version
- If using old code, update `risk_scorer.py`

**Error:** Model download fails
```bash
# Manually download model
python -c "
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
model_name = 'sshleifer/distilbart-cnn-12-6'
AutoTokenizer.from_pretrained(model_name)
AutoModelForSeq2SeqLM.from_pretrained(model_name)
"
```

### OCR not working

1. Install Tesseract OCR
2. Add to system PATH
3. Verify: `tesseract --version`

---

## Performance Tips

1. **First request is slow**: NLP models load on first use. Subsequent requests are faster.

2. **Large documents**: Documents with 100+ pages may take several minutes to process.

3. **Memory usage**: Monitor with `docker stats` if using containers.

4. **CPU usage**: Set `--workers 1` in production if RAM is limited.

---

## Getting Help

- Check the [API Documentation](API.md)
- Review logs: Backend logs appear in the terminal running uvicorn
- Open an issue on GitHub
