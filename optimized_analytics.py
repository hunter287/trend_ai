"""Оптимизированные функции аналитики с использованием MongoDB aggregation"""

import logging
from analytics_cache import cached
from collections import defaultdict

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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
        # Используем aggregation с проекцией для уменьшения нагрузки
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
                                "subcategory": {
                                    "$cond": [
                                        {"$ne": [{"$ifNull": ["$$obj.properties.other_attributes.Subcategory", null]}, null]},
                                        {"$arrayElemAt": ["$$obj.properties.other_attributes.Subcategory.name", 0]},
                                        {
                                            "$cond": [
                                                {"$ne": [{"$ifNull": ["$$obj.properties.other_attributes.Category", null]}, null]},
                                                {"$arrayElemAt": ["$$obj.properties.other_attributes.Category.name", 0]},
                                                null
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        ]

        # Получаем данные с помощью aggregation (более эффективно)
        images = list(self.collection.aggregate(pipeline, allowDiskUse=True))

        # Подсчитываем подкатегории с дедупликацией на уровне Python (минимальная обработка)
        subcategory_counts = defaultdict(int)

        for image in images:
            seen = set()
            for obj in image.get('ximilar_objects_structured', []):
                category = obj.get('top_category', 'Other')
                subcategory = obj.get('subcategory')

                if subcategory:
                    key = f"{category}:{subcategory}"
                    if key not in seen:
                        seen.add(key)
                        subcategory_counts[key] += 1

        # Топ-10
        top_subcategories = sorted(subcategory_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        return [{'name': k.split(':')[1], 'category': k.split(':')[0], 'count': v} for k, v in top_subcategories]

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
        """Получить топ-20 популярных вещей для категории (подкатегория без цвета)"""
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

        # Подсчет с дедупликацией (только подкатегория, без цвета)
        item_counts = defaultdict(int)

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

        # Топ-20
        top_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        result = [{'name': k, 'count': v} for k, v in top_items]
        logger.info(f"✅ get_top_items_by_category('{category}') вернул {len(result)} вещей")
        return result
