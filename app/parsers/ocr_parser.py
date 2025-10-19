"""
OCR Parser for extracting text from images and PDFs
"""

import os
import io
import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Optional, Union
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import numpy as np
from fastapi import UploadFile, HTTPException

# Optional imports with fallback handling
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from unidecode import unidecode
    UNIDECODE_AVAILABLE = True
except ImportError:
    UNIDECODE_AVAILABLE = False


class OCRParser:
    """OCR parser for extracting text from various document formats."""
    
    def __init__(self):
        """Initialize OCR parser."""
        # Configure tesseract path if needed
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'
        pass
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy using OpenCV - matches analyse_screen.py logic exactly."""
        if not CV2_AVAILABLE:
            print("OpenCV not available, skipping image preprocessing")
            return image
            
        try:
            # =============================
            # Convert PIL image to OpenCV format (BGR) - exactly like 
            # =============================
            img_array = np.array(image)
            
            # =============================
            # Convert RGB to BGR for OpenCV (same as analyse_screen.py)
            # =============================
            if len(img_array.shape) == 3:
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_array
            
            # =============================
            # Apply threshold to create binary image (exactly like analyse_screen.py)
            # =============================
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # =============================
            # Convert back to PIL Image
            # =============================
            processed_image = Image.fromarray(thresh)
            
            return processed_image
            
        except Exception as e:
            # If preprocessing fails, return original image
            print(f"Image preprocessing failed: {e}")
            return image
    
    def _extract_text_from_pdf_advanced(self, pdf_data: bytes) -> str:
        """Advanced PDF text extraction with multiple fallback methods."""
        try:
            # =============================
            # Method 1: PyMuPDF (most reliable)
            # =============================
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            pages = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                # =============================
                # Try multiple text extraction methods
                # =============================
                text = page.get_text("text")
                if not text or len(text.strip()) < 10:
                    # =============================
                    # Try alternative extraction method
                    # =============================
                    text_dict = page.get_text("dict")
                    if text_dict and "blocks" in text_dict:
                        extracted_text = ""
                        for block in text_dict["blocks"]:
                            if "lines" in block:
                                for line in block["lines"]:
                                    if "spans" in line:
                                        for span in line["spans"]:
                                            if "text" in span:
                                                extracted_text += span["text"] + " "
                        text = extracted_text.strip()
                
                if text and text.strip():
                    pages.append(text.strip())
            
            doc.close()
            result = "\n".join(pages)
            if result.strip():
                return result
        except Exception as e:
            print(f"PyMuPDF extraction error: {e}")
        
        # =============================
        # Method 2: PyPDF2 as fallback
        # =============================
        if PYPDF2_AVAILABLE:
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                if text.strip():
                    return text.strip()
            except Exception as e:
                print(f"PyPDF2 extraction error: {e}")
        
        # =============================
        # Method 3: pdfplumber as another fallback
        # =============================
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
                    text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    if text.strip():
                        return text.strip()
            except Exception as e:
                print(f"pdfplumber extraction error: {e}")
        
        # =============================
        # Method 4: Manual binary extraction
        # =============================
        try:
            # =============================
            # Simple text extraction from PDF binary
            # =============================
            text_pattern = rb'BT\s*(.*?)\s*ET'
            matches = re.findall(text_pattern, pdf_data, re.DOTALL)
            extracted_text = ""
            for match in matches:
                # Extract text from PDF commands
                text_matches = re.findall(rb'\((.*?)\)', match)
                for text_match in text_matches:
                    try:
                        extracted_text += text_match.decode('utf-8', errors='ignore') + " "
                    except:
                        continue
            return extracted_text.strip()
        except Exception as fallback_error:
            print(f"Manual PDF extraction error: {fallback_error}")
            return ""
    
    def _extract_text_from_docx(self, docx_data: bytes) -> str:
        """Extract text from DOCX files."""
        if not DOCX_AVAILABLE:
            raise HTTPException(
                status_code=400,
                detail="python-docx library not installed. Install with: pip install python-docx"
            )
        
        try:
            doc = docx.Document(io.BytesIO(docx_data))
            return "\n".join([p.text for p in doc.paragraphs if p.text])
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error extracting text from DOCX: {str(e)}"
            )
    
    def _remove_control_and_format_chars(self, s: str) -> str:
        """Remove control and format characters."""
        return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")
    
    def _normalize_whitespace(self, s: str, preserve_paragraphs: bool = True) -> str:
        """Normalize whitespace in text."""
        # Normalize common whitespace types
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        # collapse tabs
        s = s.replace("\t", " ")
        if preserve_paragraphs:
            # collapse >2 newlines to exactly 2, and collapse spaces within lines
            s = re.sub(r"\n{3,}", "\n\n", s)
            s = "\n".join(re.sub(r"[ \u00A0]{2,}", " ", line).strip() for line in s.splitlines())
            # remove leading/trailing empty lines
            s = s.strip()
        else:
            s = re.sub(r"\s+", " ", s).strip()
        return s
    
    def _preprocess_text_advanced(self, text: str) -> str:
        """Advanced text preprocessing for better OCR results."""
        if not text:
            return ""
        
        # Strip BOM
        text = text.replace("\ufeff", "")
        # Normalize unicode form
        text = unicodedata.normalize("NFC", text)
        
        # Remove control / format characters
        text = self._remove_control_and_format_chars(text)
        
        # Optionally transliterate to ASCII (remove Unicode)
        if UNIDECODE_AVAILABLE:
            try:
                text = unidecode(text)
            except Exception:
                # fallback: decompose and drop non-ascii
                text = unicodedata.normalize("NFKD", text)
                text = text.encode("ascii", "ignore").decode("ascii")
        
        # Replace common invisible separators and weird spaces
        text = text.replace("\u200b", "")  # zero-width space
        text = text.replace("\xa0", " ")   # non-breaking space
        text = text.replace("\u2028", "\n")  # line separator to newline
        
        # Normalize whitespace
        text = self._normalize_whitespace(text, preserve_paragraphs=True)
        
        # Final trim
        return text.strip()
    
    async def extract_text_from_image(self, image_file: UploadFile) -> str:
        """Extract text from image file using OCR - exactly like Colab analyse_screen function."""
        try:
            # Check if tesseract is available
            try:
                pytesseract.get_tesseract_version()
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Tesseract OCR is not installed. Please install tesseract-ocr to process images. For now, you can use the text input field instead."
                )
            
            # =============================
            # Read image data
            # =============================
            image_data = await image_file.read()
            
            # =============================
            # Convert bytes to numpy array for OpenCV (exactly like Colab script)
            # =============================
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise HTTPException(
                    status_code=400,
                    detail="Could not read image file. Please ensure it's a valid image format."
                )
            
            # =============================
            # Apply exact same preprocessing as Colab analyse_screen function
            # =============================
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            pil_img = Image.fromarray(thresh)
            
            # =============================
            # Extract text using exact same config as Colab script
            # =============================
            text = pytesseract.image_to_string(pil_img, config="--psm 6")
            
            if not text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="No text could be extracted from the image. Please ensure the image contains clear, readable text."
                )
            
            return text.strip()
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Error extracting text from image: {str(e)}"
            )
    
    async def extract_text_from_pdf(self, pdf_file: UploadFile) -> str:
        """Extract text from PDF file using advanced methods."""
        try:
            # Read PDF data
            pdf_data = await pdf_file.read()
            
            # Use advanced PDF extraction
            extracted_text = self._extract_text_from_pdf_advanced(pdf_data)
            
            if not extracted_text:
                raise HTTPException(
                    status_code=400,
                    detail="No text could be extracted from the PDF. The PDF might contain only images or be password-protected."
                )
            
            return extracted_text
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Error extracting text from PDF: {str(e)}"
            )
    
    async def extract_text_from_file(self, file: UploadFile) -> str:
        """Extract text from uploaded file (image, PDF, or DOCX)."""
        # Get file extension
        file_extension = file.filename.split('.')[-1].lower() if file.filename else ''
        
        # Check if it's an image
        if file_extension in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']:
            return await self.extract_text_from_image(file)
        
        # Check if it's a PDF
        elif file_extension == 'pdf':
            return await self.extract_text_from_pdf(file)
        
        # Check if it's a DOCX file
        elif file_extension == 'docx':
            return await self.extract_text_from_docx(file)
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_extension}. Supported formats: png, jpg, jpeg, gif, bmp, tiff, pdf, docx"
            )
    
    async def extract_text_from_docx(self, docx_file: UploadFile) -> str:
        """Extract text from DOCX file."""
        try:
            # Read DOCX data
            docx_data = await docx_file.read()
            
            # Extract text using advanced method
            extracted_text = self._extract_text_from_docx(docx_data)
            
            if not extracted_text:
                raise HTTPException(
                    status_code=400,
                    detail="No text could be extracted from the DOCX file."
                )
            
            return extracted_text
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Error extracting text from DOCX: {str(e)}"
            )
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess extracted text for better parsing using advanced methods."""
        # Use advanced preprocessing
        processed_text = self._preprocess_text_advanced(text)
        
        # Additional OCR-specific cleanup
        processed_text = processed_text.replace('|', 'I')  # Common OCR mistake
        processed_text = processed_text.replace('0', 'O')  # In certain contexts
        
        return processed_text.strip()
    
    async def parse_document(self, file: UploadFile) -> dict:
        """Parse document and return extracted text with metadata."""
        try:
            # Extract text
            raw_text = await self.extract_text_from_file(file)
            
            # Preprocess text
            processed_text = self.preprocess_text(raw_text)
            
            return {
                "filename": file.filename,
                "file_type": file.filename.split('.')[-1].lower() if file.filename else 'unknown',
                "raw_text": raw_text,
                "processed_text": processed_text,
                "text_length": len(processed_text),
                "success": True
            }
            
        except HTTPException as e:
            # Re-raise HTTPException to preserve error details
            raise e
        except Exception as e:
            return {
                "filename": file.filename,
                "file_type": file.filename.split('.')[-1].lower() if file.filename else 'unknown',
                "raw_text": "",
                "processed_text": "",
                "text_length": 0,
                "success": False,
                "error": str(e)
            }


# Global OCR parser instance
ocr_parser = OCRParser()
