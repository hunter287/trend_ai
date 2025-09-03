"""
Получение данных из существующего успешного запуска Instagram скрапера
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient
import pandas as pd

load_dotenv()

def get_data_from_run(run_id):
    """Получает данные из конкретного запуска"""
    
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    print(f"✅ Подключение к Apify API установлено")
    
    print(f"\n🔍 ПОЛУЧЕНИЕ ДАННЫХ ИЗ ЗАПУСКА {run_id}")
    print("="*60)
    
    try:
        # Получаем информацию о запуске
        run_info = client.run(run_id).get()
        
        print(f"📊 Информация о запуске:")
        print(f"   🎭 Актор: {run_info.get('actId', 'N/A')}")
        print(f"   📊 Статус: {run_info.get('status', 'N/A')}")
        print(f"   📅 Начат: {run_info.get('startedAt', 'N/A')}")
        print(f"   ⏱️ Завершен: {run_info.get('finishedAt', 'N/A')}")
        
        # Получаем входные данные
        input_data = run_info.get('options', {}).get('input', {})
        if input_data:
            print(f"\n📝 Входные данные:")
            for key, value in input_data.items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"   {key}: {value}")
        
        # Получаем dataset ID
        dataset_id = run_info.get('defaultDatasetId')
        if not dataset_id:
            print("❌ Dataset ID не найден")
            return None
        
        print(f"\n📊 Получаем данные из датасета {dataset_id}...")
        
        # Получаем информацию о датасете
        dataset_info = client.dataset(dataset_id).get()
        total_items = dataset_info.get('itemCount', 0)
        print(f"📈 Всего элементов в датасете: {total_items}")
        
        # Получаем все элементы
        print(f"⏳ Загружаем данные...")
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
                for key in list(first_item.keys())[:20]:  # Первые 20 полей
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
                        if len(caption) > 150:
                            caption = caption[:150] + "..."
                        print(f"   📝 Текст: {caption}")
                    
                    # Хештеги
                    if 'hashtags' in item and item['hashtags']:
                        hashtags = item['hashtags'][:8]  # Первые 8 хештегов
                        print(f"   🏷️ Хештеги: {', '.join(hashtags)}")
                    
                    # Дата
                    if 'timestamp' in item:
                        timestamp = item.get('timestamp', 'N/A')
                        print(f"   📅 Дата: {timestamp}")
                    
                    # Медиа
                    if 'displayUrl' in item:
                        print(f"   🖼️ Изображение: {item.get('displayUrl', 'N/A')[:50]}...")
                else:
                    print(f"   {str(item)[:200]}...")
            
            # Сохраняем результаты
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON файл
            json_filename = f"linda_sza_data_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"\n💾 JSON сохранен: {json_filename}")
            
            # CSV файл (если возможно)
            try:
                df = pd.DataFrame(items)
                csv_filename = f"linda_sza_data_{timestamp}.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8')
                print(f"💾 CSV сохранен: {csv_filename}")
            except Exception as e:
                print(f"⚠️ Ошибка при сохранении CSV: {e}")
            
            # Статистика
            print(f"\n📊 СТАТИСТИКА ДАННЫХ:")
            print("="*30)
            print(f"📈 Всего постов: {len(items)}")
            
            # Подсчитываем статистику
            if items and isinstance(items[0], dict):
                total_likes = sum(item.get('likesCount', 0) for item in items if item.get('likesCount'))
                total_comments = sum(item.get('commentsCount', 0) for item in items if item.get('commentsCount'))
                unique_users = len(set(item.get('ownerUsername', '') for item in items if item.get('ownerUsername')))
                
                # Типы постов
                post_types = {}
                for item in items:
                    post_type = item.get('type', 'Unknown')
                    post_types[post_type] = post_types.get(post_type, 0) + 1
                
                print(f"❤️ Общее количество лайков: {total_likes:,}")
                print(f"💬 Общее количество комментариев: {total_comments:,}")
                print(f"👥 Уникальных пользователей: {unique_users}")
                
                print(f"\n📝 Типы постов:")
                for post_type, count in post_types.items():
                    print(f"   {post_type}: {count}")
                
                # Топ хештегов
                all_hashtags = []
                for item in items:
                    if item.get('hashtags'):
                        all_hashtags.extend(item['hashtags'])
                
                if all_hashtags:
                    hashtag_counts = {}
                    for hashtag in all_hashtags:
                        hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
                    
                    top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                    print(f"\n🏷️ Топ-10 хештегов:")
                    for hashtag, count in top_hashtags:
                        print(f"   #{hashtag}: {count} раз")
        
        return items
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def get_data_from_another_run():
    """Получает данные из другого успешного запуска"""
    
    # Другой успешный запуск
    run_id = "2kExkDIAwlqdRuvtD"  # 267 результатов из @hannaschonberg
    
    print(f"\n🔍 ПОЛУЧЕНИЕ ДАННЫХ ИЗ ДРУГОГО ЗАПУСКА {run_id}")
    print("="*60)
    
    return get_data_from_run(run_id)

if __name__ == "__main__":
    print("📸 ПОЛУЧЕНИЕ СУЩЕСТВУЮЩИХ ДАННЫХ INSTAGRAM")
    print("="*60)
    
    # Получаем данные из успешного запуска @linda.sza
    results1 = get_data_from_run("Op4YXnZyHXqoK90yK")
    
    if results1:
        print(f"\n🎉 Данные @linda.sza получены! Всего {len(results1)} постов")
    
    # Получаем данные из другого успешного запуска
    results2 = get_data_from_another_run()
    
    if results2:
        print(f"\n🎉 Данные @hannaschonberg получены! Всего {len(results2)} постов")
    
    print(f"\n💡 Теперь у вас есть реальные данные Instagram для анализа!")
