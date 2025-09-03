# 🖼️ Instagram Parser через Apify

Комплексный инструмент для парсинга Instagram аккаунтов с сохранением в MongoDB и скачиванием изображений.

## 🚀 Возможности

- **Парсинг Instagram аккаунтов** через Apify API
- **Автоматическое удаление дубликатов** изображений
- **Скачивание изображений** в локальную папку
- **Сохранение в MongoDB** с метаданными
- **Создание HTML галереи** для просмотра
- **Интерактивный интерфейс** командной строки

## 📋 Требования

- Python 3.7+
- Apify API токен
- MongoDB (локально или удаленно)
- Интернет соединение

## 🛠️ Установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/hunter287/trend_ai.git
cd trend_ai
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка Apify токена
```bash
# Создайте .env файл
echo "APIFY_API_TOKEN=your_apify_token_here" > .env

# Или экспортируйте переменную
export APIFY_API_TOKEN=your_apify_token_here
```

### 4. Установка MongoDB (на сервере)
```bash
# Автоматическая установка
python setup_mongodb.py

# Или вручную
sudo apt-get update
sudo apt-get install -y mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

## 🎯 Использование

### Интерактивный режим (рекомендуется)
```bash
python interactive_parser.py
```

### Командная строка
```bash
# Базовое использование
python instagram_parser.py username

# С параметрами
python instagram_parser.py linda.sza --max-images 50 --mongodb-uri mongodb://localhost:27017/
```

### Параметры командной строки
- `username` - имя пользователя Instagram (обязательно)
- `--max-images` - максимальное количество изображений (по умолчанию: 100)
- `--mongodb-uri` - URI MongoDB (по умолчанию: mongodb://localhost:27017/)

## 📊 Структура данных в MongoDB

### Коллекция: `images`

```json
{
  "_id": ObjectId("..."),
  "instagram_url": "https://www.instagram.com/username/",
  "username": "username",
  "image_url": "https://scontent-xxx.cdninstagram.com/...",
  "post_id": "ABC123",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "likes_count": 1500,
  "comments_count": 50,
  "caption": "Описание поста...",
  "image_type": "main",
  "local_filename": "ABC123_main_0001.jpg",
  "local_path": "/path/to/images/ABC123_main_0001.jpg",
  "file_size": 245760,
  "parsed_at": "2024-01-01T12:00:00.000Z",
  "downloaded_at": "2024-01-01T12:00:00.000Z"
}
```

## 📁 Структура файлов

```
trend_ai/
├── instagram_parser.py      # Основной парсер
├── interactive_parser.py    # Интерактивный интерфейс
├── setup_mongodb.py         # Установка MongoDB
├── requirements.txt         # Python зависимости
├── .env                     # Переменные окружения
├── images/                  # Скачанные изображения
├── gallery_username.html    # HTML галерея
└── INSTAGRAM_PARSER_README.md
```

## 🔧 Настройка

### MongoDB
```bash
# Локальная установка
mongodb://localhost:27017/

# Удаленная установка
mongodb://username:password@host:port/database

# MongoDB Atlas
mongodb+srv://username:password@cluster.mongodb.net/database
```

### Apify
1. Зарегистрируйтесь на [Apify.com](https://apify.com)
2. Получите API токен в [настройках аккаунта](https://console.apify.com/account/integrations)
3. Добавьте токен в `.env` файл или экспортируйте переменную

## 📈 Примеры использования

### Парсинг одного аккаунта
```bash
python interactive_parser.py
# Введите: linda.sza
# Выберите: 50 изображений
```

### Парсинг нескольких аккаунтов
```bash
python instagram_parser.py linda.sza --max-images 100
python instagram_parser.py another_user --max-images 50
```

### Работа с MongoDB
```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["instagram_gallery"]
collection = db["images"]

# Найти все изображения пользователя
images = collection.find({"username": "linda.sza"})

# Найти изображения за определенный период
from datetime import datetime
images = collection.find({
    "timestamp": {
        "$gte": "2024-01-01T00:00:00.000Z",
        "$lt": "2024-02-01T00:00:00.000Z"
    }
})
```

## 🚨 Ограничения

- **Instagram блокировки**: Apify может быть заблокирован Instagram
- **Лимиты API**: Соблюдайте лимиты Apify API
- **Размер данных**: Большие аккаунты могут генерировать много данных
- **Скорость**: Парсинг может занять время для больших аккаунтов

## 🐛 Устранение неполадок

### Ошибка "Empty or private data"
- Аккаунт может быть приватным
- Instagram заблокировал Apify
- Попробуйте другой аккаунт

### Ошибка подключения к MongoDB
```bash
# Проверьте статус MongoDB
sudo systemctl status mongodb

# Перезапустите MongoDB
sudo systemctl restart mongodb

# Проверьте подключение
python -c "import pymongo; pymongo.MongoClient('mongodb://localhost:27017/').admin.command('ping')"
```

### Ошибка Apify токена
```bash
# Проверьте токен
echo $APIFY_API_TOKEN

# Установите токен
export APIFY_API_TOKEN=your_token_here
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи ошибок
2. Убедитесь в правильности настроек
3. Проверьте подключение к интернету
4. Убедитесь в работоспособности Apify и MongoDB

## 🔗 Полезные ссылки

- [Apify Instagram Scraper](https://apify.com/apify/instagram-scraper)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [Apify Python Client](https://docs.apify.com/api/client/python)
