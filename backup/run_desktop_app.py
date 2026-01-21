#!/usr/bin/env python3
"""
สคริปต์สำหรับรัน Desktop Application
"""

import sys
import os
from pathlib import Path

def check_dependencies():
    """ตรวจสอบ dependencies"""
    required_modules = [
        'tkinter',
        'playwright', 
        'PyPDF2',
        'pandas',
        'openpyxl',
        'PIL'
    ]
    
    missing = []
    for module in required_modules:
        try:
            if module == 'tkinter':
                import tkinter
            elif module == 'playwright':
                from playwright.sync_api import sync_playwright
            elif module == 'PyPDF2':
                import PyPDF2
            elif module == 'pandas':
                import pandas
            elif module == 'openpyxl':
                import openpyxl
            elif module == 'PIL':
                from PIL import Image
        except ImportError:
            missing.append(module)
    
    if missing:
        print("❌ ไม่พบ modules ต่อไปนี้:")
        for module in missing:
            print(f"   - {module}")
        print("\n📦 กรุณาติดตั้งด้วยคำสั่ง:")
        print("   pip install -r requirements_desktop.txt")
        print("   playwright install chromium")
        return False
    
    print("✅ พบ dependencies ครบถ้วน")
    return True

def main():
    """ฟังก์ชันหลัก"""
    print("=" * 60)
    print("🤖 BotV3 Desktop Application")
    print("=" * 60)
    
    # ตรวจสอบ dependencies
    if not check_dependencies():
        input("\nกด Enter เพื่อปิด...")
        return
    
    # ตรวจสอบ config.py
    if not Path("config.py").exists():
        print("❌ ไม่พบไฟล์ config.py")
        input("\nกด Enter เพื่อปิด...")
        return
    
    # ตรวจสอบ V: drive
    try:
        from config import Config
        base_path = Path(f"{Config.BASE_FOLDER}:/")
        if not base_path.exists():
            print(f"⚠️ ไม่พบ {Config.BASE_FOLDER}: drive")
            print("   ระบบจะยังทำงานได้ แต่จะไม่พบโฟลเดอร์")
    except Exception as e:
        print(f"⚠️ เกิดข้อผิดพลาดในการตรวจสอบ config: {e}")
    
    print("\n🚀 กำลังเปิด Desktop Application...")
    print("=" * 60)
    
    try:
        # Import และรัน GUI
        from bot_gui_tkinter import main as run_gui
        run_gui()
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        input("\nกด Enter เพื่อปิด...")

if __name__ == '__main__':
    main()

