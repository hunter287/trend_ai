#!/usr/bin/env python3
"""
Использование существующих данных из Apify без новых запросов
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from instagram_parser import InstagramParser

load_dotenv()
load_dotenv('mongodb_config.env')

def find_existing_data():
    """Поиск существующих JSON файлов с данными"""
    json_files = list(Path(".").glob("*account_data_*.json"))
    if json_files:
        latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
        print(f"📁 Найден файл: {latest_file}")
        return latest_file
    return None

def use_existing_data():
    """Использование существующих данных"""
    print("🔍 Поиск существующих данных...")
    
    # Ищем JSON файлы
    json_file = find_existing_data()
    if not json_file:
        print("❌ JSON файлы с данными не найдены")
        return False
    
    # Загружаем данные
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 Загружено {len(data)} постов")
    
    # Создаем парсер (без токена, так как не будем делать новые запросы)
    parser = InstagramParser("dummy_token", os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:|#!x1K52H.0{8d3@localhost:27017/instagram_gallery'))
    
    # Подключаемся к MongoDB
    if not parser.connect_mongodb():
        print("❌ Не удалось подключиться к MongoDB")
        return False
    
    # Извлекаем URL изображений
    print("🖼️ Извлечение URL изображений...")
    image_data = parser.extract_image_urls(data)
    
    if not image_data:
        print("❌ Не удалось извлечь URL изображений")
        return False
    
    # Скачиваем изображения
    print("⬇️ Скачивание изображений...")
    downloaded_data = parser.download_images(image_data, max_images=50)
    
    if not downloaded_data:
        print("❌ Не удалось скачать изображения")
        return False
    
    # Сохраняем в MongoDB
    print("💾 Сохранение в MongoDB...")
    parser.save_to_mongodb(downloaded_data, "linda.sza")
    
    # Создаем HTML галерею
    print("🌐 Создание HTML галереи...")
    parser.create_gallery_html(downloaded_data, "linda.sza")
    
    print("✅ Готово! Использованы существующие данные")
    return True

if __name__ == "__main__":
    use_existing_data()


