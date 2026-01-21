# 🖥️ BotV3 Desktop Application

ระบบประมวลผล PDF อัตโนมัติแบบ Desktop Application (ไม่ต้องใช้เว็บเบราว์เซอร์)

---

## 📋 คุณสมบัติ

✅ **UI สวยงาม** - ใช้ Tkinter ทำ Desktop App
✅ **ไม่ต้องผ่าน Web Browser** - รันได้เลยโดยตรง
✅ **Build เป็น EXE** - สามารถคัดลอกไปใช้ในเครื่องอื่นได้
✅ **ทำงานแบบ Standalone** - ไม่ต้อง Flask หรือ API
✅ **Real-time Logging** - ดูสถานะการทำงานแบบ Real-time
✅ **เลือกโฟลเดอร์ได้** - เลือกโฟลเดอร์ที่ต้องการประมวลผล
✅ **รองรับโหมดลูป** - ทำงานต่อเนื่องแบบอัตโนมัติ

---

## 🚀 วิธีใช้งาน

### **วิธีที่ 1: รันจาก Python (พัฒนา/ทดสอบ)**

```bash
# 1. ติดตั้ง dependencies (ไม่ต้องติดตั้ง Flask)
pip install playwright PyPDF2 pandas openpyxl Pillow python-dotenv
playwright install chromium

# 2. รันโปรแกรม
python bot_gui_tkinter.py
```

### **วิธีที่ 2: Build เป็น EXE (แจกจ่าย)**

```bash
# 1. Build exe
python build_exe.py

# 2. ไฟล์ exe จะอยู่ที่
dist/BotV3.exe

# 3. คัดลอกไฟล์นี้ไปใช้ในเครื่องอื่นได้เลย
```

---

## 🎯 ส่วนประกอบของ UI

```
┌────────────────────────────────────────────────────────────┐
│ 🤖 BotV3 - ระบบประมวลผล PDF อัตโนมัติ                      │
├──────────────────┬─────────────────────────────────────────┤
│ 📁 เลือกโฟลเดอร์  │ 📝 บันทึกการทำงาน                       │
│                  │                                         │
│ ☑ Build001      │ [09:30:15] 🔍 กำลังสแกนโฟลเดอร์...     │
│ ☑ Build002      │ [09:30:16] ✅ พบโฟลเดอร์: 5 โฟลเดอร์    │
│ ☐ Build003      │ [09:30:20] ▶️ เริ่มการทำงาน...          │
│                  │ [09:30:25] 📂 ประมวลผล: Build001       │
│ [✓ เลือกทั้งหมด] │ [09:30:30] 📄 อ่านไฟล์ PDF: inv001.pdf │
│                  │ [09:30:35] ✅ สร้างไฟล์สำเร็จ           │
│ ⚙️ ควบคุมระบบ    │                                         │
│                  │                                         │
│ [▶️ เริ่มการทำงาน]│                                         │
│ [🔄 เริ่มระบบลูป]│                                         │
│ [⏹️ หยุดการทำงาน]│                                         │
│ [🧪 ทดสอบระบบ]  │                                         │
│                  │                                         │
│ 📊 สถานะ         │                                         │
│ สถานะ: กำลังทำงาน│ [🗑️ ล้างบันทึก]                        │
│ ไฟล์: inv001.pdf │                                         │
│ โฟลเดอร์: Build001│                                        │
│ [████████░░░░]   │                                         │
└──────────────────┴─────────────────────────────────────────┘
```

---

## 🎨 คุณสมบัติของ UI

### **1. Panel เลือกโฟลเดอร์**
- ✅ แสดงรายการโฟลเดอร์ที่สแกนได้
- ✅ เลือกได้หลายโฟลเดอร์พร้อมกัน (Ctrl+Click)
- ✅ ปุ่ม "เลือกทั้งหมด" สำหรับเลือกครั้งเดียว

### **2. ปุ่มควบคุม**
- **▶️ เริ่มการทำงาน** - รันครั้งเดียว
- **🔄 เริ่มระบบลูป** - รันต่อเนื่อง (ลูปทุก 15 วินาที)
- **⏹️ หยุดการทำงาน** - หยุดทันที
- **🧪 ทดสอบระบบ** - ทดสอบกับโฟลเดอร์ Build000

### **3. แสดงสถานะ**
- ✅ สถานะปัจจุบัน (พร้อมใช้งาน/กำลังทำงาน/หยุด)
- ✅ ไฟล์ที่กำลังประมวลผล
- ✅ โฟลเดอร์ปัจจุบัน
- ✅ Progress bar แบบ Indeterminate

### **4. บันทึกการทำงาน**
- ✅ แสดง log แบบ Real-time
- ✅ สี coded (เขียว=สำเร็จ, แดง=ผิดพลาด, ส้ม=คำเตือน, ฟ้า=ข้อมูล)
- ✅ Auto-scroll ไปที่บรรทัดล่าสุด
- ✅ แสดง timestamp

---

## ⚙️ การตั้งค่า

### **แก้ไข config.py สำหรับเครื่องอื่น**

```python
# ถ้าเครื่องใหม่ไม่มี V: drive
class Config:
    # แก้จาก "V" เป็น path ที่มีจริง
    BASE_FOLDER = "C:/SharedData"  # ตัวอย่าง
    
    # หรือใช้ auto-detect
    import os
    from pathlib import Path
    
    if Path("V:/").exists():
        BASE_FOLDER = "V"
    elif Path("Z:/").exists():
        BASE_FOLDER = "Z"
    else:
        BASE_FOLDER = "C:/Data"
```

---

## 📦 Build เป็น EXE

### **ขั้นตอน:**

```bash
# 1. ติดตั้ง PyInstaller
pip install pyinstaller

# 2. Build
python build_exe.py

# 3. ผลลัพธ์
dist/
├── BotV3.exe       # ← ไฟล์นี้
└── BotV3/          # โฟลเดอร์ temp (ลบได้)
```

### **ขนาดไฟล์:**
- **One-file EXE**: ~80-100 MB
- **One-folder**: ~150-200 MB

### **Build Options:**

#### **แบบ One-file (แนะนำ)**
```bash
pyinstaller --onefile --windowed --name=BotV3 bot_gui_tkinter.py
```

#### **แบบ One-folder (เร็วกว่า)**
```bash
pyinstaller --windowed --name=BotV3 bot_gui_tkinter.py
```

#### **แบบมี Console (Debug)**
```bash
pyinstaller --onefile --name=BotV3 bot_gui_tkinter.py
```

---

## 🔧 การใช้งานในเครื่องอื่น

### **ไม่ต้องติดตั้ง Python!**

1. ✅ คัดลอก `BotV3.exe` ไปเครื่องใหม่
2. ✅ ตรวจสอบว่ามี `V:` drive หรือแก้ `config.py`
3. ✅ Double-click `BotV3.exe` เพื่อรัน

### **สิ่งที่ต้องมี:**
- ✅ Windows 10/11
- ✅ V: drive (หรือ path ที่กำหนดใน config)
- ✅ Internet (สำหรับ Playwright เข้าเว็บ)

### **สิ่งที่ไม่ต้องมี:**
- ❌ Python
- ❌ pip
- ❌ Flask
- ❌ Web Browser สำหรับเปิด UI

---

## 🆚 เปรียบเทียบกับ Web UI

| ฟีเจอร์ | Desktop App | Web UI |
|--------|------------|--------|
| **ติดตั้ง** | ✅ คัดลอก exe เดียว | ⚠️ ต้องติดตั้ง Python + libs |
| **รันโปรแกรม** | ✅ Double-click | ⚠️ `python control_api.py` |
| **เปิด UI** | ✅ เปิดอัตโนมัติ | ⚠️ ต้องเปิด browser |
| **API** | ✅ ไม่ต้องใช้ | ⚠️ ต้อง Flask API |
| **Polling** | ✅ ไม่มี | ⚠️ เรียก API ทุก 2 วิ |
| **Performance** | ✅ เร็วกว่า | ⚠️ ช้ากว่า |
| **ขนาด** | ⚠️ ~100 MB | ✅ ~10 MB |

---

## 🐛 การแก้ปัญหา

### **ปัญหา: ไม่พบ V: drive**
```
แก้ไข: config.py
BASE_FOLDER = "C:/YourPath"
```

### **ปัญหา: exe ไม่เปิด**
```
ลอง build แบบมี console:
pyinstaller --onefile --name=BotV3 bot_gui_tkinter.py

จะเห็น error message
```

### **ปัญหา: Playwright ไม่ทำงาน**
```
ติดตั้ง browsers บนเครื่องนั้น:
playwright install chromium
```

### **ปัญหา: ไฟล์ใหญ่เกินไป**
```
ใช้แบบ one-folder แทน:
pyinstaller --windowed --name=BotV3 bot_gui_tkinter.py
```

---

## 📝 Requirements

```txt
# สำหรับ Desktop App (ไม่ต้อง Flask)
playwright==1.40.0
PyPDF2==3.0.1
pandas==2.1.3
openpyxl==3.1.2
Pillow==10.1.0
python-dotenv==1.0.0

# สำหรับ build exe
pyinstaller==6.3.0
```

---

## 🎉 ข้อดีของ Desktop App

1. ✅ **ไม่ต้องใช้ Web Browser** - ไม่มี API polling
2. ✅ **รันเร็วกว่า** - ไม่ต้อง request/response
3. ✅ **ใช้งานง่าย** - Double-click เดียว
4. ✅ **แจกจ่ายง่าย** - คัดลอก exe ไปได้เลย
5. ✅ **UI สวยงาม** - มี progress bar และ color coding
6. ✅ **Thread-safe** - ทำงานหนักแยกเธรด ไม่แฮง

---

## 📞 สนับสนุน

หากมีปัญหา:
1. ตรวจสอบ log ใน UI
2. ลอง build แบบมี console
3. ตรวจสอบ V: drive
4. อ่าน error message

---

**สร้างโดย:** BotV3 Team  
**เวอร์ชัน:** 3.0  
**วันที่:** 2025-01-13


