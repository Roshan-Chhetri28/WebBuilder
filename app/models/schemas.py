from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ComponentFile(BaseModel):
    """Schema for individual component file."""
    file_path: str = Field(..., description="Relative file path", min_length=1)
    code: str = Field(..., description="File content", min_length=1)
    component_name: str = Field(..., description="Component name", min_length=1)
    
    @validator('file_path')
    def validate_file_path(cls, v):
        if not v or v.strip() == "":
            raise ValueError('File path cannot be empty')
        return v.strip()
    
    @validator('code')
    def validate_code(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Code content cannot be empty')
        return v.strip()


class RestaurantCreate(BaseModel):
    """Schema for creating a restaurant."""
    name: str = Field(..., min_length=1, max_length=255, description="Restaurant name")
    pdf_content: str = Field(..., description="PDF content as base64 string", min_length=1)
    design_description: Optional[str] = Field(None, description="Optional design description")
    
    @validator('pdf_content')
    def validate_pdf_content(cls, v):
        if not v or len(v.strip()) < 100:  # Basic validation for base64 content
            raise ValueError('PDF content appears to be invalid')
        return v.strip()


class RestaurantResponse(BaseModel):
    """Schema for restaurant response."""
    id: UUID
    name: str
    created_at: datetime
    design_description: Optional[str] = None
    
    class Config:
        from_attributes = True


class GeneratedCodeResponse(BaseModel):
    """Schema for generated code response."""
    id: UUID
    component_name: str
    code_content: str
    file_path: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class RestaurantWithCodeResponse(RestaurantResponse):
    """Schema for restaurant with generated code."""
    generated_code: List[GeneratedCodeResponse] = Field(default_factory=list)


class GenerateRequest(BaseModel):
    """Schema for PDF generation request."""
    design_description: Optional[str] = Field(None, description="Optional design description", max_length=1000)


class GenerateResponse(BaseModel):
    """Schema for generation response."""
    restaurant_id: UUID
    status: str = Field(..., description="Status: 'processing', 'completed', 'failed'")
    components: List[ComponentFile] = Field(default_factory=list, description="Generated React components")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['processing', 'completed', 'failed']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v


class RestaurantListResponse(BaseModel):
    """Schema for restaurant list response."""
    restaurants: List[RestaurantResponse]
    total: int = Field(..., ge=0, description="Total number of restaurants")
