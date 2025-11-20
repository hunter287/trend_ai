#!/usr/bin/env python3
"""
Отладка структуры данных Ximilar в MongoDB
"""

import os
import pymongo
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
load_dotenv('mongodb_config.env')

def debug_ximilar_structure():
    """Отладка структуры данных Ximilar"""
    try:
        # Подключаемся к MongoDB
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        client = pymongo.MongoClient(mongodb_uri)
        db = client["instagram_gallery"]
        collection = db["images"]
        
        # Находим изображение с объектно-ориентированными тегами
        image = collection.find_one(
            {"ximilar_objects_structured": {"$exists": True, "$ne": []}}
        )
        
        if image:
            print("🔍 СТРУКТУРА ДАННЫХ XIMILAR:")
            print("="*50)
            
            objects = image.get("ximilar_objects_structured", [])
            print(f"📊 Найдено {len(objects)} объектов")
            
            for i, obj in enumerate(objects):
                print(f"\n🏷️ Объект {i+1}:")
                print(f"   • name: {obj.get('name', 'НЕТ')}")
                print(f"   • top_category: {obj.get('top_category', 'НЕТ')}")
                
                if obj.get('properties'):
                    props = obj['properties']
                    print(f"   • properties:")
                    
                    if props.get('basic_info'):
                        basic = props['basic_info']
                        print(f"     - basic_info.name: {basic.get('name', 'НЕТ')}")
                        print(f"     - basic_info.category: {basic.get('category', 'НЕТ')}")
                    
                    if props.get('color_attributes'):
                        print(f"     - color_attributes: {props['color_attributes']}")
                    
                    if props.get('material_attributes'):
                        print(f"     - material_attributes: {props['material_attributes']}")
                    
                    if props.get('visual_attributes'):
                        print(f"     - visual_attributes: {props['visual_attributes']}")
                    
                    if props.get('style_attributes'):
                        print(f"     - style_attributes: {props['style_attributes']}")
                    
                    if props.get('tags_simple'):
                        print(f"     - tags_simple: {props['tags_simple']}")
                    
                    if props.get('tags_map'):
                        print(f"     - tags_map: {props['tags_map']}")
        else:
            print("❌ Не найдено изображений с объектно-ориентированными тегами")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    debug_ximilar_structure()

