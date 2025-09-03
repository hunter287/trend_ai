#!/bin/bash

# Скрипт развертывания через Git на Яндекс Облаке
# Использование: ./git-deploy.sh [server_ip] [ssh_key_path] [git_repo_url]

set -e

# Параметры
SERVER_IP=${1:-"89.169.176.64"}
SSH_KEY=${2:-"~/.ssh/ssh-key-1756891497220"}
GIT_REPO=${3:-""}
USER="styleboxlive"
APP_NAME="linda-sza-gallery"
APP_DIR="/home/$USER/$APP_NAME"

echo "🚀 РАЗВЕРТЫВАНИЕ ЧЕРЕЗ GIT НА ЯНДЕКС ОБЛАКО"
echo "=========================================="
echo "📡 Сервер: $SERVER_IP"
echo "🔑 SSH ключ: $SSH_KEY"
echo "📦 Git репозиторий: $GIT_REPO"
echo "👤 Пользователь: $USER"
echo "📁 Директория: $APP_DIR"
echo ""

# Функция для выполнения команд на сервере
run_remote() {
    ssh -i "$SSH_KEY" "$USER@$SERVER_IP" "$@"
}

# Функция для копирования файлов на сервер
copy_to_server() {
    scp -i "$SSH_KEY" -r "$1" "$USER@$SERVER_IP:$2"
}

echo "🔧 ПОДГОТОВКА СЕРВЕРА..."
echo "------------------------"

# Обновляем систему и устанавливаем необходимые пакеты
echo "📦 Установка системных пакетов..."
run_remote "sudo apt-get update && sudo apt-get install -y git docker.io docker-compose nginx"

# Добавляем пользователя в группу docker
echo "👥 Настройка прав пользователя..."
run_remote "sudo usermod -aG docker $USER"

# Создаем директорию приложения
echo "📁 Создание директории приложения..."
run_remote "mkdir -p $APP_DIR"

echo ""
echo "📤 НАСТРОЙКА GIT РЕПОЗИТОРИЯ..."
echo "-------------------------------"

if [ -n "$GIT_REPO" ]; then
    # Клонируем репозиторий
    echo "📥 Клонирование репозитория..."
    run_remote "cd $APP_DIR && git clone $GIT_REPO ."
else
    # Копируем файлы локально
    echo "📄 Копирование файлов..."
    copy_to_server "." "$APP_DIR/"
    
    # Инициализируем Git на сервере
    echo "🔧 Инициализация Git репозитория на сервере..."
    run_remote "cd $APP_DIR && git init && git add . && git commit -m 'Initial commit'"
fi

echo ""
echo "🔐 НАСТРОЙКА SSL..."
echo "-------------------"

# Создаем необходимые директории
echo "📁 Создание директорий..."
run_remote "mkdir -p $APP_DIR/ssl $APP_DIR/images $APP_DIR/data"

# Создаем самоподписанный SSL сертификат
echo "🔒 Генерация SSL сертификата..."
run_remote "cd $APP_DIR/ssl && openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem -subj '/C=RU/ST=Moscow/L=Moscow/O=Company/CN=$SERVER_IP'"

echo ""
echo "🐳 ЗАПУСК ПРИЛОЖЕНИЯ..."
echo "------------------------"

# Останавливаем старые контейнеры
echo "🛑 Остановка старых контейнеров..."
run_remote "cd $APP_DIR && docker-compose down || true"

# Собираем и запускаем новые контейнеры
echo "🔨 Сборка и запуск контейнеров..."
run_remote "cd $APP_DIR && docker-compose up --build -d"

echo ""
echo "⚙️ НАСТРОЙКА SYSTEMD СЕРВИСА..."
echo "-------------------------------"

# Копируем systemd сервис
echo "📄 Настройка systemd сервиса..."
run_remote "sudo cp $APP_DIR/linda-sza-gallery.service /etc/systemd/system/"

# Перезагружаем systemd и включаем сервис
echo "🔄 Активация сервиса..."
run_remote "sudo systemctl daemon-reload && sudo systemctl enable linda-sza-gallery"

echo ""
echo "⏳ ОЖИДАНИЕ ЗАПУСКА..."
echo "----------------------"

# Ждем запуска сервисов
sleep 10

# Проверяем статус контейнеров
echo "📊 Статус контейнеров:"
run_remote "cd $APP_DIR && docker-compose ps"

# Проверяем статус systemd сервиса
echo "📊 Статус systemd сервиса:"
run_remote "sudo systemctl status linda-sza-gallery --no-pager"

echo ""
echo "🌐 ПРОВЕРКА ДОСТУПНОСТИ..."
echo "--------------------------"

# Проверяем доступность сервисов
echo "🔍 Проверка HTTP (должен редиректить на HTTPS):"
curl -I "http://$SERVER_IP" || echo "❌ HTTP недоступен"

echo ""
echo "🔍 Проверка HTTPS:"
curl -k -I "https://$SERVER_IP" || echo "❌ HTTPS недоступен"

echo ""
echo "🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
echo "=========================="
echo "🌐 Ваше приложение доступно по адресам:"
echo "   • HTTP:  http://$SERVER_IP (редирект на HTTPS)"
echo "   • HTTPS: https://$SERVER_IP"
echo "   • Галерея: https://$SERVER_IP/gallery.html"
echo "   • API: https://$SERVER_IP/api/"
echo ""
echo "📋 ПОЛЕЗНЫЕ КОМАНДЫ:"
echo "   • Просмотр логов: ssh -i $SSH_KEY $USER@$SERVER_IP 'cd $APP_DIR && docker-compose logs -f'"
echo "   • Перезапуск: ssh -i $SSH_KEY $USER@$SERVER_IP 'cd $APP_DIR && docker-compose restart'"
echo "   • Остановка: ssh -i $SSH_KEY $USER@$SERVER_IP 'cd $APP_DIR && docker-compose down'"
echo "   • Обновление через Git: ssh -i $SSH_KEY $USER@$SERVER_IP 'cd $APP_DIR && git pull && docker-compose up --build -d'"
echo ""
echo "🔄 ОБНОВЛЕНИЕ ЧЕРЕЗ GIT:"
echo "   • Локально: git push origin main"
echo "   • На сервере: ssh -i $SSH_KEY $USER@$SERVER_IP 'cd $APP_DIR && git pull && docker-compose up --build -d'"
echo ""
echo "🔧 УПРАВЛЕНИЕ СЕРВИСОМ:"
echo "   • Статус: systemctl status linda-sza-gallery"
echo "   • Запуск: systemctl start linda-sza-gallery"
echo "   • Остановка: systemctl stop linda-sza-gallery"
