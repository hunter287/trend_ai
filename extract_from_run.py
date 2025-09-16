#!/usr/bin/env python3
"""
Извлечение данных из конкретного запуска Apify
"""

import os
import json
from dotenv import load_dotenv
from apify_client import ApifyClient
from pymongo import MongoClient

load_dotenv()
load_dotenv('mongodb_config.env')

def extract_from_run(run_id: str, limit: int = 100):
    """Извлечение данных из конкретного запуска"""
    
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        print("❌ APIFY_API_TOKEN не найден в .env")
        return
    
    client = ApifyClient(api_token)
    
    try:
        print(f"🔍 Извлечение данных из запуска: {run_id}")
        
        # Получаем информацию о запуске
        run = client.run(run_id).get()
        print(f"📊 Статус запуска: {run.get('status', 'N/A')}")
        print(f"📅 Запущен: {run.get('startedAt', 'N/A')}")
        print(f"📅 Завершен: {run.get('finishedAt', 'N/A')}")
        
        if run.get('status') != 'SUCCEEDED':
            print("❌ Запуск не завершен успешно")
            return
        
        # Получаем датасет
        dataset_id = run.get('defaultDatasetId')
        if not dataset_id:
            print("❌ Датасет не найден")
            return
        
        print(f"📊 Датасет ID: {dataset_id}")
        
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
            
            # Проверяем поле 'images' (может быть список)
            if 'images' in item and item['images']:
                if isinstance(item['images'], list):
                    image_urls.extend(item['images'])
                else:
                    image_urls.append(item['images'])
            
            # Проверяем поле 'displayUrl'
            if 'displayUrl' in item and item['displayUrl']:
                image_urls.append(item['displayUrl'])
            
            # Проверяем другие возможные поля
            for field in ['imageUrl', 'image', 'url', 'mediaUrl', 'thumbnailUrl']:
                if field in item and item[field]:
                    if isinstance(item[field], list):
                        image_urls.extend(item[field])
                    else:
                        image_urls.append(item[field])
            
            # Если есть изображения, сохраняем данные
            if image_urls:
                for j, img_url in enumerate(image_urls):
                    if img_url and ('instagram.com' in img_url or 'cdninstagram.com' in img_url):
                        images_data.append({
                            'url': img_url,
                            'post_url': item.get('url', ''),
                            'caption': item.get('caption', ''),
                            'likes': item.get('likesCount', 0),
                            'comments': item.get('commentsCount', 0),
                            'publication_date': item.get('timestamp', ''),
                            'account_name': item.get('ownerUsername', ''),
                            'hashtags': item.get('hashtags', []),
                            'mentions': item.get('mentions', []),
                            'post_id': item.get('id', ''),
                            'short_code': item.get('shortCode', ''),
                            'dimensions': {
                                'width': item.get('dimensionsWidth', 0),
                                'height': item.get('dimensionsHeight', 0)
                            },
                            'source': 'apify_run',
                            'run_id': run_id,
                            'dataset_id': dataset_id
                        })
        
        print(f"✅ Извлечено {len(images_data)} изображений")
        
        # Сохраняем в файл
        output_file = f"extracted_images_{run_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(images_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Данные сохранены в {output_file}")
        
        # Сохраняем в MongoDB
        save_to_mongodb(images_data)
        
        return images_data
        
    except Exception as e:
        print(f"❌ Ошибка извлечения: {e}")
        import traceback
        traceback.print_exc()

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

def main():
    """Главная функция"""
    print("🔍 ИЗВЛЕЧЕНИЕ ДАННЫХ ИЗ КОНКРЕТНОГО ЗАПУСКА APIFY")
    print("=" * 60)
    
    # Используем известный ID запуска
    run_id = "2kExkDIAwlqdRuvtD"
    
    print(f"📊 Извлекаем данные из запуска: {run_id}")
    
    # Выбираем лимит
    limit = input("Лимит элементов (Enter для 100): ").strip()
    limit = int(limit) if limit else 100
    
    # Извлекаем данные
    extract_from_run(run_id, limit)

if __name__ == "__main__":
    main()


