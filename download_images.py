"""
Простой скрипт для скачивания изображений на сервере
"""

import json
import requests
import os
from pathlib import Path

def download_images():
    """Скачивает изображения из JSON файла"""
    
    print("⬇️ СКАЧИВАНИЕ ИЗОБРАЖЕНИЙ")
    print("="*40)
    
    # Найти JSON файл
    json_files = list(Path(".").glob("image_urls_*.json"))
    if not json_files:
        print("❌ JSON файлы не найдены")
        return
    
    latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
    print(f"📄 Используем файл: {latest_file}")
    
    # Загрузить данные
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 Загружено {len(data)} URL изображений")
    
    # Создать папку для изображений
    images_dir = Path("images")
    images_dir.mkdir(exist_ok=True)
    
    # Скачать изображения (ограничиваем для теста)
    max_images = min(50, len(data))  # Скачиваем максимум 50 изображений
    print(f"📥 Скачиваем {max_images} изображений...")
    
    downloaded = 0
    failed = 0
    
    for i, img_data in enumerate(data[:max_images]):
        try:
            url = img_data['image_url']
            post_code = img_data.get('shortCode', 'unknown')
            img_type = img_data.get('image_type', 'main')
            
            # Создаем понятное имя файла
            filename = f"{post_code}_{img_type}_{i+1:04d}.jpg"
            filepath = images_dir / filename
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                downloaded += 1
                if downloaded % 10 == 0:
                    print(f"📥 Скачано: {downloaded}/{max_images}")
            else:
                print(f"❌ Ошибка HTTP {response.status_code}: {url}")
                failed += 1
        except Exception as e:
            print(f"❌ Ошибка скачивания {i+1}: {e}")
            failed += 1
    
    print(f"\n🎉 СКАЧИВАНИЕ ЗАВЕРШЕНО!")
    print(f"✅ Успешно скачано: {downloaded}")
    print(f"❌ Ошибок: {failed}")
    print(f"📁 Папка: {images_dir.absolute()}")
    
    # Создаем простой HTML файл для просмотра
    create_simple_gallery(images_dir, downloaded)
    
    return downloaded

def create_simple_gallery(images_dir, count):
    """Создает простую HTML галерею"""
    
    html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Linda Sza Gallery - {count} изображений</title>
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
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🖼️ Linda Sza Gallery</h1>
        <p>Всего изображений: {count}</p>
    </div>
    
    <div class="gallery">
"""

    # Добавляем изображения
    for img_file in sorted(images_dir.glob("*.jpg")):
        html_content += f"""
        <div class="image-card">
            <img src="/images/{img_file.name}" alt="{img_file.name}" loading="lazy">
            <div class="image-info">
                <p>{img_file.name}</p>
            </div>
        </div>
        """

    html_content += """
    </div>
</body>
</html>
    """
    
    # Сохраняем HTML файл
    with open("gallery.html", 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"🌐 HTML галерея создана: gallery.html")

if __name__ == "__main__":
    download_images()
