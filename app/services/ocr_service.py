import base64
import httpx
import json
import re
import asyncio
import requests
from typing import List, Optional, Union
from app.models.schemas import OCRResult, DishInfo
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OCRService:
    def __init__(self, api_url: str = None, headers: dict = None, model: str = "gpt-4"):
        self.api_url = api_url
        self.model = model
        self.headers = headers or {
            "Content-Type": "application/json",
            # "Authorization": f"Bearer {settings.OPENAI_API_KEY}"  # hoặc "dummy-key" nếu dùng vLLM
        }

        if not self.api_url:
            raise ValueError("API URL must be provided for OCRService")

    async def extract_menu_text(self, image: Union[bytes, str]) -> OCRResult:
        try:
            if isinstance(image, bytes):
                image_base64 = base64.b64encode(image).decode("utf-8")
                image_url = f"data:image/jpeg;base64,{image_base64}"
            elif isinstance(image, str) and image.startswith(("http://", "https://")):
                image_url = image
            else:
                raise ValueError("Input must be bytes or a valid image URL.")

            prompt = self._create_menu_extraction_prompt()

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ]
                    }
                ],
                "max_tokens": 800,
                "temperature": 0.3,
                "top_p": 0.9
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url=f"{self.api_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )

                if response.status_code == 503:
                    await asyncio.sleep(10)
                    response = await client.post(
                        url=f"{self.api_url}/chat/completions",
                        headers=self.headers,
                        json=payload
                    )

                response.raise_for_status()
                logger.info(f"OCR response: {response.status_code} - {response.text}")
                result = response.json()

                content = result["choices"][0]["message"]["content"]
                logger.info(f"Raw OCR content: {content}")
                dishes = self._parse_menu_text(content)

                logger.info(f"Extracted {len(dishes)} dishes from menu")
                return OCRResult(dishes=dishes, raw_text=content)

        except Exception as e:
            logger.error(f"Error extracting menu text: {str(e)}")
            raise Exception(f"Failed to extract menu text: {str(e)}")

    def _create_menu_extraction_prompt(self) -> str:
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

    def _normalize_price(self, price_str: Optional[str]) -> Optional[str]:
        if not price_str:
            return None
        price_str = price_str.lower().replace("đ", "").replace("vnd", "").strip()
        if 'k' in price_str:
            return str(int(float(price_str.replace('k', '').strip()) * 1000))
        return price_str.replace(",", "").strip()
    
    def _extract_json_block(self, text: str) -> Optional[str]:
        """
        Extract JSON block from markdown-style text.
        E.g. ```json { ... } ``` => return the inner JSON string
        """
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        return None

    def _parse_menu_text(self, text: str) -> List[DishInfo]:
        dishes = []
        try:
            text = text.strip()

            # Check and extract JSON from markdown block if needed
            if text.startswith("```json"):
                extracted = self._extract_json_block(text)
                if extracted:
                    text = extracted    
                text = extracted

            if text.strip().startswith('{'):
                data = json.loads(text)
                if "dishes" in data:
                    for d in data["dishes"]:
                        name = d.get("name")
                        price = d.get("price")
                        if name:
                            dishes.append(
                                DishInfo(name=name.strip(), price=self._normalize_price(price))
                            )
                    return dishes  # Đảm bảo không chạy tiếp nếu parse được JSON

            # Fallback: parse text using regex
            lines = text.split('\n')
            pattern = r'^(.*?)[\s\-:]+(\d+(?:[.,]\d+)?(?:\s*(?:k|đ|vnd))?)$'
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    price = match.group(2).strip()
                    name = re.sub(r'^[\d\.-]+\s*', '', name)
                    name = re.sub(r'\s*[\d\.-]+$', '', name)
                    if name and len(name) > 2:
                        dishes.append(DishInfo(name=name, price=self._normalize_price(price)))

            if not dishes:
                logger.warning("No dishes found from regex fallback")

        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON, using regex fallback")

        return dishes

