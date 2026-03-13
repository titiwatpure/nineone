"""โปรแกรม Earthwork Dashboard

เว็บแอปด้วย Flask สำหรับติดตามความก้าวหน้างานดิน (Earthwork)
"""

# เฟรมเวิร์ก Flask + สร้าง/ตอบกลับ JSON API
from flask import Flask, render_template, jsonify, request
from flask import send_file
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
from modules.data_processor import DataProcessor
from modules.volume_calculator import VolumeCalculator
from modules.fuel_repository import FuelRepository

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

# =========================
# Fuel (น้ำมันเชื้อเพลิง)
# =========================
FUEL_DB_FILE = os.path.join(BASE_DIR, 'data', 'fuel.sqlite3')
fuel_repo = FuelRepository(FUEL_DB_FILE)


@app.route('/')
def dashboard():
    """หน้าแดชบอร์ดหลัก"""
    return render_template('dashboard.html')  # UI หน้าเดียวของแดชบอร์ด


@app.route('/fuel')
def fuel_page():
    """หน้าเมนูระบบน้ำมันเชื้อเพลิง"""
    return render_template('fuel.html')


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


# -------------------------
# Fuel APIs
# -------------------------


def _iso_today() -> str:
    return datetime.now().date().isoformat()


def _iso_first_day_of_month() -> str:
    now = datetime.now().date()
    return now.replace(day=1).isoformat()


def _iso_first_day_of_year() -> str:
    now = datetime.now().date()
    return now.replace(month=1, day=1).isoformat()


@app.route('/api/fuel/entry', methods=['POST'])
def fuel_add_entry():
    """บันทึกรายการเติมน้ำมัน (กรอกมือ)"""
    try:
        payload = request.get_json(force=True, silent=False) or {}
        entry = fuel_repo.normalize_entry(payload)
        inserted, message = fuel_repo.add_entry(entry)
        return jsonify({'success': True, 'inserted': inserted, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/fuel/import-excel', methods=['POST'])
def fuel_import_excel():
    """นำเข้า Excel (.xlsx) สำหรับรายการเติมน้ำมัน"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'ไม่พบไฟล์ (field: file)'}), 400
        f = request.files['file']
        if not f or not f.filename:
            return jsonify({'success': False, 'error': 'ไฟล์ไม่ถูกต้อง'}), 400

        # อ่านไฟล์จาก memory
        df = pd.read_excel(f)
        if df.empty:
            return jsonify({'success': False, 'error': 'ไฟล์ไม่มีข้อมูล'}), 400

        entries = []
        for _, row in df.iterrows():
            raw = row.to_dict()
            entry = fuel_repo.normalize_entry(raw)
            entries.append(entry)

        result = fuel_repo.import_entries(entries)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/fuel/summary')
def fuel_summary():
    """สรุปวันนี้/เดือนนี้/ปีนี้ และ top machine ในช่วงที่เลือก"""
    try:
        # ช่วงสำหรับ top machine และ card "ช่วงที่เลือก" (ใช้ start/end จาก query)
        start = request.args.get('start') or _iso_first_day_of_month()
        end = request.args.get('end') or _iso_today()

        today = _iso_today()
        month_start = _iso_first_day_of_month()
        year_start = _iso_first_day_of_year()

        data = {
            'today': fuel_repo.totals_for_range(today, today),
            'month': fuel_repo.totals_for_range(month_start, today),
            'year': fuel_repo.totals_for_range(year_start, today),
            'top_machine': fuel_repo.top_machine_for_range(start, end)
        }
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/fuel/report')
def fuel_report():
    """รายงานสรุปในช่วงวันที่ (daily/monthly/yearly + by machine)"""
    try:
        start = request.args.get('start') or _iso_first_day_of_month()
        end = request.args.get('end') or _iso_today()

        data = {
            'daily': fuel_repo.summary_daily(start, end),
            'monthly': fuel_repo.summary_monthly(start, end),
            'yearly': fuel_repo.summary_yearly(start, end),
            'by_machine': fuel_repo.summary_by_machine(start, end)
        }
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/fuel/export')
def fuel_export():
    """ส่งออก CSV/XLSX

    Query:
      kind=details|summary
      format=csv|xlsx
      start=YYYY-MM-DD
      end=YYYY-MM-DD
    """

    try:
        kind = (request.args.get('kind') or 'details').lower()
        fmt = (request.args.get('format') or 'csv').lower()
        start = request.args.get('start') or _iso_first_day_of_month()
        end = request.args.get('end') or _iso_today()

        if fmt not in ('csv', 'xlsx'):
            return jsonify({'success': False, 'error': 'format ต้องเป็น csv หรือ xlsx'}), 400
        if kind not in ('details', 'summary'):
            return jsonify({'success': False, 'error': 'kind ต้องเป็น details หรือ summary'}), 400

        df_details = pd.DataFrame()
        df_daily = pd.DataFrame()
        df_monthly = pd.DataFrame()
        df_yearly = pd.DataFrame()
        df_by_machine = pd.DataFrame()

        if kind == 'details':
            df_details = pd.DataFrame(fuel_repo.list_details(start, end))
            filename_base = f"fuel_details_{start}_to_{end}"
        else:
            df_daily = pd.DataFrame(fuel_repo.summary_daily(start, end))
            df_monthly = pd.DataFrame(fuel_repo.summary_monthly(start, end))
            df_yearly = pd.DataFrame(fuel_repo.summary_yearly(start, end))
            df_by_machine = pd.DataFrame(
                fuel_repo.summary_by_machine(start, end))
            filename_base = f"fuel_summary_{start}_to_{end}"

        bio = BytesIO()
        if fmt == 'csv':
            if kind != 'details':
                return jsonify({'success': False, 'error': 'CSV รองรับเฉพาะ details ใน MVP นี้'}), 400

            if df_details.empty:
                df_details = pd.DataFrame(columns=[
                    'วันที่', 'รหัสเครื่องจักร', 'ปริมาณ(ลิตร)', 'ราคา/ลิตร(บาท)', 'ยอดเงิน(บาท)',
                    'เลขที่ใบเสร็จ', 'ผู้ขับ', 'ผู้บันทึก', 'ปั๊ม/ผู้ขาย', 'สถานที่เติม', 'ชั่วโมงเครื่อง', 'หมายเหตุ'
                ])
            df_details.to_csv(bio, index=False, encoding='utf-8-sig')
            bio.seek(0)
            return send_file(
                bio,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f"{filename_base}.csv",
            )

        # xlsx
        if kind == 'details':
            with pd.ExcelWriter(bio, engine='openpyxl') as writer:
                (df_details if not df_details.empty else pd.DataFrame()).to_excel(
                    writer, sheet_name='รายละเอียด', index=False)
            bio.seek(0)
            return send_file(
                bio,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f"{filename_base}.xlsx",
            )

        with pd.ExcelWriter(bio, engine='openpyxl') as writer:
            df_daily.to_excel(writer, sheet_name='สรุป-รายวัน', index=False)
            df_monthly.to_excel(
                writer, sheet_name='สรุป-รายเดือน', index=False)
            df_yearly.to_excel(writer, sheet_name='สรุป-รายปี', index=False)
            df_by_machine.to_excel(
                writer, sheet_name='สรุป-ตามเครื่อง', index=False)

        bio.seek(0)
        return send_file(
            bio,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{filename_base}.xlsx",
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


if __name__ == '__main__':
    # บน Windows + Python 3.13 ตัว Werkzeug watchdog reloader อาจแครชด้วย:
    # TypeError: 'handle' must be a _ThreadHandle
    # ปิด reloader เพื่อให้ dev server ใช้งานได้เสถียร
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
