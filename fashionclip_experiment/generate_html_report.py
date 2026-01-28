#!/usr/bin/env python3
"""
Генерация HTML отчёта для сравнения Ximilar vs FashionCLIP
"""

import json
import os
import sys
from datetime import datetime

# Параметры
INPUT_FILE = 'data/fashionclip_results.json'
OUTPUT_FILE = 'comparison_report.html'

def load_results():
    """Загрузить результаты"""
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Файл {INPUT_FILE} не найден!")
        print(f"   Сначала запустите: python run_fashionclip.py")
        sys.exit(1)

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data

def generate_html_report(data):
    """Генерация HTML отчёта"""
    samples = data['samples']
    metadata = data['metadata']

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FashionCLIP vs Ximilar - Сравнение</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}

        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }}

        .header h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}

        .header .metadata {{
            color: #666;
            font-size: 0.9em;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}

        .stat-card .number {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .stat-card .label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}

        .comparison-grid {{
            display: grid;
            gap: 30px;
        }}

        .comparison-card {{
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .card-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            font-weight: bold;
            font-size: 1.1em;
        }}

        .card-content {{
            padding: 20px;
        }}

        .image-container {{
            text-align: center;
            margin-bottom: 20px;
        }}

        .image-container img {{
            max-width: 100%;
            max-height: 500px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .image-info {{
            margin-top: 10px;
            font-size: 0.85em;
            color: #666;
        }}

        .results-comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}

        .result-column {{
            padding: 20px;
            border-radius: 10px;
        }}

        .result-column.ximilar {{
            background: #f0f7ff;
            border: 2px solid #4a90e2;
        }}

        .result-column.fashionclip {{
            background: #fff5f0;
            border: 2px solid #e27a4a;
        }}

        .result-column h3 {{
            margin-bottom: 15px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .logo {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
        }}

        .logo.ximilar {{
            background: #4a90e2;
        }}

        .logo.fashionclip {{
            background: #e27a4a;
        }}

        .attribute-section {{
            margin-bottom: 20px;
        }}

        .attribute-section h4 {{
            color: #555;
            margin-bottom: 10px;
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .attribute-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}

        .attribute-tag {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}

        .confidence {{
            background: rgba(0,0,0,0.1);
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 0.85em;
            font-weight: bold;
        }}

        .evaluation-form {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 10px;
            border: 2px dashed #ccc;
        }}

        .evaluation-form h3 {{
            margin-bottom: 15px;
            color: #333;
        }}

        .radio-group {{
            margin-bottom: 15px;
        }}

        .radio-option {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            margin-bottom: 5px;
            background: white;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }}

        .radio-option:hover {{
            background: #f0f0f0;
            transform: translateX(5px);
        }}

        .radio-option input[type="radio"] {{
            width: 20px;
            height: 20px;
            cursor: pointer;
        }}

        textarea {{
            width: 100%;
            min-height: 80px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-family: inherit;
            resize: vertical;
        }}

        .save-button {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            margin-top: 15px;
            transition: transform 0.3s;
        }}

        .save-button:hover {{
            transform: scale(1.05);
        }}

        .no-data {{
            text-align: center;
            padding: 40px;
            color: #999;
            font-style: italic;
        }}

        .error {{
            background: #fee;
            color: #c00;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #fcc;
        }}

        @media (max-width: 768px) {{
            .results-comparison {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎨 FashionCLIP vs Ximilar</h1>
        <div class="metadata">
            <p>Эксперимент по сравнению моделей распознавания одежды</p>
            <p>Создано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        <div class="stats">
            <div class="stat-card">
                <div class="number">{len(samples)}</div>
                <div class="label">Изображений</div>
            </div>
            <div class="stat-card">
                <div class="number">{metadata.get('fashionclip_processed_count', 0)}</div>
                <div class="label">Обработано</div>
            </div>
            <div class="stat-card">
                <div class="number">{metadata.get('fashionclip_failed_count', 0)}</div>
                <div class="label">Ошибок</div>
            </div>
        </div>
    </div>

    <div class="comparison-grid">
"""

    # Генерируем карточки для каждого изображения
    for idx, sample in enumerate(samples):
        image_url = sample['image_url']
        ximilar = sample.get('ximilar_results', {})
        fashionclip = sample.get('fashionclip_results', {})

        # Пропускаем образцы с ошибками
        if 'error' in fashionclip:
            continue

        html += f"""
        <div class="comparison-card" id="sample-{idx}">
            <div class="card-header">
                Образец #{idx + 1} - {sample.get('username', 'Unknown')} / {sample.get('post_id', 'N/A')}
            </div>
            <div class="card-content">
                <div class="image-container">
                    <img src="{image_url}" alt="Fashion Image {idx + 1}" loading="lazy">
                    <div class="image-info">
                        <a href="{image_url}" target="_blank">Открыть оригинал</a>
                    </div>
                </div>

                <div class="results-comparison">
                    <div class="result-column ximilar">
                        <h3>
                            <span class="logo ximilar"></span>
                            Ximilar
                        </h3>
"""

        # Ximilar результаты
        for attr_type, attr_label in [
            ('categories', 'Категории'),
            ('colors', 'Цвета'),
            ('materials', 'Материалы'),
            ('styles', 'Стили')
        ]:
            attrs = ximilar.get(attr_type, [])
            if attrs:
                html += f"""
                        <div class="attribute-section">
                            <h4>{attr_label}</h4>
                            <div class="attribute-list">
"""
                for attr in attrs[:5]:
                    conf = attr.get('confidence')
                    if conf is None or (isinstance(conf, float) and (conf != conf)):  # Check for NaN
                        confidence_pct = 'N/A'
                    else:
                        confidence_pct = f"{int(conf * 100)}%"
                    html += f"""
                                <div class="attribute-tag">
                                    {attr['name']}
                                    <span class="confidence">{confidence_pct}</span>
                                </div>
"""
                html += """
                            </div>
                        </div>
"""

        html += """
                    </div>

                    <div class="result-column fashionclip">
                        <h3>
                            <span class="logo fashionclip"></span>
                            FashionCLIP
                        </h3>
"""

        # FashionCLIP результаты
        for attr_type, attr_label in [
            ('categories', 'Категории'),
            ('colors', 'Цвета'),
            ('materials', 'Материалы'),
            ('styles', 'Стили')
        ]:
            attrs = fashionclip.get(attr_type, [])
            if attrs:
                html += f"""
                        <div class="attribute-section">
                            <h4>{attr_label}</h4>
                            <div class="attribute-list">
"""
                for attr in attrs[:5]:
                    conf = attr.get('confidence')
                    if conf is None or (isinstance(conf, float) and (conf != conf)):  # Check for NaN
                        confidence_pct = 'N/A'
                    else:
                        confidence_pct = f"{int(conf * 100)}%"
                    html += f"""
                                <div class="attribute-tag">
                                    {attr['name']}
                                    <span class="confidence">{confidence_pct}</span>
                                </div>
"""
                html += """
                            </div>
                        </div>
"""

        html += f"""
                    </div>
                </div>

                <div class="evaluation-form">
                    <h3>✍️ Ваша оценка</h3>
                    <div class="radio-group">
                        <label class="radio-option">
                            <input type="radio" name="evaluation-{idx}" value="ximilar">
                            <span>Ximilar лучше</span>
                        </label>
                        <label class="radio-option">
                            <input type="radio" name="evaluation-{idx}" value="fashionclip">
                            <span>FashionCLIP лучше</span>
                        </label>
                        <label class="radio-option">
                            <input type="radio" name="evaluation-{idx}" value="equal">
                            <span>Примерно одинаково</span>
                        </label>
                    </div>
                    <textarea id="comment-{idx}" placeholder="Комментарий (опционально)..."></textarea>
                </div>
            </div>
        </div>
"""

    html += """
    </div>

    <div class="header" style="margin-top: 30px;">
        <button class="save-button" onclick="saveEvaluations()">💾 Сохранить оценки</button>
        <p style="margin-top: 15px; color: #666; font-size: 0.9em;">
            Оценки будут сохранены в файл evaluations.json
        </p>
    </div>

    <script>
        function saveEvaluations() {
            const evaluations = [];
            const samples = """ + json.dumps([{'id': s['id'], 'image_url': s['image_url']} for s in samples]) + """;

            samples.forEach((sample, idx) => {
                const selectedRadio = document.querySelector(`input[name="evaluation-${idx}"]:checked`);
                const comment = document.getElementById(`comment-${idx}`).value;

                if (selectedRadio || comment) {
                    evaluations.push({
                        sample_id: sample.id,
                        image_url: sample.image_url,
                        evaluation: selectedRadio ? selectedRadio.value : null,
                        comment: comment || null,
                        evaluated_at: new Date().toISOString()
                    });
                }
            });

            // Сохраняем в localStorage
            localStorage.setItem('fashionclip_evaluations', JSON.stringify(evaluations));

            // Создаём blob и скачиваем
            const dataStr = JSON.stringify({
                metadata: {
                    created_at: new Date().toISOString(),
                    total_evaluations: evaluations.length
                },
                evaluations: evaluations
            }, null, 2);

            const blob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'evaluations.json';
            a.click();

            alert(`✅ Сохранено ${evaluations.length} оценок!`);
        }

        // Автосохранение в localStorage при изменении
        document.addEventListener('change', function(e) {
            if (e.target.type === 'radio' || e.target.tagName === 'TEXTAREA') {
                console.log('Автосохранение...');
                // Можно добавить автосохранение здесь
            }
        });

        // Восстановление из localStorage при загрузке
        window.addEventListener('load', function() {
            const saved = localStorage.getItem('fashionclip_evaluations');
            if (saved) {
                console.log('Найдены сохранённые оценки');
                // Можно добавить восстановление состояния
            }
        });
    </script>
</body>
</html>
"""

    return html

def main():
    """Основная функция"""
    print(f"\n📊 Генерация HTML отчёта для сравнения\n")

    # Загружаем результаты
    print(f"📂 Загрузка результатов из {INPUT_FILE}...")
    data = load_results()

    print(f"✅ Загружено {len(data['samples'])} образцов")

    # Генерируем HTML
    print(f"\n🎨 Генерация HTML...")
    html = generate_html_report(data)

    # Сохраняем
    print(f"💾 Сохранение в {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    file_size = os.path.getsize(OUTPUT_FILE)
    print(f"✅ HTML отчёт создан!")
    print(f"   Размер: {file_size:,} байт")
    print(f"\n🌐 Откройте файл в браузере:")
    print(f"   file://{os.path.abspath(OUTPUT_FILE)}")

if __name__ == '__main__':
    main()
