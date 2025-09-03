"""
Рабочий пример использования Apify API

Демонстрирует:
1. Подключение к API
2. Получение информации о пользователе
3. Список доступных акторов
4. Запуск актора и получение результатов
"""

import os
import time
import json
from dotenv import load_dotenv
from apify_client import ApifyClient
import pandas as pd

# Загружаем переменные окружения
load_dotenv()

def main():
    """Основная функция демонстрации"""
    
    # Получаем API токен
    api_token = os.getenv('APIFY_API_TOKEN')
    
    if not api_token:
        print("❌ API токен не найден!")
        return
    
    # Создаем клиент
    client = ApifyClient(api_token)
    print("✅ Подключение к Apify API установлено")
    
    # 1. Получаем информацию о пользователе
    print("\n" + "="*50)
    print("👤 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ")
    print("="*50)
    
    try:
        user = client.user().get()
        print(f"📧 Email: {user.get('email', 'N/A')}")
        print(f"🆔 ID: {user.get('id', 'N/A')}")
        print(f"💰 Месячное использование: {user.get('monthlyUsage', {}).get('compute', 0)} единиц")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # 2. Получаем список акторов в Store
    print("\n" + "="*50)
    print("🎭 ПОПУЛЯРНЫЕ АКТОРЫ В APIFY STORE")
    print("="*50)
    
    try:
        # Ищем популярные акторы
        actors = client.actors().list(limit=10)
        print(f"📊 Найдено {len(actors.items)} акторов:")
        
        for i, actor in enumerate(actors.items[:5]):
            print(f"\n{i+1}. 🎭 {actor.get('name', 'N/A')}")
            print(f"   🆔 ID: {actor.get('id', 'N/A')}")
            print(f"   📝 Описание: {(actor.get('description', 'N/A') or 'N/A')[:100]}...")
            print(f"   ⭐ Рейтинг: {actor.get('stats', {}).get('rating', 'N/A')}")
            print(f"   🔄 Использований: {actor.get('stats', {}).get('totalRuns', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # 3. Получаем информацию о конкретном акторе
    print("\n" + "="*50)
    print("🔍 ИНФОРМАЦИЯ О КОНКРЕТНОМ АКТОРЕ")
    print("="*50)
    
    # Популярный актор для веб-скрапинга
    popular_actor_id = "apify/web-scraper"
    
    try:
        actor_info = client.actor(popular_actor_id).get()
        print(f"🎭 Название: {actor_info.get('name', 'N/A')}")
        print(f"📝 Описание: {(actor_info.get('description', 'N/A') or 'N/A')[:200]}...")
        print(f"💰 Цена за 1000 страниц: ${actor_info.get('stats', {}).get('averageComputeUnits', 'N/A')}")
        print(f"🔄 Всего запусков: {actor_info.get('stats', {}).get('totalRuns', 'N/A')}")
    except Exception as e:
        print(f"❌ Ошибка получения информации об акторе: {e}")
    
    # 4. Демонстрируем структуру входных данных
    print("\n" + "="*50)
    print("📋 ПРИМЕР ВХОДНЫХ ДАННЫХ ДЛЯ АКТОРА")
    print("="*50)
    
    try:
        # Получаем схему входных данных для Web Scraper
        input_schema = client.actor(popular_actor_id).get().get('defaultRunOptions', {})
        print("💡 Пример входных данных для Web Scraper:")
        print(json.dumps({
            "urls": [
                {"url": "https://example.com"}
            ],
            "linkSelector": "a[href]",
            "pageFunction": "async function pageFunction(context) {\n    return {\n        title: document.title,\n        url: window.location.href\n    };\n}",
            "maxRequestRetries": 3,
            "maxPagesPerCrawl": 10
        }, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # 5. Демонстрируем как запустить актор (без реального запуска)
    print("\n" + "="*50)
    print("🚀 КАК ЗАПУСТИТЬ АКТОР")
    print("="*50)
    
    print("💡 Для запуска актора используйте:")
    print("""
# Пример запуска актора
input_data = {
    "urls": [{"url": "https://example.com"}],
    "maxPagesPerCrawl": 10
}

# Запуск актора (асинхронный)
run = client.actor('apify/web-scraper').start(input_data)
run_id = run['id']

# Ожидание завершения
while True:
    run_info = client.run(run_id).get()
    if run_info['status'] in ['SUCCEEDED', 'FAILED']:
        break
    time.sleep(10)

# Получение результатов
if run_info['status'] == 'SUCCEEDED':
    dataset_id = run_info['defaultDatasetId']
    items = client.dataset(dataset_id).list_items().items
    print(f"Получено {len(items)} элементов")
""")

    # 6. Получаем список своих запусков
    print("\n" + "="*50)
    print("📈 ВАШИ НЕДАВНИЕ ЗАПУСКИ")
    print("="*50)
    
    try:
        runs = client.runs().list(limit=5)
        if runs.items:
            print(f"📊 Найдено {len(runs.items)} недавних запусков:")
            for i, run in enumerate(runs.items):
                print(f"\n{i+1}. 🏃 Запуск ID: {run.get('id', 'N/A')}")
                print(f"   🎭 Актор: {run.get('actId', 'N/A')}")
                print(f"   📊 Статус: {run.get('status', 'N/A')}")
                print(f"   📅 Дата: {run.get('startedAt', 'N/A')}")
        else:
            print("📭 У вас пока нет запусков")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
