"""
Практический тест Apify API - запуск актора и получение данных
"""

import os
import time
import json
from dotenv import load_dotenv
from apify_client import ApifyClient

# Загружаем переменные окружения
load_dotenv()

def test_web_scraper():
    """Тестируем Web Scraper на простом сайте"""
    
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    print("✅ Подключение к Apify API установлено")
    
    # Данные для скрапинга простого сайта
    input_data = {
        "startUrls": [
            {"url": "https://quotes.toscrape.com/"}  # Тестовый сайт для скрапинга
        ],
        "pageFunction": """
async function pageFunction(context) {
    const { page, request } = context;
    
    // Извлекаем цитаты со страницы
    const quotes = await page.evaluate(() => {
        const quoteElements = document.querySelectorAll('.quote');
        return Array.from(quoteElements).map(quote => {
            const text = quote.querySelector('.text')?.textContent;
            const author = quote.querySelector('.author')?.textContent;
            const tags = Array.from(quote.querySelectorAll('.tag')).map(tag => tag.textContent);
            
            return {
                text: text,
                author: author,
                tags: tags,
                url: window.location.href
            };
        });
    });
    
    return quotes.map(quote => ({
        ...quote,
        scrapedAt: new Date().toISOString()
    }));
}
        """,
        "maxRequestRetries": 2,
        "maxPagesPerCrawl": 1,
        "maxRequestsPerCrawl": 1
    }
    
    print("🚀 Запускаем Web Scraper...")
    print(f"🎯 Целевой сайт: {input_data['startUrls'][0]['url']}")
    
    try:
        # Запускаем актор
        run = client.actor('apify/web-scraper').call(run_input=input_data)
        run_id = run['id']
        print(f"✅ Актор запущен с ID: {run_id}")
        
        # Ждем завершения (максимум 5 минут)
        print("⏳ Ожидаем завершения...")
        timeout = 300  # 5 минут
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            run_info = client.run(run_id).get()
            status = run_info.get('status')
            
            print(f"📊 Статус: {status}")
            
            if status == 'SUCCEEDED':
                print("✅ Скрапинг завершен успешно!")
                break
            elif status in ['FAILED', 'ABORTED']:
                print(f"❌ Скрапинг завершен с ошибкой: {status}")
                return None
            
            time.sleep(10)  # Ждем 10 секунд
        else:
            print("⏰ Таймаут - останавливаем актор")
            client.run(run_id).abort()
            return None
        
        # Получаем результаты
        dataset_id = run_info.get('defaultDatasetId')
        if not dataset_id:
            print("❌ Dataset ID не найден")
            return None
        
        print("📊 Получаем результаты...")
        dataset_items = client.dataset(dataset_id).list_items()
        items = dataset_items.items
        
        print(f"✅ Получено {len(items)} элементов")
        
        # Показываем результаты
        if items:
            print("\n📋 Результаты скрапинга:")
            print("="*60)
            
            for i, item in enumerate(items[:3]):  # Показываем первые 3
                if isinstance(item, list):
                    # Если элемент - это список цитат
                    for j, quote in enumerate(item[:2]):  # Первые 2 цитаты
                        print(f"\n{i+1}.{j+1} 💬 Цитата:")
                        print(f"📝 Текст: {quote.get('text', 'N/A')}")
                        print(f"👤 Автор: {quote.get('author', 'N/A')}")
                        print(f"🏷️ Теги: {', '.join(quote.get('tags', []))}")
                        print(f"🌐 URL: {quote.get('url', 'N/A')}")
                        print(f"📅 Время: {quote.get('scrapedAt', 'N/A')}")
                else:
                    # Если элемент - это объект
                    print(f"\n{i+1}. 📄 Элемент:")
                    for key, value in item.items():
                        if isinstance(value, str) and len(value) > 100:
                            value = value[:100] + "..."
                        print(f"   {key}: {value}")
            
            # Сохраняем в файл
            filename = f"apify_results_{run_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Результаты сохранены в: {filename}")
        
        return items
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def check_usage():
    """Проверяем использование ресурсов"""
    
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    
    try:
        user = client.user().get()
        usage = user.get('monthlyUsage', {})
        
        print("\n💰 ИСПОЛЬЗОВАНИЕ РЕСУРСОВ:")
        print("="*40)
        print(f"📊 Compute units: {usage.get('compute', 0)}")
        print(f"💾 Data transfer: {usage.get('dataTransfer', 0)} bytes")
        print(f"📦 Dataset operations: {usage.get('datasetWrites', 0)}")
        
    except Exception as e:
        print(f"❌ Ошибка получения информации об использовании: {e}")

if __name__ == "__main__":
    print("🔬 ПРАКТИЧЕСКИЙ ТЕСТ APIFY API")
    print("="*50)
    
    # Проверяем использование до запуска
    check_usage()
    
    # Запускаем тест
    results = test_web_scraper()
    
    # Проверяем использование после запуска
    if results:
        check_usage()
        print(f"\n🎉 Тест завершен! Получено {len(results) if isinstance(results, list) else 0} результатов")
    else:
        print("\n❌ Тест не удался")
