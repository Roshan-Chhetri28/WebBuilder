from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
import base64
import uuid
from contextlib import asynccontextmanager

from app.config import settings
from app.models.schemas import (
    ComponentFile, GenerateResponse, RestaurantCreate, RestaurantWithCodeResponse, RestaurantListResponse
)
from app.graph.workflow import run_menu_generation_workflow

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Menu2Site AI starting up...")
    yield
    logger.info("Menu2Site AI shutting down...")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Agentic AI backend that converts restaurant menu PDFs to React websites",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.app_name}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_website(
    pdf_file: UploadFile = File(..., description="Restaurant menu PDF file"),
    design_description: Optional[str] = Form(None, description="Optional design description")
):
    """
    Generate a React website from a restaurant menu PDF.
    
    Args:
        pdf_file: Uploaded PDF file
        design_description: Optional design description
        
    Returns:
        Generation response with restaurant ID and components
    """
    try:
        # Validate file type
        if not pdf_file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a PDF"
            )
        
        # Read and encode PDF content
        pdf_content_bytes = await pdf_file.read()
        pdf_content_b64 = base64.b64encode(pdf_content_bytes).decode('utf-8')
        
        # Generate restaurant name from filename
        restaurant_name = pdf_file.filename.replace('.pdf', '').replace('_', ' ').title()
        
        # Generate unique restaurant ID
        restaurant_id = uuid.uuid4()
        
        logger.info(f"Processing PDF for restaurant: {restaurant_name}")
        
        # Run the workflow
        workflow_result = await run_menu_generation_workflow(
            pdf_content=pdf_content_b64,
            design_description=design_description,
            restaurant_id=str(restaurant_id)
        )
        
        # Check workflow result
        if workflow_result["final_status"] == "failed":
            error_msg = workflow_result.get("error_message", "Unknown error")
            logger.error(f"Workflow failed for restaurant {restaurant_id}: {error_msg}")
            
            return GenerateResponse(
                restaurant_id=restaurant_id,
                status="failed",
                error_message=error_msg
            )
        
        # Get generated components
        components = workflow_result.get("component_files", [])
        
        # Format response with Pydantic validation
        response_components = []
        for component in components:
            try:
                component_file = ComponentFile(
                    file_path=component["file_path"],
                    code=component["code"],
                    component_name=component.get("component_name", "Unknown")
                )
                response_components.append(component_file)
            except Exception as e:
                logger.warning(f"Invalid component data: {e}")
                continue
        
        logger.info(f"Successfully generated {len(response_components)} components for {restaurant_name}")
        
        return GenerateResponse(
            restaurant_id=restaurant_id,
            status="completed",
            components=response_components
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_website: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# Database-dependent endpoints removed for simplicity
# The main functionality is PDF to React code generation


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
