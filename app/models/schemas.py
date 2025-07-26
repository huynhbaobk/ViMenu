from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class DishInfo(BaseModel):
    """Dish information extracted from menu"""
    name: str = Field(..., description="Name of the dish")
    price: Optional[str] = Field(None, description="Price of the dish")


class OCRResult(BaseModel):
    """Result from OCR processing"""
    dishes: List[DishInfo] = Field(..., description="List of dishes found")
    raw_text: str = Field(..., description="Raw text extracted from image")


class DishDetail(BaseModel):
    """Complete dish information"""
    name: str
    price: Optional[str] = None
    image_url: Optional[str] = None
    ingredients: Optional[str] = None  # Quick ingredients list


class MenuAnalysisRequest(BaseModel):
    """Request for menu analysis"""
    include_recipes: bool = True
    max_dishes: int = Field(10, ge=1, le=50)


class MenuAnalysisResponse(BaseModel):
    """Response from menu analysis"""
    request_id: str
    dishes: List[DishDetail]
    status: str = Field(..., description="processing, completed, error")
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None