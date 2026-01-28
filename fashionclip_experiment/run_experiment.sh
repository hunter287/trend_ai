#!/bin/bash
# Полный запуск эксперимента FashionCLIP vs Ximilar

set -e  # Остановка при ошибке

echo "🎨 Запуск эксперимента FashionCLIP vs Ximilar"
echo "=============================================="
echo ""

# Проверка виртуального окружения
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Виртуальное окружение не активировано"
    echo "   Рекомендуется: source venv/bin/activate"
    echo ""
fi

# Шаг 1: Подготовка датасета
echo "📊 Шаг 1/3: Подготовка датасета из MongoDB..."
python3 prepare_dataset.py
if [ $? -ne 0 ]; then
    echo "❌ Ошибка при подготовке датасета"
    exit 1
fi
echo ""

# Шаг 2: Запуск FashionCLIP
echo "🤖 Шаг 2/3: Обработка через FashionCLIP..."
echo "⚠️  Это может занять 10-30 минут..."
python3 run_fashionclip.py
if [ $? -ne 0 ]; then
    echo "❌ Ошибка при обработке FashionCLIP"
    exit 1
fi
echo ""

# Шаг 3: Генерация HTML отчёта
echo "📄 Шаг 3/3: Генерация HTML отчёта..."
python3 generate_html_report.py
if [ $? -ne 0 ]; then
    echo "❌ Ошибка при генерации отчёта"
    exit 1
fi
echo ""

echo "✅ Эксперимент завершён!"
echo ""
echo "🌐 Откройте HTML отчёт:"
echo "   file://$(pwd)/comparison_report.html"
echo ""
echo "Или используйте команду:"
echo "   open comparison_report.html    # macOS"
echo "   xdg-open comparison_report.html  # Linux"
echo ""
