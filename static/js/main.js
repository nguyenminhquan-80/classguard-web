// CLASSGUARD - Main JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Khởi tạo
    initDashboard();
    initCharts();
    initEventListeners();
    
    // Cập nhật dữ liệu mỗi 5 giây
    setInterval(updateDashboard, 5000);
    
    // Cập nhật thời gian thực
    setInterval(updateRealTime, 1000);
});

// Biểu đồ
let lineChart, barChart, gaugeChart;
let chartType = 'line'; // 'line' hoặc 'bar'

function initCharts() {
    const ctxLine = document.getElementById('lineChart')?.getContext('2d');
    const ctxBar = document.getElementById('barChart')?.getContext('2d');
    const ctxGauge = document.getElementById('gaugeChart')?.getContext('2d');
    
    if (ctxLine) {
        lineChart = new Chart(ctxLine, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Nhiệt độ (°C)',
                        data: [],
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Độ ẩm (%)',
                        data: [],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Ánh sáng (lux)',
                        data: [],
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Biểu đồ đường - Xu hướng thời gian'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        }
                    }
                }
            }
        });
    }
    
    if (ctxBar) {
        barChart = new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: ['Nhiệt độ', 'Độ ẩm', 'Ánh sáng', 'Chất lượng KK', 'Độ ồn'],
                datasets: [{
                    label: 'Giá trị hiện tại',
                    data: [0, 0, 0, 0, 0],
                    backgroundColor: [
                        'rgba(239, 68, 68, 0.7)',
                        'rgba(59, 130, 246, 0.7)',
                        'rgba(245, 158, 11, 0.7)',
                        'rgba(16, 185, 129, 0.7)',
                        'rgba(139, 92, 246, 0.7)'
                    ],
                    borderColor: [
                        '#ef4444',
                        '#3b82f6',
                        '#f59e0b',
                        '#10b981',
                        '#8b5cf6'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Biểu đồ cột - So sánh thông số'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        }
                    }
                }
            }
        });
    }
}

function initEventListeners() {
    // Nút điều khiển
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const device = this.dataset.device;
            const action = this.dataset.action;
            
            if (device && action) {
                controlDevice(device, action);
            }
        });
    });
    
    // Chuyển đổi biểu đồ
    const chartToggle = document.getElementById('chartToggle');
    if (chartToggle) {
        chartToggle.addEventListener('change', function() {
            chartType = this.value;
            updateChartVisibility();
        });
    }
    
    // Chế độ tự động
    const autoModeToggle = document.getElementById('autoModeToggle');
    if (autoModeToggle) {
        autoModeToggle.addEventListener('change', function() {
            updateSettings();
        });
    }
}

async function updateDashboard() {
    try {
        const response = await fetch('/get_sensor_data');
        const data = await response.json();
        
        if (data.sensors) {
            updateSensorDisplays(data.sensors);
            updateCharts(data);
            updateEvaluation(data.evaluation);
            updateDeviceStatus(data.sensors);
        }
    } catch (error) {
        console.error('Lỗi cập nhật dữ liệu:', error);
    }
}

function updateSensorDisplays(sensors) {
    // Cập nhật giá trị cảm biến
    document.getElementById('temp-value').textContent = sensors.nhiet_do.toFixed(1);
    document.getElementById('hum-value').textContent = sensors.do_am.toFixed(1);
    document.getElementById('light-value').textContent = Math.round(sensors.anh_sang);
    document.getElementById('air-value').textContent = Math.round(sensors.chat_luong_kk);
    document.getElementById('noise-value').textContent = Math.round(sensors.do_on);
    document.getElementById('last-update').textContent = sensors.timestamp || '--:--:--';
    
    // Cập nhật màu sắc theo giá trị
    updateSensorColor('temp', sensors.nhiet_do, [20, 28, 32]);
    updateSensorColor('hum', sensors.do_am, [40, 60, 75]);
    updateSensorColor('light', sensors.anh_sang, [200, 300, 400], true);
    updateSensorColor('air', sensors.chat_luong_kk, [400, 600, 800]);
    updateSensorColor('noise', sensors.do_on, [50, 60, 70]);
}

function updateSensorColor(type, value, thresholds, reverse = false) {
    const element = document.getElementById(`${type}-value`);
    if (!element) return;
    
    let colorClass = 'text-success'; // Tốt
    
    if (reverse) {
        if (value < thresholds[0]) colorClass = 'text-danger';
        else if (value < thresholds[1]) colorClass = 'text-warning';
        else colorClass = 'text-success';
    } else {
        if (value > thresholds[2]) colorClass = 'text-danger';
        else if (value > thresholds[1]) colorClass = 'text-warning';
        else if (value < thresholds[0]) colorClass = 'text-danger';
        else colorClass = 'text-success';
    }
    
    // Cập nhật class
    element.className = `value ${colorClass}`;
}

function updateCharts(data) {
    if (!data.history) return;
    
    const history = data.history;
    const sensors = data.sensors;
    
    // Biểu đồ đường
    if (lineChart && history.time && history.nhiet_do) {
        lineChart.data.labels = history.time.slice(-20);
        lineChart.data.datasets[0].data = history.nhiet_do.slice(-20);
        lineChart.data.datasets[1].data = history.do_am.slice(-20);
        lineChart.data.datasets[2].data = history.anh_sang.slice(-20);
        lineChart.update('none');
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

function updateEvaluation(evaluation) {
    if (!evaluation) return;
    
    // Đánh giá tổng thể
    const overallEl = document.getElementById('overall-evaluation');
    if (overallEl) {
        overallEl.textContent = evaluation.overall;
        overallEl.className = `badge bg-${evaluation.overall_class} p-3 fs-6`;
    }
    
    // Phần trăm
    const progressEl = document.getElementById('score-progress');
    if (progressEl) {
        progressEl.style.width = `${evaluation.percentage}%`;
        progressEl.textContent = `${evaluation.score}/10 (${evaluation.percentage.toFixed(1)}%)`;
        progressEl.className = `progress-bar bg-${evaluation.overall_class}`;
    }
    
    // Khuyến nghị
    const adviceEl = document.getElementById('advice-text');
    if (adviceEl) {
        adviceEl.textContent = evaluation.advice;
    }
    
    // Đánh giá chi tiết
    const detailsEl = document.getElementById('evaluation-details');
    if (detailsEl && evaluation.evaluations) {
        let html = '';
        evaluation.evaluations.forEach(item => {
            html += `
                <div class="col-md-6 mb-2">
                    <div class="d-flex justify-content-between align-items-center p-2 bg-light rounded">
                        <span>${item[0]}</span>
                        <span class="badge bg-${item[2]}">${item[1]}</span>
                    </div>
                </div>
            `;
        });
        detailsEl.innerHTML = html;
    }
}

function updateDeviceStatus(sensors) {
    // Cập nhật trạng thái nút
    ['quat', 'den', 'cua_so'].forEach(device => {
        const statusEl = document.getElementById(`${device}-status`);
        const onBtn = document.querySelector(`.btn[data-device="${device}"][data-action="BẬT"]`);
        const offBtn = document.querySelector(`.btn[data-device="${device}"][data-action="TẮT"]`);
        
        if (statusEl) {
            statusEl.textContent = sensors[device];
            statusEl.className = `badge bg-${sensors[device] === 'BẬT' ? 'success' : 'secondary'}`;
        }
        
        // Cập nhật trạng thái nút
        if (onBtn && offBtn) {
            if (sensors[device] === 'BẬT') {
                onBtn.classList.add('active', 'btn-success');
                onBtn.classList.remove('btn-outline-success');
                offBtn.classList.remove('active', 'btn-danger');
                offBtn.classList.add('btn-outline-danger');
            } else {
                offBtn.classList.add('active', 'btn-danger');
                offBtn.classList.remove('btn-outline-danger');
                onBtn.classList.remove('active', 'btn-success');
                onBtn.classList.add('btn-outline-success');
            }
        }
    });
}

async function controlDevice(device, action) {
    try {
        const response = await fetch('/control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                device: device,
                action: action
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Thành công', result.message, 'success');
            
            // Cập nhật ngay lập tức
            setTimeout(updateDashboard, 500);
        } else {
            showToast('Lỗi', result.error || 'Có lỗi xảy ra', 'danger');
        }
    } catch (error) {
        console.error('Lỗi điều khiển:', error);
        showToast('Lỗi', 'Không thể kết nối đến server', 'danger');
    }
}

async function updateSettings() {
    const autoMode = document.getElementById('autoModeToggle')?.checked || false;
    const tempMin = document.getElementById('tempMin')?.value || 20;
    const tempMax = document.getElementById('tempMax')?.value || 28;
    const lightThreshold = document.getElementById('lightThreshold')?.value || 300;
    const noiseThreshold = document.getElementById('noiseThreshold')?.value || 70;
    const airThreshold = document.getElementById('airThreshold')?.value || 800;
    
    try {
        const response = await fetch('/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                auto_mode: autoMode ? 'on' : 'off',
                temp_min: tempMin,
                temp_max: tempMax,
                light_threshold: lightThreshold,
                noise_threshold: noiseThreshold,
                air_threshold: airThreshold
            })
        });
        
        const result = await response.json();
        if (result.success) {
            showToast('Thành công', 'Đã cập nhật cài đặt!', 'success');
        }
    } catch (error) {
        console.error('Lỗi cập nhật cài đặt:', error);
    }
}

function updateChartVisibility() {
    const lineChartContainer = document.getElementById('lineChartContainer');
    const barChartContainer = document.getElementById('barChartContainer');
    
    if (chartType === 'line') {
        lineChartContainer.style.display = 'block';
        barChartContainer.style.display = 'none';
    } else {
        lineChartContainer.style.display = 'none';
        barChartContainer.style.display = 'block';
    }
}

function updateRealTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = 
        now.toLocaleTimeString('vi-VN');
    
    // Hiệu ứng nhấp nháy cho thời gian thực
    const timeElement = document.getElementById('current-time');
    timeElement.classList.toggle('text-primary');
}

function showToast(title, message, type) {
    const toastId = `toast-${Date.now()}`;
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}:</strong> ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.innerHTML = toastHtml;
    document.body.appendChild(container);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', function() {
        container.remove();
    });
}

// Hàm phụ trợ
function formatNumber(num) {
    return num.toLocaleString('vi-VN');
}

function getStatusColor(value, goodThreshold, warnThreshold) {
    if (value <= goodThreshold) return 'success';
    if (value <= warnThreshold) return 'warning';
    return 'danger';
}
