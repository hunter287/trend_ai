#!/usr/bin/env python3
"""Проверка размера коллекции MongoDB"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Подключение к MongoDB
mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
client = MongoClient(mongodb_uri)
db = client.get_database()
collection = db['images']

# Статистика
total_count = collection.count_documents({})
tagged_count = collection.count_documents({
    "ximilar_objects_structured": {"$exists": True, "$ne": []},
    "hidden": {"$ne": True},
    "is_duplicate": {"$ne": True}
})

print(f"📊 Статистика коллекции:")
print(f"  Всего документов: {total_count:,}")
print(f"  С тегами (не скрытые, не дубликаты): {tagged_count:,}")
print(f"  Размер коллекции: {db.command('collstats', 'images')['size'] / 1024 / 1024:.2f} MB")
print(f"\n📋 Существующие индексы:")
for index in collection.list_indexes():
    print(f"  - {index['name']}: {index['key']}")

client.close()
