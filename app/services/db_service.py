from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict
from uuid import UUID
import logging

from app.config import settings
from app.models.database import Base, Restaurant, GeneratedCode
from app.models.schemas import RestaurantCreate, GeneratedCodeResponse

logger = logging.getLogger(__name__)

# Database engine and session
engine = create_engine(settings.database_url, echo=settings.debug)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseService:
    """Service for database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_restaurant(self, restaurant_data: RestaurantCreate) -> Restaurant:
        """Create a new restaurant record."""
        try:
            restaurant = Restaurant(
                name=restaurant_data.name,
                pdf_content=restaurant_data.pdf_content,
                design_description=restaurant_data.design_description
            )
            self.db.add(restaurant)
            self.db.commit()
            self.db.refresh(restaurant)
            logger.info(f"Created restaurant: {restaurant.id}")
            return restaurant
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating restaurant: {e}")
            raise
    
    def get_restaurant(self, restaurant_id: UUID) -> Optional[Restaurant]:
        """Get restaurant by ID."""
        try:
            return self.db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting restaurant {restaurant_id}: {e}")
            raise
    
    def get_all_restaurants(self, skip: int = 0, limit: int = 100) -> List[Restaurant]:
        """Get all restaurants with pagination."""
        try:
            return self.db.query(Restaurant).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting restaurants: {e}")
            raise
    
    def save_generated_code(self, restaurant_id: UUID, components: List[Dict[str, str]]) -> List[GeneratedCode]:
        """Save generated React components to database."""
        try:
            generated_codes = []
            for component in components:
                generated_code = GeneratedCode(
                    restaurant_id=restaurant_id,
                    component_name=component.get("component_name", "Unknown"),
                    code_content=component["code"],
                    file_path=component["file_path"]
                )
                generated_codes.append(generated_code)
                self.db.add(generated_code)
            
            self.db.commit()
            logger.info(f"Saved {len(generated_codes)} components for restaurant {restaurant_id}")
            return generated_codes
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error saving generated code: {e}")
            raise
    
    def get_generated_code(self, restaurant_id: UUID) -> List[GeneratedCode]:
        """Get all generated code for a restaurant."""
        try:
            return self.db.query(GeneratedCode).filter(GeneratedCode.restaurant_id == restaurant_id).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting generated code for restaurant {restaurant_id}: {e}")
            raise
    
    def update_restaurant_status(self, restaurant_id: UUID, status: str, error_message: Optional[str] = None):
        """Update restaurant processing status (if we add a status field later)."""
        # This is a placeholder for future status tracking
        pass
