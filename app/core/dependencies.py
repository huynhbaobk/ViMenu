"""
Dependency injection container for services
"""
from functools import lru_cache
from app.core.config import settings
from app.services.cache_service import CacheService
from app.services.ocr_service import OCRService
from app.services.image_service import ImageService
from app.services.ingredient_service import IngredientService

# Import services based on mock mode
if settings.USE_MOCK_SERVICES:
    from app.services.mock_service import MockOCRService as OCRServiceImpl
    from app.services.mock_service import MockImageService as ImageServiceImpl
    from app.services.mock_service import MockIngredientService as IngredientServiceImpl
else:
    OCRServiceImpl = OCRService
    ImageServiceImpl = ImageService
    IngredientServiceImpl = IngredientService


@lru_cache()
def get_ocr_service() -> OCRService:
    """Get OCR service instance"""
    return OCRServiceImpl(
        api_url=settings.OCR_API_URL,
        model=settings.MODEL_ID,
    )


@lru_cache()
def get_image_service() -> ImageService:
    """Get image service instance"""
    return ImageServiceImpl()


@lru_cache()
def get_ingredient_service() -> IngredientService:
    """Get ingredient service instance"""
    return IngredientServiceImpl(
        api_url=settings.OCR_API_URL,
        model=settings.MODEL_ID,
    )


@lru_cache()
def get_cache_service() -> CacheService:
    """Get cache service instance"""
    return CacheService()
