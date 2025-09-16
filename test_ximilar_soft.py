#!/usr/bin/env python3
"""
Тестирование Ximilar API с более мягкими настройками
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
load_dotenv('mongodb_config.env')

def test_ximilar_soft():
    """Тестирование Ximilar API с мягкими настройками"""
    
    api_key = os.getenv("XIMILAR_API_KEY")
    if not api_key:
        print("❌ XIMILAR_API_KEY не найден в .env")
        return
    
    # Тестовые изображения с разным контентом
    test_images = [
        {
            "name": "Модная одежда",
            "url": "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=500"
        },
        {
            "name": "Обувь",
            "url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500"
        },
        {
            "name": "Аксессуары",
            "url": "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=500"
        },
        {
            "name": "Сумка",
            "url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500"
        }
    ]
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    print("🧪 ТЕСТИРОВАНИЕ XIMILAR API С РАЗНЫМИ ТИПАМИ ИЗОБРАЖЕНИЙ")
    print("=" * 70)
    
    for i, img in enumerate(test_images, 1):
        print(f"\n{i}️⃣ {img['name']}:")
        print(f"   URL: {img['url']}")
        
        payload = {
            "records": [
                {
                    "_id": str(i),
                    "_url": img['url']
                }
            ],
            "options": {
                "return_bbox": True,
                "return_confidence": True,
                "min_confidence": 0.05,  # Очень низкий порог
                "return_categories": True
            }
        }
        
        try:
            response = requests.post(
                "https://api.ximilar.com/tagging/fashion/v2/detect_tags_all",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Статус: {response.status_code}")
                
                if result.get("records"):
                    record = result["records"][0]
                    tags = record.get("_tags", [])
                    print(f"   🏷️ Тегов: {len(tags)}")
                    
                    if tags:
                        for tag in tags[:3]:  # Показываем первые 3 тега
                            if isinstance(tag, dict):
                                print(f"     - {tag.get('name', 'N/A')} (confidence: {tag.get('confidence', 0):.3f})")
                    else:
                        print(f"     ❌ Теги не найдены")
                        
                    # Проверяем другие поля
                    if record.get("_categories"):
                        print(f"   📂 Категории: {record['_categories']}")
                    if record.get("_bbox"):
                        print(f"   📦 Bounding box: {record['_bbox']}")
            else:
                print(f"   ❌ Ошибка: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ Исключение: {e}")
    
    # Тест с реальным изображением из MongoDB
    print(f"\n ТЕСТ С РЕАЛЬНЫМ ИЗОБРАЖЕНИЕМ ИЗ MONGODB:")
    print("=" * 50)
    
    try:
        from pymongo import MongoClient
        client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:|#!x1K52H.0{8d3@localhost:27017/instagram_gallery'))
        db = client.instagram_gallery
        collection = db.images
        
        # Берем первое изображение
        img = collection.find_one()
        if img:
            image_url = img.get('full_image_url')
            if image_url:
                print(f"   📸 Тестируем: {image_url}")
                
                payload = {
                    "records": [
                        {
                            "_id": "real_test",
                            "_url": image_url
                        }
                    ],
                    "options": {
                        "return_bbox": True,
                        "return_confidence": True,
                        "min_confidence": 0.01,  # Минимальный порог
                        "return_categories": True
                    }
                }
                
                response = requests.post(
                    "https://api.ximilar.com/tagging/fashion/v2/detect_tags_all",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Статус: {response.status_code}")
                    
                    if result.get("records"):
                        record = result["records"][0]
                        tags = record.get("_tags", [])
                        print(f"   🏷️ Тегов: {len(tags)}")
                        
                        if tags:
                            for tag in tags:
                                if isinstance(tag, dict):
                                    print(f"     - {tag.get('name', 'N/A')} (confidence: {tag.get('confidence', 0):.3f})")
                        else:
                            print(f"     ❌ Теги не найдены")
                            
                        # Показываем все поля ответа
                        print(f"   📊 Все поля ответа:")
                        for key, value in record.items():
                            if key != "_tags":
                                print(f"     - {key}: {value}")
                else:
                    print(f"   ❌ Ошибка: {response.status_code} - {response.text}")
            else:
                print(f"   ❌ Нет URL в изображении")
        else:
            print(f"   ❌ Нет изображений в MongoDB")
            
        client.close()
        
    except Exception as e:
        print(f"   ❌ Ошибка MongoDB: {e}")

if __name__ == "__main__":
    test_ximilar_soft()
