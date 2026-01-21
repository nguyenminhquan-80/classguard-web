// CLASSGUARD - Main JavaScript với nút lệnh hoạt động
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
    
    console.log('✅ Dashboard đã sẵn sàng với nút lệnh hoạt động');
});

// Biến toàn cục
let lineChart = null;
let barChart = null;
let isAutoMode = false; // MẶC ĐỊNH TẮT để nút hoạt động
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
                        pointRadius: 3
                    },
                    {
                        label: '💧 Độ ẩm',
                        data: [],
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 3
                    },
                    {
                        label: '☀️ Ánh sáng',
                        data: [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 3
                    },
                    {
                        label: '💨 Chất lượng KK',
                        data: [],
                        borderColor: '#198754',
                        backgroundColor: 'rgba(25, 135, 84, 0.1)',
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 3
                    },
                    {
                        label: '🔊 Độ ồn',
                        data: [],
                        borderColor: '#6f42c1',
                        backgroundColor: 'rgba(111, 66, 193, 0.1)',
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
                            padding: 10,
                            usePointStyle: true,
                            font: { size: 11 },
                            boxWidth: 12
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    x: {
                        grid: { color: 'rgba(0,0,0,0.05)' }
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
                    legend: { display: false }
                }
            }
        });
    }
}

function initEventListeners() {
    console.log('🔄 Thiết lập event listeners...');
    
    // Nút điều khiển thiết bị - KHÔNG KIỂM TRA AUTO MODE Ở ĐÂY
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const device = this.dataset.device;
            const action = this.dataset.action;
            
            console.log(`🎮 Nhấn nút: ${device} -> ${action}`);
            
            // LUÔN cho gửi lệnh, kiểm tra ở server
            controlDevice(device, action);
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
        const response = await fetch('/get_sensor_data');
        const data = await response.json();
        
        if (data.sensors) {
            updateSensorDisplays(data.sensors);
            updateCharts(data);
            updateEvaluation(data.evaluation);
            updateDeviceStatus(data.sensors);
            
            // QUAN TRỌNG: Cập nhật isAutoMode từ server
            if (data.settings) {
                isAutoMode = Boolean(data.settings.auto_mode);
                console.log(`🤖 Chế độ tự động: ${isAutoMode ? 'BẬT' : 'TẮT'}`);
                updateAutoModeUI(isAutoMode);
                
                // Cập nhật trạng thái nút
                updateControlButtonsState(!isAutoMode);
            }
            
            // Cập nhật trạng thái ESP32
            esp32Connected = data.esp32_connected || false;
            updateESP32StatusUI(esp32Connected, data.esp32_last_update);
        }
    } catch (error) {
        console.error('❌ Lỗi cập nhật dashboard:', error);
    }
}

// HÀM MỚI: Cập nhật trạng thái nút điều khiển
function updateControlButtonsState(enabled) {
    const controlButtons = document.querySelectorAll('.control-btn');
    const controlNotice = document.getElementById('control-notice');
    
    controlButtons.forEach(btn => {
        const device = btn.dataset.device;
        
        // CẢNH BÁO: LUÔN cho phép điều khiển
        if (device === 'canh_bao') {
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
            return;
        }
        
        // Các thiết bị khác: chỉ enable khi auto_mode = false
        if (enabled) {
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        } else {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
        }
    });
    
    // Cập nhật thông báo
    if (controlNotice) {
        if (enabled) {
            controlNotice.innerHTML = `
                <i class="fas fa-hand-point-up text-success me-2 fs-4"></i>
                <div>
                    <strong>Chế độ thủ công đang bật</strong>
                    <div class="small">Bạn có thể điều khiển thiết bị thủ công</div>
                </div>
            `;
            controlNotice.className = 'alert alert-success d-flex align-items-center mb-3';
        } else {
            controlNotice.innerHTML = `
                <i class="fas fa-robot text-warning me-2 fs-4"></i>
                <div>
                    <strong>Chế độ tự động đang bật</strong>
                    <div class="small">Hệ thống tự động điều chỉnh thiết bị. Chỉ có thể điều khiển cảnh báo.</div>
                </div>
            `;
            controlNotice.className = 'alert alert-warning d-flex align-items-center mb-3';
        }
    }
}

async function controlDevice(device, action) {
    console.log(`🎮 Gửi lệnh điều khiển: ${device} -> ${action}`);
    
    // Nếu là cảnh báo: LUÔN cho phép
    if (device === 'canh_bao') {
        await sendControlRequest(device, action);
        return;
    }
    
    // Nếu là thiết bị khác và auto mode đang BẬT
    if (isAutoMode) {
        showToast('⚠️ Cảnh báo', 'Hệ thống đang ở chế độ tự động. Tắt chế độ tự động để điều khiển thủ công.', 'warning');
        return;
    }
    
    // Thiết bị khác và auto mode TẮT
    await sendControlRequest(device, action);
}

async function sendControlRequest(device, action) {
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
            // Cập nhật ngay lập tức
            setTimeout(updateDashboard, 300);
        } else {
            showToast('❌ Lỗi', result.error || 'Có lỗi xảy ra', 'danger');
        }
    } catch (error) {
        console.error('❌ Lỗi điều khiển:', error);
        showToast('❌ Lỗi', 'Không thể kết nối đến server', 'danger');
    }
}

async function updateAutoMode(enabled) {
    console.log(`🤖 Cập nhật chế độ tự động: ${enabled}`);
    
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
            updateControlButtonsState(!enabled); // QUAN TRỌNG: Cập nhật nút
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
        console.error('❌ Lỗi cập nhật auto mode:', error);
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
}

function updateCharts(data) {
    if (!data.history) return;
    
    const history = data.history;
    const sensors = data.sensors;
    
    // Biểu đồ đường
    if (lineChart && history.time && history.nhiet_do) {
        const maxPoints = 10;
        const start = Math.max(0, history.time.length - maxPoints);
        
        const displayTimes = history.time.slice(start).map(time => {
            const [hours, minutes] = time.split(':');
            return `${hours}:${minutes}`;
        });
        
        lineChart.data.labels = displayTimes;
        
        // Cập nhật 5 dataset
        if (history.nhiet_do && history.nhiet_do.length > 0) {
            lineChart.data.datasets[0].data = history.nhiet_do.slice(start);
        }
        
        if (history.do_am && history.do_am.length > 0) {
            lineChart.data.datasets[1].data = history.do_am.slice(start);
        }
        
        if (history.anh_sang && history.anh_sang.length > 0) {
            lineChart.data.datasets[2].data = history.anh_sang.slice(start);
        }
        
        if (history.chat_luong_kk && history.chat_luong_kk.length > 0) {
            lineChart.data.datasets[3].data = history.chat_luong_kk.slice(start);
        }
        
        if (history.do_on && history.do_on.length > 0) {
            lineChart.data.datasets[4].data = history.do_on.slice(start);
        }
        
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
    });
}

function updateEvaluation(evaluation) {
    if (!evaluation) return;
    
    updateElement('overall-evaluation', evaluation.overall);
    updateElement('score-value', `${evaluation.total_score}/10`);
    updateElement('advice-text', evaluation.advice);
    updateElement('class-eval', evaluation.class_eval);
    
    const scoreElement = document.getElementById('score-value');
    if (scoreElement) {
        scoreElement.className = `overall-score score-${evaluation.overall_class}`;
    }
    
    const progressBar = document.getElementById('score-progress');
    if (progressBar) {
        progressBar.style.width = `${evaluation.percentage}%`;
        progressBar.textContent = `${evaluation.percentage}%`;
        progressBar.className = `progress-bar bg-${evaluation.overall_class}`;
    }
    
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
    
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.innerHTML = toastHtml;
    document.body.appendChild(container);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        delay: 3000
    });
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', function() {
        container.remove();
    });
}

// Kiểm tra ESP32
async function checkESP32Status() {
    try {
        const response = await fetch('/api/esp32/status');
        const status = await response.json();
        
        esp32Connected = status.connected || false;
        updateESP32StatusUI(esp32Connected, status.last_update);
    } catch (error) {
        console.error('❌ Lỗi kiểm tra ESP32:', error);
    }
}

// Thêm CSS để nút rõ ràng
const style = document.createElement('style');
style.textContent = `
    /* Nút điều khiển */
    .control-btn {
        transition: all 0.3s ease;
    }
    
    .control-btn:not(:disabled):hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .control-btn:disabled {
        opacity: 0.5 !important;
        cursor: not-allowed !important;
    }
    
    .control-btn.active {
        box-shadow: 0 0 0 3px rgba(0,0,0,0.1);
        font-weight: bold;
    }
    
    /* Nút cảnh báo luôn nổi bật */
    [data-device="canh_bao"] {
        border-width: 2px !important;
    }
    
    [data-device="canh_bao"].btn-on {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%) !important;
        border-color: #dc3545 !important;
    }
    
    [data-device="canh_bao"].btn-off {
        background: linear-gradient(135deg, #6c757d 0%, #495057 100%) !important;
        border-color: #6c757d !important;
    }
    
    /* Badge ESP32 */
    #esp32-status {
        position: fixed;
        top: 15px;
        right: 15px;
        z-index: 1000;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    }
`;
document.head.appendChild(style);
