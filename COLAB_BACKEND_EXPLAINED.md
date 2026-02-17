# AI-Based Insurance Policy Summarizer: Backend (Colab) Documentation

This document provides a comprehensive explanation of the backend logic implemented in the `Insurance_Policy_Summarizer_GPU.ipynb` Google Colab notebook.

---

## 🛠️ Technology Stack

The backend uses a high-performance stack optimized for Natural Language Processing (NLP) and document analysis:

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Core Language** | Python 3.12 | Industry standard for AI/ML. |
| **Summarization** | `facebook/bart-large-cnn` | A state-of-the-art Transformer model pre-trained on news articles, excellent for distilling long text. |
| **NLP Engine** | `spaCy` (`en_core_web_lg`) | Used for complex tokenization and general entity recognition (e.g., Names, Dates). |
| **OCR Engine** | `Tesseract OCR` | Converts images and scanned PDFs into machine-readable text. |
| **Doc Processing** | `pdfplumber`, `python-docx`, `bs4` | Libraries to handle PDF, Word, and HTML document structures. |
| **API Framework** | `FastAPI` | High-performance web framework for the backend service. |
| **GPU Acceleration** | `PyTorch` (CUDA) | Leverages NVIDIA T4 GPUs in Colab to speed up the Transformer model by ~10-20x. |
| **Tunneling** | `pyngrok` | Exposes the local FastAPI server to the internet so the Streamlit frontend can connect. |

---

## 📖 Key Terms & Concepts

- **NER (Named Entity Recognition):** The process of automatically identifying specific "entities" like monetary amounts, insurance coverage items, and exclusions within a text.
- **Traceability:** A core feature of this project that links every generated summary point back to the specific "clause" or paragraph in the original document.
- **Clause Segmentation:** Breaking down a long insurance policy into smaller, logical "clauses" or sections based on paragraph breaks or numbering.
- **Risk Scoring:** An automated assessment of a clause's impact on the user (e.g., "Critical" for exclusions that might lead to claim denial).
- **OCR (Optical Character Recognition):** The technology used to "read" text from images or scanned "image-only" PDFs.

---

## 🏗️ Core Classes and Data Structures

### 1. `Clause` (Data Model)
Represents a single paragraph or section of the policy.
- `clause_id`: Unique identifier (e.g., C001).
- `text`: The original text of the clause.
- `clause_type`: Classified category (e.g., "Coverage", "Exclusion").
- `risk_level`: Severity rating (Low to Critical).
- `summary`: A concise one-sentence summary of just this clause.

### 2. `MultiFormatExtractor`
The "Gatekeeper" of the system.
- **Goal:** Take any file (PDF, DOCX, Image, Text) and return a clean `DocumentResult`.
- **Method `extract()`:** Detects file type and routes it to the correct internal method (`_extract_pdf`, `_extract_image`, etc.).
- **Method `_segment_clauses()`:** Uses Regular Expressions (Regex) to split the document into logical paragraphs.
- **Method `_classify_clause()`:** Uses keyword matching to label a clause as "Coverage", "Payment", "Dispute", etc.

### 3. `InsuranceNERExtractor`
The "Detective" of the system.
- **Goal:** Find insurance-specific information using patterns.
- **Method `extract()`:** Combines spaCy's pre-trained entities (like Money) with custom Regex patterns for things like "Deductibles", "Waiting Periods", and "Coverage Items".
- **Method `assess_risk()`:** Scans for high-impact keywords (e.g., "not covered", "pre-existing") to determine if a clause is risky.

### 4. `GPUSummarizer`
The "Brain" of the system.
- **Goal:** Generate the overall and clause-level summaries using the BART model.
- **Method `summarize_document()`:** The main orchestrator. It generates an overall summary, extracts all entities, and then loops through every clause to summarize and risk-score them.
- **Method `_generate_summary()`:** The low-level interface with the Transformer model. It tokenizes text, runs it through the GPU-powered model, and decodes the result.

---

## 🌐 FastAPI Endpoints

The notebook hosts a web server with several routes:

1. **`GET /`**: Health check to ensure the server and GPU are running.
2. **`POST /summarize`**: Accepts raw text and returns a full JSON analysis (summary + risk + entities).
3. **`POST /upload`**: Accepts a file upload, processes it, and returns the analysis.
4. **`POST /feedback`**: A placeholder for users to rate the summary (planned for future MLOps updates).

---

## 🚀 Execution Flow

1. **Dependency Install:** Installs all NLP and system libraries.
2. **Model Loading:** Loads the 400M+ parameter BART model into the T4 GPU memory.
3. **Initialization:** Creates instances of the Extractor, NER, and Summarizer classes.
4. **Testing:** Runs a sample "Hospitalization Policy" through the system to verify output.
5. **Deployment:** Starts the FastAPI server and creates a public URL via **ngrok** for external frontend access.
