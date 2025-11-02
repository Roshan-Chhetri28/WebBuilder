from typing import Dict, Any
import logging

from app.agents.state import AgentState
from app.services.pdf_service import PDFService

logger = logging.getLogger(__name__)


def pdf_extractor_agent(state: AgentState) -> AgentState:
    """
    Agent 1: Extract text and structure from PDF content.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with extracted text and sections
    """
    try:
        logger.info("Starting PDF extraction...")
        
        # Extract text from PDF
        extracted_data = PDFService.extract_text_from_pdf(state.pdf_content)
        
        # Update state with extracted data
        state.extracted_text = extracted_data["full_text"]
        state.extracted_sections = extracted_data["sections"]
        
        logger.info(f"PDF extraction completed. Extracted {len(state.extracted_text)} characters and {len(state.extracted_sections)} sections")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in PDF extractor agent: {e}")
        state.final_status = "failed"
        state.error_message = f"PDF extraction failed: {str(e)}"
        return state
