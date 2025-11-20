#!/usr/bin/env python3
"""Создание индексов для оптимизации запросов аналитики"""

import os
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()

# Подключение к MongoDB
mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
client = MongoClient(mongodb_uri)
db = client.get_database()
collection = db['images']

print("📊 Создание индексов для оптимизации аналитики...")

# 1. Индекс для фильтрации по основным полям
print("\n1. Создание compound индекса для фильтрации...")
collection.create_index([
    ("hidden", ASCENDING),
    ("is_duplicate", ASCENDING),
    ("ximilar_objects_structured", ASCENDING)
], name="analytics_filter_idx")

# 2. Индекс для временных запросов
print("2. Создание индекса для timestamp...")
collection.create_index([
    ("timestamp", ASCENDING)
], name="timestamp_idx")

# 3. Compound индекс для временной аналитики
print("3. Создание compound индекса для временной аналитики...")
collection.create_index([
    ("hidden", ASCENDING),
    ("is_duplicate", ASCENDING),
    ("timestamp", ASCENDING)
], name="analytics_timeline_idx")

print("\n✅ Индексы созданы!")
print("\n📋 Список всех индексов:")
for index in collection.list_indexes():
    print(f"  - {index['name']}: {index['key']}")

client.close()
