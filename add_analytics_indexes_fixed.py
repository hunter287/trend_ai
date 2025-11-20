#!/usr/bin/env python3
"""Создание индексов для оптимизации запросов аналитики"""

import os
import sys
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
load_dotenv('mongodb_config.env')

# Пробуем получить URI из разных источников
mongodb_uri = os.getenv('MONGODB_URI')

# Если нет в .env, спрашиваем у пользователя
if not mongodb_uri or 'trend_ai_user' in mongodb_uri:
    print("⚠️  MONGODB_URI не найден или использует старые учетные данные")
    print("\nВведите правильный MongoDB URI (или нажмите Enter для использования локального MongoDB):")
    print("Пример: mongodb://username:password@localhost:27017/instagram_gallery")
    user_input = input("MongoDB URI: ").strip()

    if user_input:
        mongodb_uri = user_input
    else:
        # По умолчанию используем локальный MongoDB без аутентификации
        mongodb_uri = 'mongodb://localhost:27017/instagram_gallery'
        print(f"\n📌 Используем URI по умолчанию: {mongodb_uri}")

print(f"\n🔗 Подключение к MongoDB...")
print(f"URI: {mongodb_uri.split('@')[1] if '@' in mongodb_uri else mongodb_uri}")

try:
    # Подключение к MongoDB с таймаутом
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)

    # Проверяем подключение
    client.admin.command('ping')
    print("✅ Подключение успешно!")

    db = client.get_database()
    collection = db['images']

    print("\n📊 Создание индексов для оптимизации аналитики...")

    # 1. Индекс для фильтрации по основным полям
    print("\n1. Создание compound индекса для фильтрации...")
    try:
        collection.create_index([
            ("hidden", ASCENDING),
            ("is_duplicate", ASCENDING),
            ("ximilar_objects_structured", ASCENDING)
        ], name="analytics_filter_idx", background=True)
        print("   ✅ analytics_filter_idx создан")
    except Exception as e:
        if 'already exists' in str(e):
            print("   ⚠️  Индекс уже существует")
        else:
            print(f"   ❌ Ошибка: {e}")

    # 2. Индекс для временных запросов
    print("\n2. Создание индекса для timestamp...")
    try:
        collection.create_index([
            ("timestamp", ASCENDING)
        ], name="timestamp_idx", background=True)
        print("   ✅ timestamp_idx создан")
    except Exception as e:
        if 'already exists' in str(e):
            print("   ⚠️  Индекс уже существует")
        else:
            print(f"   ❌ Ошибка: {e}")

    # 3. Compound индекс для временной аналитики
    print("\n3. Создание compound индекса для временной аналитики...")
    try:
        collection.create_index([
            ("hidden", ASCENDING),
            ("is_duplicate", ASCENDING),
            ("timestamp", ASCENDING)
        ], name="analytics_timeline_idx", background=True)
        print("   ✅ analytics_timeline_idx создан")
    except Exception as e:
        if 'already exists' in str(e):
            print("   ⚠️  Индекс уже существует")
        else:
            print(f"   ❌ Ошибка: {e}")

    print("\n✅ Индексы созданы!")
    print("\n📋 Список всех индексов:")
    for index in collection.list_indexes():
        print(f"  - {index['name']}: {index['key']}")

    # Статистика коллекции
    print("\n📊 Статистика коллекции:")
    total_count = collection.count_documents({})
    tagged_count = collection.count_documents({
        "ximilar_objects_structured": {"$exists": True, "$ne": []},
        "hidden": {"$ne": True},
        "is_duplicate": {"$ne": True}
    })
    print(f"  Всего документов: {total_count:,}")
    print(f"  С тегами (не скрытые, не дубликаты): {tagged_count:,}")

    client.close()
    print("\n✅ Готово!")

except Exception as e:
    print(f"\n❌ Ошибка подключения к MongoDB: {e}")
    print("\nПроверьте:")
    print("  1. MongoDB запущен и доступен")
    print("  2. Правильность URI подключения")
    print("  3. Учетные данные (логин/пароль)")
    sys.exit(1)
