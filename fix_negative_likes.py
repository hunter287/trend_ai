"""
Скрипт для исправления отрицательных значений likes_count в MongoDB
Instagram иногда скрывает лайки, и Apify возвращает -1
"""

import os
from dotenv import load_dotenv
import pymongo

load_dotenv()
load_dotenv('mongodb_config.env')

def fix_negative_likes():
    """Исправляет отрицательные значения likes_count на 0"""
    print("🔧 ИСПРАВЛЕНИЕ ОТРИЦАТЕЛЬНЫХ ЗНАЧЕНИЙ ЛАЙКОВ")
    print("="*70)
    
    # Подключаемся к MongoDB
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
    client = pymongo.MongoClient(mongodb_uri)
    db = client["instagram_gallery"]
    collection = db["images"]
    
    print("✅ Подключение к MongoDB установлено")
    
    # Находим документы с отрицательными значениями
    negative_likes = collection.count_documents({"likes_count": {"$lt": 0}})
    negative_comments = collection.count_documents({"comments_count": {"$lt": 0}})
    
    print(f"📊 Найдено изображений с отрицательными лайками: {negative_likes}")
    print(f"📊 Найдено изображений с отрицательными комментариями: {negative_comments}")
    
    if negative_likes == 0 and negative_comments == 0:
        print("✅ Отрицательных значений не найдено!")
        return
    
    # Исправляем likes_count
    if negative_likes > 0:
        print("\n🔧 Исправление likes_count...")
        result = collection.update_many(
            {"likes_count": {"$lt": 0}},
            {"$set": {"likes_count": 0}}
        )
        print(f"✅ Обновлено likes_count: {result.modified_count} документов")
    
    # Исправляем comments_count
    if negative_comments > 0:
        print("\n🔧 Исправление comments_count...")
        result = collection.update_many(
            {"comments_count": {"$lt": 0}},
            {"$set": {"comments_count": 0}}
        )
        print(f"✅ Обновлено comments_count: {result.modified_count} документов")
    
    print(f"\n{'='*70}")
    print("✅ ЗАВЕРШЕНО!")
    print(f"{'='*70}")

if __name__ == "__main__":
    fix_negative_likes()

