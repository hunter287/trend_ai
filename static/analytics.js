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

// Переключение вкладок
function setupTabHandlers() {
    console.log('🎯 Setting up tab handlers...');
    const tabs = document.querySelectorAll('.tab');
    console.log('Found tabs:', tabs.length);

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.dataset.tab;
            console.log('🔄 Tab clicked:', targetTab);

            // Обновляем активную вкладку
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');

            // Показываем нужный контент
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(targetTab + '-content').classList.add('active');

            // Загружаем данные для вкладки, если еще не загружены
            if (targetTab === 'trends' && !window.trendsLoaded) {
                console.log('📊 Loading trends for the first time');
                loadTrendsAnalytics();
                window.trendsLoaded = true;
            } else if (targetTab === 'predictive' && !window.predictiveLoaded) {
                console.log('🔮 Loading predictive for the first time');
                loadPredictiveAnalytics();
                window.predictiveLoaded = true;
            } else {
                console.log('✅ Tab already loaded');
            }
        });
    });
    console.log('✅ Tab handlers set up');
}

// ============================================
// МОДНЫЕ ТРЕНДЫ
// ============================================

async function loadTrendsAnalytics() {
    console.log('🔄 Loading trends analytics...');
    try {
        console.log('📡 Fetching API data...');
        const [categories, subcategories, colors, materials, styles, timeline] = await Promise.all([
            fetch('/api/analytics/categories-stats').then(r => {
                console.log('✅ Categories response:', r.status);
                return r.json();
            }),
            fetch('/api/analytics/subcategories-stats').then(r => {
                console.log('✅ Subcategories response:', r.status);
                return r.json();
            }),
            fetch('/api/analytics/colors-stats').then(r => {
                console.log('✅ Colors response:', r.status);
                return r.json();
            }),
            fetch('/api/analytics/materials-stats').then(r => {
                console.log('✅ Materials response:', r.status);
                return r.json();
            }),
            fetch('/api/analytics/styles-stats').then(r => {
                console.log('✅ Styles response:', r.status);
                return r.json();
            }),
            fetch('/api/analytics/trends-timeline').then(r => {
                console.log('✅ Timeline response:', r.status);
                return r.json();
            })
        ]);

        console.log('📊 Categories data:', categories);
        console.log('📊 Subcategories data:', subcategories);
        console.log('📊 Colors data:', colors);

        // Обновляем статистику
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

        // Рисуем графики
        console.log('🎨 Drawing charts...');
        if (categories.success) {
            console.log('📊 Drawing categories chart');
            drawCategoriesChart(categories.categories);
        }
        if (subcategories.success) {
            console.log('📊 Drawing subcategories chart');
            drawSubcategoriesChart(subcategories.subcategories);
        }
        if (colors.success) {
            console.log('📊 Drawing colors chart');
            drawColorsChart(colors.colors);
        }
        if (materials.success) {
            console.log('📊 Drawing materials chart');
            drawMaterialsChart(materials.materials);
        }
        if (styles.success) {
            console.log('📊 Drawing styles chart');
            drawStylesChart(styles.styles);
        }
        if (timeline.success) {
            console.log('📊 Drawing timeline chart');
            drawTimelineChart(timeline.timeline);
        }

        console.log('✅ Trends analytics loaded successfully!');

    } catch (error) {
        console.error('❌ Ошибка загрузки аналитики трендов:', error);
        console.error('Stack trace:', error.stack);
        document.querySelector('#trends-content').insertAdjacentHTML('afterbegin',
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
// ПРОГНОЗНАЯ АНАЛИТИКА
// ============================================

async function loadPredictiveAnalytics() {
    console.log('🔮 Loading predictive analytics...');
    try {
        console.log('📡 Fetching predictive API data...');
        const [trends, dynamics, predictions, recommendations] = await Promise.all([
            fetch('/api/analytics/emerging-trends').then(r => {
                console.log('✅ Emerging trends response:', r.status);
                return r.json();
            }),
            fetch('/api/analytics/emerging-trends-dynamics').then(r => {
                console.log('✅ Emerging trends dynamics response:', r.status);
                return r.json();
            }),
            fetch('/api/analytics/trend-predictions').then(r => {
                console.log('✅ Predictions response:', r.status);
                return r.json();
            }),
            fetch('/api/analytics/recommendations').then(r => {
                console.log('✅ Recommendations response:', r.status);
                return r.json();
            })
        ]);

        console.log('📊 Trends data:', trends);
        console.log('📊 Dynamics data:', dynamics);
        console.log('📊 Predictions data:', predictions);
        console.log('📊 Recommendations data:', recommendations);

        // Обновляем статистику
        if (trends.success) {
            document.getElementById('emergingTrendsCount').textContent = trends.emerging.length;
            document.getElementById('decliningTrendsCount').textContent = trends.declining.length;
        }

        if (predictions.success) {
            const avgEngagement = predictions.overall_metrics?.predicted_engagement || 0;
            document.getElementById('predictedEngagement').textContent = '+' + avgEngagement.toFixed(0) + '%';

            const confidence = predictions.confidence_score || 0;
            document.getElementById('confidenceScore').textContent = (confidence * 100).toFixed(0) + '%';
        }

        // Рисуем инсайты
        if (predictions.success && predictions.insights) {
            drawInsights(predictions.insights);
        }

        // Рисуем графики
        if (trends.success) {
            console.log('📊 Drawing emerging trends (top 10)');
            drawEmergingTrendsTop10Chart(trends.emerging.slice(0, 10));
        }

        if (dynamics.success) {
            console.log('📈 Drawing emerging trends dynamics');
            drawEmergingTrendsDynamicsChart(dynamics);
        }

        if (predictions.success) {
            drawColorPredictionChart(predictions.color_predictions || []);
            drawCombinationsChart(predictions.top_combinations || []);
        }

        // Рисуем рекомендации
        if (recommendations.success) {
            console.log('📝 Drawing recommendations');
            drawRecommendations(recommendations.recommendations);
        }

        console.log('✅ Predictive analytics loaded successfully!');

    } catch (error) {
        console.error('❌ Ошибка загрузки прогнозной аналитики:', error);
        console.error('Stack trace:', error.stack);
        document.querySelector('#predictive-content').insertAdjacentHTML('afterbegin',
            '<div class="error-message">Ошибка загрузки данных: ' + error.message + '</div>');
    }
}

function drawInsights(insights) {
    const container = document.getElementById('insightsContainer');
    container.innerHTML = '';

    insights.forEach(insight => {
        const card = document.createElement('div');
        card.className = 'insight-card';
        card.innerHTML = `
            <h4>💡 ${insight.title}</h4>
            <p>${insight.description}</p>
        `;
        container.appendChild(card);
    });
}

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

function drawColorPredictionChart(predictions) {
    const ctx = document.getElementById('colorPredictionChart').getContext('2d');
    const backgroundColors = predictions.map(p => colorMapping[p.color] || chartColors.palette[0]);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: predictions.map(p => p.color),
            datasets: [{
                label: 'Прогноз популярности',
                data: predictions.map(p => p.predicted_score),
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
                x: { beginAtZero: true },
                y: { grid: { display: false } }
            }
        }
    });
}

function drawCombinationsChart(combinations) {
    const ctx = document.getElementById('combinationsChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: combinations.map(c => c.name),
            datasets: [{
                label: 'Прогноз engagement',
                data: combinations.map(c => c.engagement_score),
                backgroundColor: chartColors.palette[1],
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { beginAtZero: true },
                y: { grid: { display: false } }
            }
        }
    });
}

function drawRecommendations(recommendations) {
    const container = document.getElementById('recommendationsList');
    container.innerHTML = '';

    recommendations.forEach(rec => {
        const item = document.createElement('li');
        item.className = 'recommendation-item';
        item.innerHTML = `
            <h5>${rec.title}</h5>
            <p>${rec.description}</p>
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: ${rec.confidence * 100}%"></div>
            </div>
            <small style="color: #6c757d; margin-top: 5px; display: block;">
                Уверенность: ${(rec.confidence * 100).toFixed(0)}%
            </small>
        `;
        container.appendChild(item);
    });
}

// Загрузка данных при загрузке страницы
console.log('🚀 Analytics.js loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM Content Loaded - initializing analytics');

    // Настраиваем обработчики вкладок
    setupTabHandlers();

    // Загружаем начальные данные для первой вкладки
    loadTrendsAnalytics();
    window.trendsLoaded = true;
    console.log('✅ Initial load complete');
});
