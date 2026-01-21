#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Automation Wrapper for EXE
Wrapper สำหรับ web automation ที่จัดการ Playwright อย่างถูกต้องใน EXE
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_playwright_environment():
    """ตั้งค่า environment สำหรับ Playwright ใน EXE"""
    try:
        print("🌐 กำลังตั้งค่า Playwright environment...")
        
        # ตรวจสอบว่ากำลังรันใน EXE หรือไม่
        if getattr(sys, 'frozen', False):
            print("📦 กำลังรันใน EXE mode")
            exe_dir = Path(sys._MEIPASS)
            
            # ใช้ temp directory สำหรับ Playwright
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "playwright_botv3"
            temp_dir.mkdir(exist_ok=True)
            
            # ตั้งค่า environment variables
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(temp_dir / "browsers")
            os.environ['PLAYWRIGHT_DRIVER_PATH'] = str(temp_dir / "driver")
            
            print(f"   - Temp directory: {temp_dir}")
            print(f"   - Browsers path: {os.environ['PLAYWRIGHT_BROWSERS_PATH']}")
            
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
            return True
            
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการตั้งค่า Playwright: {e}")
        return False

def main():
    """ฟังก์ชันหลักสำหรับ web automation"""
    print("🚀 เริ่มต้น Web Automation...")
    
    # ตั้งค่า Playwright environment
    if not setup_playwright_environment():
        print("❌ ไม่สามารถตั้งค่า Playwright ได้")
        input("กด Enter เพื่อปิด...")
        return
    
    try:
        # Import และรัน web automation
        from web_automation_playwright import WebAutomationPlaywright
        
        print("✅ โหลด WebAutomationPlaywright สำเร็จ")
        
        # สร้าง instance และทดสอบ
        automation = WebAutomationPlaywright()
        print("✅ สร้าง WebAutomationPlaywright instance สำเร็จ")
        
        # ทดสอบการเชื่อมต่อ Playwright
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            print("✅ Playwright พร้อมใช้งาน")
            
        print("\n🎉 Web Automation พร้อมใช้งาน!")
        print("📋 คำสั่งที่ใช้ได้:")
        print("   - automation.read_config_from_txt('path/to/file.txt')")
        print("   - automation.login()")
        print("   - automation.process_pdf_file('path/to/file.pdf')")
        
    except ImportError as e:
        print(f"❌ ไม่สามารถ import modules: {e}")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
    
    input("\nกด Enter เพื่อปิด...")

if __name__ == "__main__":
    main()
