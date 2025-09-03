#!/usr/bin/env python3
"""
Скрипт для анализа изображений в MongoDB
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
import requests
from PIL import Image
import io

load_dotenv()

def analyze_images():
    """Анализ изображений в MongoDB"""
    
    # Подключение к MongoDB
    mongodb_uri = "mongodb://localhost:27017/"
    client = MongoClient(mongodb_uri)
    db = client.instagram_gallery
    collection = db.images
    
    print("🔍 АНАЛИЗ ИЗОБРАЖЕНИЙ В MONGODB")
    print("=" * 50)
    
    # Получаем все изображения
    images = list(collection.find())
    print(f"📸 Всего изображений: {len(images)}")
    
    for i, img in enumerate(images[:5], 1):  # Анализируем первые 5
        print(f"\n🖼️ Изображение {i}:")
        print(f"   • ID: {img['_id']}")
        print(f"   • URL: {img.get('full_image_url', 'N/A')}")
        print(f"   • Локальный файл: {img.get('local_filename', 'N/A')}")
        print(f"   • Размер файла: {img.get('file_size', 'N/A')} байт")
        print(f"   • Дата публикации: {img.get('publication_date', 'N/A')}")
        print(f"   • Лайки: {img.get('likes', 'N/A')}")
        print(f"   • Комментарии: {img.get('comments', 'N/A')}")
        
        # Проверяем теги
        if 'ximilar_tags' in img:
            tags = img['ximilar_tags']
            print(f"   • Теги Ximilar: {len(tags.get('tags', []))} тегов")
            if tags.get('tags'):
                for tag in tags['tags'][:3]:  # Показываем первые 3 тега
                    print(f"     - {tag.get('name', 'N/A')} (confidence: {tag.get('confidence', 0):.2f})")
        else:
            print(f"   • Теги Ximilar: НЕТ")
        
        # Проверяем локальный файл
        local_path = img.get('local_path', '')
        if local_path and os.path.exists(local_path):
            try:
                with Image.open(local_path) as pil_img:
                    print(f"   • Размер изображения: {pil_img.size[0]}x{pil_img.size[1]}")
                    print(f"   • Формат: {pil_img.format}")
                    print(f"   • Режим: {pil_img.mode}")
            except Exception as e:
                print(f"   • Ошибка чтения файла: {e}")
        else:
            print(f"   • Локальный файл: НЕ НАЙДЕН")
    
    client.close()

if __name__ == "__main__":
    analyze_images()
