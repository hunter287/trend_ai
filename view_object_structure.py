#!/usr/bin/env python3
"""
Просмотр объектной структуры данных Ximilar в MongoDB
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
import json

load_dotenv()

def view_object_structure():
    """Просмотр структуры объектов в MongoDB"""
    
    try:
        # Подключение к MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db = client["instagram_gallery"]
        collection = db["images"]
        
        print("🔍 СТРУКТУРА ОБЪЕКТОВ XIMILAR В MONGODB")
        print("=" * 60)
        
        # Находим изображения с тегами Ximilar
        images_with_tags = collection.find({
            "ximilar_objects": {"$exists": True, "$ne": []}
        }).limit(5)
        
        count = 0
        for img in images_with_tags:
            count += 1
            print(f"\n🖼️ Изображение {count}:")
            print(f"   • ID: {img['_id']}")
            print(f"   • URL: {img.get('url', 'N/A')[:50]}...")
            print(f"   • Успех тегирования: {img.get('ximilar_success', False)}")
            print(f"   • Всего тегов: {img.get('ximilar_total_tags', 0)}")
            print(f"   • Всего объектов: {img.get('ximilar_total_objects', 0)}")
            
            # Показываем структуру объектов
            objects = img.get('ximilar_objects', [])
            if objects:
                print(f"\n   📦 ОБЪЕКТЫ ({len(objects)}):")
                for i, obj in enumerate(objects, 1):
                    print(f"      {i}. {obj.get('name', 'N/A')} (ID: {obj.get('object_id', 'N/A')})")
                    print(f"         • Категория: {obj.get('top_category', 'N/A')}")
                    print(f"         • Вероятность: {obj.get('probability', 0):.3f}")
                    print(f"         • Площадь: {obj.get('area', 0):.3f}")
                    
                    # Показываем теги по категориям
                    tags = obj.get('tags', {})
                    if tags:
                        print(f"         • Теги по категориям:")
                        for category, tag_list in tags.items():
                            if tag_list:
                                tag_names = [tag.get('name', '') for tag in tag_list[:3]]
                                print(f"           - {category}: {', '.join(tag_names)}")
                    
                    # Показываем простые теги
                    simple_tags = obj.get('tags_simple', [])
                    if simple_tags:
                        print(f"         • Простые теги: {', '.join(simple_tags[:5])}")
                    
                    # Показываем карту тегов
                    tags_map = obj.get('tags_map', {})
                    if tags_map:
                        print(f"         • Карта тегов:")
                        for key, value in list(tags_map.items())[:3]:
                            print(f"           - {key}: {value}")
                    
                    print()
            else:
                print("   ❌ Объекты не найдены")
            
            print("-" * 50)
        
        if count == 0:
            print("❌ Нет изображений с объектами Ximilar")
        else:
            print(f"\n📊 Найдено {count} изображений с объектами")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def export_object_structure():
    """Экспорт структуры объектов в JSON"""
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["instagram_gallery"]
        collection = db["images"]
        
        # Находим все изображения с объектами
        images = list(collection.find({
            "ximilar_objects": {"$exists": True, "$ne": []}
        }))
        
        # Создаем структуру для экспорта
        export_data = {
            "total_images": len(images),
            "images": []
        }
        
        for img in images:
            image_data = {
                "id": str(img["_id"]),
                "url": img.get("url", ""),
                "total_objects": img.get("ximilar_total_objects", 0),
                "objects": img.get("ximilar_objects", [])
            }
            export_data["images"].append(image_data)
        
        # Сохраняем в файл
        with open("ximilar_objects_structure.json", "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Структура объектов экспортирована в ximilar_objects_structure.json")
        print(f"📊 Экспортировано {len(images)} изображений")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Ошибка экспорта: {e}")

def main():
    """Главная функция"""
    print("🔍 ПРОСМОТР ОБЪЕКТНОЙ СТРУКТУРЫ XIMILAR")
    print("=" * 50)
    
    choice = input("Выберите действие:\n1. Просмотр структуры\n2. Экспорт в JSON\nВвод (1-2): ").strip()
    
    if choice == "1":
        view_object_structure()
    elif choice == "2":
        export_object_structure()
    else:
        print("❌ Неверный выбор")

if __name__ == "__main__":
    main()
