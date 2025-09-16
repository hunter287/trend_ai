# Настройка MongoDB с аутентификацией на сервере

## 1. Создание пользователя MongoDB

Выполните на сервере:

```bash
# Подключиться к MongoDB
mongosh

# В MongoDB shell выполнить:
use admin
db.createUser({
  user: "trend_ai_user",
  pwd: "|#!x1K52H.0{8d3",
  roles: [
    { role: "readWrite", db: "instagram_gallery" },
    { role: "readWrite", db: "admin" }
  ]
})
```

Или через командную строку:
```bash
mongosh --eval "
use admin
db.createUser({
  user: 'trend_ai_user',
  pwd: '|#!x1K52H.0{8d3',
  roles: [
    { role: 'readWrite', db: 'instagram_gallery' },
    { role: 'readWrite', db: 'admin' }
  ]
})
"
```

## 2. Настройка конфигурации

Скопируйте файл конфигурации:
```bash
cp mongodb_config.env.example mongodb_config.env
```

Файл `mongodb_config.env` уже содержит правильные настройки с паролем.

## 3. Проверка подключения

```bash
# Активировать виртуальное окружение
source apify_env/bin/activate

# Проверить подключение
python check_mongodb.py
```

## 4. Команды для управления MongoDB

```bash
# Статус MongoDB
sudo systemctl status mongod

# Запуск MongoDB
sudo systemctl start mongod

# Остановка MongoDB
sudo systemctl stop mongod

# Перезапуск MongoDB
sudo systemctl restart mongod

# Включить автозапуск
sudo systemctl enable mongod
```

## 5. Проверка пользователей

```bash
# Подключиться к MongoDB
mongosh

# В MongoDB shell:
use admin
db.system.users.find()  # посмотреть всех пользователей
```

## 6. URI для подключения

Все скрипты теперь используют URI:
```
mongodb://trend_ai_user:|#!x1K52H.0{8d3@localhost:27017/instagram_gallery
```

Пароль: `|#!x1K52H.0{8d3`
