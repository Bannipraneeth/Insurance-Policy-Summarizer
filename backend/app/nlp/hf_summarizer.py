"""
Hugging Face Inference API Summarizer.
Uses the Hugging Face serverless API for low-memory cloud deployment.
"""
import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)


class HFAPISummarizer:
    """Generate abstractive summaries using Hugging Face Inference API."""
    
    API_URL = "https://api-inference.huggingface.co/models/"
    
    def __init__(self, model_name: str = "sshleifer/distilbart-cnn-12-6", api_token: str = ""):
        """
        Initialize HF API summarizer.
        
        Args:
            model_name: HuggingFace model name
            api_token: HuggingFace API token (from HF_API_TOKEN env var)
        """
        self.model_name = model_name
        self.api_token = api_token or os.getenv("HF_API_TOKEN", "")
        self.api_url = f"{self.API_URL}{model_name}"
        
        if not self.api_token:
            logger.warning("HF_API_TOKEN not set. API calls may be rate-limited.")
    
    def _get_headers(self) -> dict:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers
    
    async def summarize_async(
        self,
        text: str,
        max_length: int = 130,
        min_length: int = 30
    ) -> dict:
        """
        Generate summary using HF Inference API (async).
        
        Args:
            text: Input text to summarize
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            
        Returns:
            Dict with summary_text, model_version, confidence
        """
        if not text or len(text.strip()) < 50:
            return {
                "summary_text": text.strip() if text else "",
                "model_version": "passthrough",
                "confidence": 1.0
            }
        
        # Truncate very long texts
        max_input_chars = 4000
        if len(text) > max_input_chars:
            text = text[:max_input_chars]
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=self._get_headers(),
                    json={
                        "inputs": text,
                        "parameters": {
                            "max_length": max_length,
                            "min_length": min_length,
                            "do_sample": False
                        },
                        "options": {
                            "wait_for_model": True
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    summary_text = result[0].get("summary_text", "") if result else ""
                    return {
                        "summary_text": summary_text,
                        "model_version": f"hf-api:{self.model_name}",
                        "confidence": 0.85
                    }
                else:
                    logger.error(f"HF API error: {response.status_code} - {response.text}")
                    return self._extractive_fallback(text)
                    
        except Exception as e:
            logger.error(f"HF API summarization error: {e}")
            return self._extractive_fallback(text)
    
    def summarize(
        self,
        text: str,
        max_length: int = 130,
        min_length: int = 30,
        do_sample: bool = False
    ) -> dict:
        """
        Generate summary using HF Inference API (sync wrapper).
        
        Args:
            text: Input text to summarize
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            do_sample: Ignored for API (always deterministic)
            
        Returns:
            Dict with summary_text, model_version, confidence
        """
        if not text or len(text.strip()) < 50:
            return {
                "summary_text": text.strip() if text else "",
                "model_version": "passthrough",
                "confidence": 1.0
            }
        
        # Truncate very long texts
        max_input_chars = 4000
        if len(text) > max_input_chars:
            text = text[:max_input_chars]
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    self.api_url,
                    headers=self._get_headers(),
                    json={
                        "inputs": text,
                        "parameters": {
                            "max_length": max_length,
                            "min_length": min_length,
                            "do_sample": False
                        },
                        "options": {
                            "wait_for_model": True
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    summary_text = result[0].get("summary_text", "") if result else ""
                    return {
                        "summary_text": summary_text,
                        "model_version": f"hf-api:{self.model_name}",
                        "confidence": 0.85
                    }
                else:
                    logger.error(f"HF API error: {response.status_code} - {response.text}")
                    return self._extractive_fallback(text)
                    
        except Exception as e:
            logger.error(f"HF API summarization error: {e}")
            return self._extractive_fallback(text)
    
    def summarize_batch(
        self,
        texts: list[str],
        max_length: int = 130,
        min_length: int = 30
    ) -> list[dict]:
        """Generate summaries for multiple texts."""
        results = []
        for text in texts:
            result = self.summarize(text, max_length, min_length)
            results.append(result)
        return results
    
    def _extractive_fallback(self, text: str, num_sentences: int = 3) -> dict:
        """Fallback to extractive summarization if API fails."""
        import re
        
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        summary_sentences = sentences[:num_sentences]
        summary_text = ' '.join(summary_sentences)
        
        if len(summary_text) > 500:
            summary_text = summary_text[:497] + "..."
        
        return {
            "summary_text": summary_text,
            "model_version": "extractive_fallback",
            "confidence": 0.6
        }
    
    @property
    def is_loaded(self) -> bool:
        """Always True for API-based summarizer."""
        return True
