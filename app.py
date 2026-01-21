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

# ========== CẤU HÌNH DATABASE ==========
def init_db():
    conn = sqlite3.connect('classguard.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  role TEXT,
                  name TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sensor_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  temperature REAL,
                  humidity REAL,
                  light INTEGER,
                  air_quality INTEGER,
                  noise INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS pending_commands
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  device_id TEXT,
                  command TEXT,
                  value TEXT,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  executed INTEGER DEFAULT 0)''')
    
    # BẢNG MỚI: thresholds để đồng bộ ngưỡng với ESP32
    c.execute('''CREATE TABLE IF NOT EXISTS thresholds
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  temp_min REAL DEFAULT 20.0,
                  temp_max REAL DEFAULT 28.0,
                  light_min REAL DEFAULT 300.0,
                  air_max INTEGER DEFAULT 800,
                  noise_max INTEGER DEFAULT 70,
                  auto_mode INTEGER DEFAULT 1,
                  audio_enabled INTEGER DEFAULT 1,
                  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
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
    
    # Thêm ngưỡng mặc định
    c.execute('''INSERT OR IGNORE INTO thresholds 
                 (id, temp_min, temp_max, light_min, air_max, noise_max, auto_mode, audio_enabled) 
                 VALUES (1, 20.0, 28.0, 300.0, 800, 70, 1, 1)''')
    
    # Thêm dữ liệu mẫu cho biểu đồ
    base_time = datetime.now() - timedelta(minutes=14)
    for i in range(15):
        record_time = base_time + timedelta(minutes=i)
        temp = 25 + random.uniform(-2, 2)
        humidity = 60 + random.uniform(-10, 10)
        light = 300 + random.randint(-50, 100)
        air = 400 + random.randint(-100, 200)
        noise = 45 + random.randint(-10, 20)
        
        c.execute('''INSERT INTO sensor_history 
                     (timestamp, temperature, humidity, light, air_quality, noise)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                 (record_time, temp, humidity, light, air, noise))
    
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
    'canh_bao': 'TẮT',  # Mặc định TẮT, chỉ bật thủ công
    'timestamp': '',
    'device_status': 'online'
}

# Lịch sử dữ liệu cho biểu đồ - KHỞI TẠO RỖNG
history = {
    'time': [],
    'nhiet_do': [],
    'do_am': [],
    'anh_sang': [],
    'chat_luong_kk': [],
    'do_on': []
}

# Cài đặt hệ thống - KHỞI TẠO TỪ DATABASE
def load_system_settings():
    """Tải cài đặt từ database"""
    global system_settings
    
    conn = sqlite3.connect('classguard.db')
    c = conn.cursor()
    c.execute("SELECT * FROM thresholds WHERE id = 1")
    threshold = c.fetchone()
    conn.close()
    
    if threshold:
        system_settings = {
            'temp_min': threshold[1],
            'temp_max': threshold[2],
            'light_min': threshold[3],
            'air_max': threshold[4],
            'noise_max': threshold[5],
            'auto_mode': bool(threshold[6]),
            'audio_enabled': bool(threshold[7])
        }
    else:
        system_settings = {
            'temp_min': 20.0,
            'temp_max': 28.0,
            'light_min': 300.0,
            'air_max': 800,
            'noise_max': 70,
            'auto_mode': True,
            'audio_enabled': True
        }

# Khởi tạo system_settings
load_system_settings()

# Biến để theo dõi thời gian cập nhật
last_history_update = 0

# ========== HÀM KHỞI TẠO LỊCH SỬ ==========
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
    
    # Cập nhật dữ liệu demo nếu cần
    if sensor_data['device_status'] != 'online':
        update_demo_data()
    
    evaluation = evaluate_environment()
    
    # Cập nhật history nếu đã lâu
    if time.time() - last_history_update > 5:  # 5 giây
        update_history_from_db()
    
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
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Cập nhật dữ liệu demo nếu cần
    if sensor_data['device_status'] != 'online':
        update_demo_data()
    
    evaluation = evaluate_environment()
    
    # Cập nhật history từ database
    update_history_from_db()
    
    return jsonify({
        'success': True,
        'sensors': sensor_data,
        'evaluation': evaluation,
        'history': history,
        'settings': system_settings,
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

@app.route('/control', methods=['POST'])
def control():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if session['role'] not in ['admin', 'teacher']:
        return jsonify({'error': '❌ Không có quyền điều khiển!'}), 403
    
    data = request.json
    device = data.get('device')
    action = data.get('action')
    
    if not device or action not in ['BẬT', 'TẮT', 'MỞ', 'ĐÓNG']:
        return jsonify({'error': 'Thiếu thông tin'}), 400
    
    # KIỂM TRA CHẾ ĐỘ TỰ ĐỘNG
    if device != 'canh_bao' and system_settings['auto_mode']:
        return jsonify({'error': '⚠️ Hệ thống đang ở chế độ tự động. Tắt chế độ tự động để điều khiển thủ công.'}), 400
    
    # Cập nhật trạng thái
    sensor_data[device] = action
    
    # Tạo lệnh cho ESP32
    command_map = {
        'quat': {'BẬT': 'FAN_ON', 'TẮT': 'FAN_OFF'},
        'den': {'BẬT': 'LIGHT_ON', 'TẮT': 'LIGHT_OFF'},
        'cua_so': {'MỞ': 'WINDOW_OPEN', 'ĐÓNG': 'WINDOW_CLOSE'},
        'canh_bao': {'BẬT': 'ALARM_ON', 'TẮT': 'ALARM_OFF'}  # Cảnh báo luôn điều khiển được
    }
    
    if device in command_map and action in command_map[device]:
        esp_command = command_map[device][action]
        save_pending_command('ESP32-S3-CLASSGUARD', esp_command, '1')
    
    return jsonify({
        'success': True,
        'message': f'✅ Đã {action.lower()} {device}',
        'status': action
    })

@app.route('/update_settings', methods=['POST'])
def update_settings():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if session['role'] not in ['admin', 'teacher']:
        return jsonify({'error': '❌ Không có quyền cập nhật cài đặt!'}), 403
    
    try:
        data = request.json
        
        # Cập nhật biến toàn cục
        system_settings['auto_mode'] = data.get('auto_mode', system_settings['auto_mode'])
        system_settings['temp_min'] = float(data.get('temp_min', system_settings['temp_min']))
        system_settings['temp_max'] = float(data.get('temp_max', system_settings['temp_max']))
        system_settings['light_min'] = float(data.get('light_min', system_settings['light_min']))
        system_settings['noise_max'] = float(data.get('noise_max', system_settings['noise_max']))
        system_settings['air_max'] = float(data.get('air_max', system_settings['air_max']))
        
        # Lưu vào database thresholds
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        c.execute('''UPDATE thresholds SET 
                     temp_min = ?, temp_max = ?, light_min = ?,
                     air_max = ?, noise_max = ?, auto_mode = ?,
                     updated_at = CURRENT_TIMESTAMP
                     WHERE id = 1''',
                 (system_settings['temp_min'],
                  system_settings['temp_max'],
                  system_settings['light_min'],
                  system_settings['air_max'],
                  system_settings['noise_max'],
                  1 if system_settings['auto_mode'] else 0))
        conn.commit()
        conn.close()
        
        # Gửi lệnh thay đổi chế độ tự động cho ESP32
        if 'auto_mode' in data:
            command = 'AUTO_MODE_ON' if data['auto_mode'] else 'AUTO_MODE_OFF'
            save_pending_command('ESP32-S3-CLASSGUARD', command, '1')
        
        return jsonify({
            'success': True, 
            'message': '✅ Đã cập nhật cài đặt và đồng bộ với ESP32!'
        })
    except Exception as e:
        print(f"❌ Lỗi cập nhật settings: {e}")
        return jsonify({'error': '❌ Dữ liệu không hợp lệ!'}), 400

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

# ========== API CHO ESP32 ==========
@app.route('/api/esp32/data', methods=['POST'])
def receive_esp32_data():
    """API nhận dữ liệu từ ESP32 - TỐI ƯU TỐC ĐỘ <1s"""
    try:
        data = request.json
        print(f"📥 Nhận dữ liệu từ ESP32: {json.dumps(data, indent=2)}")
        
        with data_lock:
            # Cập nhật dữ liệu cảm biến
            sensor_data['nhiet_do'] = float(data.get('temperature', sensor_data['nhiet_do']))
            sensor_data['do_am'] = float(data.get('humidity', sensor_data['do_am']))
            sensor_data['anh_sang'] = int(data.get('light', sensor_data['anh_sang']))
            sensor_data['chat_luong_kk'] = int(data.get('air_quality', sensor_data['chat_luong_kk']))
            sensor_data['do_on'] = int(data.get('noise', sensor_data['do_on']))
            
            # Cập nhật trạng thái thiết bị
            if 'fan' in data:
                sensor_data['quat'] = 'BẬT' if data['fan'] == 1 else 'TẮT'
            if 'light_relay' in data:
                sensor_data['den'] = 'BẬT' if data['light_relay'] == 1 else 'TẮT'
            if 'alarm' in data:
                sensor_data['canh_bao'] = 'BẬT' if data['alarm'] == 1 else 'TẮT'
            if 'window' in data:
                sensor_data['cua_so'] = 'MỞ' if data['window'] == 1 else 'ĐÓNG'
                
            sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S")
            sensor_data['device_status'] = 'online'
        
        # Lưu vào database
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        c.execute('''INSERT INTO sensor_history 
                     (temperature, humidity, light, air_quality, noise)
                     VALUES (?, ?, ?, ?, ?)''',
                 (sensor_data['nhiet_do'], sensor_data['do_am'], 
                  sensor_data['anh_sang'], sensor_data['chat_luong_kk'],
                  sensor_data['do_on']))
        conn.commit()
        conn.close()
        
        # Cập nhật lịch sử
        update_history_from_db()
        
        # Kiểm tra cảnh báo (chỉ phát âm thanh, không điều khiển)
        alerts = check_alerts_only(data)
        
        # Điều khiển tự động (CHỈ 3 THIẾT BỊ: quạt, đèn, cửa)
        if system_settings['auto_mode']:
            auto_control_logic(sensor_data)
        
        # Tạo response với các audio commands nếu có cảnh báo
        audio_commands = []
        for alert in alerts:
            if 'audio_file' in alert and alert['audio_file']:
                audio_commands.append({'file': alert['audio_file']})
        
        # Lấy ngưỡng hiện tại từ database
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        c.execute("SELECT * FROM thresholds WHERE id = 1")
        threshold = c.fetchone()
        conn.close()
        
        response_data = {
            'success': True,
            'message': 'Đã nhận dữ liệu từ ESP32',
            'alerts': alerts,
            'thresholds': {
                'temp_min': system_settings['temp_min'],
                'temp_max': system_settings['temp_max'],
                'light_min': system_settings['light_min'],
                'air_max': system_settings['air_max'],
                'noise_max': system_settings['noise_max'],
                'auto_mode': system_settings['auto_mode'],
                'audio_enabled': True if threshold and threshold[7] == 1 else False
            },
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Thêm audio commands nếu có
        if audio_commands:
            response_data['audio_commands'] = audio_commands
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Lỗi nhận dữ liệu ESP32: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 400

@app.route('/api/esp32/control', methods=['GET'])
def get_esp32_control():
    """ESP32 lấy lệnh điều khiển từ web - TỐI ƯU TỐC ĐỘ"""
    device_id = request.args.get('device_id', 'ESP32-S3-CLASSGUARD')
    
    conn = sqlite3.connect('classguard.db')
    c = conn.cursor()
    c.execute('''SELECT id, command, value 
                 FROM pending_commands 
                 WHERE device_id = ? AND executed = 0 
                 ORDER BY created_at ASC 
                 LIMIT 1''', (device_id,))
    pending = c.fetchone()
    
    if pending:
        command_id, command, value = pending
        c.execute("UPDATE pending_commands SET executed = 1 WHERE id = ?", (command_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'command': command,
            'value': value,
            'command_id': command_id
        })
    
    conn.close()
    return jsonify({}), 204

@app.route('/api/esp32/ack', methods=['POST'])
def esp32_command_ack():
    """ESP32 xác nhận đã thực hiện lệnh"""
    try:
        data = request.json
        command_id = data.get('command_id')
        
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        c.execute("DELETE FROM pending_commands WHERE id = ?", (command_id,))
        conn.commit()
        conn.close()
        
        print(f"✅ ESP32 đã xác nhận lệnh: {command_id}")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/esp32/status', methods=['GET'])
def esp32_status():
    """Kiểm tra kết nối API"""
    return jsonify({
        'status': 'online',
        'server': 'classguard-web.onrender.com',
        'project': 'CLASSGUARD THCS',
        'version': '3.0',
        'auto_mode': system_settings['auto_mode'],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/esp32/thresholds', methods=['GET'])
def get_thresholds():
    """API cung cấp ngưỡng cho ESP32 - ĐỒNG BỘ"""
    try:
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        c.execute("SELECT * FROM thresholds WHERE id = 1")
        threshold = c.fetchone()
        conn.close()
        
        if threshold:
            return jsonify({
                'success': True,
                'temp_min': threshold[1],
                'temp_max': threshold[2],
                'light_min': threshold[3],
                'air_max': threshold[4],
                'noise_max': threshold[5],
                'auto_mode': bool(threshold[6]),
                'audio_enabled': bool(threshold[7])
            })
        else:
            return jsonify({
                'success': True,
                'temp_min': 20.0,
                'temp_max': 28.0,
                'light_min': 300.0,
                'air_max': 800,
                'noise_max': 70,
                'auto_mode': True,
                'audio_enabled': True
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'temp_min': 20.0,
            'temp_max': 28.0,
            'light_min': 300.0,
            'air_max': 800,
            'noise_max': 70,
            'auto_mode': True,
            'audio_enabled': True
        })

@app.route('/api/esp32/update_thresholds', methods=['POST'])
def update_thresholds():
    """ESP32 gửi yêu cầu cập nhật ngưỡng"""
    try:
        data = request.json
        
        conn = sqlite3.connect('classguard.db')
        c = conn.cursor()
        
        c.execute('''UPDATE thresholds SET 
                     temp_min = ?, temp_max = ?, light_min = ?,
                     air_max = ?, noise_max = ?, auto_mode = ?,
                     audio_enabled = ?, updated_at = CURRENT_TIMESTAMP
                     WHERE id = 1''',
                 (data.get('temp_min', 20.0),
                  data.get('temp_max', 28.0),
                  data.get('light_min', 300.0),
                  data.get('air_max', 800),
                  data.get('noise_max', 70),
                  data.get('auto_mode', True),
                  data.get('audio_enabled', True)))
        
        conn.commit()
        conn.close()
        
        # Cập nhật biến toàn cục
        system_settings['temp_min'] = data.get('temp_min', 20.0)
        system_settings['temp_max'] = data.get('temp_max', 28.0)
        system_settings['light_min'] = data.get('light_min', 300.0)
        system_settings['air_max'] = data.get('air_max', 800)
        system_settings['noise_max'] = data.get('noise_max', 70)
        system_settings['auto_mode'] = data.get('auto_mode', True)
        
        return jsonify({'success': True, 'message': 'Đã cập nhật ngưỡng'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ========== HÀM HỖ TRỢ ==========
def evaluate_environment():
    """Đánh giá môi trường lớp học theo ngưỡng chính xác"""
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

def update_demo_data():
    """Cập nhật dữ liệu demo"""
    if sensor_data['device_status'] == 'online':
        return
    
    sensor_data['nhiet_do'] = round(24 + random.random() * 4, 1)
    sensor_data['do_am'] = round(50 + random.random() * 20, 1)
    sensor_data['anh_sang'] = round(200 + random.random() * 300)
    sensor_data['chat_luong_kk'] = round(200 + random.random() * 600)
    sensor_data['do_on'] = round(30 + random.random() * 50)
    sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S")
    
    if system_settings['auto_mode']:
        auto_control_logic(sensor_data)
    
    # Lưu demo vào database
    conn = sqlite3.connect('classguard.db')
    c = conn.cursor()
    c.execute('''INSERT INTO sensor_history 
                 (temperature, humidity, light, air_quality, noise)
                 VALUES (?, ?, ?, ?, ?)''',
             (sensor_data['nhiet_do'], sensor_data['do_am'], 
              sensor_data['anh_sang'], sensor_data['chat_luong_kk'],
              sensor_data['do_on']))
    conn.commit()
    conn.close()
    
    update_history_from_db()

def auto_control_logic(data):
    """Logic điều khiển tự động - CHỈ 3 THIẾT BỊ (quạt, đèn, cửa)"""
    temp = data.get('nhiet_do', sensor_data['nhiet_do'])
    light = data.get('anh_sang', sensor_data['anh_sang'])
    air = data.get('chat_luong_kk', sensor_data['chat_luong_kk'])
    
    # Nhiệt độ - chỉ điều khiển quạt
    if temp > system_settings['temp_max']:
        if sensor_data['quat'] != 'BẬT':
            sensor_data['quat'] = 'BẬT'
            save_pending_command('ESP32-S3-CLASSGUARD', 'FAN_ON', '1')
            print(f"🤖 Tự động BẬT quạt (nhiệt độ: {temp:.1f}°C > {system_settings['temp_max']}°C)")
    elif temp < system_settings['temp_min']:
        if sensor_data['quat'] != 'TẮT':
            sensor_data['quat'] = 'TẮT'
            save_pending_command('ESP32-S3-CLASSGUARD', 'FAN_OFF', '0')
            print(f"🤖 Tự động TẮT quạt (nhiệt độ: {temp:.1f}°C < {system_settings['temp_min']}°C)")
    
    # Ánh sáng - chỉ điều khiển đèn
    if light < system_settings['light_min']:
        if sensor_data['den'] != 'BẬT':
            sensor_data['den'] = 'BẬT'
            save_pending_command('ESP32-S3-CLASSGUARD', 'LIGHT_ON', '1')
            print(f"🤖 Tự động BẬT đèn (ánh sáng: {light} lux < {system_settings['light_min']} lux)")
    else:
        if sensor_data['den'] != 'TẮT':
            sensor_data['den'] = 'TẮT'
            save_pending_command('ESP32-S3-CLASSGUARD', 'LIGHT_OFF', '0')
            print(f"🤖 Tự động TẮT đèn (ánh sáng: {light} lux >= {system_settings['light_min']} lux)")
    
    # Chất lượng không khí - chỉ điều khiển cửa sổ
    if air > system_settings['air_max']:
        if sensor_data['cua_so'] != 'MỞ':
            sensor_data['cua_so'] = 'MỞ'
            save_pending_command('ESP32-S3-CLASSGUARD', 'WINDOW_OPEN', '1')
            print(f"🤖 Tự động MỞ cửa (chất lượng KK: {air} ppm > {system_settings['air_max']} ppm)")
    else:
        if sensor_data['cua_so'] != 'ĐÓNG':
            sensor_data['cua_so'] = 'ĐÓNG'
            save_pending_command('ESP32-S3-CLASSGUARD', 'WINDOW_CLOSE', '0')
            print(f"🤖 Tự động ĐÓNG cửa (chất lượng KK: {air} ppm <= {system_settings['air_max']} ppm)")
    
    # Độ ồn - KHÔNG tự động điều khiển cảnh báo
    # Cảnh báo chỉ được bật/tắt thủ công từ web

def update_history_from_db():
    """Cập nhật history từ database"""
    global last_history_update
    
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

def check_alerts_only(data):
    """Chỉ kiểm tra và phát cảnh báo, không điều khiển thiết bị"""
    alerts = []
    
    temp = data.get('temperature', sensor_data['nhiet_do'])
    air = data.get('air_quality', sensor_data['chat_luong_kk'])
    noise = data.get('noise', sensor_data['do_on'])
    light = data.get('light', sensor_data['anh_sang'])
    
    # Tính ngưỡng cảnh báo
    temp_alert_threshold = system_settings['temp_max'] + 2  # 30°C nếu max=28
    air_alert_threshold = 1000  # ppm
    noise_alert_threshold = system_settings['noise_max'] + 10  # 80dB nếu max=70
    light_alert_threshold = 200  # lux
    
    # Kiểm tra cảnh báo NGUY HIỂM (phát âm thanh)
    if temp > temp_alert_threshold:
        alerts.append({
            'type': 'danger', 
            'message': f'⚠️ Nhiệt độ quá cao ({temp:.1f}°C > {temp_alert_threshold}°C)', 
            'audio_file': '03.mp3'
        })
    elif temp > system_settings['temp_max']:
        alerts.append({
            'type': 'warning', 
            'message': f'🌡️ Nhiệt độ hơi cao ({temp:.1f}°C > {system_settings["temp_max"]}°C)', 
            'audio_file': ''
        })
    
    if air > air_alert_threshold:
        alerts.append({
            'type': 'danger', 
            'message': f'⚠️ Chất lượng không khí kém ({air} ppm > {air_alert_threshold} ppm)', 
            'audio_file': '04.mp3'
        })
    elif air > 800:
        alerts.append({
            'type': 'warning', 
            'message': f'💨 Chất lượng không khí trung bình ({air} ppm > 800 ppm)', 
            'audio_file': ''
        })
    
    if noise > noise_alert_threshold:
        alerts.append({
            'type': 'danger', 
            'message': f'⚠️ Độ ồn quá cao ({noise} dB > {noise_alert_threshold} dB)', 
            'audio_file': '05.mp3'
        })
    elif noise > system_settings['noise_max']:
        alerts.append({
            'type': 'warning', 
            'message': f'🔊 Độ ồn hơi cao ({noise} dB > {system_settings["noise_max"]} dB)', 
            'audio_file': ''
        })
    
    if light < light_alert_threshold:
        alerts.append({
            'type': 'danger', 
            'message': f'⚠️ Ánh sáng quá yếu ({light} lux < {light_alert_threshold} lux)', 
            'audio_file': '06.mp3'
        })
    elif light < 300:
        alerts.append({
            'type': 'warning', 
            'message': f'☀️ Ánh sáng hơi yếu ({light} lux < 300 lux)', 
            'audio_file': ''
        })
    
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
    print("=" * 60)
    print("🚀 CLASSGUARD Web Server - Phiên bản 3.0")
    print("📊 Hệ thống đã được ĐỒNG BỘ HOÀN TOÀN với ESP32!")
    print("⚡ Tốc độ giao tiếp: <1 giây")
    print("🔧 Cảnh báo: TÁCH RIÊNG khỏi chế độ tự động")
    print("🌐 URL: http://localhost:5000")
    print("📡 API ESP32: http://localhost:5000/api/esp32/data")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
