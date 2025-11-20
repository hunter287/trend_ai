#!/usr/bin/env python3
"""
Простая проверка акторов в Apify
"""

from apify_client import ApifyClient
from dotenv import load_dotenv
import os

load_dotenv()

def check_actors():
    """Проверяет доступные акторы"""
    try:
        client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
        
        print("🔍 Проверяем акторы в вашем аккаунте...")
        
        # Получаем информацию о пользователе
        user_info = client.user().get()
        print(f"👤 Пользователь: {user_info.get('username', 'N/A')}")
        print(f"📧 Email: {user_info.get('email', 'N/A')}")
        
        # Получаем список акторов пользователя
        print(f"\n📋 ВАШИ АКТОРЫ:")
        print("="*50)
        
        actors = client.actors().list()
        if actors.items:
            for i, actor in enumerate(actors.items, 1):
                print(f"\n{i}. 🎭 Актор:")
                print(f"   • ID: {actor.get('id', 'N/A')}")
                print(f"   • Имя: {actor.get('name', 'N/A')}")
                print(f"   • Статус: {'Публичный' if actor.get('isPublic') else 'Приватный'}")
                print(f"   • Запусков: {actor.get('stats', {}).get('totalRuns', 0)}")
                print(f"   • Успешных: {actor.get('stats', {}).get('successfulRuns', 0)}")
                print(f"   • Неудачных: {actor.get('stats', {}).get('failedRuns', 0)}")
        else:
            print("❌ У вас нет собственных акторов")
        
        # Проверяем конкретные Instagram акторы
        print(f"\n📸 ПРОВЕРКА INSTAGRAM АКТОРОВ:")
        print("="*40)
        
        instagram_actors = [
            "apify/instagram-scraper",
            "shu8hvrXbJbY3Eb9W",  # Ваш актор
            "apify/instagram-hashtag-scraper",
            "apify/instagram-profile-scraper"
        ]
        
        for actor_id in instagram_actors:
            try:
                actor_info = client.actor(actor_id).get()
                print(f"\n✅ {actor_id}:")
                print(f"   • Имя: {actor_info.get('name', 'N/A')}")
                print(f"   • Статус: {'Публичный' if actor_info.get('isPublic') else 'Приватный'}")
                print(f"   • Запусков: {actor_info.get('stats', {}).get('totalRuns', 0)}")
                print(f"   • Успешных: {actor_info.get('stats', {}).get('successfulRuns', 0)}")
                
                # Проверяем схему входных данных
                if actor_info.get('inputSchema'):
                    schema = actor_info['inputSchema']
                    if schema.get('properties'):
                        params = list(schema['properties'].keys())[:5]
                        print(f"   • Параметры: {params}...")
                
            except Exception as e:
                print(f"❌ {actor_id}: Недоступен - {str(e)[:50]}...")
        
        # Проверяем последние запуски
        print(f"\n📊 ПОСЛЕДНИЕ ЗАПУСКИ:")
        print("="*25)
        
        runs = client.runs().list(limit=5)
        if runs.items:
            for i, run in enumerate(runs.items, 1):
                print(f"\n{i}. 🏃 Запуск:")
                print(f"   • ID: {run.get('id', 'N/A')}")
                print(f"   • Актор: {run.get('actorId', 'N/A')}")
                print(f"   • Статус: {run.get('status', 'N/A')}")
                print(f"   • Создан: {run.get('createdAt', 'N/A')}")
                
                # Время выполнения
                if run.get('startedAt') and run.get('finishedAt'):
                    import datetime
                    try:
                        start = datetime.datetime.fromisoformat(run['startedAt'].replace('Z', '+00:00'))
                        end = datetime.datetime.fromisoformat(run['finishedAt'].replace('Z', '+00:00'))
                        duration = (end - start).total_seconds()
                        print(f"   • Время выполнения: {duration:.1f} секунд")
                    except:
                        print(f"   • Время выполнения: Неизвестно")
        else:
            print("❌ Нет запусков")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = check_actors()
    if success:
        print(f"\n🎉 Проверка завершена!")
    else:
        print(f"\n💥 Проверка не удалась")















