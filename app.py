from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
from flask_socketio import SocketIO, emit
import random
from datetime import datetime, timedelta
import json
import csv
import io
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'classguard_final_v3_2024'
app.secret_key = 'classguard_final_v3_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# ========== TÀI KHOẢN ==========
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin', 'name': 'Quản trị viên'},
    'giaovien': {'password': 'giaovien123', 'role': 'teacher', 'name': 'Giáo viên'},
    'hocsinh': {'password': 'hocsinh123', 'role': 'student', 'name': 'Học sinh'},
    'xem': {'password': 'xem123', 'role': 'viewer', 'name': 'Khách xem'}
}

# ========== DỮ LIỆU THỜI GIAN THỰC ==========
sensor_data = {
    'nhiet_do': 26.5,
    'do_am': 65.0,
    'anh_sang': 450,
    'chat_luong_kk': 350,
    'do_on': 45,
    'quat': 'TẮT',
    'den': 'BẬT',
    'cua_so': 'ĐÓNG',
    'canh_bao': 'TẮT',
    'timestamp': ''
}

# Lịch sử dữ liệu cho biểu đồ
history = {
    'time': [],
    'nhiet_do': [],
    'do_am': [],
    'anh_sang': [],
    'chat_luong_kk': [],
    'do_on': []
}

# Cài đặt hệ thống
system_settings = {
    'auto_mode': True,
    'temp_min': 20,
    'temp_max': 28,
    'light_min': 300,
    'noise_max': 70,
    'air_max': 800,
    'audio_enabled': True
}

# Hàng đợi lệnh cho ESP32
command_queue = []
esp32_status = {
    'connected': False,
    'last_ping': None,
    'ip_address': None
}

# ========== QUẢN LÝ KẾT NỐI ESP32 ==========
def check_esp32_connection():
    """Kiểm tra kết nối ESP32 mỗi 5 giây"""
    while True:
        time.sleep(5)
        if esp32_status['last_ping']:
            time_diff = (datetime.now() - esp32_status['last_ping']).total_seconds()
            if time_diff > 30:  # 30 giây không ping -> mất kết nối
                if esp32_status['connected']:
                    esp32_status['connected'] = False
                    print("⚠️ ESP32 mất kết nối")
                    socketio.emit('esp32_status', {'status': 'disconnected', 'timestamp': datetime.now().isoformat()})

# Khởi động thread kiểm tra kết nối
connection_thread = threading.Thread(target=check_esp32_connection, daemon=True)
connection_thread.start()

# ========== ROUTES CHÍNH ==========
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username in USERS and USERS[username]['password'] == password:
            session['username'] = username
            session['role'] = USERS[username]['role']
            session['name'] = USERS[username]['name']
            session['login_time'] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Sai tên đăng nhập hoặc mật khẩu!")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Cập nhật dữ liệu demo
    update_demo_data()
    evaluation = evaluate_environment()
    
    return render_template('dashboard.html',
                         data=sensor_data,
                         evaluation=evaluation,
                         settings=system_settings,
                         username=session['username'],
                         name=session['name'],
                         role=session['role'],
                         login_time=session.get('login_time', ''),
                         esp32_connected=esp32_status['connected'])

# ========== API CHO ESP32 ==========
@app.route('/api/esp32/sync', methods=['POST'])
def esp32_sync():
    """API đồng bộ thời gian thực với ESP32"""
    try:
        data = request.json
        
        # Cập nhật trạng thái kết nối
        esp32_status['connected'] = True
        esp32_status['last_ping'] = datetime.now()
        esp32_status['ip_address'] = request.remote_addr
        
        print(f"✅ ESP32 connected from {request.remote_addr}")
        
        # Cập nhật dữ liệu cảm biến từ ESP32
        if 'temperature' in data:
            sensor_data['nhiet_do'] = float(data['temperature'])
        if 'humidity' in data:
            sensor_data['do_am'] = float(data['humidity'])
        if 'light' in data:
            sensor_data['anh_sang'] = float(data['light'])
        if 'air_quality' in data:
            sensor_data['chat_luong_kk'] = int(data['air_quality'])
        if 'noise' in data:
            sensor_data['do_on'] = int(data['noise'])
        
        # Cập nhật trạng thái thiết bị từ ESP32
        if 'fan' in data:
            sensor_data['quat'] = 'BẬT' if data['fan'] else 'TẮT'
        if 'light_relay' in data:
            sensor_data['den'] = 'BẬT' if data['light_relay'] else 'TẮT'
        if 'window' in data:
            sensor_data['cua_so'] = 'MỞ' if data['window'] else 'ĐÓNG'
        if 'alarm' in data:
            sensor_data['canh_bao'] = 'BẬT' if data['alarm'] else 'TẮT'
        
        # Cập nhật timestamp
        sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S")
        
        # Cập nhật lịch sử
        update_history()
        
        # Gửi thông báo đến web qua SocketIO
        evaluation = evaluate_environment()
        socketio.emit('sensor_update', {
            'sensors': sensor_data,
            'evaluation': evaluation,
            'timestamp': sensor_data['timestamp']
        })
        
        # Gửi trạng thái kết nối
        socketio.emit('esp32_status', {
            'status': 'connected',
            'timestamp': datetime.now().isoformat()
        })
        
        # Chuẩn bị phản hồi cho ESP32
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'thresholds': {
                'temp_min': system_settings['temp_min'],
                'temp_max': system_settings['temp_max'],
                'light_min': system_settings['light_min'],
                'air_max': system_settings['air_max'],
                'noise_max': system_settings['noise_max'],
                'auto_mode': system_settings['auto_mode'],
                'audio_enabled': system_settings['audio_enabled']
            },
            'commands': command_queue.copy() if command_queue else []
        }
        
        # Xóa hàng đợi sau khi gửi
        command_queue.clear()
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Lỗi đồng bộ ESP32: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/esp32/command', methods=['POST'])
def esp32_command():
    """API để web gửi lệnh đến ESP32"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    command = data.get('command')
    value = data.get('value', '')
    
    # Kiểm tra quyền
    if session['role'] not in ['admin', 'teacher']:
        return jsonify({'error': '❌ Không có quyền điều khiển!'}), 403
    
    # Kiểm tra chế độ tự động (trừ cảnh báo và âm thanh)
    if command not in ['ALARM_ON', 'ALARM_OFF', 'PLAY_AUDIO', 'CLEAR_AUDIO_QUEUE', 'STOP_AUDIO', 'SET_VOLUME']:
        if system_settings['auto_mode']:
            return jsonify({
                'error': '❌ Hệ thống đang ở chế độ tự động. Tắt chế độ tự động để điều khiển thủ công.'
            }), 403
    
    # Tạo lệnh với ID duy nhất
    command_id = int(time.time() * 1000)
    command_data = {
        'command_id': command_id,
        'command': command,
        'value': value,
        'timestamp': datetime.now().isoformat()
    }
    
    # Thêm vào hàng đợi
    command_queue.append(command_data)
    
    # Cập nhật ngay trạng thái trên web
    update_local_state(command, value)
    
    # Gửi thông báo đến web
    evaluation = evaluate_environment()
    socketio.emit('sensor_update', {
        'sensors': sensor_data,
        'evaluation': evaluation,
        'timestamp': sensor_data['timestamp']
    })
    
    # Gửi thông báo lệnh đã gửi
    socketio.emit('command_sent', {
        'command_id': command_id,
        'command': command,
        'value': value,
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({
        'success': True,
        'message': f'✅ Đã gửi lệnh {command}',
        'command_id': command_id
    })

@app.route('/api/esp32/ack', methods=['POST'])
def esp32_ack():
    """API nhận xác nhận từ ESP32"""
    try:
        data = request.json
        command_id = data.get('command_id')
        
        print(f"✅ ESP32 xác nhận đã thực thi lệnh ID: {command_id}")
        
        # Gửi thông báo đến web
        socketio.emit('command_ack', {
            'command_id': command_id,
            'status': 'executed',
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Lỗi nhận ACK: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== API CHO WEB ==========
@app.route('/get_sensor_data')
def get_sensor_data():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    update_demo_data()
    evaluation = evaluate_environment()
    
    return jsonify({
        'sensors': sensor_data,
        'evaluation': evaluation,
        'history': history,
        'settings': system_settings,
        'esp32_connected': esp32_status['connected']
    })

@app.route('/control', methods=['POST'])
def control():
    """API điều khiển cũ (giữ lại cho tương thích)"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if session['role'] not in ['admin', 'teacher']:
        return jsonify({'error': '❌ Không có quyền điều khiển!'}), 403
    
    data = request.json
    device = data.get('device')
    action = data.get('action')
    
    # Map device/action sang command ESP32
    command_map = {
        'quat_BẬT': 'FAN_ON',
        'quat_TẮT': 'FAN_OFF',
        'den_BẬT': 'LIGHT_ON',
        'den_TẮT': 'LIGHT_OFF',
        'cua_so_MỞ': 'WINDOW_OPEN',
        'cua_so_ĐÓNG': 'WINDOW_CLOSE',
        'canh_bao_BẬT': 'ALARM_ON',
        'canh_bao_TẮT': 'ALARM_OFF'
    }
    
    key = f"{device}_{action}"
    command = command_map.get(key)
    
    if not command:
        return jsonify({'error': 'Lệnh không hợp lệ'}), 400
    
    # Gửi lệnh qua API mới
    response = esp32_command_internal(command, action)
    return response

def esp32_command_internal(command, value):
    """Hàm nội bộ gửi lệnh"""
    command_id = int(time.time() * 1000)
    command_data = {
        'command_id': command_id,
        'command': command,
        'value': value,
        'timestamp': datetime.now().isoformat()
    }
    
    command_queue.append(command_data)
    update_local_state(command, value)
    
    return jsonify({
        'success': True,
        'message': f'✅ Đã gửi lệnh {command}',
        'command_id': command_id
    })

def update_local_state(command, value):
    """Cập nhật trạng thái cục bộ"""
    if command == 'FAN_ON':
        sensor_data['quat'] = 'BẬT'
    elif command == 'FAN_OFF':
        sensor_data['quat'] = 'TẮT'
    elif command == 'LIGHT_ON':
        sensor_data['den'] = 'BẬT'
    elif command == 'LIGHT_OFF':
        sensor_data['den'] = 'TẮT'
    elif command == 'WINDOW_OPEN':
        sensor_data['cua_so'] = 'MỞ'
    elif command == 'WINDOW_CLOSE':
        sensor_data['cua_so'] = 'ĐÓNG'
    elif command == 'ALARM_ON':
        sensor_data['canh_bao'] = 'BẬT'
    elif command == 'ALARM_OFF':
        sensor_data['canh_bao'] = 'TẮT'
    
    sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S")

@app.route('/update_settings', methods=['POST'])
def update_settings():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if session['role'] != 'admin':
        return jsonify({'error': 'Không có quyền!'}), 403
    
    try:
        data = request.json
        system_settings['auto_mode'] = data.get('auto_mode', system_settings['auto_mode'])
        system_settings['temp_min'] = float(data.get('temp_min', system_settings['temp_min']))
        system_settings['temp_max'] = float(data.get('temp_max', system_settings['temp_max']))
        system_settings['light_min'] = float(data.get('light_min', system_settings['light_min']))
        system_settings['noise_max'] = float(data.get('noise_max', system_settings['noise_max']))
        system_settings['air_max'] = float(data.get('air_max', system_settings['air_max']))
        system_settings['audio_enabled'] = data.get('audio_enabled', system_settings['audio_enabled'])
        
        # Gửi lệnh cập nhật chế độ tự động đến ESP32
        if 'auto_mode' in data:
            command = 'AUTO_MODE_ON' if data['auto_mode'] else 'AUTO_MODE_OFF'
            command_queue.append({
                'command_id': int(time.time() * 1000),
                'command': command,
                'value': '',
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({'success': True, 'message': '✅ Đã cập nhật cài đặt!'})
    except Exception as e:
        print(f"❌ Lỗi cập nhật cài đặt: {e}")
        return jsonify({'error': '❌ Dữ liệu không hợp lệ!'}), 400

# ========== CÁC ROUTES KHÁC ==========
@app.route('/data')
def data_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    data_list = generate_sample_data()
    
    return render_template('data.html',
                         data=data_list,
                         role=session['role'])

@app.route('/settings_page')
def settings_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['role'] != 'admin':
        return redirect(url_for('dashboard'))
    
    return render_template('settings.html',
                         settings=system_settings,
                         role=session['role'])

@app.route('/export_csv')
def export_csv():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return generate_csv_report()

# ========== HÀM PHỤ TRỢ ==========
def evaluate_environment():
    """Đánh giá môi trường theo ngưỡng chính xác"""
    evaluations = []
    scores = []
    
    # Đánh giá nhiệt độ
    temp = sensor_data['nhiet_do']
    if 18 <= temp <= 26:
        evaluations.append(('🌡️ Nhiệt độ', 'Lý tưởng', 'success'))
        scores.append(2)
    elif (16 <= temp < 18) or (26 < temp <= 30):
        evaluations.append(('🌡️ Nhiệt độ', 'Chấp nhận', 'warning'))
        scores.append(1)
    else:
        evaluations.append(('🌡️ Nhiệt độ', 'Không tốt', 'danger'))
        scores.append(0)
    
    # Đánh giá độ ẩm
    humidity = sensor_data['do_am']
    if 40 <= humidity <= 60:
        evaluations.append(('💧 Độ ẩm', 'Tốt', 'success'))
        scores.append(2)
    elif (30 <= humidity < 40) or (60 < humidity <= 70):
        evaluations.append(('💧 Độ ẩm', 'Trung bình', 'warning'))
        scores.append(1)
    else:
        evaluations.append(('💧 Độ ẩm', 'Không tốt', 'danger'))
        scores.append(0)
    
    # Đánh giá ánh sáng
    light = sensor_data['anh_sang']
    if 300 <= light <= 500:
        evaluations.append(('☀️ Ánh sáng', 'Đủ sáng', 'success'))
        scores.append(2)
    elif 200 <= light < 300:
        evaluations.append(('☀️ Ánh sáng', 'Hơi tối', 'warning'))
        scores.append(1)
    else:
        evaluations.append(('☀️ Ánh sáng', 'Thiếu sáng', 'danger'))
        scores.append(0)
    
    # Đánh giá chất lượng không khí
    air = sensor_data['chat_luong_kk']
    if air < 750:
        evaluations.append(('💨 Chất lượng KK', 'Trong lành', 'success'))
        scores.append(2)
    elif 750 <= air < 1200:
        evaluations.append(('💨 Chất lượng KK', 'Trung bình', 'warning'))
        scores.append(1)
    else:
        evaluations.append(('💨 Chất lượng KK', 'Ô nhiễm', 'danger'))
        scores.append(0)
    
    # Đánh giá độ ồn
    noise = sensor_data['do_on']
    if noise < 50:
        evaluations.append(('🔊 Độ ồn', 'Yên tĩnh', 'success'))
        scores.append(2)
    elif 50 <= noise < 70:
        evaluations.append(('🔊 Độ ồn', 'Bình thường', 'warning'))
        scores.append(1)
    else:
        evaluations.append(('🔊 Độ ồn', 'Ồn ào', 'danger'))
        scores.append(0)
    
    total_score = sum(scores)
    percentage = (total_score / 10) * 100
    
    if percentage >= 80:
        overall = 'TỐT'
        overall_class = 'success'
        advice = 'Môi trường học tập lý tưởng! Tiết học có thể diễn ra hiệu quả.'
    elif percentage >= 60:
        overall = 'KHÁ'
        overall_class = 'warning'
        advice = 'Môi trường chấp nhận được. Có một số yếu tố cần cải thiện.'
    else:
        overall = 'CẦN CẢI THIỆN'
        overall_class = 'danger'
        advice = 'Môi trường không phù hợp. Cần điều chỉnh trước khi học.'
    
    if total_score >= 8:
        class_eval = 'Tiết học lý tưởng'
        class_color = 'success'
    elif total_score >= 6:
        class_eval = 'Tiết học bình thường'
        class_color = 'warning'
    else:
        class_eval = 'Tiết học bị ảnh hưởng'
        class_color = 'danger'
    
    return {
        'total_score': total_score,
        'percentage': round(percentage, 1),
        'overall': overall,
        'overall_class': overall_class,
        'advice': advice,
        'class_eval': class_eval,
        'class_color': class_color,
        'evaluations': evaluations
    }

def update_demo_data():
    """Cập nhật dữ liệu demo khi không có ESP32"""
    if not esp32_status['connected']:
        # Thêm biến động ngẫu nhiên
        sensor_data['nhiet_do'] = round(24 + random.random() * 4, 1)
        sensor_data['do_am'] = round(50 + random.random() * 20, 1)
        sensor_data['anh_sang'] = round(200 + random.random() * 300)
        sensor_data['chat_luong_kk'] = round(200 + random.random() * 600)
        sensor_data['do_on'] = round(30 + random.random() * 50)
        sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S")
        
        # Tự động điều khiển nếu chế độ tự động bật
        if system_settings['auto_mode']:
            auto_control()
        
        # Cập nhật history
        update_history()

def auto_control():
    """Tự động điều khiển thiết bị (chỉ quạt, đèn, cửa sổ)"""
    # Nhiệt độ
    if sensor_data['nhiet_do'] > system_settings['temp_max']:
        sensor_data['quat'] = 'BẬT'
    elif sensor_data['nhiet_do'] < system_settings['temp_min']:
        sensor_data['quat'] = 'TẮT'
    
    # Ánh sáng
    if sensor_data['anh_sang'] < system_settings['light_min']:
        sensor_data['den'] = 'BẬT'
    else:
        sensor_data['den'] = 'TẮT'
    
    # Chất lượng không khí
    if sensor_data['chat_luong_kk'] > system_settings['air_max']:
        sensor_data['cua_so'] = 'MỞ'
    else:
        sensor_data['cua_so'] = 'ĐÓNG'
    
    # Độ ồn (KHÔNG tự động điều khiển cảnh báo)
    # Cảnh báo chỉ bật/tắt thủ công

def update_history():
    """Cập nhật lịch sử cho biểu đồ"""
    now = datetime.now()
    
    # Giữ tối đa 15 điểm
    if len(history['time']) >= 15:
        for key in history:
            if history[key]:
                history[key].pop(0)
    
    history['time'].append(now.strftime("%H:%M:%S"))
    history['nhiet_do'].append(sensor_data['nhiet_do'])
    history['do_am'].append(sensor_data['do_am'])
    history['anh_sang'].append(sensor_data['anh_sang'])
    history['chat_luong_kk'].append(sensor_data['chat_luong_kk'])
    history['do_on'].append(sensor_data['do_on'])

def generate_sample_data():
    """Tạo dữ liệu mẫu cho trang data"""
    data_list = []
    base_time = datetime.now()
    
    for i in range(30):
        record_time = base_time - timedelta(minutes=i*5)
        temp = round(24 + random.random() * 4, 1)
        humidity = round(55 + random.random() * 20, 1)
        light = round(250 + random.random() * 250)
        air = round(300 + random.random() * 500)
        noise = round(35 + random.random() * 40)
        
        score = 0
        if 20 <= temp <= 28: score += 1
        if 40 <= humidity <= 70: score += 1
        if light >= 300: score += 1
        if air < 400: score += 1
        if noise < 50: score += 1
        
        if score >= 4:
            eval_text = 'Tốt'
            eval_color = 'success'
        elif score >= 3:
            eval_text = 'Khá'
            eval_color = 'warning'
        else:
            eval_text = 'Cần cải thiện'
            eval_color = 'danger'
        
        data_list.append({
            'stt': i + 1,
            'thoi_gian': record_time.strftime("%H:%M"),
            'ngay': record_time.strftime("%d/%m/%Y"),
            'nhiet_do': temp,
            'do_am': humidity,
            'anh_sang': light,
            'chat_luong_kk': air,
            'do_on': noise,
            'danh_gia': eval_text,
            'danh_gia_color': eval_color
        })
    
    return data_list

def generate_csv_report():
    """Tạo báo cáo CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['CLASSGUARD - BÁO CÁO MÔI TRƯỜNG LỚP HỌC'])
    writer.writerow(['Thời gian xuất', datetime.now().strftime("%d/%m/%Y %H:%M:%S")])
    writer.writerow(['Người xuất', session.get('name', 'Unknown')])
    writer.writerow(['Vai trò', session.get('role', 'Unknown')])
    writer.writerow([])
    writer.writerow(['THÔNG SỐ CẢM BIẾN'])
    writer.writerow(['Thông số', 'Giá trị', 'Đơn vị', 'Trạng thái'])
    writer.writerow(['Nhiệt độ', f"{sensor_data['nhiet_do']:.1f}", '°C', 
                     'Tốt' if 20 <= sensor_data['nhiet_do'] <= 28 else 'Cảnh báo' if 28 < sensor_data['nhiet_do'] <= 32 else 'Nguy hiểm'])
    writer.writerow(['Độ ẩm', f"{sensor_data['do_am']:.1f}", '%',
                     'Tốt' if 40 <= sensor_data['do_am'] <= 70 else 'Cảnh báo'])
    writer.writerow(['Ánh sáng', str(sensor_data['anh_sang']), 'lux',
                     'Tốt' if sensor_data['anh_sang'] >= 300 else 'Cảnh báo' if sensor_data['anh_sang'] >= 200 else 'Thiếu sáng'])
    writer.writerow(['Chất lượng KK', str(sensor_data['chat_luong_kk']), 'PPM',
                     'Tốt' if sensor_data['chat_luong_kk'] < 400 else 'Trung bình' if sensor_data['chat_luong_kk'] < 800 else 'Ô nhiễm'])
    writer.writerow(['Độ ồn', str(sensor_data['do_on']), 'dB',
                     'Tốt' if sensor_data['do_on'] < 50 else 'Bình thường' if sensor_data['do_on'] < 70 else 'Ồn ào'])
    writer.writerow([])
    writer.writerow(['TRẠNG THÁI THIẾT BỊ'])
    writer.writerow(['Thiết bị', 'Trạng thái'])
    writer.writerow(['Quạt', sensor_data['quat']])
    writer.writerow(['Đèn', sensor_data['den']])
    writer.writerow(['Cửa sổ', sensor_data['cua_so']])
    writer.writerow(['Cảnh báo', sensor_data['canh_bao']])
    
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=classguard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

# ========== SOCKETIO EVENTS ==========
@socketio.on('connect')
def handle_connect():
    print(f'✅ Web client connected: {request.sid}')
    emit('connected', {
        'status': 'ok',
        'esp32_connected': esp32_status['connected']
    })

@socketio.on('disconnect')
def handle_disconnect():
    print(f'❌ Web client disconnected: {request.sid}')

@socketio.on('request_update')
def handle_request_update():
    """Client yêu cầu cập nhật dữ liệu"""
    evaluation = evaluate_environment()
    emit('sensor_update', {
        'sensors': sensor_data,
        'evaluation': evaluation,
        'timestamp': sensor_data['timestamp']
    })

# ========== CHẠY ỨNG DỤNG ==========
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 CLASSGUARD SYSTEM STARTING...")
    print(f"📊 Web URL: http://0.0.0.0:5000")
    print(f"📡 ESP32 Sync API: /api/esp32/sync")
    print("=" * 50)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
