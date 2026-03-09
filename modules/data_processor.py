"""โมดูลประมวลผลข้อมูล (Data Processor)

หน้าที่หลักคืออ่านไฟล์ Excel ของงานดิน และแปลงข้อมูลให้อยู่ในรูปแบบที่ API ส่งให้หน้าแดชบอร์ดได้
"""

import pandas as pd
import os
from datetime import datetime


class DataProcessor:
    def __init__(self, data_file_path):
        self.data_file_path = data_file_path  # พาธไปยังไฟล์ earthwork.xlsx
        self._cache = None  # แคชข้อมูล (dict ของ DataFrame)
        self._cache_time = None  # เวลาที่สร้างแคชล่าสุด
        # อายุแคช (วินาที) เพื่อเลี่ยงการอ่าน Excel บ่อยเกินไป
        self._cache_duration = 300

    def load_data(self):
        """โหลดข้อมูลจากไฟล์ Excel โดยใช้แคชช่วยลดการอ่านไฟล์ซ้ำ"""
        current_time = datetime.now()  # ใช้ตรวจอายุแคช (TTL)

        # ถ้าแคชยังไม่หมดอายุ ให้คืนค่าแคชทันที
        if self._cache is not None and self._cache_time is not None:
            if (current_time - self._cache_time).seconds < self._cache_duration:
                return self._cache

        # โหลดข้อมูลใหม่จากไฟล์
        if os.path.exists(self.data_file_path):
            data = {
                # แถวสรุป 1 แถว: total/completed/remaining
                'summary': pd.read_excel(self.data_file_path, sheet_name='Summary'),
                # ความก้าวหน้ารายช่วงสถานี (STA)
                'sta_progress': pd.read_excel(self.data_file_path, sheet_name='STA_Progress'),
                # ความก้าวหน้ารายชั้นงาน (Layer)
                'layer_progress': pd.read_excel(self.data_file_path, sheet_name='Layer_Progress'),
                # รายการทดสอบ QAQC
                'qaqc_tests': pd.read_excel(self.data_file_path, sheet_name='QAQC_Tests'),
                # บันทึกความก้าวหน้ารายวัน
                'daily_progress': pd.read_excel(self.data_file_path, sheet_name='Daily_Progress')
            }
        else:
            # ถ้าไม่พบไฟล์ ให้ใช้ข้อมูลตัวอย่าง
            data = self._get_sample_data()

        self._cache = data  # เก็บข้อมูลลงแคช
        self._cache_time = current_time  # เก็บเวลาที่สร้างแคช
        return data

    def refresh_data(self):
        """บังคับรีเฟรชข้อมูลใหม่จากไฟล์ (ล้างแคชก่อน)"""
        self._cache = None  # ล้างแคช เพื่อให้รอบถัดไปอ่านจาก Excel ใหม่
        self._cache_time = None  # รีเซ็ตเวลาแคช
        return self.load_data()

    def get_sta_progress(self, data):
        """จัดรูปข้อมูลความก้าวหน้ารายช่วงสถานี (STA)"""
        df = data.get('sta_progress', pd.DataFrame(
        ))  # คอลัมน์ที่คาดหวัง: sta_name, design_volume, completed_volume, status

        if df.empty:
            return []

        result = []
        for _, row in df.iterrows():
            design_vol = float(row.get('design_volume', 0))
            completed_vol = float(row.get('completed_volume', 0))
            remaining = design_vol - completed_vol  # คงเหลือของ STA นี้
            progress = (completed_vol / design_vol *
                        100) if design_vol > 0 else 0  # % ความก้าวหน้าของ STA นี้

            result.append({
                'sta_name': str(row.get('sta_name', '')),
                'sta_from': str(row.get('sta_from', '')),
                'sta_to': str(row.get('sta_to', '')),
                'design_volume': round(design_vol, 3),
                'completed_volume': round(completed_vol, 3),
                'remaining_volume': round(remaining, 3),
                'progress_percent': round(progress, 2),
                'status': str(row.get('status', 'not_started'))
            })

        return result

    def get_layer_progress(self, data):
        """จัดรูปข้อมูลความก้าวหน้ารายชั้นงาน (Layer)"""
        df = data.get('layer_progress', pd.DataFrame(
        ))  # คอลัมน์ที่คาดหวัง: sta_name, layer_number, layer_name, design_volume, completed_volume, status

        if df.empty:
            return []

        result = []
        for _, row in df.iterrows():
            design_vol = float(row.get('design_volume', 0))
            completed_vol = float(row.get('completed_volume', 0))
            remaining = design_vol - completed_vol  # คงเหลือของชั้นงานนี้
            progress = (completed_vol / design_vol *
                        100) if design_vol > 0 else 0  # % ความก้าวหน้าของชั้นงานนี้

            result.append({
                'sta_name': str(row.get('sta_name', '')),
                'layer_number': int(row.get('layer_number', 0)),
                'layer_name': str(row.get('layer_name', '')),
                'design_volume': round(design_vol, 3),
                'completed_volume': round(completed_vol, 3),
                'remaining_volume': round(remaining, 3),
                'progress_percent': round(progress, 2),
                'thickness': float(row.get('thickness', 0)),
                'status': str(row.get('status', 'not_started')),
                'completion_date': str(row.get('completion_date', '')) if pd.notna(row.get('completion_date')) else None
            })

        return result

    def get_qaqc_summary(self, data):
        """สรุปผลการทดสอบ QAQC และเตรียมรายการสำหรับตาราง"""
        df = data.get('qaqc_tests', pd.DataFrame(
            # คอลัมน์ที่คาดหวัง: sta_name, layer_name, test_date, test_type, result, ฯลฯ
        ))

        if df.empty:
            return {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'pending': 0,
                'pass_rate': 0,
                'tests': []
            }

        total = len(df)  # จำนวนแถวข้อมูล QAQC ทั้งหมด
        passed = len(df[df['result'] == 'pass']
                     ) if 'result' in df.columns else 0
        failed = len(df[df['result'] == 'fail']
                     ) if 'result' in df.columns else 0
        pending = len(df[df['result'] == 'pending']
                      ) if 'result' in df.columns else 0
        pass_rate = (passed / total * 100) if total > 0 else 0  # % อัตราผ่าน

        tests = []
        for _, row in df.iterrows():
            tests.append({
                'sta_name': str(row.get('sta_name', '')),
                'layer_name': str(row.get('layer_name', '')),
                'test_date': str(row.get('test_date', ''))[:10] if pd.notna(row.get('test_date')) else '',
                'test_type': str(row.get('test_type', '')),
                'test_location': str(row.get('test_location', '')),
                'compaction_percent': float(row.get('compaction_percent', 0)) if pd.notna(row.get('compaction_percent')) else None,
                'result': str(row.get('result', 'pending')),
                'tested_by': str(row.get('tested_by', ''))
            })

        return {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'pending': pending,
            'pass_rate': round(pass_rate, 2),
            'tests': tests
        }

    def get_volume_chart_data(self, data):
        """เตรียมข้อมูลสำหรับกราฟปริมาตร (Design/Completed/Remaining)"""
        sta_df = data.get('sta_progress', pd.DataFrame()
                          )  # กราฟใช้ยอดรวมระดับ STA

        if sta_df.empty:
            return {'labels': [], 'design': [], 'completed': [], 'remaining': []}

        return {
            'labels': sta_df['sta_name'].tolist(),
            'design': sta_df['design_volume'].tolist(),
            'completed': sta_df['completed_volume'].tolist(),
            'remaining': (sta_df['design_volume'] - sta_df['completed_volume']).tolist()
        }

    def get_daily_progress(self, data):
        """ดึงและจัดรูปข้อมูลความก้าวหน้ารายวัน"""
        df = data.get('daily_progress', pd.DataFrame())

        if df.empty:
            return []

        result = []
        for _, row in df.iterrows():
            result.append({
                'date': str(row.get('record_date', ''))[:10] if pd.notna(row.get('record_date')) else '',
                'daily_volume': float(row.get('daily_volume', 0)),
                'cumulative_volume': float(row.get('cumulative_volume', 0)),
                'weather': str(row.get('weather', '')),
                'manpower': int(row.get('manpower', 0)) if pd.notna(row.get('manpower')) else 0,
                'equipment': int(row.get('equipment', 0)) if pd.notna(row.get('equipment')) else 0,
                # หมายเหตุ (ถ้ามีในชีต Daily_Progress)
                'remarks': str(row.get('remarks', '')) if pd.notna(row.get('remarks')) else ''
            })

        return result

    def _get_sample_data(self):
        """คืนค่าข้อมูลตัวอย่าง เมื่อไม่พบไฟล์ Excel"""
        # ข้อมูลสรุปตัวอย่าง
        summary_data = {
            'project_name': ['Highway Construction Project A'],
            'total_volume': [500000.0],
            'completed_volume': [145000.0],
            'remaining_volume': [355000.0]
        }

        # ข้อมูลความก้าวหน้า STA ตัวอย่าง
        sta_data = {
            'sta_name': ['STA 0+000 - 0+500', 'STA 0+500 - 1+000', 'STA 1+000 - 1+500',
                         'STA 1+500 - 2+000', 'STA 2+000 - 2+500'],
            'sta_from': ['0+000', '0+500', '1+000', '1+500', '2+000'],
            'sta_to': ['0+500', '1+000', '1+500', '2+000', '2+500'],
            'design_volume': [50000, 60000, 55000, 70000, 65000],
            'completed_volume': [45000, 60000, 30000, 10000, 0],
            'status': ['in_progress', 'completed', 'in_progress', 'in_progress', 'not_started']
        }

        # ข้อมูลความก้าวหน้า Layer ตัวอย่าง
        layer_data = {
            'sta_name': ['STA 0+000 - 0+500', 'STA 0+000 - 0+500', 'STA 0+000 - 0+500',
                         'STA 0+500 - 1+000', 'STA 0+500 - 1+000'],
            'layer_number': [1, 2, 3, 1, 2],
            'layer_name': ['Subgrade', 'Sub-base', 'Base', 'Subgrade', 'Sub-base'],
            'design_volume': [15000, 18000, 17000, 20000, 20000],
            'completed_volume': [15000, 18000, 12000, 20000, 20000],
            'thickness': [0.30, 0.25, 0.20, 0.30, 0.25],
            'status': ['completed', 'completed', 'in_progress', 'completed', 'completed'],
            'completion_date': ['2026-02-15', '2026-02-28', None, '2026-01-30', '2026-02-10']
        }

        # ข้อมูล QAQC ตัวอย่าง
        qaqc_data = {
            'sta_name': ['STA 0+000 - 0+500', 'STA 0+000 - 0+500', 'STA 0+500 - 1+000',
                         'STA 0+500 - 1+000', 'STA 1+000 - 1+500', 'STA 1+000 - 1+500'],
            'layer_name': ['Subgrade', 'Sub-base', 'Subgrade', 'Sub-base', 'Subgrade', 'Sub-base'],
            'test_date': ['2026-02-14', '2026-02-27', '2026-01-29', '2026-02-09', '2026-03-01', '2026-03-05'],
            'test_type': ['Field Density', 'Field Density', 'Field Density', 'CBR Test', 'Field Density', 'Field Density'],
            'test_location': ['0+100 LT', '0+250 CL', '0+600 CL', '0+750 RT', '1+100 LT', '1+200 CL'],
            'compaction_percent': [97.62, 99.05, 98.60, None, 96.50, 93.40],
            'result': ['pass', 'pass', 'pass', 'pass', 'pass', 'fail'],
            'tested_by': ['Engineer A', 'Engineer A', 'Engineer B', 'Engineer B', 'Engineer C', 'Engineer A']
        }

        # ข้อมูลความก้าวหน้ารายวันตัวอย่าง
        daily_data = {
            'record_date': ['2026-03-01', '2026-03-02', '2026-03-03', '2026-03-04', '2026-03-05'],
            'daily_volume': [2500, 3000, 2800, 2200, 3200],
            'cumulative_volume': [140000, 143000, 145800, 148000, 151200],
            'weather': ['Sunny', 'Cloudy', 'Sunny', 'Rainy', 'Sunny'],
            'manpower': [45, 48, 50, 30, 52],
            'equipment': [12, 12, 14, 8, 15]
        }

        return {
            'summary': pd.DataFrame(summary_data),
            'sta_progress': pd.DataFrame(sta_data),
            'layer_progress': pd.DataFrame(layer_data),
            'qaqc_tests': pd.DataFrame(qaqc_data),
            'daily_progress': pd.DataFrame(daily_data)
        }
