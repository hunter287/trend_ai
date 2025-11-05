#!/usr/bin/env python3
"""
Проверка дубликатов в результатах фильтрации
Почему после исправления снова появились дублированные изображения?
"""

import os
import pymongo
from collections import Counter
from dotenv import load_dotenv

load_dotenv()
load_dotenv('mongodb_config.env')

def main():
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
    client = pymongo.MongoClient(mongodb_uri)
    db = client['instagram_gallery']
    collection = db['images']

    print("=" * 70)
    print("ТЕСТ 1: Базовый запрос baguette bags (без фильтра по цвету)")
    print("=" * 70)

    # Запрос без цвета
    query_no_color = {
        "local_filename": {"$exists": True},
        "hidden": {"$ne": True},
        "is_duplicate": {"$ne": True},
        "ximilar_objects_structured": {
            "$elemMatch": {
                "$and": [{
                    "$or": [
                        {"properties.other_attributes.Subcategory.0.name": "baguette bags"},
                        {"properties.other_attributes.Category.0.name": "baguette bags"}
                    ]
                }]
            }
        }
    }

    results1 = list(collection.find(query_no_color, {"_id": 1, "local_filename": 1}))
    print(f"\n📊 Найдено: {len(results1)} документов")

    # Проверяем на дубликаты по _id
    ids = [str(r['_id']) for r in results1]
    id_counts = Counter(ids)
    duplicates = {k: v for k, v in id_counts.items() if v > 1}

    if duplicates:
        print(f"❌ ДУБЛИКАТЫ по _id найдены: {len(duplicates)}")
        for doc_id, count in duplicates.items():
            print(f"   • {doc_id}: {count} раз")
    else:
        print(f"✅ Дубликатов по _id НЕТ")

    # Проверяем на дубликаты по filename
    filenames = [r['local_filename'] for r in results1]
    filename_counts = Counter(filenames)
    filename_duplicates = {k: v for k, v in filename_counts.items() if v > 1}

    if filename_duplicates:
        print(f"❌ ДУБЛИКАТЫ по filename найдены: {len(filename_duplicates)}")
        for filename, count in filename_duplicates.items():
            print(f"   • {filename}: {count} раз")
    else:
        print(f"✅ Дубликатов по filename НЕТ")

    print("\n" + "=" * 70)
    print("ТЕСТ 2: Запрос baguette bags + brown (новая логика)")
    print("=" * 70)

    query_with_color = {
        "local_filename": {"$exists": True},
        "hidden": {"$ne": True},
        "is_duplicate": {"$ne": True},
        "ximilar_objects_structured": {
            "$elemMatch": {
                "$and": [
                    {
                        "$or": [
                            {"properties.other_attributes.Subcategory.0.name": "baguette bags"},
                            {"properties.other_attributes.Category.0.name": "baguette bags"}
                        ]
                    },
                    {
                        "properties.visual_attributes.Color": {"$elemMatch": {"name": "brown"}}
                    }
                ]
            }
        }
    }

    results2 = list(collection.find(query_with_color, {"_id": 1, "local_filename": 1}))
    print(f"\n📊 Найдено: {len(results2)} документов")

    # Проверяем на дубликаты по _id
    ids2 = [str(r['_id']) for r in results2]
    id_counts2 = Counter(ids2)
    duplicates2 = {k: v for k, v in id_counts2.items() if v > 1}

    if duplicates2:
        print(f"❌ ДУБЛИКАТЫ по _id найдены: {len(duplicates2)}")
        for doc_id, count in duplicates2.items():
            print(f"   • {doc_id}: {count} раз")
    else:
        print(f"✅ Дубликатов по _id НЕТ")

    # Проверяем на дубликаты по filename
    filenames2 = [r['local_filename'] for r in results2]
    filename_counts2 = Counter(filenames2)
    filename_duplicates2 = {k: v for k, v in filename_counts2.items() if v > 1}

    if filename_duplicates2:
        print(f"❌ ДУБЛИКАТЫ по filename найдены: {len(filename_duplicates2)}")
        for filename, count in filename_duplicates2.items():
            print(f"   • {filename}: {count} раз")
    else:
        print(f"✅ Дубликатов по filename НЕТ")

    print("\nСписок найденных изображений:")
    for r in results2:
        print(f"  • {r['local_filename']}")

    print("\n" + "=" * 70)
    print("ТЕСТ 3: Проверка is_duplicate флага")
    print("=" * 70)

    # Проверяем, есть ли изображения baguette bags с is_duplicate = True
    query_duplicates_check = {
        "local_filename": {"$exists": True},
        "is_duplicate": True,
        "ximilar_objects_structured": {
            "$elemMatch": {
                "$or": [
                    {"properties.other_attributes.Subcategory.0.name": "baguette bags"},
                    {"properties.other_attributes.Category.0.name": "baguette bags"}
                ]
            }
        }
    }

    duplicate_docs = list(collection.find(query_duplicates_check, {"_id": 1, "local_filename": 1}))
    print(f"\n📊 Найдено baguette bags с is_duplicate=True: {len(duplicate_docs)} документов")

    if duplicate_docs:
        print("⚠️  Эти изображения имеют флаг is_duplicate=True:")
        for doc in duplicate_docs:
            print(f"   • {doc['local_filename']}")

    print("\n" + "=" * 70)
    print("ВЫВОД:")
    print("=" * 70)
    print("Если MongoDB НЕ возвращает дубликаты по _id,")
    print("но в браузере видны дубликаты, проблема на frontend:")
    print("  • Проверить loadMoreImages() - возможно добавляет дважды")
    print("  • Проверить applyAdvancedFilters() - возможно не очищает галерею")
    print("  • Проверить renderImage() - возможно вызывается дважды")

if __name__ == "__main__":
    main()
