from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
import paho.mqtt.client as mqtt
import random
from datetime import datetime, timedelta
import json
import csv
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'classguard_pro_2024_vietnam_secure_v2'
app.secret_key = 'classguard_pro_2024_vietnam_secure_v2'

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
history_data = {key: [] for key in ['nhiet_do', 'do_am', 'anh_sang', 'chat_luong_kk', 'do_on']}
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
            
            print(f"✅ {username} ({session['role']}) logged in")
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', 
                                 error="❌ Tên đăng nhập hoặc mật khẩu không đúng!")
    
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
    
    # GIÁO VIÊN VÀ ADMIN được điều khiển
    if session['role'] not in ['admin', 'teacher']:
        return jsonify({'error': '❌ Không có quyền điều khiển!'}), 403
    
    data = request.json
    device = data.get('device')
    action = data.get('action')
    
    if device and action in ['BẬT', 'TẮT', 'MỞ', 'ĐÓNG']:
        sensor_data[device] = action
        
        # MQTT simulation
        print(f"📡 Control: {device} -> {action}")
        
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
    
    # Tạo dữ liệu mẫu
    data_list = []
    base_time = datetime.now()
    
    for i in range(50):
        record_time = base_time - timedelta(minutes=i*5)
        
        temp = round(24 + random.random() * 4, 1)
        humidity = round(55 + random.random() * 20, 1)
        light = round(250 + random.random() * 250)
        air = round(300 + random.random() * 500)
        noise = round(35 + random.random() * 40)
        
        # Đánh giá
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
    
    # CHỈ ADMIN mới vào được settings
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
            
            return jsonify({'success': True, 'message': '✅ Đã cập nhật cài đặt!'})
        except:
            return jsonify({'error': '❌ Dữ liệu không hợp lệ!'}), 400
    
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
    writer.writerow(['CLASSGUARD - BÁO CÁO'])
    writer.writerow(['Thời gian', datetime.now().strftime("%d/%m/%Y %H:%M:%S")])
    writer.writerow(['Người xuất', session.get('name', 'Unknown')])
    writer.writerow([])
    
    # Data
    writer.writerow(['Thông số', 'Giá trị', 'Đơn vị'])
    writer.writerow(['Nhiệt độ', f"{sensor_data['nhiet_do']:.1f}", '°C'])
    writer.writerow(['Độ ẩm', f"{sensor_data['do_am']:.1f}", '%'])
    writer.writerow(['Ánh sáng', str(sensor_data['anh_sang']), 'lux'])
    writer.writerow(['Chất lượng KK', str(sensor_data['chat_luong_kk']), 'PPM'])
    writer.writerow(['Độ ồn', str(sensor_data['do_on']), 'dB'])
    
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=classguard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

# ========== HÀM PHỤ TRỢ ==========
def evaluate_environment():
    """Đánh giá môi trường"""
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
        evaluations.append(('💨 Không khí', 'Trong lành', 'success'))
        scores.append(2)
    elif 400 <= air < 800:
        evaluations.append(('💨 Không khí', 'Trung bình', 'warning'))
        scores.append(1)
    else:
        evaluations.append(('💨 Không khí', 'Ô nhiễm', 'danger'))
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
        advice = 'Môi trường học tập lý tưởng!'
    elif percentage >= 60:
        overall = 'KHÁ'
        overall_class = 'warning'
        advice = 'Môi trường chấp nhận được.'
    else:
        overall = 'CẦN CẢI THIỆN'
        overall_class = 'danger'
        advice = 'Cần điều chỉnh môi trường.'
    
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
    sensor_data['nhiet_do'] = round(24 + random.random() * 4, 1)
    sensor_data['do_am'] = round(50 + random.random() * 20, 1)
    sensor_data['anh_sang'] = round(200 + random.random() * 300)
    sensor_data['chat_luong_kk'] = round(200 + random.random() * 600)
    sensor_data['do_on'] = round(30 + random.random() * 50)
    sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    # Tự động điều khiển
    if system_settings['auto_mode']:
        if sensor_data['nhiet_do'] > system_settings['temp_max']:
            sensor_data['quat'] = 'BẬT'
        elif sensor_data['nhiet_do'] < system_settings['temp_min']:
            sensor_data['quat'] = 'TẮT'
        
        if sensor_data['anh_sang'] < system_settings['light_min']:
            sensor_data['den'] = 'BẬT'
        else:
            sensor_data['den'] = 'TẮT'
        
        if sensor_data['chat_luong_kk'] > system_settings['air_max']:
            sensor_data['cua_so'] = 'MỞ'
        else:
            sensor_data['cua_so'] = 'ĐÓNG'
        
        if sensor_data['do_on'] > system_settings['noise_max']:
            sensor_data['canh_bao'] = 'BẬT'
        else:
            sensor_data['canh_bao'] = 'TẮT'
    
    # Cập nhật lịch sử
    update_history()

def update_history():
    """Cập nhật lịch sử"""
    now = datetime.now()
    
    if len(history_data['time']) >= 30:
        for key in history_data:
            if history_data[key]:
                history_data[key].pop(0)
    
    history_data['time'].append(now.strftime("%H:%M:%S"))
    history_data['nhiet_do'].append(sensor_data['nhiet_do'])
    history_data['do_am'].append(sensor_data['do_am'])
    history_data['anh_sang'].append(sensor_data['anh_sang'])
    history_data['chat_luong_kk'].append(sensor_data['chat_luong_kk'])
    history_data['do_on'].append(sensor_data['do_on'])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
