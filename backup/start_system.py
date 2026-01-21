#!/usr/bin/env python3
"""
BotV3 System Startup Script
รันระบบ BotV3 ทั้งหมด รวมถึง backend และ frontend
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def check_python_dependencies():
    """ตรวจสอบ dependencies ที่จำเป็น"""
    print("🔍 ตรวจสอบ Python dependencies...")
    
    required_packages = [
        'flask', 'flask_cors', 'selenium', 'webdriver_manager',
        'requests', 'beautifulsoup4', 'pillow', 'playwright'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # Handle special cases for package names
            if package == 'flask_cors':
                import_name = 'flask_cors'
            elif package == 'webdriver_manager':
                import_name = 'webdriver_manager'
            elif package == 'beautifulsoup4':
                import_name = 'bs4'
            elif package == 'pillow':
                import_name = 'PIL'
            else:
                import_name = package
            
            __import__(import_name)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - ไม่พบ")
    
    if missing_packages:
        print(f"\n⚠️  กรุณาติดตั้ง packages ที่ขาดหายไป:")
        print(f"pip install -r requirements_playwright.txt")
        return False
    
    print("✅ Dependencies ทั้งหมดพร้อมใช้งาน")
    return True

def check_config_files():
    """ตรวจสอบไฟล์ config ที่จำเป็น"""
    print("\n🔍 ตรวจสอบไฟล์ config...")
    
    config_files = ['config.py', 'file_manager.py', 'web_automation.py']
    missing_files = []
    
    for file in config_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            missing_files.append(file)
            print(f"❌ {file} - ไม่พบ")
    
    if missing_files:
        print(f"\n⚠️  ไฟล์ config ที่ขาดหายไป: {missing_files}")
        return False
    
    print("✅ ไฟล์ config ทั้งหมดพร้อมใช้งาน")
    return True

def start_backend():
    """เริ่มต้น Python backend"""
    print("\n🚀 เริ่มต้น Python Backend...")
    
    try:
        # รัน Flask backend
        backend_process = subprocess.Popen([
            sys.executable, 'app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # รอให้ backend เริ่มต้น
        time.sleep(3)
        
        # ตรวจสอบว่า backend รันอยู่หรือไม่
        if backend_process.poll() is None:
            print("✅ Backend เริ่มต้นสำเร็จที่ http://localhost:5000")
            return backend_process
        else:
            print("❌ Backend เริ่มต้นล้มเหลว")
            return None
            
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการเริ่มต้น backend: {e}")
        return None

def show_frontend_instructions():
    """แสดงคำแนะนำสำหรับ frontend"""
    print("\n" + "="*60)
    print("🌐 REACT FRONTEND INSTRUCTIONS")
    print("="*60)
    print("1. เปิด Terminal ใหม่")
    print("2. ไปยังโฟลเดอร์ src:")
    print("   cd src")
    print("3. รัน React development server:")
    print("   npm start")
    print("4. เปิดเบราว์เซอร์ไปที่: http://localhost:3000")
    print("="*60)

def show_api_endpoints():
    """แสดง API endpoints ที่ใช้งานได้"""
    print("\n📡 API ENDPOINTS ที่ใช้งานได้:")
    print("- GET  /api/files              - รายการไฟล์")
    print("- POST /api/upload-to-web      - อัปโหลดไฟล์ไปยังเว็บไซต์")
    print("- GET  /api/upload-history     - ประวัติการอัปโหลด")
    print("- GET  /api/bot/status         - สถานะบอท")
    print("- POST /api/bot/start          - เริ่มบอท")
    print("- POST /api/bot/stop           - หยุดบอท")

def main():
    """ฟังก์ชันหลัก"""
    print("🤖 BotV3 System Startup")
    print("="*40)
    
    # ตรวจสอบ dependencies
    if not check_python_dependencies():
        print("\n❌ ไม่สามารถเริ่มต้นระบบได้ - กรุณาติดตั้ง dependencies ก่อน")
        return
    
    # ตรวจสอบไฟล์ config
    if not check_config_files():
        print("\n❌ ไม่สามารถเริ่มต้นระบบได้ - ไฟล์ config ไม่ครบ")
        return
    
    # เริ่มต้น backend
    backend_process = start_backend()
    if not backend_process:
        print("\n❌ ไม่สามารถเริ่มต้นระบบได้")
        return
    
    # แสดงข้อมูล API
    show_api_endpoints()
    
    # แสดงคำแนะนำสำหรับ frontend
    show_frontend_instructions()
    
    print(f"\n✅ ระบบ BotV3 พร้อมใช้งาน!")
    print("📝 Backend: http://localhost:5000")
    print("📝 Frontend: http://localhost:3000")
    print("\n💡 กด Ctrl+C เพื่อหยุดระบบ")
    
    try:
        # รอให้ผู้ใช้หยุดระบบ
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 หยุดระบบ...")
        if backend_process:
            backend_process.terminate()
            print("✅ Backend หยุดแล้ว")
        print("👋 สวัสดี!")

if __name__ == "__main__":
    main()
