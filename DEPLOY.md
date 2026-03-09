# Deploy (วิธีใช้ง่าย)

โปรเจกต์นี้เป็น Flask + อ่านข้อมูลจาก `data/earthwork.xlsx` และมีหน้าเว็บอยู่ที่ `/`.

## ตัวเลือก A: Deploy ด้วย Docker (แนะนำ)

1. สร้าง image

```bash
docker build -t earthwork-dashboard .
```

2. รัน container

```bash
docker run --rm -p 8080:8080 earthwork-dashboard
```

3. เปิดเว็บ

- http://localhost:8080

หมายเหตุ: ถ้าแพลตฟอร์มที่ deploy กำหนดพอร์ตผ่านตัวแปร `PORT` (เช่น 10000) ให้ตั้งค่า env นั้นได้:

```bash
docker run --rm -e PORT=10000 -p 10000:10000 earthwork-dashboard
```

## ตัวเลือก B: Deploy แบบไม่ใช้ Docker (VPS/Server)

1. ติดตั้ง Python 3.13+ และสร้าง venv

```bash
python -m venv .venv
```

2. ติดตั้ง dependency

```bash
pip install -r requirements.txt
```

3. รันแบบ production

```bash
python serve.py
```

- ค่าเริ่มต้นจะรันที่ `0.0.0.0:8080`
- เปลี่ยนพอร์ตได้ด้วย `PORT` เช่น

```bash
PORT=5000 python serve.py
```

## เช็คก่อน deploy

- ถ้ามีไฟล์ `data/earthwork.xlsx` ระบบจะใช้ไฟล์นั้น
- ถ้าไม่มี ระบบจะใช้ข้อมูลตัวอย่างที่อยู่ในโค้ด
