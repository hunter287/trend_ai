#!/usr/bin/env python3
"""Очистка кэша аналитики"""

from analytics_cache import analytics_cache

print("🔄 Очистка кэша аналитики...")
analytics_cache.clear()
print("✅ Кэш очищен!")
