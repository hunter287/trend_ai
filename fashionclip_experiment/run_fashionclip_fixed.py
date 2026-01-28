#!/usr/bin/env python3
"""
Скрипт для обработки изображений через FashionCLIP (ИСПРАВЛЕННАЯ ВЕРСИЯ)
и извлечения атрибутов одежды
"""

import json
import os
import sys
from PIL import Image
import requests
from io import BytesIO
from tqdm import tqdm
from datetime import datetime
from fashion_clip.fashion_clip import FashionCLIP

# Параметры
INPUT_FILE = 'data/sample_images.json'
OUTPUT_FILE = 'data/fashionclip_results.json'

# Словари атрибутов для классификации (основаны на Ximilar данных)
ATTRIBUTE_PROMPTS = {
    'categories': [
        'jacket', 'coat', 'dress', 'shirt', 'blouse', 'top', 'crop top',
        'pants', 'jeans', 'trousers', 'skirt', 'shorts',
        'sweater', 'cardigan', 'hoodie', 't-shirt',
        'accessories', 'bag', 'handbag', 'eyewear', 'sunglasses', 'hat'
    ],
    'colors': [
        'black', 'white', 'gray', 'grey', 'brown', 'beige', 'tan',
        'red', 'pink', 'orange', 'yellow', 'gold',
        'green', 'blue', 'navy', 'purple', 'violet',
        'multicolor', 'colorful', 'patterned'
    ],
    'materials': [
        'cotton', 'denim', 'leather', 'synthetic', 'polyester',
        'wool', 'silk', 'satin', 'velvet', 'lace',
        'knit', 'knitted', 'mesh', 'transparent', 'sheer',
        'suede', 'fur', 'fleece', 'nylon', 'textile'
    ],
    'styles': [
        'casual', 'formal', 'elegant', 'sporty', 'athletic',
        'vintage', 'retro', 'modern', 'classic', 'minimalist',
        'bohemian', 'boho', 'grunge', 'street style', 'preppy',
        'business', 'office', 'party', 'evening', 'summer', 'winter'
    ]
}

class FashionCLIPAnalyzer:
    def __init__(self):
        """Инициализация модели FashionCLIP"""
        print(f"📦 Загрузка FashionCLIP модели...")

        # Создаём пустой датасет (нужен для инициализации, но не используется)
        from fashion_clip.fashion_clip import FCLIPDataset
        dummy_dataset = FCLIPDataset(
            'dummy',
            image_source_path='.',
            image_source_type='local',
            catalog=[{'id': 1, 'image': 'dummy.jpg', 'caption': 'dummy'}]
        )

        self.fclip = FashionCLIP('fashion-clip', dummy_dataset)
        print(f"✅ Модель загружена")

    def load_image_from_url(self, url, timeout=10):
        """Загрузить изображение по URL"""
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content)).convert('RGB')
            return image
        except Exception as e:
            print(f"  ⚠️  Ошибка загрузки изображения: {e}")
            return None

    def classify_attributes(self, image, attribute_type, candidates, top_k=5):
        """Классифицировать атрибуты изображения"""
        if image is None:
            return []

        try:
            # Используем zero_shot_classification
            # Нужно сохранить image временно, т.к. API ожидает путь к файлу
            temp_path = '/tmp/temp_fashion_image.jpg'
            image.save(temp_path)

            # FashionCLIP zero_shot_classification возвращает вероятности
            results = self.fclip.zero_shot_classification(
                [temp_path],
                candidates
            )

            # Результаты - это список вероятностей для каждого кандидата
            if results and len(results) > 0:
                probs = results[0]  # Берём результаты для первого (и единственного) изображения

                # Создаём список (индекс, вероятность)
                indexed_probs = [(i, prob) for i, prob in enumerate(probs)]
                # Сортируем по убыванию вероятности
                indexed_probs.sort(key=lambda x: x[1], reverse=True)

                # Берём топ-k
                top_results = []
                for idx, prob in indexed_probs[:top_k]:
                    top_results.append({
                        'name': candidates[idx],
                        'confidence': float(prob)
                    })

                # Удаляем временный файл
                if os.path.exists(temp_path):
                    os.remove(temp_path)

                return top_results
            else:
                return []

        except Exception as e:
            print(f"  ⚠️  Ошибка классификации {attribute_type}: {e}")
            # Пытаемся удалить временный файл
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
            return []

    def analyze_image(self, image_url):
        """Полный анализ изображения"""
        # Загружаем изображение
        image = self.load_image_from_url(image_url)

        if image is None:
            return None

        results = {}

        # Классифицируем по каждому типу атрибутов
        for attr_type, candidates in ATTRIBUTE_PROMPTS.items():
            top_k = 5 if attr_type == 'colors' else 3
            results[attr_type] = self.classify_attributes(
                image, attr_type, candidates, top_k=top_k
            )

        return results

def process_dataset():
    """Обработать весь датасет через FashionCLIP"""
    print(f"\n🔍 Обработка датасета через FashionCLIP\n")

    # Загружаем датасет
    print(f"📂 Загрузка датасета из {INPUT_FILE}...")

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Файл {INPUT_FILE} не найден!")
        print(f"   Сначала запустите: python prepare_dataset.py")
        sys.exit(1)

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    samples = data['samples']
    print(f"✅ Загружено {len(samples)} образцов")

    # Инициализируем анализатор
    analyzer = FashionCLIPAnalyzer()

    # Обрабатываем каждое изображение
    print(f"\n🎨 Анализ изображений...\n")

    processed_count = 0
    failed_count = 0

    for i, sample in enumerate(tqdm(samples, desc="Обработка")):
        image_url = sample['image_url']

        try:
            # Анализируем изображение
            fashionclip_results = analyzer.analyze_image(image_url)

            if fashionclip_results:
                sample['fashionclip_results'] = fashionclip_results
                processed_count += 1
            else:
                sample['fashionclip_results'] = {
                    'error': 'Failed to analyze image'
                }
                failed_count += 1

        except Exception as e:
            print(f"\n  ❌ Ошибка обработки образца {i+1}: {e}")
            sample['fashionclip_results'] = {
                'error': str(e)
            }
            failed_count += 1

    # Обновляем метаданные
    data['metadata']['fashionclip_processed_at'] = datetime.now().isoformat()
    data['metadata']['fashionclip_processed_count'] = processed_count
    data['metadata']['fashionclip_failed_count'] = failed_count

    # Сохраняем результаты
    print(f"\n💾 Сохранение результатов в {OUTPUT_FILE}...")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Обработка завершена!")
    print(f"   Успешно: {processed_count}")
    print(f"   Ошибки: {failed_count}")

    # Статистика
    if processed_count > 0:
        print(f"\n📈 Статистика FashionCLIP:")

        all_categories = []
        all_colors = []
        all_materials = []
        all_styles = []

        for sample in samples:
            fc_results = sample.get('fashionclip_results', {})
            if 'error' not in fc_results:
                all_categories.extend([c['name'] for c in fc_results.get('categories', [])])
                all_colors.extend([c['name'] for c in fc_results.get('colors', [])])
                all_materials.extend([m['name'] for m in fc_results.get('materials', [])])
                all_styles.extend([s['name'] for s in fc_results.get('styles', [])])

        print(f"  Уникальных категорий: {len(set(all_categories))}")
        print(f"  Уникальных цветов: {len(set(all_colors))}")
        print(f"  Уникальных материалов: {len(set(all_materials))}")
        print(f"  Уникальных стилей: {len(set(all_styles))}")

        # Примеры топ результатов
        if samples and samples[0].get('fashionclip_results'):
            print(f"\n🎯 Пример результата для первого изображения:")
            fc = samples[0]['fashionclip_results']
            if 'error' not in fc:
                cats = [(c['name'], c['confidence']) for c in fc.get('categories', [])[:3]]
                colors = [(c['name'], c['confidence']) for c in fc.get('colors', [])[:3]]
                mats = [(m['name'], m['confidence']) for m in fc.get('materials', [])[:3]]
                styles = [(s['name'], s['confidence']) for s in fc.get('styles', [])[:3]]
                print(f"  Категории: {cats}")
                print(f"  Цвета: {colors}")
                print(f"  Материалы: {mats}")
                print(f"  Стили: {styles}")

    print(f"\n✅ Готово! Следующий шаг: генерация HTML отчёта")

if __name__ == '__main__':
    process_dataset()
