#!/usr/bin/env python3
"""
Проверка доступных акторов в Apify аккаунте
"""

from apify_client import ApifyClient
from dotenv import load_dotenv
import os
import json

load_dotenv()

def check_my_actors():
    """Проверяет доступные акторы в аккаунте"""
    try:
        client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
        
        print("🔍 Проверяем доступные акторы в вашем аккаунте...")
        
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
                print(f"   • Версия: {actor.get('versionNumber', 'N/A')}")
                print(f"   • Статус: {actor.get('isPublic', 'Private')}")
                print(f"   • Создан: {actor.get('createdAt', 'N/A')}")
                print(f"   • Обновлен: {actor.get('modifiedAt', 'N/A')}")
                
                # Описание
                if actor.get('description'):
                    desc = actor['description'][:100] + "..." if len(actor['description']) > 100 else actor['description']
                    print(f"   • Описание: {desc}")
                
                # Статистика запусков
                if actor.get('stats'):
                    stats = actor['stats']
                    print(f"   • Запусков: {stats.get('totalRuns', 0)}")
                    print(f"   • Успешных: {stats.get('successfulRuns', 0)}")
                    print(f"   • Неудачных: {stats.get('failedRuns', 0)}")
        else:
            print("❌ У вас нет собственных акторов")
        
        # Получаем список публичных акторов (популярные)
        print(f"\n🌐 ПОПУЛЯРНЫЕ ПУБЛИЧНЫЕ АКТОРЫ:")
        print("="*50)
        
        public_actors = client.actors().list(limit=10, isPublic=True)
        if public_actors.items:
            for i, actor in enumerate(public_actors.items, 1):
                print(f"\n{i}. 🌍 Публичный актор:")
                print(f"   • ID: {actor.get('id', 'N/A')}")
                print(f"   • Имя: {actor.get('name', 'N/A')}")
                print(f"   • Автор: {actor.get('username', 'N/A')}")
                print(f"   • Запусков: {actor.get('stats', {}).get('totalRuns', 0)}")
                
                # Описание
                if actor.get('description'):
                    desc = actor['description'][:80] + "..." if len(actor['description']) > 80 else actor['description']
                    print(f"   • Описание: {desc}")
        else:
            print("❌ Не удалось получить список публичных акторов")
        
        # Проверяем конкретные Instagram акторы
        print(f"\n📸 INSTAGRAM АКТОРЫ:")
        print("="*30)
        
        instagram_actors = [
            "apify/instagram-scraper",
            "shu8hvrXbJbY3Eb9W",
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
                
                # Проверяем схему входных данных
                if actor_info.get('inputSchema'):
                    schema = actor_info['inputSchema']
                    if schema.get('properties'):
                        print(f"   • Параметры: {list(schema['properties'].keys())[:5]}...")
                
            except Exception as e:
                print(f"❌ {actor_id}: Недоступен ({e})")
        
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
                print(f"   • Завершен: {run.get('finishedAt', 'N/A')}")
                
                # Время выполнения
                if run.get('startedAt') and run.get('finishedAt'):
                    import datetime
                    start = datetime.datetime.fromisoformat(run['startedAt'].replace('Z', '+00:00'))
                    end = datetime.datetime.fromisoformat(run['finishedAt'].replace('Z', '+00:00'))
                    duration = (end - start).total_seconds()
                    print(f"   • Время выполнения: {duration:.1f} секунд")
        else:
            print("❌ Нет запусков")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_my_actors()
    if success:
        print(f"\n🎉 Проверка завершена успешно!")
    else:
        print(f"\n💥 Проверка не удалась")









