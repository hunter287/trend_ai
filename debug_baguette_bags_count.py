#!/usr/bin/env python3
"""
Отладка подсчета изображений с baguette bags
Сравнение логики подсчета в /api/filter-options и фактического MongoDB запроса
"""

import os
import pymongo
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
load_dotenv('mongodb_config.env')

def normalize_subcategory_name(subcategory, category):
    """Нормализует название подкатегории (копия из web_parser.py)"""
    subcategory_lower = subcategory.lower()

    normalization_rules = {
        'Accessories': {
            'Bags': ['bag', 'handbag', 'tote', 'clutch', 'crossbody', 'purse', 'wallet'],
        }
    }

    if category in normalization_rules:
        for base_name, keywords in normalization_rules[category].items():
            for keyword in keywords:
                if keyword in subcategory_lower:
                    return base_name

    return subcategory

def main():
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
    client = pymongo.MongoClient(mongodb_uri)
    db = client['instagram_gallery']
    collection = db['images']

    print("=" * 70)
    print("ТЕСТ 1: Подсчет в /api/filter-options (логика дедупликации)")
    print("=" * 70)

    # Получаем все изображения с тегами (как в /api/filter-options)
    images = list(collection.find(
        {
            "local_filename": {"$exists": True},
            "hidden": {"$ne": True},
            "$or": [
                {"ximilar_objects_structured": {"$exists": True, "$ne": []}},
                {"ximilar_tags": {"$exists": True, "$ne": []}}
            ]
        },
        {"_id": 1, "local_filename": 1, "ximilar_objects_structured": 1}
    ))

    # Подсчитываем по логике /api/filter-options
    baguette_bags_images_deduplicated = set()

    for image in images:
        if image.get('ximilar_objects_structured'):
            # Дедуплицируем объекты по их основному названию
            unique_objects_by_name = {}

            for obj in image['ximilar_objects_structured']:
                obj_name = ''
                if obj.get('properties'):
                    if obj['properties'].get('other_attributes'):
                        if obj['properties']['other_attributes'].get('Subcategory'):
                            obj_name = obj['properties']['other_attributes']['Subcategory'][0]['name']
                        elif obj['properties']['other_attributes'].get('Category'):
                            obj_name = obj['properties']['other_attributes']['Category'][0]['name']

                # Если объект с таким названием уже есть, пропускаем
                if obj_name and obj_name in unique_objects_by_name:
                    continue

                # Сохраняем первый объект с этим названием
                if obj_name:
                    unique_objects_by_name[obj_name] = obj

            # Проверяем, есть ли baguette bags среди уникальных объектов
            for obj in unique_objects_by_name.values():
                original_subcategory = ''
                if obj.get('properties'):
                    if obj['properties'].get('other_attributes'):
                        if obj['properties']['other_attributes'].get('Subcategory'):
                            original_subcategory = obj['properties']['other_attributes']['Subcategory'][0]['name']
                        elif obj['properties']['other_attributes'].get('Category'):
                            original_subcategory = obj['properties']['other_attributes']['Category'][0]['name']

                if original_subcategory == 'baguette bags':
                    baguette_bags_images_deduplicated.add(image['_id'])
                    break

    print(f"📊 Найдено изображений (с дедупликацией): {len(baguette_bags_images_deduplicated)}")
    print(f"   Это значение должно показываться в фильтре")
    print()

    print("=" * 70)
    print("ТЕСТ 2: MongoDB запрос /api/filtered-images")
    print("=" * 70)

    # Запрос точно такой же, как в /api/filtered-images
    query = {
        'local_filename': {'$exists': True},
        'hidden': {'$ne': True},
        'is_duplicate': {'$ne': True},
        'ximilar_objects_structured': {
            '$elemMatch': {
                '$or': [
                    {'properties.other_attributes.Subcategory': {'$elemMatch': {'name': 'baguette bags'}}},
                    {'properties.other_attributes.Category': {'$elemMatch': {'name': 'baguette bags'}}}
                ]
            }
        }
    }

    images_filtered = list(collection.find(query, {'_id': 1, 'local_filename': 1, 'ximilar_objects_structured': 1}))

    print(f"📊 Найдено изображений (MongoDB запрос): {len(images_filtered)}")
    print(f"   Это значение показывается пользователю")
    print()

    print("=" * 70)
    print("АНАЛИЗ РАЗНИЦЫ")
    print("=" * 70)

    deduplicated_ids = set(baguette_bags_images_deduplicated)
    filtered_ids = set(img['_id'] for img in images_filtered)

    extra_in_filtered = filtered_ids - deduplicated_ids
    missing_in_filtered = deduplicated_ids - filtered_ids

    print(f"✅ Совпадают: {len(deduplicated_ids & filtered_ids)} изображений")
    print(f"➕ Лишние в фильтрации: {len(extra_in_filtered)} изображений")
    print(f"➖ Отсутствуют в фильтрации: {len(missing_in_filtered)} изображений")
    print()

    if extra_in_filtered:
        print("🔍 ЛИШНИЕ ИЗОБРАЖЕНИЯ (есть в фильтрации, но не в подсчете):")
        for img_id in extra_in_filtered:
            img = collection.find_one({'_id': img_id}, {'local_filename': 1, 'ximilar_objects_structured': 1})
            print(f"   • {img['local_filename']}")

            # Анализируем почему это изображение попало в фильтрацию
            all_subcats = []
            for obj in img.get('ximilar_objects_structured', []):
                props = obj.get('properties', {})
                other_attrs = props.get('other_attributes', {})

                subcat = other_attrs.get('Subcategory', [])
                if subcat:
                    all_subcats.append(subcat[0].get('name', ''))

                cat = other_attrs.get('Category', [])
                if cat:
                    all_subcats.append(f"Category: {cat[0].get('name', '')}")

            print(f"     Все объекты: {', '.join(all_subcats)}")

            # Считаем сколько раз встречается baguette bags
            baguette_count = sum(1 for s in all_subcats if 'baguette bags' in s.lower())
            print(f"     Объектов 'baguette bags': {baguette_count}")
            print()

    if missing_in_filtered:
        print("🔍 ОТСУТСТВУЮЩИЕ ИЗОБРАЖЕНИЯ (есть в подсчете, но не в фильтрации):")
        for img_id in missing_in_filtered:
            img = collection.find_one({'_id': img_id}, {'local_filename': 1})
            print(f"   • {img['local_filename']}")
        print()

    print("=" * 70)
    print("ВЫВОД:")
    print("=" * 70)
    if len(deduplicated_ids) == len(filtered_ids):
        print("✅ Подсчет совпадает с фильтрацией!")
    else:
        print(f"❌ Несоответствие: фильтр показывает {len(deduplicated_ids)}, а находит {len(filtered_ids)}")
        print(f"   Разница: {abs(len(filtered_ids) - len(deduplicated_ids))} изображений")

        if len(filtered_ids) > len(deduplicated_ids):
            print(f"   Причина: MongoDB запрос находит изображения с НЕСКОЛЬКИМИ объектами 'baguette bags',")
            print(f"            а логика подсчета дедуплицирует их и считает изображение только 1 раз")

if __name__ == "__main__":
    main()
