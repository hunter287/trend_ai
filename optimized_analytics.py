"""Оптимизированные функции аналитики с использованием MongoDB aggregation"""

import logging
from analytics_cache import cached
from collections import defaultdict

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def normalize_subcategory_name(subcategory, category):
    """
    Нормализует название подкатегории для группировки В КОНТЕКСТЕ категории.
    Импортировано из web_parser.py
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


class OptimizedAnalytics:
    """Класс с оптимизированными методами аналитики"""

    def __init__(self, collection):
        self.collection = collection

    @cached()
    def get_categories_stats(self):
        """Получить статистику по категориям (оптимизировано через aggregation)"""
        logger.info("🔄 Вызов get_categories_stats()")
        pipeline = [
            {
                "$match": {
                    "ximilar_objects_structured": {"$exists": True, "$ne": []},
                    "hidden": {"$ne": True},
                    "is_duplicate": {"$ne": True}
                }
            },
            {"$unwind": "$ximilar_objects_structured"},
            {
                "$group": {
                    "_id": "$ximilar_objects_structured.top_category",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}}
        ]

        categories = list(self.collection.aggregate(pipeline, allowDiskUse=True))
        result = [{'name': c['_id'] or 'Other', 'count': c['count']} for c in categories]
        logger.info(f"✅ get_categories_stats() вернул {len(result)} категорий")
        return result

    @cached()
    def get_subcategories_stats(self):
        """Получить статистику по подкатегориям (с дедупликацией на уровне изображения)"""
        logger.info("🔄 Вызов get_subcategories_stats()")

        # Упрощенный pipeline - получаем только нужные данные
        pipeline = [
            {
                "$match": {
                    "ximilar_objects_structured": {"$exists": True, "$ne": []},
                    "hidden": {"$ne": True},
                    "is_duplicate": {"$ne": True}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "ximilar_objects_structured": 1
                }
            }
        ]

        # Получаем данные
        images = list(self.collection.aggregate(pipeline, allowDiskUse=True))
        logger.info(f"   Получено {len(images)} изображений из БД")

        # Подсчитываем подкатегории с дедупликацией и нормализацией
        subcategory_counts = defaultdict(int)

        for image in images:
            seen = set()
            for obj in image.get('ximilar_objects_structured', []):
                category = obj.get('top_category', 'Other')
                subcategory = ''

                # Извлекаем подкатегорию
                if obj.get('properties', {}).get('other_attributes'):
                    if obj['properties']['other_attributes'].get('Subcategory'):
                        subcategory = obj['properties']['other_attributes']['Subcategory'][0]['name']
                    elif obj['properties']['other_attributes'].get('Category'):
                        subcategory = obj['properties']['other_attributes']['Category'][0]['name']

                if subcategory:
                    # Нормализуем название подкатегории
                    normalized = normalize_subcategory_name(subcategory, category)
                    key = f"{category}:{normalized}"

                    if key not in seen:
                        seen.add(key)
                        subcategory_counts[key] += 1

        # Топ-10
        top_subcategories = sorted(subcategory_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        result = [{'name': k.split(':')[1], 'category': k.split(':')[0], 'count': v} for k, v in top_subcategories]
        logger.info(f"✅ get_subcategories_stats() вернул {len(result)} подкатегорий")
        return result

    @cached()
    def get_colors_by_category(self):
        """Получить статистику цветов по категориям"""
        pipeline = [
            {
                "$match": {
                    "ximilar_objects_structured": {"$exists": True, "$ne": []},
                    "hidden": {"$ne": True},
                    "is_duplicate": {"$ne": True}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "ximilar_objects_structured": {
                        "$map": {
                            "input": "$ximilar_objects_structured",
                            "as": "obj",
                            "in": {
                                "top_category": "$$obj.top_category",
                                "colors": "$$obj.properties.visual_attributes.Color"
                            }
                        }
                    }
                }
            }
        ]

        images = list(self.collection.aggregate(pipeline, allowDiskUse=True))

        # Подсчет по категориям
        color_counts_by_category = {
            'Clothing': defaultdict(int),
            'Accessories': defaultdict(int),
            'Footwear': defaultdict(int)
        }

        for image in images:
            seen_by_category = defaultdict(set)

            for obj in image.get('ximilar_objects_structured', []):
                category = obj.get('top_category')
                colors = obj.get('colors', [])

                if category in color_counts_by_category and colors:
                    for color in colors:
                        color_name = color.get('name')
                        if color_name and color_name not in seen_by_category[category]:
                            seen_by_category[category].add(color_name)
                            color_counts_by_category[category][color_name] += 1

        # Топ-15 для каждой категории
        result = {}
        for category, counts in color_counts_by_category.items():
            top_colors = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:15]
            result[category] = [{'name': k, 'count': v} for k, v in top_colors]

        return result

    @cached()
    def get_materials_by_category(self):
        """Получить статистику материалов по категориям"""
        pipeline = [
            {
                "$match": {
                    "ximilar_objects_structured": {"$exists": True, "$ne": []},
                    "hidden": {"$ne": True},
                    "is_duplicate": {"$ne": True}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "ximilar_objects_structured": {
                        "$map": {
                            "input": "$ximilar_objects_structured",
                            "as": "obj",
                            "in": {
                                "top_category": "$$obj.top_category",
                                "materials": "$$obj.properties.material_attributes.Material"
                            }
                        }
                    }
                }
            }
        ]

        images = list(self.collection.aggregate(pipeline, allowDiskUse=True))

        # Подсчет по категориям
        material_counts_by_category = {
            'Clothing': defaultdict(int),
            'Accessories': defaultdict(int),
            'Footwear': defaultdict(int)
        }

        for image in images:
            seen_by_category = defaultdict(set)

            for obj in image.get('ximilar_objects_structured', []):
                category = obj.get('top_category')
                materials = obj.get('materials', [])

                if category in material_counts_by_category and materials:
                    for material in materials:
                        material_name = material.get('name')
                        if material_name and material_name not in seen_by_category[category]:
                            seen_by_category[category].add(material_name)
                            material_counts_by_category[category][material_name] += 1

        # Топ-10 для каждой категории
        result = {}
        for category, counts in material_counts_by_category.items():
            top_materials = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
            result[category] = [{'name': k, 'count': v} for k, v in top_materials]

        return result

    @cached()
    def get_styles_by_category(self):
        """Получить статистику стилей по категориям"""
        pipeline = [
            {
                "$match": {
                    "ximilar_objects_structured": {"$exists": True, "$ne": []},
                    "hidden": {"$ne": True},
                    "is_duplicate": {"$ne": True}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "ximilar_objects_structured": {
                        "$map": {
                            "input": "$ximilar_objects_structured",
                            "as": "obj",
                            "in": {
                                "top_category": "$$obj.top_category",
                                "styles": "$$obj.properties.style_attributes.Style"
                            }
                        }
                    }
                }
            }
        ]

        images = list(self.collection.aggregate(pipeline, allowDiskUse=True))

        # Подсчет по категориям
        style_counts_by_category = {
            'Clothing': defaultdict(int),
            'Accessories': defaultdict(int),
            'Footwear': defaultdict(int)
        }

        for image in images:
            seen_by_category = defaultdict(set)

            for obj in image.get('ximilar_objects_structured', []):
                category = obj.get('top_category')
                styles = obj.get('styles', [])

                if category in style_counts_by_category and styles:
                    for style in styles:
                        style_name = style.get('name')
                        if style_name and style_name not in seen_by_category[category]:
                            seen_by_category[category].add(style_name)
                            style_counts_by_category[category][style_name] += 1

        # Топ-10 для каждой категории
        result = {}
        for category, counts in style_counts_by_category.items():
            top_styles = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
            result[category] = [{'name': k, 'count': v} for k, v in top_styles]

        return result

    @cached(key_func=lambda self, category: f"top_items_{category}")
    def get_top_items_by_category(self, category):
        """Получить топ-20 популярных вещей для категории с детальным описанием (цвет, материал, стиль)"""
        logger.info(f"🔄 Вызов get_top_items_by_category(category='{category}')")

        # Используем более простой pipeline для извлечения только нужных данных
        pipeline = [
            {
                "$match": {
                    "ximilar_objects_structured": {"$exists": True, "$ne": []},
                    "hidden": {"$ne": True},
                    "is_duplicate": {"$ne": True}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "ximilar_objects_structured": 1
                }
            }
        ]

        images = list(self.collection.aggregate(pipeline, allowDiskUse=True))
        logger.info(f"   Получено {len(images)} изображений из БД")

        # Подсчет с дедупликацией + сбор атрибутов
        item_counts = defaultdict(int)
        item_attributes = defaultdict(lambda: {
            'colors': defaultdict(int),
            'materials': defaultdict(int),
            'styles': defaultdict(int)
        })

        for image in images:
            seen = set()

            for obj in image.get('ximilar_objects_structured', []):
                obj_category = obj.get('top_category', 'Other')

                # Фильтруем только нужную категорию
                if obj_category != category:
                    continue

                # Извлекаем подкатегорию
                subcategory = None
                if obj.get('properties', {}).get('other_attributes'):
                    if obj['properties']['other_attributes'].get('Subcategory'):
                        subcategory = obj['properties']['other_attributes']['Subcategory'][0]['name']

                # Пропускаем записи без конкретной подкатегории
                if not subcategory:
                    continue

                # Дедупликация в рамках одного изображения
                if subcategory not in seen:
                    seen.add(subcategory)
                    item_counts[subcategory] += 1

                    # Собираем атрибуты для этой подкатегории
                    props = obj.get('properties', {})

                    # Цвета
                    colors = props.get('visual_attributes', {}).get('Color', [])
                    if colors and len(colors) > 0:
                        top_color = colors[0].get('name')
                        if top_color:
                            item_attributes[subcategory]['colors'][top_color] += 1

                    # Материалы
                    materials = props.get('material_attributes', {}).get('Material', [])
                    if materials and len(materials) > 0:
                        top_material = materials[0].get('name')
                        if top_material:
                            item_attributes[subcategory]['materials'][top_material] += 1

                    # Стили
                    styles = props.get('style_attributes', {}).get('Style', [])
                    if styles and len(styles) > 0:
                        top_style = styles[0].get('name')
                        if top_style:
                            item_attributes[subcategory]['styles'][top_style] += 1

        # Топ-20 подкатегорий
        top_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        # Формируем результат с детальным описанием
        result = []
        for subcategory, count in top_items:
            attrs = item_attributes[subcategory]

            # Выбираем самый популярный цвет, материал, стиль
            top_color = max(attrs['colors'].items(), key=lambda x: x[1])[0] if attrs['colors'] else None
            top_material = max(attrs['materials'].items(), key=lambda x: x[1])[0] if attrs['materials'] else None
            top_style = max(attrs['styles'].items(), key=lambda x: x[1])[0] if attrs['styles'] else None

            # Формируем детальное название
            details = []
            if top_color:
                details.append(top_color)
            if top_material:
                details.append(top_material)
            if top_style:
                details.append(top_style)

            if details:
                detailed_name = f"{subcategory} ({', '.join(details)})"
            else:
                detailed_name = subcategory

            result.append({
                'name': detailed_name,
                'subcategory': subcategory,  # Сохраняем чистое имя подкатегории для фильтрации
                'count': count,
                'color': top_color,
                'material': top_material,
                'style': top_style
            })

        logger.info(f"✅ get_top_items_by_category('{category}') вернул {len(result)} вещей")
        return result
