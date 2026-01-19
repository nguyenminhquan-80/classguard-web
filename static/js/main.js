// CLASSGUARD - Main JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initDashboard();
    initCharts();
    initEventListeners();
    
    // Cập nhật dữ liệu mỗi 5 giây
    setInterval(updateDashboard, 5000);
    
    // Cập nhật thời gian thực
    setInterval(updateRealTime, 1000);
    
    // Cập nhật ngay lần đầu
    updateDashboard();
});

// Biểu đồ
let lineChart, barChart;
let chartData = {
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
        },
        {
            label: 'Chất lượng KK (PPM)',
            data: [],
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            tension: 0.4,
            fill: true
        },
        {
            label: 'Độ ồn (dB)',
            data: [],
            borderColor: '#8b5cf6',
            backgroundColor: 'rgba(139, 92, 246, 0.1)',
            tension: 0.4,
            fill: true
        }
    ]
};

function initCharts() {
    const ctxLine = document.getElementById('lineChart');
    const ctxBar = document.getElementById('barChart');
    
    if (ctxLine) {
        lineChart = new Chart(ctxLine.getContext('2d'), {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Biểu đồ đường - Xu hướng thời gian',
                        font: {
                            size: 16
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
                            callback: function(value) {
                                return value.toFixed(1);
                            }
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
        barChart = new Chart(ctxBar.getContext('2d'), {
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
                    borderWidth: 2,
                    borderRadius: 5
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
                        text: 'Biểu đồ cột - So sánh thông số',
                        font: {
                            size: 16
                        }
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
            updateChartVisibility();
        });
    }
    
    // Toggle password visibility
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('passwordInput');
    
    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            this.querySelector('i').classList.toggle('fa-eye');
            this.querySelector('i').classList.toggle('fa-eye-slash');
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
    // Cập nhật giá trị cảm biến (1 số sau dấu phẩy)
    document.getElementById('temp-value').textContent = sensors.nhiet_do.toFixed(1);
    document.getElementById('hum-value').textContent = sensors.do_am.toFixed(1);
    document.getElementById('light-value').textContent = Math.round(sensors.anh_sang);
    document.getElementById('air-value').textContent = Math.round(sensors.chat_luong_kk);
    document.getElementById('noise-value').textContent = Math.round(sensors.do_on);
    document.getElementById('last-update').textContent = sensors.timestamp || '--:--:--';
    
    // Cập nhật màu sắc
    updateSensorColor('temp', sensors.nhiet_do, [20, 28, 32]);
    updateSensorColor('hum', sensors.do_am, [40, 60, 75]);
    updateSensorColor('light', sensors.anh_sang, [200, 300, 400], true);
    updateSensorColor('air', sensors.chat_luong_kk, [400, 600, 800]);
    updateSensorColor('noise', sensors.do_on, [50, 60, 70]);
}

function updateSensorColor(type, value, thresholds, reverse = false) {
    const element = document.getElementById(`${type}-card`);
    if (!element) return;
    
    let colorClass = 'border-success'; // Tốt
    
    if (reverse) {
        if (value < thresholds[0]) colorClass = 'border-danger';
        else if (value < thresholds[1]) colorClass = 'border-warning';
        else colorClass = 'border-success';
    } else {
        if (value > thresholds[2]) colorClass = 'border-danger';
        else if (value > thresholds[1]) colorClass = 'border-warning';
        else if (value < thresholds[0]) colorClass = 'border-danger';
        else colorClass = 'border-success';
    }
    
    // Cập nhật border
    element.className = element.className.replace(/border-(success|warning|danger)/g, '');
    element.classList.add(colorClass);
}

function updateCharts(data) {
    if (!data.history) return;
    
    const history = data.history;
    const sensors = data.sensors;
    
    // Biểu đồ đường
    if (lineChart && history.time && history.nhiet_do) {
        // Giữ tối đa 20 điểm
        const maxPoints = 20;
        const start = Math.max(0, history.time.length - maxPoints);
        
        lineChart.data.labels = history.time.slice(start);
        lineChart.data.datasets[0].data = history.nhiet_do.slice(start);
        lineChart.data.datasets[1].data = history.do_am.slice(start);
        lineChart.data.datasets[2].data = history.anh_sang.slice(start);
        lineChart.data.datasets[3].data = history.chat_luong_kk.slice(start);
        lineChart.data.datasets[4].data = history.do_on.slice(start);
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
        overallEl.innerHTML = `
            <div class="text-center">
                <div class="fs-1 mb-2">${evaluation.overall}</div>
                <div class="fs-5 text-muted">${evaluation.class_eval}</div>
            </div>
        `;
        overallEl.className = `card evaluation-card border-${evaluation.overall_class} bg-${evaluation.overall_class} bg-opacity-10`;
    }
    
    // Phần trăm
    const scoreEl = document.getElementById('score-value');
    if (scoreEl) {
        scoreEl.textContent = `${evaluation.total_score}/10`;
        scoreEl.className = `badge bg-${evaluation.overall_class} p-3 fs-4`;
    }
    
    // Progress bar
    const progressEl = document.getElementById('score-progress');
    if (progressEl) {
        progressEl.style.width = `${evaluation.percentage}%`;
        progressEl.textContent = `${evaluation.percentage}%`;
        progressEl.className = `progress-bar progress-bar-striped progress-bar-animated bg-${evaluation.overall_class}`;
    }
    
    // Khuyến nghị
    const adviceEl = document.getElementById('advice-text');
    if (adviceEl) {
        adviceEl.textContent = evaluation.advice;
        adviceEl.className = `alert alert-${evaluation.overall_class}`;
    }
    
    // Đánh giá chi tiết
    const detailsEl = document.getElementById('evaluation-details');
    if (detailsEl && evaluation.evaluations) {
        let html = '<div class="row g-2">';
        evaluation.evaluations.forEach(item => {
            html += `
                <div class="col-md-6">
                    <div class="d-flex justify-content-between align-items-center p-3 bg-light rounded-3 border border-${item[2]} border-opacity-25">
                        <div>
                            <span class="fs-5">${item[0]}</span>
                            <div class="text-muted small">${getEvaluationDescription(item[1])}</div>
                        </div>
                        <span class="badge bg-${item[2]} fs-6 px-3 py-2">${item[1]}</span>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        detailsEl.innerHTML = html;
    }
}

function getEvaluationDescription(status) {
    const descriptions = {
        'Lý tưởng': 'Hoàn hảo cho học tập',
        'Chấp nhận': 'Có thể chấp nhận được',
        'Không tốt': 'Cần cải thiện',
        'Tốt': 'Đạt yêu cầu',
        'Trung bình': 'Cần theo dõi',
        'Đủ sáng': 'Đạt tiêu chuẩn',
        'Hơi tối': 'Cần bổ sung ánh sáng',
        'Thiếu sáng': 'Ảnh hưởng thị lực',
        'Trong lành': 'Không khí tốt',
        'Ô nhiễm': 'Cần thông thoáng',
        'Yên tĩnh': 'Môi trường tốt',
        'Bình thường': 'Ổn định',
        'Ồn ào': 'Gây mất tập trung'
    };
    return descriptions[status] || 'Đang đánh giá';
}

function updateDeviceStatus(sensors) {
    const devices = ['quat', 'den', 'cua_so', 'canh_bao'];
    
    devices.forEach(device => {
        const status = sensors[device];
        const isOn = status === 'BẬT' || status === 'MỞ';
        
        // Cập nhật icon
        const iconElement = document.getElementById(`${device}-icon`);
        if (iconElement) {
            if (device === 'quat') {
                iconElement.className = isOn ? 'fas fa-fan fa-spin text-success' : 'fas fa-fan text-secondary';
                iconElement.style.fontSize = isOn ? '2.5rem' : '2rem';
            } else if (device === 'den') {
                iconElement.className = isOn ? 'fas fa-lightbulb text-warning' : 'fas fa-lightbulb text-secondary';
                iconElement.style.filter = isOn ? 'brightness(1.2)' : 'brightness(0.7)';
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
        
        // Cập nhật trạng thái text
        const statusElement = document.getElementById(`${device}-status`);
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = `badge bg-${isOn ? 'success' : 'secondary'} p-2 fs-6`;
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
            updateDashboard(); // Cập nhật ngay
        } else {
            showToast('Lỗi', result.error || 'Có lỗi xảy ra', 'danger');
        }
    } catch (error) {
        console.error('Lỗi điều khiển:', error);
        showToast('Lỗi', 'Không thể kết nối đến server', 'danger');
    }
}

function updateChartVisibility() {
    const chartType = document.getElementById('chartToggle')?.value || 'line';
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
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = now.toLocaleTimeString('vi-VN');
        timeElement.classList.toggle('text-primary');
    }
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
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', function() {
        container.remove();
    });
}

// Hiệu ứng cho sensor cards
document.querySelectorAll('.sensor-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-5px)';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
    });
});
