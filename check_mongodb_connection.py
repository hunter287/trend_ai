#!/usr/bin/env python3
"""Проверка подключения к MongoDB и отображение правильного URI"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

print("🔍 Проверка конфигурации MongoDB...\n")

# Загружаем переменные окружения
load_dotenv()
load_dotenv('mongodb_config.env')

# Проверяем разные источники URI
print("📋 Переменные окружения:")
mongodb_uri = os.getenv('MONGODB_URI')
print(f"  MONGODB_URI: {mongodb_uri}")

# Проверяем также файлы конфигурации
config_files = ['.env', 'mongodb_config.env']
for config_file in config_files:
    if os.path.exists(config_file):
        print(f"\n📄 Содержимое {config_file}:")
        with open(config_file, 'r') as f:
            for line in f:
                if 'MONGODB' in line and not line.startswith('#'):
                    print(f"  {line.strip()}")

# Пробуем разные варианты подключения
uris_to_try = [
    mongodb_uri,
    'mongodb://localhost:27017/instagram_gallery',
    'mongodb://127.0.0.1:27017/instagram_gallery',
]

print("\n🔗 Попытка подключения к MongoDB...\n")

for uri in uris_to_try:
    if not uri:
        continue

    # Маскируем пароль для вывода
    display_uri = uri
    if '@' in uri:
        parts = uri.split('@')
        if '://' in parts[0]:
            proto_creds = parts[0].split('://')
            if ':' in proto_creds[1]:
                user = proto_creds[1].split(':')[0]
                display_uri = f"{proto_creds[0]}://{user}:****@{parts[1]}"

    print(f"Пробую: {display_uri}")

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')

        print(f"  ✅ УСПЕШНО!\n")
        print(f"🎯 Правильный URI: {display_uri}")

        # Получаем информацию о БД
        db = client.get_database()
        collection = db['images']

        total_count = collection.count_documents({})
        print(f"\n📊 База данных: {db.name}")
        print(f"   Коллекция: images")
        print(f"   Документов: {total_count:,}")

        print(f"\n💡 Используйте этот URI в скрипте add_analytics_indexes_fixed.py")
        print(f"   или обновите .env файл:\n")
        print(f"   MONGODB_URI=\"{uri}\"")

        client.close()
        break

    except Exception as e:
        print(f"  ❌ Не удалось: {e}\n")
else:
    print("❌ Не удалось подключиться ни к одному из URI")
    print("\nПопробуйте:")
    print("  1. Проверить, запущен ли MongoDB: sudo systemctl status mongod")
    print("  2. Проверить учетные данные")
    print("  3. Проверить настройки firewall")
