"""
Простой пример использования Apify API

Этот файл демонстрирует базовые возможности Apify API:
1. Подключение к API
2. Получение информации о пользователе
3. Запуск простого актора
4. Получение результатов
"""

import os
from dotenv import load_dotenv
from apify_client import ApifyClient

# Загружаем переменные окружения
load_dotenv()

def main():
    """Основная функция демонстрации"""
    
    # Получаем API токен
    api_token = os.getenv('APIFY_API_TOKEN')
    
    if not api_token:
        print("❌ API токен не найден!")
        print("💡 Создайте файл .env и добавьте в него:")
        print("   APIFY_API_TOKEN=ваш_токен_здесь")
        print("🔗 Получите токен на: https://console.apify.com/account/integrations")
        return
    
    # Создаем клиент
    client = ApifyClient(api_token)
    print("✅ Подключение к Apify API установлено")
    
    # 1. Получаем информацию о пользователе
    print("\n👤 Информация о пользователе:")
    try:
        user = client.user().get()
        print(f"   Имя: {user.get('name', 'N/A')}")
        print(f"   Email: {user.get('email', 'N/A')}")
        print(f"   ID: {user.get('id', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # 2. Получаем список популярных акторов
    print("\n🎭 Популярные акторы:")
    try:
        actors = client.actors().list(limit=3)
        for actor in actors.items:
            print(f"   - {actor.get('name', 'N/A')} (ID: {actor.get('id', 'N/A')})")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # 3. Пример запуска простого актора (комментарий, так как требует реального актора)
    print("\n🚀 Пример запуска актора:")
    print("   💡 Для запуска актора используйте:")
    print("   run = client.actor('actor_id').call(input_data)")
    print("   run_id = run['id']")
    
    # 4. Пример получения данных из датасета (комментарий)
    print("\n📊 Пример получения данных:")
    print("   💡 Для получения данных используйте:")
    print("   dataset_items = client.dataset('dataset_id').list_items()")
    print("   items = dataset_items.items")

if __name__ == "__main__":
    main()
