import pdfplumber
import base64
import io
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class PDFService:
    """Service for PDF processing operations."""
    
    @staticmethod
    def extract_text_from_pdf(pdf_content: str) -> Dict[str, any]:
        """
        Extract text and structure from PDF content.
        
        Args:
            pdf_content: Base64 encoded PDF content
            
        Returns:
            Dictionary with extracted text and sections
        """
        try:
            # Decode base64 PDF content
            pdf_bytes = base64.b64decode(pdf_content)
            pdf_file = io.BytesIO(pdf_bytes)
            
            extracted_data = {
                "full_text": "",
                "pages": [],
                "tables": [],
                "sections": []
            }
            
            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        extracted_data["full_text"] += page_text + "\n"
                        extracted_data["pages"].append({
                            "page_number": page_num + 1,
                            "text": page_text
                        })
                    
                    # Extract tables
                    tables = page.extract_tables()
                    for table_num, table in enumerate(tables):
                        if table:
                            extracted_data["tables"].append({
                                "page_number": page_num + 1,
                                "table_number": table_num + 1,
                                "data": table
                            })
            
            # Split into sections based on common patterns
            sections = PDFService._split_into_sections(extracted_data["full_text"])
            extracted_data["sections"] = sections
            
            logger.info(f"Extracted text from PDF: {len(extracted_data['full_text'])} characters, {len(sections)} sections")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    @staticmethod
    def _split_into_sections(text: str) -> List[str]:
        """
        Split text into logical sections based on common patterns.
        
        Args:
            text: Full extracted text
            
        Returns:
            List of text sections
        """
        sections = []
        
        # Common section patterns for restaurant menus
        section_patterns = [
            r'\n\s*(?:APPETIZERS?|STARTERS?|ANTIPASTI)\s*\n',
            r'\n\s*(?:MAIN\s*COURSES?|ENTRÉES?|MAINS?)\s*\n',
            r'\n\s*(?:DESSERTS?|DOLCI)\s*\n',
            r'\n\s*(?:BEVERAGES?|DRINKS?|BEVANDE)\s*\n',
            r'\n\s*(?:SALADS?|INSALATE)\s*\n',
            r'\n\s*(?:SOUPS?|ZUPPE)\s*\n',
            r'\n\s*(?:PASTA|PASTAS?)\s*\n',
            r'\n\s*(?:PIZZA|PIZZAS?)\s*\n',
            r'\n\s*(?:SANDWICHES?|PANINI)\s*\n',
            r'\n\s*(?:SPECIALS?|SPECIALITIES?)\s*\n',
        ]
        
        import re
        
        # Find all section headers
        section_headers = []
        for pattern in section_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                section_headers.append((match.start(), match.group().strip()))
        
        # Sort by position
        section_headers.sort(key=lambda x: x[0])
        
        # Extract sections
        if section_headers:
            for i, (start, header) in enumerate(section_headers):
                end = section_headers[i + 1][0] if i + 1 < len(section_headers) else len(text)
                section_text = text[start:end].strip()
                if section_text:
                    sections.append(section_text)
        else:
            # If no clear sections found, split by double newlines
            sections = [s.strip() for s in text.split('\n\n') if s.strip()]
        
        return sections
    
    @staticmethod
    def encode_pdf_to_base64(pdf_file_path: str) -> str:
        """
        Encode PDF file to base64 string.
        
        Args:
            pdf_file_path: Path to PDF file
            
        Returns:
            Base64 encoded string
        """
        try:
            with open(pdf_file_path, 'rb') as pdf_file:
                pdf_bytes = pdf_file.read()
                return base64.b64encode(pdf_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding PDF to base64: {e}")
            raise
