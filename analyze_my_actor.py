"""
Детальный анализ вашего актора

Этот скрипт показывает:
1. Полную информацию об акторе
2. Схему входных данных
3. Код актора (если доступен)
4. Историю запусков
5. Примеры использования
"""

import os
import json
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

def analyze_my_actor():
    """Детальный анализ вашего актора"""
    
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    print("✅ Подключение к Apify API установлено")
    
    # ID вашего актора
    actor_id = "shu8hvrXbJbY3Eb9W"
    
    print(f"\n🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ВАШЕГО АКТОРА")
    print("="*60)
    print(f"🆔 ID актора: {actor_id}")
    
    try:
        # Получаем полную информацию об акторе
        actor_info = client.actor(actor_id).get()
        
        print(f"\n📋 ОСНОВНАЯ ИНФОРМАЦИЯ:")
        print("-" * 30)
        print(f"🎭 Название: {actor_info.get('name', 'N/A')}")
        print(f"📝 Описание: {actor_info.get('description', 'N/A')}")
        print(f"👤 Автор: {actor_info.get('username', 'N/A')}")
        print(f"📅 Создан: {actor_info.get('createdAt', 'N/A')}")
        print(f"🔄 Обновлен: {actor_info.get('modifiedAt', 'N/A')}")
        print(f"🏷️ Теги: {', '.join(actor_info.get('taggedTemplateIds', []))}")
        
        # Статистика
        stats = actor_info.get('stats', {})
        print(f"\n📊 СТАТИСТИКА:")
        print("-" * 20)
        print(f"🏃 Всего запусков: {stats.get('totalRuns', 0)}")
        print(f"⭐ Рейтинг: {stats.get('rating', 'N/A')}")
        print(f"💰 Средняя стоимость: {stats.get('averageComputeUnits', 'N/A')} единиц")
        
        # Схема входных данных
        input_schema = actor_info.get('inputSchema', {})
        if input_schema:
            print(f"\n📋 СХЕМА ВХОДНЫХ ДАННЫХ:")
            print("-" * 30)
            
            required_fields = input_schema.get('required', [])
            properties = input_schema.get('properties', {})
            
            print(f"🔴 Обязательные поля: {required_fields}")
            print(f"\n📝 Все поля:")
            
            for field_name, field_info in properties.items():
                required = "🔴 ОБЯЗАТЕЛЬНО" if field_name in required_fields else "🟢 Опционально"
                description = field_info.get('description', 'Нет описания')
                field_type = field_info.get('type', 'unknown')
                default_value = field_info.get('default', 'Нет значения по умолчанию')
                
                print(f"\n   🔹 {field_name} ({field_type})")
                print(f"      {description}")
                print(f"      {required}")
                if default_value != 'Нет значения по умолчанию':
                    print(f"      💡 По умолчанию: {default_value}")
                
                # Показываем возможные значения для enum
                if 'enum' in field_info:
                    print(f"      📋 Возможные значения: {field_info['enum']}")
        
        # Пытаемся получить код актора
        print(f"\n💻 КОД АКТОРА:")
        print("-" * 20)
        try:
            # Получаем файлы актора
            files = client.actor(actor_id).files().list()
            if files.items:
                print(f"📁 Файлы в акторе:")
                for file in files.items:
                    print(f"   • {file.get('name', 'N/A')} ({file.get('size', 0)} байт)")
                    
                    # Показываем содержимое основных файлов
                    if file.get('name') in ['main.js', 'main.py', 'README.md', 'package.json']:
                        try:
                            file_content = client.actor(actor_id).file(file['name']).get()
                            print(f"   📄 Содержимое {file['name']}:")
                            print(f"   {'-' * 40}")
                            # Показываем первые 500 символов
                            content_preview = str(file_content)[:500]
                            print(f"   {content_preview}")
                            if len(str(file_content)) > 500:
                                print(f"   ... (еще {len(str(file_content)) - 500} символов)")
                            print(f"   {'-' * 40}")
                        except Exception as e:
                            print(f"   ❌ Не удалось прочитать файл: {e}")
            else:
                print("📁 Файлы не найдены или недоступны")
        except Exception as e:
            print(f"❌ Ошибка получения файлов: {e}")
        
        # История запусков
        print(f"\n📈 ИСТОРИЯ ЗАПУСКОВ:")
        print("-" * 25)
        try:
            runs = client.actor(actor_id).runs().list(limit=10)
            if runs.items:
                for i, run in enumerate(runs.items):
                    status_emoji = {
                        'SUCCEEDED': '✅',
                        'FAILED': '❌', 
                        'ABORTED': '⚠️',
                        'RUNNING': '🏃',
                        'READY': '⏳'
                    }.get(run.get('status', ''), '❓')
                    
                    print(f"   {i+1}. {status_emoji} {run.get('status', 'N/A')} - {run.get('startedAt', 'N/A')}")
                    
                    # Показываем входные данные для успешных запусков
                    if run.get('status') == 'SUCCEEDED' and run.get('options', {}).get('input'):
                        input_data = run['options']['input']
                        print(f"      📝 Входные данные:")
                        for key, value in list(input_data.items())[:3]:
                            if isinstance(value, str) and len(value) > 50:
                                value = value[:50] + "..."
                            print(f"         {key}: {value}")
            else:
                print("📭 Нет запусков")
        except Exception as e:
            print(f"❌ Ошибка получения истории запусков: {e}")
        
        # Примеры использования
        print(f"\n💡 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:")
        print("-" * 30)
        
        # Генерируем примеры на основе схемы
        if input_schema and properties:
            example_input = {}
            for field_name, field_info in properties.items():
                if field_name in required_fields:
                    # Генерируем примерное значение
                    field_type = field_info.get('type', 'string')
                    if field_type == 'string':
                        if 'enum' in field_info:
                            example_input[field_name] = field_info['enum'][0]
                        else:
                            example_input[field_name] = f"example_{field_name}"
                    elif field_type == 'integer':
                        example_input[field_name] = 10
                    elif field_type == 'boolean':
                        example_input[field_name] = True
                    elif field_type == 'array':
                        example_input[field_name] = ["example1", "example2"]
                    else:
                        example_input[field_name] = f"example_{field_name}"
            
            print("📝 Пример входных данных:")
            print(json.dumps(example_input, indent=2, ensure_ascii=False))
            
            print(f"\n🚀 Пример запуска:")
            print(f"```python")
            print(f"client = ApifyClient('ваш_токен')")
            print(f"run = client.actor('{actor_id}').call(run_input={json.dumps(example_input, indent=2, ensure_ascii=False)})")
            print(f"```")
        
        return actor_info
        
    except Exception as e:
        print(f"❌ Ошибка анализа актора: {e}")
        return None

if __name__ == "__main__":
    analyze_my_actor()
