#!/usr/bin/env python3
"""
Интерактивный интерфейс для Instagram Selenium парсера
"""

import os
from dotenv import load_dotenv
from instagram_selenium_parser import InstagramSeleniumParser

load_dotenv()

def get_parsing_settings():
    """Получение настроек парсинга"""
    print("🔧 НАСТРОЙКИ SELENIUM ПАРСЕРА")
    print("=" * 50)
    
    # Имя пользователя
    username = input("👤 Введите имя пользователя Instagram: ").strip()
    if not username:
        print("❌ Имя пользователя обязательно")
        return None
    
    # Пароль
    password = input("🔐 Введите пароль Instagram: ").strip()
    if not password:
        print("❌ Пароль обязателен")
        return None
    
    # Лимит постов
    print(f"\n📊 Лимит постов для парсинга:")
    print(f"   • 10-50: Быстро (2-5 мин)")
    print(f"   • 100-200: Средне (10-20 мин)")
    print(f"   • 500-1000: Медленно (30+ мин)")
    
    while True:
        try:
            posts_limit = input("   Лимит постов (Enter для 100): ").strip()
            if not posts_limit:
                posts_limit = 100
            else:
                posts_limit = int(posts_limit)
            
            if posts_limit > 0:
                break
            else:
                print("   ❌ Лимит должен быть больше 0")
        except ValueError:
            print("   ❌ Введите корректное число")
    
    # Режим браузера
    print(f"\n🖥️ Режим браузера:")
    print(f"   • headless: Без интерфейса (быстрее)")
    print(f"   • visible: С интерфейсом (медленнее, но видно процесс)")
    
    headless_choice = input("   Режим (Enter для headless): ").strip().lower()
    headless = headless_choice not in ["visible", "v", "no", "n"]
    
    return {
        "username": username,
        "password": password,
        "posts_limit": posts_limit,
        "headless": headless
    }

def confirm_settings(settings):
    """Подтверждение настроек"""
    print(f"\n⚙️ НАСТРОЙКИ ПАРСИНГА:")
    print(f"   👤 Пользователь: @{settings['username']}")
    print(f"   📥 Макс. постов: {settings['posts_limit']}")
    print(f"   🖥️ Режим браузера: {'headless' if settings['headless'] else 'visible'}")
    print(f"   🗄️ MongoDB URI: mongodb://localhost:27017/")
    
    # Оценка времени
    estimated_time = settings['posts_limit'] * 2  # ~2 секунды на пост
    if estimated_time < 60:
        time_str = f"{estimated_time} сек"
    else:
        time_str = f"{estimated_time // 60} мин {estimated_time % 60} сек"
    
    print(f"   ⏱️ Примерное время: {time_str}")
    
    confirm = input(f"\n   Продолжить? (y/n): ").strip().lower()
    return confirm in ["y", "yes", "да", "д"]

def main():
    """Главная функция"""
    print("🚀 INSTAGRAM SELENIUM ПАРСЕР")
    print("=" * 50)
    print("📋 Возможности:")
    print("   • Парсинг любых публичных аккаунтов")
    print("   • Получение всех постов без ограничений")
    print("   • Скачивание изображений")
    print("   • Сохранение в MongoDB")
    print("   • Обход лимитов API")
    
    # Получение настроек
    settings = get_parsing_settings()
    if not settings:
        return
    
    # Подтверждение
    if not confirm_settings(settings):
        print("❌ Парсинг отменен")
        return
    
    print(f"\n🔄 ПРОЦЕСС ПАРСИНГА:")
    print(f"   1. 🔧 Настройка WebDriver")
    print(f"   2. 🔐 Авторизация в Instagram")
    print(f"   3. 🔍 Парсинг аккаунта @{settings['username']}")
    print(f"   4. 🖼️ Извлечение изображений")
    print(f"   5. ⬇️ Скачивание изображений")
    print(f"   6. 💾 Сохранение в MongoDB")
    print("=" * 60)
    
    # Создание парсера
    parser = InstagramSeleniumParser()
    
    # Запуск парсинга
    success = parser.run_full_parsing(
        username=settings['username'],
        password=settings['password'],
        posts_limit=settings['posts_limit']
    )
    
    if success:
        print("\n🎉 ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
        print("📊 Проверьте MongoDB для просмотра результатов")
    else:
        print("\n❌ ПАРСИНГ ЗАВЕРШЕН С ОШИБКАМИ")
        print("💡 Проверьте логи выше для диагностики")

if __name__ == "__main__":
    main()
