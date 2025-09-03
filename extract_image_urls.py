"""
Извлечение URL статичных изображений из данных Instagram
"""

import os
import json
import pandas as pd
from datetime import datetime

def extract_image_urls():
    """Извлекает URL изображений из данных Instagram"""
    
    print("🖼️ ИЗВЛЕЧЕНИЕ URL ИЗОБРАЖЕНИЙ ИЗ ДАННЫХ INSTAGRAM")
    print("="*60)
    
    # Ищем JSON файлы с данными
    import glob
    json_files = glob.glob("image_urls_*.json")
    
    if not json_files:
        print("❌ JSON файлы с данными не найдены")
        return None
    
    # Берем самый новый файл
    latest_file = max(json_files)
    print(f"📄 Используем файл: {latest_file}")
    
    try:
        # Загружаем данные
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Загружено {len(data)} постов")
        
        # Извлекаем URL изображений с удалением дубликатов
        image_urls = []
        seen_urls = set()  # Для отслеживания уже добавленных URL
        
        for i, post in enumerate(data):
            if isinstance(post, dict):
                post_info = {
                    'post_index': i + 1,
                    'shortCode': post.get('shortCode', 'N/A'),
                    'url': post.get('url', 'N/A'),
                    'type': post.get('type', 'N/A'),
                    'timestamp': post.get('timestamp', 'N/A'),
                    'likesCount': post.get('likesCount', 0),
                    'commentsCount': post.get('commentsCount', 0),
                    'caption': post.get('caption', '')[:100] + '...' if post.get('caption') else 'N/A'
                }
                
                # Основное изображение (displayUrl)
                if post.get('displayUrl'):
                    url = post['displayUrl']
                    if url not in seen_urls:
                        seen_urls.add(url)
                        image_info = post_info.copy()
                        image_info['image_url'] = url
                        image_info['image_type'] = 'main'
                        image_urls.append(image_info)
                
                # Дополнительные изображения (images array)
                if post.get('images'):
                    for j, img_url in enumerate(post['images']):
                        if isinstance(img_url, str) and img_url not in seen_urls:
                            seen_urls.add(img_url)
                            image_info = post_info.copy()
                            image_info['image_url'] = img_url
                            image_info['image_type'] = f'gallery_{j+1}'
                            image_urls.append(image_info)
                
                # Child posts (для Sidecar постов)
                if post.get('childPosts'):
                    for j, child_post in enumerate(post['childPosts']):
                        if isinstance(child_post, dict):
                            if child_post.get('displayUrl'):
                                url = child_post['displayUrl']
                                if url not in seen_urls:
                                    seen_urls.add(url)
                                    image_info = post_info.copy()
                                    image_info['image_url'] = url
                                    image_info['image_type'] = f'child_{j+1}'
                                    image_urls.append(image_info)
                            
                            if child_post.get('images'):
                                for k, img_url in enumerate(child_post['images']):
                                    if isinstance(img_url, str) and img_url not in seen_urls:
                                        seen_urls.add(img_url)
                                        image_info = post_info.copy()
                                        image_info['image_url'] = img_url
                                        image_info['image_type'] = f'child_{j+1}_gallery_{k+1}'
                                        image_urls.append(image_info)
        
        print(f"🖼️ Найдено {len(image_urls)} уникальных изображений")
        print(f"🔄 Дубликаты автоматически удалены")
        
        if image_urls:
            # Показываем первые несколько URL
            print(f"\n📋 ПЕРВЫЕ 10 URL ИЗОБРАЖЕНИЙ:")
            print("="*50)
            
            for i, img in enumerate(image_urls[:10]):
                print(f"\n{i+1}. 🖼️ Изображение:")
                print(f"   🔗 URL: {img['image_url']}")
                print(f"   📝 Тип: {img['image_type']}")
                print(f"   📸 Пост: {img['shortCode']}")
                print(f"   ❤️ Лайки: {img['likesCount']}")
                print(f"   📅 Дата: {img['timestamp']}")
            
            # Сохраняем в разные форматы
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON файл
            json_filename = f"image_urls_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(image_urls, f, ensure_ascii=False, indent=2)
            print(f"\n💾 JSON с URL изображений сохранен: {json_filename}")
            
            # CSV файл
            df = pd.DataFrame(image_urls)
            csv_filename = f"image_urls_{timestamp}.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"💾 CSV с URL изображений сохранен: {csv_filename}")
            
            # Простой текстовый файл только с URL
            txt_filename = f"image_urls_only_{timestamp}.txt"
            with open(txt_filename, 'w', encoding='utf-8') as f:
                for img in image_urls:
                    f.write(f"{img['image_url']}\n")
            print(f"💾 Текстовый файл с URL сохранен: {txt_filename}")
            
            # Статистика
            print(f"\n📊 СТАТИСТИКА ИЗОБРАЖЕНИЙ:")
            print("="*35)
            print(f"📈 Уникальных изображений: {len(image_urls)}")
            print(f"🔄 Дубликаты удалены автоматически")
            
            # Типы изображений
            image_types = {}
            for img in image_urls:
                img_type = img['image_type']
                image_types[img_type] = image_types.get(img_type, 0) + 1
            
            print(f"\n📝 Типы изображений:")
            for img_type, count in sorted(image_types.items()):
                print(f"   {img_type}: {count}")
            
            # Уникальные домены
            domains = set()
            for img in image_urls:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(img['image_url']).netloc
                    domains.add(domain)
                except:
                    pass
            
            print(f"\n🌐 Домены изображений:")
            for domain in sorted(domains):
                print(f"   {domain}")
            
            # Топ постов по количеству изображений
            post_image_counts = {}
            for img in image_urls:
                post_code = img['shortCode']
                post_image_counts[post_code] = post_image_counts.get(post_code, 0) + 1
            
            top_posts = sorted(post_image_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"\n📸 Топ-5 постов по количеству изображений:")
            for post_code, count in top_posts:
                print(f"   {post_code}: {count} изображений")
        
        return image_urls
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def download_images_sample(image_urls, max_images=5):
    """Скачивает несколько изображений для примера"""
    
    print(f"\n⬇️ СКАЧИВАНИЕ ПРИМЕРОВ ИЗОБРАЖЕНИЙ")
    print("="*40)
    
    try:
        import requests
        from urllib.parse import urlparse
        
        # Создаем папку для изображений
        os.makedirs('sample_images', exist_ok=True)
        
        # Скачиваем первые несколько изображений
        for i, img in enumerate(image_urls[:max_images]):
            try:
                url = img['image_url']
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    # Определяем расширение файла
                    parsed_url = urlparse(url)
                    filename = f"sample_images/image_{i+1}_{img['shortCode']}.jpg"
                    
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"✅ Скачано: {filename}")
                else:
                    print(f"❌ Ошибка скачивания {url}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Ошибка скачивания изображения {i+1}: {e}")
        
        print(f"\n💾 Примеры изображений сохранены в папку: sample_images/")
        
    except ImportError:
        print("⚠️ Для скачивания изображений установите requests: pip install requests")
    except Exception as e:
        print(f"❌ Ошибка скачивания: {e}")

if __name__ == "__main__":
    # Извлекаем URL изображений
    image_urls = extract_image_urls()
    
    if image_urls:
        print(f"\n🎉 Успешно извлечено {len(image_urls)} уникальных URL изображений!")
        print(f"🔄 Дубликаты автоматически удалены")
        
        # Предлагаем скачать примеры
        print(f"\n💡 Хотите скачать несколько примеров изображений? (y/n)")
        # Для автоматического режима скачиваем 3 примера
        download_images_sample(image_urls, max_images=3)
        
        print(f"\n📋 Теперь у вас есть:")
        print(f"   • JSON файл с полной информацией об уникальных изображениях")
        print(f"   • CSV файл для анализа (без дубликатов)")
        print(f"   • Текстовый файл только с уникальными URL")
        print(f"   • Примеры скачанных изображений")
    else:
        print("\n❌ Не удалось извлечь URL изображений")
