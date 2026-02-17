# 💻 Backend Code: Line-by-Line Technical Documentation

This document provides a granular walkthrough of the source code within `Insurance_Policy_Summarizer_GPU.ipynb`.

---

## 1. Environment Verification (Step 1)
```python
import torch # The core deep learning library used for running the models
print(f"PyTorch version: {torch.__version__}") # Prints the version for debugging
print(f"CUDA available: {torch.cuda.is_available()}") # Checks if an NVIDIA GPU is detected
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}") # Prints specific GPU name (usually Tesla T4)
else:
    print("⚠️ No GPU detected!") # Warning if running on CPU (will be much slower)
```

---

## 2. Dependencies (Step 2)
The script uses `!pip install` and `!apt-get` to set up the Linux environment in Colab:
- `transformers`: Hugging Face library for the BART model.
- `accelerate`: Optimizes model loading onto GPU.
- `pdfplumber` & `pdf2image`: For text and image extraction from PDFs.
- `pytesseract`: Connects Python to the Tesseract OCR engine.
- `fastapi` & `uvicorn`: For creating the web server.
- `pyngrok`: Allows the local server to be accessed from a public URL.
- `en_core_web_lg`: The large English model for spaCy.

---

## 3. Model Loading (Step 3)
```python
# Imports specialized classes for Transformer models
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

MODEL_NAME = "facebook/bart-large-cnn" # Specifies the specific BART model to use
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') # Sets 'cuda' (GPU) as default

# Loads the tokenizer (converts text into numbers the model understands)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# Loads the model weights. float16 (Half Precision) is used to save GPU memory and increase speed.
model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16 if device.type == 'cuda' else torch.float32
).to(device)

model.eval() # Sets the model to 'Evaluation Mode' (disables training behaviors like dropout)
```

---

## 4. Multi-Format Extractor (Step 4)

### Data structures:
- `Clause`: A "dataclass" (container) representing a single policy paragraph, storing its ID, text, type, and risk.
- `DocumentResult`: Stores the full text of the entire document along with a list of all parsed `Clause` objects.

### `MultiFormatExtractor` Class Breakdown:
- `SUPPORTED_FORMATS`: A dictionary mapping categories to file extensions.
- `CLAUSE_TYPE_KEYWORDS`: A dictionary used to "guess" the type of clause. If a paragraph contains "payment" or "premium", it's labeled a "payment" clause.
- `extract()`: The main entry point. It identifies the file extension and calls the specific sub-method (e.g., `_extract_pdf`).
- `_segment_clauses()`: Uses a Regular Expression (`re.split`) to split the document whenever it sees a double newline or a numbered list (e.g., "1. COVERAGE").
- `_ocr_pdf()`: If a PDF is just an image (no selectable text), this converts pages to images and uses Tesseract to "read" the pixels.

---

## 5. Insurance NER Extractor (Step 5)

### `InsuranceEntity` (Data Model):
Stores what was found (e.g., "$500"), what type it is (e.g., "limit"), and exactly where it was found in the text (`start` and `end` character indices).

### `InsuranceNERExtractor` Class Breakdown:
- `ENTITY_PATTERNS`: A massive dictionary of **Regular Expressions**. 
    - Example: `\$[\d,]+` finds any dollar sign followed by numbers and commas.
- `RISK_KEYWORDS`: Categorizes risk levels. Words like "excluded" or "terminated" trigger a `critical` risk rating.
- `extract()`: 
    1. First, it uses `spaCy`'s built-in NLP to find general things like Dates and Organizations.
    2. Second, it runs all custom insurance Regex patterns to find specific items like "Deductibles".
    3. Finally, it removes duplicates to ensure the same entity isn't listed twice.
- `assess_risk()`: A simple function that returns "critical", "high", or "medium" if specific dangerous words are found in a clause.

---

## 6. GPU Summarizer (Step 6)

### `GPUSummarizer` Class Breakdown:
- `__init__`: Connects the model, tokenizer, and NER engine together.
- `summarize_document()`:
    1. Generates a summary for the **entire** document.
    2. Loops through every single `Clause`.
    3. If a clause is long (>100 chars), it generates a one-sentence summary for it.
    4. Calls the NER engine to find specific entities (money/dates) *inside* that specific clause.
- `_generate_summary()`: 
    - `self.tokenizer(...)`: Converts text to "input_ids" tensors.
    - `model.generate(...)`: This is where the AI actually "thinks" and generates the summary.
    - `num_beams=4`: Uses "Beam Search" to explore multiple variations of sentences and pick the most logical one.
    - `early_stopping=True`: Stops generating once a logical end-point is reached.

---

## 7. FastAPI Backend (Step 10)

### API Structure:
- `app = FastAPI(...)`: Initializes the web application.
- `TextRequest` & `FeedbackRequest`: Pydantic models that define exactly what data the frontend must send (e.g., a "text" string).
- `@app.post("/summarize")`: An "Endpoint". When the frontend sends text here:
    1. It calls the `extractor`.
    2. It calls the `summarizer`.
    3. It returns the results as JSON.
- `nest_asyncio.apply()`: A fix required to allow the web server to run inside a Jupyter/Colab notebook environment.
- `uvicorn.run(...)`: Starts the server on port 8080.
- `ngrok.connect(8080)`: Creates a bridge from the "outside world" to this Colab notebook, providing the URL for the Streamlit app to connect to.
