#!/usr/bin/env python3
"""
Скрипт для обработки изображений через FashionCLIP (ДЕТАЛИЗИРОВАННАЯ ВЕРСИЯ)
с расширенным списком специфичных категорий одежды
"""

import json
import os
import sys
from PIL import Image
import requests
from io import BytesIO
import torch
import open_clip
from tqdm import tqdm
from datetime import datetime

# Параметры
INPUT_FILE = 'data/sample_images.json'
OUTPUT_FILE = 'data/fashionclip_results_detailed.json'

# Расширенные словари атрибутов с более специфичными терминами
ATTRIBUTE_PROMPTS = {
    'categories': [
        # Куртки и пальто (детализировано)
        'leather jacket', 'denim jacket', 'bomber jacket', 'biker jacket',
        'blazer', 'suit jacket', 'jean jacket',
        'trench coat', 'puffer jacket', 'peacoat', 'parka', 'overcoat',
        'windbreaker', 'rain jacket',

        # Верхняя часть (детализировано)
        'crop top', 'tank top', 'camisole', 'tube top', 'halter top',
        't-shirt', 'graphic tee', 'polo shirt', 'henley shirt',
        'button-up shirt', 'oxford shirt', 'dress shirt', 'flannel shirt',
        'blouse', 'tunic', 'bodysuit', 'corset top',

        # Свитера и толстовки (детализировано)
        'sweater', 'pullover sweater', 'knit sweater', 'cable knit sweater',
        'cardigan', 'cardigan sweater', 'zip cardigan',
        'turtleneck', 'turtleneck sweater', 'mock neck',
        'hoodie', 'pullover hoodie', 'zip hoodie',
        'sweatshirt', 'crewneck sweatshirt',

        # Платья (детализировано)
        'maxi dress', 'midi dress', 'mini dress', 'knee-length dress',
        'wrap dress', 'shift dress', 'sheath dress',
        'shirt dress', 'slip dress', 'sundress',
        'bodycon dress', 'fit and flare dress', 'a-line dress',
        'cocktail dress', 'party dress', 'evening gown',
        'casual dress', 'summer dress',

        # Брюки (детализировано)
        'jeans', 'skinny jeans', 'straight-leg jeans', 'boyfriend jeans',
        'mom jeans', 'wide-leg jeans', 'flared jeans', 'bootcut jeans',
        'ripped jeans', 'distressed jeans', 'denim jeans',
        'pants', 'trousers', 'dress pants', 'slacks',
        'wide-leg pants', 'straight pants', 'cigarette pants',
        'cargo pants', 'joggers', 'sweatpants', 'track pants',
        'leggings', 'yoga pants', 'skinny pants',

        # Юбки (детализировано)
        'mini skirt', 'short skirt',
        'midi skirt', 'knee-length skirt',
        'maxi skirt', 'long skirt',
        'pencil skirt', 'a-line skirt', 'pleated skirt',
        'wrap skirt', 'denim skirt', 'leather skirt',

        # Шорты (детализировано)
        'shorts', 'denim shorts', 'jean shorts',
        'bermuda shorts', 'cargo shorts', 'athletic shorts',

        # Сумки (детализировано)
        'handbag', 'purse',
        'tote bag', 'shoulder bag', 'crossbody bag',
        'clutch', 'clutch bag', 'evening bag',
        'backpack', 'mini backpack',
        'messenger bag', 'satchel',

        # Очки (детализировано)
        'sunglasses', 'eyewear',
        'aviator sunglasses', 'cat-eye sunglasses',
        'round sunglasses', 'oversized sunglasses',
        'sport sunglasses',

        # Головные уборы (детализировано)
        'hat', 'cap',
        'baseball cap', 'snapback', 'dad hat',
        'beanie', 'winter hat',
        'fedora', 'wide-brim hat', 'sun hat',
        'bucket hat', 'beret',
    ],

    'colors': [
        # Базовые цвета
        'black', 'white', 'gray', 'grey', 'charcoal',

        # Коричневые оттенки
        'brown', 'light brown', 'dark brown',
        'beige', 'tan', 'camel', 'khaki', 'cream', 'ivory',

        # Красные оттенки
        'red', 'bright red', 'dark red', 'burgundy', 'maroon', 'wine',
        'pink', 'light pink', 'hot pink', 'rose', 'blush',

        # Оранжевые оттенки
        'orange', 'burnt orange', 'coral', 'peach',

        # Желтые оттенки
        'yellow', 'mustard', 'gold', 'golden',

        # Зеленые оттенки
        'green', 'dark green', 'olive', 'emerald', 'mint', 'lime',

        # Синие оттенки
        'blue', 'light blue', 'sky blue', 'royal blue',
        'navy', 'navy blue', 'dark blue',
        'teal', 'turquoise', 'cyan',

        # Фиолетовые оттенки
        'purple', 'lavender', 'violet', 'plum',

        # Паттерны
        'multicolor', 'colorful', 'rainbow',
        'patterned', 'printed', 'striped', 'floral', 'plaid', 'checkered',
    ],

    'materials': [
        # Натуральные ткани
        'cotton', 'organic cotton', '100% cotton',
        'linen', 'hemp',
        'wool', 'merino wool', 'cashmere',
        'silk', 'satin silk',

        # Синтетические ткани
        'polyester', 'synthetic', 'nylon', 'spandex', 'elastane',
        'acrylic', 'rayon', 'viscose',

        # Деним
        'denim', 'jean', 'chambray',

        # Кожа и замша
        'leather', 'genuine leather', 'faux leather', 'vegan leather',
        'suede', 'faux suede',

        # Специальные материалы
        'velvet', 'corduroy',
        'lace', 'mesh', 'net',
        'satin', 'chiffon', 'organza',
        'fleece', 'sherpa', 'fur', 'faux fur',
        'knit', 'knitted', 'ribbed knit', 'cable knit',
        'jersey', 'french terry',

        # Свойства
        'transparent', 'sheer', 'see-through',
        'textured', 'quilted', 'embroidered',
    ],

    'styles': [
        # Общие стили
        'casual', 'everyday', 'relaxed',
        'formal', 'dressy', 'elegant', 'sophisticated',
        'business', 'office', 'professional', 'workwear',

        # Специфичные стили
        'sporty', 'athletic', 'activewear', 'athleisure',
        'streetwear', 'street style', 'urban',
        'preppy', 'collegiate',
        'bohemian', 'boho', 'hippie',
        'grunge', 'edgy', 'punk', 'rock',
        'vintage', 'retro', '90s style', 'y2k',

        # Модные стили
        'modern', 'contemporary', 'minimalist', 'clean',
        'classic', 'timeless', 'traditional',
        'trendy', 'fashionable', 'stylish',
        'chic', 'sleek',

        # Случаи
        'party', 'clubwear', 'going out',
        'evening', 'cocktail', 'formal event',
        'vacation', 'resort', 'beachwear',

        # Сезоны
        'summer', 'spring', 'fall', 'autumn', 'winter',
        'warm weather', 'cold weather',
    ]
}

class FashionCLIPAnalyzer:
    def __init__(self):
        """Инициализация модели FashionCLIP"""
        print(f"📦 Загрузка FashionCLIP модели (Marqo)...")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🖥️  Устройство: {self.device}")

        # Загружаем модель Marqo FashionCLIP
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            'hf-hub:Marqo/marqo-fashionCLIP'
        )
        self.model = self.model.to(self.device).eval()
        self.tokenizer = open_clip.get_tokenizer('hf-hub:Marqo/marqo-fashionCLIP')

        print(f"✅ Модель загружена")

        # Статистика по словарям
        for key, values in ATTRIBUTE_PROMPTS.items():
            print(f"   {key}: {len(values)} вариантов")

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
            # Препроцессинг изображения
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

            # Формируем текстовые промпты
            text_prompts = [f"a photo of {candidate}" for candidate in candidates]
            text_tokens = self.tokenizer(text_prompts).to(self.device)

            # Получаем embeddings
            with torch.no_grad(), torch.cuda.amp.autocast():
                image_features = self.model.encode_image(image_tensor, normalize=True)
                text_features = self.model.encode_text(text_tokens, normalize=True)

                # Вычисляем similarity scores
                similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
                probs = similarity[0]

            # Получаем топ-k результатов
            top_indices = probs.argsort(descending=True)[:top_k]

            results = []
            for idx in top_indices:
                results.append({
                    'name': candidates[idx.item()],
                    'confidence': float(probs[idx].item())
                })

            return results

        except Exception as e:
            print(f"  ⚠️  Ошибка классификации {attribute_type}: {e}")
            return []

    def analyze_image(self, image_url):
        """Полный анализ изображения"""
        # Загружаем изображение
        image = self.load_image_from_url(image_url)

        if image is None:
            return None

        results = {}

        # Классифицируем по каждому типу атрибутов
        # Увеличиваем top_k для более детальных результатов
        for attr_type, candidates in ATTRIBUTE_PROMPTS.items():
            if attr_type == 'categories':
                top_k = 5  # Больше вариантов для категорий
            elif attr_type == 'colors':
                top_k = 5
            else:
                top_k = 3

            results[attr_type] = self.classify_attributes(
                image, attr_type, candidates, top_k=top_k
            )

        return results

def process_dataset():
    """Обработать весь датасет через FashionCLIP"""
    print(f"\n🔍 Обработка датасета через FashionCLIP (Детализированная версия)\n")

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
    data['metadata']['fashionclip_version'] = 'detailed'

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
                print(f"  Категории:")
                for c in fc.get('categories', [])[:5]:
                    print(f"    - {c['name']}: {c['confidence']:.3f}")
                print(f"  Цвета:")
                for c in fc.get('colors', [])[:5]:
                    print(f"    - {c['name']}: {c['confidence']:.3f}")

    print(f"\n✅ Готово! Следующий шаг: сравнение с базовой версией")

if __name__ == '__main__':
    process_dataset()
