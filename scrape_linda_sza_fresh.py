"""
Свежий скрапинг профиля @linda.sza с помощью Instagram актора
"""

import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient
import pandas as pd

load_dotenv()

def scrape_linda_sza_fresh():
    """Запускает свежий скрапинг профиля @linda.sza"""
    
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    print("✅ Подключение к Apify API установлено")
    
    # ID Instagram скрапера (используем рабочий актор)
    actor_id = "apify/instagram-scraper"
    
    # Входные данные для скрапинга @linda.sza (оптимизированные)
    input_data = {
        "directUrls": ["https://www.instagram.com/linda.sza/"],
        "resultsType": "posts",  # Вместо "details" для быстрого выполнения
        "resultsLimit": 50,      # Меньше для теста
        "addParentData": False
    }
    
    print(f"\n🎯 СВЕЖИЙ СКРАПИНГ ПРОФИЛЯ @linda.sza")
    print("="*60)
    print(f"🔍 URL профиля: {input_data['directUrls'][0]}")
    print(f"📊 Максимум результатов: {input_data['resultsLimit']}")
    print(f"🎯 Тип данных: {input_data['resultsType']}")
    
    try:
        # Запускаем актор
        print(f"\n🚀 Запускаем актор {actor_id}...")
        print("⏳ Это может занять 30-60 секунд...")
        
        start_time = time.time()
        run = client.actor(actor_id).call(run_input=input_data)
        elapsed_time = time.time() - start_time
        
        run_id = run['id']
        print(f"✅ Актор запущен с ID: {run_id}")
        print(f"⏱️ Время выполнения: {elapsed_time:.1f} секунд")
        
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
            json_filename = f"linda_sza_fresh_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"\n💾 JSON сохранен: {json_filename}")
            
            # CSV файл (если возможно)
            try:
                df = pd.DataFrame(items)
                csv_filename = f"linda_sza_fresh_{timestamp}.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8')
                print(f"💾 CSV сохранен: {csv_filename}")
            except Exception as e:
                print(f"⚠️ Ошибка при сохранении CSV: {e}")
            
            # Статистика
            print(f"\n📊 СТАТИСТИКА СВЕЖИХ ДАННЫХ:")
            print("="*35)
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
                
                # Анализ дат
                if items:
                    timestamps = [item.get('timestamp') for item in items if item.get('timestamp')]
                    if timestamps:
                        timestamps.sort()
                        print(f"\n📅 Временной диапазон:")
                        print(f"   Самый старый пост: {timestamps[0]}")
                        print(f"   Самый новый пост: {timestamps[-1]}")
        
        return items
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def compare_with_old_data():
    """Сравнивает свежие данные со старыми"""
    
    print(f"\n🔄 СРАВНЕНИЕ С ПРЕДЫДУЩИМИ ДАННЫМИ")
    print("="*50)
    
    # Ищем старые файлы
    import glob
    old_files = glob.glob("linda_sza_data_*.json")
    
    if old_files:
        print(f"📁 Найдено {len(old_files)} старых файлов данных")
        
        # Берем самый новый старый файл
        latest_old_file = max(old_files)
        print(f"📄 Сравниваем с: {latest_old_file}")
        
        try:
            with open(latest_old_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            
            print(f"📊 Старые данные: {len(old_data)} постов")
            
            # Сравнение будет показано после получения новых данных
            return old_data
            
        except Exception as e:
            print(f"❌ Ошибка чтения старых данных: {e}")
    else:
        print("📁 Старые файлы данных не найдены")
    
    return None

if __name__ == "__main__":
    print("📸 СВЕЖИЙ СКРАПИНГ ПРОФИЛЯ @linda.sza")
    print("="*60)
    
    # Сравниваем со старыми данными
    old_data = compare_with_old_data()
    
    # Запускаем свежий скрапинг
    fresh_results = scrape_linda_sza_fresh()
    
    if fresh_results:
        print(f"\n🎉 Свежий скрапинг завершен! Получено {len(fresh_results)} постов")
        
        # Сравнение с старыми данными
        if old_data:
            print(f"\n📊 СРАВНЕНИЕ ДАННЫХ:")
            print("="*30)
            print(f"📈 Старые данные: {len(old_data)} постов")
            print(f"📈 Новые данные: {len(fresh_results)} постов")
            print(f"📈 Разница: {len(fresh_results) - len(old_data)} постов")
            
            # Сравниваем посты по shortCode
            old_codes = set(item.get('shortCode') for item in old_data if item.get('shortCode'))
            new_codes = set(item.get('shortCode') for item in fresh_results if item.get('shortCode'))
            
            common_codes = old_codes.intersection(new_codes)
            new_only_codes = new_codes - old_codes
            old_only_codes = old_codes - new_codes
            
            print(f"🔄 Общих постов: {len(common_codes)}")
            print(f"🆕 Только в новых данных: {len(new_only_codes)}")
            print(f"🗑️ Только в старых данных: {len(old_only_codes)}")
        
        print(f"\n💡 Теперь у вас есть свежие данные @linda.sza для анализа!")
    else:
        print("\n❌ Свежий скрапинг не удался")
