"""
Продакшен версия приложения для развертывания на сервере
"""

import os
import json
import requests
import threading
import time
from datetime import datetime
from urllib.parse import urlparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
from pathlib import Path

class ProductionImageServer:
    def __init__(self, port=8080, images_dir="images"):
        self.port = port
        self.images_dir = Path(images_dir)
        self.images_dir.mkdir(exist_ok=True)
        self.server = None
        
    def download_all_images(self):
        """Скачивает все изображения из JSON файла"""
        
        print("⬇️ СКАЧИВАНИЕ ВСЕХ ИЗОБРАЖЕНИЙ")
        print("="*50)
        
        # Ищем JSON файл с URL изображений
        json_files = list(Path(".").glob("image_urls_*.json"))
        
        if not json_files:
            print("❌ JSON файлы с URL изображений не найдены")
            return None
        
        # Берем самый новый файл
        latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
        print(f"📄 Используем файл: {latest_file}")
        
        try:
            # Загружаем данные
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"📊 Загружено {len(data)} URL изображений")
            
            # Создаем папку для изображений
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            images_folder = self.images_dir / f"linda_sza_images_{timestamp}"
            images_folder.mkdir(exist_ok=True)
            print(f"📁 Создана папка: {images_folder}")
            
            # Создаем индексный файл
            index_data = {
                'total_images': len(data),
                'download_date': datetime.now().isoformat(),
                'images_folder': str(images_folder),
                'images': []
            }
            
            # Скачиваем изображения
            downloaded_count = 0
            failed_count = 0
            
            for i, img_data in enumerate(data):
                try:
                    url = img_data['image_url']
                    post_code = img_data['shortCode']
                    img_type = img_data['image_type']
                    likes = img_data['likesCount']
                    timestamp = img_data['timestamp']
                    
                    # Определяем имя файла
                    parsed_url = urlparse(url)
                    file_extension = '.jpg'  # По умолчанию jpg
                    
                    # Создаем уникальное имя файла
                    filename = f"{post_code}_{img_type}_{i+1:04d}{file_extension}"
                    filepath = images_folder / filename
                    
                    # Скачиваем изображение
                    response = requests.get(url, timeout=30)
                    
                    if response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        # Добавляем в индекс
                        index_data['images'].append({
                            'filename': filename,
                            'original_url': url,
                            'post_code': post_code,
                            'image_type': img_type,
                            'likes_count': likes,
                            'timestamp': timestamp,
                            'file_size': filepath.stat().st_size,
                            'local_url': f"/images/{images_folder.name}/{filename}"
                        })
                        
                        downloaded_count += 1
                        
                        if downloaded_count % 50 == 0:
                            print(f"📥 Скачано: {downloaded_count}/{len(data)}")
                            
                    else:
                        print(f"❌ Ошибка скачивания {url}: {response.status_code}")
                        failed_count += 1
                        
                except Exception as e:
                    print(f"❌ Ошибка скачивания изображения {i+1}: {e}")
                    failed_count += 1
            
            # Сохраняем индексный файл
            index_file = images_folder / "index.json"
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            # Создаем HTML галерею
            self.create_html_gallery(images_folder, index_data)
            
            print(f"\n🎉 СКАЧИВАНИЕ ЗАВЕРШЕНО!")
            print(f"📥 Успешно скачано: {downloaded_count}")
            print(f"❌ Ошибок: {failed_count}")
            print(f"📁 Папка: {images_folder}")
            print(f"📄 Индекс: {index_file}")
            
            return {
                'folder': str(images_folder),
                'downloaded': downloaded_count,
                'failed': failed_count,
                'index_file': str(index_file)
            }
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return None

    def create_html_gallery(self, images_folder, index_data):
        """Создает HTML галерею для просмотра изображений"""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Linda Sza - Галерея изображений</title>
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
            margin-top: 20px;
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
        .post-code {{
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
        .search {{
            margin: 20px 0;
            text-align: center;
        }}
        .search input {{
            padding: 10px;
            width: 300px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🖼️ Linda Sza - Галерея изображений</h1>
        <div class="stats">
            <div class="stat">
                <h3>{index_data['total_images']}</h3>
                <p>Всего изображений</p>
            </div>
            <div class="stat">
                <h3>{datetime.now().strftime('%d.%m.%Y')}</h3>
                <p>Дата скачивания</p>
            </div>
        </div>
    </div>
    
    <div class="search">
        <input type="text" id="searchInput" placeholder="Поиск по коду поста или типу изображения..." onkeyup="filterImages()">
    </div>
    
    <div class="gallery" id="gallery">
"""

        # Добавляем изображения
        for img in index_data['images']:
            html_content += f"""
        <div class="image-card" data-post="{img['post_code']}" data-type="{img['image_type']}">
            <img src="{img['local_url']}" alt="{img['post_code']}" loading="lazy">
            <div class="image-info">
                <div class="post-code">{img['post_code']}</div>
                <div class="likes">❤️ {img['likes_count']}</div>
                <div class="timestamp">{img['timestamp'][:10]}</div>
                <div style="font-size: 12px; color: #999;">{img['image_type']}</div>
            </div>
        </div>
        """

        html_content += """
    </div>
    
    <script>
        function filterImages() {
            const input = document.getElementById('searchInput');
            const filter = input.value.toLowerCase();
            const cards = document.querySelectorAll('.image-card');
            
            cards.forEach(card => {
                const post = card.getAttribute('data-post').toLowerCase();
                const type = card.getAttribute('data-type').toLowerCase();
                
                if (post.includes(filter) || type.includes(filter)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
        """
        
        # Сохраняем HTML файл
        html_file = images_folder / "gallery.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"🌐 HTML галерея создана: {html_file}")

    def start_server(self):
        """Запускает HTTP сервер"""
        
        print(f"\n🌐 ЗАПУСК HTTP СЕРВЕРА")
        print("="*40)
        
        class CustomHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(Path.cwd()), **kwargs)
            
            def end_headers(self):
                # Добавляем CORS заголовки
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                super().end_headers()
        
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), CustomHandler)
            print(f"🚀 Сервер запущен на http://0.0.0.0:{self.port}")
            print(f"📁 Обслуживает папку: {Path.cwd()}")
            print(f"🌐 Галерея доступна по адресу: http://0.0.0.0:{self.port}/gallery.html")
            print(f"📄 Индекс данных: http://0.0.0.0:{self.port}/index.json")
            print(f"\n💡 Для остановки сервера нажмите Ctrl+C")
            
            # Запускаем сервер
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            print(f"\n🛑 Сервер остановлен")
            if self.server:
                self.server.shutdown()
        except Exception as e:
            print(f"❌ Ошибка запуска сервера: {e}")

def main():
    """Основная функция"""
    
    print("🖼️ ПРОДАКШЕН СЕРВЕР LINDA SZA GALLERY")
    print("="*50)
    
    # Создаем экземпляр сервера
    server = ProductionImageServer()
    
    # Скачиваем изображения
    result = server.download_all_images()
    
    if result:
        print(f"\n🎯 ПРИЛОЖЕНИЕ ГОТОВО К РАБОТЕ!")
        print(f"📁 Изображения сохранены в папку: {result['folder']}")
        print(f"🌐 Запускаем HTTP сервер...")
        
        # Запускаем сервер
        server.start_server()
    else:
        print("\n❌ Не удалось скачать изображения")

if __name__ == "__main__":
    main()
