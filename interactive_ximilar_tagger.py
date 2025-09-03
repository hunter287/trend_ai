#!/usr/bin/env python3
"""
Интерактивный Ximilar Fashion Tagger
"""

import os
from dotenv import load_dotenv
from ximilar_fashion_tagger import XimilarFashionTagger

# Загружаем переменные окружения
load_dotenv()

def print_banner():
    """Печать баннера"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    🏷️  XIMILAR FASHION TAGGING            ║
║                                                              ║
║  Автоматическое тегирование одежды в изображениях          ║
║  через Ximilar Fashion API с сохранением в MongoDB          ║
╚══════════════════════════════════════════════════════════════╝
    """)

def get_ximilar_token():
    """Получение токена Ximilar"""
    token = os.getenv("XIMILAR_API_KEY")
    if not token:
        print("❌ Не найден XIMILAR_API_KEY в переменных окружения")
        print("💡 Установите токен:")
        print("   export XIMILAR_API_KEY=your_token")
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

def get_batch_settings():
    """Получение настроек пакетной обработки"""
    print(f"\n⚙️ Настройки пакетной обработки:")
    
    # Максимум изображений
    while True:
        try:
            max_images = input("   Максимум изображений (Enter для 50): ").strip()
            if not max_images:
                max_images = 50
            else:
                max_images = int(max_images)
            if max_images > 0:
                break
            else:
                print("   ❌ Количество должно быть больше 0")
        except ValueError:
            print("   ❌ Введите корректное число")
    
    # Размер пакета
    while True:
        try:
            batch_size = input("   Размер пакета (Enter для 10): ").strip()
            if not batch_size:
                batch_size = 10
            else:
                batch_size = int(batch_size)
            if batch_size > 0:
                break
            else:
                print("   ❌ Размер должен быть больше 0")
        except ValueError:
            print("   ❌ Введите корректное число")
    
    return max_images, batch_size

def confirm_settings(max_images, batch_size, mongodb_uri):
    """Подтверждение настроек"""
    print(f"\n⚙️  НАСТРОЙКИ ТЕГИРОВАНИЯ:")
    print(f"   📊 Максимум изображений: {max_images}")
    print(f"   📦 Размер пакета: {batch_size}")
    print(f"   🗄️  MongoDB URI: {mongodb_uri}")
    
    # Оценка времени
    estimated_time = max_images * 2  # Примерно 2 секунды на изображение
    if estimated_time < 60:
        time_str = f"{estimated_time} секунд"
    else:
        time_str = f"{estimated_time//60} минут {estimated_time%60} секунд"
    
    print(f"   ⏱️  Ожидаемое время: {time_str}")
    
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
    print(f"\n🔄 ПРОЦЕСС ТЕГИРОВАНИЯ:")
    print(f"   1. 🔍 Поиск изображений без тегов")
    print(f"   2. 🏷️  Тегирование через Ximilar API")
    print(f"   3. 💾 Сохранение тегов в MongoDB")
    print(f"   4. 📊 Показ статистики")
    print(f"   " + "="*50)

def main():
    """Главная функция"""
    print_banner()
    
    # Проверяем токен Ximilar
    ximilar_token = get_ximilar_token()
    if not ximilar_token:
        return
    
    # Получаем настройки
    mongodb_uri = get_mongodb_uri()
    max_images, batch_size = get_batch_settings()
    
    # Подтверждаем настройки
    if not confirm_settings(max_images, batch_size, mongodb_uri):
        print("❌ Тегирование отменено")
        return
    
    # Показываем прогресс
    show_progress()
    
    # Создаем теггер и запускаем
    try:
        tagger = XimilarFashionTagger(ximilar_token, mongodb_uri)
        
        # Показываем текущую статистику
        print(f"\n📊 ТЕКУЩАЯ СТАТИСТИКА:")
        tagger.get_tagged_images_stats()
        
        # Запускаем тегирование
        print(f"\n🚀 ЗАПУСК ТЕГИРОВАНИЯ...")
        success = tagger.tag_batch_images(batch_size, max_images)
        
        if success:
            print(f"\n🎉 ТЕГИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print(f"📊 Обновленная статистика:")
            tagger.get_tagged_images_stats()
        else:
            print(f"\n❌ ОШИБКА ПРИ ТЕГИРОВАНИИ")
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Тегирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    main()
