import httpx
import asyncio
from typing import Optional, List, Dict
from urllib.parse import quote_plus
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import ImageProcessingException

logger = get_logger(__name__)


class ImageService:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.cse_id = settings.GOOGLE_CSE_ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.timeout = httpx.Timeout(10.0, connect=5.0)
        self.retry_attempts = 2
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 3600  # 1 hour

    async def get_dish_image(self, dish_name: str) -> Optional[str]:
        """Get the first image URL for a dish from Google Images with caching"""
        
        if not self.api_key or not self.cse_id:
            logger.warning("Google API credentials not configured, using fallback")
            return self._get_fallback_image(dish_name)
        
        # Check cache first
        cache_key = self._get_cache_key(dish_name)
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"Using cached image for {dish_name}")
            return cached_result
        
        try:
            # Optimize search query for Vietnamese dishes
            optimized_query = self._optimize_search_query(dish_name)
            
            params = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": optimized_query,
                "searchType": "image",
                "num": 3,  # Get multiple results to have fallbacks
                # "imgSize": "medium",
                "imgType": "photo",
                "safe": "active",
                # "gl": "vn",  # Prioritize Vietnamese results
                # "hl": "vi"   # Vietnamese language
            }

            logger.info(f"Searching image for dish: {dish_name} with query: {optimized_query}")

            image_url = await self._make_search_request(params)
            
            # Cache the result
            self._cache_result(cache_key, image_url)
            
            if image_url:
                logger.info(f"Found image for {dish_name}: {image_url}")
            else:
                logger.warning(f"No image found for {dish_name}")
                
            return image_url
                
        except Exception as e:
            logger.error(f"Error fetching image for {dish_name}: {str(e)}")
            # Return fallback instead of raising exception
            return self._get_fallback_image(dish_name)

    async def _make_search_request(self, params: dict) -> Optional[str]:
        """Make search request with retry logic"""
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(self.base_url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get("items", [])
                        
                        # Try to find a valid image URL
                        for item in items:
                            image_url = item.get("link")
                            if image_url and await self._validate_image_url(image_url):
                                return image_url
                        
                        return None  # No valid images found
                    
                    elif response.status_code == 429:  # Rate limited
                        logger.warning("Google API rate limit reached")
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                    
                    response.raise_for_status()
                    
            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"Image search timeout on attempt {attempt + 1}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                last_exception = e
                logger.error(f"Error in image search attempt {attempt + 1}: {str(e)}")
                break

        logger.warning(f"Image search failed after {self.retry_attempts} attempts: {str(last_exception)}")
        return None

    async def _validate_image_url(self, url: str) -> bool:
        """Validate that the image URL is accessible"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
                response = await client.head(url)
                content_type = response.headers.get("content-type", "")
                return response.status_code == 200 and content_type.startswith("image/")
        except:
            return False

    def _optimize_search_query(self, dish_name: str) -> str:
        """Optimize search query for better Vietnamese food results"""
        # Add Vietnamese food context
        query = f"Hình món ăn '{dish_name}'"
        
        # Clean up the query
        query = query.replace("  ", " ").strip()
        
        return query

    def _get_cache_key(self, dish_name: str) -> str:
        """Generate cache key for dish name"""
        return f"image:{dish_name.lower().strip()}"

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """Get result from cache if not expired"""
        if cache_key in self.cache:
            cached_time, cached_url = self.cache[cache_key]
            if (datetime.utcnow() - cached_time).total_seconds() < self.cache_ttl:
                return cached_url
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
        return None

    def _cache_result(self, cache_key: str, image_url: Optional[str]):
        """Cache the result with timestamp"""
        self.cache[cache_key] = (datetime.utcnow(), image_url)
        
        # Simple cache cleanup - remove oldest entries if cache gets too large
        if len(self.cache) > 100:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][0])
            del self.cache[oldest_key]

    def _get_fallback_image(self, dish_name: str) -> str:
        """Get fallback image for Vietnamese dishes"""
        fallback_images = {
            # Popular Vietnamese dishes with their fallback images
            "phở": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=400&q=80",
            "bún bò": "https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&q=80",
            "bánh mì": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&q=80",
            "cà phê": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400&q=80",
            "bánh xèo": "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80",
            "gỏi cuốn": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400&q=80",
            "cơm tấm": "https://images.unsplash.com/photo-1576777187466-a0bcfb88ec97?w=400&q=80",
            "chả cá": "https://images.unsplash.com/photo-1565895405229-71906ad8602b?w=400&q=80",
            "chè": "https://images.unsplash.com/photo-1562059390-a761a084768e?w=400&q=80"
        }
        
        dish_name_lower = dish_name.lower().strip()
        
        # Find matching fallback image
        for keyword, image_url in fallback_images.items():
            if keyword in dish_name_lower:
                logger.debug(f"Using fallback image for {dish_name}: {keyword}")
                return image_url
        
        # Default Vietnamese food image
        return "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80"

    async def get_batch_images(self, dish_names: List[str]) -> Dict[str, Optional[str]]:
        """Get images for multiple dishes efficiently"""
        if not dish_names:
            return {}
        
        # Limit batch size to avoid overwhelming the API
        dish_names = dish_names[:20]
        
        # Process requests with some delay to respect rate limits
        results = {}
        for i, dish_name in enumerate(dish_names):
            try:
                if i > 0:  # Add small delay between requests
                    await asyncio.sleep(0.1)
                
                image_url = await self.get_dish_image(dish_name)
                results[dish_name] = image_url
                
            except Exception as e:
                logger.error(f"Error getting image for {dish_name}: {e}")
                results[dish_name] = self._get_fallback_image(dish_name)
        
        return results

    def clear_cache(self):
        """Clear the image cache"""
        self.cache.clear()
        logger.info("Image cache cleared")

    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        now = datetime.utcnow()
        valid_entries = 0
        
        for cached_time, _ in self.cache.values():
            if (now - cached_time).total_seconds() < self.cache_ttl:
                valid_entries += 1
        
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "cache_ttl_seconds": self.cache_ttl
        }