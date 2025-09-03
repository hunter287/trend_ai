"""
Правильный запуск Instagram скрапера с конкретными URL профилей
"""

import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient
import pandas as pd

load_dotenv()

def run_instagram_with_urls():
    """Запускает Instagram скрапер с конкретными URL профилей"""
    
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    print("✅ Подключение к Apify API установлено")
    
    # ID Instagram скрапера
    actor_id = "shu8hvrXbJbY3Eb9W"
    
    # Правильные входные данные - конкретные URL профилей
    input_data = {
        "addParentData": False,
        "resultsType": "details",
        "resultsLimit": 50,
        "searchType": "user",
        "searchQueries": [
            "https://www.instagram.com/instagram/",  # Официальный аккаунт Instagram
            "https://www.instagram.com/nike/"        # Nike - публичный аккаунт
        ],
        "maxRequestRetries": 3,
        "maxConcurrency": 1
    }
    
    print(f"\n🎯 ЗАПУСК INSTAGRAM СКРАПЕРА С КОНКРЕТНЫМИ URL")
    print("="*60)
    print(f"🔍 URL профилей для скрапинга:")
    for url in input_data['searchQueries']:
        print(f"   • {url}")
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
            
            for i, item in enumerate(items[:5]):  # Показываем первые 5
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
            json_filename = f"instagram_urls_results_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"\n💾 JSON сохранен: {json_filename}")
            
            # CSV файл (если возможно)
            try:
                df = pd.DataFrame(items)
                csv_filename = f"instagram_urls_results_{timestamp}.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8')
                print(f"💾 CSV сохранен: {csv_filename}")
            except Exception as e:
                print(f"⚠️ Ошибка при сохранении CSV: {e}")
            
            # Статистика
            print(f"\n📊 СТАТИСТИКА РЕЗУЛЬТАТОВ:")
            print("="*30)
            print(f"📈 Всего постов: {len(items)}")
            
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

if __name__ == "__main__":
    print("📸 INSTAGRAM СКРАПЕР - ПРАВИЛЬНОЕ ИСПОЛЬЗОВАНИЕ С URL")
    print("="*70)
    
    # Запускаем скрапер правильно
    results = run_instagram_with_urls()
    
    if results:
        print(f"\n🎉 Скрапинг завершен! Получено {len(results)} результатов")
        print(f"\n💡 Теперь вы знаете, как правильно использовать ваш Instagram скрапер!")
    else:
        print("\n❌ Скрапинг не удался")
