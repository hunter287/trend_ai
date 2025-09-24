#!/usr/bin/env python3
"""
Тестирование общей галереи с выбором изображений для теггирования
"""

import os
from dotenv import load_dotenv
from instagram_parser import InstagramParser

# Загружаем переменные окружения
load_dotenv()
load_dotenv('mongodb_config.env')

def test_combined_gallery():
    """Тестирование создания общей галереи"""
    print("🧪 ТЕСТИРОВАНИЕ ОБЩЕЙ ГАЛЕРЕИ")
    print("="*50)
    
    # Инициализация парсера
    apify_token = os.getenv("APIFY_API_TOKEN")
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
    
    if not apify_token:
        print("❌ APIFY_API_TOKEN не найден")
        return
    
    parser = InstagramParser(apify_token, mongodb_uri)
    
    # Подключаемся к MongoDB
    if not parser.connect_mongodb():
        print("❌ Ошибка подключения к MongoDB")
        return
    
    print("🌐 Создание общей галереи...")
    html_content = parser.create_combined_gallery_html(page=1, per_page=200)
    
    if html_content:
        print("✅ Общая галерея создана успешно!")
        print(f"📄 Размер HTML: {len(html_content)} символов")
        print("🔗 Откройте файл all_accounts_gallery.html в браузере для просмотра")
        print("\n📋 Функции галереи:")
        print("  • Чекбоксы для выбора изображений")
        print("  • Кнопка 'Выбрать все'")
        print("  • Счетчик выбранных изображений")
        print("  • Кнопка 'Отметить для теггирования'")
        print("  • Фильтрация по аккаунтам")
        print("  • Пагинация (200 фото на страницу)")
        print("  • Минималистичный дизайн")
    else:
        print("❌ Ошибка создания общей галереи")

if __name__ == "__main__":
    test_combined_gallery()
