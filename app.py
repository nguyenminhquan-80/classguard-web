from flask import Flask, render_template, jsonify
import random
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_key_123'

# Dữ liệu mẫu
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

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    # Cập nhật dữ liệu ngẫu nhiên
    sensor_data['nhiet_do'] = round(25 + random.random() * 5, 1)
    sensor_data['do_am'] = round(60 + random.random() * 10, 1)
    sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    return render_template('dashboard.html', 
                         data=sensor_data,
                         username="admin",
                         role="admin")

@app.route('/get_sensor_data')
def get_sensor_data():
    # Cập nhật dữ liệu
    sensor_data['nhiet_do'] = round(25 + random.random() * 5, 1)
    sensor_data['do_am'] = round(60 + random.random() * 10, 1)
    sensor_data['anh_sang'] = round(300 + random.random() * 200)
    sensor_data['chat_luong_kk'] = round(200 + random.random() * 300)
    sensor_data['do_on'] = round(40 + random.random() * 30)
    sensor_data['timestamp'] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    return jsonify(sensor_data)

@app.route('/data')
def data_page():
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
                         role="admin")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
