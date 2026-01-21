"""
database.py - Quản lý database cho CLASSGUARD
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any

class ClassGuardDB:
    def __init__(self, db_file='classguard.db'):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Khởi tạo database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Bảng lịch sử cảm biến
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                temperature REAL,
                humidity REAL,
                light REAL,
                air_quality INTEGER,
                noise INTEGER,
                fan_state TEXT,
                light_state TEXT,
                window_state TEXT,
                alarm_state TEXT,
                auto_mode BOOLEAN,
                score INTEGER
            )
        ''')
        
        # Bảng thiết bị
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                state TEXT,
                last_updated DATETIME
            )
        ''')
        
        # Bảng lệnh
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_id INTEGER,
                command TEXT,
                value TEXT,
                sender TEXT,
                timestamp DATETIME,
                executed BOOLEAN DEFAULT 0
            )
        ''')
        
        # Bảng cài đặt
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_sensor_data(self, data: Dict[str, Any]):
        """Lưu dữ liệu cảm biến"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sensor_history 
            (temperature, humidity, light, air_quality, noise, 
             fan_state, light_state, window_state, alarm_state, auto_mode, score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('temperature'),
            data.get('humidity'),
            data.get('light'),
            data.get('air_quality'),
            data.get('noise'),
            data.get('fan_state', 'TẮT'),
            data.get('light_state', 'TẮT'),
            data.get('window_state', 'ĐÓNG'),
            data.get('alarm_state', 'TẮT'),
            data.get('auto_mode', True),
            data.get('score', 0)
        ))
        
        conn.commit()
        conn.close()
    
    def get_recent_history(self, limit: int = 50):
        """Lấy lịch sử gần đây"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM sensor_history 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def log_command(self, command_id: int, command: str, value: str, sender: str):
        """Ghi log lệnh"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO commands (command_id, command, value, sender, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (command_id, command, value, sender, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def mark_command_executed(self, command_id: int):
        """Đánh dấu lệnh đã thực thi"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE commands 
            SET executed = 1 
            WHERE command_id = ?
        ''', (command_id,))
        
        conn.commit()
        conn.close()
    
    def get_pending_commands(self):
        """Lấy lệnh chưa thực thi"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM commands 
            WHERE executed = 0 
            ORDER BY timestamp ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

# Sử dụng trong app.py
from database import ClassGuardDB

db = ClassGuardDB()

# Trong hàm esp32_sync
@app.route('/api/esp32/sync', methods=['POST'])
def esp32_sync():
    try:
        data = request.json
        
        # Lưu vào database
        db.save_sensor_data({
            'temperature': data.get('temperature'),
            'humidity': data.get('humidity'),
            'light': data.get('light'),
            'air_quality': data.get('air_quality'),
            'noise': data.get('noise'),
            'fan_state': 'BẬT' if data.get('fan') else 'TẮT',
            'light_state': 'BẬT' if data.get('light_relay') else 'TẮT',
            'window_state': 'MỞ' if data.get('window') else 'ĐÓNG',
            'alarm_state': 'BẬT' if data.get('alarm') else 'TẮT',
            'auto_mode': data.get('auto_mode', True),
            'score': calculate_score(data)  # Hàm tính điểm
        })
        
        # ... phần còn lại
