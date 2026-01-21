// CLASSGUARD - Main JavaScript (Phiên bản 4.0)
// Đồng bộ hoàn toàn với Dashboard và ESP32

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Khởi tạo CLASSGUARD hệ thống...');
    
    // ========== BIẾN TOÀN CỤC ==========
    window.classguard = {
        isAutoMode: true,
        lineChart: null,
        barChart: null,
        lastUpdateTime: Date.now(),
        syncInterval: null,
        updateInterval: null,
        chartsInitialized: false,
        esp32Connected: false
        isUpdatingControls: false
    };
    
    // Khởi tạo biểu đồ
    setTimeout(initCharts, 100);
    
    // Khởi tạo event listeners
    initEventListeners();
    
    // Đồng bộ dữ liệu ngay lần đầu
    setTimeout(updateDashboard, 500);
    
    // Bắt đầu đồng bộ
    startSync();
    
    // Cập nhật thời gian
    setInterval(updateRealTime, 1000);
    
    console.log('✅ CLASSGUARD đã khởi tạo thành công');
});

// ========== KHỞI TẠO BIỂU ĐỒ ==========
function initCharts() {
    console.log('📊 Đang khởi tạo biểu đồ...');
    
    const ctxLine = document.getElementById('lineChart');
    const ctxBar = document.getElementById('barChart');
    
    // Destroy existing charts if any
    if (window.classguard.lineChart) {
        window.classguard.lineChart.destroy();
    }
    if (window.classguard.barChart) {
        window.classguard.barChart.destroy();
    }
    
    // Đặt kích thước canvas
    if (ctxLine) {
        ctxLine.style.width = '100%';
        ctxLine.style.height = '300px';
        
        window.classguard.lineChart = new Chart(ctxLine.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '🌡️ Nhiệt độ (°C)',
                        data: [],
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        tension: 0.3,
                        fill: true,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5
                    },
                    {
                        label: '💧 Độ ẩm (%)',
                        data: [],
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        tension: 0.3,
                        fill: true,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5
                    },
                    {
                        label: '☀️ Ánh sáng (lux)',
                        data: [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        tension: 0.3,
                        fill: true,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5
                    },
                    {
                        label: '💨 Chất lượng KK (PPM)',
                        data: [],
                        borderColor: '#198754',
                        backgroundColor: 'rgba(25, 135, 84, 0.1)',
                        tension: 0.3,
                        fill: true,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5
                    },
                    {
                        label: '🔊 Độ ồn (dB)',
                        data: [],
                        borderColor: '#6f42c1',
                        backgroundColor: 'rgba(111, 66, 193, 0.1)',
                        tension: 0.3,
                        fill: true,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5
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
                            font: {
                                size: 11
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.7)',
                        padding: 10,
                        cornerRadius: 6
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
                                size: 10
                            },
                            padding: 5,
                            callback: function(value) {
                                return value.toFixed(1);
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        },
                        ticks: {
                            font: {
                                size: 10
                            },
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 6
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
        console.log('✅ Biểu đồ đường đã khởi tạo');
    }
    
    if (ctxBar) {
        ctxBar.style.width = '100%';
        ctxBar.style.height = '300px';
        
        window.classguard.barChart = new Chart(ctxBar.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['🌡️', '💧', '☀️', '💨', '🔊'],
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
                    borderRadius: 4,
                    borderSkipped: false,
                    categoryPercentage: 0.6,
                    barPercentage: 0.8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const labels = ['Nhiệt độ', 'Độ ẩm', 'Ánh sáng', 'Chất lượng KK', 'Độ ồn'];
                                const units = ['°C', '%', 'lux', 'PPM', 'dB'];
                                const index = context.dataIndex;
                                let value = context.parsed.y;
                                
                                if (index === 0 || index === 1) {
                                    value = value.toFixed(1);
                                } else {
                                    value = Math.round(value);
                                }
                                
                                return `${labels[index]}: ${value} ${units[index]}`;
                            }
                        }
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
                                size: 10
                            },
                            padding: 5
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        }
                    }
                }
            }
        });
        console.log('✅ Biểu đồ cột đã khởi tạo');
    }
    
    window.classguard.chartsInitialized = true;
}

// ========== KHỞI TẠO SỰ KIỆN ==========
function initEventListeners() {
    console.log('🔄 Đang thiết lập sự kiện...');
    
    // Nút điều khiển thiết bị
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const device = this.dataset.device;
            const action = this.dataset.action;
            console.log(`🎮 Nhấn điều khiển: ${device} -> ${action}`);
            
            if (device && action) {
                controlDevice(device, action);
            }
        });
    });
    
    // Chuyển đổi biểu đồ
    const chartToggle = document.getElementById('chartToggle');
    if (chartToggle) {
        chartToggle.addEventListener('change', function() {
            console.log('📈 Chuyển đổi biểu đồ:', this.checked);
            updateChartVisibility(this.checked);
        });
    }
    
    // Chế độ tự động (cả 2 toggle)
    const autoModeToggle = document.getElementById('autoModeToggle');
    const autoModeToggle2 = document.getElementById('autoModeToggle2');
    
    if (autoModeToggle) {
        autoModeToggle.addEventListener('change', function() {
            console.log('🤖 Thay đổi chế độ tự động:', this.checked);
            updateAutoMode(this.checked);
            if (autoModeToggle2) autoModeToggle2.checked = this.checked;
        });
    }
    
    if (autoModeToggle2) {
        autoModeToggle2.addEventListener('change', function() {
            console.log('🤖 Thay đổi chế độ tự động (2):', this.checked);
            updateAutoMode(this.checked);
            if (autoModeToggle) autoModeToggle.checked = this.checked;
        });
    }
    
    // Thêm hiệu ứng hover cho sensor cards
    document.querySelectorAll('.sensor-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
            this.style.boxShadow = '0 15px 30px rgba(0, 0, 0, 0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.12)';
        });
    });
    
    console.log('✅ Sự kiện đã thiết lập');
}

// ========== BẮT ĐẦU ĐỒNG BỘ ==========
function startSync() {
    // Dừng interval cũ nếu có
    if (window.classguard.syncInterval) {
        clearInterval(window.classguard.syncInterval);
    }
    if (window.classguard.updateInterval) {
        clearInterval(window.classguard.updateInterval);
    }
    
    // Đồng bộ dữ liệu nhanh (800ms)
    window.classguard.syncInterval = setInterval(syncDashboard, 800);
    
    // Cập nhật dashboard đầy đủ (2 giây)
    window.classguard.updateInterval = setInterval(updateDashboard, 2000);
    
    console.log('🔄 Đã bắt đầu đồng bộ dữ liệu');
}

// ========== ĐỒNG BỘ DASHBOARD (NHANH) ==========
async function syncDashboard() {
    try {
        // NẾU ĐANG UPDATE THÌ BỎ QUA
        if (window.classguard.isUpdatingControls) {
            return;
        }
        
        const response = await fetch('/get_sensor_data');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.sensors) {
            // Cập nhật hiển thị sensor
            updateSensorDisplays(data.sensors);
            
            // Cập nhật trạng thái thiết bị
            updateDeviceStatus(data.sensors);
            
            // Cập nhật thời gian
            window.classguard.lastUpdateTime = Date.now();
            updateElement('last-update-time', data.sensors.timestamp || '--:--:--');
            
            // Cập nhật trạng thái kết nối
            if (data.cache) {
                updateConnectionStatus(data.cache);
            }
            
            // CHỈ CẬP NHẬT AUTO MODE NẾU KHÁC
            if (data.settings && data.settings.auto_mode !== window.classguard.isAutoMode) {
                console.log('🔄 Phát hiện thay đổi auto_mode từ server');
                window.classguard.isAutoMode = data.settings.auto_mode;
                updateAutoModeUI(window.classguard.isAutoMode);
                updateControlButtonsState(!window.classguard.isAutoMode);
            }
        }
    } catch (error) {
        console.error('❌ Lỗi đồng bộ:', error);
        updateConnectionStatus({ status: 'error' });
    }
}

// ========== CẬP NHẬT DASHBOARD (ĐẦY ĐỦ) ==========
async function updateDashboard() {
    try {
        const response = await fetch('/get_sensor_data');
        const data = await response.json();
        
        if (data.sensors) {
            // Cập nhật biểu đồ
            updateCharts(data);
            
            // Cập nhật đánh giá
            updateEvaluation(data.evaluation);
            
            // Cập nhật cài đặt
            if (data.settings) {
                window.classguard.isAutoMode = data.settings.auto_mode;
                updateAutoModeUI(window.classguard.isAutoMode);
                updateControlButtonsState(!window.classguard.isAutoMode);
            }
        }
    } catch (error) {
        console.error('❌ Lỗi cập nhật dashboard:', error);
    }
}

// ========== CẬP NHẬT HIỂN THỊ SENSOR ==========
function updateSensorDisplays(sensors) {
    // Cập nhật giá trị
    updateElement('temp-value', formatNumber(sensors.nhiet_do, 1));
    updateElement('hum-value', formatNumber(sensors.do_am, 1));
    updateElement('light-value', formatNumber(sensors.anh_sang, 0));
    updateElement('air-value', formatNumber(sensors.chat_luong_kk, 0));
    updateElement('noise-value', formatNumber(sensors.do_on, 0));
    
    // Cập nhật màu sắc và trạng thái
    updateSensorColor('temp', sensors.nhiet_do);
    updateSensorColor('hum', sensors.do_am);
    updateSensorColor('light', sensors.anh_sang);
    updateSensorColor('air', sensors.chat_luong_kk);
    updateSensorColor('noise', sensors.do_on);
}

function formatNumber(value, decimals) {
    if (decimals === 0) {
        return Math.round(value).toString();
    } else {
        return parseFloat(value).toFixed(decimals);
    }
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

// ========== CẬP NHẬT BIỂU ĐỒ ==========
function updateCharts(data) {
    if (!data.history) return;
    
    const history = data.history;
    const sensors = data.sensors;
    
    // Biểu đồ đường
    if (window.classguard.lineChart && history.time && history.nhiet_do) {
        // Giữ tối đa 8 điểm cho gọn
        const maxPoints = 8;
        const start = Math.max(0, history.time.length - maxPoints);
        
        const displayTimes = history.time.slice(start);
        const displayTemp = history.nhiet_do.slice(start);
        const displayHum = history.do_am.slice(start);
        const displayLight = history.anh_sang ? history.anh_sang.slice(start) : Array(displayTimes.length).fill(0);
        const displayAir = history.chat_luong_kk ? history.chat_luong_kk.slice(start) : Array(displayTimes.length).fill(0);
        const displayNoise = history.do_on ? history.do_on.slice(start) : Array(displayTimes.length).fill(0);
        
        // Format thời gian ngắn gọn
        const formattedTimes = displayTimes.map(time => {
            const [hours, minutes] = time.split(':');
            return `${hours}:${minutes}`;
        });
        
        window.classguard.lineChart.data.labels = formattedTimes;
        window.classguard.lineChart.data.datasets[0].data = displayTemp;
        window.classguard.lineChart.data.datasets[1].data = displayHum;
        window.classguard.lineChart.data.datasets[2].data = displayLight;
        window.classguard.lineChart.data.datasets[3].data = displayAir;
        window.classguard.lineChart.data.datasets[4].data = displayNoise;
        window.classguard.lineChart.update('none');
    }
    
    // Biểu đồ cột
    if (window.classguard.barChart && sensors) {
        window.classguard.barChart.data.datasets[0].data = [
            sensors.nhiet_do,
            sensors.do_am,
            sensors.anh_sang,
            sensors.chat_luong_kk,
            sensors.do_on
        ];
        window.classguard.barChart.update('none');
    }
}

// ========== CẬP NHẬT ĐÁNH GIÁ ==========
function updateEvaluation(evaluation) {
    if (!evaluation) return;
    
    // Đánh giá tổng thể
    updateElement('overall-evaluation', evaluation.overall);
    const overallElement = document.getElementById('overall-evaluation');
    if (overallElement) {
        overallElement.className = `badge bg-${evaluation.overall_class} p-2 fs-5`;
    }
    
    // Điểm số
    updateElement('score-value', `${evaluation.total_score}/10`);
    const scoreElement = document.getElementById('score-value');
    if (scoreElement) {
        // Update score circle class
        scoreElement.classList.remove('score-success', 'score-warning', 'score-danger');
        scoreElement.classList.add(`score-${evaluation.overall_class}`);
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
        adviceElement.className = `alert alert-${evaluation.overall_class} p-2`;
    }
    
    // Tiết học
    updateElement('class-eval', evaluation.class_eval);
    const classEvalElement = document.getElementById('class-eval');
    if (classEvalElement) {
        classEvalElement.className = `badge bg-${evaluation.class_color} p-2`;
    }
    
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

// ========== CẬP NHẬT TRẠNG THÁI THIẾT BỊ ==========
function updateDeviceStatus(sensors) {
    const devices = ['quat', 'den', 'cua_so', 'canh_bao'];
    
    devices.forEach(device => {
        const status = sensors[device];
        const isOn = status === 'BẬT' || status === 'MỞ';
        
        // Cập nhật icon với hiệu ứng
        const iconElement = document.getElementById(`${device}-icon`);
        if (iconElement) {
            // Xóa tất cả class hiệu ứng cũ
            iconElement.classList.remove('fa-spin', 'fa-shake', 'door-open', 'door-closed');
            
            if (device === 'quat') {
                iconElement.className = isOn ? 'fas fa-fan fa-spin text-success fs-4' : 'fas fa-fan text-secondary fs-4';
            } else if (device === 'den') {
                iconElement.className = isOn ? 'fas fa-lightbulb text-warning fs-4' : 'fas fa-lightbulb text-secondary fs-4';
                iconElement.style.filter = isOn ? 'brightness(1.3)' : 'brightness(0.7)';
            } else if (device === 'canh_bao') {
                iconElement.className = isOn ? 'fas fa-bell fa-shake text-danger fs-4' : 'fas fa-bell text-secondary fs-4';
            } else if (device === 'cua_so') {
                if (isOn) {
                    // Cửa MỞ
                    iconElement.className = 'fas fa-door-open text-success fs-4 door-open';
                    iconElement.style.color = '#28a745';
                    iconElement.style.transform = 'scale(1.1)';
                } else {
                    // Cửa ĐÓNG
                    iconElement.className = 'fas fa-door-closed text-danger fs-4 door-closed';
                    iconElement.style.color = '#dc3545';
                    iconElement.style.transform = 'scale(1)';
                }
            }
        }
        
        // Cập nhật nút điều khiển
        const onBtn = document.querySelector(`[data-device="${device}"][data-action="${device === 'cua_so' ? 'MỞ' : 'BẬT'}"]`);
        const offBtn = document.querySelector(`[data-device="${device}"][data-action="${device === 'cua_so' ? 'ĐÓNG' : 'TẮT'}"]`);
        
        if (onBtn && offBtn) {
            // Reset classes
            onBtn.classList.remove('btn-success', 'btn-outline-success', 'shadow', 'active');
            offBtn.classList.remove('btn-danger', 'btn-outline-danger', 'shadow', 'active');
            
            if (isOn) {
                onBtn.classList.add('btn-success', 'shadow', 'active');
                offBtn.classList.add('btn-outline-danger');
            } else {
                offBtn.classList.add('btn-danger', 'shadow', 'active');
                onBtn.classList.add('btn-outline-success');
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

// ========== ĐIỀU KHIỂN THIẾT BỊ ==========
async function controlDevice(device, action) {
    console.log(`🎮 Gửi điều khiển: ${device} -> ${action}`);
    
    // KIỂM TRA CHẾ ĐỘ TỰ ĐỘNG
    // Cảnh báo luôn được điều khiển
    if (device !== 'canh_bao' && window.classguard.isAutoMode) {
        showToast('⚠️ Cảnh báo', 'Hệ thống đang ở chế độ tự động. Tắt chế độ tự động để điều khiển thủ công.', 'warning');
        return;
    }
    
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
            setTimeout(syncDashboard, 300);
            
            // Gửi lệnh đến ESP32
            sendCommandToESP32(device, action);
        } else {
            showToast('❌ Lỗi', result.error || 'Có lỗi xảy ra', 'danger');
        }
    } catch (error) {
        console.error('❌ Lỗi điều khiển:', error);
        showToast('❌ Lỗi', 'Không thể kết nối đến server', 'danger');
    }
}

// ========== GỬI LỆNH ĐẾN ESP32 ==========
async function sendCommandToESP32(device, action) {
    try {
        const commandMap = {
            'quat': { 'BẬT': 'FAN_ON', 'TẮT': 'FAN_OFF' },
            'den': { 'BẬT': 'LIGHT_ON', 'TẮT': 'LIGHT_OFF' },
            'cua_so': { 'MỞ': 'WINDOW_OPEN', 'ĐÓNG': 'WINDOW_CLOSE' },
            'canh_bao': { 'BẬT': 'ALARM_ON', 'TẮT': 'ALARM_OFF' }
        };
        
        if (device in commandMap && action in commandMap[device]) {
            const command = commandMap[device][action];
            
            const response = await fetch('/api/esp32/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    device_id: 'ESP32-S3-CLASSGUARD',
                    command: command,
                    value: '1'
                })
            });
            
            const result = await response.json();
            if (result.success) {
                console.log(`✅ Đã gửi lệnh đến ESP32: ${command}`);
            } else {
                console.error(`❌ Lỗi gửi lệnh ESP32: ${result.error}`);
            }
        }
    } catch (error) {
        console.error('❌ Lỗi kết nối đến ESP32:', error);
    }
}

// ========== CẬP NHẬT CHẾ ĐỘ TỰ ĐỘNG ==========
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
            // CẬP NHẬT NGAY LẬP TỨC từ response
            window.classguard.isAutoMode = result.auto_mode || enabled;
            
            // CẬP NHẬT UI NGAY
            updateAutoModeUI(window.classguard.isAutoMode);
            updateControlButtonsState(!window.classguard.isAutoMode);
            
            // THÊM DELAY trước khi sync lại
            setTimeout(() => {
                syncDashboard();
            }, 300);
            
            showToast('✅ Thành công', `Chế độ tự động đã ${enabled ? 'bật' : 'tắt'}`, 'success');
        } else {
            // Rollback toggle
            const toggle1 = document.getElementById('autoModeToggle');
            const toggle2 = document.getElementById('autoModeToggle2');
            if (toggle1) toggle1.checked = !enabled;
            if (toggle2) toggle2.checked = !enabled;
            
            showToast('❌ Lỗi', result.error || 'Không thể cập nhật chế độ tự động', 'danger');
        }
    } catch (error) {
        console.error('❌ Lỗi cập nhật chế độ tự động:', error);
        
        // Rollback toggle
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

function updateControlButtonsState(enabled) {
    // KIỂM TRA NẾU ĐANG TRONG QUÁ TRÌNH UPDATE THÌ KHÔNG LÀM GÌ
    if (window.classguard.isUpdatingControls) {
        return;
    }
    
    const controlButtons = document.querySelectorAll('.control-btn');
    
    controlButtons.forEach(btn => {
        const device = btn.dataset.device;
        
        // CẢNH BÁO LUÔN ĐƯỢC ĐIỀU KHIỂN
        if (device === 'canh_bao') {
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        } else {
            // Các thiết bị khác phụ thuộc vào chế độ
            if (enabled) {
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
            } else {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
            }
        }
    });
    
    console.log(`🔄 Cập nhật trạng thái nút: ${enabled ? 'ENABLED' : 'DISABLED'}`);
}

// ========== CẬP NHẬT TRẠNG THÁI KẾT NỐI ==========
function updateConnectionStatus(cache) {
    if (!cache) return;
    
    const statusDot = document.querySelector('.status-dot');
    const syncStatus = document.getElementById('sync-status');
    const deviceStatus = document.getElementById('device-status');
    const connectionAlert = document.getElementById('connection-status');
    
    if (!statusDot || !syncStatus || !deviceStatus) return;
    
    if (cache.status === 'connected') {
        statusDot.className = 'status-dot status-online';
        syncStatus.textContent = 'Đang hoạt động';
        deviceStatus.textContent = 'Đang kết nối ESP32';
        connectionAlert.className = 'alert alert-info d-flex align-items-center justify-content-between mb-3';
        window.classguard.esp32Connected = true;
    } else if (cache.status === 'idle') {
        statusDot.className = 'status-dot status-idle';
        syncStatus.textContent = 'Chờ kết nối';
        deviceStatus.textContent = 'ESP32 không phản hồi';
        connectionAlert.className = 'alert alert-warning d-flex align-items-center justify-content-between mb-3';
        window.classguard.esp32Connected = false;
    } else if (cache.status === 'error') {
        statusDot.className = 'status-dot status-offline';
        syncStatus.textContent = 'Lỗi kết nối';
        deviceStatus.textContent = 'Kiểm tra kết nối';
        connectionAlert.className = 'alert alert-danger d-flex align-items-center justify-content-between mb-3';
        window.classguard.esp32Connected = false;
    } else {
        statusDot.className = 'status-dot status-offline';
        syncStatus.textContent = 'Mất kết nối';
        deviceStatus.textContent = 'Sử dụng dữ liệu demo';
        connectionAlert.className = 'alert alert-secondary d-flex align-items-center justify-content-between mb-3';
        window.classguard.esp32Connected = false;
    }
    
    // Cập nhật thời gian
    if (cache.last_update) {
        const age = Math.floor((Date.now() / 1000) - cache.last_update);
        if (age < 5) {
            syncStatus.textContent = 'Đang hoạt động (vài giây trước)';
        } else if (age < 60) {
            syncStatus.textContent = `Đang hoạt động (${age} giây trước)`;
        } else {
            const minutes = Math.floor(age / 60);
            syncStatus.textContent = `Đang hoạt động (${minutes} phút trước)`;
        }
    }
}

// ========== CHUYỂN ĐỔI BIỂU ĐỒ ==========
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

// ========== CẬP NHẬT THỜI GIAN ==========
function updateRealTime() {
    const now = new Date();
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = now.toLocaleTimeString('vi-VN');
    }
}

// ========== HIỂN THỊ THÔNG BÁO ==========
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

// ========== XỬ LÝ RESIZE WINDOW ==========
window.addEventListener('resize', function() {
    if (window.classguard.lineChart) {
        window.classguard.lineChart.resize();
    }
    if (window.classguard.barChart) {
        window.classguard.barChart.resize();
    }
});

// ========== CSS INLINE CHO HIỆU ỨNG ==========
const style = document.createElement('style');
style.textContent = `
    /* FIX CHART CONTAINERS */
    #lineChartContainer,
    #barChartContainer {
        height: 300px !important;
        min-height: 300px !important;
        max-height: 300px !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    #lineChart,
    #barChart {
        width: 100% !important;
        height: 300px !important;
        max-height: 300px !important;
    }
    
    /* Hiệu ứng cửa */
    .door-open {
        color: #28a745 !important;
        transform: scale(1.1) !important;
        transition: all 0.3s ease !important;
        animation: doorOpen 0.5s ease;
    }
    
    .door-closed {
        color: #dc3545 !important;
        transform: scale(1) !important;
        transition: all 0.3s ease !important;
        animation: doorClose 0.5s ease;
    }
    
    @keyframes doorOpen {
        0% { transform: rotateY(0deg) scale(1); }
        100% { transform: rotateY(-20deg) scale(1.1); }
    }
    
    @keyframes doorClose {
        0% { transform: rotateY(-20deg) scale(1.1); }
        100% { transform: rotateY(0deg) scale(1); }
    }
    
    /* Hiệu ứng cho các icon */
    .fa-fan.fa-spin {
        animation: fa-spin 1.5s infinite linear !important;
    }
    
    .fa-bell.fa-shake {
        animation: shake 0.5s infinite !important;
    }
    
    @keyframes shake {
        0%, 100% { transform: rotate(0deg); }
        25% { transform: rotate(-10deg); }
        75% { transform: rotate(10deg); }
    }
    
    /* Responsive cho mobile */
    @media (max-width: 768px) {
        #lineChartContainer,
        #barChartContainer {
            height: 240px !important;
            min-height: 240px !important;
            max-height: 240px !important;
        }
        
        #lineChart,
        #barChart {
            height: 240px !important;
            max-height: 240px !important;
        }
    }
    
    /* Chart toggle button */
    .form-switch .form-check-input {
        width: 50px;
        height: 26px;
        cursor: pointer;
    }
    
    .form-switch .form-check-input:checked {
        background-color: #4361ee;
        border-color: #4361ee;
    }
    
    /* Connection status animations */
    .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 5px;
    }
    
    .status-online {
        background-color: #28a745;
        animation: pulse 2s infinite;
    }
    
    .status-idle {
        background-color: #ffc107;
    }
    
    .status-offline {
        background-color: #dc3545;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
`;
document.head.appendChild(style);

// ========== CLEANUP KHI UNLOAD ==========
window.addEventListener('beforeunload', function() {
    if (window.classguard.syncInterval) {
        clearInterval(window.classguard.syncInterval);
    }
    if (window.classguard.updateInterval) {
        clearInterval(window.classguard.updateInterval);
    }
    console.log('🧹 Đã dọn dẹp intervals');
});

// ========== UTILITY FUNCTIONS ==========
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ========== KIỂM TRA KẾT NỐI ==========
async function checkConnection() {
    try {
        const response = await fetch('/api/system/info', { timeout: 3000 });
        const data = await response.json();
        return data.status === 'running';
    } catch (error) {
        return false;
    }
}

// ========== TỰ ĐỘNG KIỂM TRA KẾT NỐI ==========
setInterval(async () => {
    const isConnected = await checkConnection();
    if (!isConnected) {
        console.warn('⚠️ Mất kết nối server');
        updateConnectionStatus({ status: 'error' });
    }
}, 10000);

console.log('📁 main.js đã tải hoàn tất');

