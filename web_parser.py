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

app = Flask(__name__, static_folder='images', static_url_path='/images')
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

@app.route('/gallery')
def gallery():
    """Галерея изображений из базы данных"""
    try:
        # Создаем экземпляр парсера для доступа к MongoDB
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )
        
        # Подключаемся к MongoDB
        if not parser.connect_mongodb():
            return "Ошибка подключения к базе данных", 500
        
        # Получаем изображения из базы данных (только не выбранные для теггирования, не скрытые и без тегов Ximilar)
        images = list(parser.collection.find(
            {
                "local_filename": {"$exists": True}, 
                "selected_for_tagging": {"$ne": True},
                "hidden": {"$ne": True},
                "$and": [
                    {"ximilar_tags": {"$exists": False}},
                    {"ximilar_objects_structured": {"$exists": False}}
                ]
            },
            {"_id": 1, "local_filename": 1, "username": 1, "likes_count": 1, "comments_count": 1, "caption": 1, "selected_for_tagging": 1}
        ).sort("parsed_at", -1).limit(100))
        
        return render_template('gallery.html', images=images, current_page='gallery')
    except Exception as e:
        return f"Ошибка: {e}", 500

@app.route('/gallery_to_tag')
def gallery_to_tag():
    """Галерея изображений, выбранных для теггирования"""
    try:
        # Создаем экземпляр парсера для доступа к MongoDB
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )
        
        # Подключаемся к MongoDB
        if not parser.connect_mongodb():
            return "Ошибка подключения к базе данных", 500
        
        # Получаем изображения, выбранные для теггирования (только не скрытые и без тегов Ximilar)
        images = list(parser.collection.find(
            {
                "local_filename": {"$exists": True}, 
                "selected_for_tagging": True,
                "hidden": {"$ne": True},
                "$and": [
                    {"ximilar_tags": {"$exists": False}},
                    {"ximilar_objects_structured": {"$exists": False}}
                ]
            },
            {"_id": 1, "local_filename": 1, "username": 1, "likes_count": 1, "comments_count": 1, "caption": 1, "selected_for_tagging": 1, "selected_at": 1}
        ).sort("selected_at", -1).limit(100))
        
        return render_template('gallery.html', images=images, current_page='gallery_to_tag')
    except Exception as e:
        return f"Ошибка: {e}", 500

@app.route('/gallery_tagged')
def gallery_tagged():
    """Галерея изображений с тегами Ximilar"""
    try:
        # Создаем экземпляр парсера для доступа к MongoDB
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )
        
        # Подключаемся к MongoDB
        if not parser.connect_mongodb():
            return "Ошибка подключения к базе данных", 500
        
        # Получаем изображения с тегами Ximilar (только не скрытые, приоритет объектно-ориентированной структуре)
        images = list(parser.collection.find(
            {
                "local_filename": {"$exists": True},
                "hidden": {"$ne": True},
                "$or": [
                    {"ximilar_objects_structured": {"$exists": True, "$ne": []}},
                    {"ximilar_tags": {"$exists": True, "$ne": []}}
                ]
            },
            {
                "_id": 1, "local_filename": 1, "username": 1, "likes_count": 1, 
                "comments_count": 1, "caption": 1, "ximilar_tags": 1, 
                "ximilar_objects_structured": 1, "tagged_at": 1, "ximilar_tagged_at": 1
            }
        ).sort("ximilar_tagged_at", -1).limit(100))
        
        return render_template('gallery.html', images=images, current_page='gallery_tagged')
    except Exception as e:
        return f"Ошибка: {e}", 500

@app.route('/all_accounts_gallery.html')
@app.route('/all_accounts_gallery_page_<int:page>.html')
def serve_combined_gallery(page=1):
    """Обслуживание общей галереи всех аккаунтов"""
    import os
    
    # Определяем имя файла
    if page == 1:
        gallery_file = "all_accounts_gallery.html"
    else:
        gallery_file = f"all_accounts_gallery_page_{page}.html"
    
    if os.path.exists(gallery_file):
        with open(gallery_file, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return f"Общая галерея (страница {page}) не найдена", 404

# Статические файлы теперь обслуживаются автоматически Flask
# через настройку static_folder='images', static_url_path='/images'

@app.route('/api/mark-for-tagging', methods=['POST'])
def api_mark_for_tagging():
    """API для отметки изображений для теггирования"""
    try:
        data = request.get_json()
        image_ids = data.get('image_ids', [])
        
        if not image_ids:
            return jsonify({'success': False, 'message': 'Список ID изображений пуст'})
        
        # Проверяем инициализацию парсера
        success, message = web_parser.init_parser()
        if not success:
            return jsonify({'success': False, 'message': message})
        
        # Подключаемся к MongoDB
        if not web_parser.parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к MongoDB'})
        
        # Обновляем статус изображений
        from bson import ObjectId
        from datetime import datetime
        
        # Преобразуем строковые ID в ObjectId
        object_ids = []
        for img_id in image_ids:
            try:
                object_ids.append(ObjectId(img_id))
            except Exception as e:
                print(f"❌ Ошибка преобразования ID {img_id}: {e}")
                continue
        
        if not object_ids:
            return jsonify({'success': False, 'message': 'Некорректные ID изображений'})
        
        # Обновляем документы в MongoDB
        result = web_parser.parser.collection.update_many(
            {"_id": {"$in": object_ids}},
            {
                "$set": {
                    "selected_for_tagging": True,
                    "selected_at": datetime.now().isoformat()
                }
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Отмечено {result.modified_count} изображений для теггирования',
            'marked_count': result.modified_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

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
                    'images_saved': saved_count or 0,
                    'images_skipped': len(downloaded_data) - (saved_count or 0),
                    'gallery_url': f'/gallery_{account}.html'
                }
                
                socketio.emit('parsing_log', {
                    'message': f'✅ @{account} завершен: {len(downloaded_data)} изображений, сохранено {saved_count or 0}, пропущено дубликатов {len(downloaded_data) - (saved_count or 0)}',
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
        
        # Создаем общую галерею всех аккаунтов
        socketio.emit('parsing_log', {
            'message': f'🌐 Создание общей галереи всех аккаунтов...',
            'timestamp': datetime.now().isoformat()
        }, room=session_id)
        
        try:
            combined_gallery_html = web_parser.parser.create_combined_gallery_html(page=1, per_page=200)
            if combined_gallery_html:
                socketio.emit('parsing_log', {
                    'message': f'✅ Общая галерея создана: /all_accounts_gallery.html',
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
            else:
                socketio.emit('parsing_log', {
                    'message': f'⚠️ Не удалось создать общую галерею',
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
        except Exception as e:
            socketio.emit('parsing_log', {
                'message': f'❌ Ошибка создания общей галереи: {e}',
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
        
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

@app.route('/api/unmark-for-tagging', methods=['POST'])
def api_unmark_for_tagging():
    """API для снятия отметки с изображений для теггирования"""
    try:
        data = request.get_json()
        image_ids = data.get('image_ids', [])
        
        if not image_ids:
            return jsonify({'success': False, 'message': 'Список ID изображений пуст'})
        
        # Проверяем инициализацию парсера
        success, message = web_parser.init_parser()
        if not success:
            return jsonify({'success': False, 'message': message})
        
        # Подключаемся к MongoDB
        if not web_parser.parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к MongoDB'})
        
        # Обновляем статус изображений
        from bson import ObjectId
        
        # Преобразуем строковые ID в ObjectId
        object_ids = []
        for img_id in image_ids:
            try:
                object_ids.append(ObjectId(img_id))
            except Exception as e:
                print(f"❌ Ошибка преобразования ID {img_id}: {e}")
                continue
        
        if not object_ids:
            return jsonify({'success': False, 'message': 'Некорректные ID изображений'})
        
        # Обновляем статус изображений
        result = web_parser.parser.collection.update_many(
            {"_id": {"$in": object_ids}},
            {
                "$set": {
                    "selected_for_tagging": False,
                    "selected_at": None
                }
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Снята отметка с {result.modified_count} изображений',
            'unmarked_count': result.modified_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/hide-images', methods=['POST'])
def api_hide_images():
    """API для скрытия изображений"""
    try:
        data = request.get_json()
        image_ids = data.get('image_ids', [])
        
        if not image_ids:
            return jsonify({'success': False, 'message': 'Список ID изображений пуст'})
        
        # Проверяем инициализацию парсера
        success, message = web_parser.init_parser()
        if not success:
            return jsonify({'success': False, 'message': message})
        
        # Подключаемся к MongoDB
        if not web_parser.parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к MongoDB'})
        
        # Обновляем статус изображений
        from bson import ObjectId
        from datetime import datetime
        
        # Преобразуем строковые ID в ObjectId
        object_ids = []
        for img_id in image_ids:
            try:
                object_ids.append(ObjectId(img_id))
            except Exception as e:
                print(f"❌ Ошибка преобразования ID {img_id}: {e}")
                continue
        
        if not object_ids:
            return jsonify({'success': False, 'message': 'Некорректные ID изображений'})
        
        # Обновляем документы в MongoDB - помечаем как скрытые
        result = web_parser.parser.collection.update_many(
            {"_id": {"$in": object_ids}},
            {
                "$set": {
                    "hidden": True,
                    "hidden_at": datetime.now().isoformat()
                }
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Скрыто {result.modified_count} изображений',
            'hidden_count': result.modified_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/filter-options', methods=['GET'])
def api_filter_options():
    """API для получения доступных опций фильтрации"""
    try:
        # Проверяем инициализацию парсера
        success, message = web_parser.init_parser()
        if not success:
            return jsonify({'success': False, 'message': message})
        
        # Подключаемся к MongoDB
        if not web_parser.parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к MongoDB'})
        
        # Получаем все изображения с тегами Ximilar (исключаем скрытые)
        images = list(web_parser.parser.collection.find(
            {
                "local_filename": {"$exists": True},
                "hidden": {"$ne": True},
                "$or": [
                    {"ximilar_objects_structured": {"$exists": True, "$ne": []}},
                    {"ximilar_tags": {"$exists": True, "$ne": []}}
                ]
            },
            {"ximilar_objects_structured": 1}
        ))
        
        # Собираем уникальные значения для фильтров с подсчетом (по одному разу на изображение)
        categories = {}
        objects = {}
        colors = {}
        materials = {}
        styles = {}
        
        for image in images:
            if image.get('ximilar_objects_structured'):
                # Собираем уникальные теги для этого изображения
                image_categories = set()
                image_objects = set()
                image_colors = set()
                image_materials = set()
                image_styles = set()
                
                # Сначала дедуплицируем объекты по их основному названию
                # Это поможет избежать подсчета одинаковых объектов с разными атрибутами
                unique_objects_by_name = {}
                
                for obj in image['ximilar_objects_structured']:
                    # Получаем основное название объекта
                    obj_name = None
                    if obj.get('properties'):
                        if obj['properties'].get('other_attributes'):
                            if obj['properties']['other_attributes'].get('Subcategory'):
                                obj_name = obj['properties']['other_attributes']['Subcategory'][0]['name']
                            elif obj['properties']['other_attributes'].get('Category'):
                                obj_name = obj['properties']['other_attributes']['Category'][0]['name']
                    
                    # Если объект с таким названием уже есть, пропускаем
                    if obj_name and obj_name in unique_objects_by_name:
                        continue
                    
                    # Сохраняем первый объект с этим названием
                    if obj_name:
                        unique_objects_by_name[obj_name] = obj
                
                # Теперь собираем теги только из уникальных объектов
                for obj in unique_objects_by_name.values():
                    # Категории
                    if obj.get('top_category'):
                        image_categories.add(obj['top_category'])
                    
                    # Объекты (из Subcategory или Category)
                    if obj.get('properties'):
                        if obj['properties'].get('other_attributes'):
                            if obj['properties']['other_attributes'].get('Subcategory'):
                                for sub in obj['properties']['other_attributes']['Subcategory']:
                                    image_objects.add(sub['name'])
                            elif obj['properties']['other_attributes'].get('Category'):
                                for cat in obj['properties']['other_attributes']['Category']:
                                    image_objects.add(cat['name'])
                    
                    # Цвета
                    if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                        for color in obj['properties']['visual_attributes']['Color']:
                            image_colors.add(color['name'])
                    
                    # Материалы
                    if obj.get('properties', {}).get('material_attributes', {}).get('Material'):
                        for material in obj['properties']['material_attributes']['Material']:
                            image_materials.add(material['name'])
                    
                    # Стили
                    if obj.get('properties', {}).get('style_attributes', {}).get('Style'):
                        for style in obj['properties']['style_attributes']['Style']:
                            image_styles.add(style['name'])
                
                # Считаем только уникальные теги этого изображения
                # (уже собраны в sets выше)
                
                # Добавляем уникальные теги этого изображения к общему счетчику
                for cat in image_categories:
                    categories[cat] = categories.get(cat, 0) + 1
                
                for obj in image_objects:
                    objects[obj] = objects.get(obj, 0) + 1
                
                for color in image_colors:
                    colors[color] = colors.get(color, 0) + 1
                
                for material in image_materials:
                    materials[material] = materials.get(material, 0) + 1
                
                for style in image_styles:
                    styles[style] = styles.get(style, 0) + 1
        
        # Отладочная информация
        print(f"🔍 DEBUG: Найдено {len(images)} изображений с тегами")
        print(f"📊 Категории: {len(categories)} уникальных")
        print(f"📊 Объекты: {len(objects)} уникальных")
        print(f"📊 Цвета: {len(colors)} уникальных")
        print(f"📊 Материалы: {len(materials)} уникальных")
        print(f"📊 Стили: {len(styles)} уникальных")
        
        return jsonify({
            'success': True,
            'filter_options': {
                'categories': sorted([f"{cat} ({count})" for cat, count in categories.items()]),
                'objects': sorted([f"{obj} ({count})" for obj, count in objects.items()]),
                'colors': sorted([f"{color} ({count})" for color, count in colors.items()]),
                'materials': sorted([f"{material} ({count})" for material, count in materials.items()]),
                'styles': sorted([f"{style} ({count})" for style, count in styles.items()])
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/tag-images', methods=['POST'])
def api_tag_images():
    """API для теггирования изображений через Ximilar"""
    try:
        data = request.get_json()
        image_ids = data.get('image_ids', [])
        
        if not image_ids:
            return jsonify({'success': False, 'message': 'Список ID изображений пуст'})
        
        # Проверяем инициализацию парсера
        success, message = web_parser.init_parser()
        if not success:
            return jsonify({'success': False, 'message': message})
        
        # Подключаемся к MongoDB
        if not web_parser.parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к MongoDB'})
        
        from bson import ObjectId
        
        # Преобразуем строковые ID в ObjectId
        object_ids = []
        for img_id in image_ids:
            try:
                object_ids.append(ObjectId(img_id))
            except Exception as e:
                print(f"❌ Ошибка преобразования ID {img_id}: {e}")
                continue
        
        if not object_ids:
            return jsonify({'success': False, 'message': 'Некорректные ID изображений'})
        
        # Получаем изображения из базы данных
        images = list(web_parser.parser.collection.find(
            {"_id": {"$in": object_ids}},
            {"_id": 1, "local_filename": 1, "local_path": 1}
        ))
        
        if not images:
            return jsonify({'success': False, 'message': 'Изображения не найдены в базе данных'})
        
        # Создаем экземпляр Ximilar теггера
        from ximilar_fashion_tagger import XimilarFashionTagger
        ximilar_api_key = os.getenv("XIMILAR_API_KEY")
        
        if not ximilar_api_key:
            return jsonify({'success': False, 'message': 'XIMILAR_API_KEY не найден в переменных окружения'})
        
        tagger = XimilarFashionTagger(ximilar_api_key, web_parser.parser.mongodb_uri)
        
        # Подключаемся к MongoDB
        if not tagger.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к MongoDB для теггирования'})
        
        # Теггируем изображения через Ximilar
        tagged_count = 0
        for image in images:
            try:
                # Формируем URL изображения
                image_url = f"http://158.160.19.119:5000/images/{image['local_filename']}"
                
                # Используем существующую функциональность теггирования
                tags_result = tagger.tag_image_with_ximilar(image_url)
                
                if tags_result and 'success' in tags_result and tags_result['success']:
                    # Обновляем документ в базе данных с объектно-ориентированной структурой
                    update_data = {
                        "ximilar_objects_structured": tags_result.get("objects", []),
                        "ximilar_properties_summary": tags_result.get("properties_summary", {}),
                        "ximilar_tags": tags_result.get("tags", []),
                        "ximilar_objects": tags_result.get("objects", []),
                        "ximilar_total_tags": tags_result.get("total_tags", 0),
                        "ximilar_total_objects": tags_result.get("total_objects", 0),
                        "ximilar_tagged_at": datetime.now().isoformat(),
                        "ximilar_success": tags_result.get("success", False),
                        "tagged_at": datetime.now().isoformat(),
                        "selected_for_tagging": False  # Убираем из списка для теггирования
                    }
                    
                    if not tags_result.get("success"):
                        update_data["ximilar_error"] = tags_result.get("error", "Unknown error")
                    
                    web_parser.parser.collection.update_one(
                        {"_id": image['_id']},
                        {"$set": update_data}
                    )
                    tagged_count += 1
                    print(f"✅ Изображение {image['local_filename']} оттегировано")
                else:
                    print(f"❌ Не удалось оттегировать {image['local_filename']}")
                    
            except Exception as e:
                print(f"❌ Ошибка теггирования {image['local_filename']}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'message': f'Оттегировано {tagged_count} из {len(images)} изображений',
            'tagged_count': tagged_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

if __name__ == '__main__':
    print("🌐 ЗАПУСК ВЕБ-ИНТЕРФЕЙСА ДЛЯ ПАРСИНГА INSTAGRAM")
    print("="*60)
    print("📡 Сервер: http://0.0.0.0:5000")
    print("🔗 WebSocket: ws://0.0.0.0:5000/socket.io/")
    print("="*60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
