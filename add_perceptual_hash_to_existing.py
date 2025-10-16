"""
Скрипт для добавления perceptual hash к существующим изображениям в MongoDB
"""

import os
import imagehash
from PIL import Image
from pathlib import Path
from dotenv import load_dotenv
import pymongo
from tqdm import tqdm

load_dotenv()
load_dotenv('mongodb_config.env')

def calculate_perceptual_hash(image_path: str) -> str:
    """Вычисление perceptual hash из файла"""
    try:
        image = Image.open(image_path)
        phash = imagehash.phash(image, hash_size=8)
        return str(phash)
    except Exception as e:
        print(f"❌ Ошибка вычисления хеша для {image_path}: {e}")
        return None

def main():
    """Добавляет perceptual hash к существующим изображениям"""
    print("🔢 ДОБАВЛЕНИЕ PERCEPTUAL HASH К СУЩЕСТВУЮЩИМ ИЗОБРАЖЕНИЯМ")
    print("="*70)
    
    # Подключаемся к MongoDB
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
    client = pymongo.MongoClient(mongodb_uri)
    db = client["instagram_gallery"]
    collection = db["images"]
    
    print("✅ Подключение к MongoDB установлено")
    
    # Получаем все изображения без perceptual hash
    images_without_hash = list(collection.find({
        "local_filename": {"$exists": True},
        "image_hash": {"$exists": False}
    }))
    
    print(f"📊 Найдено {len(images_without_hash)} изображений без perceptual hash")
    
    if len(images_without_hash) == 0:
        print("✅ Все изображения уже имеют perceptual hash!")
        return
    
    images_dir = Path("images")
    updated_count = 0
    failed_count = 0
    
    # Обрабатываем каждое изображение
    for img_doc in tqdm(images_without_hash, desc="Обработка изображений"):
        try:
            filename = img_doc.get("local_filename")
            if not filename:
                continue
            
            filepath = images_dir / filename
            
            if not filepath.exists():
                print(f"⚠️  Файл не найден: {filepath}")
                failed_count += 1
                continue
            
            # Вычисляем perceptual hash
            image_hash = calculate_perceptual_hash(str(filepath))
            
            if image_hash:
                # Обновляем документ в MongoDB
                collection.update_one(
                    {"_id": img_doc["_id"]},
                    {"$set": {"image_hash": image_hash}}
                )
                updated_count += 1
            else:
                failed_count += 1
                
        except Exception as e:
            print(f"❌ Ошибка обработки {img_doc.get('local_filename', 'N/A')}: {e}")
            failed_count += 1
    
    print(f"\n{'='*70}")
    print(f"✅ ЗАВЕРШЕНО!")
    print(f"📊 Обработано изображений: {updated_count}")
    print(f"❌ Ошибок: {failed_count}")
    print(f"{'='*70}")
    
    # Создаем индекс для image_hash
    print("🔨 Создание индекса для image_hash...")
    collection.create_index("image_hash")
    print("✅ Индекс создан!")

if __name__ == "__main__":
    main()

