"""
Правильное использование Instagram скрапера

Этот скрипт показывает, как правильно использовать Instagram скрапер
согласно его предназначению и документации
"""

import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient
import pandas as pd

load_dotenv()

def get_actor_info(client, actor_id):
    """Получает подробную информацию об акторе"""
    
    print(f"🔍 ИНФОРМАЦИЯ ОБ АКТОРЕ {actor_id}")
    print("="*50)
    
    try:
        actor_info = client.actor(actor_id).get()
        
        print(f"🎭 Название: {actor_info.get('name', 'N/A')}")
        print(f"📝 Описание: {actor_info.get('description', 'N/A')}")
        
        # Получаем схему входных данных
        input_schema = actor_info.get('inputSchema', {})
        if input_schema:
            print(f"\n📋 СХЕМА ВХОДНЫХ ДАННЫХ:")
            print("-" * 30)
            
            # Показываем основные поля
            properties = input_schema.get('properties', {})
            for field_name, field_info in list(properties.items())[:10]:
                required = "🔴 ОБЯЗАТЕЛЬНО" if field_name in input_schema.get('required', []) else "🟢 Опционально"
                description = field_info.get('description', 'Нет описания')
                print(f"   {field_name}: {description} ({required})")
        
        return actor_info
        
    except Exception as e:
        print(f"❌ Ошибка получения информации об акторе: {e}")
        return None

def run_instagram_scraper_properly():
    """Запускает Instagram скрапер правильно"""
    
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    print("✅ Подключение к Apify API установлено")
    
    # ID Instagram скрапера
    actor_id = "shu8hvrXbJbY3Eb9W"
    
    # Получаем информацию об акторе
    actor_info = get_actor_info(client, actor_id)
    
    # Правильные входные данные для Instagram скрапера
    input_data = {
        "addParentData": False,
        "resultsType": "details",
        "resultsLimit": 20,
        "searchType": "user",  # Ищем по пользователю, а не по хештегу
        "searchQueries": ["instagram"],  # Публичный аккаунт Instagram
        "maxRequestRetries": 3,
        "maxConcurrency": 1
    }
    
    print(f"\n🎯 ЗАПУСК INSTAGRAM СКРАПЕРА (ПРАВИЛЬНО)")
    print("="*60)
    print(f"🔍 Тип поиска: {input_data['searchType']}")
    print(f"🔍 Поисковые запросы: {input_data['searchQueries']}")
    print(f"📊 Максимум результатов: {input_data['resultsLimit']}")
    
    try:
        # Запускаем актор
        print(f"\n🚀 Запускаем актор {actor_id}...")
        run = client.actor(actor_id).call(run_input=input_data)
        run_id = run['id']
        print(f"✅ Актор запущен с ID: {run_id}")
        
        # Ждем завершения
        print(f"\n⏳ Ожидаем завершения...")
        timeout = 600  # 10 минут
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            run_info = client.run(run_id).get()
            status = run_info.get('status')
            
            # Показываем прогресс
            if status == 'RUNNING':
                print(f"🏃 Статус: {status} - Актор работает...")
            elif status == 'READY':
                print(f"⏳ Статус: {status} - Актор готовится...")
            else:
                print(f"📊 Статус: {status}")
            
            if status == 'SUCCEEDED':
                print("✅ Скрапинг завершен успешно!")
                break
            elif status in ['FAILED', 'ABORTED']:
                print(f"❌ Скрапинг завершен с ошибкой: {status}")
                return None
            
            time.sleep(15)  # Ждем 15 секунд между проверками
        else:
            print("⏰ Таймаут - останавливаем актор")
            client.run(run_id).abort()
            return None
        
        # Получаем результаты
        dataset_id = run_info.get('defaultDatasetId')
        if not dataset_id:
            print("❌ Dataset ID не найден")
            return None
        
        print(f"\n📊 Получаем результаты из датасета {dataset_id}...")
        
        # Получаем информацию о датасете
        dataset_info = client.dataset(dataset_id).get()
        total_items = dataset_info.get('itemCount', 0)
        print(f"📈 Всего элементов в датасете: {total_items}")
        
        # Получаем все элементы
        dataset_items = client.dataset(dataset_id).list_items()
        items = dataset_items.items
        
        print(f"✅ Получено {len(items)} элементов")
        
        if items:
            # Показываем структуру данных
            print(f"\n📋 СТРУКТУРА ДАННЫХ:")
            print("="*50)
            
            first_item = items[0]
            if isinstance(first_item, dict):
                print("🔑 Доступные поля:")
                for key in list(first_item.keys())[:15]:  # Первые 15 полей
                    print(f"   • {key}")
            
            # Показываем первые результаты
            print(f"\n📋 ПЕРВЫЕ РЕЗУЛЬТАТЫ:")
            print("="*50)
            
            for i, item in enumerate(items[:3]):  # Показываем первые 3
                print(f"\n{i+1}. 📸 Элемент:")
                
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
                    
                    # Хештеги
                    if 'hashtags' in item and item['hashtags']:
                        hashtags = item['hashtags'][:5]  # Первые 5 хештегов
                        print(f"   🏷️ Хештеги: {', '.join(hashtags)}")
                    
                    # Дата
                    if 'timestamp' in item:
                        timestamp = item.get('timestamp', 'N/A')
                        print(f"   📅 Дата: {timestamp}")
                else:
                    print(f"   {str(item)[:200]}...")
            
            # Сохраняем результаты
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON файл
            json_filename = f"instagram_proper_results_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"\n💾 JSON сохранен: {json_filename}")
            
            # CSV файл (если возможно)
            try:
                df = pd.DataFrame(items)
                csv_filename = f"instagram_proper_results_{timestamp}.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8')
                print(f"💾 CSV сохранен: {csv_filename}")
            except Exception as e:
                print(f"⚠️ Ошибка при сохранении CSV: {e}")
            
            # Статистика
            print(f"\n📊 СТАТИСТИКА РЕЗУЛЬТАТОВ:")
            print("="*30)
            print(f"📈 Всего элементов: {len(items)}")
            
            # Подсчитываем статистику
            if items and isinstance(items[0], dict):
                total_likes = sum(item.get('likesCount', 0) for item in items if item.get('likesCount'))
                total_comments = sum(item.get('commentsCount', 0) for item in items if item.get('commentsCount'))
                unique_users = len(set(item.get('ownerUsername', '') for item in items if item.get('ownerUsername')))
                
                print(f"❤️ Общее количество лайков: {total_likes}")
                print(f"💬 Общее количество комментариев: {total_comments}")
                print(f"👥 Уникальных пользователей: {unique_users}")
        
        return items
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def try_different_search_types():
    """Пробует разные типы поиска для Instagram скрапера"""
    
    print(f"\n🔍 ПОПРОБУЕМ РАЗНЫЕ ТИПЫ ПОИСКА")
    print("="*50)
    
    # Типы поиска, которые поддерживает Instagram скрапер
    search_types = [
        {
            "name": "Поиск по пользователю",
            "searchType": "user",
            "searchQueries": ["instagram", "nike"]
        },
        {
            "name": "Поиск по хештегу",
            "searchType": "hashtag", 
            "searchQueries": ["python", "coding"]
        },
        {
            "name": "Поиск по месту",
            "searchType": "place",
            "searchQueries": ["moscow", "london"]
        },
        {
            "name": "Поиск по комментарию",
            "searchType": "comment",
            "searchQueries": ["python", "programming"]
        }
    ]
    
    for search_type in search_types:
        print(f"\n🎯 {search_type['name']}:")
        print(f"   Тип: {search_type['searchType']}")
        print(f"   Запросы: {search_type['searchQueries']}")
        print(f"   💡 Для тестирования используйте этот тип поиска")

if __name__ == "__main__":
    print("📸 INSTAGRAM СКРАПЕР - ПРАВИЛЬНОЕ ИСПОЛЬЗОВАНИЕ")
    print("="*70)
    
    # Показываем разные типы поиска
    try_different_search_types()
    
    # Запускаем скрапер правильно
    results = run_instagram_scraper_properly()
    
    if results:
        print(f"\n🎉 Скрапинг завершен! Получено {len(results)} результатов")
    else:
        print("\n❌ Скрапинг не удался")
        print("\n💡 Возможные причины:")
        print("   • Instagram блокирует скрапинг")
        print("   • Нужны другие параметры")
        print("   • Попробуйте другой тип поиска")
