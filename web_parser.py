#!/usr/bin/env python3
"""
Веб-интерфейс для парсинга Instagram аккаунтов
"""

import os
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from instagram_parser import InstagramParser

# Загружаем переменные окружения
load_dotenv()
load_dotenv('mongodb_config.env')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

# Глобальные переменные для отслеживания процессов
active_parsing_sessions = {}

class WebParser:
    def __init__(self):
        self.apify_token = os.getenv("APIFY_API_TOKEN")
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        self.parser = None
        
    def init_parser(self):
        """Инициализация парсера"""
        if not self.apify_token:
            return False, "APIFY_API_TOKEN не найден"
        
        try:
            self.parser = InstagramParser(self.apify_token, self.mongodb_uri)
            return True, "Парсер инициализирован"
        except Exception as e:
            return False, f"Ошибка инициализации парсера: {e}"

web_parser = WebParser()

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """API статуса"""
    success, message = web_parser.init_parser()
    return jsonify({
        'success': success,
        'message': message,
        'active_sessions': len(active_parsing_sessions)
    })

@app.route('/api/parse', methods=['POST'])
def api_parse():
    """API для запуска парсинга"""
    try:
        data = request.get_json()
        accounts = data.get('accounts', [])
        max_posts = data.get('max_posts', 20)
        session_id = data.get('session_id', f"session_{int(time.time())}")
        
        if not accounts:
            return jsonify({'success': False, 'message': 'Список аккаунтов пуст'})
        
        # Проверяем инициализацию парсера
        success, message = web_parser.init_parser()
        if not success:
            return jsonify({'success': False, 'message': message})
        
        # Сначала регистрируем сессию
        active_parsing_sessions[session_id] = {
            'status': 'starting',
            'accounts': accounts,
            'max_posts': max_posts,
            'started_at': datetime.now().isoformat(),
            'progress': 0,
            'current_account': None,
            'results': []
        }
        
        # Затем запускаем парсинг в отдельном потоке
        thread = threading.Thread(
            target=run_parsing_session,
            args=(session_id, accounts, max_posts)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Парсинг запущен',
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/session/<session_id>')
def api_session_status(session_id):
    """API статуса сессии"""
    if session_id in active_parsing_sessions:
        return jsonify(active_parsing_sessions[session_id])
    else:
        return jsonify({'error': 'Сессия не найдена'})

@app.route('/api/sessions')
def api_sessions():
    """API списка активных сессий"""
    return jsonify({
        'sessions': list(active_parsing_sessions.keys()),
        'count': len(active_parsing_sessions)
    })

@app.route('/gallery_<username>.html')
def serve_gallery(username):
    """Обслуживание HTML галерей"""
    import os
    gallery_file = f"gallery_{username}.html"
    if os.path.exists(gallery_file):
        with open(gallery_file, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return f"Галерея для @{username} не найдена", 404

@app.route('/images/<filename>')
def serve_image(filename):
    """Обслуживание изображений"""
    from flask import send_from_directory
    import os
    
    # Проверяем, существует ли папка с изображениями
    images_dir = "instagram_images"
    if os.path.exists(images_dir):
        return send_from_directory(images_dir, filename)
    else:
        return "Изображение не найдено", 404

def run_parsing_session(session_id, accounts, max_posts):
    """Запуск парсинга в отдельном потоке"""
    session_data = None
    try:
        # Небольшая задержка для гарантии регистрации сессии
        time.sleep(0.1)
        
        # Проверяем, что сессия существует
        if session_id not in active_parsing_sessions:
            print(f"⚠️ Сессия {session_id} не найдена в активных сессиях")
            print(f"Доступные сессии: {list(active_parsing_sessions.keys())}")
            return
        
        session_data = active_parsing_sessions[session_id]
        session_data['status'] = 'running'
        
        # Подключаемся к MongoDB
        if not web_parser.parser.connect_mongodb():
            session_data['status'] = 'error'
            session_data['error'] = 'Ошибка подключения к MongoDB'
            socketio.emit('parsing_update', session_data, room=session_id)
            return
        
        total_accounts = len(accounts)
        results = []
        
        for i, account in enumerate(accounts):
            try:
                # Обновляем статус
                session_data['current_account'] = account
                session_data['progress'] = int((i / total_accounts) * 100)
                socketio.emit('parsing_update', session_data, room=session_id)
                
                # Парсим аккаунт
                socketio.emit('parsing_log', {
                    'message': f'🔍 Парсинг аккаунта: @{account}',
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
                
                parsed_data = web_parser.parser.parse_instagram_account(account, max_posts)
                if not parsed_data:
                    socketio.emit('parsing_log', {
                        'message': f'❌ Ошибка парсинга @{account}',
                        'timestamp': datetime.now().isoformat()
                    }, room=session_id)
                    continue
                
                # Извлекаем URL изображений
                image_data = web_parser.parser.extract_image_urls(parsed_data["posts"])
                if not image_data:
                    socketio.emit('parsing_log', {
                        'message': f'❌ Нет изображений в @{account}',
                        'timestamp': datetime.now().isoformat()
                    }, room=session_id)
                    continue
                
                # Скачиваем изображения
                socketio.emit('parsing_log', {
                    'message': f'⬇️ Скачивание изображений из @{account}...',
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
                
                downloaded_data = web_parser.parser.download_images(image_data, 999999)  # Без ограничений
                
                # Сохраняем в MongoDB
                socketio.emit('parsing_log', {
                    'message': f'💾 Сохранение в MongoDB...',
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
                
                saved_count = web_parser.parser.save_to_mongodb(downloaded_data, account)
                
                # Создаем HTML галерею
                socketio.emit('parsing_log', {
                    'message': f'🌐 Создание HTML галереи...',
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
                
                web_parser.parser.create_gallery_html(downloaded_data, account)
                
                result = {
                    'account': account,
                    'success': True,
                    'images_downloaded': len(downloaded_data),
                    'images_saved': saved_count,
                    'gallery_url': f'/gallery_{account}.html'
                }
                
                socketio.emit('parsing_log', {
                    'message': f'✅ @{account} завершен: {len(downloaded_data)} изображений',
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
                
            except Exception as e:
                result = {
                    'account': account,
                    'success': False,
                    'error': str(e)
                }
                
                socketio.emit('parsing_log', {
                    'message': f'❌ Ошибка @{account}: {e}',
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
            
            results.append(result)
            session_data['results'] = results
        
        # Завершаем сессию
        session_data['status'] = 'completed'
        session_data['progress'] = 100
        session_data['completed_at'] = datetime.now().isoformat()
        socketio.emit('parsing_complete', session_data, room=session_id)
        
        # Удаляем сессию через 5 минут
        threading.Timer(300, lambda: active_parsing_sessions.pop(session_id, None)).start()
        
    except Exception as e:
        if session_data is not None:
            session_data['status'] = 'error'
            session_data['error'] = str(e)
            socketio.emit('parsing_error', session_data, room=session_id)
        else:
            # Если сессия не найдена, создаем временную запись об ошибке
            error_data = {
                'session_id': session_id,
                'status': 'error',
                'error': f'Сессия не найдена: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            socketio.emit('parsing_error', error_data, room=session_id)

@socketio.on('connect')
def handle_connect():
    """Обработка подключения WebSocket"""
    print(f'Клиент подключен: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    """Обработка отключения WebSocket"""
    print(f'Клиент отключен: {request.sid}')

@socketio.on('join_session')
def handle_join_session(data):
    """Присоединение к сессии парсинга"""
    from flask_socketio import join_room
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        print(f'Клиент присоединился к сессии: {session_id}')

if __name__ == '__main__':
    print("🌐 ЗАПУСК ВЕБ-ИНТЕРФЕЙСА ДЛЯ ПАРСИНГА INSTAGRAM")
    print("="*60)
    print("📡 Сервер: http://0.0.0.0:5000")
    print("🔗 WebSocket: ws://0.0.0.0:5000/socket.io/")
    print("="*60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
