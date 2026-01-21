#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ทดสอบการตั้งชื่อไฟล์ใหม่ที่เชื่อมกับกรุ๊ป
"""

from file_manager import FileManager
from config import Config

def test_file_naming():
    """ทดสอบการตั้งชื่อไฟล์ใหม่"""
    print("=== ทดสอบการตั้งชื่อไฟล์ใหม่ที่เชื่อมกับกรุ๊ป ===\n")
    
    # สร้าง FileManager
    file_manager = FileManager()
    
    # อ่าน folder_settings
    folder_settings = file_manager.read_folder_settings()
    print(f"📋 Folder Settings: {folder_settings}\n")
    
    # ข้อมูลทดสอบ
    test_cases = [
        {
            "name": "Shopee - Regular Group",
            "pdf_data": {
                "company_name": "Shopee (Thailand) Co., Ltd.",
                "document_date": "11/11/2024",
                "folder_code": "Build000"
            },
            "iptnumber_text": "EXP-20241100069"
        },
        {
            "name": "Lazada - Regular Group", 
            "pdf_data": {
                "company_name": "Lazada Limited (Head Office)",
                "document_date": "12/12/2024",
                "folder_code": "001"
            },
            "iptnumber_text": "EXP-20241200070"
        },
        {
            "name": "Shopee - Special Group",
            "pdf_data": {
                "company_name": "Shopee (Thailand) Co., Ltd.",
                "document_date": "13/13/2024",
                "folder_code": "002"
            },
            "iptnumber_text": "EXP-20241300071"
        },
        {
            "name": "Unknown Company - Regular Group",
            "pdf_data": {
                "company_name": "บริษัททดสอบ จำกัด",
                "document_date": "14/14/2024",
                "folder_code": "Build000"
            },
            "iptnumber_text": "EXP-20241400072"
        }
    ]
    
    # ทดสอบแต่ละกรณี
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- ทดสอบที่ {i}: {test_case['name']} ---")
        
        # เรียกใช้ฟังก์ชัน _get_service_name โดยตรง
        service_name = file_manager._get_service_name(
            test_case['pdf_data']['company_name'],
            folder_settings,
            test_case['pdf_data']
        )
        
        # สร้างชื่อไฟล์ตามรูปแบบใหม่
        document_date = test_case['pdf_data']['document_date']
        formatted_date = document_date.replace('/', '.')
        document_number = test_case['iptnumber_text']
        safe_document_number = file_manager.sanitize_filename(document_number)
        
        new_filename = f"{formatted_date} {safe_document_number} {service_name}.pdf"
        
        print(f"🏢 บริษัท: {test_case['pdf_data']['company_name']}")
        print(f"📅 วันที่: {formatted_date}")
        print(f"📄 เลขที่เอกสาร: {safe_document_number}")
        print(f"🏷️ ชื่อบริการ: {service_name}")
        print(f"📝 ชื่อไฟล์ใหม่: {new_filename}")
        print()

if __name__ == "__main__":
    test_file_naming()
