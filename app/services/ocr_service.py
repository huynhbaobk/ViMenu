import base64
import httpx
import json
import re
import asyncio
from typing import List, Optional, Union
from datetime import datetime

from app.models.schemas import OCRResult, DishInfo
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import OCRException

logger = get_logger(__name__)


class OCRService:
    def __init__(self, api_url: str = None, headers: dict = None, model: str = "gpt-4"):
        self.api_url = api_url
        self.model = model
        self.headers = headers or {
            "Content-Type": "application/json",
        }
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.retry_attempts = 3
        self.retry_delay = 1.0

        if not self.api_url:
            raise ValueError("API URL must be provided for OCRService")

    async def extract_menu_text(self, image: Union[bytes, str]) -> OCRResult:
        """Extract menu text with retry logic and error handling"""
        start_time = datetime.utcnow()
        
        try:
            image_url = self._prepare_image(image)
            prompt = self._create_menu_extraction_prompt()
            payload = self._create_payload(prompt, image_url)
            
            # Extract text with retry logic
            content = await self._make_api_request(payload)
            
            # Parse the response
            dishes = self._parse_menu_text(content)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Extracted {len(dishes)} dishes from menu in {processing_time:.2f}s")
            
            return OCRResult(
                dishes=dishes, 
                raw_text=content,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Error extracting menu text: {str(e)}")
            raise OCRException(f"Failed to extract menu text: {str(e)}")

    def _prepare_image(self, image: Union[bytes, str]) -> str:
        """Prepare image for API request"""
        if isinstance(image, bytes):
            # Validate image size
            if len(image) > settings.MAX_FILE_SIZE:
                raise OCRException(f"Image too large: {len(image)} bytes")
            
            image_base64 = base64.b64encode(image).decode("utf-8")
            return f"data:image/jpeg;base64,{image_base64}"
            
        elif isinstance(image, str) and image.startswith(("http://", "https://")):
            return image
        else:
            raise OCRException("Input must be bytes or a valid image URL")

    def _create_payload(self, prompt: str, image_url: str) -> dict:
        """Create API request payload"""
        return {
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
                        logger.warning(f"Service unavailable, attempt {attempt + 1}/{self.retry_attempts}")
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue

                    response.raise_for_status()
                    
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    logger.info(f"OCR API response received successfully")
                    return content

            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"Request timeout on attempt {attempt + 1}/{self.retry_attempts}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    
            except httpx.HTTPStatusError as e:
                last_exception = e
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                if e.response.status_code >= 500 and attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                else:
                    break
                    
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                break

        raise OCRException(f"API request failed after {self.retry_attempts} attempts: {str(last_exception)}")

    def _create_menu_extraction_prompt(self) -> str:
        """Create optimized prompt for menu extraction"""
        return """
        Trích xuất danh sách các món ăn và giá tiền từ ảnh menu bằng tiếng Việt.
        
        Yêu cầu:
        - Chỉ trích xuất món ăn và giá tiền
        - Bỏ qua các mục không phải món ăn (đồ uống có thể bao gồm)
        - Giữ nguyên tên món ăn
        - Chuẩn hóa giá tiền về định dạng số + đơn vị

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
        """Normalize price string"""
        if not price_str:
            return None
            
        # Remove common currency symbols and normalize
        price_str = price_str.lower().strip()
        price_str = re.sub(r'[đvnd]', '', price_str).strip()
        
        # Handle "k" suffix (thousands)
        if 'k' in price_str:
            try:
                number = float(re.sub(r'[^0-9.,k]', '', price_str).replace('k', ''))
                return f"{int(number * 1000):,}đ"
            except ValueError:
                pass
        
        # Extract numbers and reformat
        numbers = re.findall(r'[\d.,]+', price_str)
        if numbers:
            try:
                # Take the largest number found
                number = max([float(n.replace(',', '')) for n in numbers])
                return f"{int(number):,}đ"
            except ValueError:
                pass
                
        return price_str

    def _extract_json_block(self, text: str) -> Optional[str]:
        """Extract JSON block from markdown-style text"""
        patterns = [
            r"```json\s*(\{.*?\})\s*```",  # Markdown JSON block
            r"```\s*(\{.*?\})\s*```",      # Generic code block
            r"(\{.*?\})",                   # Direct JSON
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1)
        
        return None

    def _parse_menu_text(self, text: str) -> List[DishInfo]:
        """Parse menu text with improved error handling"""
        dishes = []
        
        try:
            text = text.strip()

            # Extract JSON if wrapped in markdown
            json_content = self._extract_json_block(text)
            if json_content:
                text = json_content

            # Try to parse as JSON first
            if text.startswith('{'):
                try:
                    data = json.loads(text)
                    if "dishes" in data and isinstance(data["dishes"], list):
                        for dish_data in data["dishes"]:
                            if isinstance(dish_data, dict) and "name" in dish_data:
                                name = dish_data["name"].strip()
                                price = dish_data.get("price")
                                
                                if name and len(name) > 1:  # Minimum name length
                                    dishes.append(
                                        DishInfo(
                                            name=name, 
                                            price=self._normalize_price(price)
                                        )
                                    )
                        
                        if dishes:  # If we successfully parsed JSON, return it
                            return dishes
                            
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse error: {e}, falling back to regex")

            # Fallback: parse text using regex patterns
            dishes = self._parse_with_regex(text)

        except Exception as e:
            logger.error(f"Error parsing menu text: {e}")
            
        return dishes

    def _parse_with_regex(self, text: str) -> List[DishInfo]:
        """Parse text using regex patterns as fallback"""
        dishes = []
        lines = text.split('\n')
        
        # Multiple regex patterns for different menu formats
        patterns = [
            r'^(.+?)[\s\-:\.]+(\d+(?:[.,]\d+)?(?:\s*(?:k|đ|vnd|vnđ|dong))?)$',  # Name - Price
            r'^(\d+)\.\s*(.+?)[\s\-:]+(\d+(?:[.,]\d+)?(?:\s*(?:k|đ|vnd))?)$',   # Number. Name - Price
            r'^(.+?)\s+(\d+(?:[.,]\d+)?(?:\s*(?:k|đ|vnd))?)$',                  # Name Price
        ]
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
                
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 2:  # Name and price
                        name, price = match.groups()
                    else:  # Number, name, and price
                        _, name, price = match.groups()
                    
                    # Clean up the name
                    name = re.sub(r'^[\d\.\-\s]+', '', name).strip()  # Remove leading numbers
                    name = re.sub(r'[\d\.\-\s]+$', '', name).strip()  # Remove trailing numbers
                    
                    if name and len(name) > 2:
                        dishes.append(
                            DishInfo(
                                name=name, 
                                price=self._normalize_price(price)
                            )
                        )
                    break  # Found a match, move to next line
        
        if not dishes:
            logger.warning("No dishes found from regex fallback")
            
        return dishes

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

