from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file, session
from datetime import datetime
import json
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
import random

# ========== KHỞI TẠO FLASK ==========
app = Flask(__name__)
app.config['SECRET_KEY'] = 'classguard_2024_minhquan'

# ========== DỮ LIỆU MẪU ==========
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

# ========== TÀI KHOẢN ĐƠN GIẢN ==========
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'xem': {'password': 'xem123', 'role': 'viewer'}
}

# ========== HÀM KIỂM TRA ĐĂNG NHẬP ==========
def check_login(username, password):
    if username in USERS and USERS[username]['password'] == password:
        return USERS[username]
    return None

# ========== ROUTES ==========
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = check_login(username, password)
        
        if user:
            session['username'] = username
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Cập nhật dữ liệu ngẫu nhiên để demo
    sensor_data['nhiet_do'] = round(25 + random.random() * 5, 1)
    sensor_data['do_am'] = round(60 + random.random() * 10, 1)
    sensor_data['anh_sang'] = round(300 + random.random() * 200)
    sensor_data['chat_luong_kk'] = round(200 + random.random() * 300)
    sensor_data['do_on'] = round(40 + random.random() * 30)
    sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    return render_template('dashboard.html', 
                         data=sensor_data,
                         username=session['username'],
                         role=session['role'])

@app.route('/get_sensor_data')
def get_sensor_data():
    if 'username' not in session:
        return jsonify({'error': 'Chưa đăng nhập'}), 401
    
    # Cập nhật dữ liệu ngẫu nhiên
    sensor_data['nhiet_do'] = round(25 + random.random() * 5, 1)
    sensor_data['do_am'] = round(60 + random.random() * 10, 1)
    sensor_data['anh_sang'] = round(300 + random.random() * 200)
    sensor_data['chat_luong_kk'] = round(200 + random.random() * 300)
    sensor_data['do_on'] = round(40 + random.random() * 30)
    sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    return jsonify(sensor_data)

@app.route('/control', methods=['POST'])
def control():
    if 'username' not in session:
        return jsonify({'error': 'Chưa đăng nhập'}), 401
    
    if session['role'] != 'admin':
        return jsonify({'error': 'Không có quyền điều khiển'}), 403
    
    device = request.json.get('device')
    action = request.json.get('action')
    
    if device and action:
        # Cập nhật trạng thái
        if device == 'quat':
            sensor_data['quat'] = 'ON' if action == 'on' else 'OFF'
        elif device == 'den':
            sensor_data['den'] = 'ON' if action == 'on' else 'OFF'
            
        return jsonify({'success': True, 'message': f'Đã {action} {device}'})
    
    return jsonify({'error': 'Thiếu thông tin'}), 400

@app.route('/data')
def data_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Tạo dữ liệu mẫu
    data_list = []
    for i in range(10):
        data_list.append({
            'thoi_gian': datetime.now().strftime("%H:%M:%S"),
            'nhiet_do': round(25 + i/2, 1),
            'do_am': round(60 + i*2, 1),
            'anh_sang': 300 + i*50,
            'chat_luong_kk': 200 + i*30,
            'do_on': 40 + i*5
        })
    
    return render_template('data.html', 
                         data=data_list,
                         role=session['role'])

@app.route('/export_pdf')
def export_pdf():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Tạo PDF đơn giản
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "BÁO CÁO CLASSGUARD")
    p.drawString(100, 730, f"Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    p.setFont("Helvetica", 12)
    y = 700
    
    data_display = [
        ("Nhiệt độ", f"{sensor_data['nhiet_do']} °C"),
        ("Độ ẩm", f"{sensor_data['do_am']} %"),
        ("Ánh sáng", f"{sensor_data['anh_sang']} lux"),
        ("Chất lượng không khí", f"{sensor_data['chat_luong_kk']} PPM"),
        ("Độ ồn", f"{sensor_data['do_on']} dB"),
        ("Trạng thái quạt", sensor_data['quat']),
        ("Trạng thái đèn", sensor_data['den'])
    ]
    
    for label, value in data_display:
        p.drawString(100, y, f"{label}: {value}")
        y -= 25
    
    p.save()
    buffer.seek(0)
    
    return send_file(buffer, 
                    download_name=f'classguard_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                    as_attachment=True,
                    mimetype='application/pdf')

# ========== CHẠY ỨNG DỤNG ==========
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
