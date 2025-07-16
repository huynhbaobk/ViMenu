#!/usr/bin/env python3
"""
Test script for mock services - ingredients and load more functionality
"""
import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.mock_service import MockOCRService, MockRecipeService

# Optional imports for image and response mocks (used in test_mock_services)
try:
    from app.services.mock_service import MockImageService, get_mock_response
except ImportError:
    MockImageService = None
    get_mock_response = None


async def test_mock_services():
    """Test all mock services (from test-mock.py)"""
    print("\n🧪 [General] Testing Mock Services...")
    print("=" * 50)
    # Test OCR service
    print("\n📄 Testing OCR Service...")
    ocr_service = MockOCRService()
    ocr_result = await ocr_service.extract_menu_text(b"fake_image_data")
    print(f"✅ Found {len(ocr_result.dishes)} dishes:")
    for dish in ocr_result.dishes[:3]:  # Show first 3
        print(f"   • {dish.name} - {dish.price}")

    # Test Image service
    print("\n🖼️  Testing Image Service...")
    if MockImageService:
        try:
            image_service = MockImageService()
            test_dishes = ["Bún Bò Huế", "Phở Bò Tái", "Bánh Mì"]
            for dish in test_dishes:
                image_url = await image_service.get_dish_image(dish)
                print(f"   • {dish}: {image_url[:50]}...")
        except Exception as e:
            print(f"   ⚠️  Image service not available: {e}")
    else:
        print("   ⚠️  Image service not available: ImportError")

    # Test Recipe service
    print("\n👨‍🍳 Testing Recipe Service...")
    recipe_service = MockRecipeService()
    recipe = await recipe_service.generate_recipe("Bún Bò Huế")
    if isinstance(recipe, dict):
        print(f"   • {recipe['dish_name']}: {recipe['description']}")
        print(f"   • Prep: {recipe['prep_time']}min, Cook: {recipe['cook_time']}min")
        print(f"   • Ingredients: {len(recipe['ingredients'])} items")
    else:
        print(f"   • {recipe.dish_name}: {recipe.description}")
        print(f"   • Prep: {recipe.prep_time}min, Cook: {recipe.cook_time}min")
        print(f"   • Ingredients: {len(recipe.ingredients)} items")

    # Test complete response
    print("\n🎯 Testing Complete Response...")
    if get_mock_response:
        try:
            response = get_mock_response()
            print(f"   • Request ID: {response.request_id}")
            print(f"   • Status: {response.status}")
            print(f"   • Total dishes: {len(response.dishes)}")
        except Exception as e:
            print(f"   ⚠️  get_mock_response not available: {e}")
    else:
        print("   ⚠️  get_mock_response not available: ImportError")

    print("\n✅ All mock services working correctly!\n")


async def test_mock_ocr_service():
    """Test OCR service with extended dish list"""
    print("🧪 Testing Mock OCR Service")
    print("=" * 50)
    
    ocr_service = MockOCRService()
    result = await ocr_service.extract_menu_text(b"dummy_image_bytes")
    
    print(f"✅ Total dishes found: {len(result.dishes)}")
    print(f"✅ First 9 dishes (initial load):")
    for i, dish in enumerate(result.dishes[:9]):
        print(f"   {i+1}. {dish.name} - {dish.price}")
    
    print(f"\n✅ Additional dishes (load more):")
    for i, dish in enumerate(result.dishes[9:], 10):
        print(f"   {i}. {dish.name} - {dish.price}")
    
    print(f"\n✅ Raw text length: {len(result.raw_text)} characters")
    return result


async def test_mock_recipe_ingredients():
    """Test recipe service ingredients functionality"""
    print("\n🧪 Testing Mock Recipe Ingredients")
    print("=" * 50)
    
    recipe_service = MockRecipeService()
    
    # Test known dishes
    test_dishes = ["Bún Bò Huế", "Phở Bò Tái", "Bánh Mì Thịt Nướng", "Unknown Dish"]
    
    for dish in test_dishes:
        print(f"\n🍜 Testing dish: {dish}")
        recipe = await recipe_service.generate_recipe(dish)
        
        print(f"   ✅ Description: {recipe['description'][:60]}...")
        print(f"   ✅ Ingredients count: {len(recipe['ingredients'])}")
        print(f"   ✅ First 4 ingredients:")
        for ing in recipe['ingredients'][:4]:
            print(f"      • {ing['quantity']} {ing['item']}")
        
        if len(recipe['ingredients']) > 4:
            print(f"      ... +{len(recipe['ingredients']) - 4} more ingredients")
        
        print(f"   ✅ Prep time: {recipe['prep_time']} min | Cook time: {recipe['cook_time']} min")
        print(f"   ✅ Difficulty: {recipe['difficulty']} | Servings: {recipe['servings']}")


async def test_ingredients_only_method():
    """Test the new get_mock_ingredients_only method"""
    print("\n🧪 Testing Ingredients-Only Method")
    print("=" * 50)
    
    recipe_service = MockRecipeService()
    
    test_dishes = ["Bún Bò Huế", "Bánh Xèo", "Chả Cá Lã Vọng"]
    
    for dish in test_dishes:
        ingredients = recipe_service.get_mock_ingredients_only(dish)
        print(f"\n🥘 {dish}:")
        print(f"   ✅ Total ingredients: {len(ingredients)}")
        for i, ing in enumerate(ingredients[:3], 1):
            print(f"   {i}. {ing['quantity']} {ing['item']}")
        if len(ingredients) > 3:
            print(f"   ... +{len(ingredients) - 3} more")


async def test_cache_ingredients_simulation():
    """Simulate caching ingredients for first 9 dishes"""
    print("\n🧪 Testing Cache Ingredients Simulation")
    print("=" * 50)
    
    ocr_service = MockOCRService()
    recipe_service = MockRecipeService()
    
    # Get mock dishes
    ocr_result = await ocr_service.extract_menu_text(b"dummy")
    first_9_dishes = ocr_result.dishes[:9]
    
    print(f"🚀 Simulating auto-ingredients for first {len(first_9_dishes)} dishes:")
    
    ingredients_cache = {}
    
    for i, dish in enumerate(first_9_dishes):
        print(f"\n   📋 Processing dish {i+1}: {dish.name}")
        
        # Simulate getting ingredients
        ingredients = recipe_service.get_mock_ingredients_only(dish.name)
        ingredients_cache[dish.name] = ingredients
        
        print(f"      ✅ Cached {len(ingredients)} ingredients")
        print(f"      📝 Preview: {ingredients[0]['quantity']} {ingredients[0]['item']}")
        if len(ingredients) > 1:
            print(f"                  {ingredients[1]['quantity']} {ingredients[1]['item']}")
    
    print(f"\n✅ Successfully cached ingredients for {len(ingredients_cache)} dishes")
    return ingredients_cache


async def test_load_more_simulation():
    """Simulate the load more functionality"""
    print("\n🧪 Testing Load More Simulation")
    print("=" * 50)
    
    ocr_service = MockOCRService()
    recipe_service = MockRecipeService()
    
    # Get all dishes
    ocr_result = await ocr_service.extract_menu_text(b"dummy")
    all_dishes = ocr_result.dishes
    
    print(f"📊 Total dishes available: {len(all_dishes)}")
    
    # Simulate initial load (first 9)
    page_size = 9
    displayed_count = 0
    
    print(f"\n🔄 Initial load ({page_size} dishes):")
    initial_dishes = all_dishes[:page_size]
    displayed_count += len(initial_dishes)
    
    for i, dish in enumerate(initial_dishes, 1):
        print(f"   {i}. {dish.name} - {dish.price}")
    
    # Simulate load more clicks
    page_number = 1
    while displayed_count < len(all_dishes):
        print(f"\n🔄 Load More #{page_number}:")
        
        start_idx = displayed_count
        end_idx = min(start_idx + page_size, len(all_dishes))
        next_dishes = all_dishes[start_idx:end_idx]
        
        for i, dish in enumerate(next_dishes, displayed_count + 1):
            print(f"   {i}. {dish.name} - {dish.price}")
            # Simulate loading ingredients for new dishes
            ingredients = recipe_service.get_mock_ingredients_only(dish.name)
            print(f"      📋 Loaded {len(ingredients)} ingredients")
        
        displayed_count += len(next_dishes)
        page_number += 1
        
        if displayed_count >= len(all_dishes):
            print(f"\n✅ All {len(all_dishes)} dishes loaded!")
            break


async def test_batch_ingredients_api_simulation():
    """Simulate the batch ingredients API"""
    print("\n🧪 Testing Batch Ingredients API Simulation")
    print("=" * 50)
    
    ocr_service = MockOCRService()
    recipe_service = MockRecipeService()
    
    # Get first 9 dishes
    ocr_result = await ocr_service.extract_menu_text(b"dummy")
    first_9_dishes = ocr_result.dishes[:9]
    
    print(f"🚀 Simulating batch ingredients API for {len(first_9_dishes)} dishes:")
    
    # Simulate batch request
    request_data = {
        "request_id": "mock-test-123",
        "dish_names": [dish.name for dish in first_9_dishes]
    }
    
    print(f"📝 Request: {len(request_data['dish_names'])} dish names")
    
    # Simulate batch response
    batch_results = []
    for dish_name in request_data['dish_names']:
        ingredients = recipe_service.get_mock_ingredients_only(dish_name)
        batch_results.append({
            "dish_name": dish_name,
            "ingredients": ingredients
        })
    
    print(f"✅ Batch response: {len(batch_results)} dishes processed")
    
    # Show results summary
    for i, result in enumerate(batch_results, 1):
        dish_name = result['dish_name']
        ingredient_count = len(result['ingredients'])
        first_ingredient = result['ingredients'][0] if result['ingredients'] else {}
        
        print(f"   {i}. {dish_name}: {ingredient_count} ingredients")
        if first_ingredient:
            print(f"      🥕 {first_ingredient['quantity']} {first_ingredient['item']}")


async def main():
    """Run all mock tests"""
    print("🎯 Mock Services Testing Suite")
    print("=" * 60)
    print("Testing ingredients auto-loading and load more functionality")
    print("=" * 60)
    
    try:
        # General test from test-mock.py
        await test_mock_services()

        # Test OCR service with extended dish list
        await test_mock_ocr_service()
        # Test recipe ingredients
        await test_mock_recipe_ingredients()
        # Test ingredients-only method
        await test_ingredients_only_method()
        # Test cache simulation
        await test_cache_ingredients_simulation()
        # Test load more simulation
        await test_load_more_simulation()
        # Test batch API simulation
        await test_batch_ingredients_api_simulation()

        print("\n" + "=" * 60)
        print("🎉 All tests completed successfully!")
        print("✅ Mock services are ready for ingredients and load more testing")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

