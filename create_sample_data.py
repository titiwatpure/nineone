"""สคริปต์สร้างไฟล์ข้อมูลตัวอย่าง earthwork.xlsx

รันสคริปต์นี้ 1 ครั้งเพื่อสร้างข้อมูลตัวอย่าง (หลายชีต) สำหรับใช้กับหน้าแดชบอร์ด
"""

import pandas as pd
import os

# หาพาธโฟลเดอร์ที่สคริปต์นี้อยู่
BASE_DIR = os.path.dirname(os.path.abspath(
    __file__))  # โฟลเดอร์ earthwork_dashboard
DATA_DIR = os.path.join(BASE_DIR, 'data')  # โฟลเดอร์ที่เก็บไฟล์ Excel
OUTPUT_FILE = os.path.join(DATA_DIR, 'earthwork.xlsx')  # พาธไฟล์ปลายทาง

# สร้างโฟลเดอร์ data ถ้ายังไม่มี
os.makedirs(DATA_DIR, exist_ok=True)  # สร้าง ./data หากยังไม่อยู่

# ชีต Summary (สรุปภาพรวมโครงการ)
summary_data = {
    'project_name': ['Highway Construction Project A'],
    'project_code': ['HWY-001'],
    'total_volume': [300000.0],
    'completed_volume': [145000.0],
    'remaining_volume': [155000.0],
    'start_date': ['2026-01-01'],
    'end_date': ['2026-12-31']
}

# ชีต STA_Progress (ความก้าวหน้าระดับช่วงสถานี)
sta_data = {
    'sta_name': [
        'STA 0+000 - 0+500',
        'STA 0+500 - 1+000',
        'STA 1+000 - 1+500',
        'STA 1+500 - 2+000',
        'STA 2+000 - 2+500'
    ],
    'sta_from': ['0+000', '0+500', '1+000', '1+500', '2+000'],
    'sta_to': ['0+500', '1+000', '1+500', '2+000', '2+500'],
    'design_volume': [50000, 60000, 55000, 70000, 65000],
    'completed_volume': [45000, 60000, 30000, 10000, 0],
    'status': ['in_progress', 'completed', 'in_progress', 'in_progress', 'not_started']
}

# ชีต Layer_Progress (ความก้าวหน้าระดับชั้นงาน)
layer_data = {
    'sta_name': [
        'STA 0+000 - 0+500', 'STA 0+000 - 0+500', 'STA 0+000 - 0+500', 'STA 0+000 - 0+500',
        'STA 0+500 - 1+000', 'STA 0+500 - 1+000', 'STA 0+500 - 1+000', 'STA 0+500 - 1+000',
        'STA 1+000 - 1+500', 'STA 1+000 - 1+500'
    ],
    'layer_number': [1, 2, 3, 4, 1, 2, 3, 4, 1, 2],
    'layer_name': [
        'Subgrade', 'Sub-base', 'Base', 'Wearing Course',
        'Subgrade', 'Sub-base', 'Base', 'Wearing Course',
        'Subgrade', 'Sub-base'
    ],
    'design_volume': [12500, 12500, 12500, 12500, 15000, 15000, 15000, 15000, 13750, 13750],
    'completed_volume': [12500, 12500, 12000, 8000, 15000, 15000, 15000, 15000, 13750, 10000],
    'thickness': [0.30, 0.25, 0.20, 0.15, 0.30, 0.25, 0.20, 0.15, 0.30, 0.25],
    'status': [
        'completed', 'completed', 'in_progress', 'in_progress',
        'completed', 'completed', 'completed', 'completed',
        'completed', 'in_progress'
    ],
    'completion_date': [
        '2026-02-15', '2026-02-28', None, None,
        '2026-01-30', '2026-02-10', '2026-02-20', '2026-03-01',
        '2026-02-25', None
    ]
}

# ชีต QAQC_Tests (บันทึกผลการทดสอบ)
qaqc_data = {
    'sta_name': [
        'STA 0+000 - 0+500', 'STA 0+000 - 0+500', 'STA 0+000 - 0+500',
        'STA 0+500 - 1+000', 'STA 0+500 - 1+000', 'STA 0+500 - 1+000',
        'STA 1+000 - 1+500', 'STA 1+000 - 1+500'
    ],
    'layer_name': [
        'Subgrade', 'Sub-base', 'Base',
        'Subgrade', 'Sub-base', 'Base',
        'Subgrade', 'Sub-base'
    ],
    'test_date': [
        '2026-02-14', '2026-02-27', '2026-03-05',
        '2026-01-29', '2026-02-09', '2026-02-19',
        '2026-02-24', '2026-03-04'
    ],
    'test_type': [
        'Field Density', 'Field Density', 'Field Density',
        'Field Density', 'CBR Test', 'Field Density',
        'Field Density', 'Field Density'
    ],
    'test_location': [
        '0+100 LT', '0+250 CL', '0+400 RT',
        '0+600 CL', '0+750 RT', '0+900 LT',
        '1+100 CL', '1+300 RT'
    ],
    'field_density': [2.05, 2.08, 1.98, 2.12, None, 2.10, 2.06, 1.95],
    'max_dry_density': [2.10, 2.10, 2.12, 2.15, None, 2.12, 2.10, 2.10],
    'compaction_percent': [97.62, 99.05, 93.40, 98.60, None, 99.06, 98.10, 92.86],
    'moisture_content': [8.5, 8.8, 9.2, 8.2, None, 8.0, 8.4, 9.5],
    'optimum_moisture': [9.0, 9.0, 8.5, 8.5, None, 8.5, 9.0, 9.0],
    'result': ['pass', 'pass', 'fail', 'pass', 'pass', 'pass', 'pass', 'fail'],
    'tested_by': [
        'Engineer A', 'Engineer A', 'Engineer A',
        'Engineer B', 'Engineer B', 'Engineer B',
        'Engineer C', 'Engineer C'
    ]
}

# ชีต Daily_Progress (บันทึกความก้าวหน้ารายวัน)
daily_data = {
    'record_date': [
        '2026-03-01', '2026-03-02', '2026-03-03',
        '2026-03-04', '2026-03-05', '2026-03-06', '2026-03-07'
    ],
    'daily_volume': [2500, 3000, 2800, 2200, 3200, 2900, 3100],
    'cumulative_volume': [130000, 133000, 135800, 138000, 141200, 144100, 147200],
    'weather': ['Sunny', 'Cloudy', 'Sunny', 'Rainy', 'Sunny', 'Sunny', 'Cloudy'],
    'manpower': [45, 48, 50, 30, 52, 50, 48],
    'equipment': [12, 12, 14, 8, 15, 14, 13],
    'remarks': [
        'Normal operation',
        'Good progress',
        'Ahead of schedule',
        'Rain delay - afternoon',
        'Catch up work',
        'Normal operation',
        'Weekend overtime'
    ]
}

# สร้าง DataFrame จาก dict
df_summary = pd.DataFrame(summary_data)
df_sta = pd.DataFrame(sta_data)
df_layer = pd.DataFrame(layer_data)
df_qaqc = pd.DataFrame(qaqc_data)
df_daily = pd.DataFrame(daily_data)

# เขียนลง Excel หลายชีตในไฟล์เดียว
with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
    df_summary.to_excel(writer, sheet_name='Summary', index=False)
    df_sta.to_excel(writer, sheet_name='STA_Progress', index=False)
    df_layer.to_excel(writer, sheet_name='Layer_Progress', index=False)
    df_qaqc.to_excel(writer, sheet_name='QAQC_Tests', index=False)
    df_daily.to_excel(writer, sheet_name='Daily_Progress', index=False)

print(f"สร้างไฟล์ข้อมูลตัวอย่างแล้ว: {OUTPUT_FILE}")
print("\nสร้างชีตแล้ว:")
print("  - Summary")
print("  - STA_Progress")
print("  - Layer_Progress")
print("  - QAQC_Tests")
print("  - Daily_Progress")
