#!/usr/bin/env python3
"""
Извлечение данных из существующих датасетов Apify
"""

import os
import json
from dotenv import load_dotenv
from apify_client import ApifyClient
from pymongo import MongoClient

load_dotenv()
load_dotenv('mongodb_config.env')

def extract_from_dataset(dataset_id: str, limit: int = 100):
    """Извлечение данных из конкретного датасета"""
    
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        print("❌ APIFY_API_TOKEN не найден в .env")
        return
    
    client = ApifyClient(api_token)
    
    try:
        print(f"🔍 Извлечение данных из датасета: {dataset_id}")
        
        # Получаем данные из датасета
        dataset = client.dataset(dataset_id)
        items = dataset.list_items(limit=limit)
        
        print(f"📊 Найдено {items.total} элементов")
        
        if not items.items:
            print("❌ Датасет пустой")
            return
        
        # Анализируем структуру данных
        print(f"\n📋 Структура данных:")
        sample_item = items.items[0]
        print(f"   Ключи: {list(sample_item.keys())}")
        
        # Извлекаем изображения
        images_data = []
        for i, item in enumerate(items.items):
            print(f"   Обработка элемента {i+1}/{len(items.items)}")
            
            # Ищем URL изображений в разных полях
            image_urls = []
            
            # Проверяем разные возможные поля
            for field in ['imageUrl', 'image', 'url', 'mediaUrl', 'thumbnailUrl']:
                if field in item and item[field]:
                    if isinstance(item[field], list):
                        image_urls.extend(item[field])
                    else:
                        image_urls.append(item[field])
            
            # Если есть изображения, сохраняем данные
            if image_urls:
                for j, img_url in enumerate(image_urls):
                    if img_url and 'instagram.com' in img_url:
                        images_data.append({
                            'url': img_url,
                            'post_url': item.get('url', ''),
                            'caption': item.get('caption', ''),
                            'likes': item.get('likes', 0),
                            'comments': item.get('comments', 0),
                            'publication_date': item.get('date', ''),
                            'account_name': item.get('username', ''),
                            'hashtags': item.get('hashtags', []),
                            'source': 'apify_dataset',
                            'dataset_id': dataset_id
                        })
        
        print(f"✅ Извлечено {len(images_data)} изображений")
        
        # Сохраняем в файл
        output_file = f"extracted_images_{dataset_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(images_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Данные сохранены в {output_file}")
        
        # Сохраняем в MongoDB
        save_to_mongodb(images_data)
        
        return images_data
        
    except Exception as e:
        print(f"❌ Ошибка извлечения: {e}")

def save_to_mongodb(images_data):
    """Сохранение данных в MongoDB"""
    try:
        client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:|#!x1K52H.0{8d3@localhost:27017/instagram_gallery'))
        db = client["instagram_gallery"]
        collection = db["images"]
        
        saved_count = 0
        for img_data in images_data:
            # Проверяем, есть ли уже такое изображение
            existing = collection.find_one({"url": img_data["url"]})
            if not existing:
                collection.insert_one(img_data)
                saved_count += 1
        
        print(f"💾 Сохранено {saved_count} новых изображений в MongoDB")
        client.close()
        
    except Exception as e:
        print(f"❌ Ошибка сохранения в MongoDB: {e}")

def list_available_datasets():
    """Список доступных датасетов"""
    
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        print("❌ APIFY_API_TOKEN не найден в .env")
        return
    
    client = ApifyClient(api_token)
    
    try:
        print("📊 ДОСТУПНЫЕ ДАТАСЕТЫ:")
        print("=" * 50)
        
        datasets = client.datasets().list(limit=20)
        
        for i, dataset in enumerate(datasets.items, 1):
            print(f"{i}. {dataset.name}")
            print(f"   ID: {dataset.id}")
            print(f"   Элементов: {dataset.itemCount}")
            print(f"   Создан: {dataset.createdAt}")
            
            if dataset.itemCount > 0:
                try:
                    items = dataset.list_items(limit=1)
                    if items.items:
                        sample = items.items[0]
                        print(f"   Ключи: {list(sample.keys())}")
                except:
                    pass
            
            print()
        
        return [dataset.id for dataset in datasets.items if dataset.itemCount > 0]
        
    except Exception as e:
        print(f"❌ Ошибка получения датасетов: {e}")
        return []

def main():
    """Главная функция"""
    print("🔍 ИЗВЛЕЧЕНИЕ ДАННЫХ ИЗ СУЩЕСТВУЮЩИХ ДАТАСЕТОВ APIFY")
    print("=" * 60)
    
    # Показываем доступные датасеты
    dataset_ids = list_available_datasets()
    
    if not dataset_ids:
        print("❌ Нет доступных датасетов")
        return
    
    # Выбираем датасет
    try:
        choice = input(f"\nВыберите датасет (1-{len(dataset_ids)}): ").strip()
        choice_idx = int(choice) - 1
        
        if 0 <= choice_idx < len(dataset_ids):
            dataset_id = dataset_ids[choice_idx]
            
            # Выбираем лимит
            limit = input("Лимит элементов (Enter для 100): ").strip()
            limit = int(limit) if limit else 100
            
            # Извлекаем данные
            extract_from_dataset(dataset_id, limit)
        else:
            print("❌ Неверный выбор")
            
    except ValueError:
        print("❌ Введите корректное число")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()


