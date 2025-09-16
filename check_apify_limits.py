#!/usr/bin/env python3
"""
Проверка лимитов Apify API
"""

from apify_client import ApifyClient
from dotenv import load_dotenv
import os

load_dotenv()

def check_limits():
    """Проверка лимитов и статуса аккаунта"""
    try:
        client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
        
        print("🔍 Проверка лимитов Apify...")
        
        # Получаем информацию о пользователе
        user_info = client.user().get()
        print(f"👤 Пользователь: {user_info.get('username', 'N/A')}")
        print(f"📧 Email: {user_info.get('email', 'N/A')}")
        
        # Получаем информацию о подписке
        subscription = user_info.get('subscription', {})
        print(f"💳 План: {subscription.get('plan', 'N/A')}")
        print(f"💰 Статус: {subscription.get('status', 'N/A')}")
        
        # Получаем статистику использования
        usage = client.user().usage()
        print(f"📊 Использование:")
        print(f"   • Запросы в этом месяце: {usage.get('requestsThisMonth', 'N/A')}")
        print(f"   • Лимит запросов: {usage.get('requestsLimit', 'N/A')}")
        print(f"   • Осталось запросов: {usage.get('requestsRemaining', 'N/A')}")
        
        # Проверяем, превышен ли лимит
        remaining = usage.get('requestsRemaining', 0)
        if remaining <= 0:
            print("❌ Лимит запросов исчерпан!")
            print("💡 Решения:")
            print("   1. Обновить план на https://console.apify.com/account/billing")
            print("   2. Дождаться сброса лимита (1 числа каждого месяца)")
            print("   3. Создать новый аккаунт Apify")
        else:
            print(f"✅ Осталось {remaining} запросов")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_limits()


