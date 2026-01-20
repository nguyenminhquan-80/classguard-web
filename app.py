from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
import random
from datetime import datetime, timedelta
import json
import csv
import io
import sqlite3
from threading import Lock

app = Flask(__name__)
app.config['SECRET_KEY'] = 'classguard_final_v3_2024'
app.secret_key = 'classguard_final_v3_2024'

# ========== CẤU HÌNH DATABASE ==========
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
    
    # Bảng cảm biến (lưu lịch sử)
    c.execute('''CREATE TABLE IF NOT EXISTS sensor_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  temperature REAL,
                  humidity REAL,
                  light INTEGER,
                  air_quality INTEGER,
                  noise INTEGER)''')
    
    # Bảng thiết bị điều khiển
    c.execute('''CREATE TABLE IF NOT EXISTS device_control
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  device_name TEXT,
                  status TEXT,
                  command_time DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Bảng lệnh chờ cho ESP32
    c.execute('''CREATE TABLE IF NOT EXISTS pending_commands
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  device_id TEXT,
                  command TEXT,
                  value TEXT,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  executed INTEGER DEFAULT 0)''')
    
    # Thêm tài khoản mẫu nếu chưa có
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
    'air_max': 800
}

# Lưu lệnh chờ cho ESP32
esp32_commands = {}

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
            session['role'] = user[3]  # role
            session['name'] = user[4]  # name
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
    
    update_demo_data()
    evaluation = evaluate_environment()
    
    return render_template('dashboard.html',
                         data=sensor_data,
                         evaluation=evaluation,
                         settings=system_settings,
                         username=session['username'],
                         name=session['name'],
                         role=session['role'],
                         login_time=session.get('login_time', ''))

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
        'settings': system_settings
    })

@app.route('/control', methods=['POST'])
def control():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # CHỈNH SỬA PHÂN QUYỀN: Cho phép admin và teacher điều khiển
    if session['role'] not in ['admin', 'teacher']:
        return jsonify({'error': '❌ Không có quyền điều khiển!'}), 403
    
    data = request.json
    device = data.get('device')
    action = data.get('action')
    
    if not device or action not in ['BẬT', 'TẮT', 'MỞ', 'ĐÓNG']:
        return jsonify({'error': 'Thiếu thông tin'}), 400
    
    # Nếu đang ở chế độ tự động và cố gắng điều khiển thủ công
    if system_settings['auto_mode']:
        # Vẫn cho phép điều khiển nhưng sẽ hiển thị cảnh báo
        # Thay vì từ chối
        pass
    
    # Cập nhật trạng thái
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
        system_settings['auto_mode'] = data.get('auto_mode', system_settings['auto_mode'])
        system_settings['temp_min'] = float(data.get('temp_min', system_settings['temp_min']))
        system_settings['temp_max'] = float(data.get('temp_max', system_settings['temp_max']))
        system_settings['light_min'] = float(data.get('light_min', system_settings['light_min']))
        system_settings['noise_max'] = float(data.get('noise_max', system_settings['noise_max']))
        system_settings['air_max'] = float(data.get('air_max', system_settings['air_max']))
        
        return jsonify({'success': True, 'message': '✅ Đã cập nhật cài đặt!'})
    except:
        return jsonify({'error': '❌ Dữ liệu không hợp lệ!'}), 400

# ========== CÁC TRANG KHÁC ==========
@app.route('/data')
def data_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Lấy dữ liệu từ database
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
        temp, humidity, light, air, noise = record[1:6]
        
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
            'thoi_gian': datetime.strptime(record[0], '%Y-%m-%d %H:%M:%S').strftime("%H:%M"),
            'ngay': datetime.strptime(record[0], '%Y-%m-%d %H:%M:%S').strftime("%d/%m/%Y"),
            'nhiet_do': temp,
            'do_am': humidity,
            'anh_sang': light,
            'chat_luong_kk': air,
            'do_on': noise,
            'danh_gia': eval_text,
            'danh_gia_color': eval_color
        })
    
    return render_template('data.html',
                         data=data_list,
                         role=session['role'])

@app.route('/settings', methods=['GET', 'POST'])
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
    """API nhận dữ liệu từ ESP32"""
    try:
        data = request.json
        print(f"📥 Nhận dữ liệu từ ESP32: {data}")
        
        # Cập nhật dữ liệu cảm biến
        with data_lock:
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
            if 'alarm' in data:
                sensor_data['canh_bao'] = 'BẬT' if data['alarm'] == 1 else 'TẮT'
            
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
        
        # Cập nhật lịch sử cho biểu đồ
        update_history()
        
        # Kiểm tra cảnh báo
        alerts = check_esp32_alerts(data)
        
        # Kiểm tra và thực hiện điều khiển tự động
        if system_settings['auto_mode']:
            auto_control_logic(data)
        
        return jsonify({
            'success': True,
            'message': 'Đã nhận dữ liệu từ ESP32',
            'alerts': alerts,
            'thresholds': system_settings,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        print(f"❌ Lỗi nhận dữ liệu ESP32: {e}")
        return jsonify({'error': str(e), 'success': False}), 400

@app.route('/api/esp32/control', methods=['GET'])
def get_esp32_control():
    """ESP32 lấy lệnh điều khiển từ web"""
    device_id = request.args.get('device_id', 'ESP32-S3-CLASSGUARD')
    
    # Lấy lệnh chờ từ database
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
        # Đánh dấu là đang xử lý
        c.execute("UPDATE pending_commands SET executed = 1 WHERE id = ?", (command_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'command': command,
            'value': value,
            'command_id': command_id
        })
    
    conn.close()
    return jsonify({}), 204  # 204 No Content

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
        'version': '2.0',
        'auto_mode': system_settings['auto_mode'],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# ========== HÀM PHỤ TRỢ ==========
def evaluate_environment():
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
    """Cập nhật dữ liệu demo khi không có ESP32"""
    if sensor_data['device_status'] == 'online':
        return  # Không cập nhật demo nếu ESP32 đang online
    
    # Thêm biến động ngẫu nhiên
    sensor_data['nhiet_do'] = round(24 + random.random() * 4, 1)
    sensor_data['do_am'] = round(50 + random.random() * 20, 1)
    sensor_data['anh_sang'] = round(200 + random.random() * 300)
    sensor_data['chat_luong_kk'] = round(200 + random.random() * 600)
    sensor_data['do_on'] = round(30 + random.random() * 50)
    sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S")
    
    # Tự động điều khiển nếu chế độ tự động bật
    if system_settings['auto_mode']:
        auto_control_logic(sensor_data)
    
    # Cập nhật history
    update_history()

def auto_control_logic(data):
    """Logic điều khiển tự động"""
    temp = data.get('temperature', sensor_data['nhiet_do'])
    light = data.get('light', sensor_data['anh_sang'])
    air = data.get('air_quality', sensor_data['chat_luong_kk'])
    noise = data.get('noise', sensor_data['do_on'])
    
    # Nhiệt độ
    if temp > system_settings['temp_max']:
        save_pending_command('ESP32-S3-CLASSGUARD', 'FAN_ON', '1')
        sensor_data['quat'] = 'BẬT'
    elif temp < system_settings['temp_min']:
        save_pending_command('ESP32-S3-CLASSGUARD', 'FAN_OFF', '0')
        sensor_data['quat'] = 'TẮT'
    
    # Ánh sáng
    if light < system_settings['light_min']:
        save_pending_command('ESP32-S3-CLASSGUARD', 'LIGHT_ON', '1')
        sensor_data['den'] = 'BẬT'
    else:
        save_pending_command('ESP32-S3-CLASSGUARD', 'LIGHT_OFF', '0')
        sensor_data['den'] = 'TẮT'
    
    # Chất lượng không khí
    if air > system_settings['air_max']:
        sensor_data['cua_so'] = 'MỞ'
        # Không có relay cửa sổ thực tế
    else:
        sensor_data['cua_so'] = 'ĐÓNG'
    
    # Độ ồn
    if noise > system_settings['noise_max']:
        save_pending_command('ESP32-S3-CLASSGUARD', 'ALARM_ON', '1')
        sensor_data['canh_bao'] = 'BẬT'
    else:
        save_pending_command('ESP32-S3-CLASSGUARD', 'ALARM_OFF', '0')
        sensor_data['canh_bao'] = 'TẮT'

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

def check_esp32_alerts(data):
    """Kiểm tra cảnh báo từ dữ liệu ESP32"""
    alerts = []
    
    temp = data.get('temperature', 25)
    air = data.get('air_quality', 400)
    noise = data.get('noise', 45)
    light = data.get('light', 300)
    
    if temp > 30:
        alerts.append({'type': 'danger', 'message': '⚠️ Nhiệt độ quá cao (>30°C)'})
    elif temp > 28:
        alerts.append({'type': 'warning', 'message': '🌡️ Nhiệt độ hơi cao (>28°C)'})
    
    if air > 1000:
        alerts.append({'type': 'danger', 'message': '⚠️ Chất lượng không khí kém (>1000 PPM)'})
    elif air > 800:
        alerts.append({'type': 'warning', 'message': '💨 Chất lượng không khí trung bình (>800 PPM)'})
    
    if noise > 80:
        alerts.append({'type': 'danger', 'message': '⚠️ Độ ồn quá cao (>80 dB)'})
    elif noise > 70:
        alerts.append({'type': 'warning', 'message': '🔊 Độ ồn hơi cao (>70 dB)'})
    
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

# Chạy server
if __name__ == '__main__':
    print("🚀 CLASSGUARD Web Server đang khởi động...")
    print("📊 Database đã được khởi tạo")
    print("🌐 Web URL: http://localhost:5000")
    print("📡 API Endpoint cho ESP32: http://localhost:5000/api/esp32/data")
    app.run(debug=True, host='0.0.0.0', port=5000)
