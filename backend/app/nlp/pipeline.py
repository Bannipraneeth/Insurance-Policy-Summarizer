"""
NLP Pipeline Module.
Orchestrates the complete document processing pipeline.
"""
from typing import Optional
from dataclasses import dataclass, field
import logging

from app.nlp.text_extractor import TextExtractor
from app.nlp.clause_segmenter import ClauseSegmenter, ClauseSegment
from app.nlp.ner_extractor import NERExtractor, ExtractedEntity
from app.nlp.summarizer import Summarizer
from app.nlp.hf_summarizer import HFAPISummarizer
from app.nlp.risk_scorer import RiskScorer, RiskAssessment
from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ProcessedClause:
    """Complete processed clause with all NLP results."""
    text: str
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    start_offset: int = 0
    end_offset: int = 0
    clause_type: Optional[str] = None
    entities: list[ExtractedEntity] = field(default_factory=list)
    summary: Optional[dict] = None
    risk_assessment: Optional[RiskAssessment] = None


@dataclass
class ProcessedDocument:
    """Complete processed document."""
    text: str
    pages: list[dict]
    metadata: dict
    clauses: list[ProcessedClause]


class NLPPipeline:
    """
    Complete NLP processing pipeline.
    
    Pipeline steps:
    1. Text Extraction (PDF/OCR/HTML/TXT)
    2. Clause Segmentation
    3. Named Entity Recognition
    4. Summarization
    5. Risk Scoring
    """
    
    def __init__(
        self,
        summarization_model: str = "sshleifer/distilbart-cnn-12-6",
        use_spacy: bool = True,
        use_hf_api: bool = None
    ):
        """
        Initialize the NLP pipeline.
        
        Args:
            summarization_model: HuggingFace model for summarization
            use_spacy: Whether to use spaCy for NER
            use_hf_api: Use HF Inference API (auto-detects from config if None)
        """
        settings = get_settings()
        
        self.text_extractor = TextExtractor()
        self.clause_segmenter = ClauseSegmenter()
        self.ner_extractor = NERExtractor(use_spacy=use_spacy)
        self.risk_scorer = RiskScorer()
        
        # Choose summarizer based on config (HF API for cloud, local for dev)
        self.use_hf_api = use_hf_api if use_hf_api is not None else settings.use_hf_api
        
        if self.use_hf_api:
            logger.info("Using Hugging Face Inference API for summarization")
            self.summarizer = HFAPISummarizer(
                model_name=summarization_model,
                api_token=settings.hf_api_token
            )
        else:
            logger.info("Using local summarization model")
            self.summarizer = Summarizer(model_name=summarization_model)
        
        logger.info("NLP Pipeline initialized")
    
    def process_file(self, file_path: str) -> ProcessedDocument:
        """
        Process a document file through the complete pipeline.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ProcessedDocument with all extracted information
        """
        logger.info(f"Processing file: {file_path}")
        
        # Step 1: Extract text
        logger.info("Step 1: Extracting text...")
        extraction_result = self.text_extractor.extract(file_path)
        text = extraction_result['text']
        pages = extraction_result['pages']
        metadata = extraction_result['metadata']
        
        if not text:
            logger.warning("No text extracted from document")
            return ProcessedDocument(
                text="",
                pages=[],
                metadata=metadata,
                clauses=[]
            )
        
        logger.info(f"Extracted {len(text)} characters from {len(pages)} pages")
        
        # Step 2: Segment into clauses
        logger.info("Step 2: Segmenting clauses...")
        clause_segments = self.clause_segmenter.segment(text, pages)
        logger.info(f"Found {len(clause_segments)} clauses")
        
        # Steps 3-5: Process each clause
        processed_clauses = []
        
        for i, segment in enumerate(clause_segments):
            logger.debug(f"Processing clause {i+1}/{len(clause_segments)}")
            
            # Step 3: Extract entities
            entities = self.ner_extractor.extract(segment.text)
            
            # Step 4: Generate summary
            summary = self.summarizer.summarize(segment.text)
            
            # Step 5: Assess risk
            risk = self.risk_scorer.assess(
                segment.text,
                entities=entities,
                clause_type=segment.clause_type
            )
            
            processed_clause = ProcessedClause(
                text=segment.text,
                section_number=segment.section_number,
                section_title=segment.section_title,
                page_number=segment.page_number,
                start_offset=segment.start_offset,
                end_offset=segment.end_offset,
                clause_type=segment.clause_type,
                entities=entities,
                summary=summary,
                risk_assessment=risk
            )
            
            processed_clauses.append(processed_clause)
        
        logger.info(f"Processing complete. {len(processed_clauses)} clauses processed.")
        
        return ProcessedDocument(
            text=text,
            pages=pages,
            metadata=metadata,
            clauses=processed_clauses
        )
    
    def process_text(self, text: str) -> ProcessedDocument:
        """
        Process raw text through the pipeline (no file extraction).
        
        Args:
            text: Raw text to process
            
        Returns:
            ProcessedDocument with all extracted information
        """
        logger.info("Processing raw text...")
        
        if not text:
            return ProcessedDocument(
                text="",
                pages=[],
                metadata={},
                clauses=[]
            )
        
        # Create a single "page" for the text
        pages = [{"page_number": 1, "text": text, "char_count": len(text)}]
        
        # Segment into clauses
        clause_segments = self.clause_segmenter.segment(text, pages)
        
        # Process each clause
        processed_clauses = []
        
        for segment in clause_segments:
            entities = self.ner_extractor.extract(segment.text)
            summary = self.summarizer.summarize(segment.text)
            risk = self.risk_scorer.assess(
                segment.text,
                entities=entities,
                clause_type=segment.clause_type
            )
            
            processed_clauses.append(ProcessedClause(
                text=segment.text,
                section_number=segment.section_number,
                section_title=segment.section_title,
                page_number=segment.page_number,
                start_offset=segment.start_offset,
                end_offset=segment.end_offset,
                clause_type=segment.clause_type,
                entities=entities,
                summary=summary,
                risk_assessment=risk
            ))
        
        return ProcessedDocument(
            text=text,
            pages=pages,
            metadata={"format": "raw_text"},
            clauses=processed_clauses
        )
    
    def preload_models(self):
        """Preload all ML models (useful for faster first request)."""
        logger.info("Preloading models...")
        
        # Load summarization model
        try:
            self.summarizer._lazy_load_model()
            logger.info("Summarization model loaded")
        except Exception as e:
            logger.error(f"Failed to load summarization model: {e}")
        
        # Load spaCy model
        try:
            self.ner_extractor._lazy_load_spacy()
            logger.info("spaCy model loaded")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
        
        logger.info("Model preloading complete")
