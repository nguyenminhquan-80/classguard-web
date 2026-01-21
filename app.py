"""
CLASSGUARD - Web Server
Phiên bản: 3.0 - Đã sửa lỗi đồng bộ hoàn toàn
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
import random
from datetime import datetime, timedelta
import json
import csv
import io
import sqlite3
from threading import Lock
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'classguard_final_v3_2024'
app.secret_key = 'classguard_final_v3_2024'

# ========== KHỞI TẠO DATABASE ==========
def init_db():
    conn = sqlite3.connect('classguard.db')
    c = conn.cursor()
    
    # Bảng người dùng
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  role TEXT,
                  name TEXT)''')
    
    # Bảng lịch sử cảm biến
    c.execute('''CREATE TABLE IF NOT EXISTS sensor_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  temperature REAL,
                  humidity REAL,
                  light INTEGER,
                  air_quality INTEGER,
                  noise INTEGER,
                  temp_status TEXT,
                  hum_status TEXT,
                  light_status TEXT,
                  air_status TEXT,
                  noise_status TEXT)''')
    
    # Bảng lệnh chờ
    c.execute('''CREATE TABLE IF NOT EXISTS pending_commands
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  device_id TEXT,
                  command TEXT,
                  value TEXT,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  executed INTEGER DEFAULT 0,
                  ack_received INTEGER DEFAULT 0)''')
    
    # Bảng trạng thái thiết bị
    c.execute('''CREATE TABLE IF NOT EXISTS device_status
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  device_id TEXT UNIQUE,
                  fan INTEGER DEFAULT 0,
                  light INTEGER DEFAULT 0,
                  window INTEGER DEFAULT 0,
                  alarm INTEGER DEFAULT 0,
                  auto_mode INTEGER DEFAULT 1,
                  last_update DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Thêm tài khoản mẫu
    users_data = [
        ('admin', 'admin123', 'admin', 'Quản trị viên'),
        ('giaovien', 'giaovien123', 'teacher', 'Giáo viên'),
        ('hocsinh', 'hocsinh123', 'student', 'Học sinh'),
        ('xem', 'xem123', 'viewer', 'Khách xem')
    ]
    
    for user in users_data:
        try:
            c.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)", user)
        except:
            pass
    
    # Thêm trạng thái thiết bị mặc định
    try:
        c.execute("INSERT INTO device_status (device_id, auto_mode) VALUES ('ESP32-S3-CLASSGUARD', 1)")
    except:
        pass
    
    conn.commit()
    conn.close()

# Khởi tạo database
init_db()

# Lock cho thread-safe
data_lock = Lock()

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

# Đánh giá cảm biến
sensor_evaluations = {
    'temp_status': 'Tốt',
    'hum_status': 'Tốt',
    'light_status': 'Tốt',
    'air_status': 'Tốt',
    'noise_status': 'Yên tĩnh'
}

# Lịch sử dữ liệu
history = {
    'time': [],
    'nhiet_do': [],
    'do_am': [],
    'anh_sang': [],
    'chat_luong_kk': [],
    'do_on': []
}

# Cài đặt hệ thống - QUAN TRỌNG: Giá trị mặc định
system_settings = {
    'auto_mode': True,  # Mặc định là TỰ ĐỘNG
    'temp_min': 20,
    'temp_max': 28,
    'light_min': 300,
    'noise_max': 70,
    'air_max': 800
}

# ========== HÀM KHỞI TẠO LỊCH SỬ ==========
def initialize_history():
    """Khởi tạo dữ liệu lịch sử từ database"""
    global history
    
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

# Khởi tạo history
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
    
    # Lấy trạng thái thiết bị từ database
    conn = sqlite3.connect('classguard.db')
    c = conn.cursor()
    c.execute("SELECT auto_mode FROM device_status WHERE device_id = 'ESP32-S3-CLASSGUARD'")
    device_status = c.fetchone()
    conn.close()
    
    if device_status:
        system_settings['auto_mode'] = bool(device_status[0])
    
    evaluation = evaluate_environment()
    
    return render_template('dashboard.html',
                         data=sensor_data,
                         evaluations=sensor_evaluations,
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
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Lấy trạng thái auto_mode từ database
    conn = sqlite3.connect('classguard.db')
    c = conn.cursor()
    c.execute("SELECT auto_mode FROM device_status WHERE device_id = 'ESP32-S3-CLASSGUARD'")
    device_status = c.fetchone()
    conn.close()
    
    if device_status:
        system_settings['auto_mode'] = bool(device_status[0])
    
    evaluation = evaluate_environment()
    
    return jsonify({
        'success': True,
        'sensors': sensor_data,
        'evaluations': sensor_evaluations,
        'evaluation': evaluation,
        'settings': system_settings,
        'history': history,
        'charts': {
            'labels': history['time'],
            'datasets': {
                'temperature': history['nhiet_do'],
                'humidity': history['do_am'],
                'light': history['anh_sang'],
                'air_quality': history['chat_luong_kk'],
                'noise': history['do_on']
            }
        }
    })

# ========== ĐIỀU KHIỂN THIẾT BỊ ==========
@app.route('/control', methods=['POST'])
def control():
    """Điều khiển thiết bị từ web - QUAN TRỌNG: Kiểm tra chế độ"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # CHỈ admin và teacher được điều khiển
    if session['role'] not in ['admin', 'teacher']:
        return jsonify({'error': '❌ Không có quyền điều khiển!'}), 403
    
    # Kiểm tra chế độ tự động - QUAN TRỌNG
    if system_settings['auto_mode']:
        return jsonify({
            'error': '⚠️ Hệ thống đang ở chế độ TỰ ĐỘNG!',
            'message': 'Vui lòng tắt chế độ tự động để điều khiển thủ công.',
            'auto_mode': True
        }), 403
    
    data = request.json
    device = data.get('device')
    action = data.get('action')
    
    if not device or action not in ['BẬT', 'TẮT', 'MỞ', 'ĐÓNG']:
        return jsonify({'error': 'Thiếu thông tin'}), 400
    
    # Cập nhật trạng thái trên web
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
        value = '1' if action in ['BẬT', 'MỞ'] else '0'
        
        # Lưu lệnh vào database
        save_pending_command('ESP32-S3-CLASSGUARD', esp_command, value)
    
    return jsonify({
        'success': True,
        'message': f'✅ Đã {action.lower()} {device}',
        'status': action,
        'auto_mode': False
    })

@app.route('/toggle_auto_mode', methods=['POST'])
def toggle_auto_mode():
    """Chuyển đổi chế độ tự động/thủ công"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if session['role'] not in ['admin', 'teacher']:
        return jsonify({'error': '❌ Không có quyền!'}), 403
    
    data = request.json
    auto_mode = data.get('auto_mode', True)
    
    # Cập nhật cài đặt
    system_settings['auto_mode'] = bool(auto_mode)
    
    # Cập nhật database
    conn = sqlite3.connect('classguard.db')
    c = conn.cursor()
    c.execute('''UPDATE device_status 
                 SET auto_mode = ?, last_update = CURRENT_TIMESTAMP
                 WHERE device_id = 'ESP32-S3-CLASSGUARD' ''',
              (1 if auto_mode else 0,))
    conn.commit()
    
    # Nếu chuyển sang chế độ tự động, xóa tất cả lệnh chờ
    if auto_mode:
        c.execute("DELETE FROM pending_commands WHERE device_id = 'ESP32-S3-CLASSGUARD'")
        conn.commit()
        message = '✅ Đã chuyển sang chế độ TỰ ĐỘNG'
    else:
        message = '✅ Đã chuyển sang chế độ THỦ CÔNG'
    
    conn.close()
    
    return jsonify({
        'success': True,
        'message': message,
        'auto_mode': auto_mode
    })

@app.route('/update_settings', methods=['POST'])
def update_settings():
    """Cập nhật cài đặt ngưỡng"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if session['role'] not in ['admin', 'teacher']:
        return jsonify({'error': '❌ Không có quyền cập nhật cài đặt!'}), 403
    
    try:
        data = request.json
        
        # Giữ nguyên auto_mode nếu không có trong request
        if 'auto_mode' in data:
            system_settings['auto_mode'] = bool(data['auto_mode'])
        
        # Cập nhật ngưỡng
        system_settings['temp_min'] = float(data.get('temp_min', system_settings['temp_min']))
        system_settings['temp_max'] = float(data.get('temp_max', system_settings['temp_max']))
        system_settings['light_min'] = float(data.get('light_min', system_settings['light_min']))
        system_settings['noise_max'] = float(data.get('noise_max', system_settings['noise_max']))
        system_settings['air_max'] = float(data.get('air_max', system_settings['air_max']))
        
        return jsonify({'success': True, 'message': '✅ Đã cập nhật cài đặt!'})
    except Exception as e:
        return jsonify({'error': f'❌ Dữ liệu không hợp lệ: {str(e)}!'}), 400

# ========== CÁC TRANG KHÁC ==========
@app.route('/data')
def data_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('classguard.db')
    c = conn.cursor()
    c.execute('''SELECT timestamp, temperature, humidity, light, air_quality, noise,
                        temp_status, hum_status, light_status, air_status, noise_status
                 FROM sensor_history 
                 ORDER BY timestamp DESC 
                 LIMIT 30''')
    records = c.fetchall()
    conn.close()
    
    data_list = []
    for i, record in enumerate(records):
        timestamp, temp, humidity, light, air, noise, temp_status, hum_status, light_status, air_status, noise_status = record
        
        # Xác định màu sắc cho đánh giá
        def get_status_color(status):
            if status in ['Lý tưởng', 'Tốt', 'Đủ sáng', 'Yên tĩnh']:
                return 'success'
            elif status in ['Hơi lạnh', 'Hơi nóng', 'Hơi khô', 'Hơi ẩm', 'Hơi tối', 'Hơi chói', 'Trung bình', 'Bình thường']:
                return 'warning'
            else:
                return 'danger'
        
        data_list.append({
            'stt': i + 1,
            'thoi_gian': datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime("%H:%M"),
            'ngay': datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime("%d/%m/%Y"),
            'nhiet_do': round(temp, 1),
            'do_am': round(humidity, 1),
            'anh_sang': light,
            'chat_luong_kk': air,
            'do_on': noise,
            'temp_status': temp_status,
            'hum_status': hum_status,
            'light_status': light_status,
            'air_status': air_status,
            'noise_status': noise_status,
            'temp_color': get_status_color(temp_status),
            'hum_color': get_status_color(hum_status),
            'light_color': get_status_color(light_status),
            'air_color': get_status_color(air_status),
            'noise_color': get_status_color(noise_status)
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
    
    writer.writerow(['CLASSGUARD - BÁO CÁO MÔI TRƯỜNG LỚP HỌC'])
    writer.writerow(['Thời gian xuất', datetime.now().strftime("%d/%m/%Y %H:%M:%S")])
    writer.writerow(['Người xuất', session.get('name', 'Unknown')])
    writer.writerow(['Vai trò', session.get('role', 'Unknown')])
    writer.writerow(['Chế độ', 'TỰ ĐỘNG' if system_settings['auto_mode'] else 'THỦ CÔNG'])
    writer.writerow([])
    writer.writerow(['THÔNG SỐ CẢM BIẾN HIỆN TẠI'])
    writer.writerow(['Thông số', 'Giá trị', 'Đơn vị', 'Trạng thái', 'Đánh giá'])
    writer.writerow(['Nhiệt độ', f"{sensor_data['nhiet_do']:.1f}", '°C', 
                     sensor_data['quat'], sensor_evaluations['temp_status']])
    writer.writerow(['Độ ẩm', f"{sensor_data['do_am']:.1f}", '%',
                     sensor_data['den'], sensor_evaluations['hum_status']])
    writer.writerow(['Ánh sáng', str(sensor_data['anh_sang']), 'lux',
                     sensor_data['den'], sensor_evaluations['light_status']])
    writer.writerow(['Chất lượng KK', str(sensor_data['chat_luong_kk']), 'PPM',
                     sensor_data['cua_so'], sensor_evaluations['air_status']])
    writer.writerow(['Độ ồn', str(sensor_data['do_on']), 'dB',
                     sensor_data['canh_bao'], sensor_evaluations['noise_status']])
    writer.writerow([])
    writer.writerow(['NGƯỠNG CÀI ĐẶT'])
    writer.writerow(['Thông số', 'Giá trị', 'Đơn vị'])
    writer.writerow(['Nhiệt độ min', system_settings['temp_min'], '°C'])
    writer.writerow(['Nhiệt độ max', system_settings['temp_max'], '°C'])
    writer.writerow(['Ánh sáng min', system_settings['light_min'], 'lux'])
    writer.writerow(['Độ ồn max', system_settings['noise_max'], 'dB'])
    writer.writerow(['Chất lượng KK max', system_settings['air_max'], 'PPM'])
    
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=classguard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

# ========== API CHO ESP32 ==========
@app.route('/api/esp32/data', methods=['POST'])
def receive_esp32_data():
    """API nhận dữ liệu từ ESP32"""
    try:
        data = request.json
        print(f"📥 Nhận dữ liệu từ ESP32: {json.dumps(data, indent=2)}")
        
        with data_lock:
            # Cập nhật dữ liệu cảm biến
            if 'temperature' in data:
                sensor_data['nhiet_do'] = float(data['temperature'])
            if 'humidity' in data:
                sensor_data['do_am'] = float(data['humidity'])
            if 'light' in data:
                sensor_data['anh_sang'] = int(data['light'])
            if 'air_quality' in data:
                sensor_data['chat_luong_kk'] = int(data['air_quality'])
            if 'noise' in data:
                sensor_data['do_on'] = int(data['noise'])
            
            # Cập nhật trạng thái thiết bị từ ESP32
            if 'fan' in data:
                sensor_data['quat'] = 'BẬT' if data['fan'] == 1 else 'TẮT'
            if 'light_relay' in data:
                sensor_data['den'] = 'BẬT' if data['light_relay'] == 1 else 'TẮT'
            if 'window' in data:
                sensor_data['cua_so'] = 'MỞ' if data['window'] == 1 else 'ĐÓNG'
            if 'alarm' in data:
                sensor_data['canh_bao'] = 'BẬT' if data['alarm'] == 1 else 'TẮT'
            
            # Cập nhật đánh giá cảm biến
            if 'temp_status' in data:
                sensor_evaluations['temp_status'] = data['temp_status']
            if 'hum_status' in data:
                sensor_evaluations['hum_status'] = data['hum_status']
            if 'light_status' in data:
                sensor_evaluations['light_status'] = data['light_status']
            if 'air_status' in data:
                sensor_evaluations['air_status'] = data['air_status']
            if 'noise_status' in data:
                sensor_evaluations['noise_status'] = data['noise_status']
            
            # Cập nhật chế độ từ ESP32
            if 'auto_mode' in data:
                auto_mode = bool(data['auto_mode'])
                system_settings['auto_mode'] = auto_mode
                
                # Cập nhật database
                conn = sqlite3.connect('classguard.db')
                c = conn.cursor()
                c.execute('''UPDATE device_status 
                             SET auto_mode = ?, last_update = CURRENT_TIMESTAMP
                             WHERE device_id = 'ESP32-S3-CLASSGUARD' ''',
                          (1 if auto_mode else 0,))
                conn.commit()
                conn.close()
            
            sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S")
            sensor_data['device_status'] = 'online'
        
        # Lưu vào database
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        c.execute('''INSERT INTO sensor_history 
                     (temperature, humidity, light, air_quality, noise,
                      temp_status, hum_status, light_status, air_status, noise_status)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (sensor_data['nhiet_do'], sensor_data['do_am'], 
                  sensor_data['anh_sang'], sensor_data['chat_luong_kk'],
                  sensor_data['do_on'],
                  sensor_evaluations['temp_status'],
                  sensor_evaluations['hum_status'],
                  sensor_evaluations['light_status'],
                  sensor_evaluations['air_status'],
                  sensor_evaluations['noise_status']))
        conn.commit()
        conn.close()
        
        # Cập nhật lịch sử
        update_history_from_db()
        
        # Kiểm tra cảnh báo
        alerts = check_esp32_alerts(data)
        
        # QUAN TRỌNG: Chỉ điều khiển tự động nếu đang ở chế độ tự động
        if system_settings['auto_mode']:
            auto_control_logic(data)
        
        return jsonify({
            'success': True,
            'message': 'Đã nhận dữ liệu từ ESP32',
            'alerts': alerts,
            'thresholds': system_settings,
            'auto_mode': system_settings['auto_mode'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        print(f"❌ Lỗi nhận dữ liệu ESP32: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 400

@app.route('/api/esp32/control', methods=['GET'])
def get_esp32_control():
    """ESP32 lấy lệnh điều khiển từ web"""
    device_id = request.args.get('device_id', 'ESP32-S3-CLASSGUARD')
    
    # Lấy chế độ hiện tại
    conn = sqlite3.connect('classguard.db')
    c = conn.cursor()
    c.execute("SELECT auto_mode FROM device_status WHERE device_id = ?", (device_id,))
    result = c.fetchone()
    
    auto_mode = True
    if result:
        auto_mode = bool(result[0])
    
    # Nếu đang ở chế độ tự động, không gửi lệnh điều khiển
    if auto_mode:
        conn.close()
        return jsonify({
            'auto_mode': True,
            'message': 'Hệ thống đang ở chế độ TỰ ĐỘNG'
        }), 200
    
    # Lấy lệnh chờ
    c.execute('''SELECT id, command, value 
                 FROM pending_commands 
                 WHERE device_id = ? AND executed = 0 
                 ORDER BY created_at ASC 
                 LIMIT 1''', (device_id,))
    pending = c.fetchone()
    
    if pending:
        command_id, command, value = pending
        # Đánh dấu là đang xử lý
        c.execute("UPDATE pending_commands SET executed = 1 WHERE id = ?", (command_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'command': command,
            'value': value,
            'command_id': command_id,
            'auto_mode': False
        })
    
    conn.close()
    return jsonify({
        'auto_mode': False,
        'message': 'Không có lệnh chờ'
    }), 200

@app.route('/api/esp32/ack', methods=['POST'])
def esp32_command_ack():
    """ESP32 xác nhận đã thực hiện lệnh"""
    try:
        data = request.json
        command_id = data.get('command_id')
        status = data.get('status', 'executed')
        
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        
        if status == 'executed':
            # Đánh dấu đã thực thi và xác nhận
            c.execute("UPDATE pending_commands SET ack_received = 1 WHERE id = ?", (command_id,))
            print(f"✅ ESP32 đã thực hiện lệnh: {command_id}")
        elif status == 'ignored_auto_mode':
            # Xóa lệnh vì bị bỏ qua do chế độ tự động
            c.execute("DELETE FROM pending_commands WHERE id = ?", (command_id,))
            print(f"⚠️ Lệnh {command_id} bị bỏ qua (chế độ tự động)")
        
        conn.commit()
        
        # Cập nhật trạng thái auto_mode nếu có
        if 'auto_mode' in data:
            auto_mode = bool(data['auto_mode'])
            c.execute('''UPDATE device_status 
                         SET auto_mode = ?, last_update = CURRENT_TIMESTAMP
                         WHERE device_id = 'ESP32-S3-CLASSGUARD' ''',
                      (1 if auto_mode else 0,))
            conn.commit()
            system_settings['auto_mode'] = auto_mode
        
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/esp32/status', methods=['GET'])
def esp32_status():
    """Kiểm tra kết nối API"""
    conn = sqlite3.connect('classguard.db')
    c = conn.cursor()
    c.execute("SELECT auto_mode FROM device_status WHERE device_id = 'ESP32-S3-CLASSGUARD'")
    result = c.fetchone()
    conn.close()
    
    auto_mode = True
    if result:
        auto_mode = bool(result[0])
    
    return jsonify({
        'status': 'online',
        'server': 'classguard-web.onrender.com',
        'project': 'CLASSGUARD THCS',
        'version': '3.0',
        'auto_mode': auto_mode,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# ========== HÀM ĐÁNH GIÁ MÔI TRƯỜNG ==========
def evaluate_environment():
    """Đánh giá môi trường tổng thể"""
    scores = []
    
    # Đánh giá nhiệt độ
    temp = sensor_data['nhiet_do']
    if 22 <= temp <= 26:
        scores.append(2)
    elif 20 <= temp < 22 or 26 < temp <= 30:
        scores.append(1)
    else:
        scores.append(0)
    
    # Đánh giá độ ẩm
    humidity = sensor_data['do_am']
    if 40 <= humidity <= 60:
        scores.append(2)
    elif 30 <= humidity < 40 or 60 < humidity <= 70:
        scores.append(1)
    else:
        scores.append(0)
    
    # Đánh giá ánh sáng
    light = sensor_data['anh_sang']
    if 300 <= light <= 500:
        scores.append(2)
    elif 200 <= light < 300 or 500 < light <= 1000:
        scores.append(1)
    else:
        scores.append(0)
    
    # Đánh giá chất lượng KK
    air = sensor_data['chat_luong_kk']
    if air < 750:
        scores.append(2)
    elif 750 <= air <= 1200:
        scores.append(1)
    else:
        scores.append(0)
    
    # Đánh giá độ ồn - QUAN TRỌNG: Sửa theo yêu cầu
    noise = sensor_data['do_on']
    if noise < 50:  # Yên tĩnh
        scores.append(2)
    elif 50 <= noise <= 70:  # Bình thường
        scores.append(1)
    else:  # Ồn ào
        scores.append(0)
    
    total_score = sum(scores)
    percentage = (total_score / 10) * 100
    
    if percentage >= 80:
        overall = 'TỐT'
        overall_class = 'success'
        advice = 'Môi trường học tập lý tưởng!'
    elif percentage >= 60:
        overall = 'KHÁ'
        overall_class = 'warning'
        advice = 'Môi trường khá tốt, có thể cải thiện một số yếu tố.'
    else:
        overall = 'CẦN CẢI THIỆN'
        overall_class = 'danger'
        advice = 'Cần điều chỉnh môi trường trước khi học.'
    
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
        'class_color': class_color
    }

def auto_control_logic(data):
    """Logic điều khiển tự động - CHỈ chạy khi auto_mode = True"""
    if not system_settings['auto_mode']:
        return
    
    temp = data.get('temperature', sensor_data['nhiet_do'])
    light = data.get('light', sensor_data['anh_sang'])
    air = data.get('air_quality', sensor_data['chat_luong_kk'])
    noise = data.get('noise', sensor_data['do_on'])
    
    # Nhiệt độ
    if temp > system_settings['temp_max']:
        sensor_data['quat'] = 'BẬT'
        save_pending_command('ESP32-S3-CLASSGUARD', 'FAN_ON', '1')
    elif temp < system_settings['temp_min']:
        sensor_data['quat'] = 'TẮT'
        save_pending_command('ESP32-S3-CLASSGUARD', 'FAN_OFF', '0')
    
    # Ánh sáng
    if light < system_settings['light_min']:
        sensor_data['den'] = 'BẬT'
        save_pending_command('ESP32-S3-CLASSGUARD', 'LIGHT_ON', '1')
    else:
        sensor_data['den'] = 'TẮT'
        save_pending_command('ESP32-S3-CLASSGUARD', 'LIGHT_OFF', '0')
    
    # Chất lượng không khí
    if air > system_settings['air_max']:
        sensor_data['cua_so'] = 'MỞ'
        save_pending_command('ESP32-S3-CLASSGUARD', 'WINDOW_OPEN', '1')
    else:
        sensor_data['cua_so'] = 'ĐÓNG'
        save_pending_command('ESP32-S3-CLASSGUARD', 'WINDOW_CLOSE', '0')
    
    # Độ ồn
    if noise > system_settings['noise_max']:
        sensor_data['canh_bao'] = 'BẬT'
        save_pending_command('ESP32-S3-CLASSGUARD', 'ALARM_ON', '1')
    else:
        sensor_data['canh_bao'] = 'TẮT'
        save_pending_command('ESP32-S3-CLASSGUARD', 'ALARM_OFF', '0')

def update_history_from_db():
    """Cập nhật history từ database"""
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

def check_esp32_alerts(data):
    """Kiểm tra cảnh báo từ dữ liệu ESP32"""
    alerts = []
    
    temp = data.get('temperature', 25)
    air = data.get('air_quality', 400)
    noise = data.get('noise', 45)
    light = data.get('light', 300)
    
    if temp > 30:
        alerts.append({'type': 'warning', 'message': '🌡️ Nhiệt độ cao (>30°C)'})
    elif temp < 20:
        alerts.append({'type': 'warning', 'message': '🌡️ Nhiệt độ thấp (<20°C)'})
    
    if air > 1000:
        alerts.append({'type': 'danger', 'message': '⚠️ Chất lượng không khí kém (>1000 PPM)'})
    elif air > 800:
        alerts.append({'type': 'warning', 'message': '💨 Chất lượng không khí trung bình (>800 PPM)'})
    
    # QUAN TRỌNG: Sửa cảnh báo độ ồn
    if noise > 70:
        alerts.append({'type': 'danger', 'message': '⚠️ Độ ồn quá cao (>70 dB)'})
    elif noise > 50:
        alerts.append({'type': 'warning', 'message': '🔊 Độ ồn ở mức bình thường (50-70 dB)'})
    
    if light < 200:
        alerts.append({'type': 'danger', 'message': '⚠️ Ánh sáng quá yếu (<200 lux)'})
    elif light < 300:
        alerts.append({'type': 'warning', 'message': '☀️ Ánh sáng hơi yếu (<300 lux)'})
    
    return alerts

def save_pending_command(device_id, command, value):
    """Lưu lệnh chờ vào database"""
    try:
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        c.execute('''INSERT INTO pending_commands (device_id, command, value)
                     VALUES (?, ?, ?)''', (device_id, command, value))
        conn.commit()
        conn.close()
        print(f"💾 Đã lưu lệnh: {command}={value} cho {device_id}")
    except Exception as e:
        print(f"❌ Lỗi lưu lệnh: {e}")

# ========== RUN SERVER ==========
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 CLASSGUARD Web Server - Phiên bản 3.0")
    print("✅ Đã sửa lỗi đồng bộ hoàn toàn")
    print("🌐 URL: http://localhost:5000")
    print("📡 API Endpoints:")
    print("  - POST /api/esp32/data    (Nhận dữ liệu từ ESP32)")
    print("  - GET  /api/esp32/control (Gửi lệnh cho ESP32)")
    print("  - POST /api/esp32/ack     (Nhận xác nhận từ ESP32)")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
