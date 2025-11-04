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
               trends, dynamics, colorDynamics, materialDynamics] = await Promise.all([
            fetch('/api/analytics/categories-stats').then(r => r.json()),
            fetch('/api/analytics/subcategories-stats').then(r => r.json()),
            fetch('/api/analytics/colors-stats').then(r => r.json()),
            fetch('/api/analytics/materials-stats').then(r => r.json()),
            fetch('/api/analytics/styles-stats').then(r => r.json()),
            fetch('/api/analytics/trends-timeline').then(r => r.json()),
            fetch('/api/analytics/emerging-trends').then(r => r.json()),
            fetch('/api/analytics/emerging-trends-dynamics').then(r => r.json()),
            fetch('/api/analytics/color-dynamics').then(r => r.json()),
            fetch('/api/analytics/material-dynamics').then(r => r.json())
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

    new Chart(ctx, {
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
                    position: 'bottom',
                    labels: { padding: 15, font: { size: 12 } }
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: { beginAtZero: true, grid: { display: true } }
            }
        }
    });
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

    new Chart(ctx, {
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
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: { size: 11 },
                        usePointStyle: true
                    }
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

    new Chart(ctx, {
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
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: { size: 11 },
                        usePointStyle: true
                    }
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

    new Chart(ctx, {
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
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: { size: 11 },
                        usePointStyle: true
                    }
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
}

// Загрузка данных при загрузке страницы
console.log('🚀 Analytics.js loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM Content Loaded - initializing analytics');

    // Загружаем всю аналитику
    loadAllAnalytics();

    console.log('✅ Initial load complete');
});
