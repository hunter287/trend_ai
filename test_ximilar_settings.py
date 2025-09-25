#!/usr/bin/env python3
"""
Тестирование Ximilar API с разными настройками
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_ximilar_with_settings():
    """Тестирование Ximilar API с разными настройками"""
    
    api_key = os.getenv("XIMILAR_API_KEY")
    if not api_key:
        print("❌ XIMILAR_API_KEY не найден в .env")
        return
    
    # Тестовое изображение с одеждой
    test_image_url = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=500"
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    print("🧪 ТЕСТИРОВАНИЕ XIMILAR API С РАЗНЫМИ НАСТРОЙКАМИ")
    print("=" * 60)
    
    # Тест 1: Базовые настройки
    print("\n1️⃣ Базовые настройки:")
    payload1 = {
        "records": [
            {
                "_id": "1",
                "_url": test_image_url
            }
        ]
    }
    
    try:
        response = requests.post(
            "https://api.ximilar.com/tagging/fashion/v2/detect_tags_all",
            headers=headers,
            json=payload1,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Статус: {response.status_code}")
            print(f"   📊 Записей: {len(result.get('records', []))}")
            
            if result.get("records"):
                record = result["records"][0]
                tags = record.get("_tags", [])
                print(f"   🏷️ Тегов: {len(tags)}")
                
                for tag in tags[:5]:  # Показываем первые 5 тегов
                    if isinstance(tag, dict):
                        print(f"     - {tag.get('name', 'N/A')} (confidence: {tag.get('confidence', 0):.3f})")
        else:
            print(f"   ❌ Ошибка: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
    
    # Тест 2: С дополнительными параметрами
    print("\n2️⃣ С дополнительными параметрами:")
    payload2 = {
        "records": [
            {
                "_id": "1",
                "_url": test_image_url
            }
        ],
        "options": {
            "return_bbox": True,
            "return_confidence": True,
            "min_confidence": 0.1  # Низкий порог confidence
        }
    }
    
    try:
        response = requests.post(
            "https://api.ximilar.com/tagging/fashion/v2/detect_tags_all",
            headers=headers,
            json=payload2,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Статус: {response.status_code}")
            print(f"   📊 Записей: {len(result.get('records', []))}")
            
            if result.get("records"):
                record = result["records"][0]
                tags = record.get("_tags", [])
                print(f"   🏷️ Тегов: {len(tags)}")
                
                for tag in tags[:5]:  # Показываем первые 5 тегов
                    if isinstance(tag, dict):
                        print(f"     - {tag.get('name', 'N/A')} (confidence: {tag.get('confidence', 0):.3f})")
        else:
            print(f"   ❌ Ошибка: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
    
    # Тест 3: С другим изображением
    print("\n3️⃣ С другим изображением (модная одежда):")
    fashion_image_url = "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=500"
    
    payload3 = {
        "records": [
            {
                "_id": "1",
                "_url": fashion_image_url
            }
        ]
    }
    
    try:
        response = requests.post(
            "https://api.ximilar.com/tagging/fashion/v2/detect_tags_all",
            headers=headers,
            json=payload3,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Статус: {response.status_code}")
            print(f"   📊 Записей: {len(result.get('records', []))}")
            
            if result.get("records"):
                record = result["records"][0]
                tags = record.get("_tags", [])
                print(f"   🏷️ Тегов: {len(tags)}")
                
                for tag in tags[:5]:  # Показываем первые 5 тегов
                    if isinstance(tag, dict):
                        print(f"     - {tag.get('name', 'N/A')} (confidence: {tag.get('confidence', 0):.3f})")
        else:
            print(f"   ❌ Ошибка: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ Исключение: {e}")

if __name__ == "__main__":
    test_ximilar_with_settings()







