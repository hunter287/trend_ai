"""
Instagram Parser через Apify с сохранением в MongoDB
"""

import os
import json
import requests
import pymongo
import imagehash
from PIL import Image
from io import BytesIO
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
    
    def calculate_perceptual_hash(self, image_data: bytes) -> str:
        """Вычисление perceptual hash изображения
        
        Args:
            image_data: Байты изображения
            
        Returns:
            Строковое представление perceptual hash
        """
        try:
            # Открываем изображение из байтов
            image = Image.open(BytesIO(image_data))
            
            # Вычисляем perceptual hash (pHash)
            # pHash более устойчив к изменениям, чем average hash
            phash = imagehash.phash(image, hash_size=8)
            
            return str(phash)
        except Exception as e:
            print(f"❌ Ошибка вычисления perceptual hash: {e}")
            return None
    
    def is_duplicate_by_hash(self, image_hash: str, threshold: int = 5) -> Optional[Dict]:
        """Проверка на дубликаты по perceptual hash
        
        Args:
            image_hash: Perceptual hash изображения
            threshold: Пороговое значение различия (Hamming distance)
                      0 = точное совпадение
                      5 = допускаем небольшие различия (сжатие, фильтры)
                      10 = более мягкая проверка
            
        Returns:
            Документ дубликата из БД или None
        """
        try:
            if not image_hash:
                return None
            
            # Получаем все хеши из БД
            existing_hashes = self.collection.find(
                {"image_hash": {"$exists": True}},
                {"image_hash": 1, "image_url": 1, "post_id": 1, "_id": 1}
            )
            
            current_hash = imagehash.hex_to_hash(image_hash)
            
            # Проверяем каждый хеш на похожесть
            for doc in existing_hashes:
                try:
                    existing_hash = imagehash.hex_to_hash(doc["image_hash"])
                    # Вычисляем Hamming distance (количество различающихся битов)
                    distance = current_hash - existing_hash
                    
                    if distance <= threshold:
                        print(f"🔍 Найден дубликат! Hamming distance: {distance}")
                        print(f"   Существующий: {doc.get('post_id', 'N/A')}")
                        return doc
                except Exception as e:
                    continue
            
            return None
        except Exception as e:
            print(f"❌ Ошибка проверки дубликатов по хешу: {e}")
            return None
    
    def parse_instagram_account(self, username: str, posts_limit: int = 100, date_from: str = None) -> Optional[Dict]:
        """Парсинг Instagram аккаунта через Apify
        
        Args:
            username: имя аккаунта Instagram
            posts_limit: максимальное количество постов
            date_from: дата начала в формате YYYY-MM-DD (опционально)
                      Парсит все посты с этой даты до сегодня
        """
        print(f"\n{'='*60}")
        print(f"🔍 [PARSER] Парсинг аккаунта: @{username}")
        print(f"📊 [PARSER] Лимит постов: {posts_limit}")
        print(f"📅 [PARSER] С даты: {date_from} до сегодня")
        print(f"{'='*60}")
        
        try:
            from apify_client import ApifyClient
            import time
            
            print("🔗 [PARSER] Подключение к Apify...")
            client = ApifyClient(self.apify_token)
            print("✅ [PARSER] Подключение к Apify установлено")
            
            # Запуск Instagram scraper
            run_input = {
                "directUrls": [f"https://www.instagram.com/{username}/"],
                "resultsType": "posts",
                "resultsLimit": posts_limit,  # Используем переданный лимит
                "addParentData": False
            }
            
            # Используем onlyPostsNewerThan для ограничения по дате
            # Этот параметр останавливает парсинг когда достигается указанная дата
            if date_from:
                run_input["onlyPostsNewerThan"] = date_from
                print(f"   • [PARSER] Парсить посты новее чем: {date_from}")
            
            print("📋 [PARSER] Параметры запуска Apify:")
            print(f"   • URL: {run_input['directUrls'][0]}")
            print(f"   • Тип данных: {run_input['resultsType']}")
            print(f"   • Лимит: {run_input['resultsLimit']}")
            if date_from:
                print(f"   • onlyPostsNewerThan: {run_input['onlyPostsNewerThan']}")
            
            print("🚀 [PARSER] Запуск Apify актора...")
            print(f"⚠️ [PARSER] Внимание: с фильтром по датам это может занять 2-5 минут...")
            print(f"🔑 [PARSER] Используется токен: {self.apify_token[:10]}...{self.apify_token[-4:]}")
            
            start_time = time.time()
            print(f"⏰ [PARSER] Время начала: {datetime.now().strftime('%H:%M:%S')}")
            
            # ВАЖНО: Вызов актора может занять много времени с большим лимитом
            print(f"⏳ [PARSER] Вызов актора с таймаутом 600 секунд (10 минут)...")
            run = client.actor("apify/instagram-scraper").call(
                run_input=run_input,
                timeout_secs=600  # Таймаут 10 минут
            )
            
            elapsed_time = time.time() - start_time
            print(f"⏱️ [PARSER] Актор выполнен за {elapsed_time:.1f} секунд")
            print(f"📦 [PARSER] Результат run: {run}")
            
            if run and run.get("defaultDatasetId"):
                print("📥 [PARSER] Получение данных из датасета...")
                dataset_id = run["defaultDatasetId"]
                print(f"   • [PARSER] ID датасета: {dataset_id}")
                
                dataset_items = client.dataset(dataset_id).list_items().items
                
                print(f"✅ [PARSER] Получено {len(dataset_items)} постов")
                print(f"{'='*60}\n")
                return {
                    "username": username,
                    "posts": dataset_items,
                    "parsed_at": datetime.now().isoformat(),
                    "total_posts": len(dataset_items)
                }
            else:
                print("❌ [PARSER] Не удалось получить данные")
                print(f"   • [PARSER] Результат run: {run}")
                print(f"{'='*60}\n")
                return None
                
        except Exception as e:
            print(f"❌ [PARSER] Ошибка парсинга: {e}")
            import traceback
            print("📋 [PARSER] Детали ошибки:")
            traceback.print_exc()
            print(f"{'='*60}\n")
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
        """Скачивание изображений с проверкой дубликатов"""
        print(f"⬇️ Скачивание изображений (максимум {max_images})...")
        
        # Создаем папку для изображений
        images_dir = Path("images")
        images_dir.mkdir(exist_ok=True)
        print(f"📁 Папка для изображений: {images_dir.absolute()}")
        
        downloaded_data = []
        downloaded_count = 0
        skipped_count = 0
        total_to_download = min(max_images, len(image_data))
        
        print(f"📊 Всего к скачиванию: {total_to_download} изображений")
        
        for i, img_data in enumerate(image_data[:max_images]):
            try:
                url = img_data["image_url"]
                post_id = img_data["post_id"]
                img_type = img_data["image_type"]
                
                # Проверяем, есть ли уже изображения с этим post_id в БД
                if self.is_image_exists(url, post_id):
                    print(f"⏭️ [{i+1}/{total_to_download}] Пропуск дубликата по post_id: {post_id}")
                    skipped_count += 1
                    continue
                
                # Проверяем, нужно ли скачивать изображение (только по локальному файлу)
                filename = f"{post_id}_{img_type}_{i+1:04d}.jpg"
                filepath = images_dir / filename
                
                if filepath.exists():
                    print(f"⏭️ [{i+1}/{total_to_download}] Файл уже существует: {filename}")
                    # Добавляем информацию о существующем файле
                    downloaded_data.append({
                        **img_data,
                        "local_filename": filename,
                        "local_path": str(filepath),
                        "file_size": filepath.stat().st_size,
                        "downloaded_at": datetime.now().isoformat()
                    })
                    skipped_count += 1
                    continue
                
                
                print(f"📥 [{i+1}/{total_to_download}] Скачивание: {filename}")
                
                # Скачиваем изображение
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    image_content = response.content
                    
                    # Вычисляем perceptual hash
                    print(f"🔢 Вычисление perceptual hash...")
                    image_hash = self.calculate_perceptual_hash(image_content)
                    
                    if image_hash:
                        # Проверяем на дубликаты по perceptual hash
                        duplicate = self.is_duplicate_by_hash(image_hash, threshold=5)
                        
                        if duplicate:
                            print(f"⏭️ [{i+1}/{total_to_download}] Найден визуальный дубликат!")
                            print(f"   Оригинал: {duplicate.get('post_id', 'N/A')}")
                            print(f"   Текущий: {post_id}")
                            skipped_count += 1
                            continue
                    
                    # Сохраняем файл
                    with open(filepath, 'wb') as f:
                        f.write(image_content)
                    
                    file_size = filepath.stat().st_size
                    print(f"✅ Скачано: {filename} ({file_size} байт)")
                    if image_hash:
                        print(f"   Hash: {image_hash}")
                    
                    # Добавляем информацию о скачанном файле
                    downloaded_data.append({
                        **img_data,
                        "local_filename": filename,
                        "local_path": str(filepath),
                        "file_size": file_size,
                        "downloaded_at": datetime.now().isoformat(),
                        "image_hash": image_hash  # Добавляем perceptual hash
                    })
                    
                    downloaded_count += 1
                else:
                    print(f"❌ Ошибка скачивания {filename}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Ошибка скачивания изображения {i+1}: {e}")
        
        print(f"✅ Скачано {downloaded_count} изображений")
        print(f"⏭️ Пропущено {skipped_count} дубликатов")
        return downloaded_data
    
    def is_image_exists(self, image_url: str, post_id: str = None) -> bool:
        """Проверка существования изображения в MongoDB"""
        try:
            # Проверяем по URL изображения
            if self.collection.find_one({"image_url": image_url}):
                return True
            
            # Дополнительная проверка по post_id, если указан
            if post_id and self.collection.find_one({"post_id": post_id}):
                return True
                
            return False
        except Exception as e:
            print(f"❌ Ошибка проверки дубликатов: {e}")
            return False

    def get_existing_images(self, image_urls: List[str], post_ids: List[str] = None) -> set:
        """Массовая проверка существующих изображений"""
        try:
            existing_urls = set()
            existing_posts = set()
            
            # Проверяем по URL изображений
            if image_urls:
                cursor = self.collection.find(
                    {"image_url": {"$in": image_urls}}, 
                    {"image_url": 1, "_id": 0}
                )
                existing_urls = {doc["image_url"] for doc in cursor}
            
            # Проверяем по post_id, если указаны
            if post_ids:
                cursor = self.collection.find(
                    {"post_id": {"$in": post_ids}}, 
                    {"post_id": 1, "_id": 0}
                )
                existing_posts = {doc["post_id"] for doc in cursor}
            
            return existing_urls, existing_posts
        except Exception as e:
            print(f"❌ Ошибка массовой проверки дубликатов: {e}")
            return set(), set()

    def save_to_mongodb(self, image_data: List[Dict], username: str):
        """Сохранение данных в MongoDB с проверкой дубликатов"""
        print("💾 Сохранение в MongoDB...")
        
        try:
            # Массовая проверка дубликатов для оптимизации
            image_urls = [img_data["image_url"] for img_data in image_data]
            post_ids = [img_data["post_id"] for img_data in image_data]
            existing_urls, existing_posts = self.get_existing_images(image_urls, post_ids)
            
            # Подготавливаем данные для MongoDB с проверкой дубликатов
            mongo_docs = []
            skipped_count = 0
            
            for img_data in image_data:
                # Проверяем, существует ли изображение
                if (img_data["image_url"] in existing_urls or 
                    img_data["post_id"] in existing_posts):
                    print(f"⏭️ Пропуск дубликата: {img_data['image_url']}")
                    skipped_count += 1
                    continue
                
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
                    "parsed_at": datetime.now().isoformat(),
                    "selected_for_tagging": False,
                    "selected_at": None
                }
                
                # Добавляем информацию о локальном файле, если есть
                if "local_filename" in img_data:
                    # Полный URL к изображению на сервере
                    full_image_url = f"http://158.160.19.119:5000/images/{img_data['local_filename']}"
                    
                    doc.update({
                        "local_filename": img_data["local_filename"],
                        "local_path": img_data["local_path"],
                        "full_image_url": full_image_url,  # Полный URL к изображению
                        "file_size": img_data["file_size"],
                        "downloaded_at": img_data["downloaded_at"]
                    })
                
                # Добавляем perceptual hash, если есть
                if "image_hash" in img_data and img_data["image_hash"]:
                    doc["image_hash"] = img_data["image_hash"]
                
                mongo_docs.append(doc)
            
            # Вставляем в MongoDB
            if mongo_docs:
                result = self.collection.insert_many(mongo_docs)
                print(f"✅ Сохранено {len(result.inserted_ids)} новых записей в MongoDB")
                
                # Создаем индексы для быстрого поиска
                self.collection.create_index("username")
                self.collection.create_index("image_url")
                self.collection.create_index("timestamp")
                self.collection.create_index("selected_for_tagging")
                self.collection.create_index("image_hash")  # Индекс для perceptual hash
                print("✅ Созданы индексы для быстрого поиска")
            else:
                print("❌ Нет новых данных для сохранения")
            
            # Выводим статистику
            total_processed = len(image_data)
            new_saved = len(mongo_docs)
            print(f"📊 Статистика: обработано {total_processed}, сохранено {new_saved}, пропущено дубликатов {skipped_count}")
            
            return new_saved
                
        except Exception as e:
            print(f"❌ Ошибка сохранения в MongoDB: {e}")
    
    def create_gallery_html(self, image_data: List[Dict], username: str):
        """Создание HTML галереи с фильтрами"""
        print("🌐 Создание HTML галереи с фильтрами...")
        
        # Читаем шаблон
        template_path = "templates/gallery_template.html"
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            print(f"❌ Шаблон {template_path} не найден, используем встроенный")
            return self._create_simple_gallery_html(image_data, username)
        
        # Генерируем контент галереи
        gallery_content = ""
        for img_data in image_data:
            if "local_filename" in img_data:
                img_src = f"http://158.160.19.119:5000/images/{img_data['local_filename']}"
            else:
                img_src = img_data["image_url"]
                
            gallery_content += f"""
        <div class="image-card" data-post-id="{img_data['post_id']}">
            <img src="{img_src}" alt="{img_data['post_id']}" loading="lazy">
            <div class="image-info">
                <div class="post-id">{img_data['post_id']}</div>
                <div class="likes">❤️ {img_data['likes_count']}</div>
                <div class="timestamp">{img_data['timestamp'][:10] if img_data['timestamp'] != 'N/A' else 'N/A'}</div>
                <div class="object-tags">
                    <!-- Здесь будут теги объектов, когда они появятся -->
                </div>
            </div>
        </div>
        """
        
        # Заменяем плейсхолдеры в шаблоне
        html_content = template.replace("{username}", username)
        html_content = html_content.replace("{total_images}", str(len(image_data)))
        html_content = html_content.replace("{parsing_date}", datetime.now().strftime('%d.%m.%Y'))
        html_content = html_content.replace("{gallery_content}", gallery_content)
        html_content = html_content.replace("{image_data_json}", json.dumps(image_data, ensure_ascii=False))
        
        # Сохраняем HTML файл
        with open(f"gallery_{username}.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"🌐 HTML галерея с фильтрами создана: gallery_{username}.html")
        return html_content

    def _create_simple_gallery_html(self, image_data: List[Dict], username: str):
        """Создание простой HTML галереи (fallback)"""
        print("🌐 Создание простой HTML галереи...")
        
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
    </style>
</head>
<body>
    <div class="header">
        <h1>🖼️ @{username} - Instagram Gallery</h1>
        <p>{len(image_data)} изображений</p>
    </div>
    <div class="gallery">
"""
        
        for img_data in image_data:
            if "local_filename" in img_data:
                img_src = f"http://158.160.19.119:5000/images/{img_data['local_filename']}"
            else:
                img_src = img_data["image_url"]
                
            html_content += f"""
        <div class="image-card">
            <img src="{img_src}" alt="{img_data['post_id']}" loading="lazy">
            <div class="image-info">
                <div>{img_data['post_id']}</div>
                <div>❤️ {img_data['likes_count']}</div>
            </div>
        </div>
        """
        
        html_content += """
    </div>
</body>
</html>
        """
        
        with open(f"gallery_{username}.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"🌐 Простая HTML галерея создана: gallery_{username}.html")
        return html_content

    def create_combined_gallery_html(self, page: int = 1, per_page: int = 200):
        """Создание общей галереи всех аккаунтов с пагинацией"""
        print(f"🌐 Создание общей галереи (страница {page})...")
        
        try:
            # Получаем данные из MongoDB с пагинацией
            skip = (page - 1) * per_page
            images_cursor = self.collection.find().sort("parsed_at", -1).skip(skip).limit(per_page)
            images = list(images_cursor)
            
            # Получаем общее количество изображений
            total_images = self.collection.count_documents({})
            
            # Получаем список всех аккаунтов для фильтрации
            accounts = self.collection.distinct("username")
            
            if not images:
                print("❌ Нет изображений для создания галереи")
                return None
            
            # Читаем шаблон общей галереи
            template_path = "templates/combined_gallery_template.html"
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read()
            except FileNotFoundError:
                print(f"❌ Шаблон {template_path} не найден")
                return None
            
            # Генерируем контент галереи
            gallery_content = ""
            for img_data in images:
                if "local_filename" in img_data:
                    img_src = f"http://158.160.19.119:5000/images/{img_data['local_filename']}"
                else:
                    img_src = img_data["image_url"]
                
                # Определяем статус выбора
                selected_class = "selected" if img_data.get("selected_for_tagging", False) else ""
                checked_attr = "checked" if img_data.get("selected_for_tagging", False) else ""
                
                gallery_content += f"""
        <div class="image-card {selected_class}" data-post-id="{img_data['post_id']}" data-image-id="{img_data['_id']}">
            <div class="image-checkbox">
                <input type="checkbox" class="image-select" {checked_attr} data-image-id="{img_data['_id']}">
            </div>
            <img src="{img_src}" alt="{img_data['post_id']}" loading="lazy">
            <div class="image-info">
                <div class="post-id">{img_data['post_id']}</div>
                <div class="username">@{img_data['username']}</div>
                <div class="likes">❤️ {img_data['likes_count']}</div>
                <div class="timestamp">{img_data['timestamp'][:10] if img_data['timestamp'] != 'N/A' else 'N/A'}</div>
                <div class="object-tags">
                    <!-- Здесь будут теги объектов, когда они появятся -->
                </div>
            </div>
        </div>
        """
            
            # Генерируем пагинацию
            total_pages = (total_images + per_page - 1) // per_page
            pagination_html = self._generate_pagination_html(page, total_pages)
            
            # Генерируем опции аккаунтов для фильтра
            account_options = ""
            for account in accounts:
                account_options += f'<option value="{account}">@{account}</option>\n                    '
            
            # Заменяем плейсхолдеры в шаблоне
            html_content = template.replace("{total_images}", str(total_images))
            html_content = html_content.replace("{current_page}", str(page))
            html_content = html_content.replace("{total_pages}", str(total_pages))
            html_content = html_content.replace("{per_page}", str(per_page))
            html_content = html_content.replace("{gallery_content}", gallery_content)
            html_content = html_content.replace("{pagination_html}", pagination_html)
            html_content = html_content.replace("{accounts_json}", json.dumps(accounts, ensure_ascii=False))
            html_content = html_content.replace("{account_options}", account_options)
            
            # Сохраняем HTML файл
            filename = f"all_accounts_gallery_page_{page}.html" if page > 1 else "all_accounts_gallery.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"🌐 Общая галерея создана: {filename}")
            return html_content
            
        except Exception as e:
            print(f"❌ Ошибка создания общей галереи: {e}")
            return None

    def _generate_pagination_html(self, current_page: int, total_pages: int):
        """Генерация HTML для пагинации"""
        if total_pages <= 1:
            return ""
        
        pagination_html = '<div class="pagination">'
        
        # Предыдущая страница
        if current_page > 1:
            prev_page = current_page - 1
            filename = f"all_accounts_gallery_page_{prev_page}.html" if prev_page > 1 else "all_accounts_gallery.html"
            pagination_html += f'<a href="{filename}" class="page-btn prev">← Предыдущая</a>'
        
        # Номера страниц
        start_page = max(1, current_page - 2)
        end_page = min(total_pages, current_page + 2)
        
        for page_num in range(start_page, end_page + 1):
            if page_num == current_page:
                pagination_html += f'<span class="page-btn current">{page_num}</span>'
            else:
                filename = f"all_accounts_gallery_page_{page_num}.html" if page_num > 1 else "all_accounts_gallery.html"
                pagination_html += f'<a href="{filename}" class="page-btn">{page_num}</a>'
        
        # Следующая страница
        if current_page < total_pages:
            next_page = current_page + 1
            filename = f"all_accounts_gallery_page_{next_page}.html"
            pagination_html += f'<a href="{filename}" class="page-btn next">Следующая →</a>'
        
        pagination_html += '</div>'
        return pagination_html
    
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
