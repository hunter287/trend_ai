# MongoDB Web Viewer

Веб-интерфейс для просмотра данных MongoDB с аутентификацией и ограничениями по IP.

## Возможности

- 📊 Просмотр всех коллекций в базе данных `instagram_gallery`
- 📄 Отображение количества документов в каждой коллекции
- 🔍 Примеры документов (первые 3 документа)
- 🔒 Ограничение доступа по IP-адресам
- 🎨 Современный и удобный интерфейс
- 🔄 API для получения данных

## Установка

### 1. Установить зависимости

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Установить Flask
pip install flask
```

### 2. Настроить IP-адреса

Отредактируйте файл `mongo_web_viewer.py` и измените список разрешенных IP:

```python
ALLOWED_IPS = ['127.0.0.1', 'YOUR_IP_1', 'YOUR_IP_2']
```

### 3. Запуск

```bash
# Ручной запуск
python mongo_web_viewer.py

# Или через systemd (автозапуск)
sudo cp mongo-web-viewer.service /etc/systemd/system/
sudo systemctl enable mongo-web-viewer
sudo systemctl start mongo-web-viewer
sudo systemctl status mongo-web-viewer
```

## Доступ

Откройте браузер и перейдите по адресу:
```
http://YOUR_SERVER_IP:8081
```

## API

### Получить список коллекций
```
GET /api/collections
```

Ответ:
```json
{
  "images": {"count": 150},
  "users": {"count": 25}
}
```

## Безопасность

- ✅ Ограничение доступа по IP-адресам
- ✅ Аутентификация через MongoDB
- ✅ Безопасное отображение данных
- ✅ Обработка ошибок

## Логи

```bash
# Просмотр логов systemd
sudo journalctl -u mongo-web-viewer -f

# Просмотр логов приложения
tail -f /var/log/mongo-web-viewer.log
```

## Управление сервисом

```bash
# Запуск
sudo systemctl start mongo-web-viewer

# Остановка
sudo systemctl stop mongo-web-viewer

# Перезапуск
sudo systemctl restart mongo-web-viewer

# Статус
sudo systemctl status mongo-web-viewer

# Отключить автозапуск
sudo systemctl disable mongo-web-viewer
```

## Настройка файрвола

```bash
# Разрешить доступ к порту 8081
sudo ufw allow 8081

# Или только с определенных IP
sudo ufw allow from YOUR_IP to any port 8081
```

## Требования

- Python 3.7+
- Flask 3.0.0
- PyMongo 4.6.0
- MongoDB с аутентификацией
