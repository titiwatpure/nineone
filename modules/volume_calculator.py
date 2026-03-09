"""โมดูลคำนวณปริมาตร (Volume Calculator)

รวมฟังก์ชันช่วยคำนวณปริมาตรงานดิน เช่น ปริมาตรรวม ปริมาตรที่ทำแล้ว และเปอร์เซ็นต์ความก้าวหน้า
"""


class VolumeCalculator:
    def __init__(self):
        self.unit = 'm³'  # หน่วยเริ่มต้น: ลูกบาศก์เมตร

    def calculate_total_volume(self, data):
        """คำนวณปริมาตรรวม (ออกแบบ/แผนงาน) จากข้อมูล"""
        summary_df = data.get('summary')  # ชีต Summary (แนะนำให้ใช้ก่อน)
        sta_df = data.get('sta_progress')  # ชีต STA (ใช้เป็นทางเลือกสำรอง)

        # พยายามดึงจาก Summary ก่อน
        if summary_df is not None and not summary_df.empty:
            if 'total_volume' in summary_df.columns:
                # ค่า total_volume แถวแรก
                return float(summary_df['total_volume'].iloc[0])

        # ถ้าไม่มี Summary ให้รวมยอดจาก STA
        if sta_df is not None and not sta_df.empty:
            if 'design_volume' in sta_df.columns:
                # รวม design_volume ของทุก STA
                return float(sta_df['design_volume'].sum())

        return 0.0

    def calculate_completed_volume(self, data):
        """คำนวณปริมาตรที่ทำแล้ว (Actual) จากข้อมูล"""
        summary_df = data.get('summary')  # ชีต Summary (แนะนำให้ใช้ก่อน)
        sta_df = data.get('sta_progress')  # ชีต STA (ใช้เป็นทางเลือกสำรอง)

        # พยายามดึงจาก Summary ก่อน
        if summary_df is not None and not summary_df.empty:
            if 'completed_volume' in summary_df.columns:
                # ค่า completed_volume แถวแรก
                return float(summary_df['completed_volume'].iloc[0])

        # ถ้าไม่มี Summary ให้รวมยอดจาก STA
        if sta_df is not None and not sta_df.empty:
            if 'completed_volume' in sta_df.columns:
                # รวม completed_volume ของทุก STA
                return float(sta_df['completed_volume'].sum())

        return 0.0

    def calculate_remaining_volume(self, total, completed):
        """คำนวณปริมาตรคงเหลือ"""
        return total - completed  # คงเหลือ = รวม - ทำแล้ว

    def calculate_completion_percentage(self, total, completed):
        """คำนวณเปอร์เซ็นต์ความก้าวหน้า"""
        if total <= 0:
            return 0.0
        return (completed / total) * 100  # % ความคืบหน้า

    def calculate_cut_fill_balance(self, cut_volume, fill_volume):
        """คำนวณสมดุล Cut/Fill"""
        return {
            'cut': cut_volume,
            'fill': fill_volume,
            'balance': cut_volume - fill_volume,
            'borrow_required': max(0, fill_volume - cut_volume),
            'waste': max(0, cut_volume - fill_volume)
        }

    def calculate_layer_volume(self, area, thickness):
        """คำนวณปริมาตรของชั้นงานจากพื้นที่และความหนา"""
        return area * thickness

    def calculate_compaction_factor(self, loose_volume, compacted_volume):
        """คำนวณค่า Compaction Factor (อัตราส่วนหลวมต่อแน่น)"""
        if compacted_volume <= 0:
            return 1.0
        return loose_volume / compacted_volume
