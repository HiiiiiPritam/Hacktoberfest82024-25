import io
import logging
import requests
from PIL import Image
import pytesseract
import PyPDF2
from typing import List, Dict

logger = logging.getLogger(__name__)

class PDFProcessor:
    @staticmethod
    async def extract_text_from_pdf(pdf_url: str) -> List[Dict]:
        """Extract text from PDF using OCR"""
        try:
            # Download PDF
            response = requests.get(pdf_url)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
                
            if "application/pdf" not in response.headers.get("content-type", ""):
                raise Exception("Not a PDF file")
                
            pdf_buffer = io.BytesIO(response.content)
            
            # Try text extraction first
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_buffer)
                results = []
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text().strip()
                    if text:  # If text extraction works
                        results.append({"page": page_num, "text": text})
                    else:  # Fall back to OCR
                        # Note: For full OCR implementation, you'd need to convert PDF to images
                        # This is a simplified version
                        results.append({"page": page_num, "text": f"[Page {page_num} - OCR required]"})
                        
                return results
                
            except Exception as e:
                logger.error(f"PDF text extraction failed: {e}")
                raise Exception(f"PDF processing failed: {e}")
                
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            raise Exception(f"PDF processing failed: {e}")

    @staticmethod  
    async def extract_text_from_image(image_url: str) -> str:
        """Extract text from image using OCR"""
        try:
            response = requests.get(image_url)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
                
            image = Image.open(io.BytesIO(response.content))
            text = pytesseract.image_to_string(image)
            return text.strip()
            
        except Exception as e:
            logger.error(f"Image OCR error: {e}")
            raise Exception(f"Image OCR failed: {e}")