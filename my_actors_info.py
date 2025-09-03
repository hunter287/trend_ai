"""
Анализ ваших акторов в Apify

Этот скрипт покажет:
1. Какие акторы у вас есть
2. Что они делают
3. Как часто используются
4. Результаты последних запусков
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

def analyze_actor(client, actor_id):
    """Анализирует конкретный актор"""
    
    print(f"\n🔍 АНАЛИЗ АКТОРА: {actor_id}")
    print("="*60)
    
    try:
        # Получаем информацию об акторе
        actor_info = client.actor(actor_id).get()
        
        print(f"🎭 Название: {actor_info.get('name', 'N/A')}")
        print(f"📝 Описание: {(actor_info.get('description', 'N/A') or 'Нет описания')[:200]}...")
        print(f"🏷️ Теги: {', '.join(actor_info.get('taggedTemplateIds', []))}")
        print(f"👤 Автор: {actor_info.get('username', 'N/A')}")
        print(f"📅 Создан: {actor_info.get('createdAt', 'N/A')}")
        print(f"🔄 Обновлен: {actor_info.get('modifiedAt', 'N/A')}")
        
        # Статистика
        stats = actor_info.get('stats', {})
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   🏃 Всего запусков: {stats.get('totalRuns', 0)}")
        print(f"   ⭐ Рейтинг: {stats.get('rating', 'N/A')}")
        print(f"   💰 Средняя стоимость: {stats.get('averageComputeUnits', 'N/A')} единиц")
        
        # Последние запуски этого актора
        print(f"\n📈 ПОСЛЕДНИЕ ЗАПУСКИ:")
        runs = client.actor(actor_id).runs().list(limit=5)
        
        if runs.items:
            for i, run in enumerate(runs.items):
                status_emoji = {
                    'SUCCEEDED': '✅',
                    'FAILED': '❌', 
                    'ABORTED': '⚠️',
                    'RUNNING': '🏃',
                    'READY': '⏳'
                }.get(run.get('status', ''), '❓')
                
                print(f"   {i+1}. {status_emoji} {run.get('status', 'N/A')} - {run.get('startedAt', 'N/A')}")
                
                # Если запуск успешен, показываем количество результатов
                if run.get('status') == 'SUCCEEDED' and run.get('defaultDatasetId'):
                    try:
                        dataset = client.dataset(run['defaultDatasetId'])
                        item_count = dataset.get().get('itemCount', 0)
                        print(f"      📊 Результатов: {item_count}")
                    except:
                        print(f"      📊 Результатов: не удалось получить")
        else:
            print("   📭 Нет запусков")
            
        return actor_info
        
    except Exception as e:
        print(f"❌ Ошибка анализа актора: {e}")
        return None

def analyze_recent_runs(client):
    """Анализирует последние запуски"""
    
    print(f"\n🏃 ВАШИ ПОСЛЕДНИЕ ЗАПУСКИ")
    print("="*60)
    
    try:
        runs = client.runs().list(limit=10)
        
        if not runs.items:
            print("📭 У вас нет запусков")
            return
        
        for i, run in enumerate(runs.items):
            status_emoji = {
                'SUCCEEDED': '✅',
                'FAILED': '❌', 
                'ABORTED': '⚠️',
                'RUNNING': '🏃',
                'READY': '⏳'
            }.get(run.get('status', ''), '❓')
            
            print(f"\n{i+1}. {status_emoji} Запуск ID: {run.get('id', 'N/A')}")
            print(f"   🎭 Актор: {run.get('actId', 'N/A')}")
            print(f"   📊 Статус: {run.get('status', 'N/A')}")
            print(f"   📅 Начат: {run.get('startedAt', 'N/A')}")
            print(f"   ⏱️ Завершен: {run.get('finishedAt', 'N/A')}")
            
            # Показываем входные данные (первые несколько полей)
            if run.get('options', {}).get('input'):
                input_data = run['options']['input']
                print(f"   📝 Входные данные:")
                for key, value in list(input_data.items())[:3]:
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"      {key}: {value}")
            
            # Результаты
            if run.get('status') == 'SUCCEEDED' and run.get('defaultDatasetId'):
                try:
                    dataset = client.dataset(run['defaultDatasetId'])
                    item_count = dataset.get().get('itemCount', 0)
                    print(f"   📊 Результатов: {item_count}")
                except:
                    pass
                    
    except Exception as e:
        print(f"❌ Ошибка анализа запусков: {e}")

def get_dataset_sample(client, dataset_id, limit=3):
    """Получает образец данных из датасета"""
    
    try:
        items = client.dataset(dataset_id).list_items(limit=limit).items
        
        if items:
            print(f"\n📋 ОБРАЗЕЦ ДАННЫХ (первые {len(items)} элементов):")
            print("-" * 40)
            
            for i, item in enumerate(items):
                print(f"\n{i+1}. Элемент:")
                if isinstance(item, dict):
                    # Показываем ключи и значения
                    for key, value in list(item.items())[:5]:  # Первые 5 полей
                        if isinstance(value, str) and len(value) > 100:
                            value = value[:100] + "..."
                        print(f"   {key}: {value}")
                else:
                    print(f"   {str(item)[:200]}...")
        else:
            print("\n📋 Датасет пуст")
            
    except Exception as e:
        print(f"❌ Ошибка получения данных: {e}")

def main():
    """Основная функция"""
    
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    print("🔬 АНАЛИЗ ВАШИХ АКТОРОВ И ЗАПУСКОВ")
    print("="*60)
    
    # Анализируем последние запуски
    analyze_recent_runs(client)
    
    # Получаем уникальные акторы из запусков
    print(f"\n🎭 АНАЛИЗ ИСПОЛЬЗУЕМЫХ АКТОРОВ")
    print("="*60)
    
    try:
        runs = client.runs().list(limit=20)
        unique_actors = set()
        
        for run in runs.items:
            if run.get('actId'):
                unique_actors.add(run['actId'])
        
        print(f"📊 Найдено {len(unique_actors)} уникальных акторов:")
        
        for actor_id in unique_actors:
            analyze_actor(client, actor_id)
            
            # Показываем образец данных из последнего успешного запуска
            actor_runs = client.actor(actor_id).runs().list(limit=5)
            for run in actor_runs.items:
                if run.get('status') == 'SUCCEEDED' and run.get('defaultDatasetId'):
                    print(f"\n📊 ПОСЛЕДНИЕ РЕЗУЛЬТАТЫ из запуска {run['id']}:")
                    get_dataset_sample(client, run['defaultDatasetId'])
                    break
            
            print("\n" + "="*60)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
