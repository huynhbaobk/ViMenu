import httpx
import asyncio
from typing import List, Dict
from app.core.config import settings
from app.core.logging import get_logger
import re

logger = get_logger(__name__)


class RecipeService:
    def __init__(self, api_url: str = None, headers: dict = None, model: str = "gpt-4"):
        self.api_url = api_url
        self.model = model
        self.headers = headers or {
            "Content-Type": "application/json",
            # "Authorization": f"Bearer {settings.OPENAI_API_KEY}"  # hoặc "dummy-key" nếu dùng vLLM
        }

        if not self.api_url:
            raise ValueError("API URL must be provided for OCRService")


    async def generate_recipe(self, dish_name: str) -> str:
        """Generate a recipe for a Vietnamese dish using AI"""
        
        try:
            prompt = self._create_recipe_prompt(dish_name)
            

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                        ]
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.2,
                "top_p": 0.85,
                "top_k": 20,
                "repetition_penalty": 1.1
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url=f"{self.api_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 503:
                    # Model is loading, wait and retry
                    await asyncio.sleep(10)
                    response = await client.post(
                        self.api_url,
                        headers=self.headers,
                        json=payload
                    )
                
                response.raise_for_status()
                logger.info(f"Recipe generation response: {response.status_code} - {response.text}")
                result = response.json()
                
                recipe_text = result["choices"][0]["message"]["content"]                
                # Parse the recipe text
                # recipe = self._parse_recipe_text(dish_name, recipe_text)

                logger.info(f"Generated recipe for {dish_name}: {recipe_text}")
                return {"ingredients": recipe_text}
                
        except Exception as e:
            logger.error(f"Error generating recipe for {dish_name}: {str(e)}")
            raise Exception(f"Failed to generate recipe for {dish_name}: {str(e)}")

    def _create_recipe_prompt(self, dish_name: str) -> str:
        """Create prompt for Vietnamese recipe generation"""
        return f"""Hãy liệt kê 5 tên nguyên liệu chính và đặc trưng cho món <{dish_name}>.Không mô tả món ăn hay giải thích cách làm. Theo định dạng: 1. Tên 1\n2. Tên 2\n3. Tên 3
        """

