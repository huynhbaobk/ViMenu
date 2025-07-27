from pydantic import BaseModel, Field, validator, HttpUrl
from typing import List, Optional
from datetime import datetime
from enum import Enum


class AnalysisStatus(str, Enum):
    """Analysis status enumeration"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    NO_DISHES_FOUND = "no_dishes_found"


class DishInfo(BaseModel):
    """Dish information extracted from menu"""
    name: str = Field(..., min_length=1, max_length=200, description="Name of the dish")
    price: Optional[str] = Field(None, max_length=50, description="Price of the dish")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or v.isspace():
            raise ValueError('Dish name cannot be empty or whitespace only')
        return v.strip()
    
    @validator('price')
    def validate_price(cls, v):
        if v:
            return v.strip()
        return v


class OCRResult(BaseModel):
    """Result from OCR processing"""
    dishes: List[DishInfo] = Field(..., description="List of dishes found")
    raw_text: str = Field(..., max_length=5000, description="Raw text extracted from image")
    processing_time: Optional[float] = Field(None, description="OCR processing time in seconds")


class DishDetail(BaseModel):
    """Complete dish information with image and ingredients"""
    name: str = Field(..., min_length=1, max_length=200)
    price: Optional[str] = Field(None, max_length=50)
    image_url: Optional[HttpUrl] = None
    ingredients: Optional[str] = Field(None, max_length=300, description="Short ingredients text")
    
    class Config:
        json_encoders = {
            HttpUrl: str
        }


class MenuAnalysisRequest(BaseModel):
    """Request for menu analysis"""
    max_dishes: int = Field(20, ge=1, le=50, description="Maximum number of dishes to process")


class MenuAnalysisResponse(BaseModel):
    """Response from menu analysis"""
    request_id: str = Field(..., pattern=r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
    dishes: List[DishDetail] = Field(..., max_items=50)
    status: AnalysisStatus = Field(..., description="Current status of analysis")
    message: str = Field(..., max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = Field(None, description="Total processing time in seconds")
    
    class Config:
        use_enum_values = True