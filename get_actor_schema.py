"""
Получение схемы входных данных актора
"""

import os
import json
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

def get_actor_schema():
    """Получает схему входных данных актора"""
    
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    
    # ID Instagram скрапера
    actor_id = "shu8hvrXbJbY3Eb9W"
    
    try:
        actor_info = client.actor(actor_id).get()
        input_schema = actor_info.get('inputSchema', {})
        
        print("📋 СХЕМА ВХОДНЫХ ДАННЫХ INSTAGRAM СКРАПЕРА")
        print("="*60)
        
        if input_schema:
            required_fields = input_schema.get('required', [])
            properties = input_schema.get('properties', {})
            
            print(f"🔴 Обязательные поля: {required_fields}")
            print(f"\n📝 Все поля:")
            
            for field_name, field_info in properties.items():
                required = "🔴 ОБЯЗАТЕЛЬНО" if field_name in required_fields else "🟢 Опционально"
                description = field_info.get('description', 'Нет описания')
                field_type = field_info.get('type', 'unknown')
                default_value = field_info.get('default')
                
                print(f"\n🔹 {field_name} ({field_type})")
                print(f"   {description}")
                print(f"   {required}")
                
                if default_value is not None:
                    print(f"   💡 По умолчанию: {default_value}")
                
                # Показываем возможные значения для enum
                if 'enum' in field_info:
                    print(f"   📋 Возможные значения: {field_info['enum']}")
                
                # Показываем примеры
                if 'examples' in field_info:
                    print(f"   📝 Примеры: {field_info['examples']}")
        
        # Сохраняем схему в файл
        with open('instagram_actor_schema.json', 'w', encoding='utf-8') as f:
            json.dump(input_schema, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Схема сохранена в: instagram_actor_schema.json")
        
        return input_schema
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

if __name__ == "__main__":
    get_actor_schema()
