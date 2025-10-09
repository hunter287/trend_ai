#!/usr/bin/env python3
"""
Проверка наличия изображений для пользователя в MongoDB
"""

import os
import pymongo
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
load_dotenv('mongodb_config.env')

def check_user_images(username):
    """Проверка наличия изображений для пользователя"""
    try:
        # Подключаемся к MongoDB
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        client = pymongo.MongoClient(mongodb_uri)
        db = client["instagram_gallery"]
        collection = db["images"]

        # Ищем изображения для пользователя
        total_images = collection.count_documents({"username": username})
        visible_images = collection.count_documents({
            "username": username,
            "hidden": {"$ne": True}
        })
        with_local_file = collection.count_documents({
            "username": username,
            "local_filename": {"$exists": True}
        })

        print(f"🔍 Статистика для @{username}:")
        print(f"   • Всего изображений: {total_images}")
        print(f"   • Видимых изображений: {visible_images}")
        print(f"   • С локальным файлом: {with_local_file}")

        if with_local_file > 0:
            # Показываем несколько примеров
            examples = list(collection.find(
                {
                    "username": username,
                    "local_filename": {"$exists": True}
                },
                {"local_filename": 1, "timestamp": 1, "likes_count": 1}
            ).limit(3))

            print(f"\n📷 Примеры изображений:")
            for img in examples:
                timestamp = img.get('timestamp', 'N/A')
                likes = img.get('likes_count', 0)
                print(f"   • {img['local_filename']} (дата: {timestamp}, лайки: {likes})")
        else:
            print("\n❌ Изображения с локальными файлами не найдены")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else "12storeez"
    check_user_images(username)
