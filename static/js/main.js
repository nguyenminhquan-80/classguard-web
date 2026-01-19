// CLASSGUARD - Main JavaScript (Final Fix)
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing CLASSGUARD system...');
    
    // Đặt kích thước cố định cho chart containers trước
    fixChartContainers();
    
    // Khởi tạo biểu đồ
    setTimeout(initCharts, 100);
    
    // Khởi tạo event listeners
    initEventListeners();
    
    // Cập nhật dữ liệu ngay lần đầu
    setTimeout(updateDashboard, 500);
    
    // Cập nhật mỗi 5 giây
    setInterval(updateDashboard, 5000);
    
    // Cập nhật thời gian
    setInterval(updateRealTime, 1000);
    
    console.log('✅ CLASSGUARD initialized successfully');
});

// Biến toàn cục
let lineChart = null;
let barChart = null;
let isAutoMode = true;

function fixChartContainers() {
    console.log('📐 Fixing chart containers...');
    
    // Đặt kích thước cố định tuyệt đối
    const lineContainer = document.getElementById('lineChartContainer');
    const barContainer = document.getElementById('barChartContainer');
    
    if (lineContainer) {
        lineContainer.style.height = '280px';
        lineContainer.style.minHeight = '280px';
        lineContainer.style.maxHeight = '280px';
        lineContainer.style.position = 'relative';
        lineContainer.style.overflow = 'hidden';
    }
    
    if (barContainer) {
        barContainer.style.height = '280px';
        barContainer.style.minHeight = '280px';
        barContainer.style.maxHeight = '280px';
        barContainer.style.position = 'relative';
        barContainer.style.overflow = 'hidden';
        barContainer.style.display = 'none'; // Ẩn ban đầu
    }
    
    // Đặt kích thước cho canvas
    setTimeout(() => {
        const canvases = document.querySelectorAll('#lineChart, #barChart');
        canvases.forEach(canvas => {
            if (canvas) {
                canvas.style.width = '100% !important';
                canvas.style.height = '280px !important';
                canvas.style.maxHeight = '280px !important';
            }
        });
    }, 200);
}

function initCharts() {
    console.log('📊 Initializing optimized charts with 5 lines...');
    
    const ctxLine = document.getElementById('lineChart');
    const ctxBar = document.getElementById('barChart');
    
    // Destroy existing charts if any
    if (lineChart) lineChart.destroy();
    if (barChart) barChart.destroy();
    
    if (ctxLine) {
        // Đặt kích thước canvas
        ctxLine.style.width = '100%';
        ctxLine.style.height = '320px';
        
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
                        fill: false,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        yAxisID: 'y1'
                    },
                    {
                        label: '💧 Độ ẩm',
                        data: [],
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        tension: 0.3,
                        fill: false,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        yAxisID: 'y1'
                    },
                    {
                        label: '☀️ Ánh sáng',
                        data: [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        tension: 0.3,
                        fill: false,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        yAxisID: 'y2'
                    },
                    {
                        label: '💨 Chất lượng KK',
                        data: [],
                        borderColor: '#198754',
                        backgroundColor: 'rgba(25, 135, 84, 0.1)',
                        tension: 0.3,
                        fill: false,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        yAxisID: 'y2'
                    },
                    {
                        label: '🔊 Độ ồn',
                        data: [],
                        borderColor: '#6f42c1',
                        backgroundColor: 'rgba(111, 66, 193, 0.1)',
                        tension: 0.3,
                        fill: false,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        yAxisID: 'y2'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false, // Ẩn legend vì đã có custom
                        position: 'top',
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
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Nhiệt độ (°C) & Độ ẩm (%)',
                            color: '#666'
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        },
                        ticks: {
                            font: {
                                size: 10
                            },
                            padding: 5,
                        }
                    },
                    y2: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Ánh sáng, KK, Ồn',
                            color: '#666'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                        ticks: {
                            font: {
                                size: 10
                            },
                            padding: 5,
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
        console.log('✅ Line chart with 5 lines initialized');
    }
    
    if (ctxBar) {
        // Đặt kích thước canvas
        ctxBar.style.width = '100%';
        ctxBar.style.height = '320px';
        
        barChart = new Chart(ctxBar.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['🌡️ Nhiệt độ', '💧 Độ ẩm', '☀️ Ánh sáng', '💨 Chất lượng KK', '🔊 Độ ồn'],
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
                                size: 12,
                                weight: 'bold'
                            }
                        }
                    }
                }
            }
        });
        console.log('✅ Bar chart initialized');
    }
}

function initEventListeners() {
    console.log('🔄 Setting up event listeners...');
    
    // Nút điều khiển thiết bị - THÊM XỬ LÝ ĐẶC BIỆT CHO CỬA
    document.querySelectorAll('.control-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const device = this.dataset.device;
            const action = this.dataset.action;
            console.log(`🎮 Control clicked: ${device} -> ${action}`);
            
            if (device && action) {
                // Nếu là cửa, thêm hiệu ứng ngay lập tức
                if (device === 'cua_so') {
                    const iconElement = document.getElementById('cua_so-icon');
                    const statusElement = document.getElementById('cua_so-status');
                    
                    if (action === 'MỞ') {
                        // Cập nhật ngay icon
                        iconElement.className = 'fas fa-door-open text-success fs-4 pulse';
                        statusElement.textContent = 'MỞ';
                        statusElement.style.color = '#28a745';
                    } else {
                        // Cập nhật ngay icon
                        iconElement.className = 'fas fa-door-closed text-danger fs-4';
                        statusElement.textContent = 'ĐÓNG';
                        statusElement.style.color = '#dc3545';
                    }
                }
                
                controlDevice(device, action);
            }
        });
    });
    
    // ... phần còn lại giữ nguyên
}   
    // Chuyển đổi biểu đồ
    const chartToggle = document.getElementById('chartToggle');
    if (chartToggle) {
        chartToggle.addEventListener('change', function() {
            console.log('📈 Chart toggle changed:', this.checked);
            updateChartVisibility(this.checked);
        });
    }
    
    // Chế độ tự động (cả 2 toggle)
    const autoModeToggle = document.getElementById('autoModeToggle');
    const autoModeToggle2 = document.getElementById('autoModeToggle2');
    
    if (autoModeToggle) {
        autoModeToggle.addEventListener('change', function() {
            console.log('🤖 Auto mode changed:', this.checked);
            updateAutoMode(this.checked);
            if (autoModeToggle2) autoModeToggle2.checked = this.checked;
        });
    }
    
    if (autoModeToggle2) {
        autoModeToggle2.addEventListener('change', function() {
            console.log('🤖 Auto mode (2) changed:', this.checked);
            updateAutoMode(this.checked);
            if (autoModeToggle) autoModeToggle.checked = this.checked;
        });
    }
    
    console.log('✅ Event listeners set up');
}

async function updateDashboard() {
    try {
        console.log('🔄 Updating dashboard data...');
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
        }
    } catch (error) {
        console.error('❌ Error updating dashboard:', error);
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
    const sensors = data.sensors;
    
    // Biểu đồ đường (5 thông số)
    if (lineChart && history.time) {
        // Giữ tối đa 10 điểm cho gọn
        const maxPoints = 10;
        const start = Math.max(0, history.time.length - maxPoints);
        
        const displayTimes = history.time.slice(start);
        
        // Lấy dữ liệu cho 5 đường
        const datasets = [
            history.nhiet_do ? history.nhiet_do.slice(start) : [],
            history.do_am ? history.do_am.slice(start) : [],
            history.anh_sang ? history.anh_sang.slice(start) : [],
            history.chat_luong_kk ? history.chat_luong_kk.slice(start) : [],
            history.do_on ? history.do_on.slice(start) : []
        ];
        
        // Format thời gian ngắn gọn
        const formattedTimes = displayTimes.map(time => {
            const [hours, minutes] = time.split(':');
            return `${hours}:${minutes}`;
        });
        
        // Cập nhật labels
        lineChart.data.labels = formattedTimes;
        
        // Cập nhật data cho 5 đường
        datasets.forEach((data, index) => {
            if (lineChart.data.datasets[index]) {
                lineChart.data.datasets[index].data = data;
            }
        });
        
        lineChart.update('none');
    }
    
    // Biểu đồ cột (5 thông số)
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

function updateDeviceStatus(sensors) {
    const devices = ['quat', 'den', 'cua_so', 'canh_bao'];
    
    devices.forEach(device => {
        const status = sensors[device];
        const isOn = status === 'BẬT' || status === 'MỞ';
        
        // Cập nhật icon với hiệu ứng đặc biệt cho cửa sổ
        const iconElement = document.getElementById(`${device}-icon`);
        if (iconElement) {
            // Xóa tất cả class hiệu ứng cũ
            iconElement.classList.remove('fa-spin', 'fa-shake', 'fa-window-open', 'fa-window-closed', 'fa-door-open', 'fa-door-closed');
            
            if (device === 'quat') {
                iconElement.className = isOn ? 'fas fa-fan fa-spin text-success fs-4' : 'fas fa-fan text-secondary fs-4';
            } else if (device === 'den') {
                iconElement.className = isOn ? 'fas fa-lightbulb text-warning fs-4' : 'fas fa-lightbulb text-secondary fs-4';
                iconElement.style.filter = isOn ? 'brightness(1.3)' : 'brightness(0.7)';
            } else if (device === 'canh_bao') {
                iconElement.className = isOn ? 'fas fa-bell fa-shake text-danger fs-4' : 'fas fa-bell text-secondary fs-4';
            } else if (device === 'cua_so') {
                // HIỆU ỨNG CỬA - SỬA LẠI THEO YÊU CẦU
                if (isOn) {
                    // Cửa MỞ - Sử dụng icon cửa mở
                    iconElement.className = 'fas fa-door-open text-success fs-4';
                    iconElement.style.color = '#28a745'; // Màu xanh lá
                    iconElement.style.transform = 'scale(1.1)';
                    iconElement.style.transition = 'transform 0.3s ease, color 0.3s ease';
                } else {
                    // Cửa ĐÓNG - Sử dụng icon cửa đóng
                    iconElement.className = 'fas fa-door-closed text-danger fs-4';
                    iconElement.style.color = '#dc3545'; // Màu đỏ
                    iconElement.style.transform = 'scale(1)';
                    iconElement.style.transition = 'transform 0.3s ease, color 0.3s ease';
                }
            }
        }
        
        // Cập nhật nút điều khiển - QUAN TRỌNG: Thêm xử lý riêng cho cửa
        const onBtn = document.querySelector(`[data-device="${device}"][data-action="${device === 'cua_so' ? 'MỞ' : 'BẬT'}"]`);
        const offBtn = document.querySelector(`[data-device="${device}"][data-action="${device === 'cua_so' ? 'ĐÓNG' : 'TẮT'}"]`);
        
        if (onBtn && offBtn) {
            // Reset classes
            onBtn.classList.remove('btn-success', 'btn-outline-success', 'shadow', 'active');
            offBtn.classList.remove('btn-danger', 'btn-outline-danger', 'shadow', 'active');
            
            if (isOn) {
                onBtn.classList.add('btn-success', 'shadow', 'active');
                offBtn.classList.add('btn-outline-danger');
                
                // Đổi màu riêng cho cửa
                if (device === 'cua_so') {
                    onBtn.style.backgroundColor = '#28a745';
                    onBtn.style.color = 'white';
                }
            } else {
                offBtn.classList.add('btn-danger', 'shadow', 'active');
                onBtn.classList.add('btn-outline-success');
                
                // Đổi màu riêng cho cửa
                if (device === 'cua_so') {
                    offBtn.style.backgroundColor = '#dc3545';
                    offBtn.style.color = 'white';
                }
            }
        }
        
        // Cập nhật trạng thái text
        updateElement(`${device}-status`, status);
        const statusElement = document.getElementById(`${device}-status`);
        if (statusElement) {
            statusElement.className = `status-badge status-${isOn ? 'on' : 'off'}`;
            // Đổi màu text riêng cho cửa
            if (device === 'cua_so') {
                statusElement.style.color = isOn ? '#28a745' : '#dc3545';
                statusElement.style.backgroundColor = isOn ? 'rgba(40, 167, 69, 0.15)' : 'rgba(220, 53, 69, 0.15)';
            }
        }
    });
}

async function controlDevice(device, action) {
    console.log(`🎮 Sending control: ${device} -> ${action}`);
    
    // Kiểm tra chế độ tự động
    if (isAutoMode) {
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
            setTimeout(updateDashboard, 300);
        } else {
            showToast('❌ Lỗi', result.error || 'Có lỗi xảy ra', 'danger');
        }
    } catch (error) {
        console.error('❌ Control error:', error);
        showToast('❌ Lỗi', 'Không thể kết nối đến server', 'danger');
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
            
            // Cập nhật trạng thái nút điều khiển
            updateControlButtonsState(!enabled);
        } else {
            // Rollback toggle
            const toggle1 = document.getElementById('autoModeToggle');
            const toggle2 = document.getElementById('autoModeToggle2');
            if (toggle1) toggle1.checked = !enabled;
            if (toggle2) toggle2.checked = !enabled;
            showToast('❌ Lỗi', result.error || 'Không thể cập nhật chế độ tự động', 'danger');
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
    
    // Cập nhật trạng thái nút điều khiển
    updateControlButtonsState(!enabled);
}

function updateControlButtonsState(enabled) {
    const controlButtons = document.querySelectorAll('.control-btn');
    const controlNotice = document.getElementById('control-notice');
    
    controlButtons.forEach(btn => {
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
    
    // Hiển thị thông báo
    if (controlNotice) {
        if (enabled) {
            controlNotice.innerHTML = `
                <i class="fas fa-check-circle text-success me-2 fs-4"></i>
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
                    <div class="small">Hệ thống tự động điều khiển thiết bị dựa trên ngưỡng cài đặt</div>
                </div>
            `;
            controlNotice.className = 'alert alert-warning d-flex align-items-center mb-3';
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

// Thêm CSS inline cho hiệu ứng cửa sổ
const style = document.createElement('style');
style.textContent = `
    /* FIX CHART CONTAINERS - QUAN TRỌNG! */
    #lineChartContainer,
    #barChartContainer {
        height: 320px !important;
        min-height: 320px !important;
        max-height: 320px !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    #lineChart,
    #barChart {
        width: 100% !important;
        height: 320px !important;
        max-height: 320px !important;
    }
    
    /* Hiệu ứng cửa - MỚI */
    .fa-door-open {
        color: #28a745 !important;
        transform: scale(1.1) !important;
        transition: all 0.3s ease !important;
        filter: drop-shadow(0 2px 4px rgba(40, 167, 69, 0.3));
    }
    
    .fa-door-closed {
        color: #dc3545 !important;
        transform: scale(1) !important;
        transition: all 0.3s ease !important;
        filter: drop-shadow(0 2px 4px rgba(220, 53, 69, 0.3));
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
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.15); }
        100% { transform: scale(1.1); }
    }
    
    .pulse {
        animation: pulse 0.5s ease-in-out;
    }
    
    /* Legend cho biểu đồ */
    .legend-color {
        display: inline-block;
        border-radius: 3px;
    }
    
    /* Responsive cho mobile */
    @media (max-width: 768px) {
        #lineChartContainer,
        #barChartContainer {
            height: 280px !important;
            min-height: 280px !important;
            max-height: 280px !important;
        }
        
        #lineChart,
        #barChart {
            height: 280px !important;
            max-height: 280px !important;
        }
        
        #lineChartLegend {
            font-size: 0.8rem;
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
`;
document.head.appendChild(style);

// Force resize charts on window resize
window.addEventListener('resize', function() {
    if (lineChart) lineChart.resize();
    if (barChart) barChart.resize();
});

// Initial resize
setTimeout(() => {
    if (lineChart) lineChart.resize();
    if (barChart) barChart.resize();
}, 1000);


