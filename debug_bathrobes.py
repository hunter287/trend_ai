#!/usr/bin/env python3
"""
Проверка проблемы с Bathrobes
Почему фильтр показывает (1 изображение), но находит 3?
"""

import os
import pymongo
import json
from dotenv import load_dotenv

load_dotenv()
load_dotenv('mongodb_config.env')

def main():
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
    client = pymongo.MongoClient(mongodb_uri)
    db = client['instagram_gallery']
    collection = db['images']

    print("=" * 70)
    print("ТЕСТ: Bathrobes - подсчет vs фильтрация")
    print("=" * 70)

    # Запрос для фильтрации (как в /api/filtered-images)
    query = {
        "local_filename": {"$exists": True},
        "hidden": {"$ne": True},
        "is_duplicate": {"$ne": True},
        "ximilar_objects_structured": {
            "$elemMatch": {
                "$and": [{
                    "$or": [
                        {"properties.other_attributes.Subcategory.0.name": "bathrobes"},
                        {"properties.other_attributes.Category.0.name": "bathrobes"}
                    ]
                }]
            }
        }
    }

    results = list(collection.find(query, {"_id": 1, "local_filename": 1, "ximilar_objects_structured": 1}))

    print(f"\n📊 MongoDB запрос находит: {len(results)} документов")
    print()

    for i, img in enumerate(results, 1):
        print(f"{i}. {img['local_filename']}")

        # Считаем сколько раз встречается bathrobes в этом изображении
        bathrobes_count = 0
        bathrobes_colors = []

        for obj in img.get('ximilar_objects_structured', []):
            if obj.get('properties', {}).get('other_attributes'):
                other_attrs = obj['properties']['other_attributes']

                # Проверяем Subcategory[0]
                if other_attrs.get('Subcategory') and len(other_attrs['Subcategory']) > 0:
                    if other_attrs['Subcategory'][0].get('name', '').lower() == 'bathrobes':
                        bathrobes_count += 1

                        # Получаем цвет этого объекта
                        colors = obj.get('properties', {}).get('visual_attributes', {}).get('Color', [])
                        if colors:
                            color_names = [c['name'] for c in colors]
                            bathrobes_colors.append(', '.join(color_names))
                        else:
                            bathrobes_colors.append('(нет цвета)')

                # Проверяем Category[0]
                elif other_attrs.get('Category') and len(other_attrs['Category']) > 0:
                    if other_attrs['Category'][0].get('name', '').lower() == 'bathrobes':
                        bathrobes_count += 1

                        colors = obj.get('properties', {}).get('visual_attributes', {}).get('Color', [])
                        if colors:
                            color_names = [c['name'] for c in colors]
                            bathrobes_colors.append(', '.join(color_names))
                        else:
                            bathrobes_colors.append('(нет цвета)')

        print(f"   📦 Объектов 'bathrobes' в изображении: {bathrobes_count}")
        for j, color in enumerate(bathrobes_colors, 1):
            print(f"      Объект #{j}: {color}")
        print()

    print("=" * 70)
    print("АНАЛИЗ:")
    print("=" * 70)

    # Подсчет как в /api/filter-options (с дедупликацией по названию объекта)
    deduplicated_count = 0
    for img in results:
        # Дедупликация объектов по их основному названию
        unique_objects_by_name = {}

        for obj in img.get('ximilar_objects_structured', []):
            obj_name = ''
            if obj.get('properties', {}).get('other_attributes'):
                other_attrs = obj['properties']['other_attributes']

                if other_attrs.get('Subcategory') and len(other_attrs['Subcategory']) > 0:
                    obj_name = other_attrs['Subcategory'][0]['name']
                elif other_attrs.get('Category') and len(other_attrs['Category']) > 0:
                    obj_name = other_attrs['Category'][0]['name']

            # Если объект с таким названием уже есть, пропускаем
            if obj_name and obj_name in unique_objects_by_name:
                continue

            # Сохраняем первый объект с этим названием
            if obj_name:
                unique_objects_by_name[obj_name] = obj

        # Проверяем, есть ли bathrobes среди уникальных объектов
        for obj in unique_objects_by_name.values():
            original_subcategory = ''
            if obj.get('properties', {}).get('other_attributes'):
                other_attrs = obj['properties']['other_attributes']

                if other_attrs.get('Subcategory') and len(other_attrs['Subcategory']) > 0:
                    original_subcategory = other_attrs['Subcategory'][0]['name']
                elif other_attrs.get('Category') and len(other_attrs['Category']) > 0:
                    original_subcategory = other_attrs['Category'][0]['name']

            if original_subcategory.lower() == 'bathrobes':
                deduplicated_count += 1
                break

    print(f"✅ Подсчет в /api/filter-options (с дедупликацией): {deduplicated_count} изображений")
    print(f"❌ Фильтрация в /api/filtered-images (без дедупликации): {len(results)} изображений")
    print()

    if deduplicated_count != len(results):
        print("⚠️  ПРОБЛЕМА: Подсчет и фильтрация не синхронизированы!")
        print()
        print("ПРИЧИНА:")
        print("  • Если в изображении несколько объектов 'bathrobes',")
        print("  • /api/filter-options считает изображение 1 раз (дедупликация)")
        print("  • /api/filtered-images находит изображение несколько раз")
        print()
        print("РЕШЕНИЕ:")
        print("  • MongoDB запрос правильный - он находит изображения с bathrobes")
        print("  • Но нужна ДЕДУПЛИКАЦИЯ на уровне Python или distinct по _id")

if __name__ == "__main__":
    main()
