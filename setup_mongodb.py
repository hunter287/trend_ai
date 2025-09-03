"""
Скрипт для установки и настройки MongoDB
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Выполнение команды с описанием"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ошибка: {e}")
        print(f"   Вывод: {e.stdout}")
        print(f"   Ошибка: {e.stderr}")
        return False

def install_mongodb():
    """Установка MongoDB"""
    print("📦 УСТАНОВКА MONGODB")
    print("="*40)
    
    # Обновляем пакеты
    if not run_command("sudo apt-get update", "Обновление списка пакетов"):
        return False
    
    # Устанавливаем MongoDB
    if not run_command("sudo apt-get install -y mongodb", "Установка MongoDB"):
        return False
    
    # Запускаем MongoDB
    if not run_command("sudo systemctl start mongodb", "Запуск MongoDB"):
        return False
    
    # Включаем автозапуск
    if not run_command("sudo systemctl enable mongodb", "Включение автозапуска MongoDB"):
        return False
    
    # Проверяем статус
    if not run_command("sudo systemctl status mongodb --no-pager", "Проверка статуса MongoDB"):
        return False
    
    print("✅ MongoDB установлен и запущен")
    return True

def install_python_dependencies():
    """Установка Python зависимостей"""
    print("\n🐍 УСТАНОВКА PYTHON ЗАВИСИМОСТЕЙ")
    print("="*40)
    
    # Устанавливаем pymongo
    if not run_command("pip install pymongo", "Установка pymongo"):
        return False
    
    print("✅ Python зависимости установлены")
    return True

def test_mongodb_connection():
    """Тестирование подключения к MongoDB"""
    print("\n🔍 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К MONGODB")
    print("="*40)
    
    test_script = """
import pymongo
try:
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["test_db"]
    collection = db["test_collection"]
    
    # Тест записи
    test_doc = {"test": "data", "timestamp": "2024-01-01"}
    result = collection.insert_one(test_doc)
    print(f"✅ Запись в MongoDB: {result.inserted_id}")
    
    # Тест чтения
    found_doc = collection.find_one({"test": "data"})
    print(f"✅ Чтение из MongoDB: {found_doc}")
    
    # Очистка тестовых данных
    collection.delete_one({"test": "data"})
    print("✅ Тестовые данные удалены")
    
    print("✅ Подключение к MongoDB работает корректно")
    
except Exception as e:
    print(f"❌ Ошибка подключения к MongoDB: {e}")
    exit(1)
"""
    
    try:
        exec(test_script)
        return True
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def create_mongodb_user():
    """Создание пользователя MongoDB (опционально)"""
    print("\n👤 СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ MONGODB")
    print("="*40)
    
    username = input("Введите имя пользователя MongoDB (Enter для пропуска): ").strip()
    if not username:
        print("⏭️  Создание пользователя пропущено")
        return True
    
    password = input("Введите пароль: ").strip()
    if not password:
        print("❌ Пароль не может быть пустым")
        return False
    
    # Создаем пользователя
    create_user_script = f"""
use admin
db.createUser({{
    user: "{username}",
    pwd: "{password}",
    roles: [{{ role: "readWrite", db: "instagram_gallery" }}]
}})
"""
    
    try:
        result = subprocess.run(
            ["mongosh", "--eval", create_user_script],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Пользователь {username} создан")
            return True
        else:
            print(f"❌ Ошибка создания пользователя: {result.stderr}")
            return False
    except FileNotFoundError:
        print("⚠️  mongosh не найден, пользователь не создан")
        return True

def main():
    """Главная функция"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    🗄️  MONGODB SETUP                       ║
║                                                              ║
║  Установка и настройка MongoDB для Instagram Parser         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Проверяем, что мы на Linux
    if sys.platform != "linux":
        print("❌ Этот скрипт предназначен для Linux")
        return
    
    # Устанавливаем MongoDB
    if not install_mongodb():
        print("❌ Ошибка установки MongoDB")
        return
    
    # Устанавливаем Python зависимости
    if not install_python_dependencies():
        print("❌ Ошибка установки Python зависимостей")
        return
    
    # Тестируем подключение
    if not test_mongodb_connection():
        print("❌ Ошибка тестирования MongoDB")
        return
    
    # Создаем пользователя (опционально)
    create_mongodb_user()
    
    print(f"\n🎉 MONGODB НАСТРОЕН УСПЕШНО!")
    print(f"📊 Информация:")
    print(f"   • URI: mongodb://localhost:27017/")
    print(f"   • База данных: instagram_gallery")
    print(f"   • Коллекция: images")
    print(f"   • Статус: Запущен и готов к работе")
    
    print(f"\n💡 Теперь можете запустить Instagram Parser:")
    print(f"   python interactive_parser.py")

if __name__ == "__main__":
    main()
