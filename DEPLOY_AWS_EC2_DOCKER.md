# Deploy บน AWS EC2 (Docker) — สำหรับคนเริ่มต้น (Windows)

เอกสารนี้ใช้สำหรับ deploy โปรเจกต์นี้ให้ “คนนอกเครือข่าย” เข้าได้ โดยใช้ AWS EC2 1 เครื่อง

ผลลัพธ์ที่ต้องได้:

- เปิดเว็บได้ที่ `http://<PUBLIC_IP>:8080/`
- หน้าน้ำมัน: `http://<PUBLIC_IP>:8080/fuel`

> ระวังค่าใช้จ่าย: AWS Free Tier มีเงื่อนไข/อาจมีค่าใช้จ่ายถ้าใช้งานเกินโควตา (เช่น ชั่วโมงเครื่อง, ดิสก์, IP, ทราฟฟิก)

---

## ทางลัด: Deploy อัตโนมัติด้วยสคริปต์ (แนะนำ)

ถ้าคุณมี:

- Public IP ของ EC2
- ไฟล์ key `.pem`
- URL repo บน GitHub

คุณสามารถ deploy แบบ “คำสั่งเดียว” จาก Windows ได้เลย โดยใช้สคริปต์นี้:

- [scripts/deploy-aws-ec2.ps1](scripts/deploy-aws-ec2.ps1)

ตัวอย่าง (ใช้ IP ของคุณ):

```powershell
Set-Location .\earthwork_dashboard

PowerShell -ExecutionPolicy Bypass -File .\scripts\deploy-aws-ec2.ps1 -PublicIp 3.26.217.39 -KeyPath "C:\\path\\to\\your-key.pem" -RepoUrl "https://github.com/titiwatpure/-dashboard.git"
```

เสร็จแล้วเปิด:

- `http://3.26.217.39:8080/`
- `http://3.26.217.39:8080/fuel`

---

## 1) สร้าง EC2 Instance

ไปที่ EC2 → Launch instance

ตั้งค่าตามนี้ (แนะนำ):

- **Name**: `earthwork-dashboard`
- **Amazon Machine Image (AMI)**: `Ubuntu Server 22.04 LTS` (แนะนำ)
- **Instance type**: `t2.micro` หรือ `t3.micro` (เลือกที่ขึ้นว่า Free tier eligible ถ้ามี)
- **Key pair (login)**: Create new key pair
  - Type: RSA (ค่าเริ่มต้นก็ได้)
  - Format: `.pem`
  - ดาวน์โหลดไฟล์ไว้ เช่น `C:\keys\earthwork-ec2.pem`

### Network settings (สำคัญ)

กด Edit ใน Network settings แล้วเช็คว่า Security group อนุญาต inbound:

- SSH: TCP `22` จาก `My IP` (ปลอดภัยกว่าเปิดทั้งโลก)
- Custom TCP: `8080` จาก `0.0.0.0/0` (เพื่อให้คนข้างนอกเข้าเว็บได้)

> ถ้าจะให้ปลอดภัยขึ้น: ควรทำระบบล็อกอิน/ตั้ง reverse proxy/หรือจำกัด IP แต่ MVP ตอนนี้คือเปิดพอร์ตตรง ๆ

สร้างเสร็จแล้วจด:

- **Public IPv4 address** (เช่น `3.1.2.3`)

---

## 2) SSH เข้า EC2 จาก Windows

เปิด PowerShell แล้วรัน (แทนค่าให้ถูก):

```powershell
ssh -i C:\keys\earthwork-ec2.pem ubuntu@<PUBLIC_IP>
```

ถ้าขึ้น error เรื่อง permission ของไฟล์ key ให้รัน:

```powershell
icacls C:\keys\earthwork-ec2.pem /inheritance:r
icacls C:\keys\earthwork-ec2.pem /grant:r "$env:USERNAME:(R)"
```

---

## 3) ติดตั้ง Docker + Git บน EC2

บน EC2 (Ubuntu):

```bash
sudo apt update
sudo apt install -y docker.io git
sudo usermod -aG docker $USER
exit
```

แล้ว SSH เข้าใหม่อีกครั้ง แล้วเช็ค:

```bash
docker --version
docker ps
```

---

## 4) โฟลเดอร์ข้อมูลถาวร + ดึงโค้ด

> จุดสำคัญ: เราจะ mount โฟลเดอร์ `/opt/earthwork-data` เข้าไปที่ `/app/data` ใน container
> เพื่อให้ไฟล์ `earthwork.xlsx` และฐานข้อมูลน้ำมัน `fuel.sqlite3` ไม่หายเวลา restart

บน EC2:

```bash
sudo mkdir -p /opt/earthwork-data
sudo chown -R $USER:$USER /opt/earthwork-data

cd /opt
git clone <URL_REPO_ของคุณ> earthwork_dashboard
cd earthwork_dashboard/earthwork_dashboard
```

ถ้า repo เป็น private และ clone ไม่ได้ ให้บอกผมว่าคุณใช้ GitHub แบบไหน (public/private) เดี๋ยวผมแนะนำวิธีที่ง่ายสุด

---

## 5) Build + Run ด้วย Docker

บน EC2:

```bash
docker build -t earthwork-dashboard .

docker rm -f earthwork 2>/dev/null || true

docker run -d --name earthwork --restart unless-stopped \
  -p 8080:8080 \
  -v /opt/earthwork-data:/app/data \
  earthwork-dashboard

docker ps
```

เปิดเว็บจากเครื่องคุณ:

- `http://<PUBLIC_IP>:8080/`

---

## 6) อัปเดตไฟล์ Excel (รายวัน)

แอปอ่านไฟล์นี้:

- ใน container: `/app/data/earthwork.xlsx`
- บน EC2 จริง: `/opt/earthwork-data/earthwork.xlsx`

วิธีง่ายสุด: ใช้ WinSCP อัปโหลดไฟล์ไปที่ EC2 path:

- `/opt/earthwork-data/earthwork.xlsx`

แล้วสั่งรีเฟรชข้อมูล (บน EC2):

```bash
curl -X POST http://127.0.0.1:8080/api/refresh-data
```

---

## 7) Debug ถ้าเปิดไม่ได้

บน EC2:

```bash
docker ps
curl -I http://127.0.0.1:8080/
```

บน Windows เครื่องคุณ:

```powershell
Test-NetConnection -ComputerName <PUBLIC_IP> -Port 8080
```

ถ้า `TcpTestSucceeded : False` แปลว่ายังติดที่ Security Group (Inbound rule) หรือ Instance ไม่มี Public IP
