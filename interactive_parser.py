"""
Интерактивный Instagram Parser
"""

import os
import sys
from dotenv import load_dotenv
from instagram_parser import InstagramParser

# Загружаем переменные окружения из .env файла
load_dotenv()
load_dotenv('mongodb_config.env')

def print_banner():
    """Печать баннера"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    🖼️  INSTAGRAM PARSER                     ║
║                                                              ║
║  Парсинг Instagram аккаунтов через Apify с сохранением      ║
║  в MongoDB и скачиванием ВСЕХ изображений из постов         ║
║                                                              ║
║  💡 Укажите количество постов - все изображения из них      ║
║     будут автоматически скачаны                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

def get_apify_token():
    """Получение токена Apify"""
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        print("❌ Не найден APIFY_API_TOKEN в переменных окружения")
        print("💡 Установите токен:")
        print("   export APIFY_API_TOKEN=your_token")
        print("   или добавьте в .env файл")
        return None
    return token

def get_mongodb_uri():
    """Получение URI MongoDB"""
    default_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:|#!x1K52H.0{8d3@localhost:27017/instagram_gallery')
    print(f"\n📊 Настройка MongoDB:")
    print(f"   По умолчанию: {default_uri}")
    
    custom_uri = input("   Введите URI MongoDB (Enter для использования по умолчанию): ").strip()
    return custom_uri if custom_uri else default_uri

def get_username():
    """Получение имени пользователя"""
    print(f"\n👤 Введите имя пользователя Instagram:")
    print(f"   Пример: linda.sza (без @ и https://instagram.com/)")
    
    while True:
        username = input("   Username: ").strip()
        if username:
            # Убираем @ если пользователь его ввел
            username = username.lstrip('@')
            # Убираем URL если пользователь его ввел
            if 'instagram.com/' in username:
                username = username.split('instagram.com/')[-1].rstrip('/')
            return username
        else:
            print("   ❌ Имя пользователя не может быть пустым")

def get_max_posts():
    """Получение максимального количества постов для парсинга"""
    print(f"\n📝 Количество постов для парсинга:")
    print(f"   Рекомендуется: 10-50 для тестирования")
    print(f"   💡 Все изображения из указанных постов будут скачаны")
    
    while True:
        try:
            max_posts = input("   Количество постов (Enter для 20): ").strip()
            if not max_posts:
                return 20
            max_posts = int(max_posts)
            if max_posts > 0:
                return max_posts
            else:
                print("   ❌ Количество должно быть больше 0")
        except ValueError:
            print("   ❌ Введите корректное число")

def confirm_settings(username, max_posts, mongodb_uri):
    """Подтверждение настроек"""
    print(f"\n⚙️  НАСТРОЙКИ ПАРСИНГА:")
    print(f"   👤 Пользователь: @{username}")
    print(f"   📝 Количество постов: {max_posts}")
    print(f"   🖼️  Все изображения из постов будут скачаны")
    print(f"   🗄️  MongoDB URI: {mongodb_uri}")
    
    while True:
        confirm = input(f"\n   Продолжить? (y/n): ").strip().lower()
        if confirm in ['y', 'yes', 'да', 'д']:
            return True
        elif confirm in ['n', 'no', 'нет', 'н']:
            return False
        else:
            print("   ❌ Введите 'y' или 'n'")

def show_progress():
    """Показ прогресса"""
    print(f"\n🔄 ПРОЦЕСС ПАРСИНГА:")
    print(f"   1. 🔍 Парсинг аккаунта через Apify")
    print(f"   2. 🖼️  Извлечение URL изображений")
    print(f"   3. 🔄 Удаление дубликатов")
    print(f"   4. ⬇️  Скачивание изображений")
    print(f"   5. 💾 Сохранение в MongoDB")
    print(f"   6. 🌐 Создание HTML галереи")
    print(f"   " + "="*50)

def main():
    """Главная функция"""
    print_banner()
    
    # Проверяем токен Apify
    apify_token = get_apify_token()
    if not apify_token:
        return
    
    # Получаем настройки
    mongodb_uri = get_mongodb_uri()
    username = get_username()
    max_posts = get_max_posts()
    
    # Подтверждаем настройки
    if not confirm_settings(username, max_posts, mongodb_uri):
        print("❌ Парсинг отменен")
        return
    
    # Показываем прогресс
    show_progress()
    
    # Создаем парсер и запускаем
    try:
        parser = InstagramParser(apify_token, mongodb_uri)
        # Передаем max_posts как posts_limit и убираем ограничение на изображения
        success = parser.run_full_parsing(username, max_images=999999, posts_limit=max_posts)
        
        if success:
            print(f"\n🎉 ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
            print(f"📁 Результаты:")
            print(f"   • Изображения: ./images/")
            print(f"   • HTML галерея: ./gallery_{username}.html")
            print(f"   • Данные в MongoDB: instagram_gallery.images")
        else:
            print(f"\n❌ ОШИБКА ПРИ ПАРСИНГЕ")
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Парсинг прерван пользователем")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    main()
