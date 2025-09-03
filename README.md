# 🚀 Apify API - Практическое руководство

Этот проект демонстрирует, как использовать Apify API для веб-скрапинга и автоматизации с помощью Python.

## 📋 Что такое Apify?

**Apify** - это платформа для веб-скрапинга и автоматизации, которая предоставляет:

- 🎭 **Готовые акторы** - готовые решения для скрапинга популярных сайтов
- 🔧 **API** - для управления акторами и получения данных
- 💾 **Хранилища данных** - Dataset, Key-value store, Request queue
- ☁️ **Облачная инфраструктура** - не нужно настраивать серверы

## 🏗️ Структура проекта

```
trend_ai/
├── requirements.txt          # Зависимости Python
├── env_example.txt          # Пример файла с переменными окружения
├── simple_example.py        # Простой пример для начала
├── apify_examples.py        # Полный пример с классом ApifyManager
├── scraping_example.py      # Практические примеры скрапинга
└── README.md               # Этот файл
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Получение API токена

1. Зарегистрируйтесь на [Apify Console](https://console.apify.com/)
2. Перейдите в [Account → Integrations](https://console.apify.com/account/integrations)
3. Скопируйте ваш API токен

### 3. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
# Скопируйте содержимое из env_example.txt
cp env_example.txt .env
```

Отредактируйте `.env` файл:

```env
APIFY_API_TOKEN=ваш_токен_здесь
```

### 4. Запуск простого примера

```bash
python simple_example.py
```

## 📚 Примеры использования

### Простой пример (`simple_example.py`)

Базовые операции с Apify API:

```python
from apify_client import ApifyClient

# Создание клиента
client = ApifyClient('ваш_токен')

# Получение информации о пользователе
user = client.user().get()

# Список акторов
actors = client.actors().list(limit=10)
```

### Полный пример (`apify_examples.py`)

Класс `ApifyManager` с полным функционалом:

```python
from apify_examples import ApifyManager

# Инициализация
apify = ApifyManager()

# Получение информации о пользователе
apify.get_user_info()

# Список акторов
actors = apify.list_actors(limit=5)

# Запуск актора
run_id = apify.run_actor('actor_id', input_data)

# Ожидание завершения
run_info = apify.wait_for_run_completion(run_id)

# Получение результатов
items = apify.get_dataset_items(dataset_id)
```

### Практические примеры скрапинга (`scraping_example.py`)

Готовые примеры для популярных сайтов:

```python
from scraping_example import ApifyScraper

scraper = ApifyScraper()

# Google Shopping
results = scraper.scrape_google_shopping(['laptop', 'smartphone'])

# Instagram профили
results = scraper.scrape_instagram_profiles(['username1', 'username2'])

# LinkedIn компании
results = scraper.scrape_linkedin_companies(['microsoft', 'google'])

# Twitter профили
results = scraper.scrape_twitter_profiles(['elonmusk', 'twitter'])
```

## 🎭 Популярные акторы Apify

### Веб-скрапинг
- `apify/google-shopping-scraper` - Google Shopping
- `apify/instagram-profile-scraper` - Instagram профили
- `apify/linkedin-company-scraper` - LinkedIn компании
- `apify/twitter-profile-scraper` - Twitter профили
- `apify/amazon-scraper` - Amazon товары
- `apify/ebay-scraper` - eBay товары

### Социальные сети
- `apify/facebook-scraper` - Facebook посты и профили
- `apify/tiktok-scraper` - TikTok видео
- `apify/youtube-scraper` - YouTube видео и каналы

### Новости и контент
- `apify/news-scraper` - Новостные сайты
- `apify/blog-scraper` - Блоги и статьи
- `apify/reddit-scraper` - Reddit посты

## 🔧 Основные концепции

### Actor (Актор)
Программа, которая выполняется на платформе Apify. Может быть готовой или созданной вами.

### Run (Запуск)
Конкретное выполнение актора с определенными входными данными.

### Dataset
Хранилище структурированных данных (результаты скрапинга).

### Key-value Store
Хранилище ключ-значение для любых данных.

### Request Queue
Очередь запросов для актора.

## 📊 Работа с данными

### Получение данных из Dataset

```python
# Получение всех элементов
dataset_items = client.dataset('dataset_id').list_items()
items = dataset_items.items

# Получение с лимитом
dataset_items = client.dataset('dataset_id').list_items(limit=100)

# Получение в формате JSON
json_data = client.dataset('dataset_id').list_items().items
```

### Сохранение в файлы

```python
import pandas as pd
import json

# В CSV
df = pd.DataFrame(items)
df.to_csv('results.csv', index=False)

# В JSON
with open('results.json', 'w') as f:
    json.dump(items, f, indent=2)
```

## 💰 Стоимость

Apify использует кредитную систему:

- **Бесплатный план**: 5,000 платформенных единиц в месяц
- **Платные планы**: от $49/месяц
- **Платформенные единицы**: зависят от сложности актора и объема данных

## 🛠️ Создание собственного актора

### 1. Установка Apify CLI

```bash
npm install -g apify-cli
```

### 2. Создание нового актора

```bash
apify create my-actor
cd my-actor
```

### 3. Разработка

```javascript
// main.js
const Apify = require('apify');

Apify.main(async () => {
    const input = await Apify.getInput();
    
    // Ваш код скрапинга
    const results = await scrapeWebsite(input.url);
    
    // Сохранение результатов
    await Apify.pushData(results);
});
```

### 4. Деплой

```bash
apify deploy
```

## 🔍 Мониторинг и отладка

### Просмотр логов

```python
# Получение логов запуска
logs = client.run('run_id').log().get()
print(logs)
```

### Статус запуска

```python
run_info = client.run('run_id').get()
status = run_info.get('status')
print(f"Статус: {status}")
```

## 🚨 Обработка ошибок

```python
try:
    run = client.actor('actor_id').call(input_data)
except Exception as e:
    print(f"Ошибка запуска актора: {e}")
    
try:
    items = client.dataset('dataset_id').list_items()
except Exception as e:
    print(f"Ошибка получения данных: {e}")
```

## 📈 Лучшие практики

1. **Используйте таймауты** для ожидания завершения акторов
2. **Обрабатывайте ошибки** при работе с API
3. **Сохраняйте данные** в разных форматах
4. **Мониторьте использование** платформенных единиц
5. **Используйте готовые акторы** когда возможно

## 🔗 Полезные ссылки

- [Apify Console](https://console.apify.com/)
- [Apify API Documentation](https://docs.apify.com/api/v2)
- [Apify Actors](https://apify.com/store)
- [Apify SDK](https://sdk.apify.com/)
- [Apify CLI](https://docs.apify.com/cli)

## 🤝 Поддержка

Если у вас есть вопросы:

1. [Apify Documentation](https://docs.apify.com/)
2. [Apify Community](https://community.apify.com/)
3. [GitHub Issues](https://github.com/apify/apify-js/issues)

---

**Удачного скрапинга! 🕷️**
