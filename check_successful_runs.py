"""
Анализ успешных запусков Instagram скрапера
"""

import os
import json
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

def check_successful_runs():
    """Анализирует успешные запуски и их входные данные"""
    
    client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
    actor_id = "shu8hvrXbJbY3Eb9W"
    
    print("🔍 АНАЛИЗ УСПЕШНЫХ ЗАПУСКОВ INSTAGRAM СКРАПЕРА")
    print("="*60)
    
    try:
        # Получаем последние запуски
        runs = client.actor(actor_id).runs().list(limit=20)
        
        successful_runs = []
        for run in runs.items:
            if run.get('status') == 'SUCCEEDED':
                successful_runs.append(run)
        
        print(f"📊 Найдено {len(successful_runs)} успешных запусков")
        
        if successful_runs:
            print(f"\n📋 АНАЛИЗ УСПЕШНЫХ ЗАПУСКОВ:")
            print("-" * 40)
            
            for i, run in enumerate(successful_runs[:5]):  # Первые 5
                print(f"\n{i+1}. 🏃 Запуск ID: {run.get('id', 'N/A')}")
                print(f"   📅 Дата: {run.get('startedAt', 'N/A')}")
                print(f"   ⏱️ Длительность: {run.get('finishedAt', 'N/A')}")
                
                # Входные данные
                input_data = run.get('options', {}).get('input', {})
                if input_data:
                    print(f"   📝 Входные данные:")
                    for key, value in input_data.items():
                        if isinstance(value, str) and len(value) > 100:
                            value = value[:100] + "..."
                        print(f"      {key}: {value}")
                
                # Результаты
                dataset_id = run.get('defaultDatasetId')
                if dataset_id:
                    try:
                        dataset = client.dataset(dataset_id)
                        item_count = dataset.get().get('itemCount', 0)
                        print(f"   📊 Результатов: {item_count}")
                        
                        # Получаем образец данных
                        if item_count > 0:
                            items = dataset.list_items(limit=1).items
                            if items:
                                print(f"   📋 Образец данных:")
                                sample = items[0]
                                if isinstance(sample, dict):
                                    for key, value in list(sample.items())[:5]:
                                        if isinstance(value, str) and len(value) > 50:
                                            value = value[:50] + "..."
                                        print(f"      {key}: {value}")
                    except Exception as e:
                        print(f"   ❌ Ошибка получения результатов: {e}")
        
        # Анализируем входные данные
        print(f"\n📊 АНАЛИЗ ВХОДНЫХ ДАННЫХ:")
        print("-" * 30)
        
        all_input_keys = set()
        for run in successful_runs:
            input_data = run.get('options', {}).get('input', {})
            all_input_keys.update(input_data.keys())
        
        print(f"🔑 Всего уникальных полей: {len(all_input_keys)}")
        print(f"📝 Поля: {sorted(all_input_keys)}")
        
        # Показываем частоту использования полей
        field_usage = {}
        for run in successful_runs:
            input_data = run.get('options', {}).get('input', {})
            for key in input_data.keys():
                field_usage[key] = field_usage.get(key, 0) + 1
        
        print(f"\n📈 ЧАСТОТА ИСПОЛЬЗОВАНИЯ ПОЛЕЙ:")
        for field, count in sorted(field_usage.items(), key=lambda x: x[1], reverse=True):
            print(f"   {field}: {count} раз")
        
        # Сохраняем примеры входных данных
        examples = []
        for run in successful_runs[:3]:
            input_data = run.get('options', {}).get('input', {})
            if input_data:
                examples.append({
                    'run_id': run.get('id'),
                    'started_at': run.get('startedAt'),
                    'input': input_data
                })
        
        with open('successful_runs_examples.json', 'w', encoding='utf-8') as f:
            json.dump(examples, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Примеры успешных запусков сохранены в: successful_runs_examples.json")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_successful_runs()
