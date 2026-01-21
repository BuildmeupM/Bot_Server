#!/usr/bin/env python3
"""
สคริปต์ติดตั้ง Dependencies สำหรับการทดสอบระบบ BotV3
"""

import subprocess
import sys
import os

def install_package(package):
    """ติดตั้ง package ที่ระบุ"""
    try:
        print(f"กำลังติดตั้ง {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ ติดตั้ง {package} สำเร็จ")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ไม่สามารถติดตั้ง {package} ได้: {e}")
        return False

def main():
    print("เริ่มต้นการติดตั้ง Dependencies สำหรับการทดสอบระบบ BotV3")
    print("=" * 60)
    
    # รายการ packages ที่จำเป็น
    required_packages = [
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.0",
        "requests",
        "openpyxl",
        "pandas",
        "numpy"
    ]
    
    # ติดตั้ง packages
    success_count = 0
    total_count = len(required_packages)
    
    for package in required_packages:
        if install_package(package):
            success_count += 1
        print()
    
    # สรุปผลการติดตั้ง
    print("=" * 60)
    print(f"สรุปผลการติดตั้ง: {success_count}/{total_count} packages")
    
    if success_count == total_count:
        print("🎉 ติดตั้ง Dependencies สำเร็จทั้งหมด!")
        print("คุณสามารถรันการทดสอบระบบได้แล้ว")
    else:
        print("⚠️ มีบาง packages ที่ติดตั้งไม่สำเร็จ")
        print("กรุณาตรวจสอบ error messages และลองติดตั้งใหม่")
    
    print("\nคำแนะนำเพิ่มเติม:")
    print("- ตรวจสอบว่าได้ติดตั้ง Chrome หรือ Firefox แล้ว")
    print("- หากมีปัญหา WebDriver ให้ลองใช้ selenium-manager (built-in)")
    print("- หรือดาวน์โหลด ChromeDriver จาก https://chromedriver.chromium.org/")

if __name__ == "__main__":
    main()
