import httpx
import asyncio
from typing import Optional
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class IngredientService:
    """Simplified service to generate basic ingredient lists"""
    
    def __init__(self, api_url: str = None, headers: dict = None, model: str = "gpt-4"):
        self.api_url = api_url
        self.model = model
        self.headers = headers or {
            "Content-Type": "application/json",
        }
        self.timeout = httpx.Timeout(30.0, connect=5.0)
        self.retry_attempts = 2

        if not self.api_url:
            raise ValueError("API URL must be provided for IngredientService")

    async def generate_ingredients(self, dish_name: str) -> str:
        """Generate simple ingredient text for a Vietnamese dish"""
        
        if not dish_name or not dish_name.strip():
            return ""
        
        try:
            prompt = self._create_ingredient_prompt(dish_name.strip())
            payload = self._create_payload(prompt)
            
            # Generate ingredients with retry logic
            ingredient_text = await self._make_api_request(payload)
            
            # Clean and format the response
            ingredients = self._format_ingredients(ingredient_text)
            
            logger.info(f"Generated ingredients for '{dish_name}': {ingredients}")
            return ingredients
                
        except Exception as e:
            logger.error(f"Error generating ingredients for {dish_name}: {str(e)}")
            # Return empty string instead of raising exception
            return ""

    def _create_payload(self, prompt: str) -> dict:
        """Create API request payload for ingredient generation"""
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                    ]
                }
            ],
            "max_tokens": 80,  # Short response for ingredients only
            "temperature": 0.2,
            "top_p": 0.85
        }

    async def _make_api_request(self, payload: dict) -> str:
        """Make API request with retry logic"""
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url=f"{self.api_url}/chat/completions",
                        headers=self.headers,
                        json=payload
                    )
                    
                    if response.status_code == 503:
                        logger.warning(f"Service unavailable for ingredient generation, attempt {attempt + 1}")
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(2)
                            continue
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    ingredient_text = result["choices"][0]["message"]["content"]
                    
                    logger.debug(f"Ingredient API response received successfully")
                    return ingredient_text

            except Exception as e:
                last_exception = e
                logger.warning(f"Error in ingredient generation attempt {attempt + 1}: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(1)

        # Don't raise exception, return empty result
        logger.warning(f"Ingredient generation failed after {self.retry_attempts} attempts: {str(last_exception)}")
        return ""

    def _create_ingredient_prompt(self, dish_name: str) -> str:
        """Create prompt for Vietnamese ingredient generation"""
        return f"""
        Liệt kê 4-5 nguyên liệu chính của món "{dish_name}" theo định dạng ngắn gọn.
        
        Chỉ trả về danh sách nguyên liệu cách nhau bằng dấu phẩy, không giải thích.
        
        Ví dụ: "Thịt bò, bánh phở, hành lá, gừng, quế"
        """

    def _format_ingredients(self, text: str) -> str:
        """Clean and format ingredient text"""
        if not text or not text.strip():
            return ""
        
        # Clean the text
        ingredients = text.strip()
        
        # Remove any unwanted prefixes/suffixes
        ingredients = ingredients.replace("Nguyên liệu:", "").strip()
        ingredients = ingredients.replace("Ingredients:", "").strip()
        
        # Remove quotes if present
        if ingredients.startswith('"') and ingredients.endswith('"'):
            ingredients = ingredients[1:-1]
        
        # Limit length
        if len(ingredients) > 200:
            ingredients = ingredients[:200] + "..."
        
        return ingredients