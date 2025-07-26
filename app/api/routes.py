from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
import asyncio
import uuid
from datetime import datetime

from app.models.schemas import MenuAnalysisRequest, MenuAnalysisResponse, DishDetail
from app.core.config import settings
from app.core.logging import get_logger

# Import services based on mock mode
if settings.USE_MOCK_SERVICES:
    from app.services.mock_service import MockOCRService as OCRService
    from app.services.mock_service import MockImageService as ImageService
    from app.services.mock_service import MockRecipeService as RecipeService
else:
    from app.services.ocr_service import OCRService
    from app.services.image_service import ImageService
    from app.services.recipe_service import RecipeService

from app.services.cache_service import CacheService

logger = get_logger(__name__)

api_router = APIRouter(prefix="/api/v1")

ocr_service = OCRService(
    api_url=settings.OCR_API_URL,
    model=settings.MODEL_ID,
)
image_service = ImageService()
recipe_service = RecipeService(
    api_url=settings.OCR_API_URL,
    model=settings.MODEL_ID,
)
cache_service = CacheService()


@api_router.post("/analyze-menu", response_model=MenuAnalysisResponse)
async def analyze_menu(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    include_recipes: bool = True
):
    """Analyze menu image and extract dish information"""
    
    # Validate file
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check file size
    file_size = 0
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    try:
        # Extract text from image using Vintern-1B
        logger.info(f"Starting OCR for request {request_id}")
        ocr_result = await ocr_service.extract_menu_text(contents)
        
        if not ocr_result.dishes:
            return MenuAnalysisResponse(
                request_id=request_id,
                dishes=[],
                status="no_dishes_found",
                message="No dishes found in the image"
            )
        
        # Get images for dishes
        logger.info(f"Fetching images for {len(ocr_result.dishes)} dishes")
        image_tasks = [
            image_service.get_dish_image(dish.name)
            for dish in ocr_result.dishes
        ]
        images = await asyncio.gather(*image_tasks, return_exceptions=True)
        
        # Create dish details
        dishes = []
        for index, (dish, image_url) in enumerate(zip(ocr_result.dishes, images)):
            dish_detail = DishDetail(
                name=dish.name,
                price=dish.price,
                image_url=image_url if not isinstance(image_url, Exception) else None
            )
            
            # Auto-generate ingredients for first 9 dishes
            if index < 9:
                background_tasks.add_task(
                    cache_service.generate_and_cache_ingredients,
                    request_id,
                    dish_detail
                )
            
            dishes.append(dish_detail)
        
        response = MenuAnalysisResponse(
            request_id=request_id,
            dishes=dishes,
            status="processing",
            message="Menu analyzed successfully. Recipes being generated..."
        )
        
        # Cache initial response
        await cache_service.cache_analysis(request_id, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing menu: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/analysis/{request_id}", response_model=MenuAnalysisResponse)
async def get_analysis_status(request_id: str):
    """Get analysis status and results"""
    
    cached_result = await cache_service.get_analysis(request_id)
    if not cached_result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return cached_result


@api_router.get("/ingredients/{request_id}/{dish_name}")
async def get_ingredients(request_id: str, dish_name: str):
    """Get ingredients for a specific dish"""
    
    ingredients = await cache_service.get_ingredients(request_id, dish_name)
    if not ingredients:
        # Generate ingredients on-demand
        try:
            recipe = await recipe_service.generate_recipe(dish_name)
            
            # Handle both Recipe object and dict
            if hasattr(recipe, 'ingredients'):
                ingredients = recipe.ingredients
            elif isinstance(recipe, dict) and 'ingredients' in recipe:
                ingredients = recipe['ingredients']
            else:
                ingredients = []
                
            await cache_service.cache_ingredients(request_id, dish_name, ingredients)
        except Exception as e:
            logger.error(f"Error generating ingredients for {dish_name}: {e}")
            ingredients = []
    
    return {"dish_name": dish_name, "ingredients": ingredients}


@api_router.post("/ingredients/batch")
async def get_batch_ingredients(request_data: dict):
    """Get ingredients for multiple dishes"""
    request_id = request_data.get("request_id")
    dish_names = request_data.get("dish_names", [])
    
    if not request_id or not dish_names:
        raise HTTPException(status_code=400, detail="request_id and dish_names are required")
    
    results = []
    for dish_name in dish_names:
        try:
            ingredients = await cache_service.get_ingredients(request_id, dish_name)
            if not ingredients:
                # Generate ingredients on-demand
                try:
                    recipe = await recipe_service.generate_recipe(dish_name)

                    logger.info(f"CACHE Generating ingredients for {dish_name}: {recipe}")

                    # Handle both Recipe object and dict
                    if hasattr(recipe, 'ingredients'):
                        ingredients = recipe.ingredients
                    elif isinstance(recipe, dict) and 'ingredients' in recipe:
                        ingredients = recipe['ingredients']
                    elif isinstance(recipe, str):
                        ingredients = recipe.split(",")
                    else:
                        ingredients = []
                        
                    await cache_service.cache_ingredients(request_id, dish_name, ingredients)
                except Exception as e:
                    logger.error(f"Error generating ingredients for {dish_name}: {e}")
                    ingredients = []
        except Exception as e:
            logger.error(f"Error processing ingredients for {dish_name}: {e}")
            ingredients = []
        
        logger.info(f"Returning ingredients for {dish_name}: {ingredients}")
        results.append({
            "dish_name": dish_name,
            "ingredients": ingredients
        })
    
    return {"results": results}