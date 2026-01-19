from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import paho.mqtt.client as mqtt
from datetime import datetime
import json
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import threading
import time

# ========== KHỞI TẠO FLASK ==========
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_classguard_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ========== MODEL USER ==========
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' hoặc 'viewer'
    email = db.Column(db.String(120), unique=True, nullable=False)

# ========== DỮ LIỆU CẢM BIẾN ==========
sensor_data = {
    'nhiet_do': 0,
    'do_am': 0,
    'anh_sang': 0,
    'chat_luong_kk': 0,
    'do_on': 0,
    'quat': 'OFF',
    'den': 'OFF',
    'timestamp': ''
}

# ========== KẾT NỐI MQTT ==========
def on_connect(client, userdata, flags, rc):
    print("Đã kết nối MQTT")
    client.subscribe("classguard/sensor")

def on_message(client, userdata, msg):
    global sensor_data
    try:
        data = json.loads(msg.payload.decode())
        sensor_data.update(data)
        sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        
        # Lưu vào file CSV
        save_to_csv(data)
        
        # Kiểm tra và cảnh báo tự động
        check_auto_control(data)
    except:
        pass

def save_to_csv(data):
    try:
        df = pd.DataFrame([data])
        df['timestamp'] = datetime.now()
        with open('data.csv', 'a') as f:
            df.to_csv(f, header=f.tell()==0, index=False)
    except:
        pass

def check_auto_control(data):
    # Tự động điều khiển dựa trên ngưỡng
    if data['nhiet_do'] > 30:
        mqtt_publish("classguard/control", "quat_on")
    elif data['nhiet_do'] < 25:
        mqtt_publish("classguard/control", "quat_off")
    
    if data['anh_sang'] < 300:
        mqtt_publish("classguard/control", "den_on")
    elif data['anh_sang'] > 500:
        mqtt_publish("classguard/control", "den_off")

# ========== KHỞI TẠO MQTT ==========
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    mqtt_client.connect("broker.hivemq.com", 1883, 60)
    mqtt_client.loop_start()

def mqtt_publish(topic, message):
    mqtt_client.publish(topic, message)

# ========== ROUTES ==========
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', 
                         data=sensor_data,
                         username=current_user.username,
                         role=current_user.role)

@app.route('/get_sensor_data')
@login_required
def get_sensor_data():
    return jsonify(sensor_data)

@app.route('/control', methods=['POST'])
@login_required
def control():
    if current_user.role != 'admin':
        return jsonify({'error': 'Không có quyền điều khiển'}), 403
    
    device = request.json.get('device')
    action = request.json.get('action')
    
    if device and action:
        command = f"{device}_{action}"
        mqtt_publish("classguard/control", command)
        return jsonify({'success': True})
    
    return jsonify({'error': 'Thiếu thông tin'}), 400

@app.route('/data')
@login_required
def data_page():
    try:
        df = pd.read_csv('data.csv')
        data_list = df.tail(100).to_dict('records')
    except:
        data_list = []
    
    return render_template('data.html', 
                         data=data_list,
                         role=current_user.role)

@app.route('/export_pdf')
@login_required
def export_pdf():
    # Tạo PDF từ dữ liệu
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Tiêu đề
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "BÁO CÁO MÔI TRƯỜNG LỚP HỌC")
    p.drawString(100, 730, f"Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Dữ liệu
    p.setFont("Helvetica", 12)
    y = 700
    for key, value in sensor_data.items():
        if key != 'timestamp':
            p.drawString(100, y, f"{key.replace('_', ' ').title()}: {value}")
            y -= 20
    
    p.save()
    buffer.seek(0)
    
    return send_file(buffer, 
                    download_name='classguard_report.pdf',
                    as_attachment=True,
                    mimetype='application/pdf')

@app.route('/settings')
@login_required
def settings():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    
    return render_template('settings.html')

# ========== TẠO USER MẪU ==========
def create_sample_users():
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', 
                    password='admin123', 
                    role='admin',
                    email='admin@classguard.edu.vn')
        db.session.add(admin)
        
        viewer = User(username='xem', 
                     password='xem123', 
                     role='viewer',
                     email='viewer@classguard.edu.vn')
        db.session.add(viewer)
        
        db.session.commit()

# ========== CHẠY ỨNG DỤNG ==========
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_sample_users()
        start_mqtt()
    
    # Chạy trên Render sẽ dùng gunicorn
    app.run(debug=False, host='0.0.0.0', port=5000)
