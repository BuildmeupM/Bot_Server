# คู่มือการตั้งค่า Ngrok สำหรับส่งไฟล์ PDF ไปยัง LINE

## ขั้นตอนการติดตั้งและใช้งาน Ngrok

### 1. ดาวน์โหลดและติดตั้ง Ngrok

#### Windows:
1. ไปที่ https://ngrok.com/download
2. ดาวน์โหลดไฟล์ `ngrok.exe` สำหรับ Windows
3. วางไฟล์ `ngrok.exe` ในโฟลเดอร์ที่ต้องการ (เช่น `C:\ngrok\`)

#### หรือใช้ Chocolatey:
```powershell
choco install ngrok
```

#### หรือใช้ Scoop:
```powershell
scoop install ngrok
```

### 2. ลงทะเบียนและรับ Auth Token

1. ไปที่ https://dashboard.ngrok.com/signup
2. สร้างบัญชี (ฟรี)
3. ไปที่ https://dashboard.ngrok.com/get-started/your-authtoken
4. คัดลอก Auth Token

### 3. ตั้งค่า Ngrok

เปิด Command Prompt หรือ PowerShell และรัน:

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

(แทนที่ `YOUR_AUTH_TOKEN` ด้วย token ที่คัดลอกมา)

**หมายเหตุ:** ถ้าเจอ error `unknown version '3'` ให้แก้ไขไฟล์ config:
- เปิดไฟล์ `C:\Users\USER\AppData\Local\ngrok\ngrok.yml`
- เปลี่ยน `version: "3"` เป็น `version: "2"`
- หรือลบบรรทัด `version:` ออก

### 4. เริ่มต้น Ngrok

รันคำสั่งต่อไปนี้ใน terminal ใหม่ (ให้ Flask app ยังรันอยู่ที่ port 5000):

```bash
ngrok http 5000
```

หรือถ้าต้องการให้รันใน background:

```bash
ngrok http 5000 --log=stdout
```

### 5. คัดลอก HTTPS URL

หลังจากรัน ngrok แล้ว คุณจะเห็น output แบบนี้:

```
Forwarding   https://xxxx-xxxx-xxxx.ngrok-free.app -> http://localhost:5000
```

คัดลอก URL ที่ขึ้นต้นด้วย `https://` (เช่น `https://xxxx-xxxx-xxxx.ngrok-free.app`)

### 6. ตั้งค่าใน config.py

เปิดไฟล์ `config.py` และแก้ไข:

```python
# Ngrok Settings
NGROK_ENABLED = True  # เปิดใช้งาน ngrok
NGROK_URL = "https://xxxx-xxxx-xxxx.ngrok-free.app"  # ใส่ URL จาก ngrok
NGROK_API_URL = "http://localhost:4040/api/tunnels"  # Ngrok API endpoint (สำหรับดึง URL อัตโนมัติ)
```

**หมายเหตุ:** ถ้าไม่ระบุ `NGROK_URL` ระบบจะพยายามดึง URL อัตโนมัติจาก ngrok API

### 7. รีสตาร์ท Flask App

รีสตาร์ท Flask app เพื่อให้การตั้งค่าใหม่มีผล

## การใช้งาน

1. เริ่มต้น Flask app (port 5000)
2. เริ่มต้น ngrok (`ngrok http 5000`)
3. ตั้งค่า `NGROK_ENABLED = True` ใน `config.py`
4. ส่งอีเมลพร้อม PDF สรุป
5. ระบบจะส่งไฟล์ PDF ไปยัง LINE โดยใช้ HTTPS URL จาก ngrok

## หมายเหตุ

- **URL จะเปลี่ยนทุกครั้งที่รัน ngrok ใหม่** (เว้นแต่จะใช้ ngrok paid plan)
- **ต้องรัน ngrok และ Flask app พร้อมกัน** เพื่อให้ระบบทำงานได้
- **สำหรับ production** ควรใช้ domain และ SSL certificate จริง แทน ngrok

## ทางเลือกอื่น

### ใช้ ngrok ด้วย Python (อัตโนมัติ)

สามารถใช้ library `pyngrok` เพื่อรัน ngrok จาก Python:

```bash
pip install pyngrok
```

แล้วเพิ่มโค้ดใน `web_app.py`:

```python
from pyngrok import ngrok

# เริ่มต้น ngrok
public_url = ngrok.connect(5000)
print(f"Ngrok URL: {public_url}")
```

## Troubleshooting

### ปัญหา: Ngrok URL ไม่ทำงาน
- ตรวจสอบว่า ngrok ยังรันอยู่
- ตรวจสอบว่า Flask app รันที่ port 5000
- ตรวจสอบว่า `NGROK_ENABLED = True` ใน config.py

### ปัญหา: LINE API ยังไม่ยอมรับ URL
- ตรวจสอบว่า URL ขึ้นต้นด้วย `https://` (ไม่ใช่ `http://`)
- ตรวจสอบว่าไฟล์ PDF สามารถเข้าถึงได้ผ่าน URL นั้น

