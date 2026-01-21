#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BotV3 Installation Script
สคริปต์ติดตั้งระบบ BotV3 อัตโนมัติ
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
import platform

class BotV3Installer:
    def __init__(self):
        self.install_dir = Path.cwd()
        self.python_version = sys.version_info
        self.platform_name = platform.system()
        
    def print_header(self):
        """แสดงหัวข้อการติดตั้ง"""
        print("=" * 60)
        print("🤖 BotV3 Installation Script")
        print("   ระบบประมวลผล PDF อัตโนมัติ")
        print("=" * 60)
        print(f"📋 ข้อมูลระบบ:")
        print(f"   - Python Version: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        print(f"   - Platform: {self.platform_name}")
        print(f"   - Install Directory: {self.install_dir}")
        print("=" * 60)
        
    def check_python_version(self):
        """ตรวจสอบเวอร์ชัน Python"""
        print("\n🔍 ตรวจสอบเวอร์ชัน Python...")
        
        if self.python_version.major < 3 or (self.python_version.major == 3 and self.python_version.minor < 8):
            print("❌ ต้องการ Python 3.8 หรือสูงกว่า")
            print(f"   เวอร์ชันปัจจุบัน: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
            return False
            
        print(f"✅ Python Version: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        return True
        
    def check_pip(self):
        """ตรวจสอบ pip"""
        print("\n🔍 ตรวจสอบ pip...")
        
        try:
            import pip
            print("✅ pip พร้อมใช้งาน")
            return True
        except ImportError:
            print("❌ ไม่พบ pip")
            print("   กรุณาติดตั้ง pip ก่อน")
            return False
            
    def install_requirements(self):
        """ติดตั้ง requirements"""
        print("\n📦 ติดตั้ง requirements...")
        
        requirements_files = [
            "requirements.txt",
            "requirements_desktop.txt", 
            "requirements_flask.txt",
            "requirements_playwright.txt"
        ]
        
        for req_file in requirements_files:
            if Path(req_file).exists():
                print(f"\n📋 ติดตั้งจาก {req_file}...")
                try:
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install", "-r", req_file
                    ])
                    print(f"✅ ติดตั้ง {req_file} สำเร็จ")
                except subprocess.CalledProcessError as e:
                    print(f"❌ ติดตั้ง {req_file} ไม่สำเร็จ: {e}")
                    return False
            else:
                print(f"⚠️ ไม่พบไฟล์ {req_file}")
                
        return True
        
    def install_playwright_browsers(self):
        """ติดตั้ง Playwright browsers"""
        print("\n🌐 ติดตั้ง Playwright browsers...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "playwright", "install", "chromium"
            ])
            print("✅ ติดตั้ง Playwright Chromium สำเร็จ")
            
            # ติดตั้ง system dependencies (สำหรับ Linux)
            if self.platform_name == "Linux":
                try:
                    subprocess.check_call([
                        sys.executable, "-m", "playwright", "install-deps", "chromium"
                    ])
                    print("✅ ติดตั้ง system dependencies สำเร็จ")
                except subprocess.CalledProcessError:
                    print("⚠️ ไม่สามารถติดตั้ง system dependencies ได้ (อาจต้องใช้ sudo)")
                    
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ ติดตั้ง Playwright browsers ไม่สำเร็จ: {e}")
            return False
            
    def create_directories(self):
        """สร้างโฟลเดอร์ที่จำเป็น"""
        print("\n📁 สร้างโฟลเดอร์ที่จำเป็น...")
        
        directories = [
            "temp_uploads",
            "รหัส",
            "folder_settings",
            "เอกสารต้นฉบับ",
            "เอกสารบันทึกแล้ว",
            "เอกสารบันทึกแล้ว/เอกสาร Vat",
            "เอกสารบันทึกแล้ว/เอกสาร NoneVat",
            "เอกสารซ้ำรอตรวจ",
            "เอกสารฐานข้อมูลไม่เรียบร้อย",
            "เอกสารรอดำเนินการ",
            "เอกสารอ่านข้อมูลไม่ได้",
            "เอกสารอ่านข้อมูลไม่ได้/เอกสาร PDF ภาพ",
            "เอกสารอ่านข้อมูลไม่ได้/ยังไม่ได้นำเข้าระบบ"
        ]
        
        for directory in directories:
            dir_path = Path(directory)
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ สร้างโฟลเดอร์: {directory}")
            except Exception as e:
                print(f"❌ ไม่สามารถสร้างโฟลเดอร์ {directory}: {e}")
                
    def create_config_template(self):
        """สร้างไฟล์ config template"""
        print("\n⚙️ สร้างไฟล์ config template...")
        
        config_template = '''# -*- coding: utf-8 -*-
"""
BotV3 Configuration Template
ไฟล์การตั้งค่าระบบ BotV3
กรุณาแก้ไขข้อมูลให้ตรงกับระบบของคุณ
"""

import os
from pathlib import Path

class Config:
    # โครงสร้างโฟลเดอร์หลัก
    BASE_FOLDER = "V"  # หรือ "Synology"
    TEST_SYSTEM_FOLDER = "000 ทดสอบระบบ"
    
    # โฟลเดอร์หลักที่ต้องสแกน
    MAIN_FOLDERS = ["A.โฟร์เดอร์หลัก", "AA.โฟรเดอร์หลัก", "AAA.โฟรเดอร์หลัก"]
    
    # โฟลเดอร์ที่ต้องข้าม
    SKIP_FOLDERS = ["#recycle", "#snapshot", "A.BMUT", "A.Buildmeup", "A.งานนอก"]

    # โฟลเดอร์ที่ต้องเข้า
    CUSTOMER_FOLDER = "ลูกค้า"
    AUTOMATION_FOLDER = "ระบบอัตโนมัติ"
    
    # การตั้งค่าการประมวลผล
    MAX_PROCESSING_ITEMS = 60  # จำกัดจำนวนการประมวลผลสูงสุด
    
    # การตั้งค่าการแจ้งเตือน LINE
    LINE_NOTIFY_TOKEN = ""  # กรอก LINE Notify Token ของคุณ
    
    # LINE OA (Messaging API) - ตัวผู้ใช้จะกรอก token/secret เอง
    LINE_OA_CHANNEL_ACCESS_TOKEN = ""  # กรอก LINE OA Channel Access Token
    LINE_OA_CHANNEL_SECRET = ""        # ใช้ตรวจสอบลายเซ็นตอนรับ Webhook
    LINE_OA_DEFAULT_TO = ""            # userId/groupId/roomId ปลายทางสำหรับ push
    
    # URL เป้าหมาย
    PEAK_ENGINE_URL = "https://secure.peakengine.com/Home/Login"
    
    # การตั้งค่า Selenium/Playwright
    SELENIUM_TIMEOUT = 30
    
    # การจัดกลุ่มบริษัท (VAT/NoneVat)
    COMPANY_VAT_STATUS = {
        "Shopee (Thailand) Co., Ltd.": "VAT",
        "Lazada Limited (Head Office)": "VAT",
        "SPX Express (Thailand) Co., Ltd.": "NoneVat",
        "gf.th.ar@grab.com": "VAT",
        "K-BIZ Contact": "VAT",
        "Delivery Hero (Thailand) Co., Ltd.": "VAT",
        "Purple Ventures Company Limited": "VAT",
        "บริษัท ทรู มันนี่ จำกัด": "VAT",
        "บริษัท ไลน์แมน (ประเทศไทย) จำกัด (สำนักงานใหญ่)": "VAT",
        "บริษัท กาแฟพันธุ์ไทย จำกัด": "VAT",
        # เพิ่มบริษัทอื่นๆ ตามต้องการ
    }
    
    # การ mapping ชื่อบริการ (GROUP1 - regular)
    GROUP1_COMPANY_MAPPING = {
        "Shopee (Thailand) Co., Ltd.": "ค่าบริการ Shopee VAT",
        "Lazada Limited (Head Office)": "ค่าบริการ Lazada VAT",
        "SPX Express (Thailand) Co., Ltd.": "ค่าขนส่ง SPX",
        "gf.th.ar@grab.com": "ค่าบริการ Grab",
        "K-BIZ Contact": "ค่าธรรมเนียมกสิกร",
        "Delivery Hero (Thailand) Co., Ltd.": "ค่าบริการ Foodpanda",
        "Purple Ventures Company Limited": "ค่าบริการ Robinhood",
        "บริษัท ทรู มันนี่ จำกัด": "ค่าบริการ TrueMoney",
        "บริษัท ไลน์แมน (ประเทศไทย) จำกัด (สำนักงานใหญ่)": "ค่าบริการ LINE MAN",
        "บริษัท กาแฟพันธุ์ไทย จำกัด": "ค่าบริการ กาแฟพันธุ์ไทย",
        # เพิ่มบริษัทอื่นๆ ตามต้องการ
    }
    
    # การ mapping ชื่อบริการ (GROUP3 - special)
    GROUP3_COMPANY_MAPPING = {
        "Shopee (Thailand) Co., Ltd.": "ค่าบริการ Shopee",
        "Lazada Limited (Head Office)": "ค่าบริการ Lazada",
        "SPX Express (Thailand) Co., Ltd.": "ค่าขนส่ง SPX",
        "gf.th.ar@grab.com": "ค่าบริการ Grab",
        "K-BIZ Contact": "ค่าธรรมเนียมกสิกร",
        "Delivery Hero (Thailand) Co., Ltd.": "ค่าบริการ Foodpanda",
        "Purple Ventures Company Limited": "ค่าบริการ Robinhood",
        "บริษัท ทรู มันนี่ จำกัด": "ค่าบริการ TrueMoney",
        "บริษัท ไลน์แมน (ประเทศไทย) จำกัด (สำนักงานใหญ่)": "ค่าบริการ LINE MAN",
        "บริษัท กาแฟพันธุ์ไทย จำกัด": "ค่าบริการ กาแฟพันธุ์ไทย",
        # เพิ่มบริษัทอื่นๆ ตามต้องการ
    }
'''
        
        try:
            with open("config_template.py", "w", encoding="utf-8") as f:
                f.write(config_template)
            print("✅ สร้างไฟล์ config_template.py สำเร็จ")
            print("   กรุณาคัดลอกไปเป็น config.py และแก้ไขข้อมูลให้ถูกต้อง")
        except Exception as e:
            print(f"❌ ไม่สามารถสร้างไฟล์ config template: {e}")
            
    def create_sample_files(self):
        """สร้างไฟล์ตัวอย่าง"""
        print("\n📄 สร้างไฟล์ตัวอย่าง...")
        
        # สร้างไฟล์ Build000.json ตัวอย่าง
        sample_json = {
            "companies": {
                "Shopee (Thailand) Co., Ltd.": {
                    "customer_id": "C00001",
                    "account_code": "520101",
                    "account_code2": "520102"
                },
                "SPX Express (Thailand) Co., Ltd.": {
                    "customer_id": "C00024",
                    "account_code": "520312",
                    "account_code2": "520313"
                }
            }
        }
        
        try:
            os.makedirs("รหัส", exist_ok=True)
            with open("รหัส/Build000.json", "w", encoding="utf-8") as f:
                json.dump(sample_json, f, ensure_ascii=False, indent=2)
            print("✅ สร้างไฟล์ รหัส/Build000.json ตัวอย่าง")
        except Exception as e:
            print(f"❌ ไม่สามารถสร้างไฟล์ JSON ตัวอย่าง: {e}")
            
        # สร้างไฟล์ Build000.txt ตัวอย่าง
        sample_txt = """Username : your_username_here
Password : your_password_here
Link company : https://secure.peakengine.com/your_company_link
Link Express : https://secure.peakengine.com/your_express_link"""
        
        try:
            with open("รหัส/Build000.txt", "w", encoding="utf-8") as f:
                f.write(sample_txt)
            print("✅ สร้างไฟล์ รหัส/Build000.txt ตัวอย่าง")
        except Exception as e:
            print(f"❌ ไม่สามารถสร้างไฟล์ TXT ตัวอย่าง: {e}")
            
        # สร้างไฟล์ folder_settings.json ตัวอย่าง
        sample_folder_settings = {
            "Build000": {
                "group": "regular",
                "description": "โฟลเดอร์ทดสอบระบบ"
            },
            "Build001": {
                "group": "special", 
                "description": "โฟลเดอร์พิเศษ"
            }
        }
        
        try:
            os.makedirs("folder_settings", exist_ok=True)
            with open("folder_settings/folder_settings.json", "w", encoding="utf-8") as f:
                json.dump(sample_folder_settings, f, ensure_ascii=False, indent=2)
            print("✅ สร้างไฟล์ folder_settings/folder_settings.json ตัวอย่าง")
        except Exception as e:
            print(f"❌ ไม่สามารถสร้างไฟล์ folder_settings ตัวอย่าง: {e}")
            
    def create_startup_scripts(self):
        """สร้างสคริปต์เริ่มต้น"""
        print("\n🚀 สร้างสคริปต์เริ่มต้น...")
        
        # Windows Batch Script
        windows_script = """@echo off
title BotV3 - ระบบประมวลผล PDF อัตโนมัติ
echo 🤖 BotV3 - ระบบประมวลผล PDF อัตโนมัติ
echo ========================================
echo กำลังเริ่มระบบ...
python bot_gui_tkinter.py
pause"""
        
        try:
            with open("start_botv3.bat", "w", encoding="utf-8") as f:
                f.write(windows_script)
            print("✅ สร้างไฟล์ start_botv3.bat")
        except Exception as e:
            print(f"❌ ไม่สามารถสร้างไฟล์ .bat: {e}")
            
        # Linux/Mac Shell Script
        linux_script = """#!/bin/bash
echo "🤖 BotV3 - ระบบประมวลผล PDF อัตโนมัติ"
echo "========================================"
echo "กำลังเริ่มระบบ..."
python3 bot_gui_tkinter.py"""
        
        try:
            with open("start_botv3.sh", "w", encoding="utf-8") as f:
                f.write(linux_script)
            # ทำให้ไฟล์ .sh executable
            os.chmod("start_botv3.sh", 0o755)
            print("✅ สร้างไฟล์ start_botv3.sh")
        except Exception as e:
            print(f"❌ ไม่สามารถสร้างไฟล์ .sh: {e}")
            
    def create_readme(self):
        """สร้างไฟล์ README"""
        print("\n📖 สร้างไฟล์ README...")
        
        readme_content = """# 🤖 BotV3 - ระบบประมวลผล PDF อัตโนมัติ

## 📋 ข้อกำหนดระบบ

- Python 3.8 หรือสูงกว่า
- pip (Python Package Manager)
- Playwright Browser (จะติดตั้งอัตโนมัติ)

## 🚀 การติดตั้ง

### วิธีที่ 1: ติดตั้งอัตโนมัติ (แนะนำ)
```bash
python install_botv3.py
```

### วิธีที่ 2: ติดตั้งด้วยตนเอง
```bash
# ติดตั้ง requirements
pip install -r requirements.txt
pip install -r requirements_desktop.txt
pip install -r requirements_flask.txt
pip install -r requirements_playwright.txt

# ติดตั้ง Playwright browsers
playwright install chromium
```

## ⚙️ การตั้งค่า

1. **คัดลอกไฟล์ config**
   ```bash
   copy config_template.py config.py  # Windows
   cp config_template.py config.py    # Linux/Mac
   ```

2. **แก้ไขไฟล์ config.py**
   - กรอก LINE Notify Token หรือ LINE OA Token
   - แก้ไขข้อมูลโฟลเดอร์ตามระบบของคุณ
   - เพิ่มข้อมูลบริษัทใน COMPANY_VAT_STATUS

3. **ตั้งค่าไฟล์ข้อมูล**
   - แก้ไขไฟล์ในโฟลเดอร์ `รหัส/` (Buildxxx.json, Buildxxx.txt)
   - แก้ไขไฟล์ `folder_settings/folder_settings.json`

## 🎯 การใช้งาน

### เริ่มต้นระบบ
```bash
# Windows
start_botv3.bat

# Linux/Mac
./start_botv3.sh

# หรือใช้ Python โดยตรง
python bot_gui_tkinter.py
```

### โหมดการทำงาน
1. **โหมด Desktop GUI** - ใช้งานผ่านหน้าต่าง GUI
2. **โหมด Web Control** - ควบคุมผ่านเว็บเบราว์เซอร์
3. **โหมด API** - ใช้งานผ่าน REST API

## 📁 โครงสร้างไฟล์

```
BotV3/
├── bot_gui_tkinter.py          # หน้าต่าง GUI หลัก
├── main_system.py              # ระบบหลัก
├── web_automation_playwright.py # Web automation
├── config.py                   # ไฟล์การตั้งค่า
├── requirements.txt            # Python packages
├── start_botv3.bat            # สคริปต์เริ่มต้น (Windows)
├── start_botv3.sh             # สคริปต์เริ่มต้น (Linux/Mac)
├── รหัส/                      # ไฟล์ข้อมูลบริษัท
├── folder_settings/           # ไฟล์การตั้งค่าโฟลเดอร์
├── temp_uploads/              # ไฟล์ชั่วคราว
├── เอกสารต้นฉบับ/            # เอกสารต้นฉบับ
├── เอกสารบันทึกแล้ว/          # เอกสารที่ประมวลผลแล้ว
└── คู่มือการใช้งานระบบ_BotV3_*.html  # คู่มือการใช้งาน
```

## 🔧 การแก้ไขปัญหา

### ปัญหาที่พบบ่อย

1. **ไม่สามารถติดตั้ง Playwright ได้**
   ```bash
   # ลองติดตั้งใหม่
   pip install --upgrade playwright
   playwright install chromium
   ```

2. **ไม่พบไฟล์ config.py**
   - คัดลอก config_template.py เป็น config.py
   - แก้ไขข้อมูลให้ถูกต้อง

3. **ไม่สามารถเชื่อมต่อ LINE ได้**
   - ตรวจสอบ LINE Notify Token หรือ LINE OA Token
   - ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต

4. **ไม่พบไฟล์ข้อมูลบริษัท**
   - ตรวจสอบไฟล์ในโฟลเดอร์ `รหัส/`
   - สร้างไฟล์ข้อมูลใหม่ผ่านระบบ

## 📞 การสนับสนุน

หากพบปัญหาหรือต้องการความช่วยเหลือ:
1. ตรวจสอบคู่มือการใช้งานในไฟล์ HTML
2. ตรวจสอบ log ไฟล์ในโฟลเดอร์ `temp_uploads/`
3. ตรวจสอบการตั้งค่าในไฟล์ `config.py`

## 📝 หมายเหตุ

- ระบบจะจำกัดการประมวลผลสูงสุดที่ 60 รายการต่อครั้ง
- ไฟล์ PDF ต้องไม่มีรหัสผ่าน
- ระบบรองรับเฉพาะไฟล์ PDF ที่มีโครงสร้างที่กำหนด

---
© 2025 BotV3 - ระบบประมวลผล PDF อัตโนมัติ
"""
        
        try:
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(readme_content)
            print("✅ สร้างไฟล์ README.md")
        except Exception as e:
            print(f"❌ ไม่สามารถสร้างไฟล์ README: {e}")
            
    def run_installation(self):
        """รันการติดตั้ง"""
        self.print_header()
        
        # ตรวจสอบระบบ
        if not self.check_python_version():
            return False
            
        if not self.check_pip():
            return False
            
        # ติดตั้ง packages
        if not self.install_requirements():
            return False
            
        # ติดตั้ง Playwright browsers
        if not self.install_playwright_browsers():
            return False
            
        # สร้างโฟลเดอร์และไฟล์
        self.create_directories()
        self.create_config_template()
        self.create_sample_files()
        self.create_startup_scripts()
        self.create_readme()
        
        print("\n" + "=" * 60)
        print("🎉 การติดตั้งเสร็จสิ้น!")
        print("=" * 60)
        print("\n📋 ขั้นตอนต่อไป:")
        print("1. คัดลอก config_template.py เป็น config.py")
        print("2. แก้ไขข้อมูลใน config.py ให้ถูกต้อง")
        print("3. แก้ไขไฟล์ข้อมูลในโฟลเดอร์ 'รหัส/'")
        print("4. เริ่มต้นระบบด้วย start_botv3.bat (Windows) หรือ start_botv3.sh (Linux/Mac)")
        print("\n📖 อ่านคู่มือการใช้งานในไฟล์ HTML")
        print("=" * 60)
        
        return True

def main():
    """ฟังก์ชันหลัก"""
    installer = BotV3Installer()
    
    try:
        success = installer.run_installation()
        if success:
            print("\n✅ การติดตั้งสำเร็จ!")
            input("\nกด Enter เพื่อปิดหน้าต่าง...")
        else:
            print("\n❌ การติดตั้งไม่สำเร็จ!")
            input("\nกด Enter เพื่อปิดหน้าต่าง...")
    except KeyboardInterrupt:
        print("\n\n⚠️ การติดตั้งถูกยกเลิกโดยผู้ใช้")
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        input("\nกด Enter เพื่อปิดหน้าต่าง...")

if __name__ == "__main__":
    main()
