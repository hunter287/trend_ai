#!/usr/bin/env python3
"""
Отладка фильтрации по цветам
Проверяем почему запрос с цветом brown возвращает 0 изображений
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
    print("ТЕСТ 1: Базовый запрос (только subsubcategory)")
    print("=" * 70)

    # Базовый запрос (как в /api/filtered-images)
    base_query = {
        "local_filename": {"$exists": True},
        "hidden": {"$ne": True},
        "is_duplicate": {"$ne": True},
        "ximilar_objects_structured": {
            "$elemMatch": {
                "$or": [
                    {"properties.other_attributes.Subcategory.0.name": "baguette bags"},
                    {"properties.other_attributes.Category.0.name": "baguette bags"}
                ]
            }
        }
    }

    result1 = list(collection.find(base_query, {"local_filename": 1, "ximilar_objects_structured": 1}))
    print(f"📊 Найдено: {len(result1)} изображений")

    # Показываем какие цвета есть у этих изображений
    print("\n🎨 Цвета в найденных изображениях:")
    for img in result1:
        print(f"\n  📄 {img['local_filename']}:")
        for obj in img.get('ximilar_objects_structured', []):
            if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                colors = obj['properties']['visual_attributes']['Color']
                color_names = [c['name'] for c in colors]
                print(f"     • {', '.join(color_names)}")

    print("\n" + "=" * 70)
    print("ТЕСТ 2: Запрос с цветом brown (через $and)")
    print("=" * 70)

    # Запрос с цветом (как должен работать в /api/filtered-images)
    query_with_color = {
        "local_filename": {"$exists": True},
        "hidden": {"$ne": True},
        "is_duplicate": {"$ne": True},
        "$and": [
            {
                "ximilar_objects_structured": {
                    "$elemMatch": {
                        "$or": [
                            {"properties.other_attributes.Subcategory.0.name": "baguette bags"},
                            {"properties.other_attributes.Category.0.name": "baguette bags"}
                        ]
                    }
                }
            },
            {
                "ximilar_objects_structured": {
                    "$elemMatch": {
                        "properties.visual_attributes.Color": {"$elemMatch": {"name": "brown"}}
                    }
                }
            }
        ]
    }

    print(f"\n🔍 MongoDB запрос:")
    print(json.dumps(query_with_color, indent=2, ensure_ascii=False))
    print()

    result2 = list(collection.find(query_with_color, {"local_filename": 1}))
    print(f"📊 Найдено: {len(result2)} изображений")

    if result2:
        for img in result2:
            print(f"  • {img['local_filename']}")
    else:
        print("  ❌ Ничего не найдено")

    print("\n" + "=" * 70)
    print("ТЕСТ 3: Упрощенный запрос (только цвет brown, без subsubcategory)")
    print("=" * 70)

    simple_color_query = {
        "local_filename": {"$exists": True},
        "ximilar_objects_structured": {
            "$elemMatch": {
                "properties.visual_attributes.Color": {"$elemMatch": {"name": "brown"}}
            }
        }
    }

    result3 = list(collection.find(simple_color_query, {"local_filename": 1}).limit(10))
    print(f"📊 Найдено: {len(result3)} изображений (первые 10)")

    for img in result3:
        print(f"  • {img['local_filename']}")

    print("\n" + "=" * 70)
    print("ТЕСТ 4: Проверка одного изображения с brown из baguette bags")
    print("=" * 70)

    # Находим изображения baguette bags, которые имеют brown
    for img in result1:
        has_brown = False
        for obj in img.get('ximilar_objects_structured', []):
            colors = obj.get('properties', {}).get('visual_attributes', {}).get('Color', [])
            if any(c['name'] == 'brown' for c in colors):
                has_brown = True
                break

        if has_brown:
            print(f"\n✅ Изображение с brown найдено: {img['local_filename']}")

            # Проверяем, находит ли его запрос с $and
            test_query = {
                "_id": img["_id"],
                "$and": [
                    {
                        "ximilar_objects_structured": {
                            "$elemMatch": {
                                "$or": [
                                    {"properties.other_attributes.Subcategory.0.name": "baguette bags"},
                                    {"properties.other_attributes.Category.0.name": "baguette bags"}
                                ]
                            }
                        }
                    },
                    {
                        "ximilar_objects_structured": {
                            "$elemMatch": {
                                "properties.visual_attributes.Color": {"$elemMatch": {"name": "brown"}}
                            }
                        }
                    }
                ]
            }

            test_result = collection.find_one(test_query)
            if test_result:
                print("   ✅ Запрос с $and НАХОДИТ это изображение")
            else:
                print("   ❌ Запрос с $and НЕ НАХОДИТ это изображение")
                print("   🔍 Проверяем каждое условие отдельно:")

                # Проверяем первое условие
                cond1 = collection.find_one({
                    "_id": img["_id"],
                    "ximilar_objects_structured": {
                        "$elemMatch": {
                            "$or": [
                                {"properties.other_attributes.Subcategory.0.name": "baguette bags"},
                                {"properties.other_attributes.Category.0.name": "baguette bags"}
                            ]
                        }
                    }
                })
                print(f"      Условие 1 (subsubcategory): {'✅ OK' if cond1 else '❌ FAIL'}")

                # Проверяем второе условие
                cond2 = collection.find_one({
                    "_id": img["_id"],
                    "ximilar_objects_structured": {
                        "$elemMatch": {
                            "properties.visual_attributes.Color": {"$elemMatch": {"name": "brown"}}
                        }
                    }
                })
                print(f"      Условие 2 (цвет brown): {'✅ OK' if cond2 else '❌ FAIL'}")

            break

    print("\n" + "=" * 70)
    print("ВЫВОД:")
    print("=" * 70)
    print("Если ТЕСТ 2 находит 0, а ТЕСТ 4 показывает что оба условия работают,")
    print("значит проблема в том, что они ищут в РАЗНЫХ объектах массива.")
    print()
    print("MongoDB $and с $elemMatch требует, чтобы ОБА условия выполнялись")
    print("в ОДНОМ И ТОМ ЖЕ элементе массива ximilar_objects_structured.")

if __name__ == "__main__":
    main()
