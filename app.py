from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response, send_file
import paho.mqtt.client as mqtt
import random
from datetime import datetime, timedelta
import json
import csv
import io
from io import BytesIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'classguard_pro_2024_vietnam_secure'
app.secret_key = 'classguard_pro_2024_vietnam_secure'

# ========== TÀI KHOẢN & PHÂN QUYỀN ==========
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
    'canh_bao': 'TẮT',
    'timestamp': ''
}

# Lịch sử dữ liệu
history_data = {key: [] for key in sensor_data.keys() if key not in ['timestamp']}
history_data['time'] = []

# Cài đặt hệ thống
system_settings = {
    'auto_mode': True,
    'temp_min': 20,
    'temp_max': 28,
    'light_min': 300,
    'noise_max': 70,
    'air_max': 800
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
        print("✅ MQTT Client initialized")
    except Exception as e:
        print(f"⚠️ MQTT setup error: {e}")
        mqtt_client = None

def on_mqtt_connect(client, userdata, flags, rc):
    global mqtt_connected
    mqtt_connected = True
    print("✅ Connected to MQTT Broker")

def on_mqtt_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        update_sensor_data_from_mqtt(data)
    except:
        pass

def update_sensor_data_from_mqtt(data):
    sensor_data.update(data)
    sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    # Thêm vào lịch sử
    update_history()
    
    # Tự động điều khiển
    if system_settings['auto_mode']:
        auto_control()

def auto_control():
    """Tự động điều khiển thiết bị"""
    # Nhiệt độ
    if sensor_data['nhiet_do'] > system_settings['temp_max']:
        send_control_command('quat', 'BẬT')
    elif sensor_data['nhiet_do'] < system_settings['temp_min']:
        send_control_command('quat', 'TẮT')
    
    # Ánh sáng
    if sensor_data['anh_sang'] < system_settings['light_min']:
        send_control_command('den', 'BẬT')
    else:
        send_control_command('den', 'TẮT')
    
    # Chất lượng không khí
    if sensor_data['chat_luong_kk'] > system_settings['air_max']:
        send_control_command('cua_so', 'MỞ')
    else:
        send_control_command('cua_so', 'ĐÓNG')
    
    # Độ ồn
    if sensor_data['do_on'] > system_settings['noise_max']:
        send_control_command('canh_bao', 'BẬT')
    else:
        send_control_command('canh_bao', 'TẮT')

def send_control_command(device, action):
    """Gửi lệnh điều khiển"""
    if mqtt_client and mqtt_connected:
        command = json.dumps({'device': device, 'action': action.lower()})
        mqtt_client.publish("classguard/control", command)
    
    # Cập nhật trạng thái
    sensor_data[device] = action
    print(f"📡 Control: {device} -> {action}")

def update_history():
    """Cập nhật lịch sử dữ liệu"""
    now = datetime.now()
    
    # Giữ tối đa 50 bản ghi
    if len(history_data['time']) >= 50:
        for key in history_data:
            if history_data[key]:
                history_data[key].pop(0)
    
    # Thêm dữ liệu mới
    history_data['time'].append(now.strftime("%H:%M:%S"))
    for key in sensor_data:
        if key in history_data and key != 'timestamp':
            history_data[key].append(sensor_data[key])

# ========== HÀM ĐÁNH GIÁ ==========
def evaluate_environment():
    """Đánh giá môi trường học tập"""
    evaluations = []
    scores = []
    
    # Nhiệt độ (20-28°C là tốt)
    temp = sensor_data['nhiet_do']
    if 20 <= temp <= 28:
        evaluations.append(('🌡️ Nhiệt độ', 'Lý tưởng', 'success', 'Tốt cho học tập'))
        scores.append(2)
    elif 18 <= temp < 20 or 28 < temp <= 30:
        evaluations.append(('🌡️ Nhiệt độ', 'Chấp nhận', 'warning', 'Có thể gây khó chịu'))
        scores.append(1)
    else:
        evaluations.append(('🌡️ Nhiệt độ', 'Không tốt', 'danger', 'Ảnh hưởng đến tập trung'))
        scores.append(0)
    
    # Độ ẩm (40-70% là tốt)
    humidity = sensor_data['do_am']
    if 40 <= humidity <= 70:
        evaluations.append(('💧 Độ ẩm', 'Tốt', 'success', 'Độ ẩm phù hợp'))
        scores.append(2)
    elif 30 <= humidity < 40 or 70 < humidity <= 80:
        evaluations.append(('💧 Độ ẩm', 'Trung bình', 'warning', 'Có thể gây khô/mốc'))
        scores.append(1)
    else:
        evaluations.append(('💧 Độ ẩm', 'Không tốt', 'danger', 'Ảnh hưởng sức khỏe'))
        scores.append(0)
    
    # Ánh sáng (>300 lux là tốt)
    light = sensor_data['anh_sang']
    if light >= 300:
        evaluations.append(('☀️ Ánh sáng', 'Đủ sáng', 'success', 'Đủ ánh sáng cho học tập'))
        scores.append(2)
    elif 200 <= light < 300:
        evaluations.append(('☀️ Ánh sáng', 'Hơi tối', 'warning', 'Cần bổ sung ánh sáng'))
        scores.append(1)
    else:
        evaluations.append(('☀️ Ánh sáng', 'Thiếu sáng', 'danger', 'Ảnh hưởng thị lực'))
        scores.append(0)
    
    # Chất lượng không khí (<400 PPM là tốt)
    air = sensor_data['chat_luong_kk']
    if air < 400:
        evaluations.append(('💨 Không khí', 'Trong lành', 'success', 'Không khí tốt'))
        scores.append(2)
    elif 400 <= air < 800:
        evaluations.append(('💨 Không khí', 'Trung bình', 'warning', 'Cần thông thoáng'))
        scores.append(1)
    else:
        evaluations.append(('💨 Không khí', 'Ô nhiễm', 'danger', 'Cần cải thiện ngay'))
        scores.append(0)
    
    # Độ ồn (<50 dB là tốt)
    noise = sensor_data['do_on']
    if noise < 50:
        evaluations.append(('🔊 Độ ồn', 'Yên tĩnh', 'success', 'Môi trường yên tĩnh'))
        scores.append(2)
    elif 50 <= noise < 70:
        evaluations.append(('🔊 Độ ồn', 'Bình thường', 'warning', 'Có thể gây phân tâm'))
        scores.append(1)
    else:
        evaluations.append(('🔊 Độ ồn', 'Ồn ào', 'danger', 'Ảnh hưởng nghiêm trọng'))
        scores.append(0)
    
    # Tính tổng điểm (0-10)
    total_score = sum(scores)
    percentage = (total_score / 10) * 100
    
    # Đánh giá tổng thể
    if percentage >= 80:
        overall = 'TỐT'
        overall_class = 'success'
        overall_icon = '👍'
        advice = 'Môi trường học tập lý tưởng! Tiết học có thể diễn ra hiệu quả.'
    elif percentage >= 60:
        overall = 'KHÁ'
        overall_class = 'warning'
        overall_icon = '👌'
        advice = 'Môi trường chấp nhận được. Có một số yếu tố cần cải thiện.'
    else:
        overall = 'CẦN CẢI THIỆN'
        overall_class = 'danger'
        overall_icon = '⚠️'
        advice = 'Môi trường không phù hợp. Cần điều chỉnh trước khi học.'
    
    # Tiết học đánh giá
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
        'percentage': percentage,
        'overall': overall,
        'overall_class': overall_class,
        'overall_icon': overall_icon,
        'advice': advice,
        'class_eval': class_eval,
        'class_color': class_color,
        'evaluations': evaluations
    }

# ========== ROUTES ==========
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
            
            print(f"✅ User {username} ({session['role']}) logged in")
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', 
                                 error="❌ Tên đăng nhập hoặc mật khẩu không đúng!")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.get('username', 'Unknown')
    session.clear()
    print(f"👋 User {username} logged out")
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
        'history': history_data
    })

@app.route('/control', methods=['POST'])
def control():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # CHỈ ADMIN mới được điều khiển
    if session['role'] != 'admin':
        return jsonify({'error': '❌ Chỉ quản trị viên mới có quyền điều khiển!'}), 403
    
    data = request.json
    device = data.get('device')
    action = data.get('action')
    
    if device and action:
        send_control_command(device, action)
        
        return jsonify({
            'success': True,
            'message': f'✅ Đã {action.lower()} {device}',
            'status': action
        })
    
    return jsonify({'error': 'Thiếu thông tin'}), 400

@app.route('/data')
def data_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Tạo dữ liệu lịch sử với đánh giá
    data_list = []
    base_time = datetime.now()
    
    for i in range(100):
        record_time = base_time - timedelta(minutes=i*5)
        
        # Tạo dữ liệu ngẫu nhiên
        temp = round(24 + random.random() * 4, 1)
        humidity = round(55 + random.random() * 20, 1)
        light = round(250 + random.random() * 250)
        air = round(300 + random.random() * 500)
        noise = round(35 + random.random() * 40)
        
        # Đánh giá từng thời điểm
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
            'thoi_gian': record_time.strftime("%H:%M:%S"),
            'ngay': record_time.strftime("%d/%m/%Y"),
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
def settings():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['role'] != 'admin':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            system_settings['auto_mode'] = request.form.get('auto_mode') == 'on'
            system_settings['temp_min'] = float(request.form.get('temp_min', 20))
            system_settings['temp_max'] = float(request.form.get('temp_max', 28))
            system_settings['light_min'] = float(request.form.get('light_min', 300))
            system_settings['noise_max'] = float(request.form.get('noise_max', 70))
            system_settings['air_max'] = float(request.form.get('air_max', 800))
            
            return jsonify({'success': True, 'message': '✅ Đã cập nhật cài đặt hệ thống!'})
        except:
            return jsonify({'error': '❌ Dữ liệu không hợp lệ!'}), 400
    
    return render_template('settings.html',
                         settings=system_settings,
                         role=session['role'])

@app.route('/report')
def report():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    evaluation = evaluate_environment()
    
    return render_template('report.html',
                         data=sensor_data,
                         evaluation=evaluation,
                         settings=system_settings,
                         name=session['name'],
                         role=session['role'])

@app.route('/export_pdf')
def export_pdf():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Tạo CSV thay vì PDF (đơn giản hơn)
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['CLASSGUARD - BÁO CÁO MÔI TRƯỜNG LỚP HỌC'])
    writer.writerow([f'Thời gian xuất: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'])
    writer.writerow([f'Người xuất: {session.get("name", "Unknown")}'])
    writer.writerow([])
    
    # Dữ liệu cảm biến
    writer.writerow(['THÔNG SỐ CẢM BIẾN'])
    writer.writerow(['Thông số', 'Giá trị', 'Đơn vị'])
    writer.writerow(['Nhiệt độ', f"{sensor_data['nhiet_do']:.1f}", '°C'])
    writer.writerow(['Độ ẩm', f"{sensor_data['do_am']:.1f}", '%'])
    writer.writerow(['Ánh sáng', str(sensor_data['anh_sang']), 'lux'])
    writer.writerow(['Chất lượng KK', str(sensor_data['chat_luong_kk']), 'PPM'])
    writer.writerow(['Độ ồn', str(sensor_data['do_on']), 'dB'])
    writer.writerow([])
    
    # Trạng thái thiết bị
    writer.writerow(['TRẠNG THÁI THIẾT BỊ'])
    writer.writerow(['Thiết bị', 'Trạng thái'])
    writer.writerow(['Quạt', sensor_data['quat']])
    writer.writerow(['Đèn', sensor_data['den']])
    writer.writerow(['Cửa sổ', sensor_data['cua_so']])
    writer.writerow(['Cảnh báo', sensor_data['canh_bao']])
    writer.writerow([])
    
    # Đánh giá
    eval_data = evaluate_environment()
    writer.writerow(['ĐÁNH GIÁ TỔNG THỂ'])
    writer.writerow(['Điểm số', f"{eval_data['total_score']}/10"])
    writer.writerow(['Xếp hạng', eval_data['overall']])
    writer.writerow(['Tiết học', eval_data['class_eval']])
    writer.writerow(['Khuyến nghị', eval_data['advice']])
    
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=classguard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

def update_demo_data():
    """Cập nhật dữ liệu demo"""
    # Thêm biến động tự nhiên
    sensor_data['nhiet_do'] = max(18, min(35, sensor_data['nhiet_do'] + random.uniform(-0.5, 0.5)))
    sensor_data['do_am'] = max(30, min(85, sensor_data['do_am'] + random.uniform(-1, 1)))
    sensor_data['anh_sang'] = max(100, min(800, sensor_data['anh_sang'] + random.uniform(-20, 20)))
    sensor_data['chat_luong_kk'] = max(100, min(1200, sensor_data['chat_luong_kk'] + random.uniform(-30, 30)))
    sensor_data['do_on'] = max(20, min(100, sensor_data['do_on'] + random.uniform(-5, 5)))
    sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    # Cập nhật lịch sử
    update_history()

# ========== KHỞI TẠO ==========
def initialize_app():
    setup_mqtt()
    
    # Khởi tạo lịch sử
    for _ in range(20):
        update_demo_data()
    
    print("=" * 60)
    print("🚀 CLASSGUARD SYSTEM INITIALIZED")
    print(f"📊 URL: https://classguard-web.onrender.com")
    print(f"🔗 MQTT: {'✅ Connected' if mqtt_connected else '⚠️ Demo Mode'}")
    print("👤 Accounts: admin/admin123, giaovien/giaovien123")
    print("👤 Accounts: hocsinh/hocsinh123, xem/xem123")
    print("=" * 60)

initialize_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
