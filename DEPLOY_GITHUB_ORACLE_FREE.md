# Deploy ฟรีด้วย GitHub + Oracle Always Free (Docker)

เอกสารนี้อธิบายการ deploy โปรเจกต์นี้ให้คนดูได้จาก “นอกเครือข่าย” โดยใช้:

- Oracle Cloud Always Free VM (เป็นเซิร์ฟเวอร์รัน Docker)
- GitHub Actions (กด deploy อัตโนมัติเมื่อ push เข้า `main`)
- อัปเดตข้อมูลรายวันผ่านไฟล์ Excel โดยอัปโหลดไปที่เซิร์ฟเวอร์

> หมายเหตุ: ตัวแอปยังไม่มีระบบล็อกอิน/สิทธิ์เข้าถึง หากเปิด public แล้ว “ใครรู้ URL ก็เข้าได้”

---

## Quickstart (ทำครั้งแรกแบบเร็ว)

ถ้าคุณยังไม่เคยสร้าง VM มาก่อน แนะนำทำตามลำดับนี้:

1. สร้าง SSH key บน Windows (ได้ไฟล์ public key)
2. สร้าง Oracle VM (เลือก Always Free eligible) และใส่ public key
3. เปิด Ingress port `22` (SSH) และ `8080` (หน้าเว็บ)
4. SSH เข้า VM → ติดตั้ง Docker + Git → clone repo
5. Push โค้ดเข้า `main` → GitHub Actions จะ deploy ให้
6. เปิดเว็บ `http://<Public-IP>:8080/`

---

## 1) สร้าง Oracle VM (Always Free)

### 1.1 สร้าง SSH key บน Windows (แนะนำ)

เปิด PowerShell แล้วรัน:

```powershell
ssh-keygen -t ed25519 -C "earthwork-oracle" -f "$env:USERPROFILE\\.ssh\\earthwork_oracle"
```

แล้วดู public key:

```powershell
Get-Content "$env:USERPROFILE\\.ssh\\earthwork_oracle.pub"
```

คัดลอกข้อความทั้งบรรทัด (เริ่มด้วย `ssh-ed25519 ...`) เพื่อเอาไปวางใน Oracle ตอนสร้าง VM

### 1.2 สร้าง Compute Instance

1. เข้า Oracle Cloud Console → **Compute** → **Instances** → **Create instance**
2. เลือก Image เป็น **Ubuntu** (แนะนำ)
3. เลือก Shape ที่เป็น **Always Free eligible**
4. ในหัวข้อ SSH keys ให้เลือก **Paste public keys** แล้ววาง public key จากข้อ 1.1
5. สร้างเสร็จแล้วจด 2 อย่างนี้ไว้:

- **Public IP**
- OS ที่เลือก (Ubuntu / Oracle Linux) เพื่อใช้เลือก username เวลา SSH

> Username ที่พบบ่อย: Ubuntu = `ubuntu`, Oracle Linux = `opc`

### 1.3 เปิด Ingress (สำคัญมาก)

ต้องเปิด 2 พอร์ต:

- `22` สำหรับ SSH
- `8080` สำหรับหน้าเว็บ

ใน Oracle มักมีได้ทั้ง **NSG** หรือ **Security List** (แล้วแต่คุณสร้างแบบไหน) ให้เพิ่ม Ingress Rules ประมาณนี้:

- Source CIDR: `0.0.0.0/0` (เพื่อทดสอบให้เข้าได้จากทุกที่)
- IP Protocol: TCP
- Destination Port Range: `22`
- Destination Port Range: `8080`

> ใน Oracle ต้องเปิดทั้ง Security List/NSG และ (ถ้ามี) firewall ใน OS

### 1.4 ทดสอบว่า SSH เข้าได้ (จาก Windows)

สมมติว่า Public IP คือ `203.0.113.10`

```powershell
ssh -i "$env:USERPROFILE\\.ssh\\earthwork_oracle" ubuntu@203.0.113.10
```

ถ้า VM เป็น Oracle Linux ให้ลอง:

```powershell
ssh -i "$env:USERPROFILE\\.ssh\\earthwork_oracle" opc@203.0.113.10
```

---

## 2) เตรียมเซิร์ฟเวอร์ (SSH เข้าเครื่อง)

### 2.1 ติดตั้ง Docker + Git

Ubuntu:

```bash
sudo apt update
sudo apt install -y docker.io git
sudo usermod -aG docker $USER
# logout/login ใหม่เพื่อให้สิทธิ์ docker มีผล
```

ตรวจว่า docker ใช้ได้ (หลัง logout/login แล้ว):

```bash
docker --version
docker ps
```

### 2.2 โฟลเดอร์แอป + โฟลเดอร์ข้อมูลถาวร

- โฟลเดอร์โค้ด (clone repo ลงเครื่อง): `/opt/earthwork_dashboard`
- โฟลเดอร์ข้อมูลถาวร (Excel + SQLite): `/opt/earthwork-data`

```bash
sudo mkdir -p /opt/earthwork_dashboard /opt/earthwork-data
sudo chown -R $USER:$USER /opt/earthwork_dashboard /opt/earthwork-data
```

### 2.3 Clone repo ลงเซิร์ฟเวอร์

แนะนำ clone แบบ SSH:

```bash
cd /opt
git clone <YOUR_GITHUB_REPO_SSH_URL> earthwork_dashboard
```

> ถ้า repo เป็น private: ใช้ deploy key หรือใช้วิธีอื่นที่คุณถนัด

---

## 3) ตั้งค่า GitHub Actions ให้ deploy อัตโนมัติ

โปรเจกต์มี workflow ที่: `.github/workflows/deploy-oracle-free.yml`

ให้ไปที่ GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

สร้าง secrets ต่อไปนี้:

- `DEPLOY_HOST` = Public IP หรือโดเมนของ VM (เช่น `203.0.113.10`)
- `DEPLOY_USER` = user สำหรับ SSH (เช่น `ubuntu` หรือ `opc`)
- `DEPLOY_SSH_KEY` = private key (OpenSSH) ที่ใช้ SSH เข้า VM
- (ไม่บังคับ) ถ้า SSH ไม่ได้ที่ port 22 ให้ปรับ workflow เองหรือเพิ่ม `port:` ตามต้องการ

เมื่อ push เข้า branch `main` → GitHub Actions จะ SSH เข้า VM แล้ว:

- `git reset --hard origin/main`
- `docker build ...`
- `docker run ...` โดย mount `/opt/earthwork-data` ไปที่ `/app/data`

เปิดเว็บ:

- `http://<Public-IP>:8080/`

ถ้าเปิดไม่ได้ ให้เช็ค 3 อย่างนี้ก่อน:

1. Oracle Ingress เปิดพอร์ต `8080` แล้ว
2. Firewall ในเครื่อง (UFW) อนุญาต `8080`
3. container รันอยู่จริง: `docker ps`

---

## 4) อัปเดตข้อมูลรายวันผ่าน Excel

ฝั่งแอปอ่านไฟล์นี้:

- `/app/data/earthwork.xlsx` (ภายใน container)

แต่เรา mount จากเครื่องจริงไว้ที่:

- `/opt/earthwork-data/earthwork.xlsx` (บน VM)

### 4.1 อัปโหลดไฟล์ Excel ไปที่ VM

ใช้ WinSCP / SFTP อัปโหลดไฟล์ใหม่ไปที่:

- `/opt/earthwork-data/earthwork.xlsx`

แนะนำให้อัปโหลดเป็นไฟล์ชั่วคราวก่อน แล้วค่อย rename เพื่อลดความเสี่ยงอ่านไฟล์ค้าง:

```bash
mv /opt/earthwork-data/earthwork_new.xlsx /opt/earthwork-data/earthwork.xlsx
```

### 4.2 สั่งให้แอปโหลดข้อมูลใหม่ทันที

หลังอัปโหลดเสร็จ ให้ SSH เข้า VM แล้วสั่ง:

```bash
curl -X POST http://127.0.0.1:8080/api/refresh-data
```

> ถ้าไม่เรียก refresh: ระบบมี cache 5 นาที แล้วจะอ่านใหม่เองเมื่อ cache หมด

---

## 5) หมายเหตุเรื่อง Fuel (น้ำมันเชื้อเพลิง)

ระบบน้ำมันเก็บ SQLite ที่:

- `/app/data/fuel.sqlite3`

เมื่อเรา mount `/opt/earthwork-data:/app/data` แล้ว ข้อมูลน้ำมันจะอยู่ที่:

- `/opt/earthwork-data/fuel.sqlite3` และจะไม่หายเมื่อ restart container
