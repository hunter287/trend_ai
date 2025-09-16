"""
Instagram Parser через Apify с сохранением в MongoDB
"""

import os
import json
import requests
import pymongo
from datetime import datetime
from pathlib import Path
import argparse
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()
load_dotenv('mongodb_config.env')

class InstagramParser:
    def __init__(self, apify_token: str, mongodb_uri: str = None):
        """Инициализация парсера"""
        self.apify_token = apify_token
        self.mongodb_uri = mongodb_uri or os.getenv('MONGODB_URI', 'mongodb://trend_ai_user:LoGRomE2zJ0k0fuUhoTn@localhost:27017/instagram_gallery')
        self.client = None
        self.db = None
        self.collection = None
        
    def connect_mongodb(self):
        """Подключение к MongoDB"""
        try:
            self.client = pymongo.MongoClient(self.mongodb_uri)
            self.db = self.client["instagram_gallery"]
            self.collection = self.db["images"]
            print("✅ Подключение к MongoDB установлено")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к MongoDB: {e}")
            return False
    
    def parse_instagram_account(self, username: str, posts_limit: int = 100) -> Optional[Dict]:
        """Парсинг Instagram аккаунта через Apify"""
        print(f"🔍 Парсинг аккаунта: @{username}")
        
        try:
            from apify_client import ApifyClient
            import time
            
            print("🔗 Подключение к Apify...")
            client = ApifyClient(self.apify_token)
            print("✅ Подключение установлено")
            
            # Запуск Instagram scraper
            run_input = {
                "directUrls": [f"https://www.instagram.com/{username}/"],
                "resultsType": "posts",
                "resultsLimit": posts_limit,  # Используем переданный лимит
                "addParentData": False
            }
            
            print("📋 Параметры запуска:")
            print(f"   • URL: {run_input['directUrls'][0]}")
            print(f"   • Тип данных: {run_input['resultsType']}")
            print(f"   • Лимит: {run_input['resultsLimit']}")
            
            print("🚀 Запуск Apify актора...")
            print("⏳ Это может занять 30-60 секунд...")
            
            start_time = time.time()
            run = client.actor("apify/instagram-scraper").call(run_input=run_input)
            elapsed_time = time.time() - start_time
            
            print(f"⏱️ Актор выполнен за {elapsed_time:.1f} секунд")
            
            if run and run.get("defaultDatasetId"):
                print("📥 Получение данных из датасета...")
                dataset_id = run["defaultDatasetId"]
                print(f"   • ID датасета: {dataset_id}")
                
                dataset_items = client.dataset(dataset_id).list_items().items
                
                print(f"✅ Получено {len(dataset_items)} постов")
                return {
                    "username": username,
                    "posts": dataset_items,
                    "parsed_at": datetime.now().isoformat(),
                    "total_posts": len(dataset_items)
                }
            else:
                print("❌ Не удалось получить данные")
                print(f"   • Результат run: {run}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка парсинга: {e}")
            import traceback
            print("📋 Детали ошибки:")
            traceback.print_exc()
            return None
    
    def extract_image_urls(self, posts: List[Dict]) -> List[Dict]:
        """Извлечение URL изображений с удалением дубликатов"""
        print("🖼️ Извлечение URL изображений...")
        
        image_data = []
        seen_urls = set()
        
        for post in posts:
            if not isinstance(post, dict):
                continue
                
            post_info = {
                "post_id": post.get("shortCode", "N/A"),
                "username": post.get("ownerUsername", "N/A"),
                "timestamp": post.get("timestamp", "N/A"),
                "likes_count": post.get("likesCount", 0),
                "comments_count": post.get("commentsCount", 0),
                "caption": post.get("caption", "")[:200] + "..." if post.get("caption") else ""
            }
            
            # Основное изображение
            if post.get("displayUrl"):
                url = post["displayUrl"]
                if url not in seen_urls:
                    seen_urls.add(url)
                    image_data.append({
                        **post_info,
                        "image_url": url,
                        "image_type": "main"
                    })
            
            # Дополнительные изображения
            if post.get("images"):
                for img_url in post["images"]:
                    if isinstance(img_url, str) and img_url not in seen_urls:
                        seen_urls.add(img_url)
                        image_data.append({
                            **post_info,
                            "image_url": img_url,
                            "image_type": "gallery"
                        })
            
            # Child posts (карусели)
            if post.get("childPosts"):
                for child_post in post["childPosts"]:
                    if isinstance(child_post, dict):
                        if child_post.get("displayUrl"):
                            url = child_post["displayUrl"]
                            if url not in seen_urls:
                                seen_urls.add(url)
                                image_data.append({
                                    **post_info,
                                    "image_url": url,
                                    "image_type": "child"
                                })
        
        print(f"✅ Извлечено {len(image_data)} уникальных изображений")
        return image_data
    
    def download_images(self, image_data: List[Dict], max_images: int = 100) -> List[Dict]:
        """Скачивание изображений"""
        print(f"⬇️ Скачивание изображений (максимум {max_images})...")
        
        # Создаем папку для изображений
        images_dir = Path("images")
        images_dir.mkdir(exist_ok=True)
        print(f"📁 Папка для изображений: {images_dir.absolute()}")
        
        downloaded_data = []
        downloaded_count = 0
        total_to_download = min(max_images, len(image_data))
        
        print(f"📊 Всего к скачиванию: {total_to_download} изображений")
        
        for i, img_data in enumerate(image_data[:max_images]):
            try:
                url = img_data["image_url"]
                post_id = img_data["post_id"]
                img_type = img_data["image_type"]
                
                # Создаем имя файла
                filename = f"{post_id}_{img_type}_{i+1:04d}.jpg"
                filepath = images_dir / filename
                
                print(f"📥 [{i+1}/{total_to_download}] Скачивание: {filename}")
                
                # Скачиваем изображение
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    file_size = filepath.stat().st_size
                    print(f"✅ Скачано: {filename} ({file_size} байт)")
                    
                    # Добавляем информацию о скачанном файле
                    downloaded_data.append({
                        **img_data,
                        "local_filename": filename,
                        "local_path": str(filepath),
                        "file_size": file_size,
                        "downloaded_at": datetime.now().isoformat()
                    })
                    
                    downloaded_count += 1
                else:
                    print(f"❌ Ошибка скачивания {filename}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Ошибка скачивания изображения {i+1}: {e}")
        
        print(f"✅ Скачано {downloaded_count} изображений")
        return downloaded_data
    
    def save_to_mongodb(self, image_data: List[Dict], username: str):
        """Сохранение данных в MongoDB"""
        print("💾 Сохранение в MongoDB...")
        
        try:
            # Подготавливаем данные для MongoDB
            mongo_docs = []
            for img_data in image_data:
                doc = {
                    "instagram_url": f"https://www.instagram.com/{username}/",
                    "username": username,
                    "image_url": img_data["image_url"],
                    "post_id": img_data["post_id"],
                    "timestamp": img_data["timestamp"],
                    "likes_count": img_data["likes_count"],
                    "comments_count": img_data["comments_count"],
                    "caption": img_data["caption"],
                    "image_type": img_data["image_type"],
                    "parsed_at": datetime.now().isoformat()
                }
                
                # Добавляем информацию о локальном файле, если есть
                if "local_filename" in img_data:
                    # Полный URL к изображению на сервере
                    full_image_url = f"http://89.169.176.64/images/{img_data['local_filename']}"
                    
                    doc.update({
                        "local_filename": img_data["local_filename"],
                        "local_path": img_data["local_path"],
                        "full_image_url": full_image_url,  # Полный URL к изображению
                        "file_size": img_data["file_size"],
                        "downloaded_at": img_data["downloaded_at"]
                    })
                
                mongo_docs.append(doc)
            
            # Вставляем в MongoDB
            if mongo_docs:
                result = self.collection.insert_many(mongo_docs)
                print(f"✅ Сохранено {len(result.inserted_ids)} записей в MongoDB")
                
                # Создаем индексы для быстрого поиска
                self.collection.create_index("username")
                self.collection.create_index("image_url")
                self.collection.create_index("timestamp")
                print("✅ Созданы индексы для быстрого поиска")
            else:
                print("❌ Нет данных для сохранения")
                
        except Exception as e:
            print(f"❌ Ошибка сохранения в MongoDB: {e}")
    
    def create_gallery_html(self, image_data: List[Dict], username: str):
        """Создание HTML галереи"""
        print("🌐 Создание HTML галереи...")
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>@{username} - Instagram Gallery</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
        }}
        .stat {{
            text-align: center;
            padding: 10px;
            background: #e3f2fd;
            border-radius: 5px;
        }}
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
        }}
        .image-card {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        .image-card:hover {{
            transform: translateY(-5px);
        }}
        .image-card img {{
            width: 100%;
            height: 200px;
            object-fit: cover;
        }}
        .image-info {{
            padding: 15px;
        }}
        .post-id {{
            font-weight: bold;
            color: #1976d2;
        }}
        .likes {{
            color: #e91e63;
            font-size: 14px;
        }}
        .timestamp {{
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🖼️ @{username} - Instagram Gallery</h1>
        <div class="stats">
            <div class="stat">
                <h3>{len(image_data)}</h3>
                <p>Изображений</p>
            </div>
            <div class="stat">
                <h3>{datetime.now().strftime('%d.%m.%Y')}</h3>
                <p>Дата парсинга</p>
            </div>
        </div>
    </div>
    
    <div class="gallery">
"""

        # Добавляем изображения
        for img_data in image_data:
            if "local_filename" in img_data:
                # Используем полный URL к изображению на сервере
                img_src = f"http://89.169.176.64/images/{img_data['local_filename']}"
            else:
                img_src = img_data["image_url"]
                
            html_content += f"""
        <div class="image-card">
            <img src="{img_src}" alt="{img_data['post_id']}" loading="lazy">
            <div class="image-info">
                <div class="post-id">{img_data['post_id']}</div>
                <div class="likes">❤️ {img_data['likes_count']}</div>
                <div class="timestamp">{img_data['timestamp'][:10] if img_data['timestamp'] != 'N/A' else 'N/A'}</div>
            </div>
        </div>
        """

        html_content += """
    </div>
</body>
</html>
        """
        
        # Сохраняем HTML файл
        with open(f"gallery_{username}.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"🌐 HTML галерея создана: gallery_{username}.html")
    
    def run_full_parsing(self, username: str, max_images: int = 100, posts_limit: int = 100):
        """Полный цикл парсинга"""
        print(f"🚀 ЗАПУСК ПОЛНОГО ПАРСИНГА ДЛЯ @{username}")
        print("="*60)
        print(f"📊 Лимит постов: {posts_limit}")
        print(f"📥 Макс. изображений: {max_images}")
        
        # 1. Подключение к MongoDB
        if not self.connect_mongodb():
            return False
        
        # 2. Парсинг Instagram
        parsed_data = self.parse_instagram_account(username, posts_limit)
        if not parsed_data:
            return False
        
        # 3. Извлечение URL изображений
        image_data = self.extract_image_urls(parsed_data["posts"])
        if not image_data:
            print("❌ Не найдено изображений")
            return False
        
        # 4. Скачивание изображений
        downloaded_data = self.download_images(image_data, max_images)
        
        # 5. Сохранение в MongoDB
        self.save_to_mongodb(downloaded_data, username)
        
        # 6. Создание HTML галереи
        self.create_gallery_html(downloaded_data, username)
        
        print(f"\n🎉 ПАРСИНГ ЗАВЕРШЕН!")
        print(f"📊 Статистика:")
        print(f"   • Аккаунт: @{username}")
        print(f"   • Всего постов: {parsed_data['total_posts']}")
        print(f"   • Уникальных изображений: {len(image_data)}")
        print(f"   • Скачано изображений: {len(downloaded_data)}")
        print(f"   • Сохранено в MongoDB: {len(downloaded_data)}")
        print(f"   • HTML галерея: gallery_{username}.html")
        
        return True

def main():
    """Главная функция с интерфейсом командной строки"""
    parser = argparse.ArgumentParser(description="Instagram Parser через Apify")
    parser.add_argument("username", help="Имя пользователя Instagram (без @)")
    parser.add_argument("--max-images", type=int, default=100, help="Максимальное количество изображений для скачивания")
    parser.add_argument("--mongodb-uri", default="mongodb://localhost:27017/", help="URI MongoDB")
    
    args = parser.parse_args()
    
    # Получаем токен Apify из переменной окружения
    apify_token = os.getenv("APIFY_API_TOKEN")
    if not apify_token:
        print("❌ Не найден APIFY_API_TOKEN в переменных окружения")
        print("💡 Установите токен: export APIFY_API_TOKEN=your_token")
        return
    
    # Создаем парсер и запускаем
    parser_instance = InstagramParser(apify_token, args.mongodb_uri)
    success = parser_instance.run_full_parsing(args.username, args.max_images)
    
    if success:
        print(f"\n✅ Парсинг @{args.username} завершен успешно!")
    else:
        print(f"\n❌ Ошибка при парсинге @{args.username}")

if __name__ == "__main__":
    main()
