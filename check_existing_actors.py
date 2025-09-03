#!/usr/bin/env python3
"""
Проверка существующих акторов Apify и их данных
"""

import os
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

def check_existing_actors():
    """Проверка существующих акторов и их данных"""
    
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        print("❌ APIFY_API_TOKEN не найден в .env")
        return
    
    client = ApifyClient(api_token)
    
    print("🔍 ПРОВЕРКА СУЩЕСТВУЮЩИХ АКТОРОВ APIFY")
    print("=" * 60)
    
    try:
        # Получаем список акторов пользователя
        print("📋 Ваши акторы:")
        actors = client.actors().list()
        
        for actor in actors.items:
            print(f"   • {actor.name} (ID: {actor.id})")
            print(f"     - Статус: {actor.stats.get('runs', 0)} запусков")
            print(f"     - Последний запуск: {actor.stats.get('lastRunStartedAt', 'N/A')}")
            print()
        
        # Получаем список запусков
        print("🚀 Последние запуски:")
        runs = client.runs().list(limit=10)
        
        for run in runs.items:
            print(f"   • Актор: {run.actorId}")
            print(f"     - Статус: {run.status}")
            print(f"     - Запущен: {run.startedAt}")
            print(f"     - Завершен: {run.finishedAt}")
            print(f"     - ID запуска: {run.id}")
            
            # Проверяем есть ли данные
            if run.status == "SUCCEEDED":
                try:
                    dataset = client.dataset(run.defaultDatasetId)
                    items = dataset.list_items(limit=5)
                    print(f"     - Данных в датасете: {items.total} элементов")
                    
                    if items.items:
                        print(f"     - Пример данных:")
                        for i, item in enumerate(items.items[:2]):
                            print(f"       {i+1}. {list(item.keys())}")
                except Exception as e:
                    print(f"     - Ошибка получения данных: {e}")
            
            print()
        
        # Проверяем конкретные датасеты
        print("📊 Проверка датасетов:")
        datasets = client.datasets().list(limit=10)
        
        for dataset in datasets.items:
            print(f"   • Датасет: {dataset.name}")
            print(f"     - ID: {dataset.id}")
            print(f"     - Элементов: {dataset.itemCount}")
            print(f"     - Создан: {dataset.createdAt}")
            
            if dataset.itemCount > 0:
                try:
                    items = dataset.list_items(limit=3)
                    print(f"     - Примеры данных:")
                    for i, item in enumerate(items.items):
                        print(f"       {i+1}. Ключи: {list(item.keys())}")
                        if 'url' in item:
                            print(f"          URL: {item['url'][:50]}...")
                        if 'imageUrl' in item:
                            print(f"          Image: {item['imageUrl'][:50]}...")
                        if 'caption' in item:
                            print(f"          Caption: {item['caption'][:50]}...")
                except Exception as e:
                    print(f"     - Ошибка: {e}")
            
            print()
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_existing_actors()
