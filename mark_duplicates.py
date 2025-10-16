"""
Скрипт для пометки визуальных дубликатов изображений в MongoDB
Использует perceptual hash для определения похожих изображений
"""

import os
import imagehash
from dotenv import load_dotenv
import pymongo
from collections import defaultdict
from tqdm import tqdm
from datetime import datetime

load_dotenv()
load_dotenv('mongodb_config.env')

def find_and_mark_duplicates(threshold: int = 5, dry_run: bool = False):
    """
    Находит и помечает визуальные дубликаты
    
    Args:
        threshold: Пороговое значение Hamming distance (0-10)
                  5 = рекомендуется (находит измененные версии)
        dry_run: Если True, только показывает дубликаты без изменения БД
    """
    print("🔍 ПОИСК И ПОМЕТКА ВИЗУАЛЬНЫХ ДУБЛИКАТОВ")
    print("="*70)
    print(f"⚙️  Threshold: {threshold} (Hamming distance)")
    print(f"⚙️  Dry run: {'Да (только показать)' if dry_run else 'Нет (пометить в БД)'}")
    print("="*70)
    
    # Подключаемся к MongoDB
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
    client = pymongo.MongoClient(mongodb_uri)
    db = client["instagram_gallery"]
    collection = db["images"]
    
    print("✅ Подключение к MongoDB установлено")
    
    # Получаем все изображения с perceptual hash
    images_with_hash = list(collection.find({
        "image_hash": {"$exists": True, "$ne": None}
    }).sort("parsed_at", 1))  # Сортируем по дате добавления
    
    print(f"📊 Найдено {len(images_with_hash)} изображений с perceptual hash")
    
    if len(images_with_hash) == 0:
        print("❌ Нет изображений с perceptual hash!")
        print("💡 Сначала запустите: python add_perceptual_hash_to_existing.py")
        return
    
    # Группируем похожие изображения
    print("\n🔍 Поиск похожих изображений...")
    duplicate_groups = []
    processed_ids = set()
    
    for i, img in enumerate(tqdm(images_with_hash, desc="Анализ изображений")):
        if img["_id"] in processed_ids:
            continue
        
        try:
            current_hash = imagehash.hex_to_hash(img["image_hash"])
        except Exception as e:
            print(f"⚠️  Ошибка парсинга хеша для {img.get('post_id', 'N/A')}: {e}")
            continue
        
        # Ищем похожие изображения
        similar_images = [img]  # Первое изображение - "оригинал"
        processed_ids.add(img["_id"])
        
        for j, other_img in enumerate(images_with_hash[i+1:], start=i+1):
            if other_img["_id"] in processed_ids:
                continue
            
            try:
                other_hash = imagehash.hex_to_hash(other_img["image_hash"])
                distance = current_hash - other_hash
                
                if distance <= threshold:
                    similar_images.append(other_img)
                    processed_ids.add(other_img["_id"])
            except Exception as e:
                continue
        
        # Если найдены дубликаты, добавляем группу
        if len(similar_images) > 1:
            duplicate_groups.append(similar_images)
    
    print(f"\n📊 Найдено {len(duplicate_groups)} групп дубликатов")
    
    if len(duplicate_groups) == 0:
        print("✅ Дубликатов не найдено!")
        return
    
    # Показываем статистику
    total_duplicates = sum(len(group) - 1 for group in duplicate_groups)
    print(f"📊 Всего дубликатов: {total_duplicates}")
    
    # Показываем примеры
    print(f"\n📋 Примеры найденных дубликатов (первые 5 групп):")
    print("-" * 70)
    
    for i, group in enumerate(duplicate_groups[:5]):
        original = group[0]
        duplicates = group[1:]
        
        print(f"\n🔵 Группа {i+1}:")
        print(f"   ОРИГИНАЛ:")
        print(f"      Post ID: {original.get('post_id', 'N/A')}")
        print(f"      Username: @{original.get('username', 'N/A')}")
        print(f"      Likes: {original.get('likes_count', 0)}")
        print(f"      Hash: {original.get('image_hash', 'N/A')}")
        print(f"   ДУБЛИКАТЫ ({len(duplicates)}):")
        
        for dup in duplicates:
            try:
                orig_hash = imagehash.hex_to_hash(original["image_hash"])
                dup_hash = imagehash.hex_to_hash(dup["image_hash"])
                distance = orig_hash - dup_hash
            except:
                distance = "?"
            
            print(f"      • Post ID: {dup.get('post_id', 'N/A')}, "
                  f"Username: @{dup.get('username', 'N/A')}, "
                  f"Distance: {distance}")
    
    if len(duplicate_groups) > 5:
        print(f"\n... и еще {len(duplicate_groups) - 5} групп")
    
    # Помечаем дубликаты в БД
    if not dry_run:
        print(f"\n🏷️  Пометка дубликатов в MongoDB...")
        marked_count = 0
        
        for group in tqdm(duplicate_groups, desc="Пометка дубликатов"):
            original = group[0]
            duplicates = group[1:]
            
            for dup in duplicates:
                try:
                    # Вычисляем расстояние для записи
                    orig_hash = imagehash.hex_to_hash(original["image_hash"])
                    dup_hash = imagehash.hex_to_hash(dup["image_hash"])
                    distance = int(orig_hash - dup_hash)
                except:
                    distance = None
                
                # Помечаем как дубликат
                collection.update_one(
                    {"_id": dup["_id"]},
                    {
                        "$set": {
                            "is_duplicate": True,
                            "duplicate_of": original["_id"],
                            "duplicate_of_post_id": original.get("post_id"),
                            "duplicate_hash_distance": distance,
                            "marked_duplicate_at": datetime.now().isoformat()
                        }
                    }
                )
                marked_count += 1
        
        print(f"✅ Помечено {marked_count} дубликатов в MongoDB")
        
        # Создаем индекс для is_duplicate
        print("🔨 Создание индекса для is_duplicate...")
        collection.create_index("is_duplicate")
        print("✅ Индекс создан!")
    else:
        print(f"\n⚠️  DRY RUN MODE: Изменения в БД не внесены")
        print(f"💡 Запустите без --dry-run для пометки дубликатов")
    
    print(f"\n{'='*70}")
    print(f"✅ ЗАВЕРШЕНО!")
    print(f"📊 Найдено групп дубликатов: {len(duplicate_groups)}")
    print(f"📊 Всего дубликатов: {total_duplicates}")
    if not dry_run:
        print(f"✅ Помечено в БД: {marked_count}")
    print(f"{'='*70}")

def unmark_all_duplicates():
    """Снимает пометку дубликата со всех изображений"""
    print("🔄 СНЯТИЕ ПОМЕТОК ДУБЛИКАТОВ")
    print("="*70)
    
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
    client = pymongo.MongoClient(mongodb_uri)
    db = client["instagram_gallery"]
    collection = db["images"]
    
    print("✅ Подключение к MongoDB установлено")
    
    # Подсчитываем количество помеченных дубликатов
    duplicates_count = collection.count_documents({"is_duplicate": True})
    print(f"📊 Найдено {duplicates_count} помеченных дубликатов")
    
    if duplicates_count == 0:
        print("✅ Нет помеченных дубликатов!")
        return
    
    # Снимаем пометки
    result = collection.update_many(
        {"is_duplicate": True},
        {
            "$set": {"is_duplicate": False},
            "$unset": {
                "duplicate_of": "",
                "duplicate_of_post_id": "",
                "duplicate_hash_distance": "",
                "marked_duplicate_at": ""
            }
        }
    )
    
    print(f"✅ Снято пометок: {result.modified_count}")
    print("="*70)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Поиск и пометка визуальных дубликатов")
    parser.add_argument("--threshold", type=int, default=5, 
                       help="Пороговое значение Hamming distance (0-10, по умолчанию 5)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Только показать дубликаты без изменения БД")
    parser.add_argument("--unmark", action="store_true",
                       help="Снять пометки дубликатов со всех изображений")
    
    args = parser.parse_args()
    
    if args.unmark:
        unmark_all_duplicates()
    else:
        find_and_mark_duplicates(threshold=args.threshold, dry_run=args.dry_run)

