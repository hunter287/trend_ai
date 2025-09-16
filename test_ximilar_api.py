#!/usr/bin/env python3
"""
Тест Ximilar Fashion API
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_ximilar_api():
    """Тестирование Ximilar Fashion API"""
    api_key = os.getenv("XIMILAR_API_KEY")
    
    if not api_key:
        print("❌ Не найден XIMILAR_API_KEY в переменных окружения")
        return False
    
    print("🔍 Тестируем Ximilar Fashion API...")
    
    # Тестовое изображение (можно заменить на любое)
    test_image_url = "https://example.com/test-image.jpg"
    
    payload = {
        "records": [
            {
                "_id": "test_1",
                "_url": test_image_url
            }
        ]
    }
    
    # Пробуем разные форматы авторизации
    headers_formats = [
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        {"Authorization": f"Token {api_key}", "Content-Type": "application/json"},
        {"X-API-Key": api_key, "Content-Type": "application/json"},
        {"Authorization": api_key, "Content-Type": "application/json"}
    ]
    
    for i, headers in enumerate(headers_formats, 1):
        print(f"🔄 Пробуем формат {i}: {list(headers.keys())}")
        
        try:
            response = requests.post(
                "https://api.ximilar.com/tagging/fashion/v2/detect_tags_all",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ API работает с этим форматом!")
                print(f"📋 Ответ: {result}")
                return True
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                print(f"📋 Ответ: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print()
    
    return False

if __name__ == "__main__":
    success = test_ximilar_api()
    if success:
        print("\n🎉 Тест прошел успешно!")
    else:
        print("\n💥 Тест не прошел")
