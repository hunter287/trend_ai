"""Модуль кеширования для аналитики"""

import time
from functools import wraps
from threading import Lock

class AnalyticsCache:
    """Простой кеш с TTL для результатов аналитики"""

    def __init__(self, ttl=300):  # TTL по умолчанию 5 минут
        self.cache = {}
        self.ttl = ttl
        self.lock = Lock()

    def get(self, key):
        """Получить значение из кеша"""
        with self.lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    return data
                else:
                    del self.cache[key]
        return None

    def set(self, key, value):
        """Сохранить значение в кеш"""
        with self.lock:
            self.cache[key] = (value, time.time())

    def clear(self):
        """Очистить весь кеш"""
        with self.lock:
            self.cache.clear()

    def invalidate(self, pattern=None):
        """Инвалидировать кеш по паттерну"""
        with self.lock:
            if pattern is None:
                self.cache.clear()
            else:
                keys_to_delete = [k for k in self.cache.keys() if pattern in k]
                for key in keys_to_delete:
                    del self.cache[key]


# Глобальный экземпляр кеша
analytics_cache = AnalyticsCache(ttl=300)  # 5 минут


def cached(key_func=None):
    """
    Декоратор для кеширования результатов функций

    Args:
        key_func: функция для генерации ключа кеша из аргументов
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Генерируем ключ кеша
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}"

            # Проверяем кеш
            cached_result = analytics_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Вычисляем результат
            result = func(*args, **kwargs)

            # Сохраняем в кеш
            analytics_cache.set(cache_key, result)

            return result
        return wrapper
    return decorator
