"""
Практический пример скрапинга с Apify

Этот пример показывает, как использовать готовые акторы Apify для скрапинга:
1. Google Shopping - поиск товаров
2. Instagram - профили и посты
3. LinkedIn - профили компаний
4. Twitter - твиты и профили
"""

import os
import time
import json
from dotenv import load_dotenv
from apify_client import ApifyClient
import pandas as pd

# Загружаем переменные окружения
load_dotenv()

class ApifyScraper:
    """Класс для скрапинга с помощью Apify акторов"""
    
    def __init__(self):
        """Инициализация клиента Apify"""
        self.api_token = os.getenv('APIFY_API_TOKEN')
        if not self.api_token:
            raise ValueError("API токен не найден. Установите APIFY_API_TOKEN в .env файле")
        
        self.client = ApifyClient(self.api_token)
        print("✅ Apify клиент инициализирован")
    
    def scrape_google_shopping(self, queries: list, max_items: int = 20):
        """
        Скрапинг Google Shopping
        
        Args:
            queries: Список поисковых запросов
            max_items: Максимальное количество товаров на запрос
        """
        print(f"\n🛒 Скрапинг Google Shopping для запросов: {queries}")
        
        # ID актора Google Shopping
        actor_id = "apify/google-shopping-scraper"
        
        # Входные данные
        input_data = {
            "queries": queries,
            "maxItemsPerQuery": max_items,
            "maxRequestRetries": 3,
            "maxConcurrency": 5
        }
        
        return self._run_actor_and_get_results(actor_id, input_data, "google_shopping")
    
    def scrape_instagram_profiles(self, usernames: list):
        """
        Скрапинг профилей Instagram
        
        Args:
            usernames: Список имен пользователей
        """
        print(f"\n📸 Скрапинг профилей Instagram: {usernames}")
        
        # ID актора Instagram
        actor_id = "apify/instagram-profile-scraper"
        
        # Входные данные
        input_data = {
            "usernames": usernames,
            "resultsType": "details",
            "maxRequestRetries": 3
        }
        
        return self._run_actor_and_get_results(actor_id, input_data, "instagram_profiles")
    
    def scrape_linkedin_companies(self, company_names: list):
        """
        Скрапинг компаний LinkedIn
        
        Args:
            company_names: Список названий компаний
        """
        print(f"\n💼 Скрапинг компаний LinkedIn: {company_names}")
        
        # ID актора LinkedIn
        actor_id = "apify/linkedin-company-scraper"
        
        # Входные данные
        input_data = {
            "companyNames": company_names,
            "maxRequestRetries": 3
        }
        
        return self._run_actor_and_get_results(actor_id, input_data, "linkedin_companies")
    
    def scrape_twitter_profiles(self, usernames: list):
        """
        Скрапинг профилей Twitter
        
        Args:
            usernames: Список имен пользователей
        """
        print(f"\n🐦 Скрапинг профилей Twitter: {usernames}")
        
        # ID актора Twitter
        actor_id = "apify/twitter-profile-scraper"
        
        # Входные данные
        input_data = {
            "usernames": usernames,
            "maxRequestRetries": 3
        }
        
        return self._run_actor_and_get_results(actor_id, input_data, "twitter_profiles")
    
    def _run_actor_and_get_results(self, actor_id: str, input_data: dict, output_prefix: str):
        """
        Запуск актора и получение результатов
        
        Args:
            actor_id: ID актора
            input_data: Входные данные
            output_prefix: Префикс для файлов результатов
        """
        try:
            # Запускаем актор
            print(f"🚀 Запускаем актор {actor_id}...")
            run = self.client.actor(actor_id).call(input_data)
            run_id = run['id']
            print(f"✅ Актор запущен с ID: {run_id}")
            
            # Ждем завершения
            print("⏳ Ожидаем завершения...")
            while True:
                run_info = self.client.run(run_id).get()
                status = run_info.get('status')
                
                if status == 'SUCCEEDED':
                    print("✅ Актор завершен успешно")
                    break
                elif status in ['FAILED', 'ABORTED']:
                    print(f"❌ Актор завершен со статусом: {status}")
                    return None
                
                time.sleep(10)  # Ждем 10 секунд
            
            # Получаем результаты
            dataset_id = run_info.get('defaultDatasetId')
            if not dataset_id:
                print("❌ Dataset ID не найден")
                return None
            
            print("📊 Получаем результаты...")
            dataset_items = self.client.dataset(dataset_id).list_items()
            items = dataset_items.items
            
            print(f"✅ Получено {len(items)} элементов")
            
            # Сохраняем результаты
            self._save_results(items, output_prefix)
            
            return items
            
        except Exception as e:
            print(f"❌ Ошибка при выполнении актора: {e}")
            return None
    
    def _save_results(self, items: list, prefix: str):
        """Сохранение результатов в разные форматы"""
        if not items:
            print("❌ Нет данных для сохранения")
            return
        
        # Сохраняем в JSON
        json_filename = f"{prefix}_results.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON сохранен: {json_filename}")
        
        # Сохраняем в CSV
        try:
            df = pd.DataFrame(items)
            csv_filename = f"{prefix}_results.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"💾 CSV сохранен: {csv_filename}")
        except Exception as e:
            print(f"⚠️ Ошибка при сохранении CSV: {e}")
        
        # Показываем первые результаты
        print(f"\n📋 Первые результаты:")
        for i, item in enumerate(items[:3]):
            if isinstance(item, dict):
                # Показываем ключи для понимания структуры данных
                keys = list(item.keys())[:5]  # Первые 5 ключей
                print(f"  {i+1}. Ключи: {keys}")
                # Показываем несколько значений
                for key in keys[:3]:
                    value = str(item.get(key, ''))[:50]  # Обрезаем длинные значения
                    print(f"     {key}: {value}...")
            else:
                print(f"  {i+1}. {str(item)[:100]}...")
            print()


def main():
    """Основная функция с примерами скрапинга"""
    print("🚀 ПРАКТИЧЕСКИЕ ПРИМЕРЫ СКРАПИНГА С APIFY")
    print("="*60)
    
    try:
        scraper = ApifyScraper()
        
        # Пример 1: Google Shopping
        print("\n" + "="*40)
        print("ПРИМЕР 1: GOOGLE SHOPPING")
        print("="*40)
        
        shopping_queries = ["laptop", "smartphone"]
        scraper.scrape_google_shopping(shopping_queries, max_items=10)
        
        # Пример 2: Instagram (закомментирован, так как требует реальных данных)
        print("\n" + "="*40)
        print("ПРИМЕР 2: INSTAGRAM PROFILES")
        print("="*40)
        print("💡 Для тестирования Instagram скрапинга раскомментируйте код ниже")
        print("   и укажите реальные имена пользователей")
        
        # instagram_users = ["instagram", "nike"]  # Примеры
        # scraper.scrape_instagram_profiles(instagram_users)
        
        # Пример 3: LinkedIn (закомментирован)
        print("\n" + "="*40)
        print("ПРИМЕР 3: LINKEDIN COMPANIES")
        print("="*40)
        print("💡 Для тестирования LinkedIn скрапинга раскомментируйте код ниже")
        
        # linkedin_companies = ["microsoft", "google"]  # Примеры
        # scraper.scrape_linkedin_companies(linkedin_companies)
        
        # Пример 4: Twitter (закомментирован)
        print("\n" + "="*40)
        print("ПРИМЕР 4: TWITTER PROFILES")
        print("="*40)
        print("💡 Для тестирования Twitter скрапинга раскомментируйте код ниже")
        
        # twitter_users = ["elonmusk", "twitter"]  # Примеры
        # scraper.scrape_twitter_profiles(twitter_users)
        
    except ValueError as e:
        print(f"❌ Ошибка инициализации: {e}")
        print("\n💡 Для работы:")
        print("1. Создайте файл .env")
        print("2. Добавьте: APIFY_API_TOKEN=ваш_токен")
        print("3. Получите токен на https://console.apify.com/account/integrations")
    
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")


if __name__ == "__main__":
    main()
