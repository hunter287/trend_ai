"""
Примеры использования Apify API с Python

Apify - это платформа для веб-скрапинга и автоматизации, которая предоставляет:
1. Готовые акторы (готовые решения для скрапинга)
2. Возможность создавать собственные акторы
3. API для управления акторами и получения данных
4. Хранилище данных (Dataset, Key-value store, Request queue)

Основные концепции:
- Actor: программа, которая выполняется на платформе Apify
- Run: конкретное выполнение актора
- Dataset: хранилище структурированных данных
- Key-value store: хранилище ключ-значение
- Request queue: очередь запросов для актора
"""

import os
import json
import time
from typing import Dict, List, Any
from dotenv import load_dotenv
from apify_client import ApifyClient
import pandas as pd

# Загружаем переменные окружения
load_dotenv()

class ApifyManager:
    """Класс для работы с Apify API"""
    
    def __init__(self, api_token: str = None):
        """
        Инициализация клиента Apify
        
        Args:
            api_token: API токен Apify. Если не указан, берется из переменной окружения
        """
        self.api_token = api_token or os.getenv('APIFY_API_TOKEN')
        if not self.api_token:
            raise ValueError("API токен не найден. Установите переменную APIFY_API_TOKEN или передайте токен в конструктор")
        
        self.client = ApifyClient(self.api_token)
        print(f"✅ Подключение к Apify API установлено")
    
    def get_user_info(self) -> Dict[str, Any]:
        """Получение информации о пользователе"""
        try:
            user_info = self.client.user().get()
            print(f"👤 Пользователь: {user_info.get('name', 'N/A')}")
            print(f"📧 Email: {user_info.get('email', 'N/A')}")
            return user_info
        except Exception as e:
            print(f"❌ Ошибка при получении информации о пользователе: {e}")
            return {}
    
    def list_actors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение списка доступных акторов"""
        try:
            actors = self.client.actors().list(limit=limit)
            print(f"🎭 Найдено {len(actors.items)} акторов:")
            for actor in actors.items:
                print(f"  - {actor.get('name', 'N/A')} (ID: {actor.get('id', 'N/A')})")
            return actors.items
        except Exception as e:
            print(f"❌ Ошибка при получении списка акторов: {e}")
            return []
    
    def run_actor(self, actor_id: str, input_data: Dict[str, Any] = None) -> str:
        """
        Запуск актора
        
        Args:
            actor_id: ID актора для запуска
            input_data: Входные данные для актора
            
        Returns:
            run_id: ID запуска
        """
        try:
            print(f"🚀 Запускаем актор {actor_id}...")
            
            # Запускаем актор
            run = self.client.actor(actor_id).call(input_data or {})
            run_id = run['id']
            
            print(f"✅ Актор запущен с ID: {run_id}")
            return run_id
            
        except Exception as e:
            print(f"❌ Ошибка при запуске актора: {e}")
            return None
    
    def wait_for_run_completion(self, run_id: str, timeout: int = 300) -> Dict[str, Any]:
        """
        Ожидание завершения выполнения актора
        
        Args:
            run_id: ID запуска
            timeout: Таймаут ожидания в секундах
            
        Returns:
            run_info: Информация о запуске
        """
        try:
            print(f"⏳ Ожидаем завершения запуска {run_id}...")
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                run_info = self.client.run(run_id).get()
                status = run_info.get('status')
                
                print(f"📊 Статус: {status}")
                
                if status in ['SUCCEEDED', 'FAILED', 'ABORTED']:
                    print(f"✅ Запуск завершен со статусом: {status}")
                    return run_info
                
                time.sleep(5)  # Ждем 5 секунд перед следующей проверкой
            
            print(f"⏰ Таймаут ожидания превышен")
            return {}
            
        except Exception as e:
            print(f"❌ Ошибка при ожидании завершения: {e}")
            return {}
    
    def get_dataset_items(self, dataset_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получение данных из датасета
        
        Args:
            dataset_id: ID датасета
            limit: Максимальное количество элементов
            
        Returns:
            items: Список элементов из датасета
        """
        try:
            print(f"📊 Получаем данные из датасета {dataset_id}...")
            
            dataset_items = self.client.dataset(dataset_id).list_items(limit=limit)
            items = dataset_items.items
            
            print(f"✅ Получено {len(items)} элементов из датасета")
            return items
            
        except Exception as e:
            print(f"❌ Ошибка при получении данных из датасета: {e}")
            return []
    
    def save_to_csv(self, items: List[Dict[str, Any]], filename: str):
        """Сохранение данных в CSV файл"""
        try:
            df = pd.DataFrame(items)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"💾 Данные сохранены в файл: {filename}")
        except Exception as e:
            print(f"❌ Ошибка при сохранении в CSV: {e}")
    
    def get_key_value_store(self, store_id: str, key: str = None) -> Any:
        """
        Получение данных из Key-value store
        
        Args:
            store_id: ID хранилища
            key: Ключ для получения (если None, возвращает все ключи)
            
        Returns:
            data: Данные из хранилища
        """
        try:
            if key:
                data = self.client.key_value_store(store_id).get_record(key)
                print(f"🔑 Получено значение для ключа '{key}' из хранилища {store_id}")
            else:
                data = self.client.key_value_store(store_id).list_keys()
                print(f"🔑 Получены все ключи из хранилища {store_id}")
            
            return data
            
        except Exception as e:
            print(f"❌ Ошибка при получении данных из Key-value store: {e}")
            return None


def example_web_scraping():
    """Пример веб-скрапинга с помощью готового актора"""
    print("\n" + "="*50)
    print("🌐 ПРИМЕР ВЕБ-СКРАПИНГА")
    print("="*50)
    
    # Инициализируем менеджер
    apify = ApifyManager()
    
    # Получаем информацию о пользователе
    apify.get_user_info()
    
    # Пример: скрапинг Google Shopping
    # Actor ID для Google Shopping: apify/google-shopping-scraper
    actor_id = "apify/google-shopping-scraper"
    
    # Входные данные для актора
    input_data = {
        "queries": ["laptop", "smartphone"],
        "maxRequestRetries": 3,
        "maxConcurrency": 10,
        "maxRequestRetries": 3,
        "maxItemsPerQuery": 20
    }
    
    print(f"\n🎯 Запускаем скрапинг Google Shopping...")
    print(f"📝 Поисковые запросы: {input_data['queries']}")
    
    # Запускаем актор
    run_id = apify.run_actor(actor_id, input_data)
    
    if run_id:
        # Ждем завершения
        run_info = apify.wait_for_run_completion(run_id)
        
        if run_info.get('status') == 'SUCCEEDED':
            # Получаем данные из датасета
            dataset_id = run_info.get('defaultDatasetId')
            if dataset_id:
                items = apify.get_dataset_items(dataset_id, limit=50)
                
                if items:
                    # Сохраняем в CSV
                    apify.save_to_csv(items, 'google_shopping_results.csv')
                    
                    # Показываем первые несколько результатов
                    print(f"\n📋 Первые результаты:")
                    for i, item in enumerate(items[:3]):
                        print(f"  {i+1}. {item.get('title', 'N/A')} - {item.get('price', 'N/A')}")


def example_actor_management():
    """Пример управления акторами"""
    print("\n" + "="*50)
    print("🎭 УПРАВЛЕНИЕ АКТОРАМИ")
    print("="*50)
    
    apify = ApifyManager()
    
    # Получаем список популярных акторов
    actors = apify.list_actors(limit=5)
    
    if actors:
        print(f"\n📋 Доступные акторы:")
        for i, actor in enumerate(actors):
            print(f"  {i+1}. {actor.get('name', 'N/A')}")
            print(f"     ID: {actor.get('id', 'N/A')}")
            print(f"     Описание: {actor.get('description', 'N/A')[:100]}...")
            print()


def example_key_value_store():
    """Пример работы с Key-value store"""
    print("\n" + "="*50)
    print("🔑 KEY-VALUE STORE")
    print("="*50)
    
    apify = ApifyManager()
    
    # Пример: получение данных из Key-value store
    # Обычно store_id получается из информации о запуске
    print("💡 Для работы с Key-value store нужен store_id из информации о запуске актора")
    print("   Этот пример показывает структуру, но требует реального store_id")


if __name__ == "__main__":
    print("🚀 ДЕМОНСТРАЦИЯ APIFY API")
    print("="*50)
    
    try:
        # Проверяем подключение
        apify = ApifyManager()
        
        # Запускаем примеры
        example_actor_management()
        example_web_scraping()
        example_key_value_store()
        
    except ValueError as e:
        print(f"❌ Ошибка инициализации: {e}")
        print("\n💡 Для работы с Apify API:")
        print("1. Создайте файл .env в корне проекта")
        print("2. Добавьте в него: APIFY_API_TOKEN=ваш_токен")
        print("3. Получите токен на https://console.apify.com/account/integrations")
    
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
