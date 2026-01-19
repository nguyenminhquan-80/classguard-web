from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import random
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'classguard_2024_minhquan'
app.secret_key = 'classguard_2024_minhquan'

# ========== TÀI KHOẢN ĐƠN GIẢN ==========
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin', 'email': 'admin@classguard.edu.vn'},
    'xem': {'password': 'xem123', 'role': 'viewer', 'email': 'viewer@classguard.edu.vn'}
}

# ========== DỮ LIỆU CẢM BIẾN ==========
sensor_data = {
    'nhiet_do': 27.5,
    'do_am': 65.2,
    'anh_sang': 450,
    'chat_luong_kk': 350,
    'do_on': 45,
    'quat': 'OFF',
    'den': 'ON',
    'timestamp': ''
}

# ========== HÀM CẬP NHẬT DỮ LIỆU ==========
def update_sensor_data():
    """Cập nhật dữ liệu cảm biến ngẫu nhiên"""
    sensor_data['nhiet_do'] = round(25 + random.random() * 5, 1)
    sensor_data['do_am'] = round(60 + random.random() * 10, 1)
    sensor_data['anh_sang'] = round(300 + random.random() * 200)
    sensor_data['chat_luong_kk'] = round(200 + random.random() * 300)
    sensor_data['do_on'] = round(40 + random.random() * 30)
    sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

# ========== ROUTES ==========
@app.route('/')
def home():
    """Trang chủ - chuyển hướng đến login"""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Trang đăng nhập"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Kiểm tra đăng nhập
        if username in USERS and USERS[username]['password'] == password:
            # Lưu thông tin vào session
            session['username'] = username
            session['role'] = USERS[username]['role']
            session['email'] = USERS[username]['email']
            
            # Chuyển hướng đến dashboard
            return redirect(url_for('dashboard'))
        else:
            # Đăng nhập thất bại
            return render_template('login.html', 
                                 error="❌ Tên đăng nhập hoặc mật khẩu không đúng!")
    
    # Hiển thị trang login
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Đăng xuất"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Trang dashboard chính"""
    # Kiểm tra đăng nhập
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Cập nhật dữ liệu
    update_sensor_data()
    
    # Render dashboard
    return render_template('dashboard.html',
                         data=sensor_data,
                         username=session['username'],
                         role=session['role'])

@app.route('/get_sensor_data')
def get_sensor_data():
    """API lấy dữ liệu cảm biến (AJAX)"""
    # Kiểm tra đăng nhập
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Cập nhật và trả về dữ liệu
    update_sensor_data()
    return jsonify(sensor_data)

@app.route('/control', methods=['POST'])
def control():
    """API điều khiển thiết bị"""
    # Kiểm tra đăng nhập
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Kiểm tra quyền admin
    if session.get('role') != 'admin':
        return jsonify({'error': 'Không có quyền điều khiển!'}), 403
    
    # Nhận dữ liệu
    data = request.json
    device = data.get('device')
    action = data.get('action')
    
    # Xử lý điều khiển
    if device in ['quat', 'den'] and action in ['on', 'off']:
        sensor_data[device] = 'ON' if action == 'on' else 'OFF'
        return jsonify({
            'success': True,
            'message': f'Đã {action} {device}',
            'status': sensor_data[device]
        })
    
    return jsonify({'error': 'Yêu cầu không hợp lệ'}), 400

@app.route('/data')
def data():
    """Trang xem dữ liệu"""
    # Kiểm tra đăng nhập
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Tạo dữ liệu mẫu (50 bản ghi)
    data_list = []
    base_time = datetime.now()
    
    for i in range(50):
        record_time = base_time.replace(minute=base_time.minute - i)
        data_list.append({
            'thoi_gian': record_time.strftime("%H:%M:%S"),
            'nhiet_do': round(25 + (i % 10) / 2, 1),
            'do_am': round(60 + (i % 10) * 2, 1),
            'anh_sang': 300 + (i % 10) * 50,
            'chat_luong_kk': 200 + (i % 10) * 30,
            'do_on': 40 + (i % 10) * 5
        })
    
    return render_template('data.html',
                         data=data_list,
                         role=session.get('role', 'viewer'))

@app.route('/export_pdf')
def export_pdf():
    """Xuất báo cáo PDF - TẠM THỜI VÔ HIỆU HÓA"""
    # Kiểm tra đăng nhập
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # TẠM THỜI: Trả về thông báo
    return "Tính năng xuất PDF tạm thời không khả dụng. Đang cập nhật..."

# ========== CHẠY ỨNG DỤNG ==========
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
