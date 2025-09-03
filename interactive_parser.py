"""
Интерактивный Instagram Parser
"""

import os
import sys
from dotenv import load_dotenv
from instagram_parser import InstagramParser

# Загружаем переменные окружения из .env файла
load_dotenv()

def print_banner():
    """Печать баннера"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    🖼️  INSTAGRAM PARSER                     ║
║                                                              ║
║  Парсинг Instagram аккаунтов через Apify с сохранением      ║
║  в MongoDB и скачиванием изображений                         ║
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
    default_uri = "mongodb://localhost:27017/"
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

def get_max_images():
    """Получение максимального количества изображений"""
    print(f"\n📥 Максимальное количество изображений для скачивания:")
    print(f"   Рекомендуется: 50-100 для тестирования")
    
    while True:
        try:
            max_images = input("   Количество (Enter для 100): ").strip()
            if not max_images:
                return 100
            max_images = int(max_images)
            if max_images > 0:
                return max_images
            else:
                print("   ❌ Количество должно быть больше 0")
        except ValueError:
            print("   ❌ Введите корректное число")

def confirm_settings(username, max_images, mongodb_uri):
    """Подтверждение настроек"""
    print(f"\n⚙️  НАСТРОЙКИ ПАРСИНГА:")
    print(f"   👤 Пользователь: @{username}")
    print(f"   📥 Макс. изображений: {max_images}")
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
    max_images = get_max_images()
    
    # Подтверждаем настройки
    if not confirm_settings(username, max_images, mongodb_uri):
        print("❌ Парсинг отменен")
        return
    
    # Показываем прогресс
    show_progress()
    
    # Создаем парсер и запускаем
    try:
        parser = InstagramParser(apify_token, mongodb_uri)
        success = parser.run_full_parsing(username, max_images)
        
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
