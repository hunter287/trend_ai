#!/usr/bin/env python3
"""
Проверка структуры хранения цветов в MongoDB
Какое поле правильное: visual_attributes.Color или color_attributes?
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

    # Получаем одно изображение с цветами
    image = collection.find_one({
        'ximilar_objects_structured': {'$exists': True, '$ne': []}
    })

    if not image:
        print("❌ Изображений не найдено")
        return

    print("=" * 70)
    print(f"СТРУКТУРА ДАННЫХ: {image.get('local_filename', 'unknown')}")
    print("=" * 70)
    print()

    for i, obj in enumerate(image.get('ximilar_objects_structured', [])[:3], 1):
        print(f"📦 Объект #{i}:")

        if obj.get('properties'):
            props = obj['properties']

            print("\n  🔍 Проверка полей:")

            # Проверяем visual_attributes
            if 'visual_attributes' in props:
                print(f"    ✅ visual_attributes существует")
                if props['visual_attributes'].get('Color'):
                    colors = props['visual_attributes']['Color']
                    print(f"       Color: {json.dumps(colors[:2], ensure_ascii=False, indent=8)}")
            else:
                print(f"    ❌ visual_attributes НЕ существует")

            # Проверяем color_attributes
            if 'color_attributes' in props:
                print(f"    ✅ color_attributes существует")
                print(f"       Содержимое: {json.dumps(props['color_attributes'], ensure_ascii=False, indent=8)}")
            else:
                print(f"    ❌ color_attributes НЕ существует")

            # Проверяем material_attributes
            if 'material_attributes' in props:
                print(f"    ✅ material_attributes существует")
                if props['material_attributes'].get('Material'):
                    materials = props['material_attributes']['Material']
                    print(f"       Material: {json.dumps(materials[:2], ensure_ascii=False, indent=8)}")
            else:
                print(f"    ❌ material_attributes НЕ существует")

            # Проверяем style_attributes
            if 'style_attributes' in props:
                print(f"    ✅ style_attributes существует")
                if props['style_attributes'].get('Style'):
                    styles = props['style_attributes']['Style']
                    print(f"       Style: {json.dumps(styles[:2], ensure_ascii=False, indent=8)}")
            else:
                print(f"    ❌ style_attributes НЕ существует")

        print()

    print("=" * 70)
    print("ВЫВОД:")
    print("=" * 70)
    print("Правильные названия полей должны использоваться ВЕЗДЕ:")
    print("  • В /api/filter-options (подсчет)")
    print("  • В /api/filtered-images (фильтрация)")

if __name__ == "__main__":
    main()
