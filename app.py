"""โปรแกรม Earthwork Dashboard

เว็บแอปด้วย Flask สำหรับติดตามความก้าวหน้างานดิน (Earthwork)
"""

# เฟรมเวิร์ก Flask + สร้าง/ตอบกลับ JSON API
from flask import Flask, render_template, jsonify, request
import pandas as pd
import os
from datetime import datetime
from modules.data_processor import DataProcessor
from modules.volume_calculator import VolumeCalculator

app = Flask(__name__)  # สร้างอ็อบเจ็กต์แอป Flask
# ใช้สำหรับ session/signing (ค่า dev ตัวอย่าง)
app.config['SECRET_KEY'] = 'earthwork_dashboard_secret_key'

# เตรียมตัวอ่าน/ประมวลผลข้อมูล
BASE_DIR = os.path.dirname(os.path.abspath(
    __file__))  # โฟลเดอร์ที่มีไฟล์ app.py อยู่
# แหล่งข้อมูลหลัก (Excel)
DATA_FILE = os.path.join(BASE_DIR, 'data', 'earthwork.xlsx')
# อ่าน + จัดรูปข้อมูลเพื่อส่งกลับให้ API
data_processor = DataProcessor(DATA_FILE)
# ตัวช่วยคำนวณปริมาตรรวม/ทำแล้ว/คงเหลือ
volume_calculator = VolumeCalculator()


@app.route('/')
def dashboard():
    """หน้าแดชบอร์ดหลัก"""
    return render_template('dashboard.html')  # UI หน้าเดียวของแดชบอร์ด


@app.route('/api/summary')
def get_summary():
    """ดึงข้อมูลสรุปสำหรับการ์ด KPI บนหน้าแดชบอร์ด"""
    try:
        data = data_processor.load_data()  # โหลดข้อมูลจาก Excel (มีแคช)

        # คำนวณปริมาตร
        total_volume = volume_calculator.calculate_total_volume(
            data)  # ปริมาตรออกแบบ/แผนงาน
        completed_volume = volume_calculator.calculate_completed_volume(
            data)  # ปริมาตรที่ทำจริงแล้ว
        remaining_volume = total_volume - completed_volume  # คงเหลือ = รวม - ทำแล้ว
        completion_percent = (
            completed_volume / total_volume * 100) if total_volume > 0 else 0  # % ความคืบหน้า

        return jsonify({
            'success': True,
            'data': {
                'total_volume': round(total_volume, 3),
                'completed_volume': round(completed_volume, 3),
                'remaining_volume': round(remaining_volume, 3),
                'completion_percent': round(completion_percent, 2),
                'unit': 'm³'  # ลูกบาศก์เมตร
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sta-progress')
def get_sta_progress():
    """ดึงข้อมูลความก้าวหน้ารายช่วงสถานี (STA)"""
    try:
        data = data_processor.load_data()
        sta_progress = data_processor.get_sta_progress(data)

        return jsonify({
            'success': True,
            'data': sta_progress
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/layer-progress')
def get_layer_progress():
    """ดึงข้อมูลความก้าวหน้ารายชั้นงาน (Layer)"""
    try:
        data = data_processor.load_data()
        layer_progress = data_processor.get_layer_progress(data)

        return jsonify({
            'success': True,
            'data': layer_progress
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/qaqc-tests')
def get_qaqc_tests():
    """ดึงข้อมูลสรุป/รายการทดสอบ QAQC"""
    try:
        data = data_processor.load_data()
        qaqc_data = data_processor.get_qaqc_summary(data)

        return jsonify({
            'success': True,
            'data': qaqc_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/volume-chart')
def get_volume_chart_data():
    """ดึงข้อมูลสำหรับกราฟปริมาตร (รายสถานี)"""
    try:
        data = data_processor.load_data()
        chart_data = data_processor.get_volume_chart_data(data)

        return jsonify({
            'success': True,
            'data': chart_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/daily-progress')
def get_daily_progress():
    """ดึงข้อมูลความก้าวหน้ารายวัน"""
    try:
        data = data_processor.load_data()
        daily_data = data_processor.get_daily_progress(data)

        return jsonify({
            'success': True,
            'data': daily_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/refresh-data', methods=['POST'])
def refresh_data():
    """สั่งรีเฟรชข้อมูลใหม่จากไฟล์ Excel"""
    try:
        data_processor.refresh_data()
        return jsonify({
            'success': True,
            'message': 'Data refreshed successfully',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # บน Windows + Python 3.13 ตัว Werkzeug watchdog reloader อาจแครชด้วย:
    # TypeError: 'handle' must be a _ThreadHandle
    # ปิด reloader เพื่อให้ dev server ใช้งานได้เสถียร
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
