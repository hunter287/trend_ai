#!/usr/bin/env python3
"""
Тестирование галереи с фильтрами
"""

import os
from dotenv import load_dotenv
from instagram_parser import InstagramParser

# Загружаем переменные окружения
load_dotenv()
load_dotenv('mongodb_config.env')

def test_gallery_with_filters():
    """Тестирование создания галереи с фильтрами"""
    print("🧪 ТЕСТИРОВАНИЕ ГАЛЕРЕИ С ФИЛЬТРАМИ")
    print("="*50)
    
    # Инициализация парсера
    apify_token = os.getenv("APIFY_API_TOKEN")
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
    
    if not apify_token:
        print("❌ APIFY_API_TOKEN не найден")
        return
    
    parser = InstagramParser(apify_token, mongodb_uri)
    
    # Тестовые данные изображений
    test_images = [
        {
            "image_url": "https://example.com/test1.jpg",
            "post_id": "test_post_1",
            "timestamp": "2025-01-01T00:00:00Z",
            "likes_count": 100,
            "comments_count": 10,
            "caption": "Test image 1",
            "image_type": "image",
            "local_filename": "test1.jpg",
            "local_path": "instagram_images/test1.jpg",
            "file_size": 1024000,
            "downloaded_at": "2025-01-01T00:00:00Z"
        },
        {
            "image_url": "https://example.com/test2.jpg",
            "post_id": "test_post_2", 
            "timestamp": "2025-01-01T00:00:00Z",
            "likes_count": 200,
            "comments_count": 20,
            "caption": "Test image 2",
            "image_type": "image",
            "local_filename": "test2.jpg",
            "local_path": "instagram_images/test2.jpg",
            "file_size": 2048000,
            "downloaded_at": "2025-01-01T00:00:00Z"
        },
        {
            "image_url": "https://example.com/test3.jpg",
            "post_id": "test_post_3",
            "timestamp": "2025-01-01T00:00:00Z", 
            "likes_count": 300,
            "comments_count": 30,
            "caption": "Test image 3",
            "image_type": "image",
            "local_filename": "test3.jpg",
            "local_path": "instagram_images/test3.jpg",
            "file_size": 1536000,
            "downloaded_at": "2025-01-01T00:00:00Z"
        }
    ]
    
    print("🌐 Создание галереи с фильтрами...")
    html_content = parser.create_gallery_html(test_images, "test_user")
    
    if html_content:
        print("✅ Галерея с фильтрами создана успешно!")
        print(f"📄 Размер HTML: {len(html_content)} символов")
        print("🔗 Откройте файл gallery_test_user.html в браузере для просмотра")
    else:
        print("❌ Ошибка создания галереи")

if __name__ == "__main__":
    test_gallery_with_filters()

