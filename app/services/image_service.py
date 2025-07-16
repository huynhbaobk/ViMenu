import httpx
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ImageService:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.cse_id = settings.GOOGLE_CSE_ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def get_dish_image(self, dish_name: str) -> Optional[str]:
        """Get the first image URL for a dish from Google Images"""
        
        if not self.api_key or not self.cse_id:
            logger.error("Google API credentials not configured")
            raise Exception("Image service not properly configured")
        
        try:
            params = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": f"{dish_name} Vietnamese food",
                "searchType": "image",
                "num": 1,
                "imgSize": "medium",
                "safe": "high"
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    if items:
                        image_url = items[0]["link"]
                        logger.info(f"Found image for {dish_name}: {image_url}")
                        return image_url
                
                logger.warning(f"No image found for {dish_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching image for {dish_name}: {str(e)}")
            raise Exception(f"Failed to fetch image for {dish_name}: {str(e)}")