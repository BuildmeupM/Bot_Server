#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ตัวอย่างการใช้งานระบบบอทอัตโนมัติ
"""

from main_bot import MainBot
from pathlib import Path
import time

def example_basic_usage():
    """ตัวอย่างการใช้งานพื้นฐาน"""
    print("=== ตัวอย่างการใช้งานระบบบอท ===")
    
    # สร้างบอท
    bot = MainBot()
    
    # ตรวจสอบสถานะ
    status = bot.get_status()
    print(f"สถานะบอท: {status}")
    
    # เริ่มการทำงาน
    print("\nเริ่มการทำงานของบอท...")
    success = bot.start_bot()
    
    if success:
        print("บอททำงานเสร็จสิ้น")
    else:
        print("บอททำงานผิดพลาด")

def example_custom_path():
    """ตัวอย่างการใช้งานกับ path ที่กำหนดเอง"""
    print("=== ตัวอย่างการใช้งานกับ Path ที่กำหนดเอง ===")
    
    # กำหนด path เอง
    custom_path = "C:/MyDocuments/Synology"
    
    # สร้างบอทพร้อม path ที่กำหนด
    bot = MainBot(custom_path)
    
    # เริ่มการทำงาน
    success = bot.start_bot()
    
    if success:
        print("บอททำงานเสร็จสิ้น")
    else:
        print("บอททำงานผิดพลาด")

def example_step_by_step():
    """ตัวอย่างการใช้งานแบบทีละขั้นตอน"""
    print("=== ตัวอย่างการใช้งานแบบทีละขั้นตอน ===")
    
    # สร้างบอท
    bot = MainBot()
    
    try:
        # ขั้นตอนที่ 1: ตรวจสอบโฟลเดอร์หลัก
        print("1. ตรวจสอบโฟลเดอร์หลัก...")
        main_folders = bot.file_manager.get_main_folders()
        print(f"   พบโฟลเดอร์: {[f.name for f in main_folders]}")
        
        # ขั้นตอนที่ 2: อ่านการตั้งค่า
        print("2. อ่านการตั้งค่าระบบ...")
        folder_settings = bot.file_manager.read_folder_settings()
        print(f"   การตั้งค่าที่อ่านได้: {len(folder_settings)} รายการ")
        
        # ขั้นตอนที่ 3: ตรวจสอบสถานะ
        print("3. ตรวจสอบสถานะระบบ...")
        status = bot.get_status()
        print(f"   สถานะ: {status}")
        
        print("\nการตรวจสอบเสร็จสิ้น")
        
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")

def example_error_handling():
    """ตัวอย่างการจัดการข้อผิดพลาด"""
    print("=== ตัวอย่างการจัดการข้อผิดพลาด ===")
    
    try:
        # สร้างบอทพร้อม path ที่ไม่มีอยู่จริง
        invalid_path = "C:/NonExistentPath"
        bot = MainBot(invalid_path)
        
        # พยายามเริ่มการทำงาน
        success = bot.start_bot()
        
    except Exception as e:
        print(f"จับข้อผิดพลาดได้: {e}")
        print("ระบบจัดการข้อผิดพลาดได้อย่างถูกต้อง")

def example_logging():
    """ตัวอย่างการใช้งานระบบ logging"""
    print("=== ตัวอย่างการใช้งานระบบ Logging ===")
    
    # สร้างบอท
    bot = MainBot()
    
    # บันทึก log ต่างๆ
    bot.logger.log_system_status("INFO", "เริ่มการทดสอบระบบ")
    bot.logger.log_pdf_processing("test.pdf", "Test Company", "SUCCESS", "ทดสอบการประมวลผล")
    bot.logger.log_web_automation("Login", "SUCCESS", "ทดสอบการล็อกอิน")
    
    # สร้างรายงาน
    print("สร้างรายงาน...")
    bot.logger.create_excel_report()
    bot.logger.create_text_report()
    
    # แสดงสถิติ
    stats = bot.logger.get_summary_stats()
    print(f"สถิติ: {stats}")

def example_data_processing():
    """ตัวอย่างการประมวลผลข้อมูล"""
    print("=== ตัวอย่างการประมวลผลข้อมูล ===")
    
    # สร้างบอท
    bot = MainBot()
    
    # ข้อมูลตัวอย่าง
    sample_pdf_data = {
        'filename': 'sample.pdf',
        'company_name': 'Shopee (Thailand) Co., Ltd.',
        'invoice_number': 'INV001',
        'amount_before_vat': 1000.0,
        'total_amount': 1070.0,
        'folder_code': '001'
    }
    
    # การตั้งค่าตัวอย่าง
    sample_folder_settings = {
        '001': {
            'message': 'บริษัทจดภาษีมูลค่าเพิ่ม',
            'group': 'regular'
        }
    }
    
    # ประมวลผลข้อมูล
    processed_data = bot.data_processor.process_company_data(
        sample_pdf_data, 
        sample_folder_settings
    )
    
    print(f"ข้อมูลที่ประมวลผลแล้ว: {processed_data}")
    
    # สร้างชื่อไฟล์ใหม่
    new_filename = bot.data_processor.generate_output_filename(
        processed_data, 
        processed_data['group']
    )
    print(f"ชื่อไฟล์ใหม่: {new_filename}")

def main():
    """ฟังก์ชันหลักสำหรับรันตัวอย่าง"""
    print("ระบบบอทอัตโนมัติ - ตัวอย่างการใช้งาน")
    print("=" * 50)
    
    while True:
        print("\nเลือกตัวอย่างที่ต้องการทดสอบ:")
        print("1. การใช้งานพื้นฐาน")
        print("2. การใช้งานกับ Path ที่กำหนดเอง")
        print("3. การใช้งานแบบทีละขั้นตอน")
        print("4. การจัดการข้อผิดพลาด")
        print("5. การใช้งานระบบ Logging")
        print("6. การประมวลผลข้อมูล")
        print("0. ออกจากโปรแกรม")
        
        choice = input("\nกรุณาเลือก (0-6): ").strip()
        
        if choice == '0':
            print("ขอบคุณที่ใช้งานระบบบอท")
            break
        elif choice == '1':
            example_basic_usage()
        elif choice == '2':
            example_custom_path()
        elif choice == '3':
            example_step_by_step()
        elif choice == '4':
            example_error_handling()
        elif choice == '5':
            example_logging()
        elif choice == '6':
            example_data_processing()
        else:
            print("กรุณาเลือกตัวเลข 0-6")
        
        input("\nกด Enter เพื่อดำเนินการต่อ...")

if __name__ == "__main__":
    main()
