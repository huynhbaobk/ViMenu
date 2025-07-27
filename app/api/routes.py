from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
import asyncio
import uuid
from datetime import datetime

from app.models.schemas import MenuAnalysisRequest, MenuAnalysisResponse, DishDetail, AnalysisStatus
from app.core.config import settings
from app.core.logging import get_logger
from app.core.dependencies import (
    get_ocr_service, 
    get_image_service, 
    get_ingredient_service, 
    get_cache_service
)
from app.core.exceptions import OCRException, ImageProcessingException, CacheException

logger = get_logger(__name__)

api_router = APIRouter(tags=["menu-analysis"])


@api_router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify API is working"""
    logger.info("📱 Test endpoint called")
    return {"status": "ok", "message": "API is working", "timestamp": datetime.utcnow()}


@api_router.post("/test-upload")
async def test_upload(file: UploadFile = File(...)):
    """Test file upload endpoint"""
    logger.info(f"📱 Test upload called - File: {file.filename}, Type: {file.content_type}")
    contents = await file.read()
    return {
        "status": "ok", 
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents)
    }


def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")


def validate_file_size(contents: bytes) -> None:
    """Validate file size"""
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE} bytes"
        )


async def process_dish_images_and_ingredients(
    dishes: List, 
    image_service, 
    ingredient_service,
    request_id: str,
    cache_service
) -> List[DishDetail]:
    """Process images and ingredients for dishes concurrently"""
    try:
        # Process images and ingredients in parallel
        image_tasks = [image_service.get_dish_image(dish.name) for dish in dishes]
        ingredient_tasks = [ingredient_service.generate_ingredients(dish.name) for dish in dishes]
        
        images, ingredients_list = await asyncio.gather(
            asyncio.gather(*image_tasks, return_exceptions=True),
            asyncio.gather(*ingredient_tasks, return_exceptions=True)
        )
        
        dish_details = []
        for dish, image_url, ingredients in zip(dishes, images, ingredients_list):
            # Handle exceptions
            if isinstance(image_url, Exception):
                image_url = None
            if isinstance(ingredients, Exception):
                ingredients = ""
            
            dish_detail = DishDetail(
                name=dish.name,
                price=dish.price,
                image_url=image_url,
                ingredients=ingredients
            )
            dish_details.append(dish_detail)
            
            # Cache the ingredients
            if ingredients:
                await cache_service.cache_ingredients(request_id, dish.name, ingredients)
        
        return dish_details
        
    except Exception as e:
        logger.error(f"Error processing dishes: {e}")
        # Fallback: create dishes without images and ingredients
        return [
            DishDetail(name=dish.name, price=dish.price, image_url=None, ingredients="")
            for dish in dishes
        ]


@api_router.post("/analyze-menu", response_model=MenuAnalysisResponse)
async def analyze_menu(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ocr_service=Depends(get_ocr_service),
    image_service=Depends(get_image_service),
    ingredient_service=Depends(get_ingredient_service),
    cache_service=Depends(get_cache_service)
):
    """Analyze menu image and extract dish information"""
    
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    logger.info(f"📱 Received file upload request {request_id}")
    logger.info(f"📁 File info - Name: {file.filename}, Content-Type: {file.content_type}, Size: {file.size if hasattr(file, 'size') else 'unknown'}")
    
    try:
        # Validate file
        validate_image_file(file)
        logger.info(f"✅ File validation passed for {request_id}")
        
        # Read and validate file size
        contents = await file.read()
        file_size = len(contents)
        logger.info(f"📊 File read successfully - Size: {file_size} bytes for {request_id}")
        
        validate_file_size(contents)
        logger.info(f"✅ File size validation passed for {request_id}")
        
    except Exception as e:
        logger.error(f"❌ File validation failed for {request_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"File validation error: {str(e)}")
    
    try:
        # Extract text from image using OCR
        logger.info(f"Starting OCR for request {request_id}")
        ocr_result = await ocr_service.extract_menu_text(contents)
        
        if not ocr_result.dishes:
            return MenuAnalysisResponse(
                request_id=request_id,
                dishes=[],
                status=AnalysisStatus.NO_DISHES_FOUND,
                message="No dishes found in the image"
            )
        
        # Process dishes with images and ingredients
        logger.info(f"Processing {len(ocr_result.dishes)} dishes")
        dishes = await process_dish_images_and_ingredients(
            ocr_result.dishes, 
            image_service, 
            ingredient_service,
            request_id,
            cache_service
        )
        
        response = MenuAnalysisResponse(
            request_id=request_id,
            dishes=dishes,
            status=AnalysisStatus.COMPLETED,
            message=f"Menu analyzed successfully. Found {len(dishes)} dishes."
        )
        
        # Cache the complete response
        await cache_service.cache_analysis(request_id, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing menu: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/analysis/{request_id}", response_model=MenuAnalysisResponse)
async def get_analysis_status(
    request_id: str,
    cache_service=Depends(get_cache_service)
):
    """Get analysis status and results"""
    
    cached_result = await cache_service.get_analysis(request_id)
    if not cached_result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return cached_result


@api_router.get("/ingredients/{request_id}/{dish_name}")
async def get_ingredients(
    request_id: str, 
    dish_name: str,
    cache_service=Depends(get_cache_service),
    ingredient_service=Depends(get_ingredient_service)
):
    """Get ingredients for a specific dish"""
    
    try:
        ingredients = await cache_service.get_ingredients(request_id, dish_name)
        
        if not ingredients:
            # Generate ingredients on-demand
            ingredients = await ingredient_service.generate_ingredients(dish_name)
            await cache_service.cache_ingredients(request_id, dish_name, ingredients)
        
        return {"dish_name": dish_name, "ingredients": ingredients}
        
    except Exception as e:
        logger.error(f"Error getting ingredients for {dish_name}: {e}")
        return {"dish_name": dish_name, "ingredients": ""}


@api_router.post("/ingredients/batch")
async def get_batch_ingredients(
    request_data: dict,
    cache_service=Depends(get_cache_service),
    ingredient_service=Depends(get_ingredient_service)
):
    """Get ingredients for multiple dishes"""
    request_id = request_data.get("request_id")
    dish_names = request_data.get("dish_names", [])
    
    if not request_id or not dish_names:
        raise HTTPException(status_code=400, detail="request_id and dish_names are required")
    
    # Limit batch size
    if len(dish_names) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 dishes per batch request")
    
    # Process dishes concurrently
    async def process_dish(dish_name: str):
        try:
            ingredients = await cache_service.get_ingredients(request_id, dish_name)
            
            if not ingredients:
                ingredients = await ingredient_service.generate_ingredients(dish_name)
                await cache_service.cache_ingredients(request_id, dish_name, ingredients)
            
            return {"dish_name": dish_name, "ingredients": ingredients}
            
        except Exception as e:
            logger.error(f"Error processing ingredients for {dish_name}: {e}")
            return {"dish_name": dish_name, "ingredients": ""}
    
    # Execute all dish processing concurrently
    results = await asyncio.gather(*[process_dish(name) for name in dish_names])
    
    return {"results": results}


@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }