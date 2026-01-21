# BotV3 - Flask Web Application

## 📖 ภาพรวม

Flask Web Application สำหรับ BotV3 ที่รวมฟังก์ชันการประมวลผล PDF และการส่งอีเมลล์ไว้ในที่เดียว

## 🚀 การติดตั้งและใช้งาน

### 1. ติดตั้ง Dependencies

```bash
pip install -r requirements_flask.txt
```

### 2. รัน Web Application

```bash
python web_app.py
```

### 3. เปิดเบราว์เซอร์

เปิดเบราว์เซอร์และไปที่:
- **หน้าแรก**: http://localhost:5000/
- **หน้าประมวลผล PDF**: http://localhost:5000/pdf
- **หน้าส่งอีเมลล์**: http://localhost:5000/email

## 📋 ฟีเจอร์

### 🤖 ประมวลผล PDF
- เพิ่มงานประมวลผล PDF โดยระบุ path โฟลเดอร์
- ติดตามสถานะการประมวลผลแบบเรียลไทม์
- ดู progress และ log ของแต่ละงาน
- ลบงานที่เสร็จสิ้นแล้ว

### 📧 ส่งอีเมลล์
- ตั้งค่า SMTP server
- ส่งอีเมลล์เดี่ยวหรือหลายฉบับ
- รองรับการส่งแบบ HTML และ Text
- ดูประวัติการส่งอีเมลล์

## 🔧 API Endpoints

### Jobs API
- `GET /api/jobs` - ดึงข้อมูล jobs ทั้งหมด
- `POST /api/jobs` - สร้าง job ใหม่
  ```json
  {
    "folder_path": "V:/A.โฟร์เดอร์หลัก/..."
  }
  ```
- `DELETE /api/jobs/<job_id>` - ลบ job

### Email API
- `POST /api/email/config` - บันทึกการตั้งค่า SMTP
  ```json
  {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_use_tls": true,
    "smtp_username": "your-email@gmail.com",
    "smtp_password": "your-password",
    "email_from": "your-email@gmail.com"
  }
  ```
- `POST /api/email/send` - ส่งอีเมลล์
  ```json
  {
    "to_emails": ["email1@example.com", "email2@example.com"],
    "subject": "หัวข้ออีเมลล์",
    "body": "เนื้อหาอีเมลล์",
    "body_html": "<html>...</html>",
    "cc_emails": ["cc@example.com"],
    "bcc_emails": ["bcc@example.com"]
  }
  ```

## 📁 โครงสร้างไฟล์

```
BotV3/
├── web_app.py              # Flask application หลัก
├── templates/               # HTML templates
│   ├── index.html          # หน้าแรก
│   ├── pdf_processing.html # หน้าประมวลผล PDF
│   └── email_sending.html  # หน้าส่งอีเมลล์
└── static/                 # Static files (CSS, JS, images)
```

## ⚙️ การตั้งค่า

### SMTP Configuration
1. ไปที่หน้า "ส่งอีเมลล์"
2. กรอกข้อมูล SMTP:
   - **SMTP Server**: เช่น `smtp.gmail.com`
   - **SMTP Port**: เช่น `587` (TLS) หรือ `465` (SSL)
   - **Username**: อีเมลล์ของคุณ
   - **Password**: รหัสผ่านหรือ App Password
3. กด "บันทึกการตั้งค่า"

### Gmail App Password
สำหรับ Gmail ต้องใช้ App Password:
1. ไปที่ Google Account Settings
2. Security → 2-Step Verification → App passwords
3. สร้าง App Password สำหรับ "Mail"
4. ใช้ App Password แทนรหัสผ่านปกติ

## 🔄 ความแตกต่างจาก Streamlit

### ข้อดีของ Flask Web App
- ✅ ควบคุม UI ได้เต็มที่ (HTML/CSS/JavaScript)
- ✅ Performance ดีกว่า (ไม่มี overhead ของ Streamlit)
- ✅ Customizable มากกว่า
- ✅ ใช้ REST API ได้ง่าย
- ✅ Deploy ได้หลากหลาย (Docker, Cloud, etc.)

### ข้อเสีย
- ❌ ต้องเขียน HTML/CSS/JavaScript เอง
- ❌ ใช้เวลาในการพัฒนา UI มากกว่า

## 🐛 Troubleshooting

### Port 5000 ถูกใช้งานแล้ว
เปลี่ยน port ใน `web_app.py`:
```python
app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False)
```

### ไม่สามารถ import modules ได้
ตรวจสอบว่า:
- ไฟล์ `config.py`, `main_system.py`, `email_manager.py` อยู่ในโฟลเดอร์เดียวกัน
- ติดตั้ง dependencies ทั้งหมดแล้ว

### SMTP Connection Error
- ตรวจสอบว่า SMTP server และ port ถูกต้อง
- สำหรับ Gmail ต้องใช้ App Password
- ตรวจสอบ firewall และ network settings

## 📝 หมายเหตุ

- Web app นี้ใช้ Flask development server ซึ่งไม่เหมาะสำหรับ production
- สำหรับ production ควรใช้ Gunicorn, uWSGI, หรือ WSGI server อื่นๆ
- ควรเพิ่ม authentication และ security measures สำหรับ production

## 🔗 ดูเพิ่มเติม

- [Flask Documentation](https://flask.palletsprojects.com/)
- [BotV3 Main Documentation](./README.md)

