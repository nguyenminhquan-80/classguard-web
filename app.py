from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
import random
from datetime import datetime, timedelta
import json
import csv
import io
import threading
import time
from collections import deque

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

# ========== DỮ LIỆU HỆ THỐNG ==========
class SystemManager:
    def __init__(self):
        # Dữ liệu từ ESP32
        self.esp32_data = {
            'temperature': 26.5,
            'humidity': 65.0,
            'light': 450,
            'air_quality': 350,
            'noise': 45,
            'fan': False,
            'light_relay': False,
            'window': False,
            'alarm': False,
            'auto_mode': False,
            'audio_enabled': True,
            'last_update': datetime.now().strftime("%H:%M:%S"),
            'connected': False
        }
        
        # Dữ liệu hiển thị trên web
        self.sensor_data = {
            'nhiet_do': 26.5,
            'do_am': 65.0,
            'anh_sang': 450,
            'chat_luong_kk': 350,
            'do_on': 45,
            'quat': 'TẮT',
            'den': 'BẬT',
            'cua_so': 'ĐÓNG',
            'canh_bao': 'TẮT',
            'timestamp': datetime.now().strftime("%H:%M:%S")
        }
        
        # Cài đặt hệ thống
        self.settings = {
            'auto_mode': False,
            'temp_min': 20,
            'temp_max': 28,
            'light_min': 300,
            'noise_max': 70,
            'air_max': 800,
            'audio_enabled': True
        }
        
        # Lịch sử dữ liệu - ĐẢM BẢO 5 THÔNG SỐ
        self.history = {
            'time': deque(maxlen=15),
            'nhiet_do': deque(maxlen=15),
            'do_am': deque(maxlen=15),
            'anh_sang': deque(maxlen=15),
            'chat_luong_kk': deque(maxlen=15),
            'do_on': deque(maxlen=15)
        }
        
        # Hàng đợi lệnh
        self.command_queue = []
        self.command_id = 1
        
        # Khởi tạo dữ liệu demo cho 5 thông số
        self.init_demo_data()
    
    def init_demo_data(self):
        """Khởi tạo dữ liệu demo ban đầu cho 5 thông số"""
        now = datetime.now()
        for i in range(15):
            time_str = (now - timedelta(minutes=i)).strftime("%H:%M:%S")
            self.history['time'].appendleft(time_str)
            self.history['nhiet_do'].appendleft(round(24 + random.random() * 4, 1))
            self.history['do_am'].appendleft(round(50 + random.random() * 20, 1))
            self.history['anh_sang'].appendleft(round(200 + random.random() * 300))
            self.history['chat_luong_kk'].appendleft(round(200 + random.random() * 600))
            self.history['do_on'].appendleft(round(30 + random.random() * 50))
        print("✅ Đã khởi tạo dữ liệu demo cho 5 thông số")
    
    def sync_from_esp32(self, data):
        """Đồng bộ dữ liệu từ ESP32 - CẬP NHẬT ĐẦY ĐỦ 5 THÔNG SỐ"""
        if not data:
            return False
        
        try:
            # Cập nhật dữ liệu cảm biến từ ESP32
            self.esp32_data.update({
                'temperature': float(data.get('temperature', self.esp32_data['temperature'])),
                'humidity': float(data.get('humidity', self.esp32_data['humidity'])),
                'light': float(data.get('light', self.esp32_data['light'])),
                'air_quality': int(data.get('air_quality', self.esp32_data['air_quality'])),
                'noise': int(data.get('noise', self.esp32_data['noise'])),
                'fan': bool(data.get('fan', self.esp32_data['fan'])),
                'light_relay': bool(data.get('light_relay', self.esp32_data['light_relay'])),
                'window': bool(data.get('window', self.esp32_data['window'])),
                'alarm': bool(data.get('alarm', self.esp32_data['alarm'])),
                'auto_mode': bool(data.get('auto_mode', self.esp32_data['auto_mode'])),
                'audio_enabled': bool(data.get('audio_enabled', self.esp32_data['audio_enabled'])),
                'last_update': datetime.now().strftime("%H:%M:%S"),
                'connected': True
            })
            
            # Cập nhật dữ liệu hiển thị trên web
            self.sensor_data.update({
                'nhiet_do': self.esp32_data['temperature'],
                'do_am': self.esp32_data['humidity'],
                'anh_sang': self.esp32_data['light'],
                'chat_luong_kk': self.esp32_data['air_quality'],
                'do_on': self.esp32_data['noise'],
                'quat': 'BẬT' if self.esp32_data['fan'] else 'TẮT',
                'den': 'BẬT' if self.esp32_data['light_relay'] else 'TẮT',
                'cua_so': 'MỞ' if self.esp32_data['window'] else 'ĐÓNG',
                'canh_bao': 'BẬT' if self.esp32_data['alarm'] else 'TẮT',
                'timestamp': self.esp32_data['last_update']
            })
            
            # Cập nhật lịch sử cho 5 thông số
            current_time = datetime.now().strftime("%H:%M:%S")
            self.history['time'].append(current_time)
            self.history['nhiet_do'].append(self.esp32_data['temperature'])
            self.history['do_am'].append(self.esp32_data['humidity'])
            self.history['anh_sang'].append(self.esp32_data['light'])
            self.history['chat_luong_kk'].append(self.esp32_data['air_quality'])
            self.history['do_on'].append(self.esp32_data['noise'])
            
            # Log để debug
            print(f"📊 Đã cập nhật lịch sử 5 thông số:")
            print(f"  🌡️  Nhiệt độ: {self.esp32_data['temperature']:.1f}°C")
            print(f"  💧 Độ ẩm: {self.esp32_data['humidity']:.1f}%")
            print(f"  ☀️  Ánh sáng: {self.esp32_data['light']:.0f} lux")
            print(f"  💨 Chất lượng KK: {self.esp32_data['air_quality']} ppm")
            print(f"  🔊 Độ ồn: {self.esp32_data['noise']} dB")
            
            return True
            
        except Exception as e:
            print(f"❌ Lỗi đồng bộ ESP32: {e}")
            return False
    
    # ... phần còn lại giữ nguyên ...
    
    def add_command(self, command, value='', sender='Web'):
        """Thêm lệnh cho ESP32"""
        cmd = {
            'command_id': self.command_id,
            'command': command,
            'value': value,
            'sender': sender,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.command_queue.append(cmd)
        self.command_id += 1
        return cmd
    
    def get_pending_commands(self):
        """Lấy lệnh đang chờ"""
        commands = self.command_queue.copy()
        self.command_queue.clear()
        return commands
    
    def evaluate_environment(self):
        """Đánh giá môi trường từ dữ liệu hiện tại"""
        evaluations = []
        scores = []
        
        temp = self.sensor_data['nhiet_do']
        if 20 <= temp <= 28:
            evaluations.append(('🌡️ Nhiệt độ', 'Lý tưởng', 'success'))
            scores.append(2)
        elif 18 <= temp < 20 or 28 < temp <= 30:
            evaluations.append(('🌡️ Nhiệt độ', 'Chấp nhận', 'warning'))
            scores.append(1)
        else:
            evaluations.append(('🌡️ Nhiệt độ', 'Không tốt', 'danger'))
            scores.append(0)
        
        humidity = self.sensor_data['do_am']
        if 40 <= humidity <= 70:
            evaluations.append(('💧 Độ ẩm', 'Tốt', 'success'))
            scores.append(2)
        elif 30 <= humidity < 40 or 70 < humidity <= 80:
            evaluations.append(('💧 Độ ẩm', 'Trung bình', 'warning'))
            scores.append(1)
        else:
            evaluations.append(('💧 Độ ẩm', 'Không tốt', 'danger'))
            scores.append(0)
        
        light = self.sensor_data['anh_sang']
        if light >= 300:
            evaluations.append(('☀️ Ánh sáng', 'Đủ sáng', 'success'))
            scores.append(2)
        elif 200 <= light < 300:
            evaluations.append(('☀️ Ánh sáng', 'Hơi tối', 'warning'))
            scores.append(1)
        else:
            evaluations.append(('☀️ Ánh sáng', 'Thiếu sáng', 'danger'))
            scores.append(0)
        
        air = self.sensor_data['chat_luong_kk']
        if air < 400:
            evaluations.append(('💨 Chất lượng KK', 'Trong lành', 'success'))
            scores.append(2)
        elif 400 <= air < 800:
            evaluations.append(('💨 Chất lượng KK', 'Trung bình', 'warning'))
            scores.append(1)
        else:
            evaluations.append(('💨 Chất lượng KK', 'Ô nhiễm', 'danger'))
            scores.append(0)
        
        noise = self.sensor_data['do_on']
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

# Khởi tạo hệ thống
system = SystemManager()

# ========== ROUTES CHÍNH (GIỮ NGUYÊN TỪ CODE CŨ) ==========
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
    
    evaluation = system.evaluate_environment()
    
    return render_template('dashboard.html',
                         data=system.sensor_data,
                         evaluation=evaluation,
                         settings=system.settings,
                         username=session['username'],
                         name=session['name'],
                         role=session['role'],
                         login_time=session.get('login_time', ''),
                         esp32_connected=system.esp32_data['connected'])

# ========== API ĐỒNG BỘ 2 CHIỀU ==========
@app.route('/api/esp32/sync', methods=['POST'])
def esp32_sync():
    """API đồng bộ 2 chiều với ESP32"""
    try:
        # Nhận dữ liệu từ ESP32
        esp32_data = request.json
        
        if esp32_data:
            print(f"[ESP32] Nhận dữ liệu: {esp32_data}")
            system.sync_from_esp32(esp32_data)
        
        # Chuẩn bị phản hồi
        response = {
            'success': True,
            'message': 'Đồng bộ thành công',
            'thresholds': system.settings,
            'commands': system.get_pending_commands(),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"[ESP32] Lỗi đồng bộ: {str(e)}")
        return jsonify({'error': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/esp32/ack', methods=['POST'])
def esp32_ack():
    """ESP32 xác nhận đã thực thi lệnh"""
    try:
        data = request.json
        command_id = data.get('command_id')
        
        if command_id:
            print(f"[ESP32] ACK lệnh {command_id}")
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_sensor_data')
def get_sensor_data():
    """Lấy dữ liệu cảm biến cho web"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Chuyển deque thành list cho JSON
    history_dict = {
        'time': list(system.history['time']),
        'nhiet_do': list(system.history['nhiet_do']),
        'do_am': list(system.history['do_am']),
        'anh_sang': list(system.history['anh_sang']),
        'chat_luong_kk': list(system.history['chat_luong_kk']),
        'do_on': list(system.history['do_on'])
    }
    
    evaluation = system.evaluate_environment()
    
    return jsonify({
        'sensors': system.sensor_data,
        'evaluation': evaluation,
        'history': history_dict,
        'settings': system.settings,
        'esp32_connected': system.esp32_data['connected'],
        'esp32_last_update': system.esp32_data['last_update']
    })

@app.route('/control', methods=['POST'])
def control():
    """Điều khiển thiết bị từ web"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Kiểm tra chế độ tự động
    if system.settings['auto_mode']:
        return jsonify({'error': '❌ Hệ thống đang ở chế độ tự động. Tắt chế độ tự động để điều khiển thủ công.'}), 403
    
    if session['role'] not in ['admin', 'teacher']:
        return jsonify({'error': '❌ Không có quyền điều khiển!'}), 403
    
    data = request.json
    device = data.get('device')
    action = data.get('action')
    
    # Map device name từ web sang ESP32 command
    command_map = {
        'quat': {'BẬT': 'FAN_ON', 'TẮT': 'FAN_OFF'},
        'den': {'BẬT': 'LIGHT_ON', 'TẮT': 'LIGHT_OFF'},
        'cua_so': {'MỞ': 'WINDOW_OPEN', 'ĐÓNG': 'WINDOW_CLOSE'},
        'canh_bao': {'BẬT': 'ALARM_ON', 'TẮT': 'ALARM_OFF'}
    }
    
    if device in command_map and action in command_map[device]:
        # Cập nhật ngay cho UX
        system.sensor_data[device] = action
        
        # Cập nhật ESP32 data
        if device == 'quat':
            system.esp32_data['fan'] = (action == 'BẬT')
        elif device == 'den':
            system.esp32_data['light_relay'] = (action == 'BẬT')
        elif device == 'cua_so':
            system.esp32_data['window'] = (action == 'MỞ')
        elif device == 'canh_bao':
            system.esp32_data['alarm'] = (action == 'BẬT')
        
        # Gửi lệnh đến ESP32
        command = command_map[device][action]
        system.add_command(command, sender=session.get('name', 'Web'))
        
        return jsonify({
            'success': True,
            'message': f'✅ Đã {action.lower()} {device}',
            'status': action
        })
    
    return jsonify({'error': 'Thiếu thông tin'}), 400

@app.route('/update_settings', methods=['POST'])
def update_settings():
    """Cập nhật cài đặt hệ thống"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if session['role'] != 'admin':
        return jsonify({'error': 'Không có quyền!'}), 403
    
    try:
        data = request.json
        
        # Cập nhật settings
        for key in system.settings:
            if key in data:
                if key == 'auto_mode':
                    system.settings[key] = bool(data[key])
                else:
                    system.settings[key] = data[key]
        
        # Đồng bộ với ESP32 data
        system.esp32_data['auto_mode'] = system.settings['auto_mode']
        system.esp32_data['audio_enabled'] = system.settings['audio_enabled']
        
        # Gửi lệnh auto_mode đến ESP32
        if 'auto_mode' in data:
            command = 'AUTO_MODE_ON' if data['auto_mode'] else 'AUTO_MODE_OFF'
            system.add_command(command, sender=session.get('name', 'Admin'))
        
        return jsonify({'success': True, 'message': '✅ Đã cập nhật cài đặt!'})
    except Exception as e:
        return jsonify({'error': f'❌ Dữ liệu không hợp lệ: {str(e)}'}), 400

# ========== CÁC ROUTE KHÁC (GIỮ NGUYÊN) ==========
@app.route('/api/esp32/status')
def esp32_status():
    return jsonify({
        'connected': system.esp32_data['connected'],
        'last_update': system.esp32_data['last_update'],
        'data': system.esp32_data
    })

@app.route('/data')
def data_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Tạo dữ liệu mẫu (giữ nguyên từ code cũ)
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

@app.route('/settings')
def settings_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['role'] != 'admin':
        return redirect(url_for('dashboard'))
    
    return render_template('settings.html',
                         settings=system.settings,
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
    
    # Dữ liệu cảm biến
    writer.writerow(['THÔNG SỐ CẢM BIẾN'])
    writer.writerow(['Thông số', 'Giá trị', 'Đơn vị', 'Trạng thái'])
    
    data = system.sensor_data
    writer.writerow(['Nhiệt độ', f"{data['nhiet_do']:.1f}", '°C', 
                     'Tốt' if 20 <= data['nhiet_do'] <= 28 else 'Cảnh báo' if 28 < data['nhiet_do'] <= 32 else 'Nguy hiểm'])
    writer.writerow(['Độ ẩm', f"{data['do_am']:.1f}", '%',
                     'Tốt' if 40 <= data['do_am'] <= 70 else 'Cảnh báo'])
    writer.writerow(['Ánh sáng', str(data['anh_sang']), 'lux',
                     'Tốt' if data['anh_sang'] >= 300 else 'Cảnh báo' if data['anh_sang'] >= 200 else 'Thiếu sáng'])
    writer.writerow(['Chất lượng KK', str(data['chat_luong_kk']), 'PPM',
                     'Tốt' if data['chat_luong_kk'] < 400 else 'Trung bình' if data['chat_luong_kk'] < 800 else 'Ô nhiễm'])
    writer.writerow(['Độ ồn', str(data['do_on']), 'dB',
                     'Tốt' if data['do_on'] < 50 else 'Bình thường' if data['do_on'] < 70 else 'Ồn ào'])
    writer.writerow([])
    
    # Trạng thái thiết bị
    writer.writerow(['TRẠNG THÁI THIẾT BỊ'])
    writer.writerow(['Thiết bị', 'Trạng thái'])
    writer.writerow(['Quạt', data['quat']])
    writer.writerow(['Đèn', data['den']])
    writer.writerow(['Cửa sổ', data['cua_so']])
    writer.writerow(['Cảnh báo', data['canh_bao']])
    
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=classguard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

