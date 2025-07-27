import json
import redis.asyncio as redis
from typing import Optional
from datetime import timedelta
from contextlib import asynccontextmanager

from app.models.schemas import MenuAnalysisResponse
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    def __init__(self):
        self._redis_client = None
        self.default_ttl = timedelta(hours=24)
        self.connection_pool = None

    async def _get_redis_client(self):
        """Get or create Redis client with connection pooling"""
        if self._redis_client is None:
            try:
                if self.connection_pool is None:
                    self.connection_pool = redis.ConnectionPool.from_url(
                        settings.REDIS_URL,
                        decode_responses=True,
                        max_connections=10,
                        retry_on_timeout=True
                    )
                
                self._redis_client = redis.Redis(connection_pool=self.connection_pool)
                # Test connection
                await self._redis_client.ping()
                logger.info("Redis connection established")
                
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                return None
        return self._redis_client

    @asynccontextmanager
    async def get_redis_connection(self):
        """Context manager for Redis operations"""
        client = await self._get_redis_client()
        try:
            yield client
        except Exception as e:
            logger.error(f"Redis operation failed: {e}")
            yield None

    async def cache_analysis(self, request_id: str, response: MenuAnalysisResponse) -> bool:
        """Cache menu analysis result"""
        async with self.get_redis_connection() as client:
            if not client:
                logger.info(f"Mock: Would cache analysis for request {request_id}")
                return True

            try:
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
        async with self.get_redis_connection() as client:
            if not client:
                return None

            try:
                key = f"analysis:{request_id}"
                value = await client.get(key)
                
                if value:
                    data = json.loads(value)
                    return MenuAnalysisResponse(**data)
                
                return None
                
            except Exception as e:
                logger.error(f"Error getting cached analysis: {e}")
                return None

    async def cache_ingredients(self, request_id: str, dish_name: str, ingredients: str) -> bool:
        """Cache ingredients for a dish"""
        async with self.get_redis_connection() as client:
            if not client:
                logger.info(f"Mock: Would cache ingredients for {dish_name} in request {request_id}")
                return True

            try:
                key = f"ingredients:{request_id}:{dish_name}"
                await client.setex(key, self.default_ttl, ingredients)
                
                logger.info(f"Cached ingredients for {dish_name} in request {request_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error caching ingredients: {e}")
                return False

    async def get_ingredients(self, request_id: str, dish_name: str) -> Optional[str]:
        """Get cached ingredients for a dish"""
        async with self.get_redis_connection() as client:
            if not client:
                return None

            try:
                key = f"ingredients:{request_id}:{dish_name}"
                value = await client.get(key)
                
                if value:
                    logger.info(f"Retrieved cached ingredients for {dish_name} in request {request_id}")
                    return value
                
                logger.info(f"No cached ingredients found for {dish_name} in request {request_id}")
                return None
            
            except Exception as e:
                logger.error(f"Error getting cached ingredients: {e}")
                return None

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        async with self.get_redis_connection() as client:
            if not client:
                return {"status": "disconnected", "keys": 0}

            try:
                keys = await client.keys("*")
                return {
                    "status": "connected",
                    "total_keys": len(keys),
                    "analysis_keys": len([k for k in keys if k.startswith("analysis:")]),
                    "ingredients_keys": len([k for k in keys if k.startswith("ingredients:")])
                }
                
            except Exception as e:
                logger.error(f"Error getting cache stats: {e}")
                return {"status": "error", "message": str(e)}

    async def clear_cache(self) -> bool:
        """Clear all cached data"""
        async with self.get_redis_connection() as client:
            if not client:
                return False

            try:
                keys = await client.keys("*")
                if keys:
                    await client.delete(*keys)
                    
                logger.info("Cache cleared successfully")
                return True
                
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
                return False

    async def close(self):
        """Close Redis connection and cleanup"""
        if self._redis_client:
            await self._redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()