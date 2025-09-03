#!/usr/bin/env python3
"""
Тест Ximilar API с реальным изображением
"""

import os
import requests
import pymongo
from dotenv import load_dotenv

load_dotenv()

def test_with_real_image():
    """Тестирование с реальным изображением из MongoDB"""
    api_key = os.getenv("XIMILAR_API_KEY")
    
    if not api_key:
        print("❌ Не найден XIMILAR_API_KEY")
        return False
    
    # Используем публичное изображение для теста
    image_url = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=500"
    print(f"🖼️ Тестируем с публичным изображением:")
    print(f"   URL: {image_url}")
    
    # Тестируем API
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "records": [
            {
                "_id": "test_real",
                "_url": image_url
            }
        ]
    }
    
    try:
        print("🚀 Отправляем запрос к Ximilar API...")
        response = requests.post(
            "https://api.ximilar.com/tagging/fashion/v2/detect_tags_all",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API работает!")
            
            if result.get("records") and len(result["records"]) > 0:
                record = result["records"][0]
                if record.get("_tags"):
                    print(f"🏷️ Найдено {len(record['_tags'])} тегов:")
                    for i, tag in enumerate(record["_tags"][:5], 1):
                        name = tag.get("name", "N/A")
                        confidence = tag.get("confidence", 0)
                        print(f"   {i}. {name} ({confidence:.2f})")
                else:
                    print("❌ Теги не найдены")
            else:
                print("❌ Нет данных в ответе")
            
            return True
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"📋 Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_with_real_image()
    if success:
        print("\n🎉 Тест с реальным изображением прошел успешно!")
    else:
        print("\n💥 Тест не прошел")
