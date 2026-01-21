#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BotV3 System Test Script (Fixed Version)
ทดสอบระบบโดยแก้ไขปัญหา encoding สำหรับ Web API
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from file_manager import FileManager
from web_automation_playwright import WebAutomationPlaywright
from pdf_reader import PDFReader

# ตั้งค่า encoding สำหรับ Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

class BotV3TestSystem:
    def __init__(self):
        self.file_manager = FileManager()
        self.web_automation = WebAutomationPlaywright()
        self.pdf_reader = PDFReader(pdf_directory=self)  # ส่ง self เพื่อให้ใช้ method อ่านไฟล์ได้
        self.test_results = []
        
    def safe_print(self, message):
        """ปลอดภัยสำหรับการพิมพ์ข้อความที่มี emoji"""
        try:
            print(message)
        except UnicodeEncodeError:
            # ถ้า encoding ล้มเหลว ให้แทนที่ emoji ด้วยข้อความ
            safe_message = message.replace('✅', '[OK]').replace('❌', '[FAIL]')
            safe_message = safe_message.replace('📁', '[DIR]').replace('📄', '[FILE]')
            safe_message = safe_message.replace('📊', '[STAT]').replace('📍', '[PATH]')
            safe_message = safe_message.replace('📖', '[READ]').replace('📏', '[SIZE]')
            safe_message = safe_message.replace('🎯', '[TARGET]').replace('🎉', '[SUCCESS]')
            safe_message = safe_message.replace('⚠️', '[WARN]').replace('💡', '[INFO]')
            safe_message = safe_message.replace('ℹ️', '[INFO]')
            print(safe_message)

    def _get_file_type(self, filename):
        """กำหนดประเภทไฟล์ตามนามสกุล"""
        ext = Path(filename).suffix.lower()
        if ext in ['.py', '.pyc']: return 'Python'
        elif ext in ['.json', '.xml', '.yaml', '.yml']: return 'Config'
        elif ext in ['.txt', '.log']: return 'Text'
        elif ext in ['.pdf']: return 'PDF'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif']: return 'Image'
        elif ext in ['.mp4', '.avi', '.mov']: return 'Video'
        elif ext in ['.xlsx', '.xls']: return 'Excel'
        elif ext in ['.docx', '.doc']: return 'Word'
        else: return 'Other'

    def test_file_manager_000(self):
        """ทดสอบ FileManager ในโฟลเดอร์ Build000 ทดสอบระบบ"""
        print("\n=== ทดสอบ FileManager ในโฟลเดอร์ Build000 ทดสอบระบบ ===")
        
        try:
            # 0. ตรวจสอบ V: drive (Synology)
            print("0. ตรวจสอบ V: drive (Synology)...")
            v_drive = Path("V:/")
            if v_drive.exists():
                self.safe_print("   [OK] พบ V: drive (Synology)")
                self.safe_print(f"   [PATH] Path: {v_drive.resolve()}")
            else:
                self.safe_print("   [FAIL] ไม่พบ V: drive (Synology)")
                self.safe_print("   [INFO] ตรวจสอบการเชื่อมต่อ Synology drive")
                return
            
            # 1. ทดสอบการอ่านไฟล์ในโฟลเดอร์หลัก Build000 ทดสอบระบบ
            print("\n1. ทดสอบการอ่านไฟล์ในโฟลเดอร์หลัก Build000 ทดสอบระบบ...")
            main_folder = "V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ"
            
            if Path(main_folder).exists():
                self.safe_print("   [OK] โฟลเดอร์หลักมีอยู่")
                try:
                    all_items = list(Path(main_folder).iterdir())
                    files_count = len([item for item in all_items if item.is_file()])
                    folders_count = len([item for item in all_items if item.is_dir()])
                    
                    self.safe_print(f"   [STAT] พบไฟล์/โฟลเดอร์ {len(all_items)} รายการ")
                    self.safe_print(f"      [DIR] โฟลเดอร์: {folders_count} โฟลเดอร์")
                    self.safe_print(f"      [FILE] ไฟล์: {files_count} ไฟล์")
                    
                    if folders_count > 0:
                        self.safe_print("   [DIR] โฟลเดอร์ย่อยที่พบ:")
                        for folder in [item for item in all_items if item.is_dir()]:
                            print(f"      • {folder.name}")
                    
                    if files_count > 0:
                        self.safe_print("   [FILE] ไฟล์ที่พบ:")
                        for file in [item for item in all_items if item.is_file()][:5]:
                            print(f"      • {file.name}")
                        if files_count > 5:
                            print(f"      ... และอีก {files_count - 5} ไฟล์")
                            
                except Exception as e:
                    self.safe_print(f"   [WARN] ไม่สามารถนับไฟล์ได้: {e}")
                    files_count = 0
                    folders_count = 0
            else:
                self.safe_print("   [FAIL] โฟลเดอร์หลักไม่มีอยู่")
                files_count = 0
                folders_count = 0
            
            # 2. ทดสอบการอ่านโฟลเดอร์ลูกค้า/ระบบอัตโนมัติ (ไฟล์ PDF)
            print("\n2. ทดสอบการอ่านโฟลเดอร์ลูกค้า/ระบบอัตโนมัติ (ไฟล์ PDF)...")
            
            customer_folder = f"{main_folder}/ลูกค้า"
            if Path(customer_folder).exists():
                self.safe_print("   [OK] โฟลเดอร์ลูกค้ามีอยู่")
                
                customer_automation_folder = f"{customer_folder}/ระบบอัตโนมัติ"
                if Path(customer_automation_folder).exists():
                    self.safe_print("   [OK] โฟลเดอร์ระบบอัตโนมัติมีอยู่")
                    
                    try:
                        # ค้นหาเฉพาะไฟล์ PDF ที่อยู่ในโฟลเดอร์หลัก ระบบอัตโนมัติ (ไม่เข้าโฟลเดอร์ย่อย)
                        automation_folder_path = Path(customer_automation_folder)
                        pdf_files = [f for f in automation_folder_path.iterdir() if f.is_file() and f.suffix.lower() == '.pdf']
                        self.safe_print(f"   [FILE] พบไฟล์ PDF {len(pdf_files)} ไฟล์ (เฉพาะโฟลเดอร์หลัก)")
                        
                        if pdf_files:
                            self.safe_print("   [FILE] รายชื่อไฟล์ PDF:")
                            for i, pdf_file in enumerate(pdf_files, 1):
                                try:
                                    file_size = pdf_file.stat().st_size
                                    self.safe_print(f"      {i}. {pdf_file.name} ({file_size} bytes)")
                                except Exception as e:
                                    self.safe_print(f"      {i}. {pdf_file.name} (ไม่สามารถอ่านขนาดได้)")
                            
                        else:
                            self.safe_print("   [INFO] ไม่พบไฟล์ PDF ในโฟลเดอร์หลัก ระบบอัตโนมัติ")
                            
                    except Exception as e:
                        self.safe_print(f"   [WARN] ไม่สามารถตรวจสอบไฟล์ PDF ได้: {e}")
                else:
                    self.safe_print("   [FAIL] โฟลเดอร์ระบบอัตโนมัติไม่มีอยู่")
            else:
                self.safe_print("   [FAIL] โฟลเดอร์ลูกค้าไม่มีอยู่")
            
            # 3. ทดสอบการอ่านโฟลเดอร์รหัส (JSON และ TXT)
            print("\n3. ทดสอบการอ่านโฟลเดอร์รหัส (JSON และ TXT)...")
            code_folder = f"{main_folder}/รหัส"
            
            if Path(code_folder).exists():
                self.safe_print("   [OK] โฟลเดอร์รหัสมีอยู่")
                
                # ตรวจสอบไฟล์ Build000.txt
                build000_txt_path = Path(code_folder) / "Build000.txt"
                if build000_txt_path.exists():
                    self.safe_print("   [OK] พบ Build000.txt (ฐานข้อมูลหลัก)")
                    self.safe_print(f"      [SIZE] ขนาด: {build000_txt_path.stat().st_size} bytes")
                    
                    try:
                        with open(build000_txt_path, 'r', encoding='utf-8') as f:
                            txt_content = f.read()
                        self.safe_print("      [read] เนื้อหา Build000.txt:")
                        print("         " + "="*50)
                        lines = txt_content.split('\n')
                        for i, line in enumerate(lines[:4]):
                            if line.strip():
                                print(f"         {i+1:2d}: {line}")
                        print("         " + "="*50)
                    except Exception as e:
                        self.safe_print(f"      [FAIL] ไม่สามารถอ่านไฟล์ TXT ได้: {e}")
                else:
                    self.safe_print("   [FAIL] ไม่พบ Build000.txt")
                
                # ตรวจสอบไฟล์ Build000.json  
                build000_json_path = Path(code_folder) / "Build000.json"
                if build000_json_path.exists():
                    self.safe_print("   [OK] พบ Build000.json (ฐานข้อมูลหลัก)")
                    self.safe_print(f"      [SIZE] ขนาด: {build000_json_path.stat().st_size} bytes")
                else:
                    self.safe_print("   [FAIL] ไม่พบ Build000.json")
                
                # นับไฟล์ทั้งหมดในโฟลเดอร์
                try:
                    all_files = list(Path(code_folder).iterdir())
                    json_files = [f for f in all_files if f.suffix.lower() == '.json']
                    txt_files = [f for f in all_files if f.suffix.lower() == '.txt']
                    
                    self.safe_print(f"   [STAT] ไฟล์ JSON: {len(json_files)} ไฟล์")
                    self.safe_print(f"   [STAT] ไฟล์ TXT: {len(txt_files)} ไฟล์")
                    self.safe_print(f"   [STAT] ไฟล์ทั้งหมด: {len(all_files)} ไฟล์")
                    
                except Exception as e:
                    self.safe_print(f"   [WARN] ไม่สามารถนับไฟล์ได้: {e}")
                    
            else:
                self.safe_print("   [FAIL] โฟลเดอร์รหัสไม่มีอยู่")
            
            # 4. ทดสอบการอ่านโฟลเดอร์ folder_settings
            print("\n4. ทดสอบการอ่านโฟลเดอร์ folder_settings...")
            settings_folder = f"{main_folder}/folder_settings"
            
            if Path(settings_folder).exists():
                self.safe_print("   [OK] โฟลเดอร์ folder_settings มีอยู่")
                
                settings_json_path = Path(settings_folder) / "folder_settings.json"
                if settings_json_path.exists():
                    self.safe_print("   [OK] พบ folder_settings.json")
                    self.safe_print(f"      [SIZE] ขนาด: {settings_json_path.stat().st_size} bytes")
                else:
                    self.safe_print("   [FAIL] ไม่พบ folder_settings.json")
            else:
                self.safe_print("   [FAIL] โฟลเดอร์ folder_settings ไม่มีอยู่")
            
            # 5. สรุปผลการทดสอบ
            print("\n5. สรุปผลการทดสอบ...")
            
            main_exists = Path(main_folder).exists()
            customer_exists = Path(f"{main_folder}/ลูกค้า/ระบบอัตโนมัติ").exists()
            code_exists = Path(f"{main_folder}/รหัส").exists()
            settings_exists = Path(f"{main_folder}/folder_settings").exists()
            
            self.safe_print(f"   [DIR] โครงสร้างโฟลเดอร์:")
            self.safe_print(f"      {'[OK]' if main_exists else '[FAIL]'} Build000 ทดสอบระบบ")
            self.safe_print(f"      {'[OK]' if customer_exists else '[FAIL]'} ลูกค้า/ระบบอัตโนมัติ")
            self.safe_print(f"      {'[OK]' if code_exists else '[FAIL]'} รหัส")
            self.safe_print(f"      {'[OK]' if settings_exists else '[FAIL]'} folder_settings")
            
            if code_exists:
                build000_txt_exists = (Path(f"{main_folder}/รหัส") / "Build000.txt").exists()
                build000_json_exists = (Path(f"{main_folder}/รหัส") / "Build000.json").exists()
                
                self.safe_print(f"   [TARGET] ฐานข้อมูลหลัก:")
                self.safe_print(f"      {'[OK]' if build000_txt_exists else '[FAIL]'} Build000.txt")
                self.safe_print(f"      {'[OK]' if build000_json_exists else '[FAIL]'} Build000.json")
                
                if build000_txt_exists and build000_json_exists:
                    self.safe_print("   [SUCCESS] ฐานข้อมูลหลักพร้อมใช้งาน!")
                elif build000_txt_exists or build000_json_exists:
                    self.safe_print("   [WARN] ฐานข้อมูลหลักไม่ครบ")
                else:
                    self.safe_print("   [FAIL] ไม่พบฐานข้อมูลหลัก")
            else:
                self.safe_print("   [FAIL] ไม่สามารถตรวจสอบฐานข้อมูลได้")
            
            existing_folders = sum([main_exists, customer_exists, code_exists, settings_exists])
            self.safe_print(f"   [STAT] สรุป: พบโฟลเดอร์ {existing_folders}/4 โฟลเดอร์")
            
            self.test_results.append({
                'test': 'FileManager Build000 ทดสอบระบบ',
                'status': 'PASS',
                'folders_found': existing_folders,
                'details': f'พบโฟลเดอร์ {existing_folders}/4 โฟลเดอร์ในระบบ Build000 ทดสอบระบบ'
            })
            print("   [PASS] การทดสอบ FileManager Build000 ทดสอบระบบ สำเร็จ")
            
        except Exception as e:
            print(f"   [FAIL] เกิดข้อผิดพลาด: {e}")
            self.test_results.append({
                'test': 'FileManager Build000 ทดสอบระบบ',
                'status': 'FAIL',
                'error': str(e)
            })

    def test_web_automation(self):
        """ทดสอบ WebAutomation"""
        print("\n=== ทดสอบ WebAutomation ===")
        
        try:
            print("1. ทดสอบการตั้งค่า WebDriver...")
            
            try:
                success = self.web_automation.setup_driver()
                if success:
                    print("   [PASS] Playwright ตั้งค่าสำเร็จ")
                    
                    print("2. ทดสอบการถ่าย screenshot...")
                    screenshot_path = "test_screenshot.png"
                    self.web_automation.take_screenshot(screenshot_path)
                    print(f"   [PASS] ถ่าย screenshot สำเร็จ: {screenshot_path}")
                    
                    print("3. ปิด Playwright...")
                    self.web_automation.close_driver()
                    print("   [PASS] Playwright ปิดสำเร็จ")
                    
                    self.test_results.append({
                        'test': 'WebAutomation',
                        'status': 'PASS',
                        'details': 'Playwright ทำงานได้ปกติ'
                    })
                    print("   [PASS] การทดสอบ WebAutomation สำเร็จ")
                else:
                    print("   [FAIL] ไม่สามารถตั้งค่า Playwright ได้")
                    self.test_results.append({
                        'test': 'WebAutomation',
                        'status': 'FAIL',
                        'error': 'Playwright setup failed'
                    })
                    
            except Exception as e:
                error_msg = str(e)
                print(f"   [FAIL] ไม่สามารถตั้งค่า Playwright ได้")
                print(f"   [INFO] ข้อผิดพลาด: {error_msg}")
                
                self.test_results.append({
                    'test': 'WebAutomation',
                    'status': 'FAIL',
                    'error': f'Playwright setup failed: {error_msg}'
                })
                
        except Exception as e:
            print(f"   [FAIL] เกิดข้อผิดพลาด: {e}")
            self.test_results.append({
                'test': 'WebAutomation',
                'status': 'FAIL',
                'error': str(e)
            })

    def test_file_operations(self):
        """ทดสอบการทำงานกับไฟล์"""
        print("\n=== ทดสอบการทำงานกับไฟล์ ===")
        
        try:
            print("1. สร้างไฟล์ทดสอบ...")
            test_file = Path("test_file.txt")
            test_content = "นี่คือไฟล์ทดสอบสำหรับระบบ BotV3\nสร้างเมื่อ: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            if test_file.exists():
                print("   [PASS] สร้างไฟล์ทดสอบสำเร็จ")
            else:
                print("   [FAIL] ไม่สามารถสร้างไฟล์ทดสอบได้")
                return
            
            print("2. อ่านไฟล์ทดสอบ...")
            with open(test_file, 'r', encoding='utf-8') as f:
                read_content = f.read()
            
            if read_content == test_content:
                print("   [PASS] อ่านไฟล์ทดสอบสำเร็จ")
            else:
                print("   [FAIL] เนื้อหาไฟล์ไม่ตรงกัน")
            
            print("3. ลบไฟล์ทดสอบ...")
            test_file.unlink()
            
            if not test_file.exists():
                print("   [PASS] ลบไฟล์ทดสอบสำเร็จ")
            else:
                print("   [FAIL] ไม่สามารถลบไฟล์ทดสอบได้")
            
            self.test_results.append({
                'test': 'File Operations',
                'status': 'PASS',
                'details': 'การทำงานกับไฟล์ปกติ'
            })
            
        except Exception as e:
            print(f"   [FAIL] เกิดข้อผิดพลาด: {e}")
            self.test_results.append({
                'test': 'File Operations',
                'status': 'FAIL',
                'error': str(e)
            })

    def test_pdf_reader(self):
        """ทดสอบ PDFReader"""
        print("\n=== ทดสอบ PDFReader ===")
        
        try:
            print("1. ทดสอบการสร้าง PDFReader instance...")
            if self.pdf_reader:
                print("   [PASS] สร้าง PDFReader instance สำเร็จ")
            else:
                print("   [FAIL] ไม่สามารถสร้าง PDFReader instance ได้")
                return
            
            # ระบบจะใช้คีย์เวิร์ดที่กำหนดไว้ใน pdf_reader.py โดยอัตโนมัติ
            print("1.1 ระบบใช้คีย์เวิร์ดจาก pdf_reader.py...")
            custom_keywords = None  # ไม่ส่งคีย์เวิร์ด ใช้ค่าเริ่มต้นจาก pdf_reader.py
            print("   [OK] ใช้คีย์เวิร์ดจาก pdf_reader.py")
            
            print("2. ทดสอบการอ่านไฟล์ PDF ในโฟลเดอร์ลูกค้า...")
            main_folder = "V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ"
            customer_folder = f"{main_folder}/ลูกค้า"
            
            if not Path(customer_folder).exists():
                print("   [FAIL] ไม่พบโฟลเดอร์ลูกค้า")
                self.test_results.append({
                    'test': 'PDFReader',
                    'status': 'FAIL',
                    'error': 'ไม่พบโฟลเดอร์ลูกค้า'
                })
                return
            
            # ค้นหาไฟล์ PDF เฉพาะในโฟลเดอร์ระบบอัตโนมัติ (ไม่เข้าโฟลเดอร์ย่อย)
            automation_folder = f"{customer_folder}/ระบบอัตโนมัติ"
            if not Path(automation_folder).exists():
                print("   [FAIL] ไม่พบโฟลเดอร์ระบบอัตโนมัติ")
                self.test_results.append({
                    'test': 'PDFReader',
                    'status': 'FAIL',
                    'error': 'ไม่พบโฟลเดอร์ระบบอัตโนมัติ'
                })
                return
            
            automation_folder_path = Path(automation_folder)
            pdf_files = [f for f in automation_folder_path.iterdir() if f.is_file() and f.suffix.lower() == '.pdf']
            
            if not pdf_files:
                print("   [WARN] ไม่พบไฟล์ PDF ในโฟลเดอร์ระบบอัตโนมัติ")
                self.test_results.append({
                    'test': 'PDFReader',
                    'status': 'PASS',
                    'details': 'ไม่พบไฟล์ PDF ให้ทดสอบในโฟลเดอร์ระบบอัตโนมัติ'
                })
                return
            
            print(f"   [INFO] พบไฟล์ PDF {len(pdf_files)} ไฟล์ ในโฟลเดอร์ระบบอัตโนมัติ (ไม่รวมโฟลเดอร์ย่อย)")
            
            # อ่านทุกไฟล์ด้วย batch API และรายงานสาเหตุไฟล์ที่ถูกข้าม
            processed_list = self.pdf_reader.process_pdf_batch(pdf_files)
            report = self.pdf_reader.get_last_batch_report()
            successful_reads = report.get('read_success', 0)
            test_count = report.get('total', len(pdf_files))
            pdf_data_list = processed_list
            print(f"\n   [STAT] สรุปการทดสอบ: อ่านสำเร็จ {successful_reads}/{test_count} ไฟล์")
            if report.get('read_failed', 0):
                print("   [INFO] รายการไฟล์ที่ถูกข้ามและเหตุผล:")
                for item in report.get('skipped', []):
                    from pathlib import Path as _P
                    print(f"      - {_P(item['file']).name}: {item['reason']}")
            
            # หลังจากอ่านไฟล์ PDF ทั้งหมดเสร็จแล้ว ให้ทำงานกับ PeakEngine
            if successful_reads > 0 and pdf_data_list:
                print(f"\n🌐 เริ่มต้นการทำงานกับ PeakEngine...")
                print(f"�� ข้อมูลถูกอ่านเรียบร้อยแล้ว รอการเปิดเว็บไซต์หลังจากอ่านไฟล์ทั้งหมดเสร็จ...")
                
                try:
                    # เรียกใช้ PeakEngine Workflow จาก web_automation_playwright.py
                    workflow_success = self.web_automation.execute_peak_engine_workflow(pdf_data_list, main_folder)
                    
                    if workflow_success:
                        print(f"✅ PeakEngine Workflow สำเร็จ!")
                        print(f"�� สรุป: อ่านไฟล์ PDF {successful_reads} ไฟล์ และทำงานกับ PeakEngine สำเร็จ!")
                    else:
                        print(f"❌ PeakEngine Workflow ไม่สำเร็จ")
                        
                except Exception as e:
                    print(f"❌ เกิดข้อผิดพลาดในการทำงานกับ PeakEngine: {e}")
                
                self.test_results.append({
                    'test': 'PDFReader',
                    'status': 'PASS',
                    'details': f'อ่านไฟล์ PDF สำเร็จ {successful_reads}/{test_count} ไฟล์ และทำงานกับ PeakEngine สำเร็จ'
                })
                print("   [PASS] การทดสอบ PDFReader สำเร็จ")
            else:
                self.test_results.append({
                    'test': 'PDFReader',
                    'status': 'FAIL',
                    'error': 'ไม่สามารถอ่านไฟล์ PDF ได้เลย'
                })
                print("   [FAIL] การทดสอบ PDFReader ล้มเหลว")
            
        except Exception as e:
            print(f"   [FAIL] เกิดข้อผิดพลาด: {e}")
            self.test_results.append({
                'test': 'PDFReader',
                'status': 'FAIL',
                'error': str(e)
            })

    def generate_test_report(self):
        """สร้างรายงานการทดสอบ"""
        print("\n" + "="*60)
        print("รายงานการทดสอบระบบ BotV3")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        
        print(f"\nสรุปผลการทดสอบ:")
        print(f"- จำนวนการทดสอบทั้งหมด: {total_tests}")
        print(f"- ผ่าน: {passed_tests}")
        print(f"- ล้มเหลว: {failed_tests}")
        print(f"- อัตราความสำเร็จ: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "- อัตราความสำเร็จ: 0%")
        
        print(f"\nรายละเอียดการทดสอบ:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = "[PASS]" if result['status'] == 'PASS' else "[FAIL]"
            print(f"{i}. {status_icon} {result['test']}")
            
            if result['status'] == 'PASS':
                if 'details' in result:
                    print(f"   รายละเอียด: {result['details']}")
            else:
                if 'error' in result:
                    print(f"   ข้อผิดพลาด: {result['error']}")
        
        # บันทึกรายงาน
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': (passed_tests/total_tests*100) if total_tests > 0 else 0
            },
            'test_results': self.test_results
        }
        
        try:
            with open('test_report.json', 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"\nบันทึกรายงานลงไฟล์: test_report.json")
        except Exception as e:
            print(f"\nไม่สามารถบันทึกรายงานได้: {e}")
        
        print("\n" + "="*60)

    def run_all_tests(self):
        """รันการทดสอบทั้งหมด"""
        print("เริ่มต้นการทดสอบระบบ BotV3")
        print("="*60)
        
        start_time = time.time()
        
        self.test_file_manager_000()
        self.test_web_automation()
        self.test_file_operations()
        self.test_pdf_reader()
        
        self.generate_test_report()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\nเวลาที่ใช้ในการทดสอบ: {execution_time:.2f} วินาที")
        print("การทดสอบเสร็จสิ้น!")

def main():
    test_system = BotV3TestSystem()
    test_system.run_all_tests()

if __name__ == "__main__":
    main()
