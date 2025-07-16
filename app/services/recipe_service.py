import httpx
import asyncio
from typing import List, Dict
from app.models.schemas import Recipe, RecipeStep
from app.core.config import settings
from app.core.logging import get_logger
import re

logger = get_logger(__name__)


class RecipeService:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/Viet-Mistral/Vintern-1B"
        self.headers = {
            "Authorization": f"Bearer {settings.HF_API_TOKEN}",
            "Content-Type": "application/json"
        }

    async def generate_recipe(self, dish_name: str) -> Recipe:
        """Generate a recipe for a Vietnamese dish using AI"""
        
        try:
            prompt = self._create_recipe_prompt(dish_name)
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 1000,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "return_full_text": False
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
                
                recipe_text = result[0]["generated_text"] if isinstance(result, list) else result.get("generated_text", "")
                
                # Parse the recipe text
                recipe = self._parse_recipe_text(dish_name, recipe_text)
                
                logger.info(f"Generated recipe for {dish_name}")
                return recipe
                
        except Exception as e:
            logger.error(f"Error generating recipe for {dish_name}: {str(e)}")
            raise Exception(f"Failed to generate recipe for {dish_name}: {str(e)}")

    def _create_recipe_prompt(self, dish_name: str) -> str:
        """Create prompt for Vietnamese recipe generation"""
        return f"""
        Là một đầu bếp Việt Nam chuyên nghiệp, hãy cung cấp công thức chi tiết cho món {dish_name}.
        
        Định dạng trả lờI:
        
        MÔ TẢ: [Mô tả ngắn về món ăn, nguồn gốc, đặc điểm]
        
        NGUYÊN LIỆU:
        - [Tên nguyên liệu]: [Số lượng]
        - [Tên nguyên liệu]: [Số lượng]
        
        CÁCH LÀM:
        1. [Hướng dẫn chi tiết bước 1]
        2. [Hướng dẫn chi tiết bước 2]
        3. [Hướng dẫn chi tiết bước 3]
        
        THỜI GIAN:
        - Chuẩn bị: [X] phút
        - Nấu: [Y] phút
        - Độ khó: [Dễ/Trung bình/Khó]
        - Khẩu phần: [Z] ngườI
        
        LƯU Ý: [Mẹo và lưu ý quan trọng]
        
        Hãy đảm bảo công thức thật chi tiết và chính xác cho món {dish_name}.
        """

    def _parse_recipe_text(self, dish_name: str, text: str) -> Recipe:
        """Parse recipe text into structured format"""
        
        # Default values
        description = f"Món {dish_name} truyền thống của Việt Nam"
        ingredients = []
        instructions = []
        prep_time = 15
        cook_time = 30
        difficulty = "Trung bình"
        servings = 2
        
        try:
            lines = text.strip().split('\n')
            
            # Parse description
            for line in lines:
                if line.startswith('MÔ TẢ:'):
                    description = line.replace('MÔ TẢ:', '').strip()
                    break
            
            # Parse ingredients
            in_ingredients = False
            for line in lines:
                line = line.strip()
                if line.startswith('NGUYÊN LIỆU:'):
                    in_ingredients = True
                    continue
                elif line.startswith('CÁCH LÀM:'):
                    in_ingredients = False
                    break
                
                if in_ingredients and line.startswith('-'):
                    ingredient_line = line[1:].strip()
                    if ':' in ingredient_line:
                        item, quantity = ingredient_line.split(':', 1)
                        ingredients.append({
                            "item": item.strip(),
                            "quantity": quantity.strip()
                        })
            
            # Parse instructions
            in_instructions = False
            step_num = 1
            for line in lines:
                line = line.strip()
                if line.startswith('CÁCH LÀM:'):
                    in_instructions = True
                    continue
                elif line.startswith('THỜI GIAN:'):
                    in_instructions = False
                    break
                
                if in_instructions and (line.startswith(str(step_num) + '.') or line.startswith('-')):
                    instruction = line[line.find('.') + 1:].strip() if '.' in line else line[1:].strip()
                    if instruction:
                        instructions.append(RecipeStep(
                            step_number=step_num,
                            instruction=instruction
                        ))
                        step_num += 1
            
            # Parse timing and difficulty
            for line in lines:
                line = line.strip()
                if 'Chuẩn bị:' in line:
                    prep_match = re.search(r'Chuẩn bị:\s*(\d+)\s*phút', line)
                    if prep_match:
                        prep_time = int(prep_match.group(1))
                
                if 'Nấu:' in line:
                    cook_match = re.search(r'Nấu:\s*(\d+)\s*phút', line)
                    if cook_match:
                        cook_time = int(cook_match.group(1))
                
                if 'Độ khó:' in line:
                    difficulty_match = re.search(r'Độ khó:\s*(\w+)', line)
                    if difficulty_match:
                        difficulty = difficulty_match.group(1)
                
                if 'Khẩu phần:' in line:
                    servings_match = re.search(r'Khẩu phần:\s*(\d+)\s*ngườI', line)
                    if servings_match:
                        servings = int(servings_match.group(1))
            
        except Exception as e:
            logger.error(f"Error parsing recipe text: {str(e)}")
            ingredients, instructions = [], []

        return Recipe(
            dish_name=dish_name,
            description=description,
            ingredients=ingredients,
            instructions=instructions,
            prep_time=prep_time,
            cook_time=cook_time,
            difficulty=difficulty,
            servings=servings
        )

