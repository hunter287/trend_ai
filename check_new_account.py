"""
Проверка нового аккаунта Apify и поиск рабочего актора для @linda.sza
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

def check_new_account():
    """Проверяет новый аккаунт Apify"""
    
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    print("✅ Подключение к новому аккаунту Apify API установлено")
    
    # Получаем информацию о пользователе
    print(f"\n👤 ИНФОРМАЦИЯ О НОВОМ ПОЛЬЗОВАТЕЛЕ")
    print("="*50)
    
    try:
        user = client.user().get()
        print(f"📧 Email: {user.get('email', 'N/A')}")
        print(f"🆔 ID: {user.get('id', 'N/A')}")
        print(f"💰 Месячное использование: {user.get('monthlyUsage', {}).get('compute', 0)} единиц")
    except Exception as e:
        print(f"❌ Ошибка получения информации о пользователе: {e}")
        return None
    
    # Получаем список акторов
    print(f"\n🎭 АКТОРЫ В НОВОМ АККАУНТЕ")
    print("="*40)
    
    try:
        actors = client.actors().list(limit=20)
        print(f"📊 Найдено {len(actors.items)} акторов:")
        
        for i, actor in enumerate(actors.items):
            print(f"\n{i+1}. 🎭 {actor.get('name', 'N/A')}")
            print(f"   🆔 ID: {actor.get('id', 'N/A')}")
            print(f"   📝 Описание: {(actor.get('description', 'N/A') or 'N/A')[:100]}...")
            print(f"   👤 Автор: {actor.get('username', 'N/A')}")
            print(f"   📅 Создан: {actor.get('createdAt', 'N/A')}")
            
            # Статистика
            stats = actor.get('stats', {})
            print(f"   🏃 Запусков: {stats.get('totalRuns', 0)}")
            
            # Проверяем, есть ли успешные запуски
            try:
                runs = client.actor(actor['id']).runs().list(limit=5)
                successful_runs = [run for run in runs.items if run.get('status') == 'SUCCEEDED']
                if successful_runs:
                    print(f"   ✅ Успешных запусков: {len(successful_runs)}")
                    
                    # Проверяем, есть ли запуски с данными
                    for run in successful_runs[:2]:
                        if run.get('defaultDatasetId'):
                            try:
                                dataset = client.dataset(run['defaultDatasetId'])
                                item_count = dataset.get().get('itemCount', 0)
                                if item_count > 0:
                                    print(f"   📊 Последний успешный запуск: {item_count} элементов")
                                    break
                            except:
                                pass
                else:
                    print(f"   ❌ Успешных запусков: 0")
            except Exception as e:
                print(f"   ❌ Ошибка получения запусков: {e}")
        
        return actors.items
        
    except Exception as e:
        print(f"❌ Ошибка получения списка акторов: {e}")
        return []

def find_linda_sza_actor(actors):
    """Ищет актор, который работал с @linda.sza"""
    
    print(f"\n🔍 ПОИСК АКТОРА ДЛЯ @linda.sza")
    print("="*40)
    
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    linda_actors = []
    
    for actor in actors:
        actor_id = actor.get('id')
        actor_name = actor.get('name', 'N/A')
        
        print(f"\n🔍 Проверяем актор: {actor_name} ({actor_id})")
        
        try:
            # Получаем последние запуски
            runs = client.actor(actor_id).runs().list(limit=10)
            
            for run in runs.items:
                if run.get('status') == 'SUCCEEDED':
                    # Проверяем входные данные
                    input_data = run.get('options', {}).get('input', {})
                    search_queries = input_data.get('searchQueries', [])
                    
                    # Ищем упоминания linda.sza
                    for query in search_queries:
                        if isinstance(query, str) and 'linda.sza' in query.lower():
                            print(f"   ✅ Найден запуск с @linda.sza!")
                            print(f"   🆔 Run ID: {run.get('id')}")
                            print(f"   📅 Дата: {run.get('startedAt')}")
                            
                            # Проверяем результаты
                            dataset_id = run.get('defaultDatasetId')
                            if dataset_id:
                                try:
                                    dataset = client.dataset(dataset_id)
                                    item_count = dataset.get().get('itemCount', 0)
                                    print(f"   📊 Результатов: {item_count}")
                                    
                                    if item_count > 0:
                                        linda_actors.append({
                                            'actor_id': actor_id,
                                            'actor_name': actor_name,
                                            'run_id': run.get('id'),
                                            'dataset_id': dataset_id,
                                            'item_count': item_count,
                                            'started_at': run.get('startedAt')
                                        })
                                except Exception as e:
                                    print(f"   ❌ Ошибка получения результатов: {e}")
                            break
        except Exception as e:
            print(f"   ❌ Ошибка проверки актора: {e}")
    
    return linda_actors

def get_data_from_linda_actor(linda_actor):
    """Получает данные из найденного актора для @linda.sza"""
    
    print(f"\n📊 ПОЛУЧЕНИЕ ДАННЫХ ИЗ АКТОРА {linda_actor['actor_name']}")
    print("="*60)
    
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    
    try:
        dataset_id = linda_actor['dataset_id']
        print(f"📊 Получаем данные из датасета {dataset_id}...")
        
        # Получаем информацию о датасете
        dataset_info = client.dataset(dataset_id).get()
        total_items = dataset_info.get('itemCount', 0)
        print(f"📈 Всего элементов в датасете: {total_items}")
        
        # Получаем все элементы
        dataset_items = client.dataset(dataset_id).list_items()
        items = dataset_items.items
        
        print(f"✅ Получено {len(items)} элементов")
        
        if items:
            # Показываем первые результаты
            print(f"\n📋 ПЕРВЫЕ РЕЗУЛЬТАТЫ:")
            print("="*50)
            
            for i, item in enumerate(items[:3]):  # Показываем первые 3
                print(f"\n{i+1}. 📸 Пост:")
                
                if isinstance(item, dict):
                    # Основная информация
                    if 'shortCode' in item:
                        print(f"   🔗 Код: {item.get('shortCode', 'N/A')}")
                    if 'url' in item:
                        print(f"   🌐 URL: {item.get('url', 'N/A')}")
                    if 'type' in item:
                        print(f"   📝 Тип: {item.get('type', 'N/A')}")
                    
                    # Информация о пользователе
                    if 'ownerUsername' in item:
                        print(f"   👤 Пользователь: @{item.get('ownerUsername', 'N/A')}")
                    if 'ownerFullName' in item:
                        print(f"   📛 Полное имя: {item.get('ownerFullName', 'N/A')}")
                    
                    # Статистика
                    if 'likesCount' in item:
                        print(f"   ❤️ Лайки: {item.get('likesCount', 'N/A')}")
                    if 'commentsCount' in item:
                        print(f"   💬 Комментарии: {item.get('commentsCount', 'N/A')}")
                    
                    # Текст поста
                    if 'caption' in item and item['caption']:
                        caption = item['caption']
                        if len(caption) > 100:
                            caption = caption[:100] + "..."
                        print(f"   📝 Текст: {caption}")
                    
                    # Дата
                    if 'timestamp' in item:
                        timestamp = item.get('timestamp', 'N/A')
                        print(f"   📅 Дата: {timestamp}")
            
            # Сохраняем результаты
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON файл
            json_filename = f"linda_sza_new_account_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"\n💾 JSON сохранен: {json_filename}")
            
            # Статистика
            print(f"\n📊 СТАТИСТИКА ДАННЫХ:")
            print("="*30)
            print(f"📈 Всего постов: {len(items)}")
            
            # Подсчитываем статистику
            if items and isinstance(items[0], dict):
                total_likes = sum(item.get('likesCount', 0) for item in items if item.get('likesCount'))
                total_comments = sum(item.get('commentsCount', 0) for item in items if item.get('commentsCount'))
                unique_users = len(set(item.get('ownerUsername', '') for item in items if item.get('ownerUsername')))
                
                print(f"❤️ Общее количество лайков: {total_likes:,}")
                print(f"💬 Общее количество комментариев: {total_comments:,}")
                print(f"👥 Уникальных пользователей: {unique_users}")
        
        return items
        
    except Exception as e:
        print(f"❌ Ошибка получения данных: {e}")
        return None

if __name__ == "__main__":
    print("🔍 ПРОВЕРКА НОВОГО АККАУНТА APIFY")
    print("="*50)
    
    # Проверяем новый аккаунт
    actors = check_new_account()
    
    if actors:
        # Ищем актор для @linda.sza
        linda_actors = find_linda_sza_actor(actors)
        
        if linda_actors:
            print(f"\n🎉 Найдено {len(linda_actors)} акторов с данными @linda.sza!")
            
            # Берем первый найденный актор
            best_actor = linda_actors[0]
            print(f"\n📊 Используем актор: {best_actor['actor_name']}")
            print(f"   🆔 ID: {best_actor['actor_id']}")
            print(f"   📊 Элементов: {best_actor['item_count']}")
            print(f"   📅 Дата: {best_actor['started_at']}")
            
            # Получаем данные
            data = get_data_from_linda_actor(best_actor)
            
            if data:
                print(f"\n🎉 Успешно получены данные @linda.sza из нового аккаунта!")
            else:
                print(f"\n❌ Не удалось получить данные")
        else:
            print(f"\n❌ Акторы с данными @linda.sza не найдены")
    else:
        print(f"\n❌ Не удалось получить список акторов")
