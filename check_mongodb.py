#!/usr/bin/env python3
"""
Проверка состояния MongoDB и данных
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

def check_mongodb():
    """Проверка MongoDB и данных"""
    
    print("🔍 ПРОВЕРКА MONGODB И ДАННЫХ")
    print("=" * 50)
    
    # Проверяем подключение
    try:
        mongodb_uri = "mongodb://localhost:27017/"
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        
        # Тестируем подключение
        client.admin.command('ping')
        print("✅ MongoDB подключен успешно")
        
        # Получаем список баз данных
        dbs = client.list_database_names()
        print(f"📊 Базы данных: {dbs}")
        
        # Проверяем базу instagram_images
        if 'instagram_images' in dbs:
            db = client.instagram_images
            collections = db.list_collection_names()
            print(f"📂 Коллекции в instagram_images: {collections}")
            
            if 'images' in collections:
                count = db.images.count_documents({})
                print(f"📸 Изображений в коллекции images: {count}")
                
                if count > 0:
                    # Показываем первое изображение
                    first_img = db.images.find_one()
                    print(f"🖼️ Первое изображение:")
                    print(f"   • ID: {first_img['_id']}")
                    print(f"   • URL: {first_img.get('full_image_url', 'N/A')}")
                    print(f"   • Локальный файл: {first_img.get('local_filename', 'N/A')}")
                    print(f"   • Дата публикации: {first_img.get('publication_date', 'N/A')}")
                    print(f"   • Лайки: {first_img.get('likes', 'N/A')}")
                    print(f"   • Комментарии: {first_img.get('comments', 'N/A')}")
                    
                    # Проверяем теги
                    if 'ximilar_tags' in first_img:
                        tags = first_img['ximilar_tags']
                        print(f"   • Теги Ximilar: {len(tags.get('tags', []))} тегов")
                    else:
                        print(f"   • Теги Ximilar: НЕТ")
                else:
                    print("❌ Коллекция images пустая")
            else:
                print("❌ Коллекция images не найдена")
        else:
            print("❌ База данных instagram_images не найдена")
            
        client.close()
        
    except Exception as e:
        print(f"❌ Ошибка подключения к MongoDB: {e}")
        print("💡 Возможные решения:")
        print("   • sudo systemctl start mongod")
        print("   • sudo systemctl enable mongod")
        print("   • Проверить статус: sudo systemctl status mongod")

if __name__ == "__main__":
    check_mongodb()
