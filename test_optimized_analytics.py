#!/usr/bin/env python3
"""Тестирование оптимизированных функций аналитики"""

import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from optimized_analytics import OptimizedAnalytics

load_dotenv()
load_dotenv('mongodb_config.env')

# Подключение к MongoDB
mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/instagram_gallery')
print(f"Подключение к MongoDB...")

try:
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ Подключение успешно!\n")

    db = client.get_database()
    collection = db['images']

    # Создаем экземпляр оптимизированной аналитики
    analytics = OptimizedAnalytics(collection)

    # Тест 1: Категории
    print("=" * 60)
    print("ТЕСТ 1: Статистика по категориям")
    print("=" * 60)
    categories = analytics.get_categories_stats()
    print(f"Результат: {json.dumps(categories, indent=2, ensure_ascii=False)}\n")

    # Тест 2: Подкатегории
    print("=" * 60)
    print("ТЕСТ 2: Топ-10 подкатегорий")
    print("=" * 60)
    subcategories = analytics.get_subcategories_stats()
    print(f"Результат: {json.dumps(subcategories, indent=2, ensure_ascii=False)}\n")

    # Тест 3: Цвета по категориям
    print("=" * 60)
    print("ТЕСТ 3: Цвета по категориям")
    print("=" * 60)
    colors = analytics.get_colors_by_category()
    for category, items in colors.items():
        print(f"\n{category}: {len(items)} цветов")
        if items:
            print(f"  Топ-3: {items[:3]}")

    # Тест 4: Топ-20 для каждой категории
    print("\n" + "=" * 60)
    print("ТЕСТ 4: Топ-20 популярных вещей")
    print("=" * 60)
    for category in ['Accessories', 'Clothing', 'Footwear']:
        print(f"\n{category}:")
        items = analytics.get_top_items_by_category(category)
        print(f"  Найдено: {len(items)} вещей")
        if items:
            print(f"  Топ-5: {items[:5]}")
        else:
            print("  ⚠️  ПУСТО!")

    print("\n✅ Тестирование завершено!")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
