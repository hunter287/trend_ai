#!/usr/bin/env python3
"""
Скрипт для выборки 100-150 случайных изображений из MongoDB
с данными Ximilar для последующего сравнения с FashionCLIP
"""

import os
import sys
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные окружения
import sys
sys.path.append('..')
# load_dotenv('../.env')
# load_dotenv('../mongodb_config.env')
# Используем прямое подключение к серверу вместо локального

# Параметры выборки
SAMPLE_SIZE = 120  # Целевой размер выборки
OUTPUT_FILE = 'data/sample_images.json'

def connect_to_mongodb():
    """Подключение к MongoDB на удаленном сервере"""
    # Прямое подключение к серверу
    mongodb_uri = 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@158.160.19.119:27017/instagram_gallery?authSource=admin'

    try:
        print(f"🔗 Подключение к MongoDB на 158.160.19.119...")
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=15000)
        client.admin.command('ping')
        print(f"✅ Подключено к MongoDB")
        return client
    except Exception as e:
        print(f"❌ Ошибка подключения к MongoDB: {e}")
        sys.exit(1)

def extract_ximilar_summary(doc):
    """Извлечь основную информацию из Ximilar данных"""
    ximilar_data = {
        'categories': [],
        'colors': [],
        'materials': [],
        'styles': []
    }

    if not doc.get('ximilar_objects'):
        return ximilar_data

    # Извлекаем данные из всех объектов
    for obj in doc['ximilar_objects']:
        props = obj.get('properties', {})

        # Категории
        categories = props.get('other_attributes', {}).get('Category', [])
        for cat in categories:
            if cat.get('confidence', 0) > 0.5:
                ximilar_data['categories'].append({
                    'name': cat['name'],
                    'confidence': cat['confidence']
                })

        # Цвета
        colors = props.get('visual_attributes', {}).get('Color', [])
        for color in colors:
            if color.get('confidence', 0) > 0.5:
                ximilar_data['colors'].append({
                    'name': color['name'],
                    'confidence': color['confidence']
                })

        # Материалы
        materials = props.get('material_attributes', {}).get('Material', [])
        for material in materials:
            if material.get('confidence', 0) > 0.5:
                ximilar_data['materials'].append({
                    'name': material['name'],
                    'confidence': material['confidence']
                })

        # Стили
        styles = props.get('style_attributes', {}).get('Style', [])
        for style in styles:
            if style.get('confidence', 0) > 0.5:
                ximilar_data['styles'].append({
                    'name': style['name'],
                    'confidence': style['confidence']
                })

    # Дедупликация и сортировка по confidence
    for key in ximilar_data:
        # Дедупликация по имени, оставляем с максимальной confidence
        seen = {}
        for item in ximilar_data[key]:
            name = item['name']
            if name not in seen or item['confidence'] > seen[name]['confidence']:
                seen[name] = item

        # Сортировка по confidence
        ximilar_data[key] = sorted(seen.values(), key=lambda x: x['confidence'], reverse=True)

    return ximilar_data

def prepare_sample_dataset():
    """Подготовить датасет для сравнения"""
    print(f"\n🔍 Подготовка датасета для сравнения FashionCLIP vs Ximilar\n")

    client = connect_to_mongodb()
    db = client.get_database()
    collection = db['images']

    # Получаем случайную выборку с успешными Ximilar результатами
    print(f"📊 Выборка {SAMPLE_SIZE} случайных изображений...")

    pipeline = [
        # Фильтр: только изображения с успешными Ximilar результатами
        {
            '$match': {
                'ximilar_success': True,
                'ximilar_objects': {'$exists': True, '$ne': []},
                'full_image_url': {'$exists': True}
            }
        },
        # Случайная выборка
        {'$sample': {'size': SAMPLE_SIZE}},
        # Выбираем только нужные поля
        {
            '$project': {
                '_id': 1,
                'image_url': 1,
                'full_image_url': 1,
                'local_path': 1,
                'username': 1,
                'post_id': 1,
                'timestamp': 1,
                'ximilar_objects': 1,
                'ximilar_tagged_at': 1
            }
        }
    ]

    sample_docs = list(collection.aggregate(pipeline))

    print(f"✅ Получено {len(sample_docs)} изображений")

    # Обрабатываем документы
    print(f"\n📋 Извлечение Ximilar атрибутов...")

    processed_samples = []
    for doc in sample_docs:
        # Извлекаем основную информацию из Ximilar
        ximilar_summary = extract_ximilar_summary(doc)

        sample_item = {
            'id': str(doc['_id']),
            'image_url': doc.get('full_image_url', doc.get('image_url')),
            'username': doc.get('username'),
            'post_id': doc.get('post_id'),
            'timestamp': doc.get('timestamp'),
            'ximilar_results': ximilar_summary,
            'ximilar_objects_count': len(doc.get('ximilar_objects', [])),
            'fashionclip_results': None  # Будет заполнено позже
        }

        processed_samples.append(sample_item)

    # Сохраняем в JSON
    print(f"\n💾 Сохранение в {OUTPUT_FILE}...")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    output_data = {
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'total_samples': len(processed_samples),
            'source': 'MongoDB instagram_gallery.images',
            'experiment': 'FashionCLIP vs Ximilar comparison'
        },
        'samples': processed_samples
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Сохранено {len(processed_samples)} образцов")

    # Статистика
    print(f"\n📈 Статистика:")
    total_categories = sum(len(s['ximilar_results']['categories']) for s in processed_samples)
    total_colors = sum(len(s['ximilar_results']['colors']) for s in processed_samples)
    total_materials = sum(len(s['ximilar_results']['materials']) for s in processed_samples)
    total_styles = sum(len(s['ximilar_results']['styles']) for s in processed_samples)

    print(f"  Всего категорий: {total_categories}")
    print(f"  Всего цветов: {total_colors}")
    print(f"  Всего материалов: {total_materials}")
    print(f"  Всего стилей: {total_styles}")

    # Примеры
    print(f"\n🎯 Пример первого образца:")
    if processed_samples:
        sample = processed_samples[0]
        print(f"  URL: {sample['image_url']}")
        print(f"  Категории: {[c['name'] for c in sample['ximilar_results']['categories'][:3]]}")
        print(f"  Цвета: {[c['name'] for c in sample['ximilar_results']['colors'][:3]]}")
        print(f"  Материалы: {[m['name'] for m in sample['ximilar_results']['materials'][:3]]}")
        print(f"  Стили: {[s['name'] for s in sample['ximilar_results']['styles'][:3]]}")

    client.close()
    print(f"\n✅ Датасет готов! Следующий шаг: запуск FashionCLIP")

if __name__ == '__main__':
    prepare_sample_dataset()
