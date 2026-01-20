from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
import random
from datetime import datetime, timedelta
import json
import csv
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'classguard_final_v3_2024'
app.secret_key = 'classguard_final_v3_2024'

# ========== TÀI KHOẢN ==========
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin', 'name': 'Quản trị viên'},
    'giaovien': {'password': 'giaovien123', 'role': 'teacher', 'name': 'Giáo viên'},
    'hocsinh': {'password': 'hocsinh123', 'role': 'student', 'name': 'Học sinh'},
    'xem': {'password': 'xem123', 'role': 'viewer', 'name': 'Khách xem'}
}

# ========== DỮ LIỆU ==========
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

# Cài đặt
system_settings = {
    'auto_mode': True,
    'temp_min': 20,
    'temp_max': 28,
    'light_min': 300,
    'noise_max': 70,
    'air_max': 800
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
    
    # Kiểm tra chế độ tự động - nếu đang bật thì không cho điều khiển thủ công
    if system_settings['auto_mode']:
        return jsonify({'error': '❌ Hệ thống đang ở chế độ tự động. Tắt chế độ tự động để điều khiển thủ công.'}), 403
    
    if session['role'] not in ['admin', 'teacher']:
        return jsonify({'error': '❌ Không có quyền điều khiển!'}), 403
    
    data = request.json
    device = data.get('device')
    action = data.get('action')
    
    if device and action in ['BẬT', 'TẮT', 'MỞ', 'ĐÓNG']:
        sensor_data[device] = action
        return jsonify({
            'success': True,
            'message': f'✅ Đã {action.lower()} {device}',
            'status': action
        })
    
    return jsonify({'error': 'Thiếu thông tin'}), 400

@app.route('/update_settings', methods=['POST'])
def update_settings():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if session['role'] not in ['admin', 'teacher']:
    return jsonify({'error': '❌ Không có quyền điều khiển!'}), 403
    
    try:
        system_settings['auto_mode'] = request.json.get('auto_mode', system_settings['auto_mode'])
        system_settings['temp_min'] = float(request.json.get('temp_min', system_settings['temp_min']))
        system_settings['temp_max'] = float(request.json.get('temp_max', system_settings['temp_max']))
        system_settings['light_min'] = float(request.json.get('light_min', system_settings['light_min']))
        system_settings['noise_max'] = float(request.json.get('noise_max', system_settings['noise_max']))
        system_settings['air_max'] = float(request.json.get('air_max', system_settings['air_max']))
        
        return jsonify({'success': True, 'message': '✅ Đã cập nhật cài đặt!'})
    except:
        return jsonify({'error': '❌ Dữ liệu không hợp lệ!'}), 400

@app.route('/data')
def data_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
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
    """Cập nhật dữ liệu demo"""
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
    """Tự động điều khiển thiết bị"""
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
    
    # Độ ồn
    if sensor_data['do_on'] > system_settings['noise_max']:
        sensor_data['canh_bao'] = 'BẬT'
    else:
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

# ========== API CHO ESP32 ==========
@app.route('/api/esp32/data', methods=['POST'])
def receive_esp32_data():
    try:
        data = request.json
        
        # Lưu dữ liệu từ ESP32
        if 'sensors' in data:
            sensors = data['sensors']
            # Cập nhật dữ liệu cảm biến
            sensor_data['nhiet_do'] = sensors.get('temperature', sensor_data['nhiet_do'])
            sensor_data['do_am'] = sensors.get('humidity', sensor_data['do_am'])
            sensor_data['anh_sang'] = sensors.get('light', sensor_data['anh_sang'])
            sensor_data['chat_luong_kk'] = sensors.get('air_quality', sensor_data['chat_luong_kk'])
            sensor_data['do_on'] = sensors.get('noise', sensor_data['do_on'])
            
            # Cập nhật trạng thái thiết bị
            if 'devices' in data:
                devices = data['devices']
                # Đồng bộ trạng thái với ESP32
        
        # Kiểm tra cảnh báo
        alerts = check_esp32_alerts(sensors)
        
        return jsonify({
            'success': True,
            'message': 'Đã nhận dữ liệu từ ESP32',
            'alert': alerts[0] if alerts else None,
            'thresholds': system_settings
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/esp32/control', methods=['GET'])
def get_esp32_control():
    """ESP32 lấy lệnh điều khiển từ web"""
    device_id = request.args.get('device_id', 'ESP32-S3-CLASSGUARD')
    
    # Kiểm tra nếu có lệnh chờ cho ESP32 này
    # Ở đây bạn cần lưu lệnh vào database hoặc biến tạm
    # Tạm thời trả về không có lệnh
    
    return jsonify({}), 204  # 204 No Content

@app.route('/api/esp32/ack', methods=['POST'])
def esp32_command_ack():
    """ESP32 xác nhận đã thực hiện lệnh"""
    data = request.json
    command_id = data.get('command_id')
    
    # Cập nhật trạng thái lệnh
    print(f"✅ ESP32 đã thực hiện lệnh: {command_id}")
    
    return jsonify({'success': True})

@app.route('/api/esp32/status', methods=['GET'])
def esp32_status():
    """Kiểm tra kết nối API"""
    return jsonify({
        'status': 'online',
        'server': 'classguard-web.onrender.com',
        'project': 'CLASSGUARD THCS',
        'version': '1.0',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

def check_esp32_alerts(sensors):
    """Kiểm tra cảnh báo từ dữ liệu ESP32"""
    alerts = []
    
    if sensors.get('temperature', 25) > 30:
        alerts.append('Nhiệt độ quá cao (>30°C)')
    if sensors.get('air_quality', 400) > 1000:
        alerts.append('Chất lượng không khí kém (>1000 PPM)')
    if sensors.get('noise', 45) > 80:
        alerts.append('Độ ồn quá cao (>80 dB)')
    if sensors.get('light', 300) < 200:
        alerts.append('Ánh sáng quá yếu (<200 lux)')
    
    return alerts
