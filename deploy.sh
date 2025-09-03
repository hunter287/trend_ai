#!/bin/bash

# Скрипт развертывания на Яндекс Облаке
# Использование: ./deploy.sh [server_ip] [ssh_key_path]

set -e

# Параметры
SERVER_IP=${1:-"89.169.176.64"}
SSH_KEY=${2:-"~/.ssh/ssh-key-1756891497220"}
USER="styleboxlive"
APP_NAME="linda-sza-gallery"
APP_DIR="/home/$USER/$APP_NAME"

echo "🚀 РАЗВЕРТЫВАНИЕ НА ЯНДЕКС ОБЛАКО"
echo "=================================="
echo "📡 Сервер: $SERVER_IP"
echo "🔑 SSH ключ: $SSH_KEY"
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

# Обновляем систему и устанавливаем Docker
echo "📦 Установка Docker..."
run_remote "sudo apt-get update && sudo apt-get install -y docker.io docker-compose"

# Добавляем пользователя в группу docker
echo "👥 Настройка прав пользователя..."
run_remote "sudo usermod -aG docker $USER"

# Создаем директорию приложения
echo "📁 Создание директории приложения..."
run_remote "mkdir -p $APP_DIR"

echo ""
echo "📤 КОПИРОВАНИЕ ФАЙЛОВ..."
echo "------------------------"

# Копируем файлы приложения
echo "📄 Копирование исходного кода..."
copy_to_server "." "$APP_DIR/"

# Создаем необходимые директории на сервере
echo "📁 Создание директорий..."
run_remote "mkdir -p $APP_DIR/images $APP_DIR/data $APP_DIR/ssl"

echo ""
echo "🔐 НАСТРОЙКА SSL..."
echo "-------------------"

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
echo "⏳ ОЖИДАНИЕ ЗАПУСКА..."
echo "----------------------"

# Ждем запуска сервисов
sleep 10

# Проверяем статус контейнеров
echo "📊 Статус контейнеров:"
run_remote "cd $APP_DIR && docker-compose ps"

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
echo "   • Обновление: ./deploy.sh $SERVER_IP $SSH_KEY"
echo ""
echo "🔧 УПРАВЛЕНИЕ СЕРВИСОМ:"
echo "   • Статус: systemctl status linda-sza-gallery"
echo "   • Запуск: systemctl start linda-sza-gallery"
echo "   • Остановка: systemctl stop linda-sza-gallery"
