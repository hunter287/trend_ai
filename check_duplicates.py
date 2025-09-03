"""
Проверка дубликатов URL изображений
"""

import json
import pandas as pd
from collections import Counter

def check_duplicates():
    """Проверяет дубликаты URL изображений"""
    
    print("🔍 ПРОВЕРКА ДУБЛИКАТОВ URL ИЗОБРАЖЕНИЙ")
    print("="*50)
    
    # Ищем JSON файл с URL изображений
    import glob
    json_files = glob.glob("image_urls_*.json")
    
    if not json_files:
        print("❌ JSON файлы с URL изображений не найдены")
        return None
    
    # Берем самый новый файл
    latest_file = max(json_files)
    print(f"📄 Используем файл: {latest_file}")
    
    try:
        # Загружаем данные
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Загружено {len(data)} записей об изображениях")
        
        # Извлекаем все URL
        all_urls = [item['image_url'] for item in data]
        print(f"🔗 Всего URL: {len(all_urls)}")
        
        # Проверяем уникальность
        unique_urls = set(all_urls)
        print(f"🔗 Уникальных URL: {len(unique_urls)}")
        
        # Подсчитываем дубликаты
        url_counts = Counter(all_urls)
        duplicates = {url: count for url, count in url_counts.items() if count > 1}
        
        print(f"\n📊 РЕЗУЛЬТАТЫ АНАЛИЗА ДУБЛИКАТОВ:")
        print("="*40)
        print(f"📈 Всего URL: {len(all_urls)}")
        print(f"🔗 Уникальных URL: {len(unique_urls)}")
        print(f"🔄 Дубликатов: {len(all_urls) - len(unique_urls)}")
        print(f"📋 URL с дубликатами: {len(duplicates)}")
        
        if duplicates:
            print(f"\n🔄 ТОП-10 URL С НАИБОЛЬШИМ КОЛИЧЕСТВОМ ДУБЛИКАТОВ:")
            print("-" * 50)
            
            # Сортируем по количеству дубликатов
            sorted_duplicates = sorted(duplicates.items(), key=lambda x: x[1], reverse=True)
            
            for i, (url, count) in enumerate(sorted_duplicates[:10]):
                print(f"\n{i+1}. 🔗 URL встречается {count} раз:")
                print(f"   {url[:100]}...")
                
                # Показываем информацию о дубликатах
                duplicate_items = [item for item in data if item['image_url'] == url]
                print(f"   📝 В постах:")
                for item in duplicate_items:
                    print(f"      • {item['shortCode']} ({item['image_type']}) - {item['timestamp']}")
        
        # Анализ по типам изображений
        print(f"\n📊 АНАЛИЗ ДУБЛИКАТОВ ПО ТИПАМ ИЗОБРАЖЕНИЙ:")
        print("-" * 45)
        
        type_analysis = {}
        for item in data:
            img_type = item['image_type']
            if img_type not in type_analysis:
                type_analysis[img_type] = {'total': 0, 'unique': 0, 'duplicates': 0}
            
            type_analysis[img_type]['total'] += 1
        
        # Подсчитываем уникальные URL для каждого типа
        for img_type in type_analysis:
            type_urls = [item['image_url'] for item in data if item['image_type'] == img_type]
            unique_type_urls = set(type_urls)
            type_analysis[img_type]['unique'] = len(unique_type_urls)
            type_analysis[img_type]['duplicates'] = len(type_urls) - len(unique_type_urls)
        
        for img_type, stats in sorted(type_analysis.items()):
            print(f"   {img_type}:")
            print(f"      📈 Всего: {stats['total']}")
            print(f"      🔗 Уникальных: {stats['unique']}")
            print(f"      🔄 Дубликатов: {stats['duplicates']}")
            if stats['duplicates'] > 0:
                duplicate_rate = (stats['duplicates'] / stats['total']) * 100
                print(f"      📊 Процент дубликатов: {duplicate_rate:.1f}%")
        
        # Анализ по постам
        print(f"\n📊 АНАЛИЗ ДУБЛИКАТОВ ПО ПОСТАМ:")
        print("-" * 35)
        
        post_analysis = {}
        for item in data:
            post_code = item['shortCode']
            if post_code not in post_analysis:
                post_analysis[post_code] = {'total': 0, 'unique': 0, 'duplicates': 0}
            
            post_analysis[post_code]['total'] += 1
        
        # Подсчитываем уникальные URL для каждого поста
        for post_code in post_analysis:
            post_urls = [item['image_url'] for item in data if item['shortCode'] == post_code]
            unique_post_urls = set(post_urls)
            post_analysis[post_code]['unique'] = len(unique_post_urls)
            post_analysis[post_code]['duplicates'] = len(post_urls) - len(unique_post_urls)
        
        # Показываем посты с наибольшим количеством дубликатов
        posts_with_duplicates = {post: stats for post, stats in post_analysis.items() if stats['duplicates'] > 0}
        
        if posts_with_duplicates:
            print(f"📋 Посты с дубликатами ({len(posts_with_duplicates)} из {len(post_analysis)}):")
            
            sorted_posts = sorted(posts_with_duplicates.items(), key=lambda x: x[1]['duplicates'], reverse=True)
            
            for i, (post_code, stats) in enumerate(sorted_posts[:10]):
                print(f"   {i+1}. {post_code}: {stats['duplicates']} дубликатов из {stats['total']} изображений")
        else:
            print("✅ Дубликатов в постах не найдено")
        
        # Создаем отчет
        report = {
            'summary': {
                'total_urls': len(all_urls),
                'unique_urls': len(unique_urls),
                'duplicates': len(all_urls) - len(unique_urls),
                'duplicate_urls': len(duplicates)
            },
            'duplicate_details': dict(sorted_duplicates[:20]),  # Топ-20 дубликатов
            'type_analysis': type_analysis,
            'post_analysis': {post: stats for post, stats in post_analysis.items() if stats['duplicates'] > 0}
        }
        
        # Сохраняем отчет
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"duplicates_report_{timestamp}.json"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Отчет о дубликатах сохранен: {report_filename}")
        
        # Создаем файл с уникальными URL
        unique_urls_list = list(unique_urls)
        unique_filename = f"unique_image_urls_{timestamp}.txt"
        
        with open(unique_filename, 'w', encoding='utf-8') as f:
            for url in unique_urls_list:
                f.write(f"{url}\n")
        
        print(f"💾 Файл с уникальными URL сохранен: {unique_filename}")
        
        return {
            'total_urls': len(all_urls),
            'unique_urls': len(unique_urls),
            'duplicates': len(all_urls) - len(unique_urls),
            'duplicate_urls': len(duplicates)
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

if __name__ == "__main__":
    result = check_duplicates()
    
    if result:
        print(f"\n🎉 Анализ завершен!")
        print(f"📊 Итого: {result['duplicates']} дубликатов из {result['total_urls']} URL")
        
        if result['duplicates'] > 0:
            duplicate_percentage = (result['duplicates'] / result['total_urls']) * 100
            print(f"📈 Процент дубликатов: {duplicate_percentage:.1f}%")
        else:
            print("✅ Дубликатов не найдено!")
    else:
        print("\n❌ Анализ не удался")
