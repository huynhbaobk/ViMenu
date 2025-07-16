"""
Mock services for testing without external API calls
"""
import asyncio
from typing import List, Optional
from app.models.schemas import OCRResult, DishInfo, Recipe, RecipeStep


class MockOCRService:
    """Mock OCR service for testing menu extraction"""
    
    async def extract_menu_text(self, image_bytes: bytes) -> OCRResult:
        """Return mock menu data instead of calling API"""
        return self._get_mock_menu_data()

    def _get_mock_menu_data(self) -> OCRResult:
        # Comprehensive mock Vietnamese menu data with 15+ dishes for testing load more
        return OCRResult(
            dishes=[
                # First 9 dishes - will show initially
                DishInfo(name="Bún Bò Huế", price="35.000đ"),
                DishInfo(name="Phở Bò Tái", price="30.000đ"),
                DishInfo(name="Bánh Mì Thịt Nướng", price="15.000đ"),
                DishInfo(name="Cà Phê Sữa Đá", price="12.000đ"),
                DishInfo(name="Bánh Xèo", price="25.000đ"),
                DishInfo(name="Gỏi Cuốn Tôm Thịt", price="20.000đ"),
                DishInfo(name="Cơm Tấm Sườn Bì", price="28.000đ"),
                DishInfo(name="Bún Thịt Nướng", price="22.000đ"),
                DishInfo(name="Hủ Tiếu Nam Vang", price="32.000đ"),
                
                # Additional dishes - will load with "Xem thêm" 
                DishInfo(name="Bánh Cuốn Nóng", price="18.000đ"),
                DishInfo(name="Chả Cá Lã Vọng", price="45.000đ"),
                DishInfo(name="Bún Riêu Cua", price="35.000đ"),
                DishInfo(name="Cao Lầu Hội An", price="28.000đ"),
                DishInfo(name="Mì Quảng", price="32.000đ"),
                DishInfo(name="Bánh Canh Cua", price="30.000đ"),
                DishInfo(name="Chè Ba Màu", price="15.000đ"),
                DishInfo(name="Bánh Tráng Nướng", price="10.000đ"),
                DishInfo(name="Nem Nướng Nha Trang", price="25.000đ")
            ],
            raw_text="""Bún Bò Huế 35.000đ
Phở Bò Tái 30.000đ
Bánh Mì Thịt Nướng 15.000đ
Cà Phê Sữa Đá 12.000đ
Bánh Xèo 25.000đ
Gỏi Cuốn Tôm Thịt 20.000đ
Cơm Tấm Sườn Bì 28.000đ
Bún Thịt Nướng 22.000đ
Hủ Tiếu Nam Vang 32.000đ
Bánh Cuốn Nóng 18.000đ
Chả Cá Lã Vọng 45.000đ
Bún Riêu Cua 35.000đ
Cao Lầu Hội An 28.000đ
Mì Quảng 32.000đ
Bánh Canh Cua 30.000đ
Chè Ba Màu 15.000đ
Bánh Tráng Nướng 10.000đ
Nem Nướng Nha Trang 25.000đ"""
        )


class MockImageService:
    """Mock image service for testing without Google Images"""
    
    async def get_dish_image(self, dish_name: str) -> str:
        """Return mock image URLs for Vietnamese dishes"""
        return self._get_mock_image(dish_name)

    def _get_mock_image(self, dish_name: str) -> str:
        """Mock image URLs for common Vietnamese dishes"""
        mock_images = {
            "bún bò huế": "https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&q=80",
            "phở bò tái": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=400&q=80",
            "bánh mì thịt nướng": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&q=80",
            "cà phê sữa đá": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400&q=80",
            "bánh xèo": "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80",
            "gỏi cuốn tôm thịt": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400&q=80",
            "cơm tấm sườn bì": "https://images.unsplash.com/photo-1576777187466-a0bcfb88ec97?w=400&q=80",
            "bún thịt nướng": "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80",
            "hủ tiếu nam vang": "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80",
            "bánh cuốn nóng": "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80",
            "chả cá lã vọng": "https://images.unsplash.com/photo-1565895405229-71906ad8602b?w=400&q=80",
            "bún riêu cua": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=400&q=80",
            "cao lầu hội an": "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80",
            "mì quảng": "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80",
            "bánh canh cua": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=400&q=80",
            "chè ba màu": "https://images.unsplash.com/photo-1562059390-a761a084768e?w=400&q=80",
            "bánh tráng nướng": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&q=80",
            "nem nướng nha trang": "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80"
        }
        
        dish_name_lower = dish_name.lower().strip()
        
        for key, url in mock_images.items():
            if key in dish_name_lower:
                return url
        
        return "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80"


class MockRecipeService:
    """Mock recipe service for testing recipe generation"""
    
    async def generate_recipe(self, dish_name: str):
        """Return mock recipes for Vietnamese dishes"""
        return self._get_mock_recipe(dish_name)

    def _get_mock_recipe(self, dish_name: str):
        """Comprehensive mock recipes with detailed ingredients for Vietnamese dishes"""
        recipes = {
            "Bún Bò Huế": {
                "dish_name": "Bún Bò Huế",
                "description": "Món bún đặc sản của cố đô Huế với nước dùng đậm đà, cay nồng đặc trưng",
                "ingredients": [
                    {"item": "Bún tươi", "quantity": "200g"},
                    {"item": "Giò heo hầm", "quantity": "100g"},
                    {"item": "Thịt bò tái", "quantity": "150g"},
                    {"item": "Sả cây", "quantity": "3 cây"},
                    {"item": "Ớt hiểm", "quantity": "2 quả"},
                    {"item": "Hành lá", "quantity": "3 cây"},
                    {"item": "Rau thơm", "quantity": "100g"},
                    {"item": "Mắm ruốc", "quantity": "1 thìa"}
                ],
                "instructions": [
                    {"step_number": 1, "instruction": "Ninh xương bò và giò heo trong 2 tiếng để lấy nước dùng"},
                    {"step_number": 2, "instruction": "Phi thơm sả băm với dầu ăn và cho vào nồi nước dùng"},
                    {"step_number": 3, "instruction": "Thái thịt bò thật mỏng, ướp với gia vị"},
                    {"step_number": 4, "instruction": "Chần bún nóng trong nước sôi, xếp vào tô"},
                    {"step_number": 5, "instruction": "Cho thịt bò và giò heo lên bún, chan nước dùng nóng"},
                    {"step_number": 6, "instruction": "Trang trí rau thơm, hành lá và ớt tươi"}
                ],
                "prep_time": 30,
                "cook_time": 120,
                "difficulty": "Khó",
                "servings": 2
            },
            "Phở Bò Tái": {
                "dish_name": "Phở Bò Tái",
                "description": "Món ăn quốc hồn quốc túy của Việt Nam với nước dùng trong, ngọt thanh tự nhiên",
                "ingredients": [
                    {"item": "Bánh phở tươi", "quantity": "200g"},
                    {"item": "Thịt bò tái", "quantity": "150g"},
                    {"item": "Xương bò", "quantity": "500g"},
                    {"item": "Hành tây", "quantity": "1 củ"},
                    {"item": "Gừng tươi", "quantity": "50g"},
                    {"item": "Hành lá", "quantity": "3 cây"},
                    {"item": "Ngò gai", "quantity": "50g"},
                    {"item": "Hành tím", "quantity": "3 củ"}
                ],
                "instructions": [
                    {"step_number": 1, "instruction": "Nướng hành tây và gừng trên lửa cho thơm, cạo vỏ"},
                    {"step_number": 2, "instruction": "Ninh xương bò với hành, gừng trong 3-4 tiếng"},
                    {"step_number": 3, "instruction": "Vớt bọt thường xuyên để nước dùng trong"},
                    {"step_number": 4, "instruction": "Thái thịt bò thật mỏng theo thớ"},
                    {"step_number": 5, "instruction": "Chần bánh phở nóng, xếp vào bát"},
                    {"step_number": 6, "instruction": "Cho thịt bò lên phở, chan nước dùng nóng"}
                ],
                "prep_time": 20,
                "cook_time": 240,
                "difficulty": "Khó",
                "servings": 2
            },
            "Bánh Mì Thịt Nướng": {
                "dish_name": "Bánh Mì Thịt Nướng",
                "description": "Bánh mì Sài Gòn với thịt nướng thơm lừng, rau củ tươi mát",
                "ingredients": [
                    {"item": "Bánh mì", "quantity": "1 ổ"},
                    {"item": "Thịt heo nướng", "quantity": "150g"},
                    {"item": "Pate gan", "quantity": "2 thìa"},
                    {"item": "Dưa leo", "quantity": "50g"},
                    {"item": "Cà rót", "quantity": "50g"},
                    {"item": "Ngò rí", "quantity": "20g"},
                    {"item": "Tương ớt", "quantity": "1 thìa"}
                ],
                "instructions": [
                    {"step_number": 1, "instruction": "Nướng bánh mì giòn rồi rạch dọc"},
                    {"step_number": 2, "instruction": "Phết pate đều lên mặt bánh"},
                    {"step_number": 3, "instruction": "Cho thịt nướng vào bánh"},
                    {"step_number": 4, "instruction": "Thêm rau củ tươi và gia vị"}
                ],
                "prep_time": 10,
                "cook_time": 15,
                "difficulty": "Dễ",
                "servings": 1
            },
            "Bánh Xèo": {
                "dish_name": "Bánh Xèo",
                "description": "Bánh xèo miền Tây với nhân tôm thịt, giá đỗ giòn ngon",
                "ingredients": [
                    {"item": "Bột bánh xèo", "quantity": "200g"},
                    {"item": "Tôm tươi", "quantity": "200g"},
                    {"item": "Thịt ba rọi", "quantity": "150g"},
                    {"item": "Giá đỗ", "quantity": "100g"},
                    {"item": "Hành lá", "quantity": "3 cây"},
                    {"item": "Nước cốt dừa", "quantity": "200ml"},
                    {"item": "Tinh nghệ", "quantity": "1/2 thìa"}
                ],
                "instructions": [
                    {"step_number": 1, "instruction": "Pha bột bánh xèo với nước cốt dừa và nghệ"},
                    {"step_number": 2, "instruction": "Xào thịt và tôm sơ qua"},
                    {"step_number": 3, "instruction": "Đổ bột vào chảo nóng, cho nhân vào"},
                    {"step_number": 4, "instruction": "Gấp đôi khi bánh chín vàng"}
                ],
                "prep_time": 20,
                "cook_time": 30,
                "difficulty": "Trung bình",
                "servings": 4
            },
            "Chả Cá Lã Vọng": {
                "dish_name": "Chả Cá Lã Vọng",
                "description": "Món đặc sản Hà Nội với cá lăng nướng thơm, ăn cùng bún và rau thơm",
                "ingredients": [
                    {"item": "Cá lăng", "quantity": "500g"},
                    {"item": "Bún tươi", "quantity": "200g"},
                    {"item": "Thì là tươi", "quantity": "100g"},
                    {"item": "Hành lá", "quantity": "50g"},
                    {"item": "Mắm tôm", "quantity": "2 thìa"},
                    {"item": "Tinh nghệ", "quantity": "1 thìa"},
                    {"item": "Mắm nêm", "quantity": "2 thìa"}
                ],
                "instructions": [
                    {"step_number": 1, "instruction": "Thái cá thành miếng vừa ăn, ướp nghệ"},
                    {"step_number": 2, "instruction": "Nướng cá trên bếp than cho thơm"},
                    {"step_number": 3, "instruction": "Xào cá với thì là và hành lá"},
                    {"step_number": 4, "instruction": "Ăn kèm bún tươi và nước mắm pha"}
                ],
                "prep_time": 25,
                "cook_time": 20,
                "difficulty": "Trung bình",
                "servings": 3
            }
        }
        
        # Enhanced default recipe with more ingredients for unknown dishes
        default_recipe = {
            "dish_name": dish_name,
            "description": f"Món {dish_name} đặc trưng của ẩm thực Việt Nam với hương vị đậm đà, thơm ngon",
            "ingredients": [
                {"item": "Nguyên liệu chính", "quantity": "200g"},
                {"item": "Gia vị truyền thống", "quantity": "tùy khẩu vị"},
                {"item": "Rau sống tươi", "quantity": "100g"},
                {"item": "Tỏi băm", "quantity": "2 củ"},
                {"item": "Hành tím", "quantity": "3 củ"},
                {"item": "Ớt sừng", "quantity": "2 quả"},
                {"item": "Nước mắm", "quantity": "2 thìa"},
                {"item": "Đường cát", "quantity": "1 thìa"}
            ],
            "instructions": [
                {"step_number": 1, "instruction": "Chuẩn bị và sơ chế tất cả nguyên liệu tươi"},
                {"step_number": 2, "instruction": "Ướp gia vị theo khẩu vị của từng vùng miền"},
                {"step_number": 3, "instruction": "Chế biến theo cách truyền thống của người Việt"},
                {"step_number": 4, "instruction": "Trình bày đẹp mắt và thưởng thức nóng"}
            ],
            "prep_time": 15,
            "cook_time": 30,
            "difficulty": "Trung bình",
            "servings": 2
        }
        
        return recipes.get(dish_name, default_recipe)

    def get_mock_ingredients_only(self, dish_name: str) -> List[dict]:
        """Get just the ingredients list for faster loading"""
        recipe = self._get_mock_recipe(dish_name)
        return recipe["ingredients"]


def get_mock_response():
    """Get complete mock response for testing with more dishes"""
    from app.models.schemas import MenuAnalysisResponse, DishDetail
    
    mock_dishes = [
        DishDetail(
            name="Bún Bò Huế",
            price="35.000đ",
            image_url="https://images.unsplash.com/photo-1574484284002-952d92456975?w=400&q=80"
        ),
        DishDetail(
            name="Phở Bò Tái",
            price="30.000đ",
            image_url="https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=400&q=80"
        ),
        DishDetail(
            name="Bánh Mì Thịt Nướng",
            price="15.000đ",
            image_url="https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&q=80"
        ),
        DishDetail(
            name="Cà Phê Sữa Đá",
            price="12.000đ",
            image_url="https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400&q=80"
        ),
        DishDetail(
            name="Bánh Xèo",
            price="25.000đ",
            image_url="https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80"
        ),
        DishDetail(
            name="Gỏi Cuốn Tôm Thịt",
            price="20.000đ",
            image_url="https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400&q=80"
        ),
        DishDetail(
            name="Cơm Tấm Sườn Bì",
            price="28.000đ",
            image_url="https://images.unsplash.com/photo-1576777187466-a0bcfb88ec97?w=400&q=80"
        ),
        DishDetail(
            name="Bún Thịt Nướng",
            price="22.000đ",
            image_url="https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80"
        ),
        DishDetail(
            name="Hủ Tiếu Nam Vang",
            price="32.000đ",
            image_url="https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80"
        ),
        # Additional dishes for "Xem thêm" testing
        DishDetail(
            name="Bánh Cuốn Nóng",
            price="18.000đ",
            image_url="https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80"
        ),
        DishDetail(
            name="Chả Cá Lã Vọng",
            price="45.000đ",
            image_url="https://images.unsplash.com/photo-1565895405229-71906ad8602b?w=400&q=80"
        ),
        DishDetail(
            name="Bún Riêu Cua",
            price="35.000đ",
            image_url="https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=400&q=80"
        ),
        DishDetail(
            name="Cao Lầu Hội An",
            price="28.000đ",
            image_url="https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80"
        ),
        DishDetail(
            name="Mì Quảng",
            price="32.000đ",
            image_url="https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&q=80"
        ),
        DishDetail(
            name="Bánh Canh Cua",
            price="30.000đ",
            image_url="https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=400&q=80"
        )
    ]
    
    return MenuAnalysisResponse(
        request_id="mock-request-123",
        dishes=mock_dishes,
        status="completed",
        message="Phân tích hoàn thành - 15 món ăn được tìm thấy"
    )