import base64
import httpx
import json
import re
import asyncio
from typing import List
from app.models.schemas import OCRResult, DishInfo
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OCRService:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/Viet-Mistral/Vintern-1B"
        self.headers = {
            "Authorization": f"Bearer {settings.HF_API_TOKEN}",
            "Content-Type": "application/json"
        }

    async def extract_menu_text(self, image_bytes: bytes) -> OCRResult:
        """Extract menu text from image using Vintern-1B"""
        
        try:
            # Convert image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Prepare prompt for Vietnamese menu extraction
            prompt = self._create_menu_extraction_prompt()
            
            payload = {
                "inputs": {
                    "image": f"data:image/jpeg;base64,{image_base64}",
                    "question": prompt
                },
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.3,
                    "top_p": 0.9
                }
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
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
                result = response.json()
                
                # Parse the response
                raw_text = result.get("answer", "")
                dishes = self._parse_menu_text(raw_text)
                
                logger.info(f"Extracted {len(dishes)} dishes from menu")
                
                return OCRResult(
                    dishes=dishes,
                    raw_text=raw_text
                )
                
        except Exception as e:
            logger.error(f"Error extracting menu text: {str(e)}")
            raise Exception(f"Failed to extract menu text: {str(e)}")

    def _create_menu_extraction_prompt(self) -> str:
        """Create prompt for Vietnamese menu extraction"""
        return """
        Trích xuất danh sách các món ăn và giá tiền từ ảnh menu bằng tiếng Việt.
        
        Định dạng trả về JSON:
        {
            "dishes": [
                {
                    "name": "Tên món ăn",
                    "price": "Giá tiền (nếu có)"
                }
            ]
        }
        
        Chỉ trả về JSON, không giải thích thêm.
        """

    def _parse_menu_text(self, text: str) -> List[DishInfo]:
        """Parse text to extract dish names and prices"""
        dishes = []
        
        try:
            # Try to parse as JSON first
            if text.strip().startswith('{'):
                data = json.loads(text)
                if "dishes" in data:
                    return [DishInfo(name=d["name"], price=d.get("price")) 
                           for d in data["dishes"]]
            
            # Fallback to regex parsing
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Vietnamese dish name and price patterns
                patterns = [
                    r'^(.*?)(?:\s+(\d+(?:\.\d+)?(?:\s*(?:k|đ|vnd))?))?$',
                    r'^(.*?)\s+(\d+(?:\.\d+)?)\s*(?:k|đ|vnd)?$',
                    r'^(.*?)\s+([\d,]+)\s*(?:k|đ|vnd)?$'
                ]
                
                for pattern in patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        name = match.group(1).strip()
                        price = match.group(2) if match.group(2) else None
                        
                        # Clean up dish name
                        name = re.sub(r'^[\d\.-]+\s*', '', name)
                        name = re.sub(r'\s*[\d\.-]+$', '', name)
                        name = name.strip()
                        
                        if name and len(name) > 2:  # Filter out very short names
                            dishes.append(DishInfo(name=name, price=price))
                        break
        
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON, using regex fallback")
        
        return dishes

