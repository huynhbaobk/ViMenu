"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, Mock
from app.main import app
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    """Async HTTP client for testing"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock = AsyncMock()
    mock.ping.return_value = True
    mock.setex.return_value = True
    mock.get.return_value = None
    mock.delete.return_value = 1
    mock.keys.return_value = []
    return mock


@pytest.fixture
def mock_ocr_service():
    """Mock OCR service"""
    from app.models.schemas import OCRResult, DishInfo
    
    mock = AsyncMock()
    mock.extract_menu_text.return_value = OCRResult(
        dishes=[
            DishInfo(name="Phở Bò", price="30.000đ"),
            DishInfo(name="Bánh Mì", price="15.000đ")
        ],
        raw_text="Phở Bò 30.000đ\nBánh Mì 15.000đ"
    )
    return mock


@pytest.fixture
def mock_image_service():
    """Mock image service"""
    mock = AsyncMock()
    mock.get_dish_image.return_value = "https://example.com/image.jpg"
    return mock


@pytest.fixture
def mock_recipe_service():
    """Mock recipe service"""
    mock = AsyncMock()
    mock.generate_recipe.return_value = {
        "ingredients": ["Thịt bò", "Bánh phở", "Hành lá"]
    }
    return mock


@pytest.fixture
def sample_image_bytes():
    """Sample image bytes for testing"""
    # Create a minimal valid JPEG
    return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'


@pytest.fixture
def override_settings():
    """Override settings for testing"""
    original_settings = settings.copy()
    
    # Override for testing
    settings.USE_MOCK_SERVICES = True
    settings.REDIS_URL = "redis://localhost:6379/1"  # Use different DB for tests
    
    yield settings
    
    # Restore original settings
    for key, value in original_settings.items():
        setattr(settings, key, value)
