#!/usr/bin/env python3
"""
Поиск всех вариантов написания bathrobes в базе
"""

import os
import pymongo
from dotenv import load_dotenv

load_dotenv()
load_dotenv('mongodb_config.env')

def main():
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
    client = pymongo.MongoClient(mongodb_uri)
    db = client['instagram_gallery']
    collection = db['images']

    print("=" * 70)
    print("ПОИСК ВСЕХ ВАРИАНТОВ 'bathrobe' В БАЗЕ")
    print("=" * 70)

    # Получаем все изображения с тегами
    images = list(collection.find(
        {
            "local_filename": {"$exists": True},
            "hidden": {"$ne": True},
            "ximilar_objects_structured": {"$exists": True, "$ne": []}
        },
        {"local_filename": 1, "ximilar_objects_structured": 1}
    ))

    print(f"\n📊 Всего изображений для анализа: {len(images)}")

    # Ищем все варианты, содержащие "bathrobe" (case-insensitive)
    bathrobe_variants = set()
    bathrobe_images = []

    for img in images:
        found_bathrobe = False
        bathrobe_objects = []

        for obj in img.get('ximilar_objects_structured', []):
            if obj.get('properties', {}).get('other_attributes'):
                other_attrs = obj['properties']['other_attributes']

                # Проверяем Subcategory
                if other_attrs.get('Subcategory'):
                    for subcat in other_attrs['Subcategory']:
                        name = subcat.get('name', '')
                        if 'bathrobe' in name.lower():
                            bathrobe_variants.add(name)
                            bathrobe_objects.append(f"Subcategory: {name}")
                            found_bathrobe = True

                # Проверяем Category
                if other_attrs.get('Category'):
                    for cat in other_attrs['Category']:
                        name = cat.get('name', '')
                        if 'bathrobe' in name.lower():
                            bathrobe_variants.add(name)
                            bathrobe_objects.append(f"Category: {name}")
                            found_bathrobe = True

        if found_bathrobe:
            bathrobe_images.append({
                'filename': img['local_filename'],
                'objects': bathrobe_objects,
                'obj_data': img['ximilar_objects_structured']
            })

    print(f"\n✅ Найдено изображений с 'bathrobe': {len(bathrobe_images)}")
    print(f"✅ Найдено вариантов написания: {len(bathrobe_variants)}")
    print()

    print("🔍 ВАРИАНТЫ НАПИСАНИЯ:")
    for variant in sorted(bathrobe_variants):
        print(f"  • '{variant}'")
    print()

    print("=" * 70)
    print("ДЕТАЛИ ИЗОБРАЖЕНИЙ:")
    print("=" * 70)

    for i, img_data in enumerate(bathrobe_images, 1):
        print(f"\n{i}. {img_data['filename']}")
        print(f"   Найденные объекты:")
        for obj in img_data['objects']:
            print(f"     • {obj}")

        # Проверяем, на какой позиции bathrobe в Subcategory
        for obj in img_data['obj_data']:
            if obj.get('properties', {}).get('other_attributes'):
                other_attrs = obj['properties']['other_attributes']

                if other_attrs.get('Subcategory'):
                    subcat_list = other_attrs['Subcategory']
                    for idx, subcat in enumerate(subcat_list):
                        name = subcat.get('name', '')
                        if 'bathrobe' in name.lower():
                            print(f"     → Позиция в Subcategory: [{idx}] (используем только [0]={subcat_list[0].get('name', '')})")

                            # Проверяем цвет этого объекта
                            colors = obj.get('properties', {}).get('visual_attributes', {}).get('Color', [])
                            if colors:
                                color_names = [c['name'] for c in colors]
                                print(f"     → Цвета объекта: {', '.join(color_names)}")

    print("\n" + "=" * 70)
    print("ВЫВОД:")
    print("=" * 70)
    print("Если bathrobe находится НЕ на позиции [0] в Subcategory,")
    print("наша логика (Subcategory.0.name) его НЕ НАЙДЕТ!")
    print()
    print("Пример:")
    print("  Subcategory: ['dress', 'bathrobe']  ← bathrobe на позиции [1]")
    print("  Мы берем: Subcategory[0] = 'dress' ← НЕ НАХОДИМ bathrobe!")

if __name__ == "__main__":
    main()
