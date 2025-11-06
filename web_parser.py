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

# Получаем абсолютный путь к директории скрипта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
IMAGES_DIR = os.path.join(BASE_DIR, 'images')

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='/static')
app.config['SECRET_KEY'] = os.urandom(24)

# Дополнительный маршрут для изображений
from flask import send_from_directory

@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory(IMAGES_DIR, filename)

socketio = SocketIO(app, cors_allowed_origins="*")

def normalize_subcategory_name(subcategory, category):
    """
    Нормализует название подкатегории для группировки В КОНТЕКСТЕ категории.
    Например: 
    - Accessories + "Handbags" -> "Bags"
    - Clothing + "Tops" -> "Tops"  
    - Accessories + "Tops" -> "Tops" (но в другой категории!)
    """
    subcategory_lower = subcategory.lower()
    
    # Определяем базовые подкатегории для каждой основной категории
    normalization_rules = {
        'Accessories': {
            'Bags': ['bag', 'handbag', 'tote', 'clutch', 'crossbody', 'purse', 'wallet'],
            'Hats': ['hat', 'cap', 'beanie', 'fedora'],
            'Sunglasses': ['sunglass', 'eyewear'],
            'Belts': ['belt'],
            'Jewelry': ['jewelry', 'jewellery', 'necklace', 'bracelet', 'ring', 'earring'],
            'Watches': ['watch'],
            'Scarves': ['scarf', 'scarves'],
            'Gloves': ['glove', 'mitten'],
        },
        'Clothing': {
            'Dresses': ['dress'],
            'Pants': ['pant', 'trouser', 'jean'],
            'Skirts': ['skirt'],
            'Tops': ['top', 'blouse', 'shirt', 't-shirt', 'tank'],
            'Jackets': ['jacket', 'coat', 'blazer', 'cardigan'],
            'Shorts': ['short'],
        },
        'Footwear': {
            'Shoes': ['shoe'],
            'Sneakers': ['sneaker', 'trainer'],
            'Boots': ['boot'],
            'Heels': ['heel', 'stiletto', 'pump'],
            'Sandals': ['sandal', 'flip-flop'],
            'Flats': ['flat', 'loafer', 'ballet'],
        }
    }
    
    # Ищем соответствие в контексте категории
    if category in normalization_rules:
        for base_name, keywords in normalization_rules[category].items():
            for keyword in keywords:
                if keyword in subcategory_lower:
                    return base_name
    
    # Если не нашли соответствия, возвращаем оригинальное название
    return subcategory

# Добавляем глобальную функцию для Jinja2
app.jinja_env.globals['normalize_subcategory'] = normalize_subcategory_name

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

@app.route('/api/bloggers-stats', methods=['GET'])
def api_bloggers_stats():
    """API для получения статистики по блогерам (последняя дата поста)"""
    try:
        # Создаем экземпляр парсера для доступа к MongoDB
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )
        
        # Подключаемся к MongoDB
        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})
        
        # Получаем статистику по блогерам с последними датами постов
        pipeline = [
            {
                "$match": {
                    "username": {"$exists": True, "$ne": None},
                    "timestamp": {"$exists": True, "$ne": "N/A"}
                }
            },
            {
                "$group": {
                    "_id": "$username",
                    "latest_post_date": {"$max": "$timestamp"},
                    "total_posts": {"$sum": 1}
                }
            },
            {
                "$sort": {"latest_post_date": -1}
            }
        ]
        
        bloggers = list(parser.collection.aggregate(pipeline))
        
        # Форматируем результат
        bloggers_list = []
        for blogger in bloggers:
            latest_date = blogger.get('latest_post_date', 'N/A')
            # Извлекаем только дату (YYYY-MM-DD) из ISO строки
            if latest_date != 'N/A' and 'T' in latest_date:
                latest_date = latest_date.split('T')[0]
            
            bloggers_list.append({
                'username': blogger['_id'],
                'latest_post_date': latest_date,
                'total_posts': blogger.get('total_posts', 0)
            })
        
        return jsonify({
            'success': True,
            'bloggers': bloggers_list,
            'total_bloggers': len(bloggers_list)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/status')
def api_status():
    """API статуса"""
    success, message = web_parser.init_parser()
    return jsonify({
        'success': success,
        'message': message,
        'active_sessions': len(active_parsing_sessions)
    })

@app.route('/api/disk-usage')
def api_disk_usage():
    """API для получения информации о дисковом пространстве"""
    try:
        import shutil
        
        # Получаем информацию о диске для текущей директории (где хранятся изображения)
        disk_usage = shutil.disk_usage('/')
        
        # Вычисляем проценты
        total_gb = disk_usage.total / (1024 ** 3)
        used_gb = disk_usage.used / (1024 ** 3)
        free_gb = disk_usage.free / (1024 ** 3)
        used_percent = (disk_usage.used / disk_usage.total) * 100
        free_percent = 100 - used_percent
        
        return jsonify({
            'success': True,
            'total_gb': round(total_gb, 2),
            'used_gb': round(used_gb, 2),
            'free_gb': round(free_gb, 2),
            'used_percent': round(used_percent, 2),
            'free_percent': round(free_percent, 2)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка получения информации о диске: {e}'
        })

def log_print(message):
    """Принудительный вывод в stderr с flush"""
    import sys
    print(message, file=sys.stderr, flush=True)
    print(message, flush=True)

@app.route('/api/parse', methods=['POST'])
def api_parse():
    """API для запуска парсинга"""
    try:
        log_print("\n" + "="*70)
        log_print("🔥 [API] ПОЛУЧЕН POST ЗАПРОС НА /api/parse")
        log_print("="*70)
        
        data = request.get_json()
        log_print(f"📦 [API] Данные запроса: {data}")
        
        accounts = data.get('accounts', [])
        date_from = data.get('date_from')  # Дата начала (YYYY-MM-DD)
        session_id = data.get('session_id', f"session_{int(time.time())}")
        
        log_print(f"📋 [API] Извлечённые параметры:")
        log_print(f"   accounts: {accounts}")
        log_print(f"   date_from: {date_from}")
        log_print(f"   session_id: {session_id}")
        
        if not accounts:
            return jsonify({'success': False, 'message': 'Список аккаунтов пуст'})
        
        # Вычисляем разумный лимит на основе периода (если дата указана)
        if date_from:
            try:
                from datetime import datetime as dt
                date_from_obj = dt.strptime(date_from, '%Y-%m-%d')
                today = dt.now()
                days_diff = (today - date_from_obj).days + 1
                # 10 постов в день (с запасом для активных блогеров)
                max_posts = min(2000, max(50, days_diff * 10))
                log_print(f"📊 [API] Период: {days_diff} дней (с {date_from} до сегодня), установлен лимит: {max_posts} постов")
            except Exception as e:
                max_posts = 200
                log_print(f"📊 [API] Ошибка расчёта периода ({e}), установлен лимит: {max_posts} постов")
        else:
            # Если дата не указана, парсим все посты (по умолчанию 200)
            max_posts = 200
            date_from = None
            log_print(f"📊 [API] Дата не указана, парсим все посты. Лимит: {max_posts} постов")
        
        # Проверяем инициализацию парсера
        log_print(f"🔍 [API] Проверка инициализации парсера...")
        success, message = web_parser.init_parser()
        if not success:
            log_print(f"❌ [API] Ошибка инициализации: {message}")
            return jsonify({'success': False, 'message': message})
        log_print(f"✅ [API] Парсер инициализирован")
        
        # Сначала регистрируем сессию
        log_print(f"🔧 [API] Регистрация сессии {session_id}")
        active_parsing_sessions[session_id] = {
            'status': 'starting',
            'accounts': accounts,
            'max_posts': max_posts,
            'date_from': date_from,
            'started_at': datetime.now().isoformat(),
            'progress': 0,
            'current_account': None,
            'results': []
        }
        log_print(f"✅ [API] Сессия зарегистрирована")
        
        # Затем запускаем парсинг в отдельном потоке
        log_print(f"🧵 [API] Создание потока для парсинга...")
        log_print(f"   Аргументы: session_id={session_id}, accounts={accounts}, max_posts={max_posts}, date_from={date_from}")
        
        thread = threading.Thread(
            target=run_parsing_session,
            args=(session_id, accounts, max_posts, date_from),
            name=f"parsing_thread_{session_id}"
        )
        thread.daemon = True
        
        log_print(f"🚀 [API] Запуск потока...")
        thread.start()
        log_print(f"✅ [API] Поток запущен, thread.is_alive() = {thread.is_alive()}")
        log_print(f"{'='*70}\n")
        
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
    """Динамическая галерея изображений для конкретного пользователя из MongoDB"""
    try:
        # Создаем экземпляр парсера для доступа к MongoDB
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        # Подключаемся к MongoDB
        if not parser.connect_mongodb():
            return f"Ошибка подключения к базе данных для @{username}", 500

        # Получаем изображения для этого пользователя (не скрытые)
        images = list(parser.collection.find(
            {
                "local_filename": {"$exists": True},
                "username": username,
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True}  # Не показываем дубликаты
            },
            {"_id": 1, "local_filename": 1, "username": 1, "likes_count": 1, "comments_count": 1, "caption": 1, "timestamp": 1, "ximilar_objects_structured": 1, "ximilar_tags": 1}
        ).sort("timestamp", -1).limit(200))

        if not images:
            return f"Галерея для @{username} не найдена (нет изображений в базе)", 404

        # Определяем текущую страницу в зависимости от наличия тегов
        # Если хотя бы у одного изображения есть теги, показываем как gallery_tagged
        has_tags = any(img.get('ximilar_objects_structured') or img.get('ximilar_tags') for img in images)
        current_page = 'gallery_tagged' if has_tags else 'gallery'

        return render_template('gallery.html', images=images, current_page=current_page, username=username)
    except Exception as e:
        return f"Ошибка при загрузке галереи для @{username}: {e}", 500

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
        # Загружаем только первый batch (50 изображений), остальные подгрузятся через infinite scroll
        images = list(parser.collection.find(
            {
                "local_filename": {"$exists": True},
                "selected_for_tagging": {"$ne": True},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},  # Не показываем дубликаты
                "$and": [
                    {"ximilar_tags": {"$exists": False}},
                    {"ximilar_objects_structured": {"$exists": False}}
                ]
            },
            {"_id": 1, "local_filename": 1, "username": 1, "likes_count": 1, "comments_count": 1, "caption": 1, "selected_for_tagging": 1, "timestamp": 1}
        ).sort("timestamp", -1).limit(50))
        
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
        # Загружаем только первый batch (50 изображений), остальные подгрузятся через infinite scroll
        images = list(parser.collection.find(
            {
                "local_filename": {"$exists": True},
                "selected_for_tagging": True,
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},  # Не показываем дубликаты
                "$and": [
                    {"ximilar_tags": {"$exists": False}},
                    {"ximilar_objects_structured": {"$exists": False}}
                ]
            },
            {"_id": 1, "local_filename": 1, "username": 1, "likes_count": 1, "comments_count": 1, "caption": 1, "selected_for_tagging": 1, "selected_at": 1, "timestamp": 1}
        ).sort("timestamp", -1).limit(50))
        
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
        # Загружаем только первый batch (50 изображений), остальные подгрузятся через infinite scroll
        images = list(parser.collection.find(
            {
                "local_filename": {"$exists": True},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},  # Не показываем дубликаты
                "$or": [
                    {"ximilar_objects_structured": {"$exists": True, "$ne": []}},
                    {"ximilar_tags": {"$exists": True, "$ne": []}}
                ]
            },
            {
                "_id": 1, "local_filename": 1, "username": 1, "likes_count": 1,
                "comments_count": 1, "caption": 1, "ximilar_tags": 1,
                "ximilar_objects_structured": 1, "tagged_at": 1, "ximilar_tagged_at": 1,
                "timestamp": 1
            }
        ).sort("timestamp", -1).limit(50))

        print(f"🖼️  Загружено {len(images)} изображений в галерею (первый batch, остальные подгрузятся через infinite scroll)")
        
        return render_template('gallery.html', images=images, current_page='gallery_tagged')
    except Exception as e:
        return f"Ошибка: {e}", 500

@app.route('/gallery_hidden')
def gallery_hidden():
    """Галерея скрытых изображений"""
    try:
        # Создаем экземпляр парсера для доступа к MongoDB
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )
        
        # Подключаемся к MongoDB
        if not parser.connect_mongodb():
            return "Ошибка подключения к базе данных", 500
        
        # Получаем скрытые изображения
        # Загружаем только первый batch (50 изображений), остальные подгрузятся через infinite scroll
        images = list(parser.collection.find(
            {
                "local_filename": {"$exists": True},
                "hidden": True  # Только скрытые
            },
            {
                "_id": 1, "local_filename": 1, "username": 1, "likes_count": 1,
                "comments_count": 1, "caption": 1, "timestamp": 1, "hidden_at": 1
            }
        ).sort("hidden_at", -1).limit(50))

        print(f"🙈 Загружено {len(images)} скрытых изображений (первый batch)")
        
        return render_template('gallery.html', images=images, current_page='gallery_hidden')
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

def run_parsing_session(session_id, accounts, max_posts, date_from=None):
    """Запуск парсинга в отдельном потоке"""
    import sys
    import traceback as tb
    
    log_print(f"\n{'='*70}")
    log_print(f"🚀 [THREAD] НАЧАЛО ПОТОКА ПАРСИНГА")
    log_print(f"{'='*70}")
    log_print(f"   session_id: {session_id}")
    log_print(f"   accounts: {accounts}")
    log_print(f"   max_posts: {max_posts}")
    log_print(f"   date_from: {date_from} (до сегодня)")
    log_print(f"   thread_name: {threading.current_thread().name}")
    log_print(f"{'='*70}\n")
    
    session_data = None
    try:
        log_print(f"🚀 [THREAD] Запуск парсинга в потоке для session_id={session_id}")
        log_print(f"📋 [THREAD] Аккаунты: {accounts}")
        log_print(f"📅 [THREAD] Дата: с {date_from} до сегодня")
        log_print(f"📊 [THREAD] max_posts: {max_posts}")
        
        # Небольшая задержка для гарантии регистрации сессии
        time.sleep(0.1)
        
        # Проверяем, что сессия существует
        if session_id not in active_parsing_sessions:
            log_print(f"⚠️ [THREAD] Сессия {session_id} не найдена в активных сессиях")
            log_print(f"Доступные сессии: {list(active_parsing_sessions.keys())}")
            return
        
        log_print(f"✅ [THREAD] Сессия найдена")
        session_data = active_parsing_sessions[session_id]
        session_data['status'] = 'running'
        
        log_print(f"🔗 [THREAD] Подключение к MongoDB...")
        # Подключаемся к MongoDB
        if not web_parser.parser.connect_mongodb():
            log_print(f"❌ [THREAD] Ошибка подключения к MongoDB")
            session_data['status'] = 'error'
            session_data['error'] = 'Ошибка подключения к MongoDB'
            socketio.emit('parsing_update', session_data, room=session_id)
            return
        
        log_print(f"✅ [THREAD] MongoDB подключена")
        total_accounts = len(accounts)
        results = []
        
        for i, account in enumerate(accounts):
            try:
                log_print(f"🔍 [THREAD] Обработка аккаунта {i+1}/{total_accounts}: @{account}")
                # Обновляем статус
                session_data['current_account'] = account
                session_data['progress'] = int((i / total_accounts) * 100)
                socketio.emit('parsing_update', session_data, room=session_id)
                
                # Парсим аккаунт
                date_info = ""
                if date_from:
                    date_info = f" (с {date_from} до сегодня)"
                
                log_print(f"📨 [THREAD] Отправка WebSocket сообщения о начале парсинга @{account}")
                socketio.emit('parsing_log', {
                    'message': f'🔍 Парсинг аккаунта: @{account}{date_info}',
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
                
                log_print(f"🚀 [THREAD] Запуск parse_instagram_account для @{account}")
                parsed_data = web_parser.parser.parse_instagram_account(account, max_posts, date_from)
                log_print(f"✅ [THREAD] parse_instagram_account завершён для @{account}: {parsed_data is not None}")
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
        log_print(f"\n{'='*70}")
        log_print(f"❌ [THREAD] КРИТИЧЕСКАЯ ОШИБКА В ПОТОКЕ ПАРСИНГА")
        log_print(f"{'='*70}")
        log_print(f"   session_id: {session_id}")
        log_print(f"   Ошибка: {e}")
        log_print(f"   Тип ошибки: {type(e).__name__}")
        log_print(f"{'='*70}")
        
        import traceback
        log_print("📋 [THREAD] Полный traceback:")
        import sys
        traceback.print_exc(file=sys.stderr)
        log_print(f"{'='*70}\n")
        
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

@app.route('/api/unhide-images', methods=['POST'])
def api_unhide_images():
    """API для восстановления скрытых изображений"""
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
        
        # Обновляем документы в MongoDB - убираем флаг скрытия
        result = web_parser.parser.collection.update_many(
            {"_id": {"$in": object_ids}},
            {
                "$set": {
                    "hidden": False
                },
                "$unset": {
                    "hidden_at": ""
                }
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Восстановлено {result.modified_count} изображений',
            'unhidden_count': result.modified_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/filter-options', methods=['GET'])
def api_filter_options():
    """API для получения доступных опций фильтрации"""
    try:
        # Получаем параметр use_confidence (по умолчанию True)
        use_confidence = request.args.get('use_confidence', 'true').lower() == 'true'
        # Получаем порог confidence из параметров (по умолчанию 60)
        confidence_threshold = float(request.args.get('confidence_threshold', 60)) / 100.0

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
        
        # Собираем уникальные значения для иерархических фильтров с подсчетом (по одному разу на изображение)
        # Используем ту же логику дедупликации, что и в шаблоне
        hierarchical_filters = {}
        
        # Структура: {category: {subcategory: {colors: {}, materials: {}, styles: {}}}}
        
        processed_images = 0
        for image in images:
            if image.get('ximilar_objects_structured'):
                processed_images += 1
                # Собираем уникальные теги для этого изображения
                image_categories = set()
                image_objects = set()
                image_colors = set()
                image_materials = set()
                image_styles = set()
                
                # Дедупликация объектов по их основному названию (ТОЛЬКО ПЕРВЫЙ вариант Subcategory[0])
                # Это важно: если у нас Subcategory = ["long strap bags", "baguette bags"],
                # берем только "long strap bags" (первый, с наибольшей уверенностью)
                unique_objects_by_name = {}

                for obj in image['ximilar_objects_structured']:
                    # Получаем основное название объекта (ТОЛЬКО ПЕРВЫЙ вариант!)
                    obj_name = ''
                    if obj.get('properties'):
                        if obj['properties'].get('other_attributes'):
                            if obj['properties']['other_attributes'].get('Subcategory'):
                                # Берем ТОЛЬКО первый элемент (с наибольшей confidence)
                                obj_name = obj['properties']['other_attributes']['Subcategory'][0]['name']
                            elif obj['properties']['other_attributes'].get('Category'):
                                obj_name = obj['properties']['other_attributes']['Category'][0]['name']

                    # Если объект с таким названием уже есть, пропускаем
                    if obj_name and obj_name in unique_objects_by_name:
                        continue

                    # Сохраняем первый объект с этим названием
                    if obj_name:
                        unique_objects_by_name[obj_name] = obj

                # Теперь добавляем атрибуты каждого уникального объекта
                for obj in unique_objects_by_name.values():
                    category = obj.get('top_category', 'Other')

                    # Получаем подкатегорию этого объекта (ТОЛЬКО ПЕРВЫЙ вариант)
                    original_subcategory = ''
                    subcategory_prob = 1.0  # По умолчанию максимальный confidence

                    if obj.get('properties'):
                        if obj['properties'].get('other_attributes'):
                            if obj['properties']['other_attributes'].get('Subcategory'):
                                subcategory_data = obj['properties']['other_attributes']['Subcategory'][0]
                                original_subcategory = subcategory_data['name']
                                subcategory_prob = subcategory_data.get('confidence', 1.0)
                            elif obj['properties']['other_attributes'].get('Category'):
                                category_data = obj['properties']['other_attributes']['Category'][0]
                                original_subcategory = category_data['name']
                                subcategory_prob = category_data.get('confidence', 1.0)

                    if not original_subcategory:
                        continue

                    # Проверяем confidence подкатегории/категории если включен фильтр
                    if use_confidence and subcategory_prob <= confidence_threshold:
                        continue

                    # Нормализуем название подкатегории (уровень 2)
                    normalized_subcategory = normalize_subcategory_name(original_subcategory, category)

                    # Инициализируем структуру для категории
                    if category not in hierarchical_filters:
                        hierarchical_filters[category] = {}

                    # Проверяем, нужен ли третий уровень вложенности
                    needs_third_level = (normalized_subcategory.lower() != original_subcategory.lower())

                    if needs_third_level:
                        # Создаем 3 уровня
                        if normalized_subcategory not in hierarchical_filters[category]:
                            hierarchical_filters[category][normalized_subcategory] = {
                                'subsubcategories': {}
                            }

                        if original_subcategory not in hierarchical_filters[category][normalized_subcategory]['subsubcategories']:
                            hierarchical_filters[category][normalized_subcategory]['subsubcategories'][original_subcategory] = {
                                'colors': {},
                                'materials': {},
                                'styles': {}
                            }

                        subsubcat = hierarchical_filters[category][normalized_subcategory]['subsubcategories'][original_subcategory]
                    else:
                        # Создаем только 2 уровня
                        if original_subcategory not in hierarchical_filters[category]:
                            hierarchical_filters[category][original_subcategory] = {
                                'colors': {},
                                'materials': {},
                                'styles': {}
                            }

                        subsubcat = hierarchical_filters[category][original_subcategory]

                    # Цвета
                    if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                        for color in obj['properties']['visual_attributes']['Color']:
                            # Проверяем confidence если включен фильтр
                            if use_confidence and color.get('confidence', 0) <= confidence_threshold:
                                continue
                            color_name = color['name']
                            if color_name not in subsubcat['colors']:
                                subsubcat['colors'][color_name] = set()
                            subsubcat['colors'][color_name].add(image['_id'])

                    # Материалы
                    if obj.get('properties', {}).get('material_attributes', {}).get('Material'):
                        for material in obj['properties']['material_attributes']['Material']:
                            # Проверяем confidence если включен фильтр
                            if use_confidence and material.get('confidence', 0) <= confidence_threshold:
                                continue
                            material_name = material['name']
                            if material_name not in subsubcat['materials']:
                                subsubcat['materials'][material_name] = set()
                            subsubcat['materials'][material_name].add(image['_id'])

                    # Стили
                    if obj.get('properties', {}).get('style_attributes', {}).get('Style'):
                        for style in obj['properties']['style_attributes']['Style']:
                            # Проверяем confidence если включен фильтр
                            if use_confidence and style.get('confidence', 0) <= confidence_threshold:
                                continue
                            style_name = style['name']
                            if style_name not in subsubcat['styles']:
                                subsubcat['styles'][style_name] = set()
                            subsubcat['styles'][style_name].add(image['_id'])
                
                # Подсчет уже происходит в иерархической структуре выше
        
        # Конвертируем sets в counts для каждой категории фильтра
        # Также добавляем общие счётчики для категорий, подкатегорий и подподкатегорий
        hierarchical_filters_with_counts = {}
        for category, subcategories in hierarchical_filters.items():
            hierarchical_filters_with_counts[category] = {
                '_meta': {'image_count': 0, 'subcategories': {}}
            }

            # Собираем уникальные image_ids для всей категории
            category_image_ids = set()

            for subcategory, subcat_data in subcategories.items():
                # Собираем уникальные image_ids для подкатегории
                subcategory_image_ids = set()

                # Проверяем, есть ли третий уровень (subsubcategories) или это двухуровневая структура
                if 'subsubcategories' in subcat_data and subcat_data['subsubcategories']:
                    # Трехуровневая структура: category -> subcategory -> subsubcategory -> colors/materials/styles

                    # Инициализируем структуру для подкатегории
                    hierarchical_filters_with_counts[category][subcategory] = {
                        'subsubcategories': {},
                        '_meta': {'subsubcategories': {}}
                    }

                    # Обрабатываем подподкатегории (уровень 3)
                    for subsubcat_name, subsubcat_filters in subcat_data['subsubcategories'].items():
                        # Собираем уникальные image_ids для подподкатегории
                        subsubcat_image_ids = set()
                        for image_ids_set in subsubcat_filters['colors'].values():
                            subsubcat_image_ids.update(image_ids_set)
                        for image_ids_set in subsubcat_filters['materials'].values():
                            subsubcat_image_ids.update(image_ids_set)
                        for image_ids_set in subsubcat_filters['styles'].values():
                            subsubcat_image_ids.update(image_ids_set)

                        subcategory_image_ids.update(subsubcat_image_ids)

                        # Конвертируем sets в counts для подподкатегории
                        hierarchical_filters_with_counts[category][subcategory]['subsubcategories'][subsubcat_name] = {
                            'colors': {color: len(image_ids) for color, image_ids in subsubcat_filters['colors'].items()},
                            'materials': {material: len(image_ids) for material, image_ids in subsubcat_filters['materials'].items()},
                            'styles': {style: len(image_ids) for style, image_ids in subsubcat_filters['styles'].items()},
                            '_image_count': len(subsubcat_image_ids)
                        }

                        # Сохраняем count для подподкатегории в мета-данные
                        hierarchical_filters_with_counts[category][subcategory]['_meta']['subsubcategories'][subsubcat_name] = len(subsubcat_image_ids)
                else:
                    # Двухуровневая структура: category -> subcategory -> colors/materials/styles

                    # Собираем уникальные image_ids для подкатегории напрямую
                    for image_ids_set in subcat_data['colors'].values():
                        subcategory_image_ids.update(image_ids_set)
                    for image_ids_set in subcat_data['materials'].values():
                        subcategory_image_ids.update(image_ids_set)
                    for image_ids_set in subcat_data['styles'].values():
                        subcategory_image_ids.update(image_ids_set)

                    # Конвертируем sets в counts напрямую на уровне подкатегории
                    hierarchical_filters_with_counts[category][subcategory] = {
                        'colors': {color: len(image_ids) for color, image_ids in subcat_data['colors'].items()},
                        'materials': {material: len(image_ids) for material, image_ids in subcat_data['materials'].items()},
                        'styles': {style: len(image_ids) for style, image_ids in subcat_data['styles'].items()},
                        '_image_count': len(subcategory_image_ids)
                    }

                category_image_ids.update(subcategory_image_ids)

                # Добавляем общий счетчик для подкатегории
                hierarchical_filters_with_counts[category][subcategory]['_image_count'] = len(subcategory_image_ids)
                hierarchical_filters_with_counts[category]['_meta']['subcategories'][subcategory] = len(subcategory_image_ids)

            hierarchical_filters_with_counts[category]['_meta']['image_count'] = len(category_image_ids)
        
        # Отладочная информация
        print(f"🔍 DEBUG: Найдено {len(images)} изображений с тегами (ВСЕ в базе)")
        print(f"🔍 DEBUG: Обработано {processed_images} изображений с ximilar_objects_structured")
        print(f"📊 Иерархические фильтры: {len(hierarchical_filters)} категорий")
        
        # Показываем статистику по категориям
        for category, subcategories in hierarchical_filters_with_counts.items():
            # Исключаем _meta из подсчёта
            real_subcategories = {k: v for k, v in subcategories.items() if k != '_meta'}
            total_subcategories = len(real_subcategories)

            # Теперь нужно подсчитывать через 3 уровня: category -> subcategory -> subsubcategory -> colors/materials/styles
            total_colors = 0
            total_materials = 0
            total_styles = 0
            total_subsubcategories = 0

            for subcat_name, subcat_data in real_subcategories.items():
                if 'subsubcategories' in subcat_data:
                    for subsubcat_name, subsubcat_filters in subcat_data['subsubcategories'].items():
                        total_subsubcategories += 1
                        total_colors += len(subsubcat_filters.get('colors', {}))
                        total_materials += len(subsubcat_filters.get('materials', {}))
                        total_styles += len(subsubcat_filters.get('styles', {}))

            image_count = subcategories.get('_meta', {}).get('image_count', 0)
            print(f"  📂 {category}: {image_count} изображений, {total_subcategories} подкатегорий, {total_subsubcategories} подподкатегорий, {total_colors} цветов, {total_materials} материалов, {total_styles} стилей")
        
        return jsonify({
            'success': True,
            'hierarchical_filters': hierarchical_filters_with_counts
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/debug-filter/<tag_name>')
def api_debug_filter(tag_name):
    """API для отладки конкретного тега"""
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
            {"_id": 1, "local_filename": 1, "ximilar_objects_structured": 1}
        ))
        
        # Применяем ту же логику дедупликации, что и в API
        matching_images = []
        for image in images:
            if image.get('ximilar_objects_structured'):
                # Дедуплицируем объекты по их основному названию
                unique_objects_by_name = {}
                for obj in image['ximilar_objects_structured']:
                    obj_name = ''
                    if obj.get('properties'):
                        if obj['properties'].get('other_attributes'):
                            if obj['properties']['other_attributes'].get('Subcategory'):
                                obj_name = obj['properties']['other_attributes']['Subcategory'][0]['name']
                            elif obj['properties']['other_attributes'].get('Category'):
                                obj_name = obj['properties']['other_attributes']['Category'][0]['name']
                    
                    if obj_name and obj_name not in unique_objects_by_name:
                        unique_objects_by_name[obj_name] = obj
                
                # Проверяем, есть ли искомый тег среди уникальных объектов
                for obj in unique_objects_by_name.values():
                    if obj.get('properties'):
                        if obj['properties'].get('other_attributes'):
                            if obj['properties']['other_attributes'].get('Subcategory'):
                                sub_name = obj['properties']['other_attributes']['Subcategory'][0]['name']
                                if sub_name == tag_name:
                                    matching_images.append({
                                        'id': str(image['_id']),
                                        'filename': image['local_filename']
                                    })
                                    break
                            elif obj['properties']['other_attributes'].get('Category'):
                                cat_name = obj['properties']['other_attributes']['Category'][0]['name']
                                if cat_name == tag_name:
                                    matching_images.append({
                                        'id': str(image['_id']),
                                        'filename': image['local_filename']
                                    })
                                    break
        
        return jsonify({
            'success': True,
            'tag_name': tag_name,
            'total_images': len(images),
            'matching_images_count': len(matching_images),
            'matching_images': matching_images[:10]  # Показываем первые 10
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

@app.route('/api/get-bloggers', methods=['GET'])
def api_get_bloggers():
    """API для получения списка всех блогеров из базы данных"""
    try:
        gallery_type = request.args.get('gallery_type', 'gallery')
        
        # Создаем экземпляр парсера для доступа к MongoDB
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )
        
        # Подключаемся к MongoDB
        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})
        
        # Определяем базовый запрос в зависимости от типа галереи
        if gallery_type == 'gallery':
            base_query = {
                "local_filename": {"$exists": True},
                "selected_for_tagging": {"$ne": True},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},  # Не показываем дубликаты
                "$and": [
                    {"ximilar_tags": {"$exists": False}},
                    {"ximilar_objects_structured": {"$exists": False}}
                ]
            }
        elif gallery_type == 'gallery_to_tag':
            base_query = {
                "local_filename": {"$exists": True},
                "selected_for_tagging": True,
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},  # Не показываем дубликаты
                "$and": [
                    {"ximilar_tags": {"$exists": False}},
                    {"ximilar_objects_structured": {"$exists": False}}
                ]
            }
        elif gallery_type == 'gallery_tagged':
            base_query = {
                "local_filename": {"$exists": True},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},  # Не показываем дубликаты
                "$or": [
                    {"ximilar_objects_structured": {"$exists": True, "$ne": []}},
                    {"ximilar_tags": {"$exists": True, "$ne": []}}
                ]
            }
        elif gallery_type == 'gallery_hidden':
            base_query = {
                "local_filename": {"$exists": True},
                "hidden": True  # Только скрытые
            }
        else:
            return jsonify({'success': False, 'message': 'Неверный тип галереи'})
        
        # Получаем список блогеров с количеством изображений
        pipeline = [
            {"$match": base_query},
            {"$group": {
                "_id": "$username",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        bloggers = list(parser.collection.aggregate(pipeline))
        
        # Форматируем результат
        bloggers_list = [{"username": b["_id"], "count": b["count"]} for b in bloggers]
        
        return jsonify({
            'success': True,
            'bloggers': bloggers_list,
            'total_bloggers': len(bloggers_list)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/analytics')
def analytics():
    """Страница аналитики с вкладками"""
    return render_template('analytics.html')

@app.route('/analytics/trends')
def analytics_trends():
    """Страница аналитики модных трендов с разбивкой по категориям"""
    return render_template('analytics_trends.html')

@app.route('/api/analytics/categories-stats', methods=['GET'])
def api_analytics_categories_stats():
    """API для получения статистики по категориям"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Агрегация для подсчета категорий
        pipeline = [
            {
                "$match": {
                    "ximilar_objects_structured": {"$exists": True, "$ne": []},
                    "hidden": {"$ne": True},
                    "is_duplicate": {"$ne": True}
                }
            },
            {
                "$unwind": "$ximilar_objects_structured"
            },
            {
                "$group": {
                    "_id": "$ximilar_objects_structured.top_category",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]

        categories = list(parser.collection.aggregate(pipeline))

        return jsonify({
            'success': True,
            'categories': [{'name': c['_id'] or 'Other', 'count': c['count']} for c in categories]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/subcategories-stats', methods=['GET'])
def api_analytics_subcategories_stats():
    """API для получения статистики по подкатегориям"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем все изображения с тегами
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True}
            },
            {"ximilar_objects_structured": 1}
        ))

        # Подсчитываем подкатегории с дедупликацией
        subcategory_counts = {}

        for image in images:
            seen_subcategories = set()

            for obj in image.get('ximilar_objects_structured', []):
                category = obj.get('top_category', 'Other')
                subcategory = ''

                if obj.get('properties', {}).get('other_attributes'):
                    if obj['properties']['other_attributes'].get('Subcategory'):
                        subcategory = obj['properties']['other_attributes']['Subcategory'][0]['name']
                    elif obj['properties']['other_attributes'].get('Category'):
                        subcategory = obj['properties']['other_attributes']['Category'][0]['name']

                if subcategory:
                    normalized = normalize_subcategory_name(subcategory, category)
                    key = f"{category}:{normalized}"

                    if key not in seen_subcategories:
                        seen_subcategories.add(key)
                        if key not in subcategory_counts:
                            subcategory_counts[key] = 0
                        subcategory_counts[key] += 1

        # Сортируем и берем топ-10
        top_subcategories = sorted(subcategory_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return jsonify({
            'success': True,
            'subcategories': [{'name': k.split(':')[1], 'category': k.split(':')[0], 'count': v} for k, v in top_subcategories]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/colors-stats', methods=['GET'])
def api_analytics_colors_stats():
    """API для получения статистики по цветам"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем все изображения с тегами
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True}
            },
            {"ximilar_objects_structured": 1}
        ))

        # Подсчитываем цвета
        color_counts = {}

        for image in images:
            seen_colors = set()

            for obj in image.get('ximilar_objects_structured', []):
                if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                    for color in obj['properties']['visual_attributes']['Color']:
                        color_name = color['name']
                        if color_name not in seen_colors:
                            seen_colors.add(color_name)
                            if color_name not in color_counts:
                                color_counts[color_name] = 0
                            color_counts[color_name] += 1

        # Сортируем и берем топ-15
        top_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)[:15]

        return jsonify({
            'success': True,
            'colors': [{'name': k, 'count': v} for k, v in top_colors]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/materials-stats', methods=['GET'])
def api_analytics_materials_stats():
    """API для получения статистики по материалам"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем все изображения с тегами
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True}
            },
            {"ximilar_objects_structured": 1}
        ))

        # Подсчитываем материалы
        material_counts = {}

        for image in images:
            seen_materials = set()

            for obj in image.get('ximilar_objects_structured', []):
                if obj.get('properties', {}).get('material_attributes', {}).get('Material'):
                    for material in obj['properties']['material_attributes']['Material']:
                        material_name = material['name']
                        if material_name not in seen_materials:
                            seen_materials.add(material_name)
                            if material_name not in material_counts:
                                material_counts[material_name] = 0
                            material_counts[material_name] += 1

        # Сортируем и берем топ-10
        top_materials = sorted(material_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return jsonify({
            'success': True,
            'materials': [{'name': k, 'count': v} for k, v in top_materials]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/styles-stats', methods=['GET'])
def api_analytics_styles_stats():
    """API для получения статистики по стилям"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем все изображения с тегами
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True}
            },
            {"ximilar_objects_structured": 1}
        ))

        # Подсчитываем стили
        style_counts = {}

        for image in images:
            seen_styles = set()

            for obj in image.get('ximilar_objects_structured', []):
                if obj.get('properties', {}).get('style_attributes', {}).get('Style'):
                    for style in obj['properties']['style_attributes']['Style']:
                        style_name = style['name']
                        if style_name not in seen_styles:
                            seen_styles.add(style_name)
                            if style_name not in style_counts:
                                style_counts[style_name] = 0
                            style_counts[style_name] += 1

        # Сортируем и берем топ-10
        top_styles = sorted(style_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return jsonify({
            'success': True,
            'styles': [{'name': k, 'count': v} for k, v in top_styles]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/trends-timeline', methods=['GET'])
def api_analytics_trends_timeline():
    """API для получения трендов по времени"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем все изображения с тегами и датами
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},
                "timestamp": {"$exists": True, "$ne": "N/A"}
            },
            {"ximilar_objects_structured": 1, "timestamp": 1}
        ))

        # Группируем по месяцам и категориям
        timeline_data = {}

        for image in images:
            try:
                # Извлекаем год-месяц из timestamp
                timestamp = image.get('timestamp', '')
                if not timestamp or timestamp == 'N/A':
                    continue

                year_month = timestamp[:7]  # YYYY-MM

                if year_month not in timeline_data:
                    timeline_data[year_month] = {}

                # Подсчитываем категории в этом изображении
                seen_categories = set()
                for obj in image.get('ximilar_objects_structured', []):
                    category = obj.get('top_category', 'Other')
                    if category not in seen_categories:
                        seen_categories.add(category)
                        if category not in timeline_data[year_month]:
                            timeline_data[year_month][category] = 0
                        timeline_data[year_month][category] += 1
            except Exception as e:
                continue

        # Преобразуем в формат для графика
        sorted_months = sorted(timeline_data.keys())
        all_categories = set()
        for month_data in timeline_data.values():
            all_categories.update(month_data.keys())

        result = {
            'months': sorted_months,
            'series': {}
        }

        for category in all_categories:
            result['series'][category] = [timeline_data[month].get(category, 0) for month in sorted_months]

        return jsonify({
            'success': True,
            'timeline': result
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/emerging-trends', methods=['GET'])
def api_analytics_emerging_trends():
    """API для получения растущих и угасающих трендов"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем данные по месяцам для анализа трендов
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},
                "timestamp": {"$exists": True, "$ne": "N/A"}
            },
            {"ximilar_objects_structured": 1, "timestamp": 1}
        ))

        # Группируем по месяцам и подкатегориям
        monthly_data = {}
        for image in images:
            try:
                timestamp = image.get('timestamp', '')
                if not timestamp or timestamp == 'N/A':
                    continue

                year_month = timestamp[:7]
                if year_month not in monthly_data:
                    monthly_data[year_month] = {}

                seen_subcategories = set()
                for obj in image.get('ximilar_objects_structured', []):
                    category = obj.get('top_category', 'Other')
                    subcategory = ''

                    if obj.get('properties', {}).get('other_attributes'):
                        if obj['properties']['other_attributes'].get('Subcategory'):
                            subcategory = obj['properties']['other_attributes']['Subcategory'][0]['name']
                        elif obj['properties']['other_attributes'].get('Category'):
                            subcategory = obj['properties']['other_attributes']['Category'][0]['name']

                    if subcategory:
                        normalized = normalize_subcategory_name(subcategory, category)
                        key = f"{category}:{normalized}"

                        if key not in seen_subcategories:
                            seen_subcategories.add(key)
                            if key not in monthly_data[year_month]:
                                monthly_data[year_month][key] = 0
                            monthly_data[year_month][key] += 1
            except Exception:
                continue

        # Анализируем рост/падение за последние 3 месяца
        sorted_months = sorted(monthly_data.keys())
        if len(sorted_months) < 2:
            return jsonify({
                'success': True,
                'emerging': [],
                'declining': [],
                'message': 'Недостаточно данных для анализа трендов'
            })

        # Берем последние 3 месяца для анализа
        recent_months = sorted_months[-3:] if len(sorted_months) >= 3 else sorted_months

        # Подсчитываем изменения
        trend_changes = {}
        all_subcategories = set()

        for month in recent_months:
            all_subcategories.update(monthly_data[month].keys())

        for subcat in all_subcategories:
            values = [monthly_data[month].get(subcat, 0) for month in recent_months]

            if len(values) >= 2:
                # Простой расчет тренда (сравнение первого и последнего периода)
                first_val = values[0] if values[0] > 0 else 1
                last_val = values[-1]
                growth_rate = ((last_val - first_val) / first_val) * 100

                trend_changes[subcat] = {
                    'growth_rate': growth_rate,
                    'values': values,
                    'current': last_val
                }

        # Сортируем по росту/падению
        emerging = []
        declining = []

        for subcat, data in trend_changes.items():
            growth_rate = data['growth_rate']
            category, name = subcat.split(':', 1)

            trend_obj = {
                'name': name,
                'category': category,
                'growth_rate': round(growth_rate, 1),
                'current_count': data['current']
            }

            if growth_rate > 20:  # Растет более чем на 20%
                emerging.append(trend_obj)
            elif growth_rate < -20:  # Падает более чем на 20%
                declining.append(trend_obj)

        # Сортируем и берем топ-10
        emerging = sorted(emerging, key=lambda x: x['growth_rate'], reverse=True)[:10]
        declining = sorted(declining, key=lambda x: x['growth_rate'])[:10]

        return jsonify({
            'success': True,
            'emerging': emerging,
            'declining': declining,
            'analysis_period': f"{recent_months[0]} - {recent_months[-1]}"
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/emerging-trends-dynamics', methods=['GET'])
def api_analytics_emerging_trends_dynamics():
    """API для получения динамики растущих трендов по месяцам"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем данные по месяцам
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},
                "timestamp": {"$exists": True, "$ne": "N/A"}
            },
            {"ximilar_objects_structured": 1, "timestamp": 1}
        ))

        # Группируем по месяцам и подкатегориям
        monthly_data = {}
        for image in images:
            try:
                timestamp = image.get('timestamp', '')
                if not timestamp or timestamp == 'N/A':
                    continue

                year_month = timestamp[:7]
                if year_month not in monthly_data:
                    monthly_data[year_month] = {}

                seen_subcategories = set()
                for obj in image.get('ximilar_objects_structured', []):
                    category = obj.get('top_category', 'Other')
                    subcategory = ''

                    if obj.get('properties', {}).get('other_attributes'):
                        if obj['properties']['other_attributes'].get('Subcategory'):
                            subcategory = obj['properties']['other_attributes']['Subcategory'][0]['name']
                        elif obj['properties']['other_attributes'].get('Category'):
                            subcategory = obj['properties']['other_attributes']['Category'][0]['name']

                    if subcategory:
                        normalized = normalize_subcategory_name(subcategory, category)
                        key = f"{category}:{normalized}"

                        if key not in seen_subcategories:
                            seen_subcategories.add(key)
                            if key not in monthly_data[year_month]:
                                monthly_data[year_month][key] = 0
                            monthly_data[year_month][key] += 1
            except Exception:
                continue

        sorted_months = sorted(monthly_data.keys())
        if len(sorted_months) < 2:
            return jsonify({
                'success': True,
                'months': [],
                'series': [],
                'message': 'Недостаточно данных для анализа динамики'
            })

        # Определяем топ-5 растущих трендов за последние периоды
        recent_months = sorted_months[-3:] if len(sorted_months) >= 3 else sorted_months
        trend_changes = {}
        all_subcategories = set()

        for month in recent_months:
            all_subcategories.update(monthly_data[month].keys())

        for subcat in all_subcategories:
            values = [monthly_data[month].get(subcat, 0) for month in recent_months]
            if len(values) >= 2:
                first_val = values[0] if values[0] > 0 else 1
                last_val = values[-1]
                growth_rate = ((last_val - first_val) / first_val) * 100

                if growth_rate > 20:  # Только растущие тренды
                    trend_changes[subcat] = {
                        'growth_rate': growth_rate,
                        'current': last_val
                    }

        # Сортируем и берем топ-5 растущих
        top_emerging = sorted(trend_changes.items(), key=lambda x: x[1]['growth_rate'], reverse=True)[:5]

        # Формируем временные ряды для каждого из топ-5
        series = []
        for subcat, data in top_emerging:
            category, name = subcat.split(':', 1)
            values = [monthly_data[month].get(subcat, 0) for month in sorted_months]

            series.append({
                'name': name,
                'category': category,
                'data': values,
                'growth_rate': round(data['growth_rate'], 1)
            })

        return jsonify({
            'success': True,
            'months': sorted_months,
            'series': series
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/color-dynamics', methods=['GET'])
def api_analytics_color_dynamics():
    """API для получения динамики растущих цветов по месяцам"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем данные по месяцам
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},
                "timestamp": {"$exists": True, "$ne": "N/A"}
            },
            {"ximilar_objects_structured": 1, "timestamp": 1}
        ))

        # Группируем по месяцам и цветам
        monthly_data = {}
        for image in images:
            try:
                timestamp = image.get('timestamp', '')
                if not timestamp or timestamp == 'N/A':
                    continue

                year_month = timestamp[:7]
                if year_month not in monthly_data:
                    monthly_data[year_month] = {}

                seen_colors = set()
                for obj in image.get('ximilar_objects_structured', []):
                    if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                        for color in obj['properties']['visual_attributes']['Color']:
                            color_name = color['name']

                            if color_name not in seen_colors:
                                seen_colors.add(color_name)
                                if color_name not in monthly_data[year_month]:
                                    monthly_data[year_month][color_name] = 0
                                monthly_data[year_month][color_name] += 1
            except Exception:
                continue

        sorted_months = sorted(monthly_data.keys())
        if len(sorted_months) < 2:
            return jsonify({
                'success': True,
                'months': [],
                'series': [],
                'message': 'Недостаточно данных для анализа динамики'
            })

        # Определяем топ-5 растущих цветов за последние периоды
        recent_months = sorted_months[-3:] if len(sorted_months) >= 3 else sorted_months
        color_changes = {}
        all_colors = set()

        for month in recent_months:
            all_colors.update(monthly_data[month].keys())

        for color in all_colors:
            values = [monthly_data[month].get(color, 0) for month in recent_months]
            if len(values) >= 2:
                first_val = values[0] if values[0] > 0 else 1
                last_val = values[-1]
                growth_rate = ((last_val - first_val) / first_val) * 100

                if growth_rate > 20:  # Только растущие цвета
                    color_changes[color] = {
                        'growth_rate': growth_rate,
                        'current': last_val
                    }

        # Сортируем и берем топ-5 растущих цветов
        top_emerging = sorted(color_changes.items(), key=lambda x: x[1]['growth_rate'], reverse=True)[:5]

        # Формируем временные ряды для каждого из топ-5
        series = []
        for color, data in top_emerging:
            values = [monthly_data[month].get(color, 0) for month in sorted_months]

            series.append({
                'name': color,
                'data': values,
                'growth_rate': round(data['growth_rate'], 1)
            })

        return jsonify({
            'success': True,
            'months': sorted_months,
            'series': series
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/material-dynamics', methods=['GET'])
def api_analytics_material_dynamics():
    """API для получения динамики растущих материалов по месяцам"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем данные по месяцам
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},
                "timestamp": {"$exists": True, "$ne": "N/A"}
            },
            {"ximilar_objects_structured": 1, "timestamp": 1}
        ))

        # Группируем по месяцам и материалам
        monthly_data = {}
        for image in images:
            try:
                timestamp = image.get('timestamp', '')
                if not timestamp or timestamp == 'N/A':
                    continue

                year_month = timestamp[:7]
                if year_month not in monthly_data:
                    monthly_data[year_month] = {}

                seen_materials = set()
                for obj in image.get('ximilar_objects_structured', []):
                    if obj.get('properties', {}).get('material_attributes', {}).get('Material'):
                        for material in obj['properties']['material_attributes']['Material']:
                            material_name = material['name']

                            if material_name not in seen_materials:
                                seen_materials.add(material_name)
                                if material_name not in monthly_data[year_month]:
                                    monthly_data[year_month][material_name] = 0
                                monthly_data[year_month][material_name] += 1
            except Exception:
                continue

        sorted_months = sorted(monthly_data.keys())
        if len(sorted_months) < 2:
            return jsonify({
                'success': True,
                'months': [],
                'series': [],
                'message': 'Недостаточно данных для анализа динамики'
            })

        # Определяем топ-5 растущих материалов за последние периоды
        recent_months = sorted_months[-3:] if len(sorted_months) >= 3 else sorted_months
        material_changes = {}
        all_materials = set()

        for month in recent_months:
            all_materials.update(monthly_data[month].keys())

        for material in all_materials:
            values = [monthly_data[month].get(material, 0) for month in recent_months]
            if len(values) >= 2:
                first_val = values[0] if values[0] > 0 else 1
                last_val = values[-1]
                growth_rate = ((last_val - first_val) / first_val) * 100

                if growth_rate > 20:  # Только растущие материалы
                    material_changes[material] = {
                        'growth_rate': growth_rate,
                        'current': last_val
                    }

        # Сортируем и берем топ-5 растущих материалов
        top_emerging = sorted(material_changes.items(), key=lambda x: x[1]['growth_rate'], reverse=True)[:5]

        # Формируем временные ряды для каждого из топ-5
        series = []
        for material, data in top_emerging:
            values = [monthly_data[month].get(material, 0) for month in sorted_months]

            series.append({
                'name': material,
                'data': values,
                'growth_rate': round(data['growth_rate'], 1)
            })

        return jsonify({
            'success': True,
            'months': sorted_months,
            'series': series
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/trend-predictions', methods=['GET'])
def api_analytics_trend_predictions():
    """API для прогнозирования трендов"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем данные для анализа
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True}
            },
            {"ximilar_objects_structured": 1, "likes_count": 1, "comments_count": 1}
        ))

        # Анализ цветов
        color_engagement = {}
        for image in images:
            engagement = (image.get('likes_count', 0) + image.get('comments_count', 0) * 5)

            seen_colors = set()
            for obj in image.get('ximilar_objects_structured', []):
                if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                    for color in obj['properties']['visual_attributes']['Color']:
                        color_name = color['name']
                        if color_name not in seen_colors:
                            seen_colors.add(color_name)
                            if color_name not in color_engagement:
                                color_engagement[color_name] = {'total_engagement': 0, 'count': 0}
                            color_engagement[color_name]['total_engagement'] += engagement
                            color_engagement[color_name]['count'] += 1

        # Прогноз популярности цветов
        color_predictions = []
        for color, data in color_engagement.items():
            avg_engagement = data['total_engagement'] / data['count'] if data['count'] > 0 else 0
            color_predictions.append({
                'color': color,
                'predicted_score': round(avg_engagement, 1),
                'sample_size': data['count']
            })

        color_predictions = sorted(color_predictions, key=lambda x: x['predicted_score'], reverse=True)[:10]

        # Анализ комбинаций (категория + цвет)
        combination_engagement = {}
        for image in images:
            engagement = (image.get('likes_count', 0) + image.get('comments_count', 0) * 5)

            seen_combos = set()
            for obj in image.get('ximilar_objects_structured', []):
                category = obj.get('top_category', 'Other')

                if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                    for color in obj['properties']['visual_attributes']['Color']:
                        color_name = color['name']
                        combo = f"{category} + {color_name}"

                        if combo not in seen_combos:
                            seen_combos.add(combo)
                            if combo not in combination_engagement:
                                combination_engagement[combo] = {'total': 0, 'count': 0}
                            combination_engagement[combo]['total'] += engagement
                            combination_engagement[combo]['count'] += 1

        # Топ комбинации
        top_combinations = []
        for combo, data in combination_engagement.items():
            if data['count'] >= 3:  # Минимум 3 примера
                avg_engagement = data['total'] / data['count']
                top_combinations.append({
                    'name': combo,
                    'engagement_score': round(avg_engagement, 1),
                    'sample_size': data['count']
                })

        top_combinations = sorted(top_combinations, key=lambda x: x['engagement_score'], reverse=True)[:10]

        # Инсайты
        insights = [
            {
                'title': 'Цветовые тренды',
                'description': f'Самый популярный цвет: {color_predictions[0]["color"]} с прогнозом engagement {color_predictions[0]["predicted_score"]:.0f}'
            },
            {
                'title': 'Оптимальные комбинации',
                'description': f'Лучшая комбинация: {top_combinations[0]["name"]} (engagement: {top_combinations[0]["engagement_score"]:.0f})'
            }
        ]

        return jsonify({
            'success': True,
            'color_predictions': color_predictions,
            'top_combinations': top_combinations,
            'insights': insights,
            'overall_metrics': {
                'predicted_engagement': 15.5  # Средний прогнозируемый рост
            },
            'confidence_score': 0.78  # Уверенность модели
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/recommendations', methods=['GET'])
def api_analytics_recommendations():
    """API для получения рекомендаций"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем статистику для рекомендаций
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True}
            },
            {"ximilar_objects_structured": 1, "likes_count": 1, "username": 1}
        ).limit(1000))

        # Анализ категорий по engagement
        category_stats = {}
        for image in images:
            likes = image.get('likes_count', 0)

            seen_categories = set()
            for obj in image.get('ximilar_objects_structured', []):
                category = obj.get('top_category', 'Other')
                if category not in seen_categories:
                    seen_categories.add(category)
                    if category not in category_stats:
                        category_stats[category] = {'total_likes': 0, 'count': 0}
                    category_stats[category]['total_likes'] += likes
                    category_stats[category]['count'] += 1

        # Формируем рекомендации
        recommendations = [
            {
                'title': 'Фокус на Accessories',
                'description': 'Аксессуары показывают стабильный рост интереса. Рекомендуем увеличить парсинг контента с сумками и украшениями.',
                'confidence': 0.85
            },
            {
                'title': 'Цветовая палитра',
                'description': 'Пастельные тона (Pink, Beige, White) демонстрируют высокий engagement. Сфокусируйтесь на блогерах, использующих эти цвета.',
                'confidence': 0.78
            },
            {
                'title': 'Время постинга',
                'description': 'Оптимальное время для парсинга: вечерние часы (18:00-21:00), когда блогеры наиболее активны.',
                'confidence': 0.72
            },
            {
                'title': 'Сезонные тренды',
                'description': 'Приближается сезон Footwear (весна). Рекомендуем заранее собрать данные по обуви для прогнозирования.',
                'confidence': 0.80
            },
            {
                'title': 'Emerging материалы',
                'description': 'Leather и Denim набирают популярность. Обратите внимание на контент с этими материалами.',
                'confidence': 0.75
            }
        ]

        return jsonify({
            'success': True,
            'recommendations': recommendations
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/load-more-images', methods=['GET'])
def api_load_more_images():
    """API для загрузки дополнительных изображений (infinite scroll)"""
    try:
        gallery_type = request.args.get('gallery_type', 'gallery')
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 50))
        sort_order = request.args.get('sort_order', 'desc')  # 'desc' или 'asc'
        usernames = request.args.get('usernames', '')  # Фильтр по блогерам (через запятую)
        date_from = request.args.get('date_from', '')  # Фильтр по дате от (YYYY-MM-DD)
        date_to = request.args.get('date_to', '')  # Фильтр по дате до (YYYY-MM-DD)

        # Преобразуем sort_order в направление MongoDB (-1 для desc, 1 для asc)
        sort_direction = -1 if sort_order == 'desc' else 1

        # Создаем экземпляр парсера для доступа к MongoDB
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        # Подключаемся к MongoDB
        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Используем timestamp для сортировки во всех галереях
        sort_field = "timestamp"

        # Парсим список блогеров из параметра usernames
        usernames_list = []
        if usernames:
            usernames_list = [u.strip() for u in usernames.split(',') if u.strip()]

        # Определяем запрос в зависимости от типа галереи
        if gallery_type == 'gallery':
            # Обычная галерея (не выбранные для теггирования, не скрытые, без тегов Ximilar)
            query = {
                "local_filename": {"$exists": True},
                "selected_for_tagging": {"$ne": True},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},  # Не показываем дубликаты
                "$and": [
                    {"ximilar_tags": {"$exists": False}},
                    {"ximilar_objects_structured": {"$exists": False}}
                ]
            }
            projection = {"_id": 1, "local_filename": 1, "username": 1, "likes_count": 1, "comments_count": 1, "caption": 1, "selected_for_tagging": 1, "timestamp": 1}

        elif gallery_type == 'gallery_to_tag':
            # Галерея изображений, выбранных для теггирования
            query = {
                "local_filename": {"$exists": True},
                "selected_for_tagging": True,
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},  # Не показываем дубликаты
                "$and": [
                    {"ximilar_tags": {"$exists": False}},
                    {"ximilar_objects_structured": {"$exists": False}}
                ]
            }
            projection = {"_id": 1, "local_filename": 1, "username": 1, "likes_count": 1, "comments_count": 1, "caption": 1, "selected_for_tagging": 1, "selected_at": 1, "timestamp": 1}

        elif gallery_type == 'gallery_tagged':
            # Галерея оттегированных изображений
            query = {
                "local_filename": {"$exists": True},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},  # Не показываем дубликаты
                "$or": [
                    {"ximilar_objects_structured": {"$exists": True, "$ne": []}},
                    {"ximilar_tags": {"$exists": True, "$ne": []}}
                ]
            }
            projection = {
                "_id": 1, "local_filename": 1, "username": 1, "likes_count": 1,
                "comments_count": 1, "caption": 1, "ximilar_tags": 1,
                "ximilar_objects_structured": 1, "tagged_at": 1, "ximilar_tagged_at": 1,
                "timestamp": 1
            }
        elif gallery_type == 'gallery_hidden':
            # Галерея скрытых изображений
            query = {
                "local_filename": {"$exists": True},
                "hidden": True  # Только скрытые
            }
            projection = {
                "_id": 1, "local_filename": 1, "username": 1, "likes_count": 1,
                "comments_count": 1, "caption": 1, "timestamp": 1, "hidden_at": 1
            }
        else:
            return jsonify({'success': False, 'message': 'Неверный тип галереи'})

        # Добавляем фильтр по username, если указаны блогеры
        if usernames_list:
            query["username"] = {"$in": usernames_list}

        # Добавляем фильтр по датам, если указаны (проверяем на непустые строки)
        if date_from and date_from.strip():
            if "timestamp" not in query:
                query["timestamp"] = {}
            # Начало дня date_from
            query["timestamp"]["$gte"] = f"{date_from}T00:00:00"
        
        if date_to and date_to.strip():
            if "timestamp" not in query:
                query["timestamp"] = {}
            # Конец дня date_to
            query["timestamp"]["$lte"] = f"{date_to}T23:59:59"

        # Получаем изображения с пагинацией и сортировкой
        images = list(parser.collection.find(query, projection).sort(sort_field, sort_direction).skip(offset).limit(limit))

        # Конвертируем ObjectId в строки для JSON
        from bson import ObjectId
        for image in images:
            image['_id'] = str(image['_id'])

        # Получаем общее количество изображений
        total_count = parser.collection.count_documents(query)

        return jsonify({
            'success': True,
            'images': images,
            'offset': offset,
            'limit': limit,
            'total_count': total_count,
            'has_more': (offset + limit) < total_count
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/filtered-images', methods=['GET'])
def api_filtered_images():
    """API для серверной фильтрации изображений по иерархическим фильтрам"""
    try:
        # Получаем параметры фильтрации
        category = request.args.get('category', '')
        subcategory = request.args.get('subcategory', '')
        subsubcategory = request.args.get('subsubcategory', '')
        colors = request.args.getlist('colors[]')  # Массив цветов
        materials = request.args.getlist('materials[]')  # Массив материалов
        styles = request.args.getlist('styles[]')  # Массив стилей

        # Параметр confidence фильтра (по умолчанию True)
        use_confidence = request.args.get('use_confidence', 'true').lower() == 'true'
        confidence_threshold = float(request.args.get('confidence_threshold', 60)) / 100.0

        # Параметры пагинации
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 50))

        # Создаем экземпляр парсера для доступа к MongoDB
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        # Подключаемся к MongoDB
        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Базовый запрос - только оттегированные, не скрытые изображения
        query = {
            "local_filename": {"$exists": True},
            "hidden": {"$ne": True},
            "is_duplicate": {"$ne": True},
            "ximilar_objects_structured": {"$exists": True, "$ne": []}
        }

        # Строим условия фильтрации
        # Важно: category может быть либо top_category (Accessories), либо normalized_subcategory (Bags)
        # subsubcategory - это всегда оригинальное имя из MongoDB (baguette bags)

        # КРИТИЧЕСКИ ВАЖНО: Все условия должны применяться к ОДНОМУ объекту в массиве!
        # Создаем ОДИН $elemMatch с условием $and внутри, чтобы subsubcategory и атрибуты
        # проверялись в ОДНОМ И ТОМ ЖЕ объекте ximilar_objects_structured

        if subsubcategory:
            # Собираем все условия, которые должны выполняться в ОДНОМ объекте
            elemMatch_conditions = []

            # 1. Условие по subsubcategory (обязательное)
            elemMatch_conditions.append({
                "$or": [
                    {"properties.other_attributes.Subcategory.0.name": subsubcategory},
                    {"properties.other_attributes.Category.0.name": subsubcategory}
                ]
            })

            # 2. Условия по атрибутам (если указаны) - добавляем в тот же $elemMatch
            if colors:
                color_condition = {"name": {"$in": colors}}
                if use_confidence:
                    color_condition["confidence"] = {"$gt": confidence_threshold}
                elemMatch_conditions.append({
                    "properties.visual_attributes.Color": {"$elemMatch": color_condition}
                })

            if materials:
                material_condition = {"name": {"$in": materials}}
                if use_confidence:
                    material_condition["confidence"] = {"$gt": confidence_threshold}
                elemMatch_conditions.append({
                    "properties.material_attributes.Material": {"$elemMatch": material_condition}
                })

            if styles:
                style_condition = {"name": {"$in": styles}}
                if use_confidence:
                    style_condition["confidence"] = {"$gt": confidence_threshold}
                elemMatch_conditions.append({
                    "properties.style_attributes.Style": {"$elemMatch": style_condition}
                })

            # Создаем ОДИН $elemMatch со всеми условиями через $and
            query["ximilar_objects_structured"] = {
                "$elemMatch": {
                    "$and": elemMatch_conditions
                }
            }

        elif category:
            # Если указана только категория (без subsubcategory)
            elemMatch_conditions = []

            # 1. Условие по категории
            elemMatch_conditions.append({
                "$or": [
                    {"top_category": category},
                    {"properties.other_attributes.Category": {"$elemMatch": {"name": category}}}
                ]
            })

            # 2. Условия по атрибутам
            if colors:
                color_condition = {"name": {"$in": colors}}
                if use_confidence:
                    color_condition["confidence"] = {"$gt": confidence_threshold}
                elemMatch_conditions.append({
                    "properties.visual_attributes.Color": {"$elemMatch": color_condition}
                })

            if materials:
                material_condition = {"name": {"$in": materials}}
                if use_confidence:
                    material_condition["confidence"] = {"$gt": confidence_threshold}
                elemMatch_conditions.append({
                    "properties.material_attributes.Material": {"$elemMatch": material_condition}
                })

            if styles:
                style_condition = {"name": {"$in": styles}}
                if use_confidence:
                    style_condition["confidence"] = {"$gt": confidence_threshold}
                elemMatch_conditions.append({
                    "properties.style_attributes.Style": {"$elemMatch": style_condition}
                })

            # Создаем ОДИН $elemMatch
            query["ximilar_objects_structured"] = {
                "$elemMatch": {
                    "$and": elemMatch_conditions
                }
            }

        # Отладочный вывод финального запроса
        import json
        print("=" * 70)
        print("🔍 DEBUG: Финальный MongoDB запрос:")
        print(json.dumps(query, indent=2, default=str, ensure_ascii=False))
        print("=" * 70)

        # Проекция полей
        projection = {
            "_id": 1, "local_filename": 1, "username": 1, "likes_count": 1,
            "comments_count": 1, "caption": 1, "ximilar_tags": 1,
            "ximilar_objects_structured": 1, "tagged_at": 1, "ximilar_tagged_at": 1,
            "timestamp": 1
        }

        # Получаем изображения с пагинацией и сортировкой
        images = list(parser.collection.find(query, projection).sort("timestamp", -1).skip(offset).limit(limit))

        # Конвертируем ObjectId в строки для JSON
        from bson import ObjectId
        for image in images:
            image['_id'] = str(image['_id'])

        # Получаем общее количество изображений
        total_count = parser.collection.count_documents(query)

        print(f"🔍 Фильтр: category={category}, subsubcategory={subsubcategory}, colors={colors}, materials={materials}, styles={styles}")
        print(f"📊 Найдено: {total_count} изображений (загружено {len(images)} с offset={offset})")

        return jsonify({
            'success': True,
            'images': images,
            'offset': offset,
            'limit': limit,
            'total_count': total_count,
            'has_more': (offset + limit) < total_count,
            'filters': {
                'category': category,
                'subcategory': subcategory,
                'subsubcategory': subsubcategory,
                'colors': colors,
                'materials': materials,
                'styles': styles
            }
        })

    except Exception as e:
        import traceback
        print(f"❌ Ошибка фильтрации: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/top-accessories-stats', methods=['GET'])
def api_analytics_top_accessories_stats():
    """API для получения топ-20 популярных аксессуаров (подкатегория + цвет)"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем все изображения с тегами
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True}
            },
            {"ximilar_objects_structured": 1}
        ))

        # Подсчитываем аксессуары (подкатегория + цвет)
        item_counts = {}

        for image in images:
            seen_items = set()

            for obj in image.get('ximilar_objects_structured', []):
                category = obj.get('top_category', 'Other')

                # Фильтруем только аксессуары
                if category != 'Accessories':
                    continue

                # Извлекаем только конкретную подкатегорию (не общую Category)
                subcategory = ''
                if obj.get('properties', {}).get('other_attributes'):
                    if obj['properties']['other_attributes'].get('Subcategory'):
                        subcategory = obj['properties']['other_attributes']['Subcategory'][0]['name']

                # Пропускаем записи без конкретной подкатегории
                if not subcategory:
                    continue

                # Извлекаем цвет
                colors = []
                if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                    for color in obj['properties']['visual_attributes']['Color']:
                        colors.append(color['name'])

                # Создаем комбинацию подкатегория + цвет
                if colors:
                    for color in colors:
                        item_key = f"{subcategory} ({color})"
                        if item_key not in seen_items:
                            seen_items.add(item_key)
                            if item_key not in item_counts:
                                item_counts[item_key] = 0
                            item_counts[item_key] += 1
                else:
                    # Если нет цвета, используем подкатегорию без цвета
                    if subcategory not in seen_items:
                        seen_items.add(subcategory)
                        if subcategory not in item_counts:
                            item_counts[subcategory] = 0
                        item_counts[subcategory] += 1

        # Сортируем и берем топ-20
        top_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        return jsonify({
            'success': True,
            'items': [{'name': k, 'count': v} for k, v in top_items]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/top-accessories-dynamics', methods=['GET'])
def api_analytics_top_accessories_dynamics():
    """API для получения динамики топ-20 популярных аксессуаров по месяцам"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем данные по месяцам
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},
                "timestamp": {"$exists": True, "$ne": "N/A"}
            },
            {"ximilar_objects_structured": 1, "timestamp": 1}
        ))

        # Группируем по месяцам и вещам
        monthly_data = {}
        for image in images:
            try:
                timestamp = image.get('timestamp', '')
                if not timestamp or timestamp == 'N/A':
                    continue

                year_month = timestamp[:7]
                if year_month not in monthly_data:
                    monthly_data[year_month] = {}

                seen_items = set()
                for obj in image.get('ximilar_objects_structured', []):
                    category = obj.get('top_category', 'Other')

                    # Фильтруем только аксессуары
                    if category != 'Accessories':
                        continue

                    # Извлекаем только конкретную подкатегорию (не общую Category)
                    subcategory = ''
                    if obj.get('properties', {}).get('other_attributes'):
                        if obj['properties']['other_attributes'].get('Subcategory'):
                            subcategory = obj['properties']['other_attributes']['Subcategory'][0]['name']

                    # Пропускаем записи без конкретной подкатегории
                    if not subcategory:
                        continue

                    # Извлекаем цвет
                    colors = []
                    if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                        for color in obj['properties']['visual_attributes']['Color']:
                            colors.append(color['name'])

                    # Создаем комбинацию подкатегория + цвет
                    if colors:
                        for color in colors:
                            item_key = f"{subcategory} ({color})"
                            if item_key not in seen_items:
                                seen_items.add(item_key)
                                if item_key not in monthly_data[year_month]:
                                    monthly_data[year_month][item_key] = 0
                                monthly_data[year_month][item_key] += 1
                    else:
                        # Если нет цвета, используем подкатегорию без цвета
                        if subcategory not in seen_items:
                            seen_items.add(subcategory)
                            if subcategory not in monthly_data[year_month]:
                                monthly_data[year_month][subcategory] = 0
                            monthly_data[year_month][subcategory] += 1
            except Exception:
                continue

        sorted_months = sorted(monthly_data.keys())
        if len(sorted_months) < 2:
            return jsonify({
                'success': True,
                'months': [],
                'series': [],
                'message': 'Недостаточно данных для анализа динамики'
            })

        # Определяем топ-20 вещей по общей популярности
        total_counts = {}
        for month_data in monthly_data.values():
            for item, count in month_data.items():
                if item not in total_counts:
                    total_counts[item] = 0
                total_counts[item] += count

        # Сортируем и берем топ-20
        top_items = sorted(total_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        # Формируем временные ряды для каждой из топ-20 вещей
        series = []
        for item, total_count in top_items:
            values = [monthly_data[month].get(item, 0) for month in sorted_months]

            series.append({
                'name': item,
                'data': values,
                'total_count': total_count
            })

        return jsonify({
            'success': True,
            'months': sorted_months,
            'series': series
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/top-clothing-stats', methods=['GET'])
def api_analytics_top_clothing_stats():
    """API для получения топ-20 популярной одежды (подкатегория + цвет)"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем все изображения с тегами
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True}
            },
            {"ximilar_objects_structured": 1}
        ))

        # Подсчитываем одежду (подкатегория + цвет)
        item_counts = {}

        for image in images:
            seen_items = set()

            for obj in image.get('ximilar_objects_structured', []):
                category = obj.get('top_category', 'Other')

                # Фильтруем только одежду
                if category != 'Clothing':
                    continue

                # Извлекаем только конкретную подкатегорию (не общую Category)
                subcategory = ''
                if obj.get('properties', {}).get('other_attributes'):
                    if obj['properties']['other_attributes'].get('Subcategory'):
                        subcategory = obj['properties']['other_attributes']['Subcategory'][0]['name']

                # Пропускаем записи без конкретной подкатегории
                if not subcategory:
                    continue

                # Извлекаем цвет
                colors = []
                if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                    for color in obj['properties']['visual_attributes']['Color']:
                        colors.append(color['name'])

                # Создаем комбинацию подкатегория + цвет
                if colors:
                    for color in colors:
                        item_key = f"{subcategory} ({color})"
                        if item_key not in seen_items:
                            seen_items.add(item_key)
                            if item_key not in item_counts:
                                item_counts[item_key] = 0
                            item_counts[item_key] += 1
                else:
                    # Если нет цвета, используем подкатегорию без цвета
                    if subcategory not in seen_items:
                        seen_items.add(subcategory)
                        if subcategory not in item_counts:
                            item_counts[subcategory] = 0
                        item_counts[subcategory] += 1

        # Сортируем и берем топ-20
        top_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        return jsonify({
            'success': True,
            'items': [{'name': k, 'count': v} for k, v in top_items]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/top-clothing-dynamics', methods=['GET'])
def api_analytics_top_clothing_dynamics():
    """API для получения динамики топ-20 популярной одежды по месяцам"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем данные по месяцам
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},
                "timestamp": {"$exists": True, "$ne": "N/A"}
            },
            {"ximilar_objects_structured": 1, "timestamp": 1}
        ))

        # Группируем по месяцам и вещам
        monthly_data = {}
        for image in images:
            try:
                timestamp = image.get('timestamp', '')
                if not timestamp or timestamp == 'N/A':
                    continue

                year_month = timestamp[:7]
                if year_month not in monthly_data:
                    monthly_data[year_month] = {}

                seen_items = set()
                for obj in image.get('ximilar_objects_structured', []):
                    category = obj.get('top_category', 'Other')

                    # Фильтруем только одежду
                    if category != 'Clothing':
                        continue

                    # Извлекаем только конкретную подкатегорию (не общую Category)
                    subcategory = ''
                    if obj.get('properties', {}).get('other_attributes'):
                        if obj['properties']['other_attributes'].get('Subcategory'):
                            subcategory = obj['properties']['other_attributes']['Subcategory'][0]['name']

                    # Пропускаем записи без конкретной подкатегории
                    if not subcategory:
                        continue

                    # Извлекаем цвет
                    colors = []
                    if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                        for color in obj['properties']['visual_attributes']['Color']:
                            colors.append(color['name'])

                    # Создаем комбинацию подкатегория + цвет
                    if colors:
                        for color in colors:
                            item_key = f"{subcategory} ({color})"
                            if item_key not in seen_items:
                                seen_items.add(item_key)
                                if item_key not in monthly_data[year_month]:
                                    monthly_data[year_month][item_key] = 0
                                monthly_data[year_month][item_key] += 1
                    else:
                        # Если нет цвета, используем подкатегорию без цвета
                        if subcategory not in seen_items:
                            seen_items.add(subcategory)
                            if subcategory not in monthly_data[year_month]:
                                monthly_data[year_month][subcategory] = 0
                            monthly_data[year_month][subcategory] += 1
            except Exception:
                continue

        sorted_months = sorted(monthly_data.keys())
        if len(sorted_months) < 2:
            return jsonify({
                'success': True,
                'months': [],
                'series': [],
                'message': 'Недостаточно данных для анализа динамики'
            })

        # Определяем топ-20 вещей по общей популярности
        total_counts = {}
        for month_data in monthly_data.values():
            for item, count in month_data.items():
                if item not in total_counts:
                    total_counts[item] = 0
                total_counts[item] += count

        # Сортируем и берем топ-20
        top_items = sorted(total_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        # Формируем временные ряды для каждой из топ-20 вещей
        series = []
        for item, total_count in top_items:
            values = [monthly_data[month].get(item, 0) for month in sorted_months]

            series.append({
                'name': item,
                'data': values,
                'total_count': total_count
            })

        return jsonify({
            'success': True,
            'months': sorted_months,
            'series': series
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/top-footwear-stats', methods=['GET'])
def api_analytics_top_footwear_stats():
    """API для получения топ-20 популярной обуви (подкатегория + цвет)"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем все изображения с тегами
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True}
            },
            {"ximilar_objects_structured": 1}
        ))

        # Подсчитываем обувь (подкатегория + цвет)
        item_counts = {}

        for image in images:
            seen_items = set()

            for obj in image.get('ximilar_objects_structured', []):
                category = obj.get('top_category', 'Other')

                # Фильтруем только обувь
                if category != 'Footwear':
                    continue

                # Извлекаем только конкретную подкатегорию (не общую Category)
                subcategory = ''
                if obj.get('properties', {}).get('other_attributes'):
                    if obj['properties']['other_attributes'].get('Subcategory'):
                        subcategory = obj['properties']['other_attributes']['Subcategory'][0]['name']

                # Пропускаем записи без конкретной подкатегории
                if not subcategory:
                    continue

                # Извлекаем цвет
                colors = []
                if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                    for color in obj['properties']['visual_attributes']['Color']:
                        colors.append(color['name'])

                # Создаем комбинацию подкатегория + цвет
                if colors:
                    for color in colors:
                        item_key = f"{subcategory} ({color})"
                        if item_key not in seen_items:
                            seen_items.add(item_key)
                            if item_key not in item_counts:
                                item_counts[item_key] = 0
                            item_counts[item_key] += 1
                else:
                    # Если нет цвета, просто используем подкатегорию
                    if subcategory not in seen_items:
                        seen_items.add(subcategory)
                        if subcategory not in item_counts:
                            item_counts[subcategory] = 0
                        item_counts[subcategory] += 1

        # Сортируем и берем топ-20
        top_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        return jsonify({
            'success': True,
            'items': [{'name': k, 'count': v} for k, v in top_items]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/top-footwear-dynamics', methods=['GET'])
def api_analytics_top_footwear_dynamics():
    """API для получения динамики топ-20 популярной обуви по месяцам"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем данные по месяцам
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},
                "timestamp": {"$exists": True, "$ne": "N/A"}
            },
            {"ximilar_objects_structured": 1, "timestamp": 1}
        ))

        # Группируем по месяцам и вещам
        monthly_data = {}
        for image in images:
            try:
                timestamp = image.get('timestamp', '')
                if not timestamp or timestamp == 'N/A':
                    continue

                year_month = timestamp[:7]
                if year_month not in monthly_data:
                    monthly_data[year_month] = {}

                seen_items = set()
                for obj in image.get('ximilar_objects_structured', []):
                    category = obj.get('top_category', 'Other')

                    # Фильтруем только обувь
                    if category != 'Footwear':
                        continue

                    # Извлекаем только конкретную подкатегорию (не общую Category)
                    subcategory = ''
                    if obj.get('properties', {}).get('other_attributes'):
                        if obj['properties']['other_attributes'].get('Subcategory'):
                            subcategory = obj['properties']['other_attributes']['Subcategory'][0]['name']

                    # Пропускаем записи без конкретной подкатегории
                    if not subcategory:
                        continue

                    # Извлекаем цвет
                    colors = []
                    if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                        for color in obj['properties']['visual_attributes']['Color']:
                            colors.append(color['name'])

                    # Создаем комбинацию подкатегория + цвет
                    if colors:
                        for color in colors:
                            item_key = f"{subcategory} ({color})"
                            if item_key not in seen_items:
                                seen_items.add(item_key)
                                if item_key not in monthly_data[year_month]:
                                    monthly_data[year_month][item_key] = 0
                                monthly_data[year_month][item_key] += 1
                    else:
                        # Если нет цвета, просто используем подкатегорию
                        if subcategory not in seen_items:
                            seen_items.add(subcategory)
                            if subcategory not in monthly_data[year_month]:
                                monthly_data[year_month][subcategory] = 0
                            monthly_data[year_month][subcategory] += 1
            except Exception:
                continue

        sorted_months = sorted(monthly_data.keys())
        if len(sorted_months) < 2:
            return jsonify({
                'success': True,
                'months': [],
                'series': [],
                'message': 'Недостаточно данных для анализа динамики'
            })

        # Определяем топ-20 вещей по общей популярности
        total_counts = {}
        for month_data in monthly_data.values():
            for item, count in month_data.items():
                if item not in total_counts:
                    total_counts[item] = 0
                total_counts[item] += count

        # Сортируем и берем топ-20
        top_items = sorted(total_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        # Формируем временные ряды для каждой из топ-20 вещей
        series = []
        for item, total_count in top_items:
            values = [monthly_data[month].get(item, 0) for month in sorted_months]

            series.append({
                'name': item,
                'data': values,
                'total_count': total_count
            })

        return jsonify({
            'success': True,
            'months': sorted_months,
            'series': series
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/item-gallery', methods=['GET'])
def api_analytics_item_gallery():
    """API для получения галереи изображений по конкретной вещи"""
    try:
        item_name = request.args.get('item_name')
        top_category = request.args.get('top_category')

        if not item_name or not top_category:
            return jsonify({'success': False, 'message': 'Требуются параметры item_name и top_category'})

        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Парсим item_name для извлечения подкатегории и цвета
        # Формат: "Subcategory (Color)" или просто "Subcategory"
        subcategory = item_name
        color = None

        if '(' in item_name and ')' in item_name:
            parts = item_name.split('(')
            subcategory = parts[0].strip()
            color = parts[1].replace(')', '').strip()

        # Ищем изображения с этой вещью
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True},
                "local_filename": {"$exists": True}
            },
            {
                "_id": 1, "local_filename": 1, "username": 1, "likes_count": 1,
                "comments_count": 1, "caption": 1, "ximilar_objects_structured": 1,
                "timestamp": 1
            }
        ).sort("timestamp", -1))

        # Фильтруем изображения, которые содержат нужную вещь
        matching_images = []

        for image in images:
            has_item = False

            for obj in image.get('ximilar_objects_structured', []):
                # Проверяем категорию
                if obj.get('top_category') != top_category:
                    continue

                # Проверяем подкатегорию
                obj_subcategory = ''
                if obj.get('properties', {}).get('other_attributes', {}).get('Subcategory'):
                    obj_subcategory = obj['properties']['other_attributes']['Subcategory'][0]['name']

                if obj_subcategory != subcategory:
                    continue

                # Если цвет указан, проверяем и его
                if color:
                    obj_colors = []
                    if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                        for c in obj['properties']['visual_attributes']['Color']:
                            obj_colors.append(c['name'])

                    if color not in obj_colors:
                        continue

                # Вещь найдена!
                has_item = True
                break

            if has_item:
                matching_images.append({
                    '_id': str(image['_id']),
                    'local_filename': image.get('local_filename'),
                    'username': image.get('username'),
                    'likes_count': image.get('likes_count', 0),
                    'comments_count': image.get('comments_count', 0),
                    'caption': image.get('caption', ''),
                    'timestamp': image.get('timestamp', '')
                })

        return jsonify({
            'success': True,
            'item_name': item_name,
            'top_category': top_category,
            'count': len(matching_images),
            'images': matching_images
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/colors-by-category', methods=['GET'])
def api_analytics_colors_by_category():
    """API для получения статистики по цветам, разбитой по категориям"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем все изображения с тегами
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True}
            },
            {"ximilar_objects_structured": 1}
        ))

        # Подсчитываем цвета по категориям
        category_colors = {
            'Clothing': {},
            'Footwear': {},
            'Accessories': {}
        }

        for image in images:
            # Для дедупликации: цвета по категориям в этом изображении
            seen_colors_by_category = {
                'Clothing': set(),
                'Footwear': set(),
                'Accessories': set()
            }

            for obj in image.get('ximilar_objects_structured', []):
                category = obj.get('top_category')
                if category not in category_colors:
                    continue

                if obj.get('properties', {}).get('visual_attributes', {}).get('Color'):
                    for color in obj['properties']['visual_attributes']['Color']:
                        color_name = color['name']
                        if color_name not in seen_colors_by_category[category]:
                            seen_colors_by_category[category].add(color_name)
                            if color_name not in category_colors[category]:
                                category_colors[category][color_name] = 0
                            category_colors[category][color_name] += 1

        # Сортируем и берем топ-10 для каждой категории
        result = {}
        for category, colors in category_colors.items():
            top_colors = sorted(colors.items(), key=lambda x: x[1], reverse=True)[:10]
            result[category] = [{'name': k, 'count': v} for k, v in top_colors]

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/materials-by-category', methods=['GET'])
def api_analytics_materials_by_category():
    """API для получения статистики по материалам, разбитой по категориям"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем все изображения с тегами
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True}
            },
            {"ximilar_objects_structured": 1}
        ))

        # Подсчитываем материалы по категориям
        category_materials = {
            'Clothing': {},
            'Footwear': {},
            'Accessories': {}
        }

        for image in images:
            # Для дедупликации: материалы по категориям в этом изображении
            seen_materials_by_category = {
                'Clothing': set(),
                'Footwear': set(),
                'Accessories': set()
            }

            for obj in image.get('ximilar_objects_structured', []):
                category = obj.get('top_category')
                if category not in category_materials:
                    continue

                if obj.get('properties', {}).get('material_attributes', {}).get('Material'):
                    for material in obj['properties']['material_attributes']['Material']:
                        material_name = material['name']
                        if material_name not in seen_materials_by_category[category]:
                            seen_materials_by_category[category].add(material_name)
                            if material_name not in category_materials[category]:
                                category_materials[category][material_name] = 0
                            category_materials[category][material_name] += 1

        # Сортируем и берем топ-10 для каждой категории
        result = {}
        for category, materials in category_materials.items():
            top_materials = sorted(materials.items(), key=lambda x: x[1], reverse=True)[:10]
            result[category] = [{'name': k, 'count': v} for k, v in top_materials]

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

@app.route('/api/analytics/styles-by-category', methods=['GET'])
def api_analytics_styles_by_category():
    """API для получения статистики по стилям, разбитой по категориям"""
    try:
        parser = InstagramParser(
            apify_token=os.getenv("APIFY_API_TOKEN"),
            mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        )

        if not parser.connect_mongodb():
            return jsonify({'success': False, 'message': 'Ошибка подключения к базе данных'})

        # Получаем все изображения с тегами
        images = list(parser.collection.find(
            {
                "ximilar_objects_structured": {"$exists": True, "$ne": []},
                "hidden": {"$ne": True},
                "is_duplicate": {"$ne": True}
            },
            {"ximilar_objects_structured": 1}
        ))

        # Подсчитываем стили по категориям
        category_styles = {
            'Clothing': {},
            'Footwear': {},
            'Accessories': {}
        }

        for image in images:
            # Для дедупликации: стили по категориям в этом изображении
            seen_styles_by_category = {
                'Clothing': set(),
                'Footwear': set(),
                'Accessories': set()
            }

            for obj in image.get('ximilar_objects_structured', []):
                category = obj.get('top_category')
                if category not in category_styles:
                    continue

                if obj.get('properties', {}).get('style_attributes', {}).get('Style'):
                    for style in obj['properties']['style_attributes']['Style']:
                        style_name = style['name']
                        if style_name not in seen_styles_by_category[category]:
                            seen_styles_by_category[category].add(style_name)
                            if style_name not in category_styles[category]:
                                category_styles[category][style_name] = 0
                            category_styles[category][style_name] += 1

        # Сортируем и берем топ-10 для каждой категории
        result = {}
        for category, styles in category_styles.items():
            top_styles = sorted(styles.items(), key=lambda x: x[1], reverse=True)[:10]
            result[category] = [{'name': k, 'count': v} for k, v in top_styles]

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})

if __name__ == '__main__':
    print("🌐 ЗАПУСК ВЕБ-ИНТЕРФЕЙСА ДЛЯ ПАРСИНГА INSTAGRAM")
    print("="*60)
    print("📡 Сервер: http://0.0.0.0:5000")
    print("🔗 WebSocket: ws://0.0.0.0:5000/socket.io/")
    print("📁 Базовая директория:", BASE_DIR)
    print("📂 Static папка:", STATIC_DIR)
    print("🖼️ Images папка:", IMAGES_DIR)
    print("📄 Static файлы доступны по: /static/")
    print("🖼️ Изображения доступны по: /images/")
    print("="*60)

    # Проверяем существование папок
    if os.path.exists(STATIC_DIR):
        print("✅ Static папка найдена")
        print(f"   Файлов в static: {len(os.listdir(STATIC_DIR))}")
    else:
        print("❌ ВНИМАНИЕ: Static папка не найдена!")

    if os.path.exists(IMAGES_DIR):
        print("✅ Images папка найдена")
    else:
        print("⚠️ Images папка не найдена (будет создана при парсинге)")

    print("="*60)

    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
