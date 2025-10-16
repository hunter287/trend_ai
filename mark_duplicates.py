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
    
    # Поиск и пометка дубликатов в реальном времени
    print("\n🔍 Поиск и пометка дубликатов...")
    processed_ids = set()
    marked_count = 0
    groups_count = 0
    examples = []  # Храним только первые 5 примеров
    
    for i, img in enumerate(tqdm(images_with_hash, desc="Обработка изображений")):
        if img["_id"] in processed_ids:
            continue
        
        try:
            current_hash = imagehash.hex_to_hash(img["image_hash"])
        except Exception as e:
            print(f"⚠️  Ошибка парсинга хеша для {img.get('post_id', 'N/A')}: {e}")
            continue
        
        # Первое изображение - "оригинал"
        original = img
        processed_ids.add(img["_id"])
        duplicates_in_group = []
        
        # Ищем похожие изображения
        for j, other_img in enumerate(images_with_hash[i+1:], start=i+1):
            if other_img["_id"] in processed_ids:
                continue
            
            try:
                other_hash = imagehash.hex_to_hash(other_img["image_hash"])
                distance = current_hash - other_hash
                
                if distance <= threshold:
                    # НАШЛИ ДУБЛИКАТ - сразу помечаем в БД!
                    if not dry_run:
                        collection.update_one(
                            {"_id": other_img["_id"]},
                            {
                                "$set": {
                                    "is_duplicate": True,
                                    "duplicate_of": original["_id"],
                                    "duplicate_of_post_id": original.get("post_id"),
                                    "duplicate_hash_distance": int(distance),
                                    "marked_duplicate_at": datetime.now().isoformat()
                                }
                            }
                        )
                    
                    duplicates_in_group.append({
                        "img": other_img,
                        "distance": int(distance)
                    })
                    processed_ids.add(other_img["_id"])
                    marked_count += 1
                    
            except Exception as e:
                continue
        
        # Если нашли дубликаты в этой группе
        if len(duplicates_in_group) > 0:
            groups_count += 1
            
            # Сохраняем первые 5 примеров для отчета
            if len(examples) < 5:
                examples.append({
                    "original": original,
                    "duplicates": duplicates_in_group
                })
    
    print(f"\n📊 Обработка завершена!")
    print(f"📊 Найдено групп дубликатов: {groups_count}")
    print(f"📊 Всего дубликатов: {marked_count}")
    
    if marked_count == 0:
        print("✅ Дубликатов не найдено!")
        return
    
    # Показываем примеры найденных дубликатов
    if len(examples) > 0:
        print(f"\n📋 Примеры найденных дубликатов (первые {len(examples)} групп):")
        print("-" * 70)
        
        for i, example in enumerate(examples):
            original = example["original"]
            duplicates = example["duplicates"]
            
            print(f"\n🔵 Группа {i+1}:")
            print(f"   ОРИГИНАЛ:")
            print(f"      Post ID: {original.get('post_id', 'N/A')}")
            print(f"      Username: @{original.get('username', 'N/A')}")
            print(f"      Likes: {original.get('likes_count', 0)}")
            print(f"      Hash: {original.get('image_hash', 'N/A')}")
            print(f"   ДУБЛИКАТЫ ({len(duplicates)}):")
            
            for dup_info in duplicates:
                dup = dup_info["img"]
                distance = dup_info["distance"]
                print(f"      • Post ID: {dup.get('post_id', 'N/A')}, "
                      f"Username: @{dup.get('username', 'N/A')}, "
                      f"Distance: {distance}")
        
        if groups_count > 5:
            print(f"\n... и еще {groups_count - 5} групп")
    
    # Создаем индекс для is_duplicate
    if not dry_run:
        print("\n🔨 Создание индекса для is_duplicate...")
        collection.create_index("is_duplicate")
        print("✅ Индекс создан!")
    else:
        print(f"\n⚠️  DRY RUN MODE: Изменения в БД не внесены")
        print(f"💡 Запустите без --dry-run для пометки дубликатов")
    
    print(f"\n{'='*70}")
    print(f"✅ ЗАВЕРШЕНО!")
    print(f"📊 Найдено групп дубликатов: {groups_count}")
    print(f"📊 Всего дубликатов помечено: {marked_count}")
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

