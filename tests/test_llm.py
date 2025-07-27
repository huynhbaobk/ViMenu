#!/usr/bin/env python3
"""
Test script to call LLM OCR API using environment variables
This script tests the Vietnamese menu OCR functionality
"""

import asyncio
import base64
import os
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OCRTester:
    def __init__(self):
        self.api_url = os.getenv("OCR_API_URL")
        self.model_id = os.getenv("MODEL_ID", "5CD-AI/Vintern-1B-v3_5")
        self.headers = {
            "Content-Type": "application/json",
        }
        
        # # Add HuggingFace token if available
        # hf_token = os.getenv("HF_API_TOKEN")
        # if hf_token and hf_token != "mock":
        #     self.headers["Authorization"] = f"Bearer {hf_token}"
        
        print(f"🚀 OCR API URL: {self.api_url}")
        print(f"🤖 Model ID: {self.model_id}")
        print(f"🔑 Headers: {self.headers}")

    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image file to base64 string"""
        try:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                base64_encoded = base64.b64encode(image_data).decode('utf-8')
                return f"data:image/jpeg;base64,{base64_encoded}"
        except Exception as e:
            print(f"❌ Error encoding image: {e}")
            return None

    def create_menu_extraction_prompt(self) -> str:
        """Create prompt for Vietnamese menu extraction"""
        return """Bạn là một chuyên gia phân tích thực đơn tiếng Việt. Hãy phân tích hình ảnh thực đơn và trích xuất thông tin các món ăn.

Với mỗi món ăn, hãy cung cấp thông tin sau:
- Tên món (tiếng Việt)
- Giá (nếu có, định dạng: số + "đ" hoặc "VND")
- Mô tả ngắn (nếu có)

Định dạng kết quả:
[TÊN MÓN] - [GIÁ] - [MÔ TẢ]

Ví dụ:
Phở Bò Tái - 50,000đ - Phở bò với thịt tái
Cơm Gà Xối Mỡ - 45,000đ - Cơm gà với nước mắm gừng

Chỉ trích xuất những gì bạn thấy rõ ràng trong hình."""

    def create_payload(self, image_base64: str) -> dict:
        """Create API request payload"""
        prompt = self.create_menu_extraction_prompt()
        
        return {
            "model": self.model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_base64}},
                    ]
                }
            ],
            "max_tokens": 800,
            "temperature": 0.3,
            "top_p": 0.9
        }

    async def test_ocr_api(self, image_path: str = None, image_url: str = None):
        """Test the OCR API with an image"""
        if not self.api_url:
            print("❌ OCR_API_URL not found in environment variables")
            return
        
        try:
            # Prepare image
            if image_path:
                print(f"📸 Encoding image: {image_path}")
                image_data = self.encode_image_to_base64(image_path)
                if not image_data:
                    return
            elif image_url:
                print(f"🌐 Using image URL: {image_url}")
                image_data = image_url
            else:
                print("❌ No image provided")
                return

            # Create payload
            payload = self.create_payload(image_data)
            print(f"📤 Sending request to: {self.api_url}/chat/completions")
            print(f"📝 Payload: {payload}")
            
            # Make API request
            timeout = httpx.Timeout(30.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    json=payload,
                    headers=self.headers
                )
                
                print(f"📊 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ API call successful!")
                    print(f"📝 Response keys: {list(result.keys())}")
                    
                    # Extract the content
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        print("\n🍜 Extracted Menu Items:")
                        print("=" * 50)
                        print(content)
                        print("=" * 50)
                    else:
                        print("❌ No choices found in response")
                        print(f"Full response: {result}")
                else:
                    print(f"❌ API call failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    
        except Exception as e:
            print(f"❌ Error during API call: {e}")
            import traceback
            traceback.print_exc()

    async def test_health_check(self):
        """Test the health check endpoint"""
        if not self.api_url:
            print("❌ OCR_API_URL not found")
            return
            
        try:
            timeout = httpx.Timeout(10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(f"{self.api_url}/health")
                print(f"🏥 Health Check Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"✅ Health Check Response: {response.json()}")
                else:
                    print(f"❌ Health Check Failed: {response.text}")
        except Exception as e:
            print(f"❌ Health check error: {e}")

async def main():
    """Main test function"""
    print("🧪 Vietnamese Menu OCR API Tester")
    print("=" * 50)
    
    tester = OCRTester()
    
    # Test health check first
    print("\n🏥 Testing Health Check...")
    await tester.test_health_check()
    
    # Test with sample image URL (if provided)
    sample_image_url = "https://scontent.fsgn5-11.fna.fbcdn.net/v/t1.6435-9/184742865_4254977971201353_542198034631261121_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=127cfc&_nc_ohc=HJpoyFkjefcQ7kNvwELrh69&_nc_oc=Admd_3w5m4WL3pXjA8DNWSUTh_9p_4p4E8cPpEnn9TLYikEA9t4w2FmJYVWnhkIHHaY&_nc_zt=23&_nc_ht=scontent.fsgn5-11.fna&_nc_gid=QCz0SXPEad9WlDGgvAXSKA&oh=00_AfT0CLLovhbLHdw6D340aoWJqooqbgfpvIR0D8yPS_CSFA&oe=68AD9A37"  # Replace with actual URL
    
    print(f"\n📸 Testing OCR with sample image URL...")
    await tester.test_ocr_api(image_url=sample_image_url)
    
    # # Test with local image file (if exists)
    # local_image_path = "sample_menu.jpg"  # Replace with actual path
    # if os.path.exists(local_image_path):
    #     print(f"\n📁 Testing OCR with local image: {local_image_path}")
    #     await tester.test_ocr_api(image_path=local_image_path)
    # else:
    #     print(f"\n📁 Local image not found: {local_image_path}")
    #     print("💡 To test with a local image, place a Vietnamese menu image as 'sample_menu.jpg'")

if __name__ == "__main__":
    asyncio.run(main())
