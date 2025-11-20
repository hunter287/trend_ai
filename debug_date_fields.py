#!/usr/bin/env python3
"""
Отладка полей с датами в MongoDB
"""

import os
import pymongo
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
load_dotenv('mongodb_config.env')

def debug_date_fields():
    """Проверка полей с датами"""
    try:
        # Подключаемся к MongoDB
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        client = pymongo.MongoClient(mongodb_uri)
        db = client["instagram_gallery"]
        collection = db["images"]

        # Находим несколько изображений с тегами
        images = list(collection.find(
            {"ximilar_objects_structured": {"$exists": True, "$ne": []}},
            limit=3
        ))

        if images:
            print("🔍 ПРОВЕРКА ПОЛЕЙ С ДАТАМИ:")
            print("="*70)

            for i, image in enumerate(images):
                print(f"\n📷 Изображение {i+1}:")
                print(f"   • _id: {image.get('_id')}")
                print(f"   • filename: {image.get('local_filename')}")

                # Проверяем все поля с датами
                date_fields = {}
                for key in image.keys():
                    if 'date' in key.lower() or 'time' in key.lower() or key in ['timestamp', 'parsed_at', 'tagged_at', 'ximilar_tagged_at']:
                        date_fields[key] = image.get(key)

                if date_fields:
                    print(f"   • Поля с датами:")
                    for field, value in date_fields.items():
                        print(f"     - {field}: {value}")
                else:
                    print(f"   • Поля с датами: НЕТ")

            # Статистика по всем изображениям
            print(f"\n\n📊 СТАТИСТИКА ПО ПОЛЯМ:")
            print("="*70)

            total_images = collection.count_documents({})
            print(f"Всего изображений: {total_images}")

            for field in ['timestamp', 'parsed_at', 'tagged_at', 'ximilar_tagged_at']:
                count = collection.count_documents({field: {"$exists": True}})
                print(f"С полем '{field}': {count} ({count*100//total_images if total_images > 0 else 0}%)")

        else:
            print("❌ Не найдено изображений с тегами")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_date_fields()
