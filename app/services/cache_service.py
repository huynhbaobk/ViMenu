import json
import redis.asyncio as redis
from typing import Optional
from datetime import timedelta
from app.models.schemas import MenuAnalysisResponse
from app.core.config import settings
from app.core.logging import get_logger
from app.services.recipe_service import RecipeService

logger = get_logger(__name__)


class CacheService:
    def __init__(self):
        self.redis_client = None
        self.recipe_service = RecipeService(
            api_url=settings.OCR_API_URL,
            model=settings.MODEL_ID,
        )
        self.default_ttl = timedelta(hours=24)

    async def _get_redis_client(self):
        """Get or create Redis client"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True
                )
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                return None
        return self.redis_client

    async def cache_analysis(self, request_id: str, response: MenuAnalysisResponse) -> bool:
        """Cache menu analysis result"""
        try:
            client = await self._get_redis_client()
            if not client:
                # For testing without Redis, just log and return success
                logger.info(f"Mock: Would cache analysis for request {request_id}")
                return True

            key = f"analysis:{request_id}"
            value = response.model_dump_json()
            await client.setex(key, self.default_ttl, value)
            
            logger.info(f"Cached analysis for request {request_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching analysis: {e}")
            return False

    async def get_analysis(self, request_id: str) -> Optional[MenuAnalysisResponse]:
        """Get cached menu analysis"""
        try:
            client = await self._get_redis_client()
            if not client:
                # For testing without Redis, return None
                return None

            key = f"analysis:{request_id}"
            value = await client.get(key)
            
            if value:
                data = json.loads(value)
                return MenuAnalysisResponse(**data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached analysis: {e}")
            return None

    async def cache_ingredients(self, request_id: str, dish_name: str, ingredients: list) -> bool:
        """Cache ingredients for a dish"""
        try:
            client = await self._get_redis_client()
            if not client:
                # For testing without Redis, just log and return success
                logger.info(f"Mock: Would cache ingredients for {dish_name} in request {request_id}")
                return True

            key = f"ingredients:{request_id}:{dish_name}"
            value = json.dumps(ingredients)
            await client.setex(key, self.default_ttl, value)
            
            logger.info(f"Cached ingredients for {dish_name} in request {request_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching ingredients: {e}")
            return False

    async def get_ingredients(self, request_id: str, dish_name: str) -> Optional[list]:
        """Get cached ingredients for a dish"""
        try:
            client = await self._get_redis_client()
            if not client:
                # For testing without Redis, return None to trigger generation
                return None

            key = f"ingredients:{request_id}:{dish_name}"
            value = await client.get(key)
            
            if value:
                logger.info(f"Retrieved cached ingredients for {dish_name} in request {request_id}")
                return json.loads(value)
            
            logger.info(f"No cached ingredients found for {dish_name} in request {request_id}")
            return None
        
        except Exception as e:
            logger.error(f"Error getting cached ingredients: {e}")
            return None

    async def generate_and_cache_ingredients(self, request_id: str, dish) -> None:
        """Generate ingredients and cache them"""
        try:
            # Get dish name - handle both object and dict
            dish_name = dish.name if hasattr(dish, 'name') else dish['name'] if isinstance(dish, dict) else str(dish)
            
            # Check if ingredients already exist
            cached_ingredients = await self.get_ingredients(request_id, dish_name)
            if cached_ingredients:
                # Update dish with ingredients
                if hasattr(dish, 'ingredients'):
                    dish.ingredients = cached_ingredients
                elif isinstance(dish, dict):
                    dish['ingredients'] = cached_ingredients
                logger.info(f"Using cached ingredients for {dish_name}: {cached_ingredients}")
                return

            # Generate ingredients from recipe service
            recipe = await self.recipe_service.generate_recipe(dish_name)
            
            # Handle both Recipe object and dict
            if hasattr(recipe, 'ingredients'):
                ingredients = recipe.ingredients
            elif isinstance(recipe, dict) and 'ingredients' in recipe:
                ingredients = recipe['ingredients']
            elif isinstance(recipe, str):
                ingredients = recipe.split(",")
            else:
                ingredients = []

            logger.info(f"Last result generated ingredients for {dish_name}: {ingredients}")
            
            # Cache the ingredients
            await self.cache_ingredients(request_id, dish_name, ingredients)
            
            # Update the dish object
            if hasattr(dish, 'ingredients'):
                dish.ingredients = ingredients
            elif isinstance(dish, dict):
                dish['ingredients'] = ingredients
            
            # Also update the cached analysis
            analysis = await self.get_analysis(request_id)
            if analysis:
                for d in analysis.dishes:
                    if d.name == dish.name:
                        d.ingredients = ingredients
                        break
                await self.cache_analysis(request_id, analysis)
            
            logger.info(f"Generated and cached ingredients for {dish.name}")
            
        except Exception as e:
            logger.error(f"Error generating ingredients for {dish.name}: {e}")
            # Set empty ingredients on error
            dish.ingredients = []

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            client = await self._get_redis_client()
            if not client:
                return {"status": "disconnected", "keys": 0}

            keys = await client.keys("*")
            return {
                "status": "connected",
                "total_keys": len(keys),
                "analysis_keys": len([k for k in keys if k.startswith("analysis:")]),
                "recipe_keys": len([k for k in keys if k.startswith("recipe:")])
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "message": str(e)}

    async def clear_cache(self) -> bool:
        """Clear all cached data"""
        try:
            client = await self._get_redis_client()
            if not client:
                return False

            keys = await client.keys("*")
            if keys:
                await client.delete(*keys)
                
            logger.info("Cache cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            await self.redis_client.connection_pool.disconnect()