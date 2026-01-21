#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright Setup for EXE
ติดตั้งและตั้งค่า Playwright สำหรับ EXE
"""

import os
import sys
import subprocess
from pathlib import Path
import tempfile
import shutil

def setup_playwright_for_exe():
    """ตั้งค่า Playwright สำหรับ EXE"""
    try:
        print("🌐 กำลังตั้งค่า Playwright...")
        
        # ตรวจสอบว่ากำลังรันใน EXE หรือไม่
        if getattr(sys, 'frozen', False):
            print("📦 กำลังรันใน EXE mode")
            exe_dir = Path(sys._MEIPASS)
            print(f"   EXE directory: {exe_dir}")
            
            # สร้างโฟลเดอร์สำหรับ Playwright
            temp_dir = Path(tempfile.gettempdir()) / "playwright_botv3"
            temp_dir.mkdir(exist_ok=True)
            
            # ตั้งค่า environment variables
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(temp_dir / "browsers")
            os.environ['PLAYWRIGHT_DRIVER_PATH'] = str(temp_dir / "driver")
            
            print(f"   Temp directory: {temp_dir}")
            print(f"   Browsers path: {os.environ['PLAYWRIGHT_BROWSERS_PATH']}")
            
            # ติดตั้ง Playwright browsers
            try:
                print("📥 กำลังติดตั้ง Playwright browsers...")
                result = subprocess.run([
                    sys.executable, "-m", "playwright", "install", "chromium"
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print("✅ ติดตั้ง Playwright browsers สำเร็จ")
                    return True
                else:
                    print(f"❌ ติดตั้ง Playwright browsers ไม่สำเร็จ: {result.stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                print("⏰ การติดตั้ง Playwright ใช้เวลานานเกินไป")
                return False
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาดในการติดตั้ง Playwright: {e}")
                return False
        else:
            print("🐍 กำลังรันใน Python mode")
            # รันในโหมด Python ปกติ
            try:
                result = subprocess.run([
                    sys.executable, "-m", "playwright", "install", "chromium"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Playwright พร้อมใช้งาน")
                    return True
                else:
                    print(f"❌ Playwright ไม่พร้อมใช้งาน: {result.stderr}")
                    return False
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาด: {e}")
                return False
                
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการตั้งค่า Playwright: {e}")
        return False

def test_playwright():
    """ทดสอบ Playwright"""
    try:
        print("🧪 กำลังทดสอบ Playwright...")
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.google.com")
            title = page.title()
            browser.close()
            
            print(f"✅ Playwright ทำงานได้ปกติ - หน้าเว็บ: {title}")
            return True
            
    except Exception as e:
        print(f"❌ Playwright ไม่ทำงาน: {e}")
        return False

if __name__ == "__main__":
    print("🚀 เริ่มต้นการตั้งค่า Playwright...")
    
    if setup_playwright_for_exe():
        if test_playwright():
            print("🎉 Playwright พร้อมใช้งาน!")
        else:
            print("❌ Playwright ไม่ทำงาน")
    else:
        print("❌ ไม่สามารถตั้งค่า Playwright ได้")
    
    input("กด Enter เพื่อปิด...")

