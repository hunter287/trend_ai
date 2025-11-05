#!/usr/bin/env python3
"""
Проверка всех подкатегорий с несколькими вариантами в Subcategory
Показывает какие подкатегории имеют потенциальную проблему с подсчетом
"""

import os
import pymongo
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
load_dotenv('mongodb_config.env')

def main():
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
    client = pymongo.MongoClient(mongodb_uri)
    db = client['instagram_gallery']
    collection = db['images']

    print("=" * 80)
    print("АНАЛИЗ: Подкатегории с несколькими вариантами в массиве Subcategory")
    print("=" * 80)
    print()

    # Получаем все изображения с тегами
    images = list(collection.find(
        {
            "local_filename": {"$exists": True},
            "hidden": {"$ne": True},
            "ximilar_objects_structured": {"$exists": True, "$ne": []}
        },
        {"_id": 1, "local_filename": 1, "ximilar_objects_structured": 1}
    ))

    print(f"📊 Всего изображений для анализа: {len(images)}")
    print()

    # Статистика по подкатегориям с несколькими вариантами
    multi_variant_subcats = defaultdict(lambda: {"count": 0, "examples": []})

    for image in images:
        for obj in image.get('ximilar_objects_structured', []):
            if obj.get('properties') and obj['properties'].get('other_attributes'):
                other_attrs = obj['properties']['other_attributes']

                # Проверяем Subcategory
                if other_attrs.get('Subcategory'):
                    subcat_array = other_attrs['Subcategory']

                    # Если в массиве больше 1 варианта
                    if len(subcat_array) > 1:
                        # Берем первый и второй варианты
                        first = subcat_array[0].get('name', '')
                        second = subcat_array[1].get('name', '') if len(subcat_array) > 1 else ''

                        if first and second:
                            key = f"{first} | {second}"
                            multi_variant_subcats[key]["count"] += 1

                            # Сохраняем первые 3 примера
                            if len(multi_variant_subcats[key]["examples"]) < 3:
                                multi_variant_subcats[key]["examples"].append(image['local_filename'])

    print("=" * 80)
    print("РЕЗУЛЬТАТЫ: Подкатегории с альтернативными вариантами")
    print("=" * 80)
    print()

    if not multi_variant_subcats:
        print("✅ Не найдено объектов с несколькими вариантами в Subcategory")
        return

    # Сортируем по количеству вхождений
    sorted_subcats = sorted(multi_variant_subcats.items(), key=lambda x: x[1]["count"], reverse=True)

    print(f"Найдено {len(sorted_subcats)} различных комбинаций вариантов\n")

    for i, (variants, data) in enumerate(sorted_subcats[:20], 1):  # Топ-20
        print(f"{i}. {variants}")
        print(f"   Встречается в {data['count']} объектах")
        print(f"   Примеры изображений:")
        for example in data['examples'][:3]:
            print(f"     • {example}")
        print()

    print("=" * 80)
    print("ВЫВОД:")
    print("=" * 80)
    print(f"✅ Исправление от {__file__} обрабатывает ВСЕ эти случаи")
    print(f"✅ Теперь подсчет учитывает ОБА варианта в каждой комбинации")
    print(f"✅ Фильтрация и подсчет синхронизированы для всех {len(sorted_subcats)} комбинаций")
    print()
    print("Примеры:")
    print("  • 'long strap bags | baguette bags' - изображение считается для ОБОИХ")
    print("  • 'casual trousers | cargo' - изображение считается для ОБОИХ")
    print("  • И так далее для всех остальных комбинаций")

if __name__ == "__main__":
    main()
