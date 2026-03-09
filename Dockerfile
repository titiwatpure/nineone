# syntax=docker/dockerfile:1

# ใช้ Python image แบบ slim เพื่อลดขนาด
FROM python:3.13-slim

# ทำให้ log แสดงทันที และลดไฟล์ .pyc
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# ติดตั้ง dependency ก่อน เพื่อให้ cache ทำงานดี
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดแอป
COPY . .

# พอร์ตเริ่มต้น (สามารถ override ด้วย env PORT)
EXPOSE 8080

# รันด้วย Waitress (production)
CMD ["python", "serve.py"]
