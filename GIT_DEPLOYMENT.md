# 🚀 Развертывание через Git на Яндекс Облаке

## 📋 Обзор

Это руководство описывает процесс развертывания Linda Sza Gallery на сервере Яндекс Облака с использованием Git для управления версиями и автоматического развертывания.

## 🏗️ Архитектура развертывания

```
Локальная машина → Git репозиторий → Сервер Яндекс Облака
     ↓                    ↓                    ↓
  Разработка          Версионирование      Автоматическое
  и тестирование      и хранение кода      развертывание
```

## 🚀 Быстрое развертывание

### 1. Подготовка локального репозитория

```bash
# Инициализация Git (уже сделано)
git init

# Добавление файлов
git add .

# Первый коммит
git commit -m "Initial commit: Linda Sza Gallery application"

# Добавление удаленного репозитория (если используете GitHub/GitLab)
git remote add origin https://github.com/yourusername/linda-sza-gallery.git
git push -u origin main
```

### 2. Развертывание на сервере

```bash
# Сделайте скрипт исполняемым
chmod +x git-deploy.sh

# Запустите развертывание
./git-deploy.sh [IP_АДРЕС_СЕРВЕРА] [ПУТЬ_К_SSH_КЛЮЧУ] [URL_GIT_РЕПОЗИТОРИЯ]

# Пример с GitHub:
./git-deploy.sh 89.169.176.64 ~/.ssh/ssh-key-1756891497220 https://github.com/yourusername/linda-sza-gallery.git

# Пример без Git репозитория (копирование файлов):
./git-deploy.sh 89.169.176.64 ~/.ssh/ssh-key-1756891497220
```

## 🔄 Процесс обновления

### Вариант 1: Ручное обновление

```bash
# Локально - вносите изменения и коммитьте
git add .
git commit -m "Update: описание изменений"
git push origin main

# На сервере - обновляйте приложение
ssh -i ~/.ssh/ssh-key-1756891497220 styleboxlive@89.169.176.64
cd /home/styleboxlive/linda-sza-gallery
git pull origin main
docker-compose up --build -d
```

### Вариант 2: Автоматическое обновление

```bash
# Локально - вносите изменения и коммитьте
git add .
git commit -m "Update: описание изменений"
git push origin main

# На сервере - запустите скрипт обновления
ssh -i ~/.ssh/ssh-key-1756891497220 styleboxlive@89.169.176.64
cd /home/styleboxlive/linda-sza-gallery
./server-update.sh
```

### Вариант 3: Git Hooks (полностью автоматическое)

```bash
# На сервере - настройте Git hook
ssh -i ~/.ssh/ssh-key-1756891497220 styleboxlive@89.169.176.64
cd /home/styleboxlive/linda-sza-gallery
chmod +x hooks/post-receive

# Локально - просто пушите изменения
git add .
git commit -m "Update: описание изменений"
git push origin main
# Приложение автоматически обновится на сервере!
```

## 📁 Структура проекта

```
linda-sza-gallery/
├── production_app.py          # Основное приложение
├── Dockerfile                 # Конфигурация Docker
├── docker-compose.yml         # Оркестрация сервисов
├── nginx.conf                 # Конфигурация Nginx
├── git-deploy.sh              # Скрипт развертывания
├── server-update.sh           # Скрипт обновления
├── linda-sza-gallery.service  # Systemd сервис
├── hooks/
│   └── post-receive           # Git hook для авторазвертывания
├── .gitignore                 # Исключения для Git
├── requirements.txt           # Python зависимости
└── README.md                  # Документация
```

## 🔧 Настройка Git репозитория

### GitHub

1. Создайте репозиторий на GitHub
2. Добавьте удаленный репозиторий:
   ```bash
   git remote add origin https://github.com/yourusername/linda-sza-gallery.git
   git push -u origin main
   ```

### GitLab

1. Создайте репозиторий на GitLab
2. Добавьте удаленный репозиторий:
   ```bash
   git remote add origin https://gitlab.com/yourusername/linda-sza-gallery.git
   git push -u origin main
   ```

### Локальный Git (без удаленного репозитория)

Если не хотите использовать внешний Git сервис, можете развернуть напрямую:

```bash
./git-deploy.sh 89.169.176.64 ~/.ssh/ssh-key-1756891497220
```

## 🛡️ Безопасность

### SSH ключи

```bash
# Проверьте права доступа к SSH ключу
chmod 600 ~/.ssh/ssh-key-1756891497220

# Проверьте подключение
ssh -i ~/.ssh/ssh-key-1756891497220 styleboxlive@89.169.176.64
```

### Firewall

```bash
# На сервере откройте необходимые порты
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

## 📊 Мониторинг

### Логи приложения

```bash
# Просмотр логов Docker контейнеров
ssh -i ~/.ssh/ssh-key-1756891497220 styleboxlive@89.169.176.64
cd /home/styleboxlive/linda-sza-gallery
docker-compose logs -f

# Просмотр логов systemd сервиса
sudo journalctl -u linda-sza-gallery -f
```

### Статус сервисов

```bash
# Статус Docker контейнеров
docker-compose ps

# Статус systemd сервиса
sudo systemctl status linda-sza-gallery

# Использование ресурсов
docker stats
```

## 🐛 Устранение неполадок

### Проблемы с Git

```bash
# Проверьте статус Git
git status

# Проверьте удаленный репозиторий
git remote -v

# Принудительное обновление
git fetch origin
git reset --hard origin/main
```

### Проблемы с Docker

```bash
# Очистка Docker
docker system prune -a

# Перезапуск Docker
sudo systemctl restart docker

# Проверка конфигурации
docker-compose config
```

### Проблемы с развертыванием

```bash
# Проверьте права доступа
ls -la /home/styleboxlive/linda-sza-gallery

# Проверьте логи
tail -f /var/log/syslog

# Ручной запуск
cd /home/styleboxlive/linda-sza-gallery
docker-compose up --build -d
```

## 🔗 Полезные команды

### Локальная разработка

```bash
# Добавление изменений
git add .
git commit -m "Описание изменений"
git push origin main

# Откат изменений
git reset --hard HEAD~1

# Просмотр истории
git log --oneline
```

### Управление сервером

```bash
# Подключение к серверу
ssh -i ~/.ssh/ssh-key-1756891497220 styleboxlive@89.169.176.64

# Обновление приложения
cd /home/styleboxlive/linda-sza-gallery
git pull origin main
docker-compose up --build -d

# Перезапуск сервиса
sudo systemctl restart linda-sza-gallery

# Остановка приложения
docker-compose down
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs -f`
2. Убедитесь, что Git репозиторий доступен
3. Проверьте права доступа к файлам
4. Убедитесь, что Docker запущен
5. Проверьте статус systemd сервиса

## 🎯 Следующие шаги

1. **Настройте CI/CD** с GitHub Actions или GitLab CI
2. **Добавьте мониторинг** с помощью Prometheus/Grafana
3. **Настройте резервное копирование** данных
4. **Добавьте SSL сертификаты** Let's Encrypt
5. **Настройте домен** вместо IP адреса
