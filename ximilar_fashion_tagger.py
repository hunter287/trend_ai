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

class XimilarFashionTagger:
    def __init__(self, ximilar_api_key: str, mongodb_uri: str = "mongodb://localhost:27017/"):
        """Инициализация теггера"""
        self.ximilar_api_key = ximilar_api_key
        self.mongodb_uri = mongodb_uri
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
                        
                        # Извлекаем теги
                        tags = []
                        if record.get("_tags"):
                            for tag in record["_tags"]:
                                if isinstance(tag, dict):
                                    tags.append({
                                        "name": tag.get("name", ""),
                                        "confidence": tag.get("confidence", 0.0),
                                        "category": tag.get("category", ""),
                                        "subcategory": tag.get("subcategory", "")
                                    })
                        
                        return {
                            "success": True,
                            "tags": tags,
                            "total_tags": len(tags),
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
        """Обновление изображения в MongoDB с тегами"""
        try:
            update_data = {
                "ximilar_tags": tags_data.get("tags", []),
                "ximilar_total_tags": tags_data.get("total_tags", 0),
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
                print(f"✅ Обновлено изображение {image_id}")
                return True
            else:
                print(f"❌ Не удалось обновить изображение {image_id}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка обновления изображения {image_id}: {e}")
            return False
    
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
    print("3. Выход")
    
    choice = input("\nВыберите (1-3): ").strip()
    
    if choice == "1":
        try:
            max_images = int(input("Максимум изображений (Enter для 50): ") or "50")
            batch_size = int(input("Размер пакета (Enter для 10): ") or "10")
            
            tagger.tag_batch_images(batch_size, max_images)
        except ValueError:
            print("❌ Введите корректное число")
    elif choice == "2":
        tagger.get_tagged_images_stats()
    else:
        print("👋 До свидания!")

if __name__ == "__main__":
    main()
