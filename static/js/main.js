// CLASSGUARD - Main JavaScript (Fixed Version)
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing CLASSGUARD system...');
    
    // Khởi tạo biểu đồ
    initCharts();
    
    // Khởi tạo event listeners
    initEventListeners();
    
    // Cập nhật dữ liệu ngay lần đầu
    updateDashboard();
    
    // Cập nhật mỗi 5 giây
    setInterval(updateDashboard, 5000);
    
    // Cập nhật thời gian
    setInterval(updateRealTime, 1000);
    
    console.log('CLASSGUARD initialized successfully');
});

// Biến toàn cục cho biểu đồ
let lineChart = null;
let barChart = null;

function initCharts() {
    console.log('Initializing charts...');
    
    const ctxLine = document.getElementById('lineChart');
    const ctxBar = document.getElementById('barChart');
    
    if (ctxLine) {
        console.log('Creating line chart...');
        lineChart = new Chart(ctxLine.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Nhiệt độ (°C)',
                        data: [],
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2
                    },
                    {
                        label: 'Độ ẩm (%)',
                        data: [],
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2
                    },
                    {
                        label: 'Ánh sáng (lux)',
                        data: [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2
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
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        },
                        ticks: {
                            font: {
                                size: 11
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        },
                        ticks: {
                            font: {
                                size: 11
                            },
                            maxRotation: 45
                        }
                    }
                }
            }
        });
        console.log('Line chart created');
    }
    
    if (ctxBar) {
        console.log('Creating bar chart...');
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
                    borderColor: [
                        '#dc3545',
                        '#0d6efd',
                        '#ffc107',
                        '#198754',
                        '#6f42c1'
                    ],
                    borderWidth: 1,
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        },
                        ticks: {
                            font: {
                                size: 11
                            }
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: 11
                            }
                        }
                    }
                }
            }
        });
        console.log('Bar chart created');
    }
}

function initEventListeners() {
    console.log('Setting up event listeners...');
    
    // Nút điều khiển thiết bị
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const device = this.dataset.device;
            const action = this.dataset.action;
            console.log(`Control clicked: ${device} -> ${action}`);
            
            if (device && action) {
                controlDevice(device, action);
            }
        });
    });
    
    // Chuyển đổi biểu đồ
    const chartToggle = document.getElementById('chartToggle');
    if (chartToggle) {
        chartToggle.addEventListener('change', function() {
            console.log('Chart toggle changed:', this.checked);
            updateChartVisibility();
        });
    }
    
    // Chế độ tự động
    const autoModeToggle = document.getElementById('autoModeToggle');
    if (autoModeToggle) {
        autoModeToggle.addEventListener('change', function() {
            console.log('Auto mode changed:', this.checked);
            updateAutoMode(this.checked);
        });
    }
    
    console.log('Event listeners set up');
}

async function updateDashboard() {
    try {
        console.log('Updating dashboard data...');
        const response = await fetch('/get_sensor_data');
        const data = await response.json();
        
        console.log('Received sensor data:', data);
        
        if (data.sensors) {
            updateSensorDisplays(data.sensors);
            updateCharts(data);
            updateEvaluation(data.evaluation);
            updateDeviceStatus(data.sensors);
        }
    } catch (error) {
        console.error('Error updating dashboard:', error);
    }
}

function updateSensorDisplays(sensors) {
    // Cập nhật giá trị
    updateElement('temp-value', sensors.nhiet_do.toFixed(1));
    updateElement('hum-value', sensors.do_am.toFixed(1));
    updateElement('light-value', Math.round(sensors.anh_sang));
    updateElement('air-value', Math.round(sensors.chat_luong_kk));
    updateElement('noise-value', Math.round(sensors.do_on));
    updateElement('last-update', sensors.timestamp || '--:--:--');
    
    // Cập nhật màu sắc
    updateSensorColor('temp', sensors.nhiet_do);
    updateSensorColor('hum', sensors.do_am);
    updateSensorColor('light', sensors.anh_sang);
    updateSensorColor('air', sensors.chat_luong_kk);
    updateSensorColor('noise', sensors.do_on);
}

function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function updateSensorColor(type, value) {
    const element = document.getElementById(`${type}-card`);
    if (!element) return;
    
    let colorClass = 'border-success';
    
    if (type === 'temp') {
        if (value > 32) colorClass = 'border-danger';
        else if (value > 28) colorClass = 'border-warning';
        else if (value >= 20) colorClass = 'border-success';
        else colorClass = 'border-danger';
    } else if (type === 'hum') {
        if (value < 40 || value > 70) colorClass = 'border-warning';
        else colorClass = 'border-success';
    } else if (type === 'light') {
        if (value < 200) colorClass = 'border-danger';
        else if (value < 300) colorClass = 'border-warning';
        else colorClass = 'border-success';
    } else if (type === 'air') {
        if (value > 800) colorClass = 'border-danger';
        else if (value > 400) colorClass = 'border-warning';
        else colorClass = 'border-success';
    } else if (type === 'noise') {
        if (value > 70) colorClass = 'border-danger';
        else if (value > 50) colorClass = 'border-warning';
        else colorClass = 'border-success';
    }
    
    element.className = element.className.replace(/border-(success|warning|danger)/g, '');
    element.classList.add(colorClass);
}

function updateCharts(data) {
    if (!data.history) {
        console.warn('No history data available');
        return;
    }
    
    const history = data.history;
    const sensors = data.sensors;
    
    console.log('Updating charts with history:', history);
    
    // Biểu đồ đường
    if (lineChart && history.time && history.nhiet_do) {
        lineChart.data.labels = history.time;
        lineChart.data.datasets[0].data = history.nhiet_do;
        lineChart.data.datasets[1].data = history.do_am;
        lineChart.data.datasets[2].data = history.anh_sang;
        lineChart.update('none');
        console.log('Line chart updated');
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
        console.log('Bar chart updated');
    }
}

function updateEvaluation(evaluation) {
    if (!evaluation) {
        console.warn('No evaluation data available');
        return;
    }
    
    console.log('Updating evaluation:', evaluation);
    
    // Đánh giá tổng thể
    updateElement('overall-evaluation', evaluation.overall);
    const overallElement = document.getElementById('overall-evaluation');
    if (overallElement) {
        overallElement.className = `badge bg-${evaluation.overall_class} p-2 fs-6`;
    }
    
    // Điểm số
    updateElement('score-value', `${evaluation.total_score}/10`);
    const scoreElement = document.getElementById('score-value');
    if (scoreElement) {
        scoreElement.className = `badge bg-${evaluation.overall_class} p-2 fs-5`;
    }
    
    // Progress bar
    const progressBar = document.getElementById('score-progress');
    if (progressBar) {
        progressBar.style.width = `${evaluation.percentage}%`;
        progressBar.textContent = `${evaluation.percentage}%`;
        progressBar.className = `progress-bar bg-${evaluation.overall_class}`;
    }
    
    // Khuyến nghị
    updateElement('advice-text', evaluation.advice);
    const adviceElement = document.getElementById('advice-text');
    if (adviceElement) {
        adviceElement.className = `alert alert-${evaluation.overall_class}`;
    }
    
    // Tiết học
    updateElement('class-eval', evaluation.class_eval);
    const classEvalElement = document.getElementById('class-eval');
    if (classEvalElement) {
        classEvalElement.className = `badge bg-${evaluation.class_color}`;
    }
    
    // Đánh giá chi tiết
    const detailsElement = document.getElementById('evaluation-details');
    if (detailsElement && evaluation.evaluations) {
        let html = '<div class="row g-2">';
        evaluation.evaluations.forEach(item => {
            html += `
                <div class="col-md-6 mb-2">
                    <div class="d-flex justify-content-between align-items-center p-2 bg-light rounded">
                        <span class="small">${item[0]}</span>
                        <span class="badge bg-${item[2]}">${item[1]}</span>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        detailsElement.innerHTML = html;
    }
}

function updateDeviceStatus(sensors) {
    console.log('Updating device status:', sensors);
    
    const devices = ['quat', 'den', 'cua_so', 'canh_bao'];
    
    devices.forEach(device => {
        const status = sensors[device];
        const isOn = status === 'BẬT' || status === 'MỞ';
        
        // Cập nhật icon
        const iconElement = document.getElementById(`${device}-icon`);
        if (iconElement) {
            if (device === 'quat') {
                iconElement.className = isOn ? 'fas fa-fan fa-spin text-success' : 'fas fa-fan text-secondary';
            } else if (device === 'den') {
                iconElement.className = isOn ? 'fas fa-lightbulb text-warning' : 'fas fa-lightbulb text-secondary';
                iconElement.style.filter = isOn ? 'brightness(1.5) drop-shadow(0 0 5px gold)' : 'brightness(0.7)';
            } else if (device === 'canh_bao') {
                iconElement.className = isOn ? 'fas fa-bell text-danger fa-shake' : 'fas fa-bell text-secondary';
            } else {
                iconElement.className = isOn ? 'fas fa-window-open text-info' : 'fas fa-window-closed text-secondary';
            }
        }
        
        // Cập nhật nút
        const onBtn = document.querySelector(`[data-device="${device}"][data-action="${device === 'cua_so' ? 'MỞ' : 'BẬT'}"]`);
        const offBtn = document.querySelector(`[data-device="${device}"][data-action="${device === 'cua_so' ? 'ĐÓNG' : 'TẮT'}"]`);
        
        if (onBtn && offBtn) {
            if (isOn) {
                onBtn.classList.remove('btn-outline-success');
                onBtn.classList.add('btn-success');
                offBtn.classList.remove('btn-danger');
                offBtn.classList.add('btn-outline-danger');
            } else {
                offBtn.classList.remove('btn-outline-danger');
                offBtn.classList.add('btn-danger');
                onBtn.classList.remove('btn-success');
                onBtn.classList.add('btn-outline-success');
            }
        }
        
        // Cập nhật trạng thái text
        updateElement(`${device}-status`, status);
        const statusElement = document.getElementById(`${device}-status`);
        if (statusElement) {
            statusElement.className = `badge bg-${isOn ? 'success' : 'secondary'} p-1`;
        }
    });
}

async function controlDevice(device, action) {
    console.log(`Sending control: ${device} -> ${action}`);
    
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
        console.log('Control response:', result);
        
        if (result.success) {
            showToast('Thành công', result.message, 'success');
            // Cập nhật ngay lập tức
            setTimeout(updateDashboard, 500);
        } else {
            showToast('Lỗi', result.error || 'Có lỗi xảy ra', 'danger');
        }
    } catch (error) {
        console.error('Control error:', error);
        showToast('Lỗi', 'Không thể kết nối đến server', 'danger');
    }
}

async function updateAutoMode(enabled) {
    try {
        const response = await fetch('/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `auto_mode=${enabled ? 'on' : 'off'}`
        });
        
        const result = await response.json();
        if (result.success) {
            showToast('Thành công', 'Đã cập nhật chế độ tự động', 'success');
        }
    } catch (error) {
        console.error('Auto mode update error:', error);
    }
}

function updateChartVisibility() {
    const chartToggle = document.getElementById('chartToggle');
    const lineContainer = document.getElementById('lineChartContainer');
    const barContainer = document.getElementById('barChartContainer');
    
    if (chartToggle && lineContainer && barContainer) {
        if (chartToggle.checked) {
            lineContainer.style.display = 'none';
            barContainer.style.display = 'block';
        } else {
            lineContainer.style.display = 'block';
            barContainer.style.display = 'none';
        }
    }
}

function updateRealTime() {
    const now = new Date();
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = now.toLocaleTimeString('vi-VN');
    }
}

function showToast(title, message, type) {
    // Tạo toast element
    const toastId = 'toast-' + Date.now();
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
    
    // Thêm vào DOM
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.innerHTML = toastHtml;
    document.body.appendChild(container);
    
    // Hiển thị toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Xóa sau khi ẩn
    toastElement.addEventListener('hidden.bs.toast', function() {
        container.remove();
    });
}

// Debug: Kiểm tra tất cả element IDs
function debugCheckElements() {
    const requiredIds = [
        'temp-value', 'hum-value', 'light-value', 'air-value', 'noise-value',
        'lineChart', 'barChart', 'overall-evaluation', 'score-value',
        'score-progress', 'advice-text', 'class-eval', 'evaluation-details'
    ];
    
    console.log('Checking required elements...');
    requiredIds.forEach(id => {
        const element = document.getElementById(id);
        console.log(`${id}: ${element ? 'FOUND' : 'NOT FOUND'}`);
    });
}

// Chạy debug khi cần
// setTimeout(debugCheckElements, 1000);
