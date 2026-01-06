"""
Text Extraction Module.
Extracts text from PDF, images (OCR), HTML, and plain text files.
"""
import os
import re
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TextExtractor:
    """Extract text from various document formats."""
    
    def __init__(self):
        self._pdfplumber = None
        self._pytesseract = None
        self._bs4 = None
        
    def _lazy_load_pdfplumber(self):
        """Lazy load pdfplumber."""
        if self._pdfplumber is None:
            import pdfplumber
            self._pdfplumber = pdfplumber
        return self._pdfplumber
    
    def _lazy_load_pytesseract(self):
        """Lazy load pytesseract."""
        if self._pytesseract is None:
            import pytesseract
            self._pytesseract = pytesseract
        return self._pytesseract
    
    def _lazy_load_bs4(self):
        """Lazy load BeautifulSoup."""
        if self._bs4 is None:
            from bs4 import BeautifulSoup
            self._bs4 = BeautifulSoup
        return self._bs4
    
    def extract(self, file_path: str) -> dict:
        """
        Extract text from a file.
        
        Returns:
            dict with keys: text, pages, metadata
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            return self._extract_from_pdf(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return self._extract_from_image(file_path)
        elif file_ext == '.html':
            return self._extract_from_html(file_path)
        elif file_ext == '.txt':
            return self._extract_from_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def _extract_from_pdf(self, file_path: str) -> dict:
        """Extract text from PDF using pdfplumber."""
        pdfplumber = self._lazy_load_pdfplumber()
        
        pages = []
        full_text = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    
                    # Clean the text
                    page_text = self._clean_text(page_text)
                    
                    if page_text.strip():
                        pages.append({
                            "page_number": i + 1,
                            "text": page_text,
                            "char_count": len(page_text)
                        })
                        full_text.append(page_text)
                
                metadata = {
                    "page_count": len(pdf.pages),
                    "has_text": len(full_text) > 0
                }
                
                # If no text extracted, try OCR on each page
                if not full_text:
                    logger.info("No text found in PDF, attempting OCR...")
                    return self._ocr_pdf(file_path)
                
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            raise
        
        return {
            "text": "\n\n".join(full_text),
            "pages": pages,
            "metadata": metadata
        }
    
    def _ocr_pdf(self, file_path: str) -> dict:
        """Perform OCR on a scanned PDF."""
        from pdf2image import convert_from_path
        pytesseract = self._lazy_load_pytesseract()
        
        pages = []
        full_text = []
        
        try:
            images = convert_from_path(file_path)
            
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image)
                page_text = self._clean_text(page_text)
                
                if page_text.strip():
                    pages.append({
                        "page_number": i + 1,
                        "text": page_text,
                        "char_count": len(page_text)
                    })
                    full_text.append(page_text)
                    
        except Exception as e:
            logger.error(f"Error performing OCR on PDF: {e}")
            raise
        
        return {
            "text": "\n\n".join(full_text),
            "pages": pages,
            "metadata": {"page_count": len(pages), "ocr_performed": True}
        }
    
    def _extract_from_image(self, file_path: str) -> dict:
        """Extract text from image using OCR."""
        pytesseract = self._lazy_load_pytesseract()
        from PIL import Image
        
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            text = self._clean_text(text)
            
            return {
                "text": text,
                "pages": [{"page_number": 1, "text": text, "char_count": len(text)}],
                "metadata": {"ocr_performed": True}
            }
        except Exception as e:
            logger.error(f"Error performing OCR on image: {e}")
            raise
    
    def _extract_from_html(self, file_path: str) -> dict:
        """Extract text from HTML file."""
        BeautifulSoup = self._lazy_load_bs4()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Remove script and style elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            
            text = soup.get_text(separator='\n')
            text = self._clean_text(text)
            
            return {
                "text": text,
                "pages": [{"page_number": 1, "text": text, "char_count": len(text)}],
                "metadata": {"format": "html"}
            }
        except Exception as e:
            logger.error(f"Error extracting HTML: {e}")
            raise
    
    def _extract_from_text(self, file_path: str) -> dict:
        """Extract text from plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            text = self._clean_text(text)
            
            return {
                "text": text,
                "pages": [{"page_number": 1, "text": text, "char_count": len(text)}],
                "metadata": {"format": "text"}
            }
        except Exception as e:
            logger.error(f"Error reading text file: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove page numbers (common patterns)
        text = re.sub(r'\n\s*Page\s*\d+\s*(?:of\s*\d+)?\s*\n', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'\n\s*-\s*\d+\s*-\s*\n', '\n', text)
        
        # Remove headers/footers (common patterns)
        text = re.sub(r'\n\s*(?:CONFIDENTIAL|DRAFT|PROPRIETARY)\s*\n', '\n', text, flags=re.IGNORECASE)
        
        return text.strip()
