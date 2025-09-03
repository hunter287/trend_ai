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
            print(f"   • {actor.get('name', 'N/A')} (ID: {actor.get('id', 'N/A')})")
            stats = actor.get('stats', {})
            print(f"     - Статус: {stats.get('runs', 0)} запусков")
            print(f"     - Последний запуск: {stats.get('lastRunStartedAt', 'N/A')}")
            print()
        
        # Получаем список запусков
        print("🚀 Последние запуски:")
        runs = client.runs().list(limit=10)
        
        for run in runs.items:
            print(f"   • Актор: {run.get('actorId', 'N/A')}")
            print(f"     - Статус: {run.get('status', 'N/A')}")
            print(f"     - Запущен: {run.get('startedAt', 'N/A')}")
            print(f"     - Завершен: {run.get('finishedAt', 'N/A')}")
            print(f"     - ID запуска: {run.get('id', 'N/A')}")
            
            # Проверяем есть ли данные
            if run.get('status') == "SUCCEEDED":
                try:
                    dataset_id = run.get('defaultDatasetId')
                    if dataset_id:
                        dataset = client.dataset(dataset_id)
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
            print(f"   • Датасет: {dataset.get('name', 'N/A')}")
            print(f"     - ID: {dataset.get('id', 'N/A')}")
            print(f"     - Элементов: {dataset.get('itemCount', 0)}")
            print(f"     - Создан: {dataset.get('createdAt', 'N/A')}")
            
            if dataset.get('itemCount', 0) > 0:
                try:
                    dataset_client = client.dataset(dataset.get('id'))
                    items = dataset_client.list_items(limit=3)
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
