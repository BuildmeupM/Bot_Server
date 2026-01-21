#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ทดสอบโครงสร้างโฟลเดอร์ใหม่
"""

import os
from pathlib import Path
from config import Config
from file_manager import FileManager

def test_folder_structure():
    """ทดสอบโครงสร้างโฟลเดอร์"""
    print("=== ทดสอบโครงสร้างโฟลเดอร์ใหม่ ===\n")
    
    # สร้าง FileManager
    file_manager = FileManager()
    
    print(f"📍 Base Path: {file_manager.base_path}")
    print(f"📍 Test System Path: {file_manager.test_system_path}\n")
    
    # ทดสอบการหาโฟลเดอร์หลัก
    print("🔍 กำลังหาโฟลเดอร์หลัก...")
    main_folders = file_manager.get_main_folders()
    
    if main_folders:
        print(f"✅ พบโฟลเดอร์หลัก {len(main_folders)} โฟลเดอร์:")
        for folder in main_folders:
            print(f"  📁 {folder.name}")
            
            # ทดสอบการหาโฟลเดอร์ลูกค้าและระบบอัตโนมัติ
            automation_folders = file_manager.get_customer_automation_folders(folder)
            if automation_folders:
                print(f"    ✅ พบโฟลเดอร์ระบบอัตโนมัติ {len(automation_folders)} โฟลเดอร์:")
                for auto_folder in automation_folders:
                    print(f"      ⚙️ {auto_folder}")
                    
                    # ทดสอบการหาไฟล์ PDF
                    pdf_files = file_manager.get_pdf_files(auto_folder)
                    if pdf_files:
                        print(f"        📄 พบไฟล์ PDF {len(pdf_files)} ไฟล์:")
                        for pdf in pdf_files[:3]:  # แสดงแค่ 3 ไฟล์แรก
                            print(f"          - {pdf.name}")
                        if len(pdf_files) > 3:
                            print(f"          ... และอีก {len(pdf_files) - 3} ไฟล์")
                    else:
                        print(f"        ❌ ไม่พบไฟล์ PDF")
            else:
                print(f"    ❌ ไม่พบโฟลเดอร์ระบบอัตโนมัติ")
    else:
        print("❌ ไม่พบโฟลเดอร์หลัก")
        print("📋 โฟลเดอร์ที่ต้องการ:")
        for folder in Config.MAIN_FOLDERS:
            print(f"  - {folder}")
        print("\n📋 โฟลเดอร์ที่ข้าม:")
        for folder in Config.SKIP_FOLDERS:
            print(f"  - {folder}")
    
    print("\n=== จบการทดสอบ ===")

def create_sample_structure():
    """สร้างโครงสร้างโฟลเดอร์ตัวอย่าง (สำหรับทดสอบ)"""
    print("\n=== สร้างโครงสร้างโฟลเดอร์ตัวอย่าง ===")
    
    # สร้างโฟลเดอร์หลัก
    base_path = Path("test_structure")
    base_path.mkdir(exist_ok=True)
    
    for main_folder in Config.MAIN_FOLDERS:
        main_path = base_path / main_folder
        main_path.mkdir(exist_ok=True)
        
        # สร้างโฟลเดอร์ลูกค้า
        customer_path = main_path / Config.CUSTOMER_FOLDER
        customer_path.mkdir(exist_ok=True)
        
        # สร้างโฟลเดอร์ระบบอัตโนมัติ
        automation_path = customer_path / Config.AUTOMATION_FOLDER
        automation_path.mkdir(exist_ok=True)
        
        # สร้างไฟล์ PDF ตัวอย่าง
        sample_pdf = automation_path / f"sample_{main_folder}.pdf"
        sample_pdf.write_text("Sample PDF content")
        
        print(f"✅ สร้าง: {main_folder}")
    
    print(f"📁 โครงสร้างตัวอย่างถูกสร้างที่: {base_path.absolute()}")

if __name__ == "__main__":
    try:
        test_folder_structure()
        
        # ถามว่าต้องการสร้างโครงสร้างตัวอย่างหรือไม่
        response = input("\nต้องการสร้างโครงสร้างโฟลเดอร์ตัวอย่างหรือไม่? (y/n): ")
        if response.lower() in ['y', 'yes', 'ใช่']:
            create_sample_structure()
            
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        print("💡 ตรวจสอบว่าไฟล์ config.py และ file_manager.py มีอยู่และถูกต้อง")
