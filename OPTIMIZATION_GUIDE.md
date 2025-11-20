# Руководство по оптимизации аналитики

## Проблемы производительности

### Обнаруженные проблемы:

1. **Полное сканирование коллекции**: Каждый API эндпоинт делает `list(parser.collection.find(...))`, загружая ВСЕ документы в память
2. **Множественные подключения**: 9 параллельных запросов создают 9 подключений к MongoDB
3. **Неэффективная обработка**: Вложенные циклы по всем изображениям вместо aggregation
4. **Отсутствие индексов**: Нет оптимизации запросов
5. **Отсутствие кеширования**: Данные пересчитываются каждый раз

## Решение

### Шаг 1: Добавить индексы MongoDB

Запустите на сервере:

```bash
python3 add_analytics_indexes.py
```

Это создаст оптимальные индексы для:
- Фильтрации по `hidden`, `is_duplicate`, `ximilar_objects_structured`
- Временных запросов по `timestamp`

### Шаг 2: Интегрировать оптимизированную аналитику

#### 2.1. Добавить импорты в `web_parser.py` (в начало файла):

```python
from optimized_analytics import OptimizedAnalytics
from analytics_cache import analytics_cache
```

#### 2.2. Создать глобальный экземпляр оптимизированной аналитики

Добавьте после инициализации Flask app:

```python
# Создаем глобальное подключение к MongoDB для аналитики
def get_analytics_collection():
    """Получить коллекцию для аналитики (переиспользуемое подключение)"""
    from pymongo import MongoClient
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
    client = MongoClient(mongodb_uri)
    db = client.get_database()
    return db['images']

# Глобальный экземпляр оптимизированной аналитики
_analytics_collection = get_analytics_collection()
optimized_analytics = OptimizedAnalytics(_analytics_collection)
```

#### 2.3. Заменить API эндпоинты

Замените следующие эндпоинты на оптимизированные версии:

**1. `/api/analytics/categories-stats`:**

```python
@app.route('/api/analytics/categories-stats', methods=['GET'])
def api_analytics_categories_stats():
    """API для получения статистики по категориям (оптимизировано)"""
    try:
        categories = optimized_analytics.get_categories_stats()
        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})
```

**2. `/api/analytics/subcategories-stats`:**

```python
@app.route('/api/analytics/subcategories-stats', methods=['GET'])
def api_analytics_subcategories_stats():
    """API для получения статистики по подкатегориям (оптимизировано)"""
    try:
        subcategories = optimized_analytics.get_subcategories_stats()
        return jsonify({'success': True, 'subcategories': subcategories})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})
```

**3. `/api/analytics/colors-by-category`:**

```python
@app.route('/api/analytics/colors-by-category', methods=['GET'])
def api_analytics_colors_by_category():
    """API для получения статистики цветов по категориям (оптимизировано)"""
    try:
        colors = optimized_analytics.get_colors_by_category()
        return jsonify({'success': True, 'data': colors})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})
```

**4. `/api/analytics/materials-by-category`:**

```python
@app.route('/api/analytics/materials-by-category', methods=['GET'])
def api_analytics_materials_by_category():
    """API для получения статистики материалов по категориям (оптимизировано)"""
    try:
        materials = optimized_analytics.get_materials_by_category()
        return jsonify({'success': True, 'data': materials})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})
```

**5. `/api/analytics/styles-by-category`:**

```python
@app.route('/api/analytics/styles-by-category', methods=['GET'])
def api_analytics_styles_by_category():
    """API для получения статистики стилей по категориям (оптимизировано)"""
    try:
        styles = optimized_analytics.get_styles_by_category()
        return jsonify({'success': True, 'data': styles})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})
```

**6. `/api/analytics/top-accessories-stats`:**

```python
@app.route('/api/analytics/top-accessories-stats', methods=['GET'])
def api_analytics_top_accessories_stats():
    """API для получения топ-20 популярных аксессуаров (оптимизировано)"""
    try:
        items = optimized_analytics.get_top_items_by_category('Accessories')
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})
```

**7. `/api/analytics/top-clothing-stats`:**

```python
@app.route('/api/analytics/top-clothing-stats', methods=['GET'])
def api_analytics_top_clothing_stats():
    """API для получения топ-20 популярных одежды (оптимизировано)"""
    try:
        items = optimized_analytics.get_top_items_by_category('Clothing')
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})
```

**8. `/api/analytics/top-footwear-stats`:**

```python
@app.route('/api/analytics/top-footwear-stats', methods=['GET'])
def api_analytics_top_footwear_stats():
    """API для получения топ-20 популярных обуви (оптимизировано)"""
    try:
        items = optimized_analytics.get_top_items_by_category('Footwear')
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})
```

### Шаг 3: Добавить эндпоинт для очистки кеша

Добавьте в `web_parser.py`:

```python
@app.route('/api/analytics/clear-cache', methods=['POST'])
def api_analytics_clear_cache():
    """API для очистки кеша аналитики"""
    try:
        analytics_cache.clear()
        return jsonify({'success': True, 'message': 'Кеш очищен'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})
```

## Ожидаемые улучшения

После применения всех оптимизаций:

1. **Скорость загрузки**: ~50-100x быстрее (вместо полного сканирования - aggregation)
2. **Использование памяти**: ~90% меньше (не загружаем все в память)
3. **Кеширование**: Повторные запросы отвечают мгновенно (5 минут TTL)
4. **Подключения**: Переиспользуем одно подключение вместо создания новых
5. **Индексы**: MongoDB использует индексы для быстрой фильтрации

## Тестирование

1. Запустите `check_collection_size.py` для проверки индексов
2. Перезапустите Flask сервер
3. Откройте страницу аналитики
4. Проверьте логи на наличие ошибок
5. Замерьте время загрузки страницы

## Мониторинг

Для мониторинга производительности добавьте логирование:

```python
import time
import logging

logger = logging.getLogger(__name__)

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        elapsed = time.time() - request.start_time
        if elapsed > 1.0:  # Логируем медленные запросы
            logger.warning(f"Slow request: {request.path} took {elapsed:.2f}s")
    return response
```

## Очистка кеша

Кеш автоматически инвалидируется через 5 минут. Для ручной очистки:

```bash
curl -X POST http://your-server/api/analytics/clear-cache
```

Или добавьте кнопку на страницу аналитики.
