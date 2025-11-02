from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import UUID


class AgentState(BaseModel):
    """Shared state for the LangGraph agent workflow."""
    
    # Input data
    pdf_content: str = Field(..., description="Base64 encoded PDF content")
    design_description: Optional[str] = Field(None, description="Optional design description")
    restaurant_id: UUID = Field(..., description="Restaurant UUID")
    
    # PDF Extraction results
    extracted_text: str = Field(default="", description="Extracted text from PDF")
    extracted_sections: List[str] = Field(default_factory=list, description="PDF sections")
    
    # Menu Structuring results
    structured_data: Dict[str, Any] = Field(default_factory=dict, description="Structured menu data")
    restaurant_name: Optional[str] = Field(default="Restaurant", description="Restaurant name")
    menu_categories: List[Dict[str, Any]] = Field(default_factory=list, description="Menu categories")
    restaurant_info: Dict[str, Any] = Field(default_factory=dict, description="Restaurant info")
    
    # UI Design results
    design_system: Dict[str, Any] = Field(default_factory=dict, description="Design system")
    color_palette: Dict[str, str] = Field(default_factory=dict, description="Color palette")
    typography: Dict[str, str] = Field(default_factory=dict, description="Typography settings")
    layout_style: str = Field(default="", description="Layout style")
    
    # Code Generation results
    generated_components: List[Dict[str, str]] = Field(default_factory=list, description="Generated components")
    component_files: List[Dict[str, str]] = Field(default_factory=list, description="Component files")
    
    # Validation results
    is_valid: bool = Field(default=False, description="Validation status")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    validation_feedback: str = Field(default="", description="Validation feedback")
    iterations: int = Field(default=0, description="Validation iterations")
    
    # Final results
    final_status: str = Field(default="processing", description="Final status")
    error_message: Optional[str] = Field(None, description="Error message")
    
    class Config:
        arbitrary_types_allowed = True
