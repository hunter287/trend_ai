#!/usr/bin/env python3
"""
Проверка состояния MongoDB и данных с аутентификацией
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
load_dotenv('mongodb_config.env')

def check_mongodb():
    """Проверка MongoDB и данных"""
    
    print("🔍 ПРОВЕРКА MONGODB И ДАННЫХ")
    print("=" * 50)
    
    # Получаем настройки из переменных окружения
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:|#!x1K52H.0{8d3@localhost:27017/instagram_gallery')
    
    print(f"🔗 Подключение к: {mongodb_uri.replace('|#!x1K52H.0{8d3', '***')}")
    
    # Проверяем подключение
    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        
        # Тестируем подключение
        client.admin.command('ping')
        print("✅ MongoDB подключен успешно с аутентификацией")
        
        # Получаем список баз данных
        dbs = client.list_database_names()
        print(f"📊 Базы данных: {dbs}")
        
        # Проверяем базу instagram_gallery
        if 'instagram_gallery' in dbs:
            db = client.instagram_gallery
            collections = db.list_collection_names()
            print(f"📂 Коллекции в instagram_gallery: {collections}")
            
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
                        tags_data = first_img['ximilar_tags']
                        if isinstance(tags_data, dict) and 'tags' in tags_data:
                            tags = tags_data['tags']
                            print(f"   • Теги Ximilar: {len(tags)} тегов")
                        elif isinstance(tags_data, list):
                            print(f"   • Теги Ximilar: {len(tags_data)} тегов")
                        else:
                            print(f"   • Теги Ximilar: {tags_data}")
                    else:
                        print(f"   • Теги Ximilar: НЕТ")
                else:
                    print("❌ Коллекция images пустая")
            else:
                print("❌ Коллекция images не найдена")
        else:
            print("❌ База данных instagram_gallery не найдена")
            
        client.close()
        
    except Exception as e:
        print(f"❌ Ошибка подключения к MongoDB: {e}")
        print("💡 Возможные решения:")
        print("   • Проверить, что MongoDB запущен: sudo systemctl status mongod")
        print("   • Проверить правильность пароля")
        print("   • Проверить, что пользователь создан: mongosh --eval 'use admin; db.system.users.find()'")

if __name__ == "__main__":
    check_mongodb()