#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BotV3 GUI Wrapper for EXE
Wrapper สำหรับ GUI ที่แสดง console window และจัดการ Playwright
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# ตั้งค่า encoding สำหรับ Windows console
if sys.platform == "win32":
    import codecs
    # ตั้งค่า console encoding เป็น UTF-8
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def setup_playwright_environment():
    """ตั้งค่า environment สำหรับ Playwright ใน EXE"""
    try:
        print("[INFO] กำลังตั้งค่า Playwright environment...")
        print("=" * 50)
        
        # ตรวจสอบว่ากำลังรันใน EXE หรือไม่
        if getattr(sys, 'frozen', False):
            print("[INFO] กำลังรันใน EXE mode")
            exe_dir = Path(sys._MEIPASS)
            
            # ใช้ temp directory สำหรับ Playwright
            temp_dir = Path(tempfile.gettempdir()) / "playwright_botv3"
            temp_dir.mkdir(exist_ok=True)
            
            # ตั้งค่า environment variables
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(temp_dir / "browsers")
            os.environ['PLAYWRIGHT_DRIVER_PATH'] = str(temp_dir / "driver")
            
            print(f"   EXE directory: {exe_dir}")
            print(f"   Temp directory: {temp_dir}")
            print(f"   Browsers path: {os.environ['PLAYWRIGHT_BROWSERS_PATH']}")
            print(f"   Driver path: {os.environ['PLAYWRIGHT_DRIVER_PATH']}")
            
            # ตรวจสอบว่า Chromium มีอยู่แล้วหรือไม่
            chromium_path = temp_dir / "browsers" / "chromium-1091" / "chrome-win" / "chrome.exe"
            if chromium_path.exists():
                print("[SUCCESS] พบ Chromium ที่ติดตั้งแล้ว")
                return True
            
            # ติดตั้ง Playwright browsers
            print("[INFO] กำลังติดตั้ง Playwright browsers...")
            print("   กรุณารอสักครู่...")
            
            try:
                result = subprocess.run([
                    sys.executable, "-m", "playwright", "install", "chromium"
                ], capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    print("[SUCCESS] ติดตั้ง Playwright browsers สำเร็จ")
                    print("   ไฟล์ถูกเก็บไว้ที่:", os.environ['PLAYWRIGHT_BROWSERS_PATH'])
                    return True
                else:
                    print("[ERROR] ติดตั้ง Playwright browsers ไม่สำเร็จ")
                    print("   Error:", result.stderr)
                    return False
                    
            except subprocess.TimeoutExpired:
                print("[ERROR] การติดตั้ง Playwright ใช้เวลานานเกินไป")
                return False
            except Exception as e:
                print(f"[ERROR] เกิดข้อผิดพลาดในการติดตั้ง Playwright: {e}")
                return False
        else:
            print("[INFO] กำลังรันใน Python mode")
            return True
            
    except Exception as e:
        print(f"[ERROR] เกิดข้อผิดพลาดในการตั้งค่า Playwright: {e}")
        return False

def test_playwright():
    """ทดสอบ Playwright"""
    try:
        print("\n[TEST] กำลังทดสอบ Playwright...")
        print("-" * 30)
        
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            print("[SUCCESS] Playwright instance สร้างสำเร็จ")
            
            # ตรวจสอบ browser
            browser = p.chromium.launch(headless=True)
            print("[SUCCESS] Chromium browser เปิดสำเร็จ")
            
            page = browser.new_page()
            print("[SUCCESS] หน้าใหม่สร้างสำเร็จ")
            
            page.goto("https://www.google.com")
            title = page.title()
            print(f"[SUCCESS] เปิดเว็บไซต์สำเร็จ - หน้า: {title}")
            
            browser.close()
            print("[SUCCESS] Browser ปิดสำเร็จ")
            
            print("\n[SUCCESS] Playwright ทำงานได้ปกติ!")
            return True
            
    except Exception as e:
        print(f"[ERROR] Playwright ไม่ทำงาน: {e}")
        print("   กรุณาตรวจสอบการติดตั้ง Chromium")
        return False

def main():
    """ฟังก์ชันหลักสำหรับ GUI"""
    print("[START] เริ่มต้น BotV3 GUI...")
    print("=" * 60)
    
    # ตั้งค่า Playwright environment
    if not setup_playwright_environment():
        print("\n[ERROR] ไม่สามารถตั้งค่า Playwright ได้")
        print("   กรุณาติดตั้ง Playwright browsers ด้วยตนเอง:")
        print("   python -m playwright install chromium")
        input("\nกด Enter เพื่อปิด...")
        return
    
    # ทดสอบ Playwright
    if not test_playwright():
        print("\n[ERROR] Playwright ไม่ทำงาน")
        input("\nกด Enter เพื่อปิด...")
        return
    
    print("\n" + "=" * 60)
    print("[INFO] กำลังเริ่มต้น GUI...")
    print("=" * 60)
    
    try:
        # Import และรัน GUI
        from bot_gui_tkinter import main as gui_main
        
        print("[SUCCESS] โหลด GUI สำเร็จ")
        print("[INFO] เปิดหน้าต่าง GUI...")
        
        # รัน GUI
        gui_main()
        
    except ImportError as e:
        print(f"[ERROR] ไม่สามารถ import GUI modules: {e}")
        input("\nกด Enter เพื่อปิด...")
    except Exception as e:
        print(f"[ERROR] เกิดข้อผิดพลาดใน GUI: {e}")
        input("\nกด Enter เพื่อปิด...")

if __name__ == "__main__":
    main()
