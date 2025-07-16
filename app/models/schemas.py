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


class RecipeStep(BaseModel):
    """Individual recipe step"""
    step_number: int
    instruction: str
    duration_minutes: Optional[int] = None


class Recipe(BaseModel):
    """Complete recipe for a dish"""
    dish_name: str
    description: str
    ingredients: List[Dict[str, str]]  # [{"item": "Bún", "quantity": "200g"}]
    instructions: List[RecipeStep]
    prep_time: int  # minutes
    cook_time: int  # minutes
    difficulty: str = Field(..., description="Easy, Medium, Hard")
    servings: int = 1
    nutrition_info: Optional[Dict[str, str]] = None


class DishDetail(BaseModel):
    """Complete dish information"""
    name: str
    price: Optional[str] = None
    image_url: Optional[str] = None
    ingredients: Optional[List[Dict[str, str]]] = None  # Quick ingredients list
    recipe: Optional[Recipe] = None


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