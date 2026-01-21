// CLASSGUARD - Main JavaScript với đồng bộ 2 chiều
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing CLASSGUARD system...');
    
    // Khởi tạo
    initCharts();
    initEventListeners();
    
    // Cập nhật lần đầu
    updateDashboard();
    
    // Cập nhật định kỳ: 1.5 giây cho mượt
    setInterval(updateDashboard, 1500);
    setInterval(updateRealTime, 1000);
    
    // Kiểm tra ESP32 mỗi 3 giây
    setInterval(checkESP32Status, 3000);
    
    console.log('✅ CLASSGUARD initialized successfully');
});

// Biến toàn cục
let lineChart = null;
let barChart = null;
let isAutoMode = false;
let esp32Connected = false;

// Khởi tạo biểu đồ
function initCharts() {
    const ctxLine = document.getElementById('lineChart');
    const ctxBar = document.getElementById('barChart');
    
    if (ctxLine) {
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
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 3
                    },
                    {
                        label: 'Độ ẩm (%)',
                        data: [],
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 3
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
                            usePointStyle: true
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
                labels: ['Nhiệt độ', 'Độ ẩm', 'Ánh sáng', 'KK', 'Độ ồn'],
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
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

function initEventListeners() {
    console.log('🔄 Setting up event listeners...');
    
    // Nút điều khiển thiết bị
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const device = this.dataset.device;
            const action = this.dataset.action;
            
            console.log(`🎮 Control clicked: ${device} -> ${action}`);
            
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
    
    // Chế độ tự động
    const autoModeToggle = document.getElementById('autoModeToggle');
    const autoModeToggle2 = document.getElementById('autoModeToggle2');
    
    if (autoModeToggle) {
        autoModeToggle.addEventListener('change', function() {
            updateAutoMode(this.checked);
            if (autoModeToggle2) autoModeToggle2.checked = this.checked;
        });
    }
    
    if (autoModeToggle2) {
        autoModeToggle2.addEventListener('change', function() {
            updateAutoMode(this.checked);
            if (autoModeToggle) autoModeToggle.checked = this.checked;
        });
    }
    
    console.log('✅ Event listeners set up');
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
        console.error('❌ Error updating dashboard:', error);
    }
}

async function checkESP32Status() {
    try {
        const response = await fetch('/api/esp32/status');
        const status = await response.json();
        
        esp32Connected = status.connected || false;
        updateESP32StatusUI(esp32Connected, status.last_update);
        
        if (!esp32Connected) {
            // Nếu mất kết nối, hiển thị cảnh báo nhẹ
            const esp32Status = document.getElementById('esp32-status');
            if (esp32Status) {
                esp32Status.innerHTML = `
                    <i class="fas fa-wifi-slash text-danger"></i>
                    <span class="ms-2">Mất kết nối ESP32</span>
                `;
            }
        }
    } catch (error) {
        console.error('❌ Error checking ESP32:', error);
    }
}

function updateESP32StatusUI(connected, lastUpdate) {
    const esp32Status = document.getElementById('esp32-status');
    const footer = document.querySelector('.dashboard-footer');
    
    if (esp32Status) {
        if (connected) {
            esp32Status.innerHTML = `
                <i class="fas fa-wifi text-success"></i>
                <span class="ms-2">ESP32: Đã kết nối</span>
                <small class="ms-2 text-muted">${lastUpdate || ''}</small>
            `;
        } else {
            esp32Status.innerHTML = `
                <i class="fas fa-wifi-slash text-danger"></i>
                <span class="ms-2">ESP32: Mất kết nối</span>
            `;
        }
    }
    
    // Cập nhật footer
    if (footer) {
        const statusText = connected ? '✅ ESP32: Đang kết nối' : '⚠️ ESP32: Mất kết nối';
        const existingStatus = footer.querySelector('.esp32-connection-status');
        
        if (existingStatus) {
            existingStatus.textContent = statusText;
        } else {
            const statusDiv = document.createElement('div');
            statusDiv.className = 'esp32-connection-status small mt-2';
            statusDiv.innerHTML = `<i class="fas fa-microchip"></i> ${statusText}`;
            footer.appendChild(statusDiv);
        }
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
    
    // Loại bỏ các lớp border cũ và thêm lớp mới
    element.classList.remove('border-success', 'border-warning', 'border-danger');
    element.classList.add(colorClass);
}

function updateCharts(data) {
    if (!data.history) return;
    
    const history = data.history;
    
    // Biểu đồ đường
    if (lineChart && history.time && history.nhiet_do) {
        const maxPoints = 8; // Hiển thị 8 điểm
        const start = Math.max(0, history.time.length - maxPoints);
        
        const displayTimes = history.time.slice(start).map(time => {
            const [hours, minutes, seconds] = time.split(':');
            return `${hours}:${minutes}`;
        });
        
        lineChart.data.labels = displayTimes;
        lineChart.data.datasets[0].data = history.nhiet_do.slice(start);
        lineChart.data.datasets[1].data = history.do_am.slice(start);
        lineChart.update('none');
    }
    
    // Biểu đồ cột
    if (barChart) {
        barChart.data.datasets[0].data = [
            data.sensors.nhiet_do,
            data.sensors.do_am,
            data.sensors.anh_sang,
            data.sensors.chat_luong_kk,
            data.sensors.do_on
        ];
        barChart.update('none');
    }
}

function updateEvaluation(evaluation) {
    if (!evaluation) return;
    
    // Đánh giá tổng thể
    updateElement('overall-evaluation', evaluation.overall);
    
    // Điểm số
    updateElement('score-value', `${evaluation.total_score}/10`);
    const scoreElement = document.getElementById('score-value');
    if (scoreElement) {
        scoreElement.className = `overall-score score-${evaluation.overall_class}`;
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
    
    // Tiết học
    updateElement('class-eval', evaluation.class_eval);
    
    // Đánh giá chi tiết
    const detailsElement = document.getElementById('evaluation-details');
    if (detailsElement && evaluation.evaluations) {
        let html = '';
        evaluation.evaluations.forEach(item => {
            html += `
                <div class="eval-item">
                    <span class="eval-label">${item[0]}</span>
                    <span class="eval-value bg-${item[2]} text-white">${item[1]}</span>
                </div>
            `;
        });
        detailsElement.innerHTML = html;
    }
}

function updateDeviceStatus(sensors) {
    const devices = ['quat', 'den', 'cua_so', 'canh_bao'];
    
    devices.forEach(device => {
        const status = sensors[device];
        const isOn = status === 'BẬT' || status === 'MỞ';
        
        // Cập nhật nút điều khiển
        const onBtn = document.querySelector(`[data-device="${device}"][data-action="${device === 'cua_so' ? 'MỞ' : 'BẬT'}"]`);
        const offBtn = document.querySelector(`[data-device="${device}"][data-action="${device === 'cua_so' ? 'ĐÓNG' : 'TẮT'}"]`);
        
        if (onBtn && offBtn) {
            onBtn.classList.remove('active');
            offBtn.classList.remove('active');
            
            if (isOn) {
                onBtn.classList.add('active');
            } else {
                offBtn.classList.add('active');
            }
        }
        
        // Cập nhật trạng thái text
        updateElement(`${device}-status`, status);
        const statusElement = document.getElementById(`${device}-status`);
        if (statusElement) {
            statusElement.className = `status-badge status-${isOn ? 'on' : 'off'}`;
        }
        
        // Cập nhật icon với hiệu ứng
        updateDeviceIcon(device, isOn);
    });
}

function updateDeviceIcon(device, isOn) {
    const iconElement = document.getElementById(`${device}-icon`);
    if (!iconElement) return;
    
    // Xóa tất cả class hiệu ứng cũ
    iconElement.classList.remove('fa-spin', 'fa-shake', 'text-success', 'text-danger', 'text-warning');
    
    if (device === 'quat') {
        iconElement.className = isOn ? 'fas fa-fan fa-spin text-success fs-4' : 'fas fa-fan text-secondary fs-4';
    } else if (device === 'den') {
        iconElement.className = isOn ? 'fas fa-lightbulb text-warning fs-4' : 'fas fa-lightbulb text-secondary fs-4';
    } else if (device === 'canh_bao') {
        iconElement.className = isOn ? 'fas fa-bell fa-shake text-danger fs-4' : 'fas fa-bell text-secondary fs-4';
    } else if (device === 'cua_so') {
        if (isOn) {
            iconElement.className = 'fas fa-door-open text-success fs-4';
            iconElement.style.transform = 'scale(1.1)';
        } else {
            iconElement.className = 'fas fa-door-closed text-danger fs-4';
            iconElement.style.transform = 'scale(1)';
        }
    }
}

async function controlDevice(device, action) {
    console.log(`🎮 Sending control: ${device} -> ${action}`);
    
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
            showToast('✅ Thành công', result.message, 'success');
            
            // Cập nhật ngay lập tức (optimistic update)
            updateDeviceStatusLocally(device, action === 'BẬT' || action === 'MỞ');
            
            // Đồng bộ lại sau 500ms
            setTimeout(updateDashboard, 500);
        } else {
            showToast('❌ Lỗi', result.error || 'Có lỗi xảy ra', 'danger');
        }
    } catch (error) {
        console.error('❌ Control error:', error);
        showToast('❌ Lỗi', 'Không thể kết nối đến server', 'danger');
    }
}

function updateDeviceStatusLocally(device, isOn) {
    const statusMap = {
        'quat': { on: 'BẬT', off: 'TẮT' },
        'den': { on: 'BẬT', off: 'TẮT' },
        'cua_so': { on: 'MỞ', off: 'ĐÓNG' },
        'canh_bao': { on: 'BẬT', off: 'TẮT' }
    };
    
    if (statusMap[device]) {
        const status = isOn ? statusMap[device].on : statusMap[device].off;
        
        // Cập nhật nút
        const onBtn = document.querySelector(`[data-device="${device}"][data-action="${device === 'cua_so' ? 'MỞ' : 'BẬT'}"]`);
        const offBtn = document.querySelector(`[data-device="${device}"][data-action="${device === 'cua_so' ? 'ĐÓNG' : 'TẮT'}"]`);
        
        if (onBtn && offBtn) {
            onBtn.classList.remove('active');
            offBtn.classList.remove('active');
            
            if (isOn) {
                onBtn.classList.add('active');
            } else {
                offBtn.classList.add('active');
            }
        }
        
        // Cập nhật trạng thái text
        updateElement(`${device}-status`, status);
    }
}

async function updateAutoMode(enabled) {
    console.log(`🤖 Updating auto mode to: ${enabled}`);
    
    try {
        const response = await fetch('/update_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                auto_mode: enabled
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            isAutoMode = enabled;
            updateAutoModeUI(enabled);
            showToast('✅ Thành công', `Chế độ tự động đã ${enabled ? 'bật' : 'tắt'}`, 'success');
        } else {
            // Rollback toggle
            const toggle1 = document.getElementById('autoModeToggle');
            const toggle2 = document.getElementById('autoModeToggle2');
            if (toggle1) toggle1.checked = !enabled;
            if (toggle2) toggle2.checked = !enabled;
            showToast('❌ Lỗi', result.error || 'Không thể cập nhật', 'danger');
        }
    } catch (error) {
        console.error('❌ Auto mode update error:', error);
        const toggle1 = document.getElementById('autoModeToggle');
        const toggle2 = document.getElementById('autoModeToggle2');
        if (toggle1) toggle1.checked = !enabled;
        if (toggle2) toggle2.checked = !enabled;
        showToast('❌ Lỗi', 'Không thể kết nối đến server', 'danger');
    }
}

function updateAutoModeUI(enabled) {
    const statusElement = document.getElementById('auto-mode-status');
    
    if (statusElement) {
        statusElement.textContent = enabled ? 'ĐANG BẬT' : 'ĐANG TẮT';
        statusElement.className = `badge ${enabled ? 'bg-success' : 'bg-secondary'} p-2`;
    }
    
    // Cập nhật thông báo
    const controlNotice = document.getElementById('control-notice');
    if (controlNotice) {
        if (enabled) {
            controlNotice.innerHTML = `
                <i class="fas fa-robot text-warning me-2 fs-4"></i>
                <div>
                    <strong>Chế độ tự động đang bật</strong>
                    <div class="small">Hệ thống tự động điều chỉnh thiết bị dựa trên ngưỡng cài đặt</div>
                </div>
            `;
            controlNotice.className = 'alert alert-warning d-flex align-items-center mb-3';
        } else {
            controlNotice.innerHTML = `
                <i class="fas fa-hand-point-up text-success me-2 fs-4"></i>
                <div>
                    <strong>Chế độ thủ công đang bật</strong>
                    <div class="small">Bạn có thể điều khiển thiết bị thủ công</div>
                </div>
            `;
            controlNotice.className = 'alert alert-success d-flex align-items-center mb-3';
        }
    }
}

function updateChartVisibility(isBarChart) {
    const lineContainer = document.getElementById('lineChartContainer');
    const barContainer = document.getElementById('barChartContainer');
    const chartLabel = document.getElementById('chartLabel');
    
    if (lineContainer && barContainer && chartLabel) {
        if (isBarChart) {
            lineContainer.style.display = 'none';
            barContainer.style.display = 'block';
            chartLabel.textContent = 'Biểu đồ cột';
        } else {
            lineContainer.style.display = 'block';
            barContainer.style.display = 'none';
            chartLabel.textContent = 'Biểu đồ đường';
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
                    <strong>${title}</strong><br>
                    <small>${message}</small>
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
    const toast = new bootstrap.Toast(toastElement, {
        delay: 3000
    });
    toast.show();
    
    // Xóa sau khi ẩn
    toastElement.addEventListener('hidden.bs.toast', function() {
        container.remove();
    });
}

// Thêm CSS cho ESP32 status
const style = document.createElement('style');
style.textContent = `
    #esp32-status {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
        background: rgba(255, 255, 255, 0.9);
        padding: 8px 15px;
        border-radius: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        font-size: 0.9rem;
        display: flex;
        align-items: center;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
`;
document.head.appendChild(style);
