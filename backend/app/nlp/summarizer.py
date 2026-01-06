"""
Summarization Module.
Generates concise summaries of clauses using transformer models (CPU-optimized).
"""
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Summarizer:
    """Generate abstractive summaries using HuggingFace Transformers."""
    
    def __init__(self, model_name: str = "sshleifer/distilbart-cnn-12-6"):
        """
        Initialize summarizer with a CPU-optimized model.
        
        Args:
            model_name: HuggingFace model name (default: distilbart for CPU)
        """
        self.model_name = model_name
        self._pipeline = None
        self._model_loaded = False
    
    def _lazy_load_model(self):
        """Lazy load the summarization pipeline."""
        if self._pipeline is None:
            try:
                from transformers import pipeline
                import torch
                
                # Use CPU explicitly
                device = -1  # CPU
                
                logger.info(f"Loading summarization model: {self.model_name}")
                self._pipeline = pipeline(
                    "summarization",
                    model=self.model_name,
                    device=device,
                    framework="pt"
                )
                self._model_loaded = True
                logger.info("Summarization model loaded successfully")
                
            except Exception as e:
                logger.error(f"Error loading summarization model: {e}")
                self._model_loaded = False
                raise
        
        return self._pipeline
    
    def summarize(
        self,
        text: str,
        max_length: int = 130,
        min_length: int = 30,
        do_sample: bool = False
    ) -> dict:
        """
        Generate a summary for the given text.
        
        Args:
            text: Input text to summarize
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            do_sample: Whether to use sampling
            
        Returns:
            Dict with summary_text, model_version, confidence
        """
        if not text or len(text.strip()) < 50:
            return {
                "summary_text": text.strip() if text else "",
                "model_version": "passthrough",
                "confidence": 1.0
            }
        
        # Truncate very long texts (model has max token limit)
        max_input_length = 1024
        if len(text) > max_input_length * 4:  # Rough char to token ratio
            text = text[:max_input_length * 4]
        
        try:
            pipeline = self._lazy_load_model()
            
            result = pipeline(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=do_sample,
                truncation=True
            )
            
            summary_text = result[0]['summary_text'] if result else text[:200]
            
            return {
                "summary_text": summary_text,
                "model_version": self.model_name,
                "confidence": 0.85
            }
            
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            # Fallback to extractive summary
            return self._extractive_fallback(text)
    
    def summarize_batch(
        self,
        texts: list[str],
        max_length: int = 130,
        min_length: int = 30
    ) -> list[dict]:
        """
        Generate summaries for multiple texts.
        
        Args:
            texts: List of texts to summarize
            max_length: Maximum length of each summary
            min_length: Minimum length of each summary
            
        Returns:
            List of summary dicts
        """
        results = []
        
        for text in texts:
            result = self.summarize(text, max_length, min_length)
            results.append(result)
        
        return results
    
    def _extractive_fallback(self, text: str, num_sentences: int = 3) -> dict:
        """
        Fallback to extractive summarization if model fails.
        Simply selects the first N sentences.
        """
        import re
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        # Take first N sentences
        summary_sentences = sentences[:num_sentences]
        summary_text = ' '.join(summary_sentences)
        
        # Truncate if still too long
        if len(summary_text) > 500:
            summary_text = summary_text[:497] + "..."
        
        return {
            "summary_text": summary_text,
            "model_version": "extractive_fallback",
            "confidence": 0.6
        }
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model_loaded
