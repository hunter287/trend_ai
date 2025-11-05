#!/usr/bin/env python3
"""
Детальный анализ ложного срабатывания
Почему DLK8Gw9tIiW_gallery_0827.jpg попадает в фильтр "baguette bags"
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

    # Получаем проблемное изображение
    image = collection.find_one({'local_filename': 'DLK8Gw9tIiW_gallery_0827.jpg'})

    if not image:
        print("❌ Изображение не найдено")
        return

    print("=" * 70)
    print("АНАЛИЗ ИЗОБРАЖЕНИЯ: DLK8Gw9tIiW_gallery_0827.jpg")
    print("=" * 70)
    print()

    print("СТРУКТУРА ximilar_objects_structured:")
    print("-" * 70)

    for i, obj in enumerate(image.get('ximilar_objects_structured', []), 1):
        print(f"\n📦 Объект #{i}:")
        print(f"   top_category: {obj.get('top_category', 'НЕТ')}")

        if obj.get('properties'):
            props = obj['properties']

            if props.get('other_attributes'):
                other_attrs = props['other_attributes']
                print(f"   other_attributes:")

                if 'Subcategory' in other_attrs:
                    subcat = other_attrs['Subcategory']
                    print(f"      Subcategory: {json.dumps(subcat, indent=10, ensure_ascii=False)}")

                if 'Category' in other_attrs:
                    cat = other_attrs['Category']
                    print(f"      Category: {json.dumps(cat, indent=10, ensure_ascii=False)}")

    print()
    print("=" * 70)
    print("ТЕСТ MONGODB ЗАПРОСА")
    print("=" * 70)

    # Тестируем разные варианты запроса
    queries = [
        {
            'name': 'Текущий запрос (через $or)',
            'query': {
                '_id': image['_id'],
                'ximilar_objects_structured': {
                    '$elemMatch': {
                        '$or': [
                            {'properties.other_attributes.Subcategory': {'$elemMatch': {'name': 'baguette bags'}}},
                            {'properties.other_attributes.Category': {'$elemMatch': {'name': 'baguette bags'}}}
                        ]
                    }
                }
            }
        },
        {
            'name': 'Только по Subcategory',
            'query': {
                '_id': image['_id'],
                'ximilar_objects_structured': {
                    '$elemMatch': {
                        'properties.other_attributes.Subcategory': {'$elemMatch': {'name': 'baguette bags'}}
                    }
                }
            }
        },
        {
            'name': 'Только по Category',
            'query': {
                '_id': image['_id'],
                'ximilar_objects_structured': {
                    '$elemMatch': {
                        'properties.other_attributes.Category': {'$elemMatch': {'name': 'baguette bags'}}
                    }
                }
            }
        }
    ]

    for test in queries:
        result = collection.find_one(test['query'])
        match = "✅ НАЙДЕНО" if result else "❌ НЕ НАЙДЕНО"
        print(f"\n{test['name']}: {match}")

    print()
    print("=" * 70)
    print("ВЫВОД:")
    print("=" * 70)
    print("Если 'Текущий запрос' находит изображение, а 'Только по Subcategory' и 'Только по Category' НЕ находят,")
    print("значит проблема в логике MongoDB - возможно пустые массивы или null значения")

if __name__ == "__main__":
    main()
