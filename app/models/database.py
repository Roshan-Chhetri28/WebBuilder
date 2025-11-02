from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Restaurant(Base):
    """Restaurant model storing PDF content and metadata."""
    
    __tablename__ = "restaurants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    pdf_content = Column(Text, nullable=False)  # Store PDF as text/base64
    design_description = Column(Text, nullable=True)
    
    # Relationship to generated code
    generated_code = relationship("GeneratedCode", back_populates="restaurant", cascade="all, delete-orphan")


class GeneratedCode(Base):
    """Generated React code components for restaurants."""
    
    __tablename__ = "generated_code"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False)
    component_name = Column(String(255), nullable=False)  # e.g., "App.jsx", "Menu.jsx"
    code_content = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=False)  # Relative path in React project
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to restaurant
    restaurant = relationship("Restaurant", back_populates="generated_code")
