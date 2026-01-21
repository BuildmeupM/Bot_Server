#!/usr/bin/env python3
"""
สคริปต์สำหรับ build BotV3 เป็น exe
"""

import os
import sys
import subprocess
from pathlib import Path

def install_pyinstaller():
    """ติดตั้ง PyInstaller"""
    print("📦 กำลังติดตั้ง PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    print("✅ ติดตั้ง PyInstaller เสร็จสิ้น\n")

def build_exe():
    """Build exe file"""
    print("🔨 กำลัง build BotV3.exe...")
    print("=" * 60)
    
    # คำสั่ง PyInstaller
    cmd = [
        "pyinstaller",
        "--name=BotV3",
        "--windowed",  # ไม่แสดง console
        "--onefile",   # รวมเป็นไฟล์เดียว
        "--icon=NONE",
        # เพิ่มไฟล์ที่จำเป็น
        "--add-data=config.py;.",
        # เพิ่ม hidden imports
        "--hidden-import=playwright",
        "--hidden-import=PyPDF2",
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--hidden-import=PIL",
        # ไฟล์หลัก
        "bot_gui_tkinter.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("✅ Build สำเร็จ!")
        print(f"📁 ไฟล์ exe อยู่ที่: {Path('dist/BotV3.exe').absolute()}")
        print("=" * 60)
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build ล้มเหลว: {e}")
        sys.exit(1)

def main():
    """ฟังก์ชันหลัก"""
    print("\n" + "=" * 60)
    print("🤖 BotV3 - Build Executable")
    print("=" * 60 + "\n")
    
    # ตรวจสอบว่ามี PyInstaller หรือไม่
    try:
        import PyInstaller
        print("✅ พบ PyInstaller แล้ว\n")
    except ImportError:
        install_pyinstaller()
    
    # Build
    build_exe()
    
    print("\n📝 หมายเหตุ:")
    print("  - ไฟล์ exe อยู่ในโฟลเดอร์ dist/")
    print("  - ขนาดไฟล์จะประมาณ 50-100 MB")
    print("  - สามารถคัดลอกไฟล์ไปใช้ในเครื่องอื่นได้เลย")
    print("  - ต้องมี V: drive หรือแก้ config.py ก่อน")
    print()

if __name__ == '__main__':
    main()


