#!/usr/bin/env python3
"""
Проверка структуры Category для Bathrobes
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
    print("СТРУКТУРА CATEGORY ДЛЯ BATHROBES")
    print("=" * 70)

    # Находим одно изображение с Bathrobes
    image = collection.find_one({
        'local_filename': 'DPUCBVpjMZw_gallery_0097.jpg'
    })

    if not image:
        print("❌ Изображение не найдено")
        return

    print(f"\n📄 Изображение: {image['local_filename']}")
    print()

    for i, obj in enumerate(image.get('ximilar_objects_structured', []), 1):
        print(f"📦 Объект #{i}:")

        if obj.get('properties', {}).get('other_attributes'):
            other_attrs = obj['properties']['other_attributes']

            # Проверяем Category
            if 'Category' in other_attrs:
                print(f"   ✅ Category существует")
                print(f"   Структура Category:")
                print(json.dumps(other_attrs['Category'], indent=6, ensure_ascii=False))
                print()

                # Проверяем, есть ли bathrobe
                if isinstance(other_attrs['Category'], list):
                    for idx, cat in enumerate(other_attrs['Category']):
                        name = cat.get('name', '')
                        if 'bathrobe' in name.lower():
                            print(f"   🎯 Bathrobe найден на позиции [{idx}]")
                            print(f"      Значение: {name}")
                            if idx == 0:
                                print(f"      ✅ На первой позиции - Category.0.name должен работать")
                            else:
                                print(f"      ❌ НЕ на первой позиции - Category.0.name НЕ найдет!")

            # Проверяем Subcategory
            if 'Subcategory' in other_attrs:
                print(f"   ✅ Subcategory существует")
                print(f"   Структура Subcategory:")
                print(json.dumps(other_attrs['Subcategory'], indent=6, ensure_ascii=False))
                print()

        print()

    print("=" * 70)
    print("ТЕСТ MONGODB ЗАПРОСОВ")
    print("=" * 70)

    # Тест 1: Category.0.name
    query1 = {
        '_id': image['_id'],
        'ximilar_objects_structured': {
            '$elemMatch': {
                'properties.other_attributes.Category.0.name': 'Clothing/Bathrobes'
            }
        }
    }
    result1 = collection.find_one(query1)
    print(f"\n1. Category.0.name = 'Clothing/Bathrobes': {'✅ НАЙДЕНО' if result1 else '❌ НЕ НАЙДЕНО'}")

    # Тест 2: Category с $elemMatch
    query2 = {
        '_id': image['_id'],
        'ximilar_objects_structured': {
            '$elemMatch': {
                'properties.other_attributes.Category': {'$elemMatch': {'name': 'Clothing/Bathrobes'}}
            }
        }
    }
    result2 = collection.find_one(query2)
    print(f"2. Category $elemMatch name = 'Clothing/Bathrobes': {'✅ НАЙДЕНО' if result2 else '❌ НЕ НАЙДЕНО'}")

    # Тест 3: Проверка с $or (как в нашем коде)
    query3 = {
        '_id': image['_id'],
        'ximilar_objects_structured': {
            '$elemMatch': {
                '$and': [{
                    '$or': [
                        {'properties.other_attributes.Subcategory.0.name': 'Clothing/Bathrobes'},
                        {'properties.other_attributes.Category.0.name': 'Clothing/Bathrobes'}
                    ]
                }]
            }
        }
    }
    result3 = collection.find_one(query3)
    print(f"3. Текущий запрос (Subcategory.0 OR Category.0): {'✅ НАЙДЕНО' if result3 else '❌ НЕ НАЙДЕНО'}")

    print("\n" + "=" * 70)
    print("ВЫВОД:")
    print("=" * 70)
    print("Если ТЕСТ 3 НЕ НАХОДИТ, значит проблема в структуре запроса.")
    print("Нужно использовать $elemMatch для Category, а не .0.name")

if __name__ == "__main__":
    main()
