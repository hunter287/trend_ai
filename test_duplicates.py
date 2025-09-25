#!/usr/bin/env python3
"""
Тестирование функциональности проверки дубликатов
"""

import os
from dotenv import load_dotenv
from instagram_parser import InstagramParser

# Загружаем переменные окружения
load_dotenv()
load_dotenv('mongodb_config.env')

def test_duplicate_detection():
    """Тестирование обнаружения дубликатов"""
    print("🧪 ТЕСТИРОВАНИЕ ОБНАРУЖЕНИЯ ДУБЛИКАТОВ")
    print("="*50)
    
    # Инициализация парсера
    apify_token = os.getenv("APIFY_API_TOKEN")
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
    
    if not apify_token:
        print("❌ APIFY_API_TOKEN не найден")
        return
    
    parser = InstagramParser(apify_token, mongodb_uri)
    
    # Подключаемся к MongoDB
    if not parser.connect_mongodb():
        print("❌ Ошибка подключения к MongoDB")
        return
    
    # Тестовые данные
    test_images = [
        {
            "image_url": "https://example.com/test1.jpg",
            "post_id": "test_post_1",
            "timestamp": "2025-01-01T00:00:00Z",
            "likes_count": 100,
            "comments_count": 10,
            "caption": "Test image 1",
            "image_type": "image"
        },
        {
            "image_url": "https://example.com/test2.jpg", 
            "post_id": "test_post_2",
            "timestamp": "2025-01-01T00:00:00Z",
            "likes_count": 200,
            "comments_count": 20,
            "caption": "Test image 2",
            "image_type": "image"
        }
    ]
    
    print("📊 Тестирование сохранения...")
    saved_count = parser.save_to_mongodb(test_images, "test_user")
    print(f"✅ Сохранено {saved_count} изображений")
    
    print("\n📊 Тестирование повторного сохранения (должны быть дубликаты)...")
    saved_count_2 = parser.save_to_mongodb(test_images, "test_user")
    print(f"✅ Сохранено {saved_count_2} изображений (должно быть 0)")
    
    print("\n📊 Тестирование с новыми изображениями...")
    new_images = [
        {
            "image_url": "https://example.com/test3.jpg",
            "post_id": "test_post_3", 
            "timestamp": "2025-01-01T00:00:00Z",
            "likes_count": 300,
            "comments_count": 30,
            "caption": "Test image 3",
            "image_type": "image"
        }
    ]
    saved_count_3 = parser.save_to_mongodb(new_images, "test_user")
    print(f"✅ Сохранено {saved_count_3} изображений (должно быть 1)")
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    test_duplicate_detection()

