// Конфигурация цветов для графиков
const chartColors = {
    primary: '#667eea',
    secondary: '#764ba2',
    success: '#28a745',
    danger: '#dc3545',
    warning: '#ffc107',
    info: '#17a2b8',
    palette: [
        '#667eea', '#764ba2', '#f093fb', '#4facfe',
        '#43e97b', '#fa709a', '#fee140', '#30cfd0',
        '#a8edea', '#fed6e3', '#c471ed', '#12c2e9'
    ]
};

// Маппинг цветов на CSS цвета
const colorMapping = {
    'Black': '#000000',
    'White': '#FFFFFF',
    'Red': '#FF0000',
    'Blue': '#0000FF',
    'Green': '#00FF00',
    'Yellow': '#FFFF00',
    'Pink': '#FFC0CB',
    'Purple': '#800080',
    'Orange': '#FFA500',
    'Brown': '#8B4513',
    'Gray': '#808080',
    'Grey': '#808080',
    'Beige': '#F5F5DC',
    'Navy': '#000080',
    'Turquoise': '#40E0D0',
    'Gold': '#FFD700',
    'Silver': '#C0C0C0'
};

// Глобальное хранилище для Chart instances
const chartInstances = {};

// ============================================
// МОДАЛЬНОЕ ОКНО ГАЛЕРЕИ ВЕЩЕЙ
// ============================================

function openItemGallery(itemName, topCategory) {
    const modal = document.getElementById('itemGalleryModal');
    const title = document.getElementById('itemGalleryTitle');
    const loader = document.getElementById('itemGalleryLoader');
    const grid = document.getElementById('itemGalleryGrid');

    // Показываем модальное окно и loader
    modal.style.display = 'block';
    title.textContent = `Галерея: ${itemName}`;
    loader.classList.remove('hidden');
    grid.innerHTML = '';

    // Загружаем изображения
    fetch(`/api/analytics/item-gallery?item_name=${encodeURIComponent(itemName)}&top_category=${encodeURIComponent(topCategory)}`)
        .then(response => response.json())
        .then(data => {
            loader.classList.add('hidden');

            if (!data.success) {
                grid.innerHTML = `<div style="text-align: center; color: #dc3545; padding: 40px;">${data.message}</div>`;
                return;
            }

            if (data.images.length === 0) {
                grid.innerHTML = '<div style="text-align: center; color: #666; padding: 40px;">Изображения не найдены</div>';
                return;
            }

            // Отображаем изображения
            data.images.forEach(image => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'item-gallery-item';

                const imageUrl = `/images/${image.local_filename}`;

                itemDiv.innerHTML = `
                    <img src="${imageUrl}" alt="${itemName}" loading="lazy">
                    <div class="item-gallery-item-info">
                        <div class="item-gallery-item-username">@${image.username || 'unknown'}</div>
                        <div class="item-gallery-item-stats">
                            <div class="item-gallery-item-stat">❤️ ${image.likes_count || 0}</div>
                            <div class="item-gallery-item-stat">💬 ${image.comments_count || 0}</div>
                        </div>
                    </div>
                `;

                grid.appendChild(itemDiv);
            });
        })
        .catch(error => {
            console.error('Error loading gallery:', error);
            loader.classList.add('hidden');
            grid.innerHTML = '<div style="text-align: center; color: #dc3545; padding: 40px;">Ошибка загрузки галереи</div>';
        });
}

function closeItemGallery() {
    const modal = document.getElementById('itemGalleryModal');
    modal.style.display = 'none';
}

// Настройка закрытия модального окна
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('itemGalleryModal');
    const closeBtn = document.querySelector('.item-gallery-close');

    if (closeBtn) {
        closeBtn.onclick = closeItemGallery;
    }

    // Закрытие при клике вне модального окна
    window.onclick = function(event) {
        if (event.target === modal) {
            closeItemGallery();
        }
    };
});

// Функция для скрытия всех линий на графике
function hideAllLines(chartId) {
    const chart = chartInstances[chartId];
    if (!chart) {
        console.log('Chart not found:', chartId);
        return;
    }

    chart.data.datasets.forEach((dataset, index) => {
        chart.hide(index);
    });
    chart.update();

    // Обновляем HTML-легенду (убираем "Chart" из ID, если есть)
    const legendContainerId = chartId.replace('Chart', '') + 'Legend';
    console.log('Looking for legend container:', legendContainerId);
    const legendContainer = document.getElementById(legendContainerId);

    if (legendContainer) {
        const checkmarks = legendContainer.querySelectorAll('.legend-checkmark');
        const labels = legendContainer.querySelectorAll('.legend-label');

        console.log('Found checkmarks:', checkmarks.length);
        console.log('Found labels:', labels.length);

        checkmarks.forEach((checkmark, idx) => {
            console.log('Hiding checkmark', idx, checkmark);
            checkmark.style.display = 'none';
        });

        labels.forEach((label, idx) => {
            console.log('Fading label', idx, label);
            label.style.opacity = '0.5';
        });
    } else {
        console.log('Legend container not found:', legendContainerId);
    }
}

// Функция для показа всех линий на графике
function showAllLines(chartId) {
    const chart = chartInstances[chartId];
    if (!chart) return;

    chart.data.datasets.forEach((dataset, index) => {
        chart.show(index);
    });
    chart.update();

    // Обновляем HTML-легенду (убираем "Chart" из ID, если есть)
    const legendContainerId = chartId.replace('Chart', '') + 'Legend';
    const legendContainer = document.getElementById(legendContainerId);
    if (legendContainer) {
        const checkmarks = legendContainer.querySelectorAll('.legend-checkmark');
        const labels = legendContainer.querySelectorAll('.legend-label');

        checkmarks.forEach(checkmark => {
            checkmark.style.display = 'block';
        });

        labels.forEach(label => {
            label.style.opacity = '1';
        });
    }
}

// Функция для создания HTML-легенды с галочками в цветных кружках
function createHtmlLegend(chart, containerId) {
    const legendContainer = document.getElementById(containerId);
    if (!legendContainer) return;

    legendContainer.innerHTML = '';
    legendContainer.style.display = 'flex';
    legendContainer.style.flexWrap = 'wrap';
    legendContainer.style.gap = '12px';
    legendContainer.style.justifyContent = 'center';
    legendContainer.style.marginTop = '15px';

    chart.data.datasets.forEach((dataset, index) => {
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        legendItem.setAttribute('data-index', index);
        legendItem.style.display = 'flex';
        legendItem.style.alignItems = 'center';
        legendItem.style.gap = '6px';
        legendItem.style.cursor = 'pointer';
        legendItem.style.padding = '4px 8px';
        legendItem.style.borderRadius = '4px';
        legendItem.style.transition = 'background-color 0.2s';

        // Цветной кружок с галочкой
        const circle = document.createElement('div');
        circle.className = 'legend-circle';
        circle.style.width = '18px';
        circle.style.height = '18px';
        circle.style.borderRadius = '50%';
        circle.style.backgroundColor = dataset.borderColor;
        circle.style.display = 'flex';
        circle.style.alignItems = 'center';
        circle.style.justifyContent = 'center';
        circle.style.fontSize = '12px';
        circle.style.fontWeight = 'bold';
        circle.style.color = 'white';
        circle.style.textShadow = '0 0 2px rgba(0,0,0,0.3)';

        // Галочка (отображается только если датасет видимый)
        const checkmark = document.createElement('span');
        checkmark.className = 'legend-checkmark';
        checkmark.textContent = '✓';
        checkmark.style.display = chart.isDatasetVisible(index) ? 'block' : 'none';
        circle.appendChild(checkmark);

        // Текст названия
        const label = document.createElement('span');
        label.className = 'legend-label';
        label.textContent = dataset.label;
        label.style.fontSize = '11px';
        label.style.opacity = chart.isDatasetVisible(index) ? '1' : '0.5';

        legendItem.appendChild(circle);
        legendItem.appendChild(label);

        // Обработчик клика для переключения видимости
        legendItem.onclick = () => {
            const meta = chart.getDatasetMeta(index);
            meta.hidden = !meta.hidden;

            // Обновляем визуальное состояние
            if (meta.hidden) {
                checkmark.style.display = 'none';
                label.style.opacity = '0.5';
            } else {
                checkmark.style.display = 'block';
                label.style.opacity = '1';
            }

            chart.update();
        };

        // Hover эффект
        legendItem.onmouseenter = () => {
            legendItem.style.backgroundColor = 'rgba(0,0,0,0.05)';
        };
        legendItem.onmouseleave = () => {
            legendItem.style.backgroundColor = 'transparent';
        };

        legendContainer.appendChild(legendItem);
    });
}

// ============================================
// ЗАГРУЗКА ВСЕЙ АНАЛИТИКИ
// ============================================

async function loadAllAnalytics() {
    console.log('🔄 Loading all analytics...');

    // Показываем спиннер, скрываем контент
    const loader = document.getElementById('analyticsLoader');
    const content = document.getElementById('analyticsContentWrapper');
    loader.classList.remove('hidden');
    content.classList.remove('loaded');

    try {
        console.log('📡 Fetching all API data...');
        const [categories, subcategories, colors, materials, styles, timeline,
               trends, dynamics, colorDynamics, materialDynamics,
               topAccessories, topAccessoriesDynamics,
               topClothing, topClothingDynamics,
               topFootwear, topFootwearDynamics] = await Promise.all([
            fetch('/api/analytics/categories-stats').then(r => r.json()),
            fetch('/api/analytics/subcategories-stats').then(r => r.json()),
            fetch('/api/analytics/colors-stats').then(r => r.json()),
            fetch('/api/analytics/materials-stats').then(r => r.json()),
            fetch('/api/analytics/styles-stats').then(r => r.json()),
            fetch('/api/analytics/trends-timeline').then(r => r.json()),
            fetch('/api/analytics/emerging-trends').then(r => r.json()),
            fetch('/api/analytics/emerging-trends-dynamics').then(r => r.json()),
            fetch('/api/analytics/color-dynamics').then(r => r.json()),
            fetch('/api/analytics/material-dynamics').then(r => r.json()),
            fetch('/api/analytics/top-accessories-stats').then(r => r.json()),
            fetch('/api/analytics/top-accessories-dynamics').then(r => r.json()),
            fetch('/api/analytics/top-clothing-stats').then(r => r.json()),
            fetch('/api/analytics/top-clothing-dynamics').then(r => r.json()),
            fetch('/api/analytics/top-footwear-stats').then(r => r.json()),
            fetch('/api/analytics/top-footwear-dynamics').then(r => r.json())
        ]);

        console.log('✅ All data fetched successfully');

        // Обновляем статистику трендов
        if (categories.success) {
            const totalImages = categories.categories.reduce((sum, c) => sum + c.count, 0);
            document.getElementById('totalImages').textContent = totalImages.toLocaleString();
            document.getElementById('totalCategories').textContent = categories.categories.length;
        }

        if (colors.success) {
            document.getElementById('totalColors').textContent = colors.colors.length;
        }

        if (materials.success) {
            document.getElementById('totalMaterials').textContent = materials.materials.length;
        }

        // Рисуем графики трендов
        console.log('🎨 Drawing trends charts...');
        if (categories.success) drawCategoriesChart(categories.categories);
        if (subcategories.success) drawSubcategoriesChart(subcategories.subcategories);
        if (colors.success) drawColorsChart(colors.colors);
        if (materials.success) drawMaterialsChart(materials.materials);
        if (styles.success) drawStylesChart(styles.styles);
        if (timeline.success) drawTimelineChart(timeline.timeline);

        // Рисуем графики прогнозов
        console.log('🔮 Drawing predictive charts...');
        if (trends.success) drawEmergingTrendsTop10Chart(trends.emerging.slice(0, 10));
        if (dynamics.success) drawEmergingTrendsDynamicsChart(dynamics);
        if (colorDynamics.success) drawColorDynamicsChart(colorDynamics);
        if (materialDynamics.success) drawMaterialDynamicsChart(materialDynamics);
        if (topAccessories.success) drawTopAccessoriesChart(topAccessories.items);
        if (topAccessoriesDynamics.success) drawTopAccessoriesDynamicsChart(topAccessoriesDynamics);
        if (topClothing.success) drawTopClothingChart(topClothing.items);
        if (topClothingDynamics.success) drawTopClothingDynamicsChart(topClothingDynamics);
        if (topFootwear.success) drawTopFootwearChart(topFootwear.items);
        if (topFootwearDynamics.success) drawTopFootwearDynamicsChart(topFootwearDynamics);

        console.log('✅ All analytics loaded successfully!');

        // Скрываем спиннер, показываем контент
        loader.classList.add('hidden');
        content.classList.add('loaded');

    } catch (error) {
        console.error('❌ Ошибка загрузки аналитики:', error);
        console.error('Stack trace:', error.stack);

        // Скрываем спиннер при ошибке тоже
        loader.classList.add('hidden');
        content.classList.add('loaded');

        content.insertAdjacentHTML('afterbegin',
            '<div class="error-message">Ошибка загрузки данных: ' + error.message + '</div>');
    }
}

function drawCategoriesChart(data) {
    const ctx = document.getElementById('categoriesChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.name),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: chartColors.palette,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 15, font: { size: 12 } }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return context.label + ': ' + context.parsed.toLocaleString() + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

function drawSubcategoriesChart(data) {
    const ctx = document.getElementById('subcategoriesChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.name),
            datasets: [{
                label: 'Количество',
                data: data.map(d => d.count),
                backgroundColor: chartColors.palette[0],
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return data[context[0].dataIndex].name + ' (' + data[context[0].dataIndex].category + ')';
                        }
                    }
                }
            },
            scales: {
                x: { beginAtZero: true, grid: { display: true } },
                y: { grid: { display: false } }
            }
        }
    });
}

function drawColorsChart(data) {
    const ctx = document.getElementById('colorsChart').getContext('2d');
    const backgroundColors = data.map(d => colorMapping[d.name] || chartColors.palette[0]);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.name),
            datasets: [{
                label: 'Количество',
                data: data.map(d => d.count),
                backgroundColor: backgroundColors,
                borderColor: '#fff',
                borderWidth: 1,
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { beginAtZero: true, grid: { display: true } },
                y: { grid: { display: false } }
            }
        }
    });
}

function drawMaterialsChart(data) {
    const ctx = document.getElementById('materialsChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.name),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: chartColors.palette,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 15, font: { size: 12 } }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return context.label + ': ' + context.parsed.toLocaleString() + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

function drawStylesChart(data) {
    const ctx = document.getElementById('stylesChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.name),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: chartColors.palette,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 15, font: { size: 12 } }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return context.label + ': ' + context.parsed.toLocaleString() + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

function drawTimelineChart(timeline) {
    const ctx = document.getElementById('timelineChart').getContext('2d');
    const datasets = Object.keys(timeline.series).map((category, index) => ({
        label: category,
        data: timeline.series[category],
        borderColor: chartColors.palette[index % chartColors.palette.length],
        backgroundColor: chartColors.palette[index % chartColors.palette.length] + '20',
        borderWidth: 2,
        tension: 0.4,
        fill: true
    }));

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeline.months,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: false  // Отключаем стандартную легенду
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: { beginAtZero: true, grid: { display: true } }
            }
        }
    });

    chartInstances['timelineChart'] = chart;
    createHtmlLegend(chart, 'timelineLegend');
}

// ============================================
// ФУНКЦИИ ОТРИСОВКИ
// ============================================

function drawEmergingTrendsTop10Chart(trends) {
    const ctx = document.getElementById('emergingTrendsTop10Chart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: trends.map(t => t.name),
            datasets: [{
                label: 'Рост (%)',
                data: trends.map(t => t.growth_rate),
                backgroundColor: chartColors.success,
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const index = context[0].dataIndex;
                            return trends[index].name + ' (' + trends[index].category + ')';
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Рост (%)'
                    }
                },
                y: { grid: { display: false } }
            }
        }
    });
}

function drawEmergingTrendsDynamicsChart(dynamics) {
    const ctx = document.getElementById('emergingTrendsDynamicsChart').getContext('2d');

    // Создаём datasets для каждого тренда
    const datasets = dynamics.series.map((trend, index) => ({
        label: `${trend.name} (+${trend.growth_rate}%)`,
        data: trend.data,
        borderColor: chartColors.palette[index % chartColors.palette.length],
        backgroundColor: chartColors.palette[index % chartColors.palette.length] + '20',
        borderWidth: 3,
        tension: 0.4,
        fill: false,
        pointRadius: 4,
        pointHoverRadius: 6
    }));

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dynamics.months,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: false  // Отключаем стандартную легенду
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return 'Месяц: ' + context[0].label;
                        },
                        afterLabel: function(context) {
                            const trend = dynamics.series[context.datasetIndex];
                            return trend.category;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    title: {
                        display: true,
                        text: 'Месяц'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: { display: true },
                    title: {
                        display: true,
                        text: 'Количество упоминаний'
                    }
                }
            }
        }
    });

    chartInstances['emergingTrendsDynamicsChart'] = chart;
    createHtmlLegend(chart, 'emergingTrendsDynamicsLegend');
}

function drawColorDynamicsChart(dynamics) {
    const ctx = document.getElementById('colorDynamicsChart').getContext('2d');

    // Создаём datasets для каждого цвета с реальными цветами
    const datasets = dynamics.series.map((colorData, index) => {
        const colorName = colorData.name;
        const realColor = colorMapping[colorName] || chartColors.palette[index % chartColors.palette.length];

        return {
            label: `${colorName} (+${colorData.growth_rate}%)`,
            data: colorData.data,
            borderColor: realColor,
            backgroundColor: realColor + '20',
            borderWidth: 3,
            tension: 0.4,
            fill: false,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: realColor,
            pointBorderColor: '#fff',
            pointBorderWidth: 2
        };
    });

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dynamics.months,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: false  // Отключаем стандартную легенду
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return 'Месяц: ' + context[0].label;
                        },
                        label: function(context) {
                            const colorData = dynamics.series[context.datasetIndex];
                            return colorData.name + ': ' + context.parsed.y + ' упоминаний';
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    title: {
                        display: true,
                        text: 'Месяц'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: { display: true },
                    title: {
                        display: true,
                        text: 'Количество упоминаний'
                    }
                }
            }
        }
    });

    chartInstances['colorDynamicsChart'] = chart;
    createHtmlLegend(chart, 'colorDynamicsLegend');
}

function drawMaterialDynamicsChart(dynamics) {
    const ctx = document.getElementById('materialDynamicsChart').getContext('2d');

    // Создаём datasets для каждого материала
    const datasets = dynamics.series.map((materialData, index) => {
        const color = chartColors.palette[index % chartColors.palette.length];

        return {
            label: `${materialData.name} (+${materialData.growth_rate}%)`,
            data: materialData.data,
            borderColor: color,
            backgroundColor: color + '20',
            borderWidth: 3,
            tension: 0.4,
            fill: false,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: color,
            pointBorderColor: '#fff',
            pointBorderWidth: 2
        };
    });

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dynamics.months,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: false  // Отключаем стандартную легенду
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return 'Месяц: ' + context[0].label;
                        },
                        label: function(context) {
                            const materialData = dynamics.series[context.datasetIndex];
                            return materialData.name + ': ' + context.parsed.y + ' упоминаний';
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    title: {
                        display: true,
                        text: 'Месяц'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: { display: true },
                    title: {
                        display: true,
                        text: 'Количество упоминаний'
                    }
                }
            }
        }
    });

    chartInstances['materialDynamicsChart'] = chart;
    createHtmlLegend(chart, 'materialDynamicsLegend');
}

function drawTopAccessoriesChart(items) {
    const ctx = document.getElementById('topAccessoriesChart').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: items.map(item => item.name),
            datasets: [{
                label: 'Количество упоминаний',
                data: items.map(item => item.count),
                backgroundColor: chartColors.palette[3],
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const itemName = items[index].name;
                    openItemGallery(itemName, 'Accessories');
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.x + ' упоминаний';
                        },
                        footer: function() {
                            return 'Кликните для просмотра галереи';
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { display: true },
                    title: {
                        display: true,
                        text: 'Количество упоминаний'
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: {
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

function drawTopAccessoriesDynamicsChart(dynamics) {
    const ctx = document.getElementById('topAccessoriesDynamicsChart').getContext('2d');

    const datasets = dynamics.series.map((itemData, index) => {
        const color = chartColors.palette[index % chartColors.palette.length];

        return {
            label: itemData.name,
            data: itemData.data,
            borderColor: color,
            backgroundColor: color + '20',
            borderWidth: 2,
            tension: 0.4,
            fill: false,
            pointRadius: 3,
            pointHoverRadius: 5
        };
    });

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dynamics.months,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: false  // Отключаем стандартную легенду
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return 'Месяц: ' + context[0].label;
                        },
                        label: function(context) {
                            const itemData = dynamics.series[context.datasetIndex];
                            return itemData.name + ': ' + context.parsed.y + ' упоминаний';
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    title: {
                        display: true,
                        text: 'Месяц'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: { display: true },
                    title: {
                        display: true,
                        text: 'Количество упоминаний'
                    }
                }
            }
        }
    });

    chartInstances['topAccessoriesDynamicsChart'] = chart;
    createHtmlLegend(chart, 'topAccessoriesDynamicsLegend');
}

function drawTopClothingChart(items) {
    const ctx = document.getElementById('topClothingChart').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: items.map(item => item.name),
            datasets: [{
                label: 'Количество упоминаний',
                data: items.map(item => item.count),
                backgroundColor: chartColors.palette[4],
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const itemName = items[index].name;
                    openItemGallery(itemName, 'Clothing');
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.x + ' упоминаний';
                        },
                        footer: function() {
                            return 'Кликните для просмотра галереи';
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { display: true },
                    title: {
                        display: true,
                        text: 'Количество упоминаний'
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: {
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

function drawTopClothingDynamicsChart(dynamics) {
    const ctx = document.getElementById('topClothingDynamicsChart').getContext('2d');

    const datasets = dynamics.series.map((itemData, index) => {
        const color = chartColors.palette[index % chartColors.palette.length];

        return {
            label: itemData.name,
            data: itemData.data,
            borderColor: color,
            backgroundColor: color + '20',
            borderWidth: 2,
            tension: 0.4,
            fill: false,
            pointRadius: 3,
            pointHoverRadius: 5
        };
    });

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dynamics.months,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: false  // Отключаем стандартную легенду
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return 'Месяц: ' + context[0].label;
                        },
                        label: function(context) {
                            const itemData = dynamics.series[context.datasetIndex];
                            return itemData.name + ': ' + context.parsed.y + ' упоминаний';
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    title: {
                        display: true,
                        text: 'Месяц'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: { display: true },
                    title: {
                        display: true,
                        text: 'Количество упоминаний'
                    }
                }
            }
        }
    });

    chartInstances['topClothingDynamicsChart'] = chart;
    createHtmlLegend(chart, 'topClothingDynamicsLegend');
}

function drawTopFootwearChart(items) {
    const ctx = document.getElementById('topFootwearChart').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: items.map(item => item.name),
            datasets: [{
                label: 'Количество упоминаний',
                data: items.map(item => item.count),
                backgroundColor: chartColors.palette[5],
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const itemName = items[index].name;
                    openItemGallery(itemName, 'Footwear');
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.x + ' упоминаний';
                        },
                        footer: function() {
                            return 'Кликните для просмотра галереи';
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { display: true },
                    title: {
                        display: true,
                        text: 'Количество упоминаний'
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: {
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

function drawTopFootwearDynamicsChart(dynamics) {
    const ctx = document.getElementById('topFootwearDynamicsChart').getContext('2d');

    const datasets = dynamics.series.map((itemData, index) => {
        const color = chartColors.palette[index % chartColors.palette.length];

        return {
            label: itemData.name,
            data: itemData.data,
            borderColor: color,
            backgroundColor: color + '20',
            borderWidth: 2,
            tension: 0.4,
            fill: false,
            pointRadius: 3,
            pointHoverRadius: 5
        };
    });

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dynamics.months,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: false  // Отключаем стандартную легенду
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return 'Месяц: ' + context[0].label;
                        },
                        label: function(context) {
                            const itemData = dynamics.series[context.datasetIndex];
                            return itemData.name + ': ' + context.parsed.y + ' упоминаний';
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    title: {
                        display: true,
                        text: 'Месяц'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: { display: true },
                    title: {
                        display: true,
                        text: 'Количество упоминаний'
                    }
                }
            }
        }
    });

    chartInstances['topFootwearDynamicsChart'] = chart;
    createHtmlLegend(chart, 'topFootwearDynamicsLegend');
}

// Загрузка данных при загрузке страницы
console.log('🚀 Analytics.js loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM Content Loaded - initializing analytics');

    // Загружаем всю аналитику
    loadAllAnalytics();

    console.log('✅ Initial load complete');
});
