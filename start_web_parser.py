#!/usr/bin/env python3
"""
Скрипт запуска веб-интерфейса для парсинга Instagram
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
load_dotenv('mongodb_config.env')

def check_requirements():
    """Проверка требований"""
    print("🔍 Проверка требований...")
    
    # Проверяем APIFY_API_TOKEN
    if not os.getenv("APIFY_API_TOKEN"):
        print("❌ APIFY_API_TOKEN не найден в переменных окружения")
        print("💡 Добавьте в .env файл: APIFY_API_TOKEN=your_token")
        return False
    
    # Проверяем MONGODB_URI
    if not os.getenv("MONGODB_URI"):
        print("❌ MONGODB_URI не найден в переменных окружения")
        print("💡 Добавьте в mongodb_config.env файл: MONGODB_URI=your_uri")
        return False
    
    print("✅ Все требования выполнены")
    return True

def install_dependencies():
    """Установка зависимостей"""
    print("📦 Установка зависимостей...")
    
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Зависимости установлены")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False

def main():
    """Главная функция"""
    print("🌐 ЗАПУСК ВЕБ-ИНТЕРФЕЙСА ДЛЯ ПАРСИНГА INSTAGRAM")
    print("="*60)
    
    # Проверяем требования
    if not check_requirements():
        return
    
    # Устанавливаем зависимости
    if not install_dependencies():
        return
    
    print("\n🚀 Запуск веб-сервера...")
    print("📡 Веб-интерфейс будет доступен по адресу: http://0.0.0.0:5000")
    print("🔗 WebSocket: ws://0.0.0.0:5000/socket.io/")
    print("\n💡 Для остановки нажмите Ctrl+C")
    print("="*60)
    
    # Запускаем веб-приложение
    try:
        from web_parser import app, socketio
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Веб-сервер остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка запуска веб-сервера: {e}")

if __name__ == "__main__":
    main()

