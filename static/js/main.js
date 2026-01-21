// CLASSGUARD - Main JavaScript với biểu đồ 5 đường hoàn chỉnh
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 CLASSGUARD Dashboard đang khởi động...');
    
    // Khởi tạo biểu đồ với 5 đường
    initCharts();
    initEventListeners();
    
    // Cập nhật lần đầu
    setTimeout(updateDashboard, 500);
    
    // Cập nhật định kỳ
    setInterval(updateDashboard, 2000);
    setInterval(updateRealTime, 1000);
    setInterval(checkESP32Status, 3000);
    
    console.log('✅ Dashboard đã sẵn sàng với biểu đồ 5 đường');
});

// Biến toàn cục
let lineChart = null;
let barChart = null;
let isAutoMode = false;
let esp32Connected = false;

function initCharts() {
    console.log('📊 Khởi tạo biểu đồ với 5 thông số...');
    
    const ctxLine = document.getElementById('lineChart');
    const ctxBar = document.getElementById('barChart');
    
    if (lineChart) lineChart.destroy();
    if (barChart) barChart.destroy();
    
    if (ctxLine) {
        lineChart = new Chart(ctxLine.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '🌡️ Nhiệt độ',
                        data: [],
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 3,
                        yAxisID: 'y-temp'
                    },
                    {
                        label: '💧 Độ ẩm',
                        data: [],
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 3,
                        yAxisID: 'y-hum'
                    },
                    {
                        label: '☀️ Ánh sáng',
                        data: [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 3,
                        yAxisID: 'y-light'
                    },
                    {
                        label: '💨 Chất lượng KK',
                        data: [],
                        borderColor: '#198754',
                        backgroundColor: 'rgba(25, 135, 84, 0.1)',
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 3,
                        yAxisID: 'y-air'
                    },
                    {
                        label: '🔊 Độ ồn',
                        data: [],
                        borderColor: '#6f42c1',
                        backgroundColor: 'rgba(111, 66, 193, 0.1)',
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 3,
                        yAxisID: 'y-noise'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            font: { size: 11 },
                            boxWidth: 12
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                let value = context.parsed.y;
                                let unit = '';
                                
                                if (label.includes('Nhiệt độ')) unit = '°C';
                                else if (label.includes('Độ ẩm')) unit = '%';
                                else if (label.includes('Ánh sáng')) unit = 'lux';
                                else if (label.includes('Chất lượng')) unit = 'ppm';
                                else if (label.includes('Độ ồn')) unit = 'dB';
                                
                                if (label.includes('Nhiệt độ') || label.includes('Độ ẩm')) {
                                    value = value.toFixed(1);
                                } else {
                                    value = Math.round(value);
                                }
                                
                                return `${label}: ${value} ${unit}`;
                            }
                        }
                    }
                },
                scales: {
                    'y-temp': {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Nhiệt độ (°C)',
                            font: { size: 11 }
                        },
                        min: 15,
                        max: 40,
                        grid: { drawOnChartArea: false }
                    },
                    'y-hum': {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Độ ẩm (%)',
                            font: { size: 11 }
                        },
                        min: 20,
                        max: 90,
                        grid: { drawOnChartArea: false }
                    },
                    'y-light': {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Ánh sáng (lux)',
                            font: { size: 11 }
                        },
                        min: 0,
                        max: 1000,
                        grid: { drawOnChartArea: false }
                    },
                    'y-air': {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Chất lượng KK (ppm)',
                            font: { size: 11 }
                        },
                        min: 0,
                        max: 1200,
                        grid: { drawOnChartArea: false }
                    },
                    'y-noise': {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Độ ồn (dB)',
                            font: { size: 11 }
                        },
                        min: 20,
                        max: 100,
                        grid: { drawOnChartArea: false }
                    },
                    x: {
                        grid: { color: 'rgba(0,0,0,0.05)' },
                        ticks: { 
                            font: { size: 10 },
                            maxRotation: 0,
                            maxTicksLimit: 8
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
        console.log('✅ Biểu đồ đường đã khởi tạo với 5 thông số');
    }
    
    if (ctxBar) {
        barChart = new Chart(ctxBar.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Nhiệt độ', 'Độ ẩm', 'Ánh sáng', 'Chất lượng KK', 'Độ ồn'],
                datasets: [{
                    label: 'Giá trị',
                    data: [0, 0, 0, 0, 0],
                    backgroundColor: [
                        'rgba(220, 53, 69, 0.7)',
                        'rgba(13, 110, 253, 0.7)',
                        'rgba(255, 193, 7, 0.7)',
                        'rgba(25, 135, 84, 0.7)',
                        'rgba(111, 66, 193, 0.7)'
                    ],
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const units = ['°C', '%', 'lux', 'ppm', 'dB'];
                                let value = context.parsed.y;
                                const index = context.dataIndex;
                                
                                if (index === 0 || index === 1) {
                                    value = value.toFixed(1);
                                } else {
                                    value = Math.round(value);
                                }
                                
                                return `Giá trị: ${value} ${units[index]}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { font: { size: 10 } }
                    },
                    x: {
                        ticks: { font: { size: 11 } }
                    }
                }
            }
        });
    }
}

function initEventListeners() {
    console.log('🔄 Thiết lập event listeners...');
    
    // Nút điều khiển thiết bị
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const device = this.dataset.device;
            const action = this.dataset.action;
            
            // LUÔN cho phép điều khiển cảnh báo
            if (device === 'canh_bao') {
                controlDevice(device, action);
            } 
            // Các thiết bị khác kiểm tra auto mode
            else if (!isAutoMode) {
                controlDevice(device, action);
            } else {
                showToast('⚠️ Cảnh báo', 'Tắt chế độ tự động để điều khiển thủ công', 'warning');
            }
        });
    });
    
    // Chuyển đổi biểu đồ
    const chartToggle = document.getElementById('chartToggle');
    if (chartToggle) {
        chartToggle.addEventListener('change', function() {
            updateChartVisibility(this.checked);
        });
    }
    
    // Đồng bộ 2 toggle auto mode
    const autoToggle1 = document.getElementById('autoModeToggle');
    const autoToggle2 = document.getElementById('autoModeToggle2');
    
    if (autoToggle1 && autoToggle2) {
        autoToggle1.addEventListener('change', function() {
            updateAutoMode(this.checked);
            autoToggle2.checked = this.checked;
        });
        
        autoToggle2.addEventListener('change', function() {
            updateAutoMode(this.checked);
            autoToggle1.checked = this.checked;
        });
    }
}

async function updateDashboard() {
    try {
        console.log('🔄 Đang cập nhật dashboard...');
        const response = await fetch('/get_sensor_data');
        const data = await response.json();
        
        if (data.sensors) {
            console.log('📊 Nhận dữ liệu cảm biến:', data.sensors);
            
            updateSensorDisplays(data.sensors);
            updateCharts(data);
            updateEvaluation(data.evaluation);
            updateDeviceStatus(data.sensors);
            
            // Cập nhật chế độ tự động
            if (data.settings) {
                isAutoMode = data.settings.auto_mode;
                updateAutoModeUI(isAutoMode);
            }
            
            // Cập nhật trạng thái ESP32
            esp32Connected = data.esp32_connected || false;
            updateESP32StatusUI(esp32Connected, data.esp32_last_update);
        }
    } catch (error) {
        console.error('❌ Lỗi cập nhật dashboard:', error);
    }
}

function updateCharts(data) {
    if (!data.history) {
        console.log('⚠️ Không có dữ liệu history');
        return;
    }
    
    console.log('📈 Cập nhật biểu đồ với dữ liệu:', data.history);
    
    const history = data.history;
    const sensors = data.sensors;
    
    // Biểu đồ đường - CẬP NHẬT 5 THÔNG SỐ
    if (lineChart && history.time) {
        const maxPoints = 10;
        const start = Math.max(0, history.time.length - maxPoints);
        
        // Lấy dữ liệu time
        const displayTimes = history.time.slice(start).map(time => {
            const [hours, minutes, seconds] = time.split(':');
            return `${hours}:${minutes}`;
        });
        
        // Cập nhật labels
        lineChart.data.labels = displayTimes;
        
        // Cập nhật 5 dataset
        if (history.nhiet_do && history.nhiet_do.length > 0) {
            lineChart.data.datasets[0].data = history.nhiet_do.slice(start);
            console.log('🌡️ Nhiệt độ data:', history.nhiet_do.slice(start));
        }
        
        if (history.do_am && history.do_am.length > 0) {
            lineChart.data.datasets[1].data = history.do_am.slice(start);
            console.log('💧 Độ ẩm data:', history.do_am.slice(start));
        }
        
        if (history.anh_sang && history.anh_sang.length > 0) {
            lineChart.data.datasets[2].data = history.anh_sang.slice(start);
            console.log('☀️ Ánh sáng data:', history.anh_sang.slice(start));
        }
        
        if (history.chat_luong_kk && history.chat_luong_kk.length > 0) {
            lineChart.data.datasets[3].data = history.chat_luong_kk.slice(start);
            console.log('💨 Chất lượng KK data:', history.chat_luong_kk.slice(start));
        }
        
        if (history.do_on && history.do_on.length > 0) {
            lineChart.data.datasets[4].data = history.do_on.slice(start);
            console.log('🔊 Độ ồn data:', history.do_on.slice(start));
        }
        
        lineChart.update('none');
        console.log('✅ Biểu đồ đường đã cập nhật với 5 thông số');
    }
    
    // Biểu đồ cột
    if (barChart) {
        barChart.data.datasets[0].data = [
            sensors.nhiet_do,
            sensors.do_am,
            sensors.anh_sang,
            sensors.chat_luong_kk,
            sensors.do_on
        ];
        barChart.update('none');
    }
}

// Các hàm khác giữ nguyên như trước...

function updateESP32StatusUI(connected, lastUpdate) {
    const esp32Status = document.getElementById('esp32-status');
    
    if (esp32Status) {
        if (connected) {
            esp32Status.innerHTML = `
                <i class="fas fa-wifi text-success"></i>
                <span class="ms-2">ESP32: Đã kết nối</span>
                <small class="ms-2 text-muted">${lastUpdate || ''}</small>
            `;
            esp32Status.className = 'badge bg-success p-2';
        } else {
            esp32Status.innerHTML = `
                <i class="fas fa-wifi-slash text-danger"></i>
                <span class="ms-2">ESP32: Mất kết nối</span>
            `;
            esp32Status.className = 'badge bg-danger p-2';
        }
    }
}

function updateSensorDisplays(sensors) {
    updateElement('temp-value', sensors.nhiet_do.toFixed(1));
    updateElement('hum-value', sensors.do_am.toFixed(1));
    updateElement('light-value', Math.round(sensors.anh_sang));
    updateElement('air-value', Math.round(sensors.chat_luong_kk));
    updateElement('noise-value', Math.round(sensors.do_on));
    updateElement('last-update', sensors.timestamp || '--:--:--');
}

function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

// ... các hàm khác giữ nguyên ...

// Thêm CSS cho biểu đồ 5 đường
const style = document.createElement('style');
style.textContent = `
    /* Fix chart containers */
    .chart-container {
        height: 320px !important;
        min-height: 320px !important;
        max-height: 320px !important;
        position: relative;
    }
    
    #lineChart, #barChart {
        width: 100% !important;
        height: 320px !important;
        max-height: 320px !important;
    }
    
    /* Compact legend */
    .chartjs-legend {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        margin-bottom: 10px;
    }
    
    .chartjs-legend li {
        display: inline-flex;
        align-items: center;
        margin: 0 8px 5px 0;
    }
    
    .chartjs-legend .legend-marker {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 5px;
        display: inline-block;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .chart-container {
            height: 280px !important;
        }
        
        #lineChart, #barChart {
            height: 280px !important;
        }
        
        .chartjs-legend {
            justify-content: flex-start;
        }
        
        .chartjs-legend li {
            margin: 0 5px 3px 0;
            font-size: 0.85rem;
        }
    }
`;
document.head.appendChild(style);
