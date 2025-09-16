#!/usr/bin/env python3
"""
Веб-интерфейс для просмотра MongoDB
"""

from flask import Flask, render_template_string, request, abort
import pymongo
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()
load_dotenv('mongodb_config.env')

app = Flask(__name__)

# Разрешенные IP-адреса (замените на ваши)
ALLOWED_IPS = ['127.0.0.1', '89.169.176.64']  # Добавьте нужные IP

@app.before_request
def limit_remote_addr():
    """Ограничение доступа по IP"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if client_ip not in ALLOWED_IPS:
        abort(403)

# HTML шаблон
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>🗄️ MongoDB Data Viewer</title>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .collection { 
            margin: 20px 0; 
            padding: 15px; 
            border: 1px solid #ddd; 
            border-radius: 8px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .document { 
            margin: 10px 0; 
            padding: 10px; 
            background: #f8f9fa; 
            border-left: 4px solid #007bff;
            border-radius: 4px;
        }
        .stats { 
            background: #e8f4f8; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 8px;
            border: 1px solid #bee5eb;
        }
        .collection-header {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 12px;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #f5c6cb;
        }
        .refresh-btn {
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 10px 0;
        }
        .refresh-btn:hover {
            background: #218838;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🗄️ MongoDB Data Viewer</h1>
        <p>Instagram Gallery Database</p>
        <a href="/" class="refresh-btn">🔄 Обновить</a>
    </div>
    
    {% if error %}
    <div class="error">
        <h3>❌ Ошибка подключения:</h3>
        <p>{{ error }}</p>
    </div>
    {% else %}
    <div class="stats">
        <strong>📊 База данных:</strong> instagram_gallery<br>
        <strong>📂 Коллекций:</strong> {{ collections|length }}<br>
        <strong>🕐 Время обновления:</strong> {{ update_time }}
    </div>
    
    {% for collection_name, data in collections.items() %}
    <div class="collection">
        <div class="collection-header">
            <h2>📂 {{ collection_name }}</h2>
            <p><strong>📄 Документов:</strong> {{ data.count }}</p>
        </div>
        
        {% if data.sample %}
        <h3>📋 Примеры документов:</h3>
        {% for doc in data.sample %}
        <div class="document">
            <pre>{{ doc }}</pre>
        </div>
        {% endfor %}
        {% else %}
        <p><em>Коллекция пустая</em></p>
        {% endif %}
    </div>
    {% endfor %}
    {% endif %}
</body>
</html>
'''

@app.route('/')
def index():
    """Главная страница с данными MongoDB"""
    try:
        # Подключение к MongoDB
        client = pymongo.MongoClient(
            os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/admin')
        )
        db = client.instagram_gallery
        collections = {}
        
        # Получение списка коллекций
        collection_names = db.list_collection_names()
        
        for collection_name in collection_names:
            collection = db[collection_name]
            count = collection.count_documents({})
            
            # Получение примеров документов (максимум 3)
            sample = []
            if count > 0:
                sample_docs = list(collection.find().limit(3))
                for doc in sample_docs:
                    # Преобразование ObjectId в строку для JSON сериализации
                    if '_id' in doc:
                        doc['_id'] = str(doc['_id'])
                    sample.append(json.dumps(doc, indent=2, ensure_ascii=False))
            
            collections[collection_name] = {
                'count': count,
                'sample': sample
            }
        
        client.close()
        
        return render_template_string(HTML_TEMPLATE, 
                                    collections=collections,
                                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, 
                                    error=str(e),
                                    collections={},
                                    update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/api/collections')
def api_collections():
    """API для получения списка коллекций"""
    try:
        client = pymongo.MongoClient(
            os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/admin')
        )
        db = client.instagram_gallery
        collections = {}
        
        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            count = collection.count_documents({})
            collections[collection_name] = {'count': count}
        
        client.close()
        return collections
        
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    print("🚀 Запуск MongoDB Web Viewer...")
    print("📊 База данных: instagram_gallery")
    print("🌐 Доступ: http://YOUR_SERVER_IP:8081")
    print("🔒 Ограничения по IP:", ALLOWED_IPS)
    
    app.run(host='0.0.0.0', port=8081, debug=True)
