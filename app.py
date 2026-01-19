from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import paho.mqtt.client as mqtt
from datetime import datetime
import json
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

# ========== KHỞI TẠO FLASK ==========
app = Flask(__name__)
app.config['SECRET_KEY'] = 'classguard_secret_key_2024_minhquan'
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
    role = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))

# ========== DỮ LIỆU MẪU ==========
sensor_data = {
    'nhiet_do': 27.5,
    'do_am': 65.2,
    'anh_sang': 450,
    'chat_luong_kk': 350,
    'do_on': 45,
    'quat': 'OFF',
    'den': 'ON',
    'timestamp': datetime.now().strftime("%H:%M:%S %d/%m/%Y")
}

# ========== MQTT CLIENT ĐƠN GIẢN ==========
mqtt_client = None

def setup_mqtt():
    global mqtt_client
    try:
        mqtt_client = mqtt.Client()
        mqtt_client.connect("broker.hivemq.com", 1883, 60)
        mqtt_client.loop_start()
        print("MQTT connected successfully")
    except Exception as e:
        print(f"MQTT connection failed: {e}")
        mqtt_client = None

def mqtt_publish(topic, message):
    if mqtt_client:
        try:
            mqtt_client.publish(topic, message)
            print(f"Published to {topic}: {message}")
        except:
            pass

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
    # Giả lập dữ liệu thay đổi
    import random
    sensor_data['nhiet_do'] = round(25 + random.random() * 5, 1)
    sensor_data['do_am'] = round(60 + random.random() * 10, 1)
    sensor_data['anh_sang'] = round(300 + random.random() * 200)
    sensor_data['chat_luong_kk'] = round(200 + random.random() * 300)
    sensor_data['do_on'] = round(40 + random.random() * 30)
    sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
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
        
        # Cập nhật trạng thái
        if device == 'quat':
            sensor_data['quat'] = 'ON' if action == 'on' else 'OFF'
        elif device == 'den':
            sensor_data['den'] = 'ON' if action == 'on' else 'OFF'
            
        return jsonify({'success': True})
    
    return jsonify({'error': 'Thiếu thông tin'}), 400

@app.route('/data')
@login_required
def data_page():
    # Tạo dữ liệu mẫu
    data_list = []
    for i in range(10):
        data_list.append({
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'nhiet_do': round(25 + i, 1),
            'do_am': round(60 + i*2, 1),
            'anh_sang': 300 + i*50,
            'chat_luong_kk': 200 + i*30,
            'do_on': 40 + i*5
        })
    
    return render_template('data.html', 
                         data=data_list,
                         role=current_user.role)

@app.route('/export_pdf')
@login_required
def export_pdf():
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "BÁO CÁO CLASSGUARD")
    p.drawString(100, 730, f"Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    p.setFont("Helvetica", 12)
    y = 700
    data = [
        ("Nhiệt độ", f"{sensor_data['nhiet_do']} °C"),
        ("Độ ẩm", f"{sensor_data['do_am']} %"),
        ("Ánh sáng", f"{sensor_data['anh_sang']} lux"),
        ("Chất lượng KK", f"{sensor_data['chat_luong_kk']} PPM"),
        ("Độ ồn", f"{sensor_data['do_on']} dB"),
        ("Quạt", sensor_data['quat']),
        ("Đèn", sensor_data['den'])
    ]
    
    for label, value in data:
        p.drawString(100, y, f"{label}: {value}")
        y -= 20
    
    p.save()
    buffer.seek(0)
    
    return send_file(buffer, 
                    download_name='classguard_report.pdf',
                    as_attachment=True,
                    mimetype='application/pdf')

# ========== TẠO USER MẪU ==========
def create_sample_users():
    try:
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
            print("Created sample users")
    except Exception as e:
        print(f"Error creating users: {e}")

# ========== KHỞI TẠO ==========
def initialize_app():
    with app.app_context():
        db.create_all()
        create_sample_users()
        setup_mqtt()
    
    print("Application initialized successfully")

# ========== CHẠY ỨNG DỤNG ==========
if __name__ == '__main__':
    initialize_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
else:
    initialize_app()
