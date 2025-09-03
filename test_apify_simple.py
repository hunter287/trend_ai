#!/usr/bin/env python3
"""
Простой тест Apify Instagram Scraper
"""

from apify_client import ApifyClient
from dotenv import load_dotenv
import os
import time

# Загружаем переменные окружения
load_dotenv()

def test_instagram_scraper():
    """Тест Instagram Scraper с таймаутом"""
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    
    print("🔍 Тестируем Instagram Scraper...")
    print("📝 Входные данные:")
    
    run_input = {
        "directUrls": [f"https://www.instagram.com/linda.sza/"],
        "resultsType": "posts",
        "resultsLimit": 10,  # Ограничиваем для теста
        "addParentData": False
    }
    
    print(f"   • URL: {run_input['directUrls'][0]}")
    print(f"   • Лимит: {run_input['resultsLimit']}")
    
    try:
        print("🚀 Запуск актора...")
        start_time = time.time()
        
        # Запускаем актор
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
        
        elapsed_time = time.time() - start_time
        print(f"⏱️ Время выполнения: {elapsed_time:.2f} секунд")
        
        if run and run.get("defaultDatasetId"):
            print("📥 Получение данных...")
            dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
            print(f"✅ Получено {len(dataset_items)} постов")
            
            # Показываем первый пост
            if dataset_items:
                first_post = dataset_items[0]
                print(f"📄 Первый пост:")
                print(f"   • ID: {first_post.get('shortCode', 'N/A')}")
                print(f"   • Пользователь: {first_post.get('ownerUsername', 'N/A')}")
                print(f"   • Лайки: {first_post.get('likesCount', 0)}")
                print(f"   • Есть изображение: {'Да' if first_post.get('displayUrl') else 'Нет'}")
            
            return True
        else:
            print("❌ Не удалось получить данные")
            return False
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ Ошибка после {elapsed_time:.2f} секунд: {e}")
        return False

if __name__ == "__main__":
    success = test_instagram_scraper()
    if success:
        print("\n🎉 Тест прошел успешно!")
    else:
        print("\n💥 Тест не прошел")
