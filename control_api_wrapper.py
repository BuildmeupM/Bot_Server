#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Control API Wrapper for EXE
Wrapper สำหรับ Control API ที่แสดง console window และจัดการ Playwright
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
    """ฟังก์ชันหลักสำหรับ Control API"""
    print("🚀 เริ่มต้น BotV3 Control API...")
    print("=" * 50)
    
    # ตั้งค่า Playwright environment
    if not setup_playwright_environment():
        print("❌ ไม่สามารถตั้งค่า Playwright ได้")
        input("กด Enter เพื่อปิด...")
        return
    
    try:
        # Import และรัน Control API
        from control_api import app, system_state
        
        print("✅ โหลด Control API สำเร็จ")
        print("🌐 เริ่มต้น Flask server...")
        print("📡 API จะรันที่: http://localhost:5000")
        print("🛑 กด Ctrl+C เพื่อหยุดการทำงาน")
        print("=" * 50)
        
        # รัน Flask app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False
        )
        
    except ImportError as e:
        print(f"❌ ไม่สามารถ import modules: {e}")
        input("กด Enter เพื่อปิด...")
    except KeyboardInterrupt:
        print("\n🛑 หยุดการทำงานโดยผู้ใช้")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        input("กด Enter เพื่อปิด...")

if __name__ == "__main__":
    main()
