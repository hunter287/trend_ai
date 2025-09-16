#!/usr/bin/env python3
"""
Ximilar Fashion API для тегирования одежды в изображениях
"""

import os
import json
import requests
import pymongo
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
load_dotenv('mongodb_config.env')

class XimilarFashionTagger:
    def __init__(self, ximilar_api_key: str, mongodb_uri: str = None):
        """Инициализация теггера"""
        self.ximilar_api_key = ximilar_api_key
        self.mongodb_uri = mongodb_uri or os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:|#!x1K52H.0{8d3@localhost:27017/instagram_gallery')
        self.api_url = "https://api.ximilar.com/tagging/fashion/v2/detect_tags_all"
        self.client = None
        self.db = None
        self.collection = None
        
    def connect_mongodb(self) -> bool:
        """Подключение к MongoDB"""
        try:
            self.client = pymongo.MongoClient(self.mongodb_uri)
            self.db = self.client["instagram_gallery"]
            self.collection = self.db["images"]
            
            # Проверяем подключение
            self.client.admin.command('ping')
            print("✅ Подключение к MongoDB установлено")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к MongoDB: {e}")
            return False
    
    def _categorize_property(self, category: str) -> str:
        """Категоризация свойств по типам"""
        category_lower = category.lower()
        
        # Визуальные атрибуты
        if any(word in category_lower for word in ['color', 'pattern', 'texture', 'shape', 'size', 'length', 'width', 'height']):
            return "visual_attributes"
        
        # Стилевые атрибуты
        elif any(word in category_lower for word in ['style', 'fashion', 'trend', 'design', 'cut', 'fit', 'silhouette']):
            return "style_attributes"
        
        # Цветовые атрибуты
        elif any(word in category_lower for word in ['color', 'hue', 'shade', 'tone', 'brightness']):
            return "color_attributes"
        
        # Материальные атрибуты
        elif any(word in category_lower for word in ['material', 'fabric', 'textile', 'leather', 'cotton', 'silk', 'wool']):
            return "material_attributes"
        
        # Брендовые атрибуты
        elif any(word in category_lower for word in ['brand', 'logo', 'label', 'manufacturer']):
            return "brand_attributes"
        
        # Остальные атрибуты
        else:
            return "other_attributes"
    
    def get_untagged_images(self, limit: int = 100) -> List[Dict]:
        """Получение изображений без тегов Ximilar"""
        try:
            # Ищем изображения без поля ximilar_tags
            query = {
                "full_image_url": {"$exists": True},
                "$or": [
                    {"ximilar_tags": {"$exists": False}},
                    {"ximilar_tags": None},
                    {"ximilar_tags": []}
                ]
            }
            
            images = list(self.collection.find(query).limit(limit))
            print(f"📊 Найдено {len(images)} изображений без тегов Ximilar")
            return images
            
        except Exception as e:
            print(f"❌ Ошибка получения изображений: {e}")
            return []
    
    def tag_image_with_ximilar(self, image_url: str, max_retries: int = 3) -> Optional[Dict]:
        """Тегирование одного изображения через Ximilar API с retry"""
        headers = {
            "Authorization": f"Token {self.ximilar_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "records": [
                {
                    "_id": "1",
                    "_url": image_url
                }
            ]
        }
        
        print(f"🏷️ Тегирование: {image_url[:50]}...")
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"   🔄 Попытка {attempt + 1}/{max_retries}")
                    import time
                    time.sleep(2)  # Пауза между попытками
                
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=60  # Увеличиваем timeout до 60 секунд
                )
            
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("records") and len(result["records"]) > 0:
                        record = result["records"][0]
                        
                        # Извлекаем объекты с их тегами (объектно-ориентированная структура)
                        objects = []
                        if record.get("_objects"):
                            for obj in record["_objects"]:
                                object_data = {
                                    "object_id": obj.get("id", ""),
                                    "name": obj.get("name", ""),
                                    "top_category": obj.get("Top Category", ""),
                                    "bound_box": obj.get("bound_box", []),
                                    "probability": obj.get("prob", 0.0),
                                    "area": obj.get("area", 0.0),
                                    "properties": {
                                        "basic_info": {
                                            "name": obj.get("name", ""),
                                            "category": obj.get("Top Category", ""),
                                            "confidence": obj.get("prob", 0.0),
                                            "area": obj.get("area", 0.0)
                                        },
                                        "visual_attributes": {},
                                        "style_attributes": {},
                                        "color_attributes": {},
                                        "material_attributes": {},
                                        "brand_attributes": {},
                                        "other_attributes": {}
                                    },
                                    "tags_simple": [],
                                    "tags_map": {}
                                }
                                
                                # Извлекаем теги объекта и группируем по типам свойств
                                if obj.get("_tags"):
                                    obj_tags = obj["_tags"]
                                    
                                    # Простые теги
                                    if obj_tags.get("_tags_simple"):
                                        object_data["tags_simple"] = obj_tags["_tags_simple"]
                                    
                                    # Карта тегов
                                    if obj_tags.get("_tags_map"):
                                        object_data["tags_map"] = obj_tags["_tags_map"]
                                    
                                    # Группируем теги по типам свойств
                                    for category, tag_list in obj_tags.items():
                                        if category not in ["_tags_simple", "_tags_map"] and isinstance(tag_list, list):
                                            # Определяем тип свойства по категории
                                            property_type = self._categorize_property(category)
                                            
                                            if property_type not in object_data["properties"]:
                                                object_data["properties"][property_type] = {}
                                            
                                            object_data["properties"][property_type][category] = []
                                            for tag in tag_list:
                                                if isinstance(tag, dict):
                                                    tag_data = {
                                                        "name": tag.get("name", ""),
                                                        "confidence": tag.get("prob", 0.0),
                                                        "id": tag.get("id", ""),
                                                        "category": category
                                                    }
                                                    object_data["properties"][property_type][category].append(tag_data)
                                
                                objects.append(object_data)
                        
                        # Создаем плоский список тегов для обратной совместимости
                        tags = []
                        for obj in objects:
                            for property_type, properties in obj["properties"].items():
                                if isinstance(properties, dict):
                                    for category, tag_list in properties.items():
                                        if isinstance(tag_list, list):
                                            for tag in tag_list:
                                                tags.append({
                                                    "name": tag["name"],
                                                    "confidence": tag["confidence"],
                                                    "category": category,
                                                    "property_type": property_type,
                                                    "object_id": obj["object_id"],
                                                    "object_name": obj["name"]
                                                })
                        
                        return {
                            "success": True,
                            "tags": tags,
                            "objects": objects,
                            "total_tags": len(tags),
                            "total_objects": len(objects),
                            "api_response": result
                        }
                    else:
                        return {
                            "success": False,
                            "error": "No tags returned",
                            "api_response": result
                        }
                else:
                    if attempt == max_retries - 1:  # Последняя попытка
                        return {
                            "success": False,
                            "error": f"HTTP {response.status_code}: {response.text}",
                            "api_response": None
                        }
                    else:
                        print(f"   ⚠️ HTTP {response.status_code}, повторяем...")
                        continue
                        
            except Exception as e:
                if attempt == max_retries - 1:  # Последняя попытка
                    return {
                        "success": False,
                        "error": str(e),
                        "api_response": None
                    }
                else:
                    print(f"   ⚠️ Ошибка: {str(e)[:50]}..., повторяем...")
                    continue
        
        # Если все попытки исчерпаны
        return {
            "success": False,
            "error": f"Все {max_retries} попыток исчерпаны",
            "api_response": None
        }
    
    def update_image_with_tags(self, image_id: str, tags_data: Dict) -> bool:
        """Обновление изображения в MongoDB с тегами (объектно-ориентированная структура)"""
        try:
            update_data = {
                # Новая объектно-ориентированная структура
                "ximilar_objects_structured": tags_data.get("objects", []),
                "ximilar_properties_summary": self._create_properties_summary(tags_data.get("objects", [])),
                
                # Обратная совместимость
                "ximilar_tags": tags_data.get("tags", []),
                "ximilar_objects": tags_data.get("objects", []),
                "ximilar_total_tags": tags_data.get("total_tags", 0),
                "ximilar_total_objects": tags_data.get("total_objects", 0),
                "ximilar_tagged_at": datetime.now().isoformat(),
                "ximilar_success": tags_data.get("success", False)
            }
            
            if not tags_data.get("success"):
                update_data["ximilar_error"] = tags_data.get("error", "Unknown error")
            
            result = self.collection.update_one(
                {"_id": image_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                print(f"✅ Обновлено изображение {image_id} с объектно-ориентированной структурой")
                return True
            else:
                print(f"❌ Не удалось обновить изображение {image_id}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка обновления изображения {image_id}: {e}")
            return False
    
    def _create_properties_summary(self, objects: List[Dict]) -> Dict:
        """Создание сводки по свойствам объектов"""
        summary = {
            "total_objects": len(objects),
            "property_types": {},
            "most_common_properties": {},
            "objects_by_category": {}
        }
        
        for obj in objects:
            # Группируем по категориям
            category = obj.get("top_category", "unknown")
            if category not in summary["objects_by_category"]:
                summary["objects_by_category"][category] = 0
            summary["objects_by_category"][category] += 1
            
            # Анализируем свойства
            properties = obj.get("properties", {})
            for property_type, property_data in properties.items():
                if isinstance(property_data, dict):
                    if property_type not in summary["property_types"]:
                        summary["property_types"][property_type] = 0
                    summary["property_types"][property_type] += len(property_data)
        
        return summary
    
    def tag_batch_images(self, batch_size: int = 10, max_images: int = 100):
        """Тегирование пакета изображений"""
        print(f"🏷️ ЗАПУСК ТЕГИРОВАНИЯ ЧЕРЕЗ XIMILAR")
        print("="*50)
        
        if not self.connect_mongodb():
            return False
        
        # Получаем изображения для тегирования
        images = self.get_untagged_images(max_images)
        if not images:
            print("❌ Нет изображений для тегирования")
            return False
        
        print(f"📊 Будет обработано {len(images)} изображений")
        
        success_count = 0
        error_count = 0
        
        for i, image in enumerate(images, 1):
            try:
                image_id = image["_id"]
                image_url = image.get("full_image_url")
                
                if not image_url:
                    print(f"⚠️ [{i}/{len(images)}] Пропущено: нет URL")
                    continue
                
                print(f"\n🔄 [{i}/{len(images)}] Обработка изображения...")
                print(f"   • ID: {image_id}")
                print(f"   • URL: {image_url[:60]}...")
                
                # Тегируем изображение
                tags_result = self.tag_image_with_ximilar(image_url)
                
                if tags_result:
                    # Обновляем в MongoDB
                    if self.update_image_with_tags(image_id, tags_result):
                        success_count += 1
                        
                        if tags_result.get("success"):
                            tags_count = tags_result.get("total_tags", 0)
                            print(f"   ✅ Успешно: {tags_count} тегов")
                            
                            # Показываем топ-3 тега
                            if tags_result.get("tags"):
                                top_tags = sorted(
                                    tags_result["tags"], 
                                    key=lambda x: x.get("confidence", 0), 
                                    reverse=True
                                )[:3]
                                
                                print(f"   🏷️ Топ теги:")
                                for tag in top_tags:
                                    name = tag.get("name", "N/A")
                                    confidence = tag.get("confidence", 0)
                                    print(f"      • {name} ({confidence:.2f})")
                        else:
                            print(f"   ❌ Ошибка API: {tags_result.get('error', 'Unknown')}")
                            error_count += 1
                    else:
                        error_count += 1
                else:
                    print(f"   ❌ Не удалось получить теги")
                    error_count += 1
                
                # Небольшая пауза между запросами
                if i % 5 == 0:
                    print(f"   ⏸️ Пауза 2 секунды...")
                    import time
                    time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Ошибка обработки: {e}")
                error_count += 1
        
        # Итоговая статистика
        print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
        print("="*30)
        print(f"✅ Успешно обработано: {success_count}")
        print(f"❌ Ошибок: {error_count}")
        print(f"📈 Успешность: {success_count/(success_count+error_count)*100:.1f}%")
        
        return success_count > 0
    
    def get_tagged_images_stats(self):
        """Статистика по тегированным изображениям"""
        try:
            if not self.connect_mongodb():
                return
            
            # Общая статистика
            total_images = self.collection.count_documents({})
            tagged_images = self.collection.count_documents({"ximilar_tags": {"$exists": True, "$ne": []}})
            untagged_images = total_images - tagged_images
            
            print(f"\n📊 СТАТИСТИКА ТЕГИРОВАНИЯ:")
            print("="*30)
            print(f"📸 Всего изображений: {total_images}")
            print(f"🏷️ С тегами: {tagged_images}")
            print(f"❓ Без тегов: {untagged_images}")
            print(f"📈 Процент тегированных: {tagged_images/total_images*100:.1f}%")
            
            # Топ теги
            pipeline = [
                {"$match": {"ximilar_tags": {"$exists": True, "$ne": []}}},
                {"$unwind": "$ximilar_tags"},
                {"$group": {
                    "_id": "$ximilar_tags.name",
                    "count": {"$sum": 1},
                    "avg_confidence": {"$avg": "$ximilar_tags.confidence"}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            
            top_tags = list(self.collection.aggregate(pipeline))
            
            if top_tags:
                print(f"\n🏷️ ТОП-10 ТЕГОВ:")
                print("-" * 30)
                for i, tag in enumerate(top_tags, 1):
                    name = tag["_id"]
                    count = tag["count"]
                    avg_conf = tag["avg_confidence"]
                    print(f"{i:2d}. {name:<20} ({count} раз, {avg_conf:.2f})")
            
        except Exception as e:
            print(f"❌ Ошибка получения статистики: {e}")
    
    def show_object_structure(self, image_id: str = None):
        """Показать структуру объекта для конкретного изображения"""
        try:
            if not self.connect_mongodb():
                return
            
            if image_id:
                # Показать конкретное изображение
                image = self.collection.find_one({"_id": image_id})
                if not image:
                    print(f"❌ Изображение {image_id} не найдено")
                    return
                
                print(f"\n🔍 СТРУКТУРА ОБЪЕКТОВ ДЛЯ ИЗОБРАЖЕНИЯ {image_id}")
                print("="*60)
                
                if "ximilar_objects_structured" in image:
                    for i, obj in enumerate(image["ximilar_objects_structured"], 1):
                        print(f"\n📦 ОБЪЕКТ {i}: {obj.get('name', 'Unknown')}")
                        print(f"   Категория: {obj.get('top_category', 'Unknown')}")
                        print(f"   Уверенность: {obj.get('probability', 0):.2f}")
                        print(f"   Область: {obj.get('bound_box', [])}")
                        
                        properties = obj.get("properties", {})
                        for prop_type, prop_data in properties.items():
                            if isinstance(prop_data, dict) and prop_data:
                                print(f"   {prop_type.upper()}:")
                                for category, tags in prop_data.items():
                                    if isinstance(tags, list) and tags:
                                        print(f"     {category}: {[tag.get('name', '') for tag in tags]}")
                else:
                    print("❌ Нет объектно-ориентированных данных для этого изображения")
            else:
                # Показать пример структуры
                image = self.collection.find_one({"ximilar_objects_structured": {"$exists": True, "$ne": []}})
                if image:
                    self.show_object_structure(str(image["_id"]))
                else:
                    print("❌ Нет изображений с объектно-ориентированными данными")
                    
        except Exception as e:
            print(f"❌ Ошибка показа структуры: {e}")

def main():
    """Главная функция"""
    print("🏷️ XIMILAR FASHION TAGGING")
    print("="*40)
    
    # Получаем API ключ
    ximilar_api_key = os.getenv("XIMILAR_API_KEY")
    if not ximilar_api_key:
        print("❌ Не найден XIMILAR_API_KEY в переменных окружения")
        print("💡 Добавьте в .env файл: XIMILAR_API_KEY=your_key")
        return
    
    # Создаем теггер
    tagger = XimilarFashionTagger(ximilar_api_key)
    
    # Показываем статистику
    tagger.get_tagged_images_stats()
    
    # Спрашиваем пользователя
    print(f"\n🤔 Что хотите сделать?")
    print("1. Тегировать новые изображения")
    print("2. Показать статистику")
    print("3. Показать структуру объектов")
    print("4. Выход")
    
    choice = input("\nВыберите (1-4): ").strip()
    
    if choice == "1":
        try:
            max_images = int(input("Максимум изображений (Enter для 50): ") or "50")
            batch_size = int(input("Размер пакета (Enter для 10): ") or "10")
            
            tagger.tag_batch_images(batch_size, max_images)
        except ValueError:
            print("❌ Введите корректное число")
    elif choice == "2":
        tagger.get_tagged_images_stats()
    elif choice == "3":
        image_id = input("ID изображения (Enter для примера): ").strip()
        tagger.show_object_structure(image_id if image_id else None)
    else:
        print("👋 До свидания!")

if __name__ == "__main__":
    main()
