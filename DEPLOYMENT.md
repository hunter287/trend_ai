# 🚀 Развертывание Linda Sza Gallery на Яндекс Облаке

## 📋 Обзор

Это руководство поможет вам развернуть приложение Linda Sza Gallery на сервере Яндекс Облака с использованием Docker и Nginx.

## 🏗️ Архитектура

- **Приложение**: Python HTTP сервер для обслуживания изображений
- **Nginx**: Прокси-сервер с SSL поддержкой
- **Docker**: Контейнеризация приложения
- **SSL**: Самоподписанные сертификаты (можно заменить на Let's Encrypt)

## 📦 Компоненты

- `production_app.py` - Основное приложение
- `Dockerfile` - Конфигурация Docker контейнера
- `docker-compose.yml` - Оркестрация сервисов
- `nginx.conf` - Конфигурация Nginx
- `deploy.sh` - Скрипт автоматического развертывания
- `linda-sza-gallery.service` - Systemd сервис

## 🚀 Быстрое развертывание

### 1. Подготовка

Убедитесь, что у вас есть:
- SSH ключ для доступа к серверу
- IP адрес сервера Яндекс Облака
- Файлы с данными Instagram (`image_urls_*.json`)

### 2. Запуск развертывания

```bash
# Сделайте скрипт исполняемым
chmod +x deploy.sh

# Запустите развертывание
./deploy.sh [IP_АДРЕС_СЕРВЕРА] [ПУТЬ_К_SSH_КЛЮЧУ]

# Пример:
./deploy.sh 89.169.176.64 ~/.ssh/ssh-key-1756891497220
```

### 3. Проверка

После развертывания ваше приложение будет доступно по адресам:
- **HTTP**: `http://YOUR_SERVER_IP` (редирект на HTTPS)
- **HTTPS**: `https://YOUR_SERVER_IP`
- **Галерея**: `https://YOUR_SERVER_IP/gallery.html`
- **API**: `https://YOUR_SERVER_IP/api/`

## 🔧 Ручное развертывание

### 1. Подключение к серверу

```bash
ssh -i ~/.ssh/ssh-key-1756891497220 styleboxlive@89.169.176.64
```

### 2. Установка Docker

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER
```

### 3. Копирование файлов

```bash
# Создайте директорию
mkdir -p ~/linda-sza-gallery
cd ~/linda-sza-gallery

# Скопируйте файлы с локальной машины
scp -i ~/.ssh/ssh-key-1756891497220 -r ./* styleboxlive@89.169.176.64:~/linda-sza-gallery/
```

### 4. Настройка SSL

```bash
cd ~/linda-sza-gallery
mkdir -p ssl
cd ssl

# Создайте самоподписанный сертификат
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem -out cert.pem \
  -subj '/C=RU/ST=Moscow/L=Moscow/O=Company/CN=YOUR_SERVER_IP'
```

### 5. Запуск приложения

```bash
cd ~/linda-sza-gallery
docker-compose up --build -d
```

## 📊 Управление сервисом

### Просмотр логов

```bash
# Логи всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f app
docker-compose logs -f nginx
```

### Перезапуск

```bash
# Перезапуск всех сервисов
docker-compose restart

# Перезапуск конкретного сервиса
docker-compose restart app
```

### Остановка

```bash
# Остановка всех сервисов
docker-compose down

# Остановка с удалением данных
docker-compose down -v
```

## 🔄 Обновление

### Автоматическое обновление

```bash
# Запустите скрипт развертывания заново
./deploy.sh [IP_АДРЕС_СЕРВЕРА] [ПУТЬ_К_SSH_КЛЮЧУ]
```

### Ручное обновление

```bash
# На сервере
cd ~/linda-sza-gallery
git pull  # если используете git
docker-compose down
docker-compose up --build -d
```

## 🛡️ Безопасность

### Firewall

```bash
# Откройте необходимые порты
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### SSL сертификаты

Для продакшена рекомендуется использовать Let's Encrypt:

```bash
# Установите certbot
sudo apt-get install -y certbot

# Получите сертификат
sudo certbot certonly --standalone -d your-domain.com

# Обновите nginx.conf для использования реальных сертификатов
```

## 📈 Мониторинг

### Systemd сервис

```bash
# Установите systemd сервис
sudo cp linda-sza-gallery.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable linda-sza-gallery
sudo systemctl start linda-sza-gallery

# Управление сервисом
sudo systemctl status linda-sza-gallery
sudo systemctl restart linda-sza-gallery
sudo systemctl stop linda-sza-gallery
```

### Мониторинг ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Использование дискового пространства
df -h
du -sh ~/linda-sza-gallery/images/*
```

## 🐛 Устранение неполадок

### Проблемы с Docker

```bash
# Проверьте статус Docker
sudo systemctl status docker

# Перезапустите Docker
sudo systemctl restart docker

# Очистите неиспользуемые контейнеры
docker system prune -a
```

### Проблемы с Nginx

```bash
# Проверьте конфигурацию
sudo nginx -t

# Перезапустите Nginx
sudo systemctl restart nginx

# Просмотрите логи
sudo tail -f /var/log/nginx/error.log
```

### Проблемы с SSL

```bash
# Проверьте сертификаты
openssl x509 -in ssl/cert.pem -text -noout

# Проверьте подключение
openssl s_client -connect YOUR_SERVER_IP:443
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs -f`
2. Убедитесь, что все порты открыты
3. Проверьте права доступа к файлам
4. Убедитесь, что Docker запущен

## 🔗 Полезные ссылки

- [Docker Documentation](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Яндекс Облако](https://cloud.yandex.ru/)
