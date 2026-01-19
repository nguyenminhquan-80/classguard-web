from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
import paho.mqtt.client as mqtt
import random
from datetime import datetime, timedelta
import json
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'classguard_pro_2024_vietnam'
app.secret_key = 'classguard_pro_2024_vietnam'

# ========== TÀI KHOẢN ==========
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin', 'name': 'Quản trị viên'},
    'giaovien': {'password': 'giaovien123', 'role': 'teacher', 'name': 'Giáo viên'},
    'hocsinh': {'password': 'hocsinh123', 'role': 'student', 'name': 'Học sinh'},
    'xem': {'password': 'xem123', 'role': 'viewer', 'name': 'Khách xem'}
}

# ========== DỮ LIỆU HỆ THỐNG ==========
sensor_data = {
    'nhiet_do': 27.5,
    'do_am': 65.2,
    'anh_sang': 450,
    'chat_luong_kk': 350,
    'do_on': 45,
    'quat': 'TẮT',
    'den': 'BẬT',
    'cua_so': 'ĐÓNG',
    'timestamp': '',
    'danh_gia': 'TỐT'
}

# Lịch sử dữ liệu cho biểu đồ
history_data = {
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
    'temp_threshold': {'min': 20, 'max': 28},
    'light_threshold': 300,
    'noise_threshold': 70,
    'air_threshold': 800
}

# ========== MQTT CLIENT ==========
mqtt_client = None
mqtt_connected = False

def setup_mqtt():
    global mqtt_client, mqtt_connected
    try:
        mqtt_client = mqtt.Client()
        mqtt_client.on_connect = on_mqtt_connect
        mqtt_client.on_message = on_mqtt_message
        mqtt_client.connect("broker.hivemq.com", 1883, 60)
        mqtt_client.loop_start()
        mqtt_client.subscribe("classguard/sensors")
        print("MQTT Client initialized")
    except Exception as e:
        print(f"MQTT setup error: {e}")
        mqtt_client = None

def on_mqtt_connect(client, userdata, flags, rc):
    global mqtt_connected
    mqtt_connected = True
    print("Connected to MQTT Broker")

def on_mqtt_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        update_sensor_data_from_mqtt(data)
    except:
        pass

def update_sensor_data_from_mqtt(data):
    """Cập nhật dữ liệu từ MQTT (ESP32)"""
    sensor_data.update(data)
    sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    # Thêm vào lịch sử
    now = datetime.now()
    if len(history_data['time']) > 50:
        for key in history_data:
            if history_data[key]:
                history_data[key].pop(0)
    
    history_data['time'].append(now.strftime("%H:%M:%S"))
    history_data['nhiet_do'].append(sensor_data.get('nhiet_do', 0))
    history_data['do_am'].append(sensor_data.get('do_am', 0))
    history_data['anh_sang'].append(sensor_data.get('anh_sang', 0))
    history_data['chat_luong_kk'].append(sensor_data.get('chat_luong_kk', 0))
    history_data['do_on'].append(sensor_data.get('do_on', 0))
    
    # Tự động điều khiển
    if system_settings['auto_mode']:
        auto_control()

def auto_control():
    """Tự động điều khiển thiết bị"""
    # Nhiệt độ
    if sensor_data['nhiet_do'] > system_settings['temp_threshold']['max']:
        send_control_command('quat', 'BẬT')
    elif sensor_data['nhiet_do'] < system_settings['temp_threshold']['min']:
        send_control_command('quat', 'TẮT')
    
    # Ánh sáng
    if sensor_data['anh_sang'] < system_settings['light_threshold']:
        send_control_command('den', 'BẬT')
    else:
        send_control_command('den', 'TẮT')
    
    # Chất lượng không khí
    if sensor_data['chat_luong_kk'] > system_settings['air_threshold']:
        send_control_command('cua_so', 'MỞ')
    else:
        send_control_command('cua_so', 'ĐÓNG')

def send_control_command(device, action):
    """Gửi lệnh điều khiển qua MQTT"""
    if mqtt_client and mqtt_connected:
        command = json.dumps({'device': device, 'action': action.lower()})
        mqtt_client.publish("classguard/control", command)
    
    # Cập nhật trạng thái
    sensor_data[device] = action

# ========== HÀM ĐÁNH GIÁ ==========
def evaluate_environment():
    """Đánh giá môi trường học tập"""
    score = 0
    evaluations = []
    
    # Nhiệt độ (20-28°C là lý tưởng)
    temp = sensor_data['nhiet_do']
    if 20 <= temp <= 28:
        score += 2
        evaluations.append(('🌡️ Nhiệt độ', 'Lý tưởng', 'success'))
    elif 18 <= temp < 20 or 28 < temp <= 30:
        score += 1
        evaluations.append(('🌡️ Nhiệt độ', 'Chấp nhận được', 'warning'))
    else:
        evaluations.append(('🌡️ Nhiệt độ', 'Không phù hợp', 'danger'))
    
    # Độ ẩm (40-70% là tốt)
    humidity = sensor_data['do_am']
    if 40 <= humidity <= 70:
        score += 2
        evaluations.append(('💧 Độ ẩm', 'Tốt', 'success'))
    elif 30 <= humidity < 40 or 70 < humidity <= 80:
        score += 1
        evaluations.append(('💧 Độ ẩm', 'Trung bình', 'warning'))
    else:
        evaluations.append(('💧 Độ ẩm', 'Khô/Ẩm quá', 'danger'))
    
    # Ánh sáng (>300 lux là tốt)
    light = sensor_data['anh_sang']
    if light >= 300:
        score += 2
        evaluations.append(('☀️ Ánh sáng', 'Đủ sáng', 'success'))
    elif 200 <= light < 300:
        score += 1
        evaluations.append(('☀️ Ánh sáng', 'Hơi tối', 'warning'))
    else:
        evaluations.append(('☀️ Ánh sáng', 'Thiếu sáng', 'danger'))
    
    # Chất lượng không khí (<400 PPM là tốt)
    air = sensor_data['chat_luong_kk']
    if air < 400:
        score += 2
        evaluations.append(('💨 Chất lượng KK', 'Trong lành', 'success'))
    elif 400 <= air < 800:
        score += 1
        evaluations.append(('💨 Chất lượng KK', 'Trung bình', 'warning'))
    else:
        evaluations.append(('💨 Chất lượng KK', 'Ô nhiễm', 'danger'))
    
    # Độ ồn (<50 dB là tốt)
    noise = sensor_data['do_on']
    if noise < 50:
        score += 2
        evaluations.append(('🔊 Độ ồn', 'Yên tĩnh', 'success'))
    elif 50 <= noise < 70:
        score += 1
        evaluations.append(('🔊 Độ ồn', 'Bình thường', 'warning'))
    else:
        evaluations.append(('🔊 Độ ồn', 'Ồn ào', 'danger'))
    
    # Đánh giá tổng thể
    max_score = 10
    percentage = (score / max_score) * 100
    
    if percentage >= 80:
        overall = 'TỐT'
        overall_class = 'success'
        advice = 'Môi trường học tập lý tưởng!'
    elif percentage >= 60:
        overall = 'KHÁ'
        overall_class = 'warning'
        advice = 'Môi trường học tập chấp nhận được.'
    else:
        overall = 'CẦN CẢI THIỆN'
        overall_class = 'danger'
        advice = 'Cần điều chỉnh môi trường học tập.'
    
    sensor_data['danh_gia'] = overall
    
    return {
        'score': score,
        'percentage': percentage,
        'overall': overall,
        'overall_class': overall_class,
        'advice': advice,
        'evaluations': evaluations
    }

# ========== ROUTES ==========
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
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
            
            # Ghi log đăng nhập
            print(f"User {username} logged in at {session['login_time']}")
            
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', 
                                 error="🔐 Tên đăng nhập hoặc mật khẩu không đúng!")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.get('username', 'Unknown')
    session.clear()
    print(f"User {username} logged out")
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Cập nhật dữ liệu demo nếu không có MQTT
    if not mqtt_connected:
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
    
    # Cập nhật dữ liệu demo
    if not mqtt_connected:
        update_demo_data()
    
    evaluation = evaluate_environment()
    
    return jsonify({
        'sensors': sensor_data,
        'evaluation': evaluation,
        'history': history_data
    })

@app.route('/control', methods=['POST'])
def control():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if session['role'] not in ['admin', 'teacher']:
        return jsonify({'error': 'Không có quyền điều khiển!'}), 403
    
    data = request.json
    device = data.get('device')
    action = data.get('action')
    
    if device and action:
        send_control_command(device, action)
        
        # Ghi log
        print(f"User {session['username']} {action} {device}")
        
        return jsonify({
            'success': True,
            'message': f'Đã {action.lower()} {device}',
            'status': action
        })
    
    return jsonify({'error': 'Thiếu thông tin'}), 400

@app.route('/data')
def data_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Tạo dữ liệu lịch sử
    data_list = []
    base_time = datetime.now()
    
    for i in range(100):
        record_time = base_time - timedelta(minutes=i)
        data_list.append({
            'time': record_time.strftime("%H:%M:%S"),
            'date': record_time.strftime("%d/%m/%Y"),
            'nhiet_do': round(24 + random.random() * 4, 1),
            'do_am': round(55 + random.random() * 20, 1),
            'anh_sang': round(250 + random.random() * 250),
            'chat_luong_kk': round(300 + random.random() * 500),
            'do_on': round(35 + random.random() * 40)
        })
    
    return render_template('data.html',
                         data=data_list,
                         role=session['role'])

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['role'] not in ['admin', 'teacher']:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Cập nhật cài đặt
        system_settings['auto_mode'] = request.form.get('auto_mode') == 'on'
        system_settings['temp_threshold']['min'] = float(request.form.get('temp_min', 20))
        system_settings['temp_threshold']['max'] = float(request.form.get('temp_max', 28))
        system_settings['light_threshold'] = float(request.form.get('light_threshold', 300))
        system_settings['noise_threshold'] = float(request.form.get('noise_threshold', 70))
        system_settings['air_threshold'] = float(request.form.get('air_threshold', 800))
        
        return jsonify({'success': True, 'message': 'Đã cập nhật cài đặt!'})
    
    return render_template('settings.html',
                         settings=system_settings,
                         role=session['role'])

@app.route('/report')
def report_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    evaluation = evaluate_environment()
    
    # Tạo dữ liệu báo cáo
    report_data = {
        'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'user': session['name'],
        'role': session['role'],
        'sensors': sensor_data,
        'evaluation': evaluation,
        'settings': system_settings,
        'history_count': len(history_data['time'])
    }
    
    return render_template('report.html',
                         report=report_data,
                         role=session['role'])

@app.route('/export_report')
def export_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Tạo báo cáo văn bản đơn giản
    evaluation = evaluate_environment()
    
    report_text = f"""
CLASSGUARD - BÁO CÁO MÔI TRƯỜNG LỚP HỌC
Thời gian: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
Người xuất: {session.get('name', 'Unknown')}
Vai trò: {session.get('role', 'Unknown')}

=== THÔNG SỐ CẢM BIẾN ===
🌡️ Nhiệt độ: {sensor_data['nhiet_do']} °C
💧 Độ ẩm: {sensor_data['do_am']} %
☀️ Ánh sáng: {sensor_data['anh_sang']} lux
💨 Chất lượng KK: {sensor_data['chat_luong_kk']} PPM
🔊 Độ ồn: {sensor_data['do_on']} dB

=== TRẠNG THÁI THIẾT BỊ ===
🌀 Quạt: {sensor_data['quat']}
💡 Đèn: {sensor_data['den']}
🚪 Cửa sổ: {sensor_data['cua_so']}

=== ĐÁNH GIÁ TỔNG THỂ ===
Điểm số: {evaluation['score']}/10 ({evaluation['percentage']:.1f}%)
Xếp hạng: {evaluation['overall']}
Khuyến nghị: {evaluation['advice']}

=== ĐÁNH GIÁ CHI TIẾT ===
"""
    
    for item in evaluation['evaluations']:
        report_text += f"{item[0]}: {item[1]}\n"
    
    # Trả về dạng text
    return Response(
        report_text,
        mimetype="text/plain",
        headers={"Content-disposition": f"attachment; filename=classguard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"}
    )

def update_demo_data():
    """Cập nhật dữ liệu demo (khi không có ESP32)"""
    # Tạo biến động cho dữ liệu
    sensor_data['nhiet_do'] = round(24 + random.random() * 5, 1)
    sensor_data['do_am'] = round(50 + random.random() * 25, 1)
    sensor_data['anh_sang'] = round(200 + random.random() * 400)
    sensor_data['chat_luong_kk'] = round(200 + random.random() * 600)
    sensor_data['do_on'] = round(30 + random.random() * 50)
    sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    # Thêm vào lịch sử
    now = datetime.now()
    if len(history_data['time']) > 50:
        for key in history_data:
            if history_data[key]:
                history_data[key].pop(0)
    
    history_data['time'].append(now.strftime("%H:%M:%S"))
    history_data['nhiet_do'].append(sensor_data['nhiet_do'])
    history_data['do_am'].append(sensor_data['do_am'])
    history_data['anh_sang'].append(sensor_data['anh_sang'])
    history_data['chat_luong_kk'].append(sensor_data['chat_luong_kk'])
    history_data['do_on'].append(sensor_data['do_on'])

# ========== KHỞI TẠO ==========
def initialize_app():
    # Khởi tạo MQTT
    setup_mqtt()
    
    # Khởi tạo dữ liệu demo
    for _ in range(20):
        update_demo_data()
    
    print("=" * 50)
    print("CLASSGUARD SYSTEM INITIALIZED SUCCESSFULLY")
    print(f"Web URL: https://classguard-web.onrender.com")
    print(f"MQTT Status: {'Connected' if mqtt_connected else 'Demo Mode'}")
    print("=" * 50)

# Chạy khởi tạo
initialize_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
