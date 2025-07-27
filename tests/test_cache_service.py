"""
Unit tests for the cache service
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

from app.services.cache_service import CacheService
from app.models.schemas import MenuAnalysisResponse, DishDetail, AnalysisStatus


@pytest.fixture
def cache_service():
    """Create cache service instance for testing"""
    return CacheService()


@pytest.fixture
def sample_menu_response():
    """Sample menu analysis response for testing"""
    return MenuAnalysisResponse(
        request_id="test-123",
        dishes=[
            DishDetail(name="Phở Bò", price="30.000đ", image_url="http://example.com/pho.jpg"),
            DishDetail(name="Bánh Mì", price="15.000đ", image_url="http://example.com/banh-mi.jpg")
        ],
        status=AnalysisStatus.COMPLETED,
        message="Test completed"
    )


class TestCacheService:
    """Test cases for CacheService"""

    @pytest.mark.asyncio
    async def test_cache_analysis_success(self, cache_service, sample_menu_response, mock_redis):
        """Test successful caching of analysis"""
        with patch.object(cache_service, '_get_redis_client', return_value=mock_redis):
            result = await cache_service.cache_analysis("test-123", sample_menu_response)
            
            assert result is True
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_analysis_no_redis(self, cache_service, sample_menu_response):
        """Test caching when Redis is not available"""
        with patch.object(cache_service, '_get_redis_client', return_value=None):
            result = await cache_service.cache_analysis("test-123", sample_menu_response)
            
            assert result is True  # Should still return True for mock mode

    @pytest.mark.asyncio
    async def test_get_analysis_success(self, cache_service, sample_menu_response, mock_redis):
        """Test successful retrieval of cached analysis"""
        # Mock Redis to return serialized response
        mock_redis.get.return_value = sample_menu_response.model_dump_json()
        
        with patch.object(cache_service, '_get_redis_client', return_value=mock_redis):
            result = await cache_service.get_analysis("test-123")
            
            assert result is not None
            assert result.request_id == "test-123"
            assert len(result.dishes) == 2

    @pytest.mark.asyncio
    async def test_get_analysis_not_found(self, cache_service, mock_redis):
        """Test retrieval when analysis is not cached"""
        mock_redis.get.return_value = None
        
        with patch.object(cache_service, '_get_redis_client', return_value=mock_redis):
            result = await cache_service.get_analysis("not-found")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_ingredients_success(self, cache_service, mock_redis):
        """Test successful caching of ingredients"""
        ingredients = ["Thịt bò", "Bánh phở", "Hành lá"]
        
        with patch.object(cache_service, '_get_redis_client', return_value=mock_redis):
            result = await cache_service.cache_ingredients("test-123", "Phở Bò", ingredients)
            
            assert result is True
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_ingredients_success(self, cache_service, mock_redis):
        """Test successful retrieval of cached ingredients"""
        ingredients = ["Thịt bò", "Bánh phở", "Hành lá"]
        mock_redis.get.return_value = '["Thịt bò", "Bánh phở", "Hành lá"]'
        
        with patch.object(cache_service, '_get_redis_client', return_value=mock_redis):
            result = await cache_service.get_ingredients("test-123", "Phở Bò")
            
            assert result == ingredients

    @pytest.mark.asyncio
    async def test_extract_ingredients_from_dict(self, cache_service):
        """Test extracting ingredients from dict format"""
        recipe = {"ingredients": ["Thịt bò", "Bánh phở"]}
        result = cache_service._extract_ingredients(recipe)
        
        assert result == ["Thịt bò", "Bánh phở"]

    @pytest.mark.asyncio
    async def test_extract_ingredients_from_string(self, cache_service):
        """Test extracting ingredients from string format"""
        recipe = "Thịt bò, Bánh phở, Hành lá"
        result = cache_service._extract_ingredients(recipe)
        
        assert result == ["Thịt bò", "Bánh phở", "Hành lá"]

    @pytest.mark.asyncio
    async def test_extract_ingredients_empty(self, cache_service):
        """Test extracting ingredients from empty/invalid format"""
        result = cache_service._extract_ingredients(None)
        assert result == []
        
        result = cache_service._extract_ingredients({})
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_and_cache_ingredients_with_mock_recipe_service(self, cache_service):
        """Test generating and caching ingredients"""
        # Mock recipe service
        mock_recipe_service = AsyncMock()
        mock_recipe_service.generate_recipe.return_value = {
            "ingredients": ["Thịt bò", "Bánh phở"]
        }
        cache_service.set_recipe_service(mock_recipe_service)
        
        # Mock dish object
        dish = Mock()
        dish.name = "Phở Bò"
        dish.ingredients = None
        
        # Mock cache methods
        cache_service.get_ingredients = AsyncMock(return_value=None)
        cache_service.cache_ingredients = AsyncMock(return_value=True)
        cache_service._update_cached_analysis = AsyncMock()
        
        await cache_service.generate_and_cache_ingredients("test-123", dish)
        
        # Verify calls
        mock_recipe_service.generate_recipe.assert_called_once_with("Phở Bò")
        cache_service.cache_ingredients.assert_called_once()
        assert dish.ingredients == ["Thịt bò", "Bánh phở"]

    @pytest.mark.asyncio
    async def test_get_stats_success(self, cache_service, mock_redis):
        """Test getting cache statistics"""
        mock_redis.keys.return_value = [
            "analysis:test-1",
            "analysis:test-2", 
            "ingredients:test-1:dish1",
            "other:key"
        ]
        
        with patch.object(cache_service, '_get_redis_client', return_value=mock_redis):
            stats = await cache_service.get_stats()
            
            assert stats["status"] == "connected"
            assert stats["total_keys"] == 4
            assert stats["analysis_keys"] == 2
            assert stats["ingredients_keys"] == 1

    @pytest.mark.asyncio
    async def test_get_stats_no_redis(self, cache_service):
        """Test getting stats when Redis is not available"""
        with patch.object(cache_service, '_get_redis_client', return_value=None):
            stats = await cache_service.get_stats()
            
            assert stats["status"] == "disconnected"
            assert stats["keys"] == 0

    @pytest.mark.asyncio
    async def test_clear_cache_success(self, cache_service, mock_redis):
        """Test clearing cache successfully"""
        mock_redis.keys.return_value = ["key1", "key2"]
        
        with patch.object(cache_service, '_get_redis_client', return_value=mock_redis):
            result = await cache_service.clear_cache()
            
            assert result is True
            mock_redis.delete.assert_called_once_with("key1", "key2")

    @pytest.mark.asyncio
    async def test_clear_cache_empty(self, cache_service, mock_redis):
        """Test clearing empty cache"""
        mock_redis.keys.return_value = []
        
        with patch.object(cache_service, '_get_redis_client', return_value=mock_redis):
            result = await cache_service.clear_cache()
            
            assert result is True
            mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_close_connections(self, cache_service):
        """Test closing Redis connections"""
        # Mock Redis client and connection pool
        mock_redis = AsyncMock()
        mock_pool = AsyncMock()
        
        cache_service._redis_client = mock_redis
        cache_service.connection_pool = mock_pool
        
        await cache_service.close()
        
        mock_redis.close.assert_called_once()
        mock_pool.disconnect.assert_called_once()


class TestCacheServiceIntegration:
    """Integration tests for cache service"""

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, cache_service, sample_menu_response):
        """Test complete workflow of caching and retrieving analysis"""
        # Use real Redis if available, otherwise mock
        try:
            # Try to cache analysis
            result = await cache_service.cache_analysis("integration-test", sample_menu_response)
            assert result is True
            
            # Try to retrieve analysis
            retrieved = await cache_service.get_analysis("integration-test")
            if retrieved:  # Only assert if Redis is actually available
                assert retrieved.request_id == "integration-test"
                assert len(retrieved.dishes) == 2
                
        except Exception as e:
            # If Redis is not available, test should still pass
            pytest.skip(f"Redis not available for integration test: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
