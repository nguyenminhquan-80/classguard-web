# CLASSGUARD - Web Server hoàn thiện với đồng bộ tức thì
# Phiên bản: 4.0 - Đồng bộ ESP32 ↔ Web <1s

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
import random
from datetime import datetime, timedelta
import json
import csv
import io
import sqlite3
from threading import Lock
import time
import threading
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'classguard_final_v4_2024'
app.secret_key = 'classguard_final_v4_2024'
CORS(app)  # Hỗ trợ CORS cho ESP32

# ========== KHỞI TẠO DATABASE ==========
def init_db():
    """Khởi tạo database với cấu trúc mới"""
    conn = sqlite3.connect('classguard.db')
    c = conn.cursor()
    
    # Bảng users
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  role TEXT,
                  name TEXT,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Bảng sensor_history (cải tiến)
    c.execute('''CREATE TABLE IF NOT EXISTS sensor_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
                  temperature REAL NOT NULL,
                  humidity REAL NOT NULL,
                  light INTEGER NOT NULL,
                  air_quality INTEGER NOT NULL,
                  noise INTEGER NOT NULL,
                  fan_state INTEGER DEFAULT 0,
                  light_state INTEGER DEFAULT 0,
                  window_state INTEGER DEFAULT 0,
                  alarm_state INTEGER DEFAULT 0,
                  auto_mode INTEGER DEFAULT 1)''')
    
    # Bảng pending_commands (cải tiến)
    c.execute('''CREATE TABLE IF NOT EXISTS pending_commands
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  device_id TEXT NOT NULL,
                  command TEXT NOT NULL,
                  value TEXT NOT NULL,
                  created_at DATETIME DEFAULT (datetime('now', 'localtime')),
                  executed INTEGER DEFAULT 0,
                  executed_at DATETIME,
                  response TEXT)''')
    
    # Bảng system_settings
    c.execute('''CREATE TABLE IF NOT EXISTS system_settings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  setting_key TEXT UNIQUE NOT NULL,
                  setting_value TEXT NOT NULL,
                  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Thêm tài khoản mẫu nếu chưa có
    users_data = [
        ('admin', 'admin123', 'admin', 'Quản trị viên'),
        ('giaovien', 'giaovien123', 'teacher', 'Giáo viên'),
        ('hocsinh', 'hocsinh123', 'student', 'Học sinh'),
        ('xem', 'xem123', 'viewer', 'Khách xem')
    ]
    
    for user in users_data:
        try:
            c.execute("INSERT OR IGNORE INTO users (username, password, role, name) VALUES (?, ?, ?, ?)", user)
        except:
            pass
    
    # Thêm cài đặt mặc định
    default_settings = [
        ('auto_mode', '1'),
        ('temp_min', '20.0'),
        ('temp_max', '28.0'),
        ('light_min', '300.0'),
        ('air_max', '800'),
        ('noise_max', '70'),
        ('audio_enabled', '1'),
        ('sync_interval', '800'),
        ('device_id', 'ESP32-S3-CLASSGUARD')
    ]
    
    for key, value in default_settings:
        c.execute("INSERT OR IGNORE INTO system_settings (setting_key, setting_value) VALUES (?, ?)", (key, value))
    
    conn.commit()
    conn.close()

# Khởi tạo database
init_db()

# ========== BIẾN TOÀN CỤC ==========
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
    'timestamp': '',
    'device_status': 'online'
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
    'temp_min': 20.0,
    'temp_max': 28.0,
    'light_min': 300.0,
    'noise_max': 70,
    'air_max': 800,
    'audio_enabled': True,
    'sync_interval': 800,
    'device_id': 'ESP32-S3-CLASSGUARD'
}

# Cache cho ESP32
esp32_cache = {
    'last_update': time.time(),
    'data': {},
    'status': 'disconnected',
    'commands_sent': 0
}

# Lock cho thread-safe
data_lock = Lock()
cache_lock = Lock()

# Biến để theo dõi thời gian
last_history_update = 0
last_settings_load = 0

# ========== HÀM HỖ TRỢ ==========
def load_settings():
    """Tải cài đặt từ database"""
    global system_settings, last_settings_load
    
    with data_lock:
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        
        c.execute("SELECT setting_key, setting_value FROM system_settings")
        settings = c.fetchall()
        conn.close()
        
        for key, value in settings:
            if key in system_settings:
                if key in ['auto_mode', 'audio_enabled']:
                    system_settings[key] = bool(int(value))
                elif key in ['temp_min', 'temp_max', 'light_min']:
                    system_settings[key] = float(value)
                elif key in ['noise_max', 'air_max', 'sync_interval']:
                    system_settings[key] = int(value)
                else:
                    system_settings[key] = value
        
        last_settings_load = time.time()
        print(f"⚙️ Đã tải cài đặt: {system_settings}")

def save_setting(key, value):
    """Lưu cài đặt vào database"""
    try:
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        
        # Chuyển đổi giá trị
        if isinstance(value, bool):
            db_value = '1' if value else '0'
        else:
            db_value = str(value)
        
        c.execute('''INSERT OR REPLACE INTO system_settings (setting_key, setting_value, updated_at) 
                     VALUES (?, ?, datetime('now', 'localtime'))''', 
                 (key, db_value))
        conn.commit()
        conn.close()
        
        # Cập nhật biến toàn cục
        if key in system_settings:
            system_settings[key] = value
        
        print(f"💾 Đã lưu cài đặt: {key} = {value}")
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu cài đặt {key}: {e}")
        return False

def initialize_history():
    """Khởi tạo dữ liệu lịch sử từ database"""
    global history, last_history_update
    
    with data_lock:
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        
        # Lấy 15 bản ghi gần nhất
        c.execute('''SELECT timestamp, temperature, humidity, light, air_quality, noise 
                     FROM sensor_history 
                     ORDER BY timestamp DESC 
                     LIMIT 15''')
        records = c.fetchall()
        conn.close()
        
        # Xóa dữ liệu cũ
        for key in history:
            history[key] = []
        
        # Thêm dữ liệu mới (theo thứ tự thời gian tăng dần)
        for record in reversed(records):
            time_str = datetime.strptime(record[0], '%Y-%m-%d %H:%M:%S').strftime("%H:%M:%S")
            history['time'].append(time_str)
            history['nhiet_do'].append(float(record[1]))
            history['do_am'].append(float(record[2]))
            history['anh_sang'].append(int(record[3]))
            history['chat_luong_kk'].append(int(record[4]))
            history['do_on'].append(int(record[5]))
        
        last_history_update = time.time()
        print(f"📊 Đã tải {len(records)} bản ghi lịch sử")

def update_history_from_db():
    """Cập nhật history từ database"""
    global last_history_update
    
    if time.time() - last_history_update < 5:  # 5 giây
        return
    
    with data_lock:
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        c.execute('''SELECT timestamp, temperature, humidity, light, air_quality, noise 
                     FROM sensor_history 
                     ORDER BY timestamp DESC 
                     LIMIT 15''')
        records = c.fetchall()
        conn.close()
        
        # Xóa dữ liệu cũ
        for key in history:
            history[key] = []
        
        # Thêm dữ liệu mới
        for record in reversed(records):
            time_str = datetime.strptime(record[0], '%Y-%m-%d %H:%M:%S').strftime("%H:%M:%S")
            history['time'].append(time_str)
            history['nhiet_do'].append(float(record[1]))
            history['do_am'].append(float(record[2]))
            history['anh_sang'].append(int(record[3]))
            history['chat_luong_kk'].append(int(record[4]))
            history['do_on'].append(int(record[5]))
        
        last_history_update = time.time()

def save_sensor_to_db(temp, hum, light, air, noise):
    """Lưu dữ liệu cảm biến vào database"""
    try:
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        
        c.execute('''INSERT INTO sensor_history 
                     (timestamp, temperature, humidity, light, air_quality, noise,
                      fan_state, light_state, window_state, alarm_state, auto_mode)
                     VALUES (datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (temp, hum, light, air, noise,
                  int(sensor_data['quat'] == 'BẬT'),
                  int(sensor_data['den'] == 'BẬT'),
                  int(sensor_data['cua_so'] == 'MỞ'),
                  int(sensor_data['canh_bao'] == 'BẬT'),
                  int(system_settings['auto_mode'])))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu dữ liệu cảm biến: {e}")
        return False

def save_pending_command(device_id, command, value):
    """Lưu lệnh chờ vào database"""
    try:
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        
        c.execute('''INSERT INTO pending_commands (device_id, command, value) 
                     VALUES (?, ?, ?)''', 
                 (device_id, command, value))
        conn.commit()
        conn.close()
        
        with cache_lock:
            esp32_cache['commands_sent'] += 1
        
        print(f"💾 Đã lưu lệnh: {command}={value} cho {device_id}")
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu lệnh: {e}")
        return False

def get_pending_commands(device_id, limit=5):
    """Lấy lệnh chờ cho ESP32"""
    try:
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        
        c.execute('''SELECT id, command, value 
                     FROM pending_commands 
                     WHERE device_id = ? AND executed = 0 
                     ORDER BY created_at ASC 
                     LIMIT ?''', (device_id, limit))
        commands = c.fetchall()
        conn.close()
        
        result = []
        for cmd_id, cmd, val in commands:
            result.append({
                'command_id': cmd_id,
                'command': cmd,
                'value': val
            })
        return result
    except Exception as e:
        print(f"❌ Lỗi lấy lệnh chờ: {e}")
        return []

def mark_command_executed(command_id):
    """Đánh dấu lệnh đã được thực thi"""
    try:
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        
        c.execute('''UPDATE pending_commands 
                     SET executed = 1, executed_at = datetime('now', 'localtime')
                     WHERE id = ?''', (command_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Lỗi đánh dấu lệnh: {e}")
        return False

def update_demo_data():
    """Cập nhật dữ liệu demo khi không có ESP32"""
    if sensor_data['device_status'] == 'online':
        return
    
    with data_lock:
        # Tạo dữ liệu ngẫu nhiên trong ngưỡng hợp lý
        sensor_data['nhiet_do'] = round(22 + random.random() * 6, 1)  # 22-28°C
        sensor_data['do_am'] = round(45 + random.random() * 25, 1)    # 45-70%
        sensor_data['anh_sang'] = round(250 + random.random() * 250)  # 250-500 lux
        sensor_data['chat_luong_kk'] = round(300 + random.random() * 500)  # 300-800 PPM
        sensor_data['do_on'] = round(40 + random.random() * 30)      # 40-70 dB
        sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S")
        
        # Lưu vào database
        save_sensor_to_db(
            sensor_data['nhiet_do'],
            sensor_data['do_am'],
            sensor_data['anh_sang'],
            sensor_data['chat_luong_kk'],
            sensor_data['do_on']
        )
        
        # Cập nhật lịch sử
        update_history_from_db()

def auto_control_logic(temp, light, air):
    """Logic điều khiển tự động - KHÔNG BAO GỒM CẢNH BÁO"""
    if not system_settings['auto_mode']:
        return
    
    with data_lock:
        # NHIỆT ĐỘ - điều khiển quạt
        if temp > system_settings['temp_max']:
            if sensor_data['quat'] != 'BẬT':
                sensor_data['quat'] = 'BẬT'
                save_pending_command('ESP32-S3-CLASSGUARD', 'FAN_ON', '1')
                print("🤖 Tự động BẬT quạt (nhiệt độ cao)")
        elif temp < system_settings['temp_min']:
            if sensor_data['quat'] != 'TẮT':
                sensor_data['quat'] = 'TẮT'
                save_pending_command('ESP32-S3-CLASSGUARD', 'FAN_OFF', '0')
                print("🤖 Tự động TẮT quạt (nhiệt độ thấp)")
        
        # ÁNH SÁNG - điều khiển đèn
        if light < system_settings['light_min']:
            if sensor_data['den'] != 'BẬT':
                sensor_data['den'] = 'BẬT'
                save_pending_command('ESP32-S3-CLASSGUARD', 'LIGHT_ON', '1')
                print("🤖 Tự động BẬT đèn (thiếu sáng)")
        elif light >= (system_settings['light_min'] + 100):
            if sensor_data['den'] != 'TẮT':
                sensor_data['den'] = 'TẮT'
                save_pending_command('ESP32-S3-CLASSGUARD', 'LIGHT_OFF', '0')
                print("🤖 Tự động TẮT đèn (đủ sáng)")
        
        # CHẤT LƯỢNG KHÔNG KHÍ - điều khiển cửa sổ
        if air > system_settings['air_max']:
            if sensor_data['cua_so'] != 'MỞ':
                sensor_data['cua_so'] = 'MỞ'
                save_pending_command('ESP32-S3-CLASSGUARD', 'WINDOW_OPEN', '1')
                print("🤖 Tự động MỞ cửa (KK kém)")
        elif air <= (system_settings['air_max'] - 200):
            if sensor_data['cua_so'] != 'ĐÓNG':
                sensor_data['cua_so'] = 'ĐÓNG'
                save_pending_command('ESP32-S3-CLASSGUARD', 'WINDOW_CLOSE', '0')
                print("🤖 Tự động ĐÓNG cửa (KK tốt)")
        
        # CẢNH BÁO: KHÔNG TỰ ĐỘNG ĐIỀU KHIỂN

def evaluate_environment():
    """Đánh giá môi trường học tập"""
    evaluations = []
    scores = []
    
    temp = sensor_data['nhiet_do']
    if 20 <= temp <= 28:
        evaluations.append(('🌡️ Nhiệt độ', 'Lý tưởng', 'success'))
        scores.append(2)
    elif 18 <= temp < 20 or 28 < temp <= 30:
        evaluations.append(('🌡️ Nhiệt độ', 'Chấp nhận', 'warning'))
        scores.append(1)
    else:
        evaluations.append(('🌡️ Nhiệt độ', 'Không tốt', 'danger'))
        scores.append(0)
    
    humidity = sensor_data['do_am']
    if 40 <= humidity <= 70:
        evaluations.append(('💧 Độ ẩm', 'Tốt', 'success'))
        scores.append(2)
    elif 30 <= humidity < 40 or 70 < humidity <= 80:
        evaluations.append(('💧 Độ ẩm', 'Trung bình', 'warning'))
        scores.append(1)
    else:
        evaluations.append(('💧 Độ ẩm', 'Không tốt', 'danger'))
        scores.append(0)
    
    light = sensor_data['anh_sang']
    if light >= 300:
        evaluations.append(('☀️ Ánh sáng', 'Đủ sáng', 'success'))
        scores.append(2)
    elif 200 <= light < 300:
        evaluations.append(('☀️ Ánh sáng', 'Hơi tối', 'warning'))
        scores.append(1)
    else:
        evaluations.append(('☀️ Ánh sáng', 'Thiếu sáng', 'danger'))
        scores.append(0)
    
    air = sensor_data['chat_luong_kk']
    if air < 400:
        evaluations.append(('💨 Chất lượng KK', 'Trong lành', 'success'))
        scores.append(2)
    elif 400 <= air < 800:
        evaluations.append(('💨 Chất lượng KK', 'Trung bình', 'warning'))
        scores.append(1)
    else:
        evaluations.append(('💨 Chất lượng KK', 'Ô nhiễm', 'danger'))
        scores.append(0)
    
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

# Tải cài đặt và lịch sử ban đầu
load_settings()
initialize_history()

# ========== ROUTES CHÍNH ==========
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            session['role'] = user[3]
            session['name'] = user[4]
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
    
    # Cập nhật cài đặt nếu cần
    if time.time() - last_settings_load > 30:
        load_settings()
    
    # Cập nhật dữ liệu demo nếu không có ESP32
    if sensor_data['device_status'] != 'online':
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
                         history_labels=json.dumps(history['time']),
                         temp_data=json.dumps(history['nhiet_do']),
                         hum_data=json.dumps(history['do_am']),
                         light_data=json.dumps(history['anh_sang']),
                         air_data=json.dumps(history['chat_luong_kk']),
                         noise_data=json.dumps(history['do_on']))

@app.route('/get_sensor_data')
def get_sensor_data():
    """API cho dashboard lấy dữ liệu"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Cập nhật dữ liệu demo nếu cần
    if sensor_data['device_status'] != 'online':
        update_demo_data()
    
    evaluation = evaluate_environment()
    
    # Cập nhật lịch sử
    update_history_from_db()
    
    return jsonify({
        'success': True,
        'sensors': sensor_data,
        'evaluation': evaluation,
        'history': history,
        'settings': system_settings,
        'cache': {
            'last_update': esp32_cache['last_update'],
            'status': esp32_cache['status'],
            'commands_sent': esp32_cache['commands_sent']
        }
    })

@app.route('/control', methods=['POST'])
def control():
    """Điều khiển thiết bị từ web"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Kiểm tra quyền
    if session['role'] not in ['admin', 'teacher']:
        return jsonify({'error': '❌ Không có quyền điều khiển!'}), 403
    
    data = request.json
    device = data.get('device')
    action = data.get('action')
    
    if not device or action not in ['BẬT', 'TẮT', 'MỞ', 'ĐÓNG']:
        return jsonify({'error': 'Thiếu thông tin'}), 400
    
    # CẢNH BÁO LUÔN ĐƯỢC ĐIỀU KHIỂN
    # Các thiết bị khác chỉ điều khiển được khi tắt chế độ tự động
    if device != 'canh_bao' and system_settings['auto_mode']:
        return jsonify({
            'error': '⚠️ Hệ thống đang ở chế độ tự động. Tắt chế độ tự động để điều khiển thủ công.'
        }), 400
    
    # Cập nhật trạng thái
    with data_lock:
        sensor_data[device] = action
    
    # Tạo lệnh cho ESP32
    command_map = {
        'quat': {'BẬT': 'FAN_ON', 'TẮT': 'FAN_OFF'},
        'den': {'BẬT': 'LIGHT_ON', 'TẮT': 'LIGHT_OFF'},
        'cua_so': {'MỞ': 'WINDOW_OPEN', 'ĐÓNG': 'WINDOW_CLOSE'},
        'canh_bao': {'BẬT': 'ALARM_ON', 'TẮT': 'ALARM_OFF'}
    }
    
    if device in command_map and action in command_map[device]:
        esp_command = command_map[device][action]
        save_pending_command('ESP32-S3-CLASSGUARD', esp_command, '1')
    
    # Thêm âm thanh xác nhận
    if device != 'canh_bao':  # Cảnh báo có âm thanh riêng
        save_pending_command('ESP32-S3-CLASSGUARD', 'PLAY_AUDIO', '07.mp3')
    
    return jsonify({
        'success': True,
        'message': f'✅ Đã {action.lower()} {device.replace("_", " ")}',
        'status': action,
        'auto_mode': system_settings['auto_mode']
    })

@app.route('/update_settings', methods=['POST'])
def update_settings():
    """Cập nhật cài đặt hệ thống"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if session['role'] not in ['admin', 'teacher']:
        return jsonify({'error': '❌ Không có quyền cập nhật cài đặt!'}), 403
    
    try:
        data = request.json
        
        # Cập nhật từng cài đặt
        updated = []
        for key in ['auto_mode', 'temp_min', 'temp_max', 'light_min', 'noise_max', 'air_max']:
            if key in data:
                save_setting(key, data[key])
                updated.append(key)
        
        # Tải lại cài đặt
        load_settings()
        
        # Gửi lệnh đến ESP32 nếu thay đổi chế độ
        if 'auto_mode' in updated:
            if system_settings['auto_mode']:
                save_pending_command('ESP32-S3-CLASSGUARD', 'AUTO_MODE_ON', '1')
                save_pending_command('ESP32-S3-CLASSGUARD', 'PLAY_AUDIO', '08.mp3')
            else:
                save_pending_command('ESP32-S3-CLASSGUARD', 'AUTO_MODE_OFF', '1')
                save_pending_command('ESP32-S3-CLASSGUARD', 'PLAY_AUDIO', '09.mp3')
        
        return jsonify({
            'success': True, 
            'message': '✅ Đã cập nhật cài đặt!',
            'settings': system_settings
        })
    except Exception as e:
        return jsonify({'error': f'❌ Dữ liệu không hợp lệ: {str(e)}'}), 400

# ========== API CHO ESP32 ==========
@app.route('/api/esp32/sync', methods=['POST'])
def esp32_sync():
    """API đồng bộ tất cả dữ liệu - NHANH <1s"""
    try:
        data = request.json
        device_id = data.get('device_id', 'ESP32-S3-CLASSGUARD')
        
        # Cập nhật cache
        with cache_lock:
            esp32_cache['last_update'] = time.time()
            esp32_cache['data'] = data
            esp32_cache['status'] = 'connected'
        
        # Cập nhật dữ liệu cảm biến từ ESP32
        with data_lock:
            sensor_data['nhiet_do'] = float(data.get('temperature', sensor_data['nhiet_do']))
            sensor_data['do_am'] = float(data.get('humidity', sensor_data['do_am']))
            sensor_data['anh_sang'] = int(data.get('light', sensor_data['anh_sang']))
            sensor_data['chat_luong_kk'] = int(data.get('air_quality', sensor_data['chat_luong_kk']))
            sensor_data['do_on'] = int(data.get('noise', sensor_data['do_on']))
            
            # Cập nhật trạng thái thiết bị từ ESP32
            if 'fan' in data:
                sensor_data['quat'] = 'BẬT' if data['fan'] == 1 else 'TẮT'
            if 'light_relay' in data:
                sensor_data['den'] = 'BẬT' if data['light_relay'] == 1 else 'TẮT'
            if 'window' in data:
                sensor_data['cua_so'] = 'MỞ' if data['window'] == 1 else 'ĐÓNG'
            if 'alarm' in data:
                sensor_data['canh_bao'] = 'BẬT' if data['alarm'] == 1 else 'TẮT'
            
            sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S")
            sensor_data['device_status'] = 'online'
        
        # Lưu vào database
        save_sensor_to_db(
            sensor_data['nhiet_do'],
            sensor_data['do_am'],
            sensor_data['anh_sang'],
            sensor_data['chat_luong_kk'],
            sensor_data['do_on']
        )
        
        # Điều khiển tự động (không bao gồm cảnh báo)
        auto_control_logic(
            sensor_data['nhiet_do'],
            sensor_data['anh_sang'],
            sensor_data['chat_luong_kk']
        )
        
        # Cập nhật lịch sử
        update_history_from_db()
        
        # Lấy lệnh chờ cho ESP32
        pending_commands = get_pending_commands(device_id, limit=3)
        
        # Kiểm tra cảnh báo âm thanh
        audio_commands = check_audio_alerts(
            sensor_data['nhiet_do'],
            sensor_data['anh_sang'],
            sensor_data['chat_luong_kk'],
            sensor_data['do_on']
        )
        
        # TRẢ VỀ TẤT CẢ THÔNG TIN
        response = {
            'success': True,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'settings': system_settings,
            'thresholds': {
                'temp_min': system_settings['temp_min'],
                'temp_max': system_settings['temp_max'],
                'light_min': system_settings['light_min'],
                'air_max': system_settings['air_max'],
                'noise_max': system_settings['noise_max'],
                'auto_mode': system_settings['auto_mode'],
                'audio_enabled': system_settings['audio_enabled']
            },
            'commands': pending_commands,
            'audio_commands': audio_commands,
            'sync_interval': system_settings['sync_interval']
        }
        
        print(f"✅ Đồng bộ với {device_id}: {len(pending_commands)} lệnh chờ")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Lỗi đồng bộ ESP32: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/esp32/command', methods=['POST'])
def send_command_to_esp32():
    """Gửi lệnh điều khiển đến ESP32"""
    try:
        data = request.json
        device_id = data.get('device_id', 'ESP32-S3-CLASSGUARD')
        command = data.get('command')
        value = data.get('value', '1')
        
        if not command:
            return jsonify({'error': 'Thiếu lệnh'}), 400
        
        # Lưu lệnh vào database
        save_pending_command(device_id, command, value)
        
        # Lấy ID lệnh vừa thêm
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        c.execute("SELECT MAX(id) FROM pending_commands")
        command_id = c.fetchone()[0]
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Đã gửi lệnh {command}',
            'command_id': command_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/esp32/ack', methods=['POST'])
def esp32_command_ack():
    """ESP32 xác nhận đã thực hiện lệnh"""
    try:
        data = request.json
        command_id = data.get('command_id')
        
        if command_id:
            mark_command_executed(command_id)
            print(f"✅ ESP32 đã xác nhận lệnh: {command_id}")
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/esp32/status', methods=['GET'])
def esp32_status():
    """Kiểm tra kết nối API"""
    with cache_lock:
        status = esp32_cache['status']
        last_update = esp32_cache['last_update']
        age = time.time() - last_update
    
    return jsonify({
        'status': status,
        'server': 'classguard-web.onrender.com',
        'project': 'CLASSGUARD THCS',
        'version': '4.0',
        'auto_mode': system_settings['auto_mode'],
        'last_update': round(age, 1),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

def check_audio_alerts(temp, light, air, noise):
    """Kiểm tra và tạo lệnh âm thanh cảnh báo"""
    audio_commands = []
    
    # Nhiệt độ cao (>30°C) - File 03.mp3
    if temp > 30.0:
        audio_commands.append({'file': '03.mp3', 'priority': 'high'})
    
    # Chất lượng không khí kém (>1000 PPM) - File 04.mp3
    if air > 1000:
        audio_commands.append({'file': '04.mp3', 'priority': 'high'})
    
    # Ánh sáng yếu (<200 lux) - File 06.mp3
    if light < 200:
        audio_commands.append({'file': '06.mp3', 'priority': 'medium'})
    
    # Độ ồn cao (>noise_max) - File 05.mp3
    if noise > system_settings['noise_max']:
        audio_commands.append({'file': '05.mp3', 'priority': 'high'})
    
    return audio_commands

# ========== CÁC TRANG KHÁC ==========
@app.route('/data')
def data_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('classguard.db')
    c = conn.cursor()
    c.execute('''SELECT timestamp, temperature, humidity, light, air_quality, noise 
                 FROM sensor_history 
                 ORDER BY timestamp DESC 
                 LIMIT 30''')
    records = c.fetchall()
    conn.close()
    
    data_list = []
    for i, record in enumerate(records):
        timestamp, temp, humidity, light, air, noise = record
        
        # Đánh giá dựa trên ngưỡng
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
            'thoi_gian': datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime("%H:%M"),
            'ngay': datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime("%d/%m/%Y"),
            'nhiet_do': round(temp, 1),
            'do_am': round(humidity, 1),
            'anh_sang': light,
            'chat_luong_kk': air,
            'do_on': noise,
            'danh_gia': eval_text,
            'danh_gia_color': eval_color
        })
    
    return render_template('data.html',
                         data=data_list,
                         role=session['role'])

@app.route('/settings')
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
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['CLASSGUARD - BÁO CÁO MÔI TRƯỜNG LỚP HỌC'])
    writer.writerow(['Thời gian xuất', datetime.now().strftime("%d/%m/%Y %H:%M:%S")])
    writer.writerow(['Người xuất', session.get('name', 'Unknown')])
    writer.writerow(['Vai trò', session.get('role', 'Unknown')])
    writer.writerow([])
    
    # Thông số cảm biến hiện tại
    writer.writerow(['THÔNG SỐ CẢM BIẾN HIỆN TẠI'])
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
    
    # Trạng thái thiết bị
    writer.writerow(['TRẠNG THÁI THIẾT BỊ'])
    writer.writerow(['Thiết bị', 'Trạng thái'])
    writer.writerow(['Quạt', sensor_data['quat']])
    writer.writerow(['Đèn', sensor_data['den']])
    writer.writerow(['Cửa sổ', sensor_data['cua_so']])
    writer.writerow(['Cảnh báo', sensor_data['canh_bao']])
    writer.writerow([])
    
    # Cài đặt hệ thống
    writer.writerow(['CÀI ĐẶT HỆ THỐNG'])
    writer.writerow(['Chế độ tự động', 'BẬT' if system_settings['auto_mode'] else 'TẮT'])
    writer.writerow(['Nhiệt độ min', f"{system_settings['temp_min']}°C"])
    writer.writerow(['Nhiệt độ max', f"{system_settings['temp_max']}°C"])
    writer.writerow(['Ánh sáng min', f"{system_settings['light_min']} lux"])
    writer.writerow(['Chất lượng KK max', f"{system_settings['air_max']} PPM"])
    writer.writerow(['Độ ồn max', f"{system_settings['noise_max']} dB"])
    
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=classguard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@app.route('/api/system/info')
def system_info():
    """Thông tin hệ thống"""
    with cache_lock:
        cache_info = {
            'status': esp32_cache['status'],
            'last_update': round(time.time() - esp32_cache['last_update'], 1),
            'commands_sent': esp32_cache['commands_sent']
        }
    
    # Thống kê database
    conn = sqlite3.connect('classguard.db')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM sensor_history")
    history_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM pending_commands WHERE executed = 0")
    pending_commands = c.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'version': '4.0',
        'project': 'CLASSGUARD - Hệ thống giám sát lớp học',
        'status': 'running',
        'database': {
            'sensor_history': history_count,
            'pending_commands': pending_commands,
            'size': 'classguard.db'
        },
        'cache': cache_info,
        'settings': system_settings,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# ========== BACKGROUND TASKS ==========
def background_tasks():
    """Các tác vụ chạy nền"""
    while True:
        try:
            # Cập nhật cài đặt mỗi 30 giây
            if time.time() - last_settings_load > 30:
                load_settings()
            
            # Kiểm tra kết nối ESP32
            with cache_lock:
                age = time.time() - esp32_cache['last_update']
                if age > 60:  # 60 giây không có tín hiệu
                    esp32_cache['status'] = 'disconnected'
                    with data_lock:
                        sensor_data['device_status'] = 'offline'
                elif age > 10:  # 10 giây
                    esp32_cache['status'] = 'idle'
                else:
                    esp32_cache['status'] = 'connected'
            
            # Cập nhật dữ liệu demo nếu không có ESP32
            if sensor_data['device_status'] != 'online':
                update_demo_data()
            
            time.sleep(5)  # Chạy mỗi 5 giây
            
        except Exception as e:
            print(f"❌ Lỗi background task: {e}")
            time.sleep(10)

# Khởi động background task
background_thread = threading.Thread(target=background_tasks, daemon=True)
background_thread.start()

# ========== RUN SERVER ==========
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 CLASSGUARD Web Server - Phiên bản 4.0")
    print("📊 Đồng bộ ESP32 ↔ Web <1s")
    print("🎯 Cảnh báo riêng biệt - Điều khiển tức thì")
    print("=" * 60)
    print(f"🌐 URL: http://localhost:5000")
    print(f"📡 API: http://localhost:5000/api/esp32/sync")
    print(f"⚙️  Chế độ tự động: {'BẬT' if system_settings['auto_mode'] else 'TẮT'}")
    print(f"📊 Số bản ghi lịch sử: {len(history['time'])}")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
