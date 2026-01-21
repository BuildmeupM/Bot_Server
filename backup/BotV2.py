import os
import re
import json
import pdfplumber
import numpy as np
import locale
import shutil
from pdfminer.pdfdocument import PDFPasswordIncorrect
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox
from pdf2image import convert_from_path
import threading
from pathlib import Path
import time
import concurrent.futures
import requests
import pandas as pd
from datetime import datetime
from glob import glob
from PyPDF2 import PdfReader, PdfWriter
from pypdf import PdfReader, PdfWriter
import queue
import threading
import time
from datetime import datetime
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from collections import Counter
import os, re, json, time, asyncio, random, shutil
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader, PdfWriter
from collections import Counter, defaultdict
from playwright.async_api import async_playwright, TimeoutError as PwTimeout

class LineMessagingBot:
    """คลาสสำหรับส่งข้อความไปยัง LINE"""
    
    def __init__(self, channel_access_token=None, channel_secret=None):
        self.channel_access_token = channel_access_token
        self.channel_secret = channel_secret
        self.api_url = "https://api.line.me/v2/bot/message/push"
        self.group_api_url = "https://api.line.me/v2/bot/message/push"
        self.is_enabled = channel_access_token is not None
        
    def send_message(self, user_id, message, is_group=False):
        """ส่งข้อความไปยัง LINE (User หรือ Group)"""
        if not self.is_enabled:
            print("⚠️ LINE messaging is not enabled. Please set channel_access_token.")
            return False
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}"
        }
        
        data = {
            "to": user_id,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            if response.status_code == 200:
                target_type = "กลุ่ม" if is_group else "ผู้ใช้"
                print(f"✅ ส่งข้อความ LINE ไปยัง{target_type} สำเร็จ: {message[:50]}...")
                return True
            elif response.status_code == 429:
                print(f"⚠️ LINE Bot ถึงขีดจำกัดรายเดือน: {response.text}")
                print("💡 วิธีแก้ไข:")
                print("  1. อัปเกรด LINE Bot เป็น Pro Plan")
                print("  2. รอจนถึงเดือนถัดไป")
                print("  3. ใช้ LINE Bot ใหม่")
                return False
            else:
                print(f"❌ ส่งข้อความ LINE ไม่สำเร็จ: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการส่งข้อความ LINE: {e}")
            return False
    
    def send_message_to_group(self, group_id, message):
        """ส่งข้อความไปยังกลุ่ม LINE"""
        return self.send_message(group_id, message, is_group=True)
    
    def send_processing_start_to_group(self, group_id, company_name, pdf_count=0):
        """ส่งข้อความเริ่มประมวลผลไปยังกลุ่ม"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"🚀 เริ่มการทำงาน\n"
        message += f"📅 เวลา: {timestamp}\n"
        message += f"🏢 บริษัท: {company_name}\n"
        if pdf_count > 0:
            message += f"📄 พบไฟล์ PDF: {pdf_count} ไฟล์"
        else:
            message += f"📄 กำลังตรวจสอบไฟล์ PDF..."
        return self.send_message_to_group(group_id, message)
    
    def send_processing_summary_to_group(self, group_id, company_name, success_count, failed_count, total_count, incomplete_count=0, unreadable_count=0, pending_count=0):
        """ส่งข้อความสรุปการประมวลผลไปยังกลุ่ม"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"✅ เสร็จสิ้นการทำงาน\n"
        message += f"📅 เวลา: {timestamp}\n"
        message += f"🏢 บริษัท: {company_name}\n"
        message += f"📊 สรุปผลการประมวลผล:\n"
        message += f"  ✅ อ่านเอกสารได้: {success_count} เอกสาร\n"
        message += f"  ⚠️ ข้อมูลไม่ครบ: {incomplete_count} เอกสาร\n"
        message += f"  ❌ อ่านไม่ได้: {unreadable_count} เอกสาร\n"
        message += f"  ⏳ รอดำเนินการ: {pending_count} เอกสาร\n"
        message += f"  📄 รวมทั้งหมด: {total_count} เอกสาร"
        return self.send_message_to_group(group_id, message)
    
    def send_company_status(self, user_id, company_name, status, details=""):
        """ส่งสถานะการประมวลผลบริษัทไปยัง LINE"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""
🤖 สถานะการประมวลผลเอกสาร

📅 เวลา: {timestamp}
🏢 บริษัท: {company_name}
📊 สถานะ: {status}

{details}
        """.strip()
        
        return self.send_message(user_id, message)
    
    def send_processing_start(self, user_id, company_name):
        """ส่งข้อความเริ่มประมวลผล"""
        return self.send_company_status(user_id, company_name, "🟡 เริ่มประมวลผล")
    
    def send_processing_complete(self, user_id, company_name, valid_count, total_count):
        """ส่งข้อความเสร็จสิ้นการประมวลผล"""
        details = f"✅ เอกสารถูกต้อง: {valid_count} ไฟล์\n📄 เอกสารทั้งหมด: {total_count} ไฟล์"
        return self.send_company_status(user_id, company_name, "🟢 ประมวลผลเสร็จสิ้น", details)
    
    def send_processing_error(self, user_id, company_name, error_message):
        """ส่งข้อความข้อผิดพลาด"""
        return self.send_company_status(user_id, company_name, "🔴 เกิดข้อผิดพลาด", f"❌ {error_message}")
    
    def send_processing_error_to_group(self, group_id, company_name, error_message):
        """ส่งข้อความข้อผิดพลาดไปยังกลุ่ม"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"🔴 เกิดข้อผิดพลาด\n"
        message += f"📅 เวลา: {timestamp}\n"
        message += f"🏢 บริษัท: {company_name}\n"
        message += f"❌ ข้อผิดพลาด: {error_message}"
        return self.send_message_to_group(group_id, message)
    
    def send_processing_start(self, user_id, company_name, pdf_count=0):
        """ส่งข้อความเมื่อเริ่มประมวลผล"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"🚀 เริ่มการทำงาน\n"
        message += f"📅 เวลา: {timestamp}\n"
        message += f"🏢 บริษัท: {company_name}\n"
        if pdf_count > 0:
            message += f"📄 พบไฟล์ PDF: {pdf_count} ไฟล์"
        else:
            message += f"📄 กำลังตรวจสอบไฟล์ PDF..."
        self.send_message(user_id, message)
    
    def send_processing_summary(self, user_id, company_name, success_count, failed_count, total_count, incomplete_count=0, unreadable_count=0, pending_count=0):
        """ส่งข้อความสรุปการประมวลผล"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"✅ เสร็จสิ้นการทำงาน\n"
        message += f"📅 เวลา: {timestamp}\n"
        message += f"🏢 บริษัท: {company_name}\n"
        message += f"📊 สรุปผลการประมวลผล:\n"
        message += f"  ✅ อ่านเอกสารได้: {success_count} เอกสาร\n"
        message += f"  ⚠️ ข้อมูลไม่ครบ: {incomplete_count} เอกสาร\n"
        message += f"  ❌ อ่านไม่ได้: {unreadable_count} เอกสาร\n"
        message += f"  ⏳ รอดำเนินการ: {pending_count} เอกสาร\n"
        message += f"  📄 รวมทั้งหมด: {total_count} เอกสาร"
        self.send_message(user_id, message)

class PDF_Folder_Directory:
    """คลาสสำหรับอ่านไฟล์ PDF และดึงข้อมูลจากเอกสาร"""
    
    def __init__(self, file_path=None, ui_manager=None, line_bot=None, line_user_id=None, line_group_id=None):
        assert file_path, "❌ Error: file_path ไม่สามารถเป็น None ได้"
        self.file_path = file_path
        self.root = None  # ✅ แก้ไขจาก root เป็น None เนื่องจากไม่ได้ใช้
        self.documents = []
        self.company_counter = {}
        self.root_directory = file_path  # ✅ กำหนด root_directory ให้ถูกต้อง
        self.pdf_directory = self  # ✅ ให้ `pdf_directory` อ้างอิงคลาสนี้เอง
        self.ui_manager = ui_manager  # ✅ เก็บ ui_manager สำหรับส่งข้อมูลไปยัง UI
        self.pdf_reader = reding_PDF(self, ui_manager)  # ✅ ส่ง `self` และ `ui_manager` ไปใน `reding_PDF()`
        self.report_manager = ReportManager()  # ✅ เพิ่มระบบรายงาน
        self.line_bot = line_bot  # ✅ เพิ่ม LINE bot สำหรับส่งข้อความ
        self.line_user_id = line_user_id  # ✅ เพิ่ม LINE user ID
        self.line_group_id = line_group_id  # ✅ เพิ่ม LINE group ID
        # สร้างปุ่ม Tkinter
        self.running = False 

    def read_json_file(self, json_file_path):
        """ อ่านไฟล์ JSON และคืนค่าข้อมูล """
        print(f"📂 กำลังอ่านไฟล์ JSON: {json_file_path}")

        if not os.path.exists(json_file_path):
            print(f"❌ Error: ไฟล์ JSON '{json_file_path}' ไม่พบ")
            return {}

        try:
            with open(json_file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
            print(f"✅ อ่านไฟล์ JSON สำเร็จ: {json_file_path}")
            return data
        except json.JSONDecodeError as e:
            print(f"❌ Error: ไฟล์ JSON มีปัญหา: {e}")
            return {}
        
    def read_txt_file(self, txt_file_path):
        """อ่านข้อมูลจากไฟล์ TXT"""
        print(f"📂 กำลังอ่านไฟล์ TXT: {txt_file_path}")
        
        credentials = {}
        try:
            with open(txt_file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    parts = line.strip().split(' : ', 1)
                    if len(parts) == 2:
                        key, value = parts
                        credentials[key.strip()] = value.strip()
        except Exception as e:
            print(f"❌ Error อ่านไฟล์ TXT: {e}")
        
        return credentials

    def get_json_file_path(self, main_folder):
        """คืนค่าพาธของไฟล์ JSON ตามชื่อ BuildXXX เท่านั้น"""
        build_number = main_folder.split()[0]  # ✅ ดึงแค่ BuildXXX ออกมา
        json_file_path = os.path.join(r'V:\\A.โฟร์เดอร์หลัก\\Build000 ทดสอบระบบ\\รหัส', f'{build_number}.json')

        if os.path.exists(json_file_path):
            return json_file_path
        else:
            print(f"⚠️ ไม่พบไฟล์ JSON สำหรับ {build_number}, ข้ามไป...")
            return None

    def extract_build_number(self, folder_name):
        match = re.match(r'Build(\d+)', folder_name)
        return int(match.group(1)) if match else float('inf')
    
    def read_csv_files_from_customer_directory(self, directory_path):
        all_data = pd.DataFrame()
        customer_directory_path = os.path.join(directory_path, 'CSV')
        print(f"ตรวจสอบเส้นทาง: {customer_directory_path}")

        if os.path.exists(customer_directory_path) and os.path.isdir(customer_directory_path):
            csv_files = glob(os.path.join(customer_directory_path, "*.csv"))
            print(f"ไฟล์ CSV ที่พบ: {csv_files}")

            for file_path in csv_files:
                print(f"Trying to read CSV file: {file_path}")
                try:
                    # ลองอ่านไฟล์ด้วย encoding ต่างๆ
                    data = None
                    encodings = ['utf-8', 'utf-8-sig', 'cp874', 'latin-1', 'iso-8859-1']
                    
                    for encoding in encodings:
                        try:
                            data = pd.read_csv(file_path, encoding=encoding)
                            print(f"✅ อ่านไฟล์สำเร็จด้วย encoding: {encoding}")
                            break
                        except UnicodeDecodeError:
                            continue
                        except Exception as e:
                            print(f"⚠️ ไม่สามารถอ่านไฟล์ด้วย encoding {encoding}: {e}")
                            continue
                    
                    if data is None:
                        print(f"❌ ไม่สามารถอ่านไฟล์ {file_path} ด้วย encoding ใดๆ")
                        continue

                    # แปลงตัวเลขให้เป็น string แบบไม่มี .0
                    for col in ['No.', 'account_code', 'account_code2', 'account_code3']:
                        if col in data.columns:
                            data[col] = data[col].apply(
                                lambda x: str(int(float(x))) if pd.notna(x) and x != '' and str(x).strip() != '' else np.nan
                            )

                    all_data = pd.concat([all_data, data], ignore_index=True)
                    print(f"✅ Read CSV file successfully: {file_path}")
                except Exception as e:
                    print(f"❌ Error reading file {file_path}: {e}")
        else:
            print(f"❌ Directory 'CSV' not found in {customer_directory_path}")

        if all_data.empty:
            print("⚠️ No data found in CSV files or unable to read file")
        else:
            print("✅ Data read successfully")
            print(f"📊 จำนวนแถวทั้งหมด: {len(all_data)}")
            print(f"📊 จำนวนคอลัมน์: {len(all_data.columns)}")
            print(f"📊 คอลัมน์ที่มี: {list(all_data.columns)}")
            print(all_data.head(10))  # หรือ display ใน UI/Log

        return all_data


    def read_pdf_from_customer_directory(self):
        """
        อ่านไฟล์ PDF ทั้งหมดในโฟลเดอร์ 'ระบบอัตโนมัติ'
        - แยกเอกสารที่อ่านได้, ข้อมูลไม่ครบ, อ่านไม่ได้, และรอดำเนินการ
        - ย้ายเอกสารไปโฟลเดอร์ที่เหมาะสมก่อน
        - ส่งข้อมูลไป submit_to_web() หลังจากจัดการไฟล์เสร็จแล้ว
        - ดำเนินการกับโฟลเดอร์ถัดไปทันที
        """
        
        if not self.root_directory:
            print("❌ Error: root_directory ไม่ถูกกำหนดค่า")
            return [], [], [], []  # ✅ ป้องกันปัญหาการคืนค่า NoneType

        print("\n📂 กำลังประมวลผลไฟล์ PDF ทั้งหมด...")
        print(f"📂 Root Directory: {self.root_directory}")

        # ✅ สร้างตัวแปรเก็บผลลัพธ์ **นอก loop** เพื่อป้องกันการรีเซ็ตค่า
        valid_documents = []
        incomplete_documents = []
        unreadable_documents = []
        pending_documents = []
        special_folders = { 
                           "Build198", 
                           "Build316 ทดสอบระบบ",
                           "Build356", 
                           "Build386"
                           }#"Build000 ทดสอบระบบ",
        
        for main_folder in sorted(os.listdir(self.root_directory)):
            main_folder_path = os.path.join(self.root_directory, main_folder)

            if not os.path.isdir(main_folder_path) or not main_folder.startswith("Build"):
                continue

            # ✅ ถ้าเป็นโฟลเดอร์พิเศษ ให้สั่ง I3_BP_SS_Bot ทำงาน แล้วข้าม
            if main_folder in special_folders:
                print(f"\n🚀 เรียกใช้ I3_BP_SS_Bot สำหรับโฟลเดอร์: {main_folder}")
                
                # ✅ ส่งข้อความ LINE เมื่อเริ่มประมวลผลโฟลเดอร์พิเศษ
                if self.line_bot:
                    if self.line_group_id:
                        self.line_bot.send_processing_start_to_group(self.line_group_id, main_folder, 0)
                    elif self.line_user_id:
                        self.line_bot.send_processing_start(self.line_user_id, main_folder, 0)
                
                try:
                    special_bot = I3_BP_SS_Bot(main_folder_path, self)  # ← ส่ง self มาด้วยกรณีจะใช้งานร่วมกัน
                    special_bot.run()  # ← ฟังก์ชันหลักที่จะทำงาน
                    
                    # ✅ ส่งข้อความ LINE เมื่อเสร็จสิ้นโฟลเดอร์พิเศษ
                    if self.line_bot:
                        if self.line_group_id:
                            self.line_bot.send_processing_summary_to_group(
                                self.line_group_id, 
                                main_folder, 
                                success_count=1,  # สมมติว่าสำเร็จ
                                failed_count=0,
                                total_count=1,
                                incomplete_count=0,
                                unreadable_count=0,
                                pending_count=0
                            )
                        elif self.line_user_id:
                            self.line_bot.send_processing_summary(
                                self.line_user_id, 
                                main_folder, 
                                success_count=1,  # สมมติว่าสำเร็จ
                                failed_count=0,
                                total_count=1,
                                incomplete_count=0,
                                unreadable_count=0,
                                pending_count=0
                            )
                except Exception as e:
                    print(f"❌ เกิดข้อผิดพลาดใน I3_BP_SS_Bot: {e}")
                    # ✅ ส่งข้อความ LINE เมื่อเกิดข้อผิดพลาด
                    if self.line_bot:
                        if self.line_group_id:
                            self.line_bot.send_processing_error_to_group(self.line_group_id, main_folder, str(e))
                        elif self.line_user_id:
                            self.line_bot.send_processing_error(self.line_user_id, main_folder, str(e))
                continue
            main_folder_path = os.path.join(self.root_directory, main_folder)

            if not os.path.isdir(main_folder_path) or not main_folder.startswith("Build"):
                continue  # ✅ ข้ามโฟลเดอร์ที่ไม่ใช่ BuildXXX

            print(f"\n📂 กำลังประมวลผลโฟลเดอร์: {main_folder}")
            
            customer_folder_path = os.path.join(main_folder_path, 'ลูกค้า', 'ระบบอัตโนมัติ')
            if not os.path.exists(customer_folder_path):
                print(f"⚠️ ไม่พบโฟลเดอร์ {customer_folder_path}, ข้ามไป...")
                continue

            pdf_files = [f for f in sorted(os.listdir(customer_folder_path)) if f.endswith('.pdf')]
            if not pdf_files:
                print(f"⚠️ ไม่มีไฟล์ PDF ในโฟลเดอร์ {customer_folder_path}, ข้ามไป...")
                continue

            print(f"📂 พบไฟล์ PDF {len(pdf_files)} ไฟล์ ใน '{customer_folder_path}'")
            print(f"📂 รายชื่อไฟล์ PDF: {pdf_files}")
            
            # ✅ รีเซ็ตข้อมูล JSON ก่อนเริ่มประมวลผลบริษัทใหม่
            self.pdf_reader.reset_json_data()
            print(f"🔄 รีเซ็ตข้อมูล JSON สำหรับบริษัท: {main_folder}")
            
            # ✅ ส่งข้อความ LINE เมื่อเริ่มประมวลผลบริษัท (หลังจากตรวจสอบว่ามีไฟล์ PDF แล้ว)
            if self.line_bot:
                if self.line_group_id:
                    # ส่งไปยังกลุ่ม
                    self.line_bot.send_processing_start_to_group(self.line_group_id, main_folder, len(pdf_files))
                elif self.line_user_id:
                    # ส่งไปยังผู้ใช้
                    self.line_bot.send_processing_start(self.line_user_id, main_folder, len(pdf_files))

            json_file_path = self.get_json_file_path(main_folder)
            if not json_file_path:
                print(f"⚠️ ไม่พบไฟล์ JSON สำหรับ {main_folder}, ข้ามไป...")
                continue

            txt_file_path = json_file_path.replace(".json", ".txt")
            if not os.path.exists(txt_file_path):
                txt_file_path = None

            credentials = self.read_credentials(txt_file_path) if txt_file_path else {}

            # ✅ อ่านทุกไฟล์ PDF
            for pdf_file in pdf_files:
                pdf_path = Path(customer_folder_path) / pdf_file

                # ✅ รีเซ็ตข้อมูล JSON สำหรับแต่ละไฟล์ PDF
                self.pdf_reader.reset_json_data()

                try:
                    print(f"\n📄 กำลังอ่านไฟล์ PDF: {pdf_file}")
                    
                    # ✅ ส่งข้อมูลไปยัง UI log viewer
                    if self.ui_manager:
                        self.ui_manager.add_log_message(f"📄 กำลังอ่านไฟล์ PDF: {pdf_file}", "INFO")

                    with pdfplumber.open(pdf_path) as pdf:
                        text_lines = []
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text_lines.extend(page_text.split("\n"))

                    if text_lines:
                        print(f"✅ อ่านข้อความสำเร็จจากไฟล์: {pdf_file}")
                        
                        # ✅ ส่งข้อมูลไปยัง UI log viewer
                        if self.ui_manager:
                            self.ui_manager.add_log_message(f"✅ อ่านข้อความสำเร็จจากไฟล์: {pdf_file}", "SUCCESS")

                        try:
                            found_data = self.pdf_reader.extract_keywords_from_text(text_lines, json_file_path, pdf_file)
                        except Exception as e:
                            print(f"❌ เกิดข้อผิดพลาดในการดึงข้อมูลจากไฟล์ {pdf_file}: {e}")
                            if self.ui_manager:
                                self.ui_manager.add_log_message(f"❌ เกิดข้อผิดพลาดในการดึงข้อมูลจากไฟล์ {pdf_file}: {e}", "ERROR")
                            found_data = None

                        if found_data:
                            print(f"✅ ดึงข้อมูลสำเร็จจากไฟล์: {pdf_file}")
                            print(f"📄 ข้อมูลที่ดึงได้: {found_data}")
                            found_data["pdf_path"] = pdf_path
                            found_data["pdf_file"] = pdf_file  # ✅ เพิ่มชื่อไฟล์ให้แน่ใจว่ามีค่าถูกต้อง

                            # ✅ ไม่ส่งการแจ้งเตือนทุกไฟล์ เพื่อลดสแปม

                            # ✅ ตรวจสอบว่ามีข้อมูลครบถ้วนหรือไม่
                            if found_data.get("customer_code") and (found_data.get("account_code") or found_data.get("account_code2")):
                                # ตรวจสอบว่ามี document_number และ document_date หรือไม่
                                if found_data.get("document_number") and found_data.get("document_date"):
                                    valid_documents.append(found_data)
                                    if self.ui_manager:
                                        self.ui_manager.add_log_message(f"✅ เอกสารถูกต้อง: {pdf_file}", "SUCCESS")
                                else:
                                    # เอกสารที่มีข้อมูลครบแต่ไม่มี document_number หรือ document_date
                                    pending_documents.append(found_data)
                                    if self.ui_manager:
                                        self.ui_manager.add_log_message(f"⚠️ เอกสารรอดำเนินการ: {pdf_file}", "WARNING")
                            else:
                                # เอกสารที่ข้อมูลไม่ครบ
                                incomplete_documents.append(found_data)
                                if self.ui_manager:
                                    self.ui_manager.add_log_message(f"⚠️ เอกสารข้อมูลไม่ครบ: {pdf_file}", "WARNING")
                        else:
                            unreadable_documents.append({"pdf_file": pdf_file, "pdf_path": pdf_path})
                            if self.ui_manager:
                                self.ui_manager.add_log_message(f"❌ เอกสารอ่านไม่ได้: {pdf_file}", "ERROR")
                    else:
                        unreadable_documents.append({"pdf_file": pdf_file, "pdf_path": pdf_path})
                        if self.ui_manager:
                            self.ui_manager.add_log_message(f"❌ เอกสารอ่านไม่ได้: {pdf_file}", "ERROR")

                except Exception as e:
                    print(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์ {pdf_file}: {e}")
                    unreadable_documents.append({"pdf_file": pdf_file, "pdf_path": pdf_path})
                    if self.ui_manager:
                        self.ui_manager.add_log_message(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์ {pdf_file}: {e}", "ERROR")
            
            # ✅ ย้ายไฟล์ไปยังโฟลเดอร์ที่เหมาะสมก่อน
            base_destination = os.path.join(customer_folder_path, "ผลการประมวลผล")
            os.makedirs(base_destination, exist_ok=True)

            incomplete_folder = os.path.join(base_destination, "ฐานข้อมูลไม่เรียบร้อย")
            unreadable_folder = os.path.join(base_destination, "เอกสารอ่านข้อมูลไม่ได้")
            pending_folder = os.path.join(base_destination, "เอกสารรอดำเนินการ")  # ✅ เพิ่มโฟลเดอร์สำหรับเอกสารรอดำเนินการ
            os.makedirs(incomplete_folder, exist_ok=True)
            os.makedirs(unreadable_folder, exist_ok=True)
            os.makedirs(pending_folder, exist_ok=True)

            for doc in incomplete_documents:
                new_path = os.path.join(incomplete_folder, os.path.basename(doc["pdf_path"]))
                shutil.move(doc["pdf_path"], new_path)
                print(f"📁 ย้ายไฟล์ที่ข้อมูลไม่ครบไปที่: {new_path}")

            for doc in unreadable_documents:
                new_path = os.path.join(unreadable_folder, os.path.basename(doc["pdf_path"]))
                shutil.move(doc["pdf_path"], new_path)
                print(f"📁 ย้ายไฟล์ที่อ่านไม่ได้ไปที่: {new_path}")

            for doc in pending_documents:  # ✅ ย้ายเอกสารรอดำเนินการไปยังโฟลเดอร์เฉพาะ
                new_path = os.path.join(pending_folder, os.path.basename(doc["pdf_path"]))
                shutil.move(doc["pdf_path"], new_path)
                print(f"📁 ย้ายไฟล์ที่รอดำเนินการไปที่: {new_path}")

            # ✅ สร้างรายงานสำหรับเอกสารทั้งหมด
            print(f"\n📊 สรุปการประมวลผลโฟลเดอร์ {main_folder}:")
            print(f"   ✅ เอกสารถูกต้อง: {len(valid_documents)} ไฟล์")
            print(f"   ⚠️ เอกสารข้อมูลไม่ครบ: {len(incomplete_documents)} ไฟล์")
            print(f"   ❌ เอกสารอ่านไม่ได้: {len(unreadable_documents)} ไฟล์")
            print(f"   ⏳ เอกสารรอดำเนินการ: {len(pending_documents)} ไฟล์")
            print(f"   📄 รวมทั้งหมด: {len(valid_documents) + len(incomplete_documents) + len(unreadable_documents) + len(pending_documents)} ไฟล์")
            
            self.report_manager.print_summary(valid_documents, incomplete_documents, unreadable_documents, pending_documents)

            # ✅ ส่งข้อมูลไป submit_to_web() หลังจากย้ายไฟล์เสร็จแล้ว
            if valid_documents:
                print(f"\n🔹 พบข้อมูล {len(valid_documents)} รายการ ส่งไปที่ PlaywrightBot")
                try:
                    # ใช้ self.root_directory ที่ถูกกำหนดไว้ในคลาส
                    playwright_bot = PlaywrightBot(self.root_directory)
                    # ใช้ asyncio เพื่อเรียกใช้ PlaywrightBot
                    import asyncio
                    asyncio.run(playwright_bot.submit_to_web(credentials, valid_documents))
                except Exception as e:
                    print(f"❌ เกิดข้อผิดพลาดในการส่งข้อมูลผ่าน PlaywrightBot: {e}")
                    if self.ui_manager:
                        self.ui_manager.add_log_message(f"❌ เกิดข้อผิดพลาดในการส่งข้อมูลผ่าน PlaywrightBot: {e}", "ERROR")
            
            # ✅ ประมวลผลเอกสารที่ข้อมูลไม่ครบถ้วน
            if incomplete_documents:
                print(f"\n🔹 พบข้อมูล {len(incomplete_documents)} รายการที่ข้อมูลไม่ครบ")
                # ลองประมวลผลเอกสารที่ข้อมูลไม่ครบด้วย
                for doc in incomplete_documents:
                    if doc.get("customer_code") and (doc.get("account_code") or doc.get("account_code2")):
                        # ถ้ามีข้อมูลครบแล้ว ให้ย้ายไป valid_documents
                        if doc.get("document_number") and doc.get("document_date"):
                            valid_documents.append(doc)
                            incomplete_documents.remove(doc)
                            print(f"✅ ย้ายเอกสารไป valid_documents: {doc.get('pdf_file', 'unknown')}")

            # ✅ ส่งข้อความ LINE สรุปการประมวลผล
            if self.line_bot:
                success_count = len(valid_documents)
                incomplete_count = len(incomplete_documents)
                unreadable_count = len(unreadable_documents)
                pending_count = len(pending_documents)
                total_count = success_count + incomplete_count + unreadable_count + pending_count
                
                if self.line_group_id:
                    # ส่งไปยังกลุ่ม
                    self.line_bot.send_processing_summary_to_group(
                        self.line_group_id, 
                        main_folder, 
                        success_count, 
                        failed_count=incomplete_count + unreadable_count + pending_count, 
                        total_count=total_count,
                        incomplete_count=incomplete_count,
                        unreadable_count=unreadable_count,
                        pending_count=pending_count
                    )
                elif self.line_user_id:
                    # ส่งไปยังผู้ใช้
                    self.line_bot.send_processing_summary(
                        self.line_user_id, 
                        main_folder, 
                        success_count, 
                        failed_count=incomplete_count + unreadable_count + pending_count, 
                        total_count=total_count,
                        incomplete_count=incomplete_count,
                        unreadable_count=unreadable_count,
                        pending_count=pending_count
                    )

            # ✅ เสร็จสิ้นโฟลเดอร์นี้ ไปโฟลเดอร์ถัดไป
            print(f"✅ เสร็จสิ้นการประมวลผลโฟลเดอร์: {main_folder}\n")
            self.report_manager.handle_pending_documents(customer_folder_path)
        print("✅ เสร็จสิ้นการประมวลผลไฟล์ PDF ทั้งหมด!")

        # ✅ RETURN ข้อมูลทั้งหมดเพื่อให้ start_monitoring() ทำงานได้ถูกต้อง
        return valid_documents, incomplete_documents, unreadable_documents, pending_documents

    def process_pdf_file(self, pdf_path, json_file_path):
        """อ่านไฟล์ PDF และดึงข้อมูล"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

                print(f"\n📄 ข้อความจากไฟล์ PDF: {pdf_path}")
                print("-" * 50)
                print(text)  # ✅ แสดงข้อความที่อ่านได้จาก PDF
                print("-" * 50)

                if text:
                    # ✅ เรียกใช้ฟังก์ชัน `extract_keywords_from_text()` ผ่าน `self.pdf_reader`
                    found_data = self.pdf_reader.extract_keywords_from_text(text.split("\n"), json_file_path, pdf_path)
                    
                    if found_data:
                        print(f"✅ ดึงข้อมูลสำเร็จจากไฟล์: {pdf_path}")
                        return found_data
                    else:
                        print(f"⚠️ ไม่พบข้อมูลที่ต้องการในไฟล์ {pdf_path}")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์ {pdf_path}: {e}")
        return None

    def read_special_folder(self, root_directory):
        """อ่านโฟลเดอร์พิเศษเฉพาะ Build214 เท่านั้น"""
        special_folder_name = "Build214 เอส.ยู.คอมพาเนียน"
        special_folder_path = os.path.join(root_directory, special_folder_name)

        if not os.path.exists(special_folder_path):
            print(f"⚠️ ไม่พบโฟลเดอร์พิเศษ {special_folder_name}, ข้ามไป...")
            return

        print(f"📂 กำลังประมวลผลโฟลเดอร์พิเศษ: {special_folder_name}")

        sub_folders = ["1.สำนักงานใหญ่ อำเภอเมืองนนทบุรี", "2.สาขา1 ปากเกร็ด"]
        for sub_folder in sub_folders:
            sub_folder_path = os.path.join(special_folder_path, sub_folder)
            if not os.path.exists(sub_folder_path):
                continue

            # ✅ อ่าน JSON ตามโฟลเดอร์
            txt_file_name = f"Build214{'.1' if 'สาขา1' in sub_folder else ''}.txt"
            json_file_name = f"Build214{'.1' if 'สาขา1' in sub_folder else ''}.json"
            txt_file_path = os.path.join(r'V:\A.โฟร์เดอร์หลัก\Build000 ทดสอบระบบ\รหัส', txt_file_name)
            json_file_path = os.path.join(r'V:\A.โฟร์เดอร์หลัก\Build000 ทดสอบระบบ\รหัส', json_file_name)

            json_data = self.read_json_file(json_file_path)
            if not json_data:
                continue  # ✅ ถ้าไม่มี JSON ให้ข้าม

            customer_folder_path = os.path.join(sub_folder_path, 'ลูกค้า', 'ระบบอัตโนมัติ')
            pdf_files = [f for f in sorted(os.listdir(customer_folder_path)) if f.endswith('.pdf')]

            if not pdf_files:
                print(f"⚠️ ไม่มีไฟล์ PDF ใน '{customer_folder_path}', ข้ามไป...")
                continue

            for pdf_file in pdf_files:
                pdf_path = os.path.join(customer_folder_path, pdf_file)
                found_data = self.pdf_reader.extract_keywords_from_text(pdf_path, json_file_path, pdf_path)

                if found_data:
                    self.submit_to_web(json_data, [found_data])

        print("✅ ดำเนินการเสร็จสิ้น `read_special_folder()`")

       
    def read_credentials(self, file_path):
        print(f"Reading data form .txt file: {file_path}")
        credentials = {}
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                parts = line.strip().split(' : ', 1)
                if len(parts) == 2:  # ตรวจสอบว่ามีทั้ง key และ value
                    key, value = parts
                    credentials[key.strip()] = value.strip()
                else:
                    print(f"ข้ามบรรทัดที่ไม่ถูกต้อง: {line.strip()}")  # แจ้งเตือนถ้าบรรทัดไม่ถูกต้อง
        return credentials
    
    root_directories = [
        r'V:\\A.โฟร์เดอร์หลัก\\',
        r'V:\\AA.โฟรเดอร์หลัก\\'
    ]
    
    def monitor_directory(self):
        """ใช้ ThreadPoolExecutor เพื่อรันหลายโฟลเดอร์พร้อมกัน"""
        print("📂 เริ่มมอนิเตอร์โฟลเดอร์...")

    def monitor_pdf_processing(self):
        """ฟังก์ชันมอนิเตอร์ใน Thread"""
        while self.running:
            print("\n📂 กำลังประมวลผลไฟล์ PDF...")

            # ✅ ป้องกัน `NoneType` Error
            result = self.read_pdf_from_customer_directory()
            if not isinstance(result, tuple) or len(result) != 4:
                print("❌ Error: read_pdf_from_customer_directory() คืนค่าผิดรูปแบบ")
                valid_documents, incomplete_documents, unreadable_documents, pending_documents = [], [], [], []
            else:
                valid_documents, incomplete_documents, unreadable_documents, pending_documents = result

            # ✅ เรียกใช้ print_summary()
            self.report_manager.print_summary(valid_documents, incomplete_documents, unreadable_documents, pending_documents)

            # ✅ Countdown 30 วินาที
            for i in range(30, 0, -1):
                if not self.running:
                    break
                print(f"⏳ กำลังรอ {i} วินาที...", end="\r")
                time.sleep(1)

        print("\n⛔ การมอนิเตอร์หยุดลงแล้ว")
    
    def start_monitoring(self):
        """เริ่มมอนิเตอร์ไฟล์ PDF"""
        if self.running:
            print("⚠️ ระบบกำลังทำงานอยู่แล้ว!")
            return

        self.running = True
        print("✅ ระบบกำลังทำงาน...")

        self.monitoring_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """หยุดมอนิเตอร์ไฟล์ PDF"""
        self.running = False
        print("\n⛔ การมอนิเตอร์หยุดลงแล้ว")

    def monitor_loop(self):
        """ลูปการมอนิเตอร์"""
        while self.running:
            print("\n📂 กำลังประมวลผลไฟล์ PDF...")
            self.read_pdf_from_customer_directory()

            for i in range(30, 0, -1):
                if not self.running:
                    break
                print(f"⏳ กำลังรอ {i} วินาที...", end="\r")
                time.sleep(1)
        
        print("\n⛔ การมอนิเตอร์หยุดลงแล้ว")

    def print_credentials(credentials):
        print(f"Username: {credentials.get('Username', 'N/A')}")
        print(f"Password: {credentials.get('Password', 'N/A')}")
        print(f"Link company: {credentials.get('Link company', 'N/A')}")
        print(f"Link Express: {credentials.get('Link Express', 'N/A')}")
        print("\n" + "-"*40 + "\n")

    

    def read_pdf_from_multiple_directories(self, root_directories):
        """เรียกใช้งาน read_pdf_from_customer_directory() สำหรับทุกโฟลเดอร์"""
        for directory in root_directories:
            self.read_pdf_from_customer_directory(directory)  # เรียกใช้ฟังก์ชันเดิมสำหรับแต่ละโฟลเดอร์
    
    def save_status(index, status_file):
        # ตรวจสอบให้แน่ใจว่าโฟลเดอร์สำหรับ status_file มีอยู่แล้ว
        status_folder = os.path.dirname(status_file)
        if not os.path.exists(status_folder):
            os.makedirs(status_folder)

        # บันทึกสถานะของการประมวลผล
        with open(status_file, 'a') as file:
            file.write(f"{index}\n")
            print(f"Saved status for index: {index}")

    def load_completed_status(status_file):
        if os.path.exists(status_file):
            # อ่านข้อมูลจากไฟล์สถานะ
            completed_indices = pd.read_csv(status_file, header=None)[0]

            # แปลงค่าทั้งหมดให้เป็น string และตัด .0 ออกถ้ามี
            completed_indices = completed_indices.apply(
                lambda x: str(int(float(x))) if pd.notna(x) and x != '' else x
            ).astype(str)

            # แปลงค่าทั้งหมดให้เป็นเซ็ต (เพื่อไม่ให้มีค่าซ้ำ)
            completed_indices = set(completed_indices)
            
            print(f"Loaded completed indices: {completed_indices}")
            return completed_indices

        print("No completed status file found. Starting fresh.")
        return set()
    
class reding_PDF:
    def __init__(self, pdf_directory, ui_manager=None):
        self.pdf_directory = pdf_directory
        self.ui_manager = ui_manager  # ✅ เก็บ ui_manager สำหรับส่งข้อมูลไปยัง UI  # ✅ ต้องสร้างอินสแตนซ์ก่อน
        self.current_json_data = None  # ✅ เพิ่มตัวแปรเก็บข้อมูล JSON ปัจจุบัน

    def reset_json_data(self):
        """รีเซ็ตข้อมูล JSON ปัจจุบัน"""
        self.current_json_data = None
        print("🔄 รีเซ็ตข้อมูล JSON เรียบร้อย")

    def read_json_file(self, file_path):
        if not os.path.exists(file_path):
            print(f"❌ ไม่พบไฟล์ JSON: {file_path}")
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดขณะอ่าน JSON: {e}")
            return None

    def convert_date(self, date_str):
        thai_months = {
            "มกราคม": "01", "กุมภาพันธ์": "02", "มีนาคม": "03", "เมษายน": "04", "พฤษภาคม": "05",
            "มิถุนายน": "06", "กรกฎาคม": "07", "สิงหาคม": "08", "กันยายน": "09", "ตุลาคม": "10",
            "พฤศจิกายน": "11", "ธันวาคม": "12"
        }

        eng_months = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
            "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
        }

        parts = date_str.split()
        if len(parts) == 3:
            day = parts[1].strip(",")  
            month = parts[0]  
            year = parts[2]  
            if month in thai_months:
                month_num = thai_months[month]
                year = int(year) - 543  
            elif month in eng_months:
                month_num = eng_months[month]
            else:
                return None
            return f"{day.zfill(2)}/{month_num}/{year}"
        return None

    def convert_thai_date(self, thai_date_str):
        thai_months = {
            "มกราคม": "01",
            "กุมภาพันธ์": "02",
            "มีนาคม": "03",
            "เมษายน": "04",
            "พฤษภาคม": "05",
            "มิถุนายน": "06",
            "กรกฎาคม": "07",
            "สิงหาคม": "08",
            "กันยายน": "09",
            "ตุลาคม": "10",
            "พฤศจิกายน": "11",
            "ธันวาคม": "12"
        }
        parts = thai_date_str.split()
        if len(parts) == 3:
            day = parts[0]
            month_thai = parts[1]
            year_thai = int(parts[2]) - 543

            month_num = thai_months.get(month_thai, "00")

            return f"{day}/{month_num}/{year_thai}"
        return None
    
    def extract_keywords_from_text(self, lines, json_file_path, pdf_file):
        print(f"📂 Checking self.pdf_directory: {self.pdf_directory}")
        if not self.pdf_directory:
            print("❌ self.pdf_directory เป็น None!")
            return None
        
        # ✅ รีเซ็ตข้อมูล JSON ก่อนอ่านใหม่
        json_data = None
        
        # อ่านไฟล์ JSON เพื่อดึงข้อมูลรหัสลูกค้าและโค้ดบัญชี
        print(f"📂 กำลังอ่านไฟล์ JSON: {json_file_path}")
        try:
            json_data = self.pdf_directory.read_json_file(json_file_path)
            # ✅ เก็บข้อมูล JSON ปัจจุบัน
            self.current_json_data = json_data
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์ JSON: {e}")
            return None

        if not json_data:
            print(f"❌ ไม่พบข้อมูลในไฟล์ JSON: {json_file_path}")
            return None

        # ✅ แสดงรายการบริษัทใน JSON
        print("📄 รายการข้อมูลจาก JSON:")
        for company_key, data in json_data.items():
            company_name = data.get("company_name", "ไม่ระบุชื่อบริษัท")
            customer_id = data.get("customer_id", "ไม่พบ customer_id")
            account_code = data.get("account_code", "ไม่พบ account_code")
            account_code2 = data.get("account_code2", "ไม่พบ account_code2")
            print(f"🔹 Key: {company_key}")
            print(f"   ├─ Company Name : {company_name}")
            print(f"   ├─ Customer ID  : {customer_id}")
            print(f"   └─ Account Code : {account_code}")
            print(f"   └─ Account Code : {account_code2}")
            
            # ✅ ส่งข้อมูลไปยัง UI log viewer
            if self.ui_manager:
                self.ui_manager.add_log_message(f"🔹 Key: {company_key}", "INFO")
                self.ui_manager.add_log_message(f"   ├─ Company Name : {company_name}", "INFO")
                self.ui_manager.add_log_message(f"   ├─ Customer ID  : {customer_id}", "INFO")
                self.ui_manager.add_log_message(f"   └─ Account Code : {account_code}", "INFO")
                self.ui_manager.add_log_message(f"   └─ Account Code2: {account_code2}", "INFO")
        
        txt_file_path = json_file_path.replace('.json', '.txt')
        txt_data = self.pdf_directory.read_txt_file(txt_file_path)  # ✅ อ่าน TXT
        txt_content = txt_data if txt_data else "ไม่มีข้อมูลใน TXT"
    
        detected_company_name = None
        customer_id = ""
        account_code = ""
        keyword_results = {
            "เลขที่เอกสาร": "", 
            "วันที่เอกสาร": "", 
            "ยอดก่อนภาษีมูลค่าเพิ่ม": "",
            "ยอดก่อนภาษีมูลค่าเพิ่ม(NoneVat)": "",  # <== เพิ่มไว้เลย
            "ยอดภาษีมูลค่าเพิ่ม": "", 
            "ยอดหลังบวกภาษีมูลค่าเพิ่ม": ""
        }
        file_has_data = False

        # ตรวจสอบชื่อบริษัทจากเนื้อหาในไฟล์ PDF ก่อน
        detected_company_name = None
        customer_id = ""
        account_code = ""
        
        try:
            for line in lines:
                clean_line = re.sub(r'\s+', '', line).lower()
                
                for company, data in json_data.items():
                    json_company = data.get("company_name", "")
                    clean_json_company = re.sub(r'\s+', '', json_company).lower()
                    
                    if clean_json_company in clean_line:
                        detected_company_name = json_company
                        customer_id = data.get("customer_id", "ไม่พบข้อมูล").strip()
                        account_code = data.get("account_code", "ไม่พบข้อมูล").strip()
                        print(f"✅ ตรวจพบชื่อบริษัท: {detected_company_name}")
                        break

                if detected_company_name:
                    break
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการตรวจสอบชื่อบริษัท: {e}")
            return None
            
        # หากตรวจไม่พบชื่อบริษัทในเนื้อหา ให้แจ้งเตือนและออกจากฟังก์ชัน
        if not detected_company_name:
            print(f"ไม่พบชื่อบริษัทในไฟล์ {pdf_file}")
            return None

        # ดำเนินการประมวลผลข้อมูลตามบริษัทที่ตรวจพบ
        try:
            for i, line in enumerate(lines):
                if detected_company_name == "Shopee (Thailand) Co., Ltd.":
                    if 'TRSPEMKP00-00000-25' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"TRSPEMKP00-00000-25{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    elif 'TRSPECPS00-00000-25' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}',next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"TRSPECPS00-00000-25{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    elif 'TRSPEMKP00-00000-24' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}',next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"TRSPECPS00-00000-25{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    elif 'TRSPEFHM00-00000-25' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'(\d{4}-\d{6,7})\s*$', next_line)
                        if match:
                            last_number = match.group(1)
                            combined_info = f"TRSPEFHM00-00000-25{last_number}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                        else:
                            print(f"❗️ ไม่พบเลขที่รูปแบบถูกต้องในบรรทัด: {next_line}")
                    if 'วันที่/ Date' in line:
                        keyword_results["วันที่เอกสาร"] = line.split('วันที่/ Date')[-1].strip()
                        print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                    if 'Total Value of Services (Excluded VAT) after discount' in line:
                        keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = line.split('Total Value of Services (Excluded VAT) after discount')[-1].strip()
                        print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                    if 'VAT 7%' in line:
                        keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = line.split('VAT 7%')[-1].strip()
                        print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                    if 'Total Value of Services (Included VAT)' in line:
                        keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = line.split('Total Value of Services (Included VAT)')[-1].strip()
                        print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                    file_has_data = True

                elif detected_company_name == "Lazada Limited (Head Office)":
                    if 'Invoice No.:' in line:
                        keyword_results["เลขที่เอกสาร"] = line.split('Invoice No.:')[-1].strip()
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    if 'Invoice Date:' in line:
                        iso_date_str = line.split(':')[-1].strip()
                        try:
                            date_obj = datetime.strptime(iso_date_str, "%Y-%m-%d")
                            formatted_date = date_obj.strftime("%d/%m/%Y")
                            keyword_results["วันที่เอกสาร"] = formatted_date
                            print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                        except ValueError:
                            keyword_results["วันที่เอกสาร"] = iso_date_str
                    if 'Total' in line and 'Including Tax' not in line:
                        keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = line.split('Total')[-1].strip()
                        print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                    if '(VAT)' in line:
                        keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = line.split('(VAT)')[-1].strip()
                        print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                    if '(Including Tax)' in line:
                        keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = line.split('(Including Tax)')[-1].strip()
                        print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                    file_has_data = True

                elif detected_company_name == "gf.th.ar@grab.com":
                    if 'เลขที่/No.' in line:
                        keyword_results["เลขที่เอกสาร"] = line.split('เลขที่/No.')[-1].strip()
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    if 'วันที่/Date' in line:
                        keyword_results["วันที่เอกสาร"] = line.split('วันที่/Date')[-1].strip()
                        print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                    if 'รวมมูลคาสินคาและบริการ' in line:
                        keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = lines[i + 1].strip() if i + 1 < len(lines) else ""
                        print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                    if 'ภาษีมูลคาเพิ่ม' in line:
                        keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = lines[i + 1].strip() if i + 1 < len(lines) else ""
                        print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                    if 'จํานวนเงินรวมทั้งสิ้น' in line:
                        keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = lines[i + 1].strip() if i + 1 < len(lines) else ""
                        print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                    file_has_data = True
                    
                elif detected_company_name == "SPX Express (Thailand) Co., Ltd.":
                    if 'RCSPXSPB00-00000-25' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"RCSPXSPB00-00000-25{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                            pass
                    elif 'RCSPXSPR00-00000-25' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"RCSPXSPB00-00000-24{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                            pass
                    elif 'RCSPXSPB00-00000-24' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"RCSPXSPB00-00000-24{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                            pass
                    elif 'RCSPXSPR00-00000-24' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"RCSPXSPB00-00000-24{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                            pass
                    elif 'NRSPXSPW00-00000-2' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"NRSPXSPW00-00000-2{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร :{keyword_results['เลขที่เอกสาร']}")
                            pass
                    if 'วันที่/ Date' in line:
                        keyword_results["วันที่เอกสาร"] = line.split('วันที่/ Date')[-1].strip()
                        print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                    if 'จำนวนเงินรวม/ Total amount' in line:
                        keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = line.split('จำนวนเงินรวม/ Total amount')[-1].strip()
                        print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                    if 'จำนวนเงินรวม/ Total amount' in line:
                        keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = line.split('จำนวนเงินรวม/ Total amount')[-1].strip()
                        print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                    if 'จำนวนเงินรวม/ Total amount' in line:
                        keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = line.split('จำนวนเงินรวม/ Total amount')[-1].strip()
                        print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                    file_has_data = True

                elif detected_company_name == "K-BIZ Contact":
                    if 'Issued Date' in line and i + 1 < len(lines):
                        keyword_results["วันที่เอกสาร"] = lines[i + 1].strip().split()[0]
                        print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                    if 'Document number' in line and i + 1 < len(lines):
                        keyword_results["เลขที่เอกสาร"] = lines[i + 1].strip().split()[1]
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    if 'บัตรเครดิต/เดบิต' in line:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = parts[3]
                            print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                            keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = parts[4]
                            print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                            try:
                                fee = float(parts[3].replace(',', ''))
                                vat = float(parts[4].replace(',', ''))
                                keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = f"{fee + vat:.2f}"
                                print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                            except ValueError:
                                keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = ""
                            file_has_data = True   

                elif detected_company_name == "Delivery Hero (Thailand) Co., Ltd.":
                    if 'Tax invoice No. :' in line:
                        keyword_results["เลขที่เอกสาร"] = line.split('Tax invoice No. :')[-1].strip()
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    if 'Tax invoice Date :' in line:
                        iso_date_str = line.split(':')[-1].strip()
                        try:
                            date_obj = datetime.strptime(iso_date_str, "%Y-%m-%d")
                            formatted_date = date_obj.strftime("%d/%m/%Y")
                            keyword_results["วันที่เอกสาร"] = formatted_date
                            print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                        except ValueError:
                            keyword_results["วันที่เอกสาร"] = iso_date_str
                            print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                    if 'Amount before VAT' in line:
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = line.split('Amount before VAT')[-1].strip()
                            print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                    if 'VAT 7%' in line:
                            keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = line.split('VAT 7%')[-1].strip()
                            print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                    if 'Total' in line:
                        keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = line.split('Four Hundred Eighty-One Baht And Ninety-Three Satang Total')[-1].strip()
                        try:
                            before_vat = float(keyword_results.get("ยอดก่อนภาษีมูลค่าเพิ่ม", "").replace(',', ''))
                            vat = float(keyword_results.get("ยอดภาษีมูลค่าเพิ่ม", "").replace(',', ''))
                            keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = f"{before_vat + vat:,.2f}"
                            print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                        except ValueError:
                            keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = ""
                            print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                    file_has_data = True
                            
                elif detected_company_name == "Purple Ventures Company Limited":
                    if 'เลขที่ / No. :' in line:
                        keyword_results["เลขที่เอกสาร"] = line.split('เลขที่ / No. :')[-1].strip() 
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    if 'วันที่ / Date :' in line:
                        keyword_results["วันที่เอกสาร"] = line.split('วันที่ / Date :')[-1].strip()
                        print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                    if '(ก่อนภาษีมูลค่าเพิ่ม)' in line:
                        keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = line.split('(ก่อนภาษีมูลค่าเพิ่ม)')[-1].strip()
                        print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                    if 'ภาษีมูลค่าเพิ่ม 7%' in line:
                        keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = line.split('ภาษีมูลค่าเพิ่ม 7%')[-1].strip()
                        print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                    if '(รวมภาษีมูลค่าเพิ่ม)' in line:
                        keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = line.split('(รวมภาษีมูลค่าเพิ่ม)')[-1].strip()
                        print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                    file_has_data = True
            
                # elif detected_company_name == "Omise Company Limited (Head Office)":
                #     if 'Receipt No.' in line and i + 1 < len(lines):
                #         keyword_results["เลขที่เอกสาร"] = lines[i + 1].strip().split()[0].replace(',', '')
                #         print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                #     if 'Date | 6(+415' in line:
                #         keyword_results["วันที่เอกสาร"] = line.split('Date | 6(+415')[-1].strip()
                #         print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                #     if 'Subtotal | !"#$%%&'()*&%.& ' in line:
                #         keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = line.split('Subtotal | !"#$%%&'()*&%.& ')[-1].strip()
                #         print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                #     if 'VAT | /#0)&12!"#'34"& 7% ' in line:
                #         keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = line.split('VAT | /#0)&12!"#'34"& 7% ')[-1].strip()
                #         print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                #     if 'Total | %/:/%6<4(;)$*;+ ' in line:
                #         keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = line.split('Total | %/:/%6<4(;)$*;+ ')[-1].strip()
                #         print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                #     file_has_data = True

                elif detected_company_name == "บริษัท ทรู มันนี่ จำกัด":
                    if 'Document No. ' in line :
                        keyword_results["เลขที่เอกสาร"] = line.split('Document No. ')[-1].strip()
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    if 'Date ' in line:
                        thai_date_str = line.split()[-3:]
                        thai_date_str = " ".join(thai_date_str) 
                        keyword_results["วันที่เอกสาร"] = self.convert_thai_date(thai_date_str)
                    if 'Total Amount Before Vat ' in line:
                        keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = line.split('Total Amount Before Vat ')[-1].strip()
                        print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                    if 'VAT 7% ' in line:
                        keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = line.split('VAT 7% ')[-1].strip()
                        print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                    if 'Grand Total ' in line:
                        keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = line.split('Grand Total ')[-1].strip()
                        print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                    file_has_data = True

                elif detected_company_name == "บริษัท ไลน์แมน (ประเทศไทย) จำกัด (สำนักงานใหญ่)":
                    if 'เลขที่ : ' in line:
                        keyword_results["เลขที่เอกสาร"] = line.split('เลขที่ : ')[-1].strip()
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    if 'วันที่ (ว/ด/ป) : ' in line:
                        keyword_results["วันที่เอกสาร"] = line.split('วันที่ (ว/ด/ป) : ')[-1].strip()
                        print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                    if 'จำนวนเงินค่าบริการ ' in line:
                        keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = line.split('จำนวนเงินค่าบริการ ')[-1].strip()
                        print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                    if 'ภาษีมูลค่าเพิ่ม ' in line:
                        keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = line.split('ภาษีมูลค่าเพิ่ม ')[-1].strip()
                        print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                    if 'จำนวนเงินทั้งสิ้น ' in line:
                        keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = line.split('จำนวนเงินทั้งสิ้น ')[-1].strip()
                        print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                    file_has_data = True
            
                elif detected_company_name == "บริษัท กาแฟพันธุ์ไทย จำกัด":
                    print(f"พบบริษัท บริษัท กาแฟพันธุ์ไทย จำกัด ที่บรรทัด {i}: {line}")
                    if 'ETIV' in line:
                        etiv_no = re.search(r'ETIV\d+', line)
                        if etiv_no:
                            keyword_results["เลขที่เอกสาร"] = etiv_no.group(0)
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")

                    if 'สาขาที่' in line:
                        date_match = re.search(r'\d{2}\.\d{2}\.\d{4}', line)
                        if date_match:
                            formatted_date = date_match.group(0).replace('.', '/')
                            keyword_results["วันที่เอกสาร"] = formatted_date
                            print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")

                    if "INVOICE/TAX INVOICE" in line:
                        floats_found = []
                        for l in lines[i:]:
                            nums = re.findall(r'\d+\.\d{2}', l)
                            for num in nums:
                                if f"{num}.202" in l or f"{num}.20" in l:
                                    continue
                                try : 
                                    if float(num) > 10:
                                        floats_found.append(num)
                                except: 
                                    pass
                        print(f"floasts_found: {floats_found}")
                        if len(floats_found) >= 3:
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = floats_found[1]
                            keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = floats_found[3]
                            keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = floats_found[2]
                            print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                            print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                            print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                        file_has_data = True

                elif detected_company_name == "บริษัท แมกซ์ การ์ด จำกัด":
                    if 'ETIV' in line:
                        keyword_results["เลขที่เอกสาร"] = line.strip().split()[-1]
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")

                    if 'RECEIPT/TAX INVOICE' in line:
                        # 🔹 หาวันที่ภายใน 15 บรรทัดหลังจากเจอ REFERENCE LINE
                        for m in range(i, i + 15):
                            if m < len(lines):
                                date_match = re.search(r'\d{2}\.\d{2}\.\d{4}', lines[m])
                                if date_match:
                                    raw_date = date_match.group()
                                    keyword_results["วันที่เอกสาร"] = raw_date.replace('.', '/')
                                    print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                                    break
                        # 🔹 ไล่จากบรรทัดล่างสุดเพื่อหาข้อมูลการเงิน 3 บรรทัด
                        vat_total_lines = []
                        for reverse_line in reversed(lines):
                            if re.search(r'\d+\.\d{2}', reverse_line):
                                vat_total_lines.append(reverse_line.strip())
                            if len(vat_total_lines) == 3:
                                break
                        if len(vat_total_lines) == 3:
                            # ยอดหลังบวกภาษี
                            match_total = re.search(r'(\d+\.\d{2})', vat_total_lines[2])
                            if match_total:
                                keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = match_total.group(1)
                                print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                            # ภาษีมูลค่าเพิ่ม
                            match_vat = re.search(r'(\d+\.\d{2})', vat_total_lines[1])
                            if match_vat:
                                keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = match_vat.group(1)
                                print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                            # ยอดก่อนภาษี
                            match_before_vat = re.search(r'(\d+\.\d{2})', vat_total_lines[0])
                            if match_before_vat:
                                keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = match_before_vat.group(1)
                                print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                        file_has_data = True

                elif detected_company_name == "Ksher Payment Co., Ltd.":
                            if 'เลขที่/No.' in line:
                                    keyword_results["เลขที่เอกสาร"] = line.split('เลขที่/No.')[1].strip()
                                    print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                            if 'วันที่/Date' in line:
                                    keyword_results["วันที่เอกสาร"] = line.split('วันที่/Date.')[1].strip()
                                    print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                            if 'GrandTotal' in line:
                                    parts = line.split('GrandTotal')[1].strip().split()
                                    keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = parts[1]
                                    print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                                    keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = parts[2]
                                    print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                                    keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = float(parts[1]) + float(parts[2])
                                    print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                            file_has_data = True

                elif detected_company_name == "Lazada Express Limited":
                            if 'Invoice No.:' in line:
                                keyword_results["เลขที่เอกสาร"] = line.split('Invoice No.')[1].strip()
                                print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                            if 'Invoice Date:' in line:
                                date_str = line.split('Invoice Date:')[1].strip()
                                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                                formatted_date = date_obj.strftime("%d/%m/%Y")
                                keyword_results["วันที่เอกสาร"] = formatted_date
                                print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                            if 'Net Total Shipping Fee' in line:
                                keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = line.split()[-1].strip()
                                print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                            file_has_data = True
                            
                elif detected_company_name == "Thai Happy Logistics Ltd. (Head Office)":
                    if 'Receipt Number :' in line:
                        keyword_results["เลขที่เอกสาร"] = line.split('Receipt Number :')[-1].strip()

                    if 'Receipt Date :' in line:
                        match = re.search(r'Receipt Date : (.+)', line)
                        if match:
                            date_str = match.group(1).strip()
                            try:
                                date_obj = datetime.strptime(date_str, "%b %d, %Y")
                                keyword_results["วันที่เอกสาร"] = date_obj.strftime("%d/%m/%Y")
                            except ValueError:
                                pass
                    if 'Total Amount' in line:
                        parts = line.split('฿')
                        if len(parts) > 1:
                            total_amount = parts[1].strip()
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = total_amount
                            keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = total_amount
                            keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = total_amount
                    file_has_data = True
                    
                elif detected_company_name == "LINE Company (THAILAND) LIMITED":
                    if 'Tax Invoice No.' in line:
                        keyword_results["เลขที่เอกสาร"] = line.split('Tax Invoice No.')[-1].strip()

                    elif 'Tax Invoice Date:' in line:
                        match_Line_Company = re.search(r'Tax Invoice Date: ([\d.]+)', line)
                        if match_Line_Company:
                            date_str = match_Line_Company.group(1).strip()
                            try:
                                date_obj = datetime.strptime(date_str, "%Y.%m.%d")
                                keyword_results["วันที่เอกสาร"] = date_obj.strftime("%d/%m/%Y")
                            except ValueError:
                                print("❌ รูปแบบวันที่ไม่ถูกต้อง:", date_str)

                    elif 'Amount before discount' in line:
                        match = re.search(r'Amount before discount\s+([0-9.]+)', line)
                        if match:
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = match.group(1).strip()

                    elif 'VAT 7%' in line:
                        match = re.search(r'VAT 7%\s+([0-9.]+)', line)
                        if match:
                            keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = match.group(1).strip()

                    elif 'Amount Inc VAT' in line:
                        match = re.search(r'Amount Inc VAT\s+([0-9.]+)', line)
                        if match:
                            keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = match.group(1).strip()

                    file_has_data = True
                    
                elif detected_company_name == "บริษัท เคอีเอ็กซ์ เอ็กซ์เพรส (ประเทศไทย) จำกัด (มหาชน)":
                    if 'เลขที่ใบเสร็จ' in line and 'วันที่' in line:
                        match = re.search(r'เลขที่ใบเสร็จ\s*:\s*(\S+)\s*วันที่\s*:\s*(\d{2}/\d{2}/\d{4})',line)
                        if match :
                            keyword_results["เลขที่เอกสาร"] = match.group(1)
                            keyword_results["วันที่เอกสาร"] = match.group(2)
                    if 'Net Total (ยอดสุทธิ)' in line:
                        parts = line.split()
                        if len(parts) > 1:
                            Net_total = parts[3].strip()
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = Net_total
                            keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = Net_total
                            keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = Net_total
                    file_has_data = True
                
                elif detected_company_name == "TikTok Shop (Thailand) Ltd. (Head Office)":
                    if 'Invoice number :' in line:
                        keyword_results["เลขที่เอกสาร"] = line.split(":")[-1].strip()
                    elif 'Invoice date :' in line:
                        match = re.search(r'Invoice date : (.+)', line)
                        if match:
                            date_str = match.group(1).strip()
                            try:
                                date_obj = datetime.strptime(date_str, "%b %d, %Y")
                                keyword_results["วันที่เอกสาร"] = date_obj.strftime("%d/%m/%Y")
                            except ValueError:
                                pass
                    elif 'Subtotal (excluding VAT)' in line:
                        parts = line.split("฿")
                        if len(parts) > 1:
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = parts[-1].strip()
                    elif 'Total VAT 7%' in line:
                        parts = line.split("฿")
                        if len(parts) > 1:
                            keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = parts[-1].strip()
                    elif 'Total amount (including VAT)' in line:
                        parts = line.split("฿")
                        if len(parts) > 1:
                            keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = parts[-1].strip()
                    file_has_data = True
                    
                elif detected_company_name == "บริษัท แอดวานซ์ ไวร์เลส เน็ทเวอร์ค จํากัด":
                        if 'เลขที่' in line and 'วันที่' in line:
                            match = re.search(r'เลขที่\s+(W-\S+)\s+วันที่\s+(\d{2}/\d{2}/\d{4})', line)
                            if match:
                                keyword_results["เลขที่เอกสาร"] = match.group(1)
                                keyword_results["วันที่เอกสาร"] = match.group(2)
                        elif 'Grand Total' in line:
                            Grand_total = re.findall(r'[\d,]+\.\d{2}', line)
                            if len(Grand_total) >= 3:
                                keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = Grand_total[1]  
                                keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = Grand_total[2]     
                                keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = Grand_total[3]  
                        file_has_data = True
                        
                elif detected_company_name == "บริษัท ชิปป๊อป จำกัด (สำนักงานใหญ่)":
                    for i, line in enumerate(lines):
                        if 'เลขที่/Receipt No.' in line:
                            match = re.search(r'เลขที่/Receipt No\.\s+(\S+)', line)
                            if match:
                                keyword_results["เลขที่เอกสาร"] = match.group(1)

                        elif 'วันที่/Date' in line:
                            match = re.search(r'วันที่/Date\s+(\d{2}/\d{2}/\d{4})', line)
                            if match:
                                keyword_results["วันที่เอกสาร"] = match.group(1)

                        elif 'นิติบุคคลโปรดหักภาษี ณ ที่จ่าย ค่าบริการ' in line:
                            values = re.findall(r'[\d,]+\.\d{2}', line)
                            if values:
                                keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = values[0]

                        elif 'ค่าขนส่งยกเว้นภาษีมูลค่าเพิ่ม' in line:
                            values = re.findall(r'[\d,]+\.\d{2}', line)
                            if values:
                                keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม(NoneVat)"] = values[0]

                        elif 'ภาษีมูลค่าเพิ่ม ค่าบริการ' in line:
                            values = re.findall(r'[\d,]+\.\d{2}', line)
                            if values:
                                keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = values[0]

                        elif 'ค่าบริการที่รวมภาษีมูลค่าเพิ่ม' in line:
                            values = re.findall(r'[\d,]+\.\d{2}', line)
                            if values:
                                keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = values[0]
                    file_has_data = True
                    
                elif detected_company_name == "Shippop Co., Ltd. (Headquarter)":
                    for i, line in enumerate(lines):
                        if 'เลขที่/Receipt No.' in line:
                            match = re.search(r'เลขที่/Receipt No\.\s+(\S+)', line)
                            if match:
                                keyword_results["เลขที่เอกสาร"] = match.group(1)
                        elif 'วันที่/Date' in line:
                            match = re.search(r'วันที่/Date\s+(\d{2}/\d{2}/\d{4})', line)
                            if match:
                                keyword_results["วันที่เอกสาร"] = match.group(1)
                        elif 'ค่าบริการ' in line:
                            values = re.findall(r'[\d,]+\.\d{2}', line)
                            if values:
                                keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = values[0]
                        elif 'ค่าขนส่งยกเว้นภาษีมูลค่าเพิ่ม' in line:
                            values = re.findall(r'[\d,]+\.\d{2}', line)
                            if values:
                                keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม(NoneVat)"] = values[0]
                        elif 'ภาษีมูลค่าเพิ่ม ค่าบริการ' in line:
                            values = re.findall(r'[\d,]+\.\d{2}', line)
                            if values:
                                keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = values[0]
                        elif 'ค่าบริการที่รวมภาษีมูลค่าเพิ่ม' in line:
                            values = re.findall(r'[\d,]+\.\d{2}', line)
                            if values:
                                keyword_results["ค่าบริการที่รวมภาษีมูลค่าเพิ่ม"] = values[0]
                    file_has_data = True

                elif detected_company_name == "ttbbank.com":
                    if 'เลขที่ใบกำากับภาษี :' in line:
                        keyword_results["เลขที่เอกสาร"] = line.split('เลขที่ใบกำากับภาษี :')[-1].strip() 
                    if 'ttbbank.com' in line:
                        try:
                            for offset in range(1,6):
                                next_line = lines[i + offset].strip()
                                if'วันที่' in next_line:
                                    match = re.search(r'\d{2}/\d{2}/\d{4}', next_line)
                                    if match:
                                        keyword_results["วันที่เอกสาร"] = match.group()
                                    break
                            line_fee = lines[i + 16].strip()
                            match = re.findall(r'[\d,]+\.\d{2}', line_fee)
                            if match and len(match) >= 1:
                                keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = match[0].replace(',','')
                            if match and len(match) >=2:
                                keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = match[1].replace(',','')
                            if match and len(match) >=3:
                                keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = match[2].replace(',','')
                        except IndexError :
                            print(" ไม่พบข้อมูลไม่ครบถ้วนในเอกสาร ttbbank.com")
                    file_has_data = True
                
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการประมวลผลข้อมูล: {e}")
            return None
                
        if file_has_data:
            print(f"\n✅ ดึงข้อมูลสำเร็จจากไฟล์: {pdf_file}")
            print(f"📄 ข้อมูลจากไฟล์ TXT: {txt_content}")  
            print(f"customer_id: {customer_id}")
            print(f"account_code: {account_code}")
            print(f"เลขที่เอกสาร: {keyword_results['เลขที่เอกสาร']}")
            print(f"วันที่เอกสาร: {keyword_results['วันที่เอกสาร']}")
            print(f"ยอดก่อนภาษีมูลค่าเพิ่ม: {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
            print(f"ยอดก่อนภาษีมูลค่าเพิ่ม(NoneVat): {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม(NoneVat)']}")
            print(f"ยอดภาษีมูลค่าเพิ่ม: {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
            print(f"ยอดหลังบวกภาษีมูลค่าเพิ่ม: {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
            
            # ✅ ส่งข้อมูลไปยัง UI log viewer
            if self.ui_manager:
                self.ui_manager.add_log_message(f"✅ ดึงข้อมูลสำเร็จจากไฟล์: {pdf_file}", "SUCCESS")
                self.ui_manager.add_log_message(f"📄 ข้อมูลจากไฟล์ TXT: {txt_content}", "INFO")
                self.ui_manager.add_log_message(f"customer_id: {customer_id}", "INFO")
                self.ui_manager.add_log_message(f"account_code: {account_code}", "INFO")
                self.ui_manager.add_log_message(f"เลขที่เอกสาร: {keyword_results['เลขที่เอกสาร']}", "INFO")
                self.ui_manager.add_log_message(f"วันที่เอกสาร: {keyword_results['วันที่เอกสาร']}", "INFO")
                self.ui_manager.add_log_message(f"ยอดก่อนภาษีมูลค่าเพิ่ม: {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}", "INFO")
                self.ui_manager.add_log_message(f"ยอดก่อนภาษีมูลค่าเพิ่ม(NoneVat): {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม(NoneVat)']}", "INFO")
                self.ui_manager.add_log_message(f"ยอดภาษีมูลค่าเพิ่ม: {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}", "INFO")
                self.ui_manager.add_log_message(f"ยอดหลังบวกภาษีมูลค่าเพิ่ม: {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}", "INFO")

            account_code2_value = keyword_results.get("ยอดก่อนภาษีมูลค่าเพิ่ม(NoneVat)", "")
            total_ex_vat = keyword_results.get("ยอดก่อนภาษีมูลค่าเพิ่ม", "")

            return {
                "company_name": detected_company_name,
                "customer_code": customer_id,
                "account_code": account_code,
                "account_code2": account_code2,  # จาก JSON
                "txt_data": txt_content,
                "document_number": keyword_results['เลขที่เอกสาร'],
                "document_date": keyword_results['วันที่เอกสาร'],
                "total_ex_vat": total_ex_vat,
                "total_ex_vat_none": keyword_results.get('ยอดก่อนภาษีมูลค่าเพิ่ม(NoneVat)', ''),
                "vat_value": keyword_results['ยอดภาษีมูลค่าเพิ่ม'],
                "total_in_vat": keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']
            }

        print(f"ไม่พบข้อมูลที่ต้องการในไฟล์ {pdf_file}")
        return None

class I3_BP_SS_Bot:
    def __init__(self, main_folder_path, parent):
        self.main_folder_path = main_folder_path
        self.parent = parent
        self.sorter = self.DocumentSorter(self.main_folder_path)

    def run(self):
        print(f"🚀 เริ่มต้นการทำงานของ I3_BP_SS_Bot ที่: {self.main_folder_path}")
        base_path = os.path.join(self.main_folder_path, "ลูกค้า", "รายจ่าย")
        if not os.path.exists(base_path):
            print("❌ ไม่พบโฟลเดอร์ 'ลูกค้า/รายจ่าย'")
            return

        self.sorter.process_nested_folders(base_path)
        self.sorter.print_report()  # ✅ ใช้ตัวนี้เป็นตัวสร้าง .txt ไปเลย
        print("✅ เสร็จสิ้นการจัดเรียงเอกสารสำหรับ I3_BP_SS_Bot")

    
    class DocumentSorter:
        def __init__(self, root_folder):
            self.root_folder = root_folder
            self.report = {
                "รายการใบเเจ้งหนี้": [],
                "รายการใบเสร็จรับเงิน": [],
                "รายการสลีปโอนเดือน": [],
                "error": []
            }
            self.root_folder = root_folder or os.getcwd()

        def create_folder_if_not_exists(self, folder_path):
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

        def move_files_to_subfolders(self, source_folder, destination_folder):
            subfolders = {
                "รายการใบเเจ้งหนี้": "invoice",
                "รายการใบเสร็จรับเงิน": "ใบเสร็จรับเงิน",
                "รายการสลีปโอนเดือน": "slip"
            }

            for subfolder_name, keyword in subfolders.items():
                subfolder_path = os.path.join(destination_folder, subfolder_name)
                self.create_folder_if_not_exists(subfolder_path)

                for file_name in os.listdir(source_folder):
                    if keyword in file_name and file_name.endswith(".pdf"):
                        source_path = os.path.join(source_folder, file_name)
                        dest_path = os.path.join(subfolder_path, file_name)
                        try:
                            shutil.move(source_path, dest_path)
                            print(f"📁 ย้ายไฟล์: {file_name} → {subfolder_name}")
                            self.report[subfolder_name].append(file_name)
                        except Exception as e:
                            print(f"❌ ไม่สามารถย้ายไฟล์ {file_name}: {e}")
                            self.report["error"].append(file_name)

        def process_nested_folders(self, base_folder):
            for subfolder_name in os.listdir(base_folder):
                subfolder_path = os.path.join(base_folder, subfolder_name)
                if os.path.isdir(subfolder_path):
                    print(f"📂 ตรวจสอบโฟลเดอร์ย่อย: {subfolder_path}")
                    filtering_folder = os.path.join(subfolder_path, "ระบบคัดกรองเอกสาร")
                    self.create_folder_if_not_exists(filtering_folder)

                    # ✅ เคลียร์รายงานก่อนเริ่มใหม่แต่ละรอบ
                    self.report = {
                        "รายการใบเเจ้งหนี้": [],
                        "รายการใบเสร็จรับเงิน": [],
                        "รายการสลีปโอนเดือน": [],
                        "error": []
                    }

                    self.move_files_to_subfolders(subfolder_path, filtering_folder)

                    # ✅ เขียนรายงานแยกไว้ในโฟลเดอร์ย่อยนี้
                    self.write_report_to_txt(subfolder_path)
        def write_report_to_txt(self, folder_path):
            report_lines = []
            total_moved = 0

            for category, files in self.report.items():
                if category != "error":
                    report_lines.append(f"\n🔸 {category} → {len(files)} ไฟล์")
                    for file in files:
                        report_lines.append(f"   • {file}")
                    total_moved += len(files)

            report_lines.append(f"\n✅ รวมไฟล์ที่ย้ายทั้งหมด: {total_moved} ไฟล์")

            if self.report["error"]:
                report_lines.append(f"\n❌ ไฟล์ที่ย้ายไม่สำเร็จ ({len(self.report['error'])}):")
                for file in self.report["error"]:
                    report_lines.append(f"   • {file}")
            else:
                report_lines.append("\n✅ ไม่มีไฟล์ที่ย้ายไม่สำเร็จ")

            report_path = os.path.join(folder_path, "i3_bp_ss_report.txt")
            try:
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(report_lines))
                print(f"📄 รายงานถูกบันทึกไว้ที่: {report_path}")
            except Exception as e:
                print(f"❌ ไม่สามารถบันทึกรายงานได้ที่ {folder_path}: {e}")

        def print_report(self):
            report_lines = []
            total_moved = 0

            for category, files in self.report.items():
                if category != "error":
                    header = f"\n🔸 {category} → {len(files)} ไฟล์"
                    print(header)
                    report_lines.append(header)
                    for file in files:
                        print(f"   • {file}")
                        report_lines.append(f"   • {file}")
                    total_moved += len(files)

            summary = f"\n✅ รวมไฟล์ที่ย้ายทั้งหมด: {total_moved} ไฟล์"
            print(summary)
            report_lines.append(summary)

            if self.report["error"]:
                error_header = f"\n❌ ไฟล์ที่ย้ายไม่สำเร็จ ({len(self.report['error'])}):"
                print(error_header)
                report_lines.append(error_header)
                for file in self.report["error"]:
                    print(f"   • {file}")
                    report_lines.append(f"   • {file}")
            else:
                print("\n✅ ไม่มีไฟล์ที่ย้ายไม่สำเร็จ")
                report_lines.append("\n✅ ไม่มีไฟล์ที่ย้ายไม่สำเร็จ")

            # ✅ บันทึกเป็น .txt ไฟล์
            report_folder = os.path.join(self.root_folder, "ระบบคัดกรองเอกสาร")  
            os.makedirs(report_folder, exist_ok=True)
            report_path = os.path.join(report_folder, "i3_bp_ss_report.txt")
            print(f"📄 รายงานการจัดเรียงไฟล์ถูกบันทึกที่: {report_path}")
            try:
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(report_lines))
                print(f"\n📝 รายงานถูกบันทึกไว้ที่: {report_path}")
            except Exception as e:
                print(f"❌ ไม่สามารถบันทึกรายงานได้: {e}")
                
        def generate_report(self):
            from datetime import datetime

            report_lines = []
            total_moved = 0

            for category, files in self.report.items():
                if category != "error":
                    header = f"\n🔸 {category} → {len(files)} ไฟล์"
                    report_lines.append(header)
                    for file in files:
                        report_lines.append(f"   • {file}")
                    total_moved += len(files)

            report_lines.append(f"\n✅ รวมไฟล์ที่ย้ายทั้งหมด: {total_moved} ไฟล์")

            if self.report["error"]:
                error_header = f"\n❌ ไฟล์ที่ย้ายไม่สำเร็จ ({len(self.report['error'])}):"
                report_lines.append(error_header)
                for file in self.report["error"]:
                    report_lines.append(f"   • {file}")
            else:
                report_lines.append("\n✅ ไม่มีไฟล์ที่ย้ายไม่สำเร็จ")

            # ✅ ตั้งชื่อไฟล์ตามเวลา
            timestamp = datetime.now().strftime("%d-%m-%Y %H.%M")
            report_filename = f"รายงานระบบการคัดกรองเอกสาร ({timestamp}).txt"
            report_path = os.path.join(self.root_folder, report_filename)

            try:
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(report_lines))
                print(f"\n📝 รายงานถูกบันทึกไว้ที่: {report_path}")
            except Exception as e:
                print(f"❌ ไม่สามารถบันทึกรายงานได้: {e}")

class Logger:
    def __init__(self): self.log_files = {}
    def initialize_log(self, log_folder):
        path = os.path.join(log_folder, "bot_log.xlsx")
        if not os.path.exists(path):
            df = pd.DataFrame(columns=[
                "ไฟล์","ชื่อไฟล์ที่เปลี่ยนและอัพโหลด","ชื่อบริษัท",
                "รหัสลูกค้า","โค้ดบัญชี","เลขที่เอกสาร","วันที่เอกสาร",
                "ยอดก่อนภาษีมูลค่าเพิ่ม","ยอดไม่มีภาษีมูลค่าเพิ่ม",
                "ยอดภาษีมูลค่าเพิ่ม","ยอดหลังบวกภาษีมูลค่าเพิ่ม"
            ])
            df.to_excel(path, index=False)
        self.log_files[log_folder] = path
    def save_log_data(self, log_folder, log_data):
        if log_folder not in self.log_files: self.initialize_log(log_folder)
        path = self.log_files[log_folder]
        df = pd.read_excel(path) if os.path.exists(path) else pd.DataFrame()
        df = pd.concat([df, pd.DataFrame(log_data)], ignore_index=True)
        df.to_excel(path, index=False)

class Moving_and_NewPDF:
    def wait_until_file_is_released(self, file_path):
        while True:
            try: os.rename(file_path, file_path); break
            except OSError: time.sleep(1.5)
    def create_new_pdf(self, input_path, output_path):
        reader, writer = PdfReader(input_path), PdfWriter()
        for p in reader.pages: writer.add_page(p)
        with open(output_path, 'wb') as f: writer.write(f)

# ===== Bot (Playwright) =====
class PlaywrightBot:
    PEAK_LOGIN_URL = "https://secure.peakengine.com/Home/Login"

    def __init__(self, root_directory:str):
        assert os.path.exists(root_directory), f"root_directory ไม่ถูกต้อง: {root_directory}"
        self.root_directory = root_directory
        self.logger = Logger()
        self.pdf_manager = Moving_and_NewPDF()
        print(f"playwrightbot เริ่มทำงานแล้ว : {root_directory}")
            
            
        def log_step(self, message:str, level:str="info"):
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_message = f"[{timestamp}]{level}: {message}"
            print(log_message)
            try:
                with open("bot_workflow.log", "a", encoding="utf-8") as f:
                    f.write(log_message + "\m")
            except: 
                pass
        # ---- mappings (ย้ายมาจาก Selenium เวอร์ชันเดิม) ----
        self.use_account_code2_companies = {
            "บริษัท ชิปป๊อป จำกัด (สำนักงานใหญ่)",
            "Shippop Co., Ltd. (Headquarter)"
        }
        # ตัวอย่าง: รวม dict ซ้ำให้เหลืออันเดียว
        self.company_groups = {
            "Shopee (Thailand) Co., Ltd.": {"label": "ค่าบริการ Shopee VAT", "special_handling": False},
            "Lazada Limited (Head Office)": {"label": "Lazada Service VAT", "special_handling": False},
            "gf.th.ar@grab.com": {"label": "Service Grab VAT", "special_handling": False},
            # ... ตัดมาเฉพาะที่ใช้จริง ...
        }
        self.company_groups2 = {
            "SPX Express (Thailand) Co., Ltd.": {"label": "Shipping SPX", "special_handling": False},
            # ...
        }
        self.company_groups3 = {
            "Shopee (Thailand) Co., Ltd.": {"label": "ค่าบริการ Shopee", "special_handling": False},
            # ...
        }
        # mapping ชื่อสั้น (ถ้าต้องใช้ในรายงาน)
        self.group1_company_name_mapping = { k:v["label"] for k,v in self.company_groups.items() }
        self.group2_company_name_mapping = { k:v["label"] for k,v in self.company_groups2.items() }
        self.group3_company_name_mapping = { k:v["label"] for k,v in self.company_groups3.items() }

    # ---------- Utilities ----------
    @staticmethod
    def clean_float_value(raw_string:str):
        if not raw_string: return 0.0
        s = raw_string.replace(" ", "")
        m = re.findall(r"\d[\d,]*\.\d+", s)
        val = m[0].replace(",","") if m else s.replace(",","")
        try: return float(val)
        except: return 0.0

    async def wait_until_value(self, page, locator_str, timeout_ms=12000):
        """รอจนกว่า input มี value (กัน while True ค้าง)"""
        loc = page.locator(locator_str)
        await loc.wait_for(state="attached", timeout=timeout_ms)
        end = time.time() + (timeout_ms/1000)
        while time.time() < end:
            v = await loc.input_value().catch(lambda _: "")
            if (v or "").strip(): return True
            await asyncio.sleep(0.3)
        return False

    # ---------- Login ----------
    async def login_peak(self, page, username:str, password:str):
        await page.goto(self.PEAK_LOGIN_URL, wait_until="domcontentloaded")
        await page.locator('[name="usernametxt"]').fill(username)
        await page.locator('[name="passwordtxt"]').fill(password)
        await page.locator('#loginbtn').click()
        # บางระบบมีปุ่ม “กลับเวอร์ชันเก่า”
        btn = page.locator('#btnBackToOldPeak')
        if await btn.count():
            await btn.click()

    # ---------- สร้าง/อัปโหลด PDF + log ----------
    async def process_document_common(self, page, document_data:dict, link_company:str, link_express:str):
        input_pdf_path = document_data.get('pdf_path')
        assert input_pdf_path and os.path.exists(input_pdf_path), f"ไม่พบไฟล์: {input_pdf_path}"

        folder_path = os.path.dirname(input_pdf_path)
        log_folder = os.path.join(folder_path, "logs")
        os.makedirs(log_folder, exist_ok=True)

        # ตั้งชื่อไฟล์ใหม่แบบยืดหยุ่น (ยกโค้ดจากของเดิมมา)
        company_name_raw = document_data.get('company_name','').strip()
        document_code = (document_data.get('document_number') or "unknown").strip()[:15]
        mapped = ( self.group3_company_name_mapping.get(company_name_raw)
                   or self.group2_company_name_mapping.get(company_name_raw)
                   or self.group1_company_name_mapping.get(company_name_raw)
                   or "Unknown Company" )
        # ตัวอย่าง: ไม่ใส่วันที่
        new_file_name = f"{document_code} {mapped}.pdf"
        new_file_path = os.path.normpath(os.path.join(folder_path, new_file_name))

        # สร้าง PDF
        self.pdf_manager.create_new_pdf(input_pdf_path, new_file_path)
        if not os.path.exists(new_file_path) or os.path.getsize(new_file_path) == 0:
            raise RuntimeError("สร้าง PDF ใหม่ไม่สำเร็จ")

        # ไปหน้า Express
        await page.goto(link_express, wait_until="domcontentloaded")

        # ตัวอย่าง: กรอกชื่อลูกค้า (แบบเดิมคุณใช้วน while-True → ใช้รอ value)
        await page.locator('[name="customer-name"]').fill(document_data['customer_code'])
        await page.keyboard.press("ArrowDown"); await page.keyboard.press("ArrowDown"); await page.keyboard.press("Enter")
        ok = await self.wait_until_value(page, '#lbcontactaddress')
        if not ok: raise TimeoutError("รอที่อยู่ลูกค้าไม่ขึ้น")

        # วันที่
        await page.locator('#iptdate').fill(document_data['document_date'])

        # กรอก account code 1/2 (ตัวอย่างย่อ)
        await page.locator('#iptaccountcode1').fill(document_data.get('account_code',''))
        await page.keyboard.press("Delete")
        await page.keyboard.press("ArrowDown"); await page.keyboard.press("Enter")
        if document_data.get('account_code2'):
            await page.locator('#iptaccountcode2').fill(document_data['account_code2'])
            await page.keyboard.press("Delete")
            await page.keyboard.press("ArrowDown"); await page.keyboard.press("Enter")

        # ราคาบรรทัด 1/2 และ VAT type ตามกฎเดิม
        await page.locator('#iptprice1').fill(str(document_data.get('total_ex_vat','')))
        await page.locator('#ddltaxstatus').select_option(label='แยกภาษี' if document_data.get('total_ex_vat') else 'รวมภาษี')
        if document_data.get('vat_value'):
            await page.locator('#iptTransactionCESummaryVat').fill(str(document_data['vat_value']))

        # อัปโหลดไฟล์ (Playwright โหดมากตรงนี้)
        # หา input[type=file] ใต้ label ที่คุณเคยใช้ XPath ยาว ๆ
        file_input = page.locator('input[type="file"]')
        await file_input.set_input_files(new_file_path)

        # แคปจอหลักฐาน
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        await page.screenshot(path=os.path.join(log_folder, f"screen_{ts}.png"), full_page=True)

        # บันทึก log
        log_data = [{
            "ไฟล์": os.path.basename(input_pdf_path),
            "ชื่อไฟล์ที่เปลี่ยนและอัพโหลด": new_file_name,
            "ชื่อบริษัท": document_data.get('company_name'),
            "รหัสลูกค้า": document_data.get('customer_code'),
            "โค้ดบัญชี": document_data.get('account_code'),
            "เลขที่เอกสาร": document_data.get('document_number'),
            "วันที่เอกสาร": document_data.get('document_date'),
            "ยอดก่อนภาษีมูลค่าเพิ่ม": document_data.get('total_ex_vat'),
            "ยอดไม่มีภาษีมูลค่าเพิ่ม": self.clean_float_value(document_data.get('account_code2_value','0')),
            "ยอดภาษีมูลค่าเพิ่ม": document_data.get('vat_value'),
            "ยอดหลังบวกภาษีมูลค่าเพิ่ม": document_data.get('total_in_vat'),
        }]
        self.logger.save_log_data(log_folder, log_data)

        # ย้ายไฟล์ตามโฟลเดอร์ที่คุณทำอยู่
        original_docs_folder = os.path.join(folder_path, 'เอกสารต้นฉบับ')
        processed_docs_folder = os.path.join(folder_path, 'เอกสารบันทึกแล้ว')
        os.makedirs(original_docs_folder, exist_ok=True)
        os.makedirs(processed_docs_folder, exist_ok=True)

        self.pdf_manager.wait_until_file_is_released(new_file_path)
        shutil.move(input_pdf_path, os.path.join(original_docs_folder, os.path.basename(input_pdf_path)))

        # แยก VAT / NoneVat ตามชื่อ
        files_with_date_folder = os.path.join(processed_docs_folder, 'VAT')
        files_without_date_folder = os.path.join(processed_docs_folder, 'NoneVat')
        os.makedirs(files_with_date_folder, exist_ok=True)
        os.makedirs(files_without_date_folder, exist_ok=True)
        dest = os.path.join(files_with_date_folder, os.path.basename(new_file_path)) \
               if re.match(r"^\d{2}\.\d{2}\.\d{4}", os.path.basename(new_file_path)) \
               else os.path.join(files_without_date_folder, os.path.basename(new_file_path))
        shutil.move(new_file_path, dest)

    # ---------- Runner ----------
    async def submit_to_web(self, credentials: dict, document_list: list[dict]):
        try:
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)  # เปลี่ยนเป็น True ได้
                context = await browser.new_context(ignore_https_errors=True, viewport={"width":1366,"height":768})
                page = await context.new_page()

                # Login
                await self.login_peak(page, credentials["Username"], credentials["Password"])

                # เปิดหน้าบริษัทก่อน (เหมือนของเดิม)
                if credentials.get("Link company"):
                    await page.goto(credentials["Link company"], wait_until="domcontentloaded")

                for doc in document_list:
                    try:
                        await self.process_document_common(page, doc, credentials.get("Link company",""), credentials.get("Link Express",""))
                        await asyncio.sleep(random.uniform(0.8, 1.6))  # มารยาท/กันโดนบล็อก
                    except Exception as e:
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        # เก็บหลักฐาน error
                        try: await page.screenshot(path=f"snap_err_{doc.get('document_number','NA')}_{ts}.png", full_page=True)
                        except: pass
                        print(f"❌ เอกสาร {doc.get('document_number')}: {e}")

                await browser.close()
        except Exception as e:
            print(f"เกิดข้อผิดพลาดใน playwrightBot: {e}")
            raise e
class ReportManager:
    """คลาสสำหรับจัดการรายงานและสถิติการประมวลผล"""
    
    def __init__(self):
        self.processing_stats = {
            'total_processed': 0,
            'success_count': 0,
            'failed_count': 0,
            'incomplete_count': 0,
            'unreadable_count': 0,
            'pending_count': 0
        }
    
    def print_summary(self, valid_documents, incomplete_documents, unreadable_documents, pending_documents):
        """พิมพ์สรุปการประมวลผล"""
        print("\n" + "="*60)
        print("�� สรุปการประมวลผลเอกสาร")
        print("="*60)
        print(f"✅ เอกสารถูกต้อง: {len(valid_documents)} ไฟล์")
        print(f"⚠️ เอกสารข้อมูลไม่ครบ: {len(incomplete_documents)} ไฟล์")
        print(f"❌ เอกสารอ่านไม่ได้: {len(unreadable_documents)} ไฟล์")
        print(f"⏳ เอกสารรอดำเนินการ: {len(pending_documents)} ไฟล์")
        print(f"📄 รวมทั้งหมด: {len(valid_documents) + len(incomplete_documents) + len(unreadable_documents) + len(pending_documents)} ไฟล์")
        print("="*60)
    
    def handle_pending_documents(self, customer_folder_path):
        """จัดการเอกสารที่รอดำเนินการ"""
        pending_folder = os.path.join(customer_folder_path, "ผลการประมวลผล", "เอกสารรอดำเนินการ")
        if os.path.exists(pending_folder):
            pending_files = [f for f in os.listdir(pending_folder) if f.endswith('.pdf')]
            if pending_files:
                print(f"📋 พบเอกสารรอดำเนินการ {len(pending_files)} ไฟล์ ใน {pending_folder}")
                for file in pending_files:
                    print(f"   - {file}")
    
    def update_stats(self, **kwargs):
        """อัปเดตสถิติการประมวลผล"""
        for key, value in kwargs.items():
            if key in self.processing_stats:
                self.processing_stats[key] = value
    
    def get_stats(self):
        """ดึงสถิติการประมวลผล"""
        return self.processing_stats.copy()
    
    def reset_stats(self):
        """รีเซ็ตสถิติการประมวลผล"""
        self.processing_stats = {key: 0 for key in self.processing_stats}

class Test_readingfile_pdf:
    """คลาสสำหรับเปิดและอ่านไฟล์ PDF พร้อมพรีวิว"""

    def __init__(self, root, pdf_managers, cooldown_time):
        self.root = root
        self.root.title("📄 ทดสอบการอ่านไฟล์ PDF")
        self.root.state("zoomed")  # เปิดเต็มจอ
        self.pdf_managers = pdf_managers  # ✅ เก็บค่าที่ส่งเข้ามา
        self.cooldown_time = cooldown_time  # ✅ เก็บค่าที่ส่งเข้ามา

        # 🟢 เฟรมหลัก
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 🔹 เฟรมแถวบน (ปุ่มควบคุม)
        self.top_frame = tk.Frame(self.main_frame)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)

        self.back_button = tk.Button(self.top_frame, text="🔙 กลับหน้าหลัก", command=self.back_to_main_window)
        self.back_button.pack(side=tk.LEFT, padx=10)

        self.select_file_button = tk.Button(self.top_frame, text="📂 เลือกไฟล์ PDF", command=self.select_pdf)
        self.select_file_button.pack(side=tk.LEFT, padx=10)

        self.compare_bot_button = tk.Button(self.top_frame, text="🤖 เทียบข้อมูล BOT", command=self.compare_bot)
        self.compare_bot_button.pack(side=tk.LEFT, padx=10)

        # 🔹 เฟรมหลักสำหรับแสดงผล (ซ้าย-ขวา)
        self.display_frame = tk.Frame(self.main_frame)
        self.display_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        # 🟡 เฟรมซ้าย (แบ่งเป็น 2 ส่วนเท่ากัน)
        self.left_frame = tk.Frame(self.display_frame)
        self.left_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)

        # 🟢 ด้านบน (Text Display)
        self.text_display = tk.Text(self.left_frame, wrap="word", height=10)
        self.text_display.pack(fill=tk.BOTH, expand=True)

        # 🟢 ด้านล่าง (เทียบข้อมูล BOT)
        self.bot_compare_text = tk.Text(self.left_frame, wrap="word", height=10)
        self.bot_compare_text.pack(fill=tk.BOTH, expand=True)

        # 🟡 เฟรมขวา (แสดง PDF Preview)
        self.right_frame = tk.Frame(self.display_frame, bg="gray")
        self.right_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=10, pady=10)

        self.canvas = tk.Canvas(self.right_frame, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 📌 ปรับ Grid Layout ให้เหมาะสม
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=2)

        self.display_frame.grid_columnconfigure(0, weight=1)  # ซ้าย
        self.display_frame.grid_columnconfigure(1, weight=2)  # ขวาเต็มจอ
        self.display_frame.grid_rowconfigure(0, weight=1)  # บน
        self.display_frame.grid_rowconfigure(1, weight=1)  # ล่าง (ซ้ายจะเท่ากัน)

    def select_pdf(self):
        """ให้ผู้ใช้เลือกไฟล์ PDF และแสดงตัวอย่างเนื้อหา พร้อมพรีวิวไฟล์"""
        file_path = filedialog.askopenfilename(
            title="เลือกไฟล์ PDF",
            filetypes=[("PDF Files", "*.pdf")]
        )

        if not file_path:
            return
        self.current_pdf_path = file_path

        # อ่านข้อความจาก PDF (2 หน้าแรก)
        try:
            with pdfplumber.open(file_path) as pdf:
                text = "\n\n".join([page.extract_text() for page in pdf.pages[:2] if page.extract_text()])
                self.text_display.delete("1.0", tk.END)
                self.text_display.insert(tk.END, text if text else "⚠️ ไม่พบข้อความใน PDF")
        except Exception as e:
            messagebox.showerror("❌ ข้อผิดพลาด", f"เกิดข้อผิดพลาดขณะอ่าน PDF\n{e}")

        # แปลง PDF เป็นรูปภาพ (พรีวิวหน้าแรก)
        try:
            images = convert_from_path(file_path, first_page=1, last_page=1, dpi=150)
            if images:
                img = images[0]

                # ปรับขนาดภาพให้พอดีกับ Canvas
                self.root.update_idletasks()  # อัปเดตขนาดหน้าต่าง
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

                img = img.resize((canvas_width, canvas_height), Image.LANCZOS)
                self.preview_image = ImageTk.PhotoImage(img)

                self.canvas.delete("all")  # ลบรูปเก่าออกก่อน
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.preview_image)

        except Exception as e:
            messagebox.showerror("❌ ข้อผิดพลาด", f"ไม่สามารถโหลดพรีวิว PDF ได้\n{e}")

    def preview_pdf(self, file_path):
        """แสดงภาพตัวอย่างของ PDF"""
        try:
            images = convert_from_path(file_path, first_page=1, last_page=1, dpi=100)
            if images:
                img = images[0].resize((500, 600), Image.LANCZOS)  # ปรับขนาด
                self.preview_image = ImageTk.PhotoImage(img)

                self.canvas.delete("all")
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.preview_image)
        
        except Exception as e:
            messagebox.showerror("❌ ข้อผิดพลาด", f"ไม่สามารถโหลดพรีวิว PDF ได้\n{e}")
        
    def compare_bot(self):
        if not hasattr(self, 'current_pdf_path') or not self.current_pdf_path:
            messagebox.showerror("⚠️ ข้อผิดพลาด", "ไม่มีไฟล์ PDF อยู่")
            return

        try:
            lines = self.text_display.get("1.0", tk.END).split("\n")
            result = self.extract_keywords_manual(lines, self.current_pdf_path)

            self.bot_compare_text.delete("1.0", tk.END)
            self.bot_compare_text.insert(tk.END, result)

        except Exception as e:
            messagebox.showerror("❌ ข้อผิดพลาด", f"ไม่สามารถวิเคราะห์ข้อมูลได้\n{e}")

    def convert_thai_date(self, thai_date_str):
        thai_months = {
            "มกราคม": "01",
            "กุมภาพันธ์": "02",
            "มีนาคม": "03",
            "เมษายน": "04",
            "พฤษภาคม": "05",
            "มิถุนายน": "06",
            "กรกฎาคม": "07",
            "สิงหาคม": "08",
            "กันยายน": "09",
            "ตุลาคม": "10",
            "พฤศจิกายน": "11",
            "ธันวาคม": "12"
        }
        parts = thai_date_str.split()
        if len(parts) == 3:
            day = parts[0]
            month_thai = parts[1]
            year_thai = int(parts[2]) - 543

            month_num = thai_months.get(month_thai, "00")

            return f"{day}/{month_num}/{year_thai}"
        return None
    
    def extract_keywords_manual(self, lines, pdf_file):
        """วิเคราะห์ข้อมูลโดยไม่ต้องใช้ JSON"""
        keyword_results = {}
        file_has_data = False
        detected_company_name = None

        # 🔍 ตรวจสอบชื่อบริษัทก่อน
        for line in lines:
            if "Shopee (Thailand) Co., Ltd." in line:
                detected_company_name = "Shopee (Thailand) Co., Ltd."
                break
            elif "Thai Happy Logistics Ltd. (Head Office)" in line:
                detected_company_name = "Thai Happy Logistics Ltd. (Head Office)"
                break
            elif "LINE Company (THAILAND) LIMITED" in line:
                detected_company_name = "LINE Company (THAILAND) LIMITED"
                break
            elif "บริษัท เคอีเอ็กซ์ เอ็กซ์เพรส (ประเทศไทย) จำกัด (มหาชน)" in line:
                detected_company_name = "บริษัท เคอีเอ็กซ์ เอ็กซ์เพรส (ประเทศไทย) จำกัด (มหาชน)"
                break
            elif "บริษัท แอดวานซ์ ไวร์เลส เน็ทเวอร์ค จํากัด" in line:
                detected_company_name = "บริษัท แอดวานซ์ ไวร์เลส เน็ทเวอร์ค จํากัด"
                break
            elif "บริษัท ชิปป๊อป จำกัด (สำนักงานใหญ่)" in line:
                detected_company_name ="บริษัท ชิปป๊อป จำกัด (สำนักงานใหญ่)"
                break
            elif "Shippop Co., Ltd. (Headquarter)" in line:
                detected_company_name = "Shippop Co., Ltd. (Headquarter)"
                break
            elif "Omise Company Limited (Head Office)" in line:
                detected_company_name = "Omise Company Limited (Head Office)"
                break
            elif "บริษัท แมกซ์ การ์ด จำกัด" in line:
                detected_company_name = "บริษัท แมกซ์ การ์ด จำกัด"
                break
            elif "กาแฟพันธุ์ไทย" in line:
                detected_company_name = "บริษัท กาแฟพันธุ์ไทย จำกัด"
                break
            elif "บริษัท ทรู มันนี่ จำกัด" in line:
                detected_company_name = "บริษัท ทรู มันนี่ จำกัด"
                break
            elif "ttbbank.com" in line:
                detected_company_name = "ttbbank.com"
                break
            
        if not detected_company_name:
            return "⚠️ ไม่สามารถระบุชื่อบริษัทได้จากเอกสาร"

        # 🧠 วิเคราะห์ตามชื่อบริษัทที่พบ
        for i, line in enumerate(lines):
            if detected_company_name == "Shopee (Thailand) Co., Ltd.":
                if 'TRSPEMKP00-00000-25' in line and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    match = re.search(r'\d{4}-\d{7}', next_line)
                    if match:
                        additional_info = match.group(0)
                        combined_info = f"TRSPEMKP00-00000-25{additional_info}"
                        keyword_results["เลขที่เอกสาร"] = combined_info
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                elif 'TRSPECPS00-00000-25' in line and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    match = re.search(r'\d{4}-\d{7}',next_line)
                    if match:
                        additional_info = match.group(0)
                        combined_info = f"TRSPECPS00-00000-25{additional_info}"
                        keyword_results["เลขที่เอกสาร"] = combined_info
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                elif 'TRSPEMKP00-00000-24' in line and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    match = re.search(r'\d{4}-\d{7}',next_line)
                    if match:
                        additional_info = match.group(0)
                        combined_info = f"TRSPEMKP00-00000-24{additional_info}"
                        keyword_results["เลขที่เอกสาร"] = combined_info
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                elif 'TRSPEFHM00-00000-25' in line and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    match = re.search(r'(\d{4}-\d{6,7})\s*$', next_line)
                    if match:
                        last_number = match.group(1)
                        combined_info = f"TRSPEFHM00-00000-25{last_number}"
                        keyword_results["เลขที่เอกสาร"] = combined_info
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    else:
                        print(f"❗️ ไม่พบเลขที่รูปแบบถูกต้องในบรรทัด: {next_line}")
                if 'วันที่/ Date' in line:
                    keyword_results["วันที่เอกสาร"] = line.split('วันที่/ Date')[-1].strip()
                    print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                if 'Total Value of Services (Excluded VAT) after discount' in line:
                    keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = line.split('Total Value of Services (Excluded VAT) after discount')[-1].strip()
                    print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                if 'VAT 7%' in line:
                    keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = line.split('VAT 7%')[-1].strip()
                    print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                if 'Total Value of Services (Included VAT)' in line:
                    keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = line.split('Total Value of Services (Included VAT)')[-1].strip()
                    print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                file_has_data = True

            elif detected_company_name == "Thai Happy Logistics Ltd. (Head Office)":
                if 'Receipt Number :' in line:
                    keyword_results["เลขที่เอกสาร"] = line.split('Receipt Number :')[-1].strip()

                elif 'Receipt Date :' in line:
                    match = re.search(r'Receipt Date : (.+)', line)
                    if match:
                        date_str = match.group(1).strip()
                        try:
                            date_obj = datetime.strptime(date_str, "%b %d, %Y")
                            keyword_results["วันที่เอกสาร"] = date_obj.strftime("%d/%m/%Y")
                        except ValueError:
                            pass
                elif 'Total Amount' in line:
                    parts = line.split('฿')
                    if len(parts) > 1:
                        total_amount = parts[1].strip()
                        keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = total_amount
                        keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = total_amount
                        keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = total_amount

                file_has_data = True
                               
            elif detected_company_name == "LINE Company (THAILAND) LIMITED":
                if 'Tax Invoice No.' in line:
                    keyword_results["เลขที่เอกสาร"] = line.split('Tax Invoice No.')[-1].strip()

                elif 'Tax Invoice Date:' in line:
                    match_Line_Company = re.search(r'Tax Invoice Date: ([\d.]+)', line)
                    if match_Line_Company:
                        date_str = match_Line_Company.group(1).strip()
                        try:
                            date_obj = datetime.strptime(date_str, "%Y.%m.%d")
                            keyword_results["วันที่เอกสาร"] = date_obj.strftime("%d/%m/%Y")
                        except ValueError:
                            print("❌ รูปแบบวันที่ไม่ถูกต้อง:", date_str)

                elif 'Amount before discount' in line:
                    match = re.search(r'Amount before discount\s+([0-9.]+)', line)
                    if match:
                        keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = match.group(1).strip()

                elif 'VAT 7%' in line:
                    match = re.search(r'VAT 7%\s+([0-9.]+)', line)
                    if match:
                        keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = match.group(1).strip()

                elif 'Amount Inc VAT' in line:
                    match = re.search(r'Amount Inc VAT\s+([0-9.]+)', line)
                    if match:
                        keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = match.group(1).strip()
                file_has_data = True
            
            elif detected_company_name == "บริษัท แมกซ์ การ์ด จำกัด":
                if 'ETIV' in line:
                    keyword_results["เลขที่เอกสาร"] = line.strip().split()[-1]
                    print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")

                if 'RECEIPT/TAX INVOICE' in line:
                    # 🔹 หาวันที่ภายใน 15 บรรทัดหลังจากเจอ REFERENCE LINE
                    for m in range(i, i + 15):
                        if m < len(lines):
                            date_match = re.search(r'\d{2}\.\d{2}\.\d{4}', lines[m])
                            if date_match:
                                raw_date = date_match.group()
                                keyword_results["วันที่เอกสาร"] = raw_date.replace('.', '/')
                                print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                                break
                    # 🔹 ไล่จากบรรทัดล่างสุดเพื่อหาข้อมูลการเงิน 3 บรรทัด
                    vat_total_lines = []
                    for reverse_line in reversed(lines):
                        if re.search(r'\d+\.\d{2}', reverse_line):
                            vat_total_lines.append(reverse_line.strip())
                        if len(vat_total_lines) == 3:
                            break
                    if len(vat_total_lines) == 3:
                        # ยอดหลังบวกภาษี
                        match_total = re.search(r'(\d+\.\d{2})', vat_total_lines[2])
                        if match_total:
                            keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = match_total.group(1)
                            print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                        # ภาษีมูลค่าเพิ่ม
                        match_vat = re.search(r'(\d+\.\d{2})', vat_total_lines[1])
                        if match_vat:
                            keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = match_vat.group(1)
                            print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                        # ยอดก่อนภาษี
                        match_before_vat = re.search(r'(\d+\.\d{2})', vat_total_lines[0])
                        if match_before_vat:
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = match_before_vat.group(1)
                            print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                    file_has_data = True 
                       
            elif detected_company_name == "บริษัท เคอีเอ็กซ์ เอ็กซ์เพรส (ประเทศไทย) จำกัด (มหาชน)":
                if 'เลขที่ใบเสร็จ' in line and 'วันที่' in line:
                    match = re.search(r'เลขที่ใบเสร็จ\s*:\s*(\S+)\s*วันที่\s*:\s*(\d{2}/\d{2}/\d{4})',line)
                    if match :
                        keyword_results["เลขที่เอกสาร"] = match.group(1)
                        keyword_results["วันที่เอกสาร"] = match.group(2)
                if 'Net Total (ยอดสุทธิ)' in line:
                    parts = line.split()
                    if len(parts) > 1:
                        Net_total = parts[3].strip()
                        keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = Net_total
                        keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = Net_total
                        keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = Net_total
                file_has_data = True
            
            elif detected_company_name == "TikTok Shop (Thailand) Ltd. (Head Office)":
                if 'Invoice number :' in line:
                    keyword_results["เลขที่เอกสาร"] = line.strip()
                elif ' Invoice date :' in line:
                    match = re.search(r'Invoice date : (.+)', line)
                    if match:
                        date_str = match.group(1).strip()
                        try:
                            date_obj = datetime.strptime(date_str, "%b %d, %Y")
                            keyword_results["วันที่เอกสาร"] = date_obj.strftime("%d/%m/%Y")
                        except ValueError:
                            pass
                elif 'Subtotal (excluding VAT)' in line:
                    keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = line.split("฿")[-1].strip()
                elif 'Total VAT 7%' in line:
                    keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = line.split("฿")[-1].strip()
                elif 'Total amount (including VAT)' in line:
                    keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = line.split("฿").strip()
                file_has_data = True
            
            elif detected_company_name == "บริษัท แอดวานซ์ ไวร์เลส เน็ทเวอร์ค จํากัด":
                    if 'เลขที่' in line and 'วันที่' in line:
                        match = re.search(r'เลขที่\s+(W-\S+)\s+วันที่\s+(\d{2}/\d{2}/\d{4})', line)
                        if match:
                            keyword_results["เลขที่เอกสาร"] = match.group(1)
                            keyword_results["วันที่เอกสาร"] = match.group(2)
                    elif 'Grand Total' in line:
                        Grand_total = re.findall(r'[\d,]+\.\d{2}', line)
                        if len(Grand_total) >= 3:
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = Grand_total[1]  
                            keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = Grand_total[2]     
                            keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = Grand_total[3]  
                    file_has_data = True
                    
            elif detected_company_name == "บริษัท ชิปป๊อป จำกัด (สำนักงานใหญ่)":
                for i, line in enumerate(lines):
                    if 'เลขที่/Receipt No.' in line:
                        match = re.search(r'เลขที่/Receipt No\.\s+(\S+)', line)
                        if match:
                            keyword_results["เลขที่เอกสาร"] = match.group(1)

                    elif 'วันที่/Date' in line:
                        match = re.search(r'วันที่/Date\s+(\d{2}/\d{2}/\d{4})', line)
                        if match:
                            keyword_results["วันที่เอกสาร"] = match.group(1)

                    elif 'นิติบุคคลโปรดหักภาษี ณ ที่จ่าย ค่าบริการ' in line:
                        values = re.findall(r'[\d,]+\.\d{2}', line)
                        if values:
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = values[0]

                    elif 'ค่าขนส่งยกเว้นภาษีมูลค่าเพิ่ม' in line:
                        values = re.findall(r'[\d,]+\.\d{2}', line)
                        if values:
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม(NoneVat)"] = values[0]

                    elif 'ภาษีมูลค่าเพิ่ม ค่าบริการ' in line:
                        values = re.findall(r'[\d,]+\.\d{2}', line)
                        if values:
                            keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = values[0]

                    elif 'ค่าบริการที่รวมภาษีมูลค่าเพิ่ม' in line:
                        values = re.findall(r'[\d,]+\.\d{2}', line)
                        if values:
                            keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = values[0]

                file_has_data = True
                
            elif detected_company_name == "Shippop Co., Ltd. (Headquarter)":
                for i, line in enumerate(lines):
                    if 'เลขที่/Receipt No.' in line:
                        match = re.search(r'เลขที่/Receipt No\.\s+(\S+)', line)
                        if match:
                            keyword_results["เลขที่เอกสาร"] = match.group(1)
                    elif 'วันที่/Date' in line:
                        match = re.search(r'วันที่/Date\s+(\d{2}/\d{2}/\d{4})', line)
                        if match:
                            keyword_results["วันที่เอกสาร"] = match.group(1)
                    elif 'ค่าบริการ' in line:
                        values = re.findall(r'[\d,]+\.\d{2}', line)
                        if values:
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = values[0]
                    elif 'ค่าขนส่งยกเว้นภาษีมูลค่าเพิ่ม' in line:
                        values = re.findall(r'[\d,]+\.\d{2}', line)
                        if values:
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม(NoneVat)"] = values[0]
                    elif 'ภาษีมูลค่าเพิ่ม ค่าบริการ (7%)' in line:
                        values = re.findall(r'[\d,]+\.\d{2}', line)
                        if values:
                            keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = values[0]
                    elif 'ค่าบริการที่รวมภาษีมูลค่าเพิ่ม' in line:
                        values = re.findall(r'[\d,]+\.\d{2}', line)
                        if values:
                            keyword_results["ค่าบริการที่รวมภาษีมูลค่าเพิ่ม"] = values[0]
                file_has_data = True
                
            # elif detected_company_name == "Omise Company Limited (Head Office)":
            #         if 'Receipt No.' in line and i + 1 < len(lines):
            #             keyword_results["เลขที่เอกสาร"] = lines[i + 1].strip().split()[0].replace(',', '')
            #             print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
            #         if 'Date | 6(+415' in line:
            #             keyword_results["วันที่เอกสาร"] = line.split('Date | 6(+415')[-1].strip()
            #             print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
            #         if 'Subtotal | !"#$%%&'()*&%.& ' in line:
            #             keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = line.split('Subtotal | !"#$%%&'()*&%.& ')[-1].strip()
            #             print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
            #         if 'VAT | /#0)&12!"#'34"& 7% ' in line:
            #             keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = line.split('VAT | /#0)&12!"#'34"& 7% ')[-1].strip()
            #             print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
            #         if 'Total | %/:/%6<4(;)$*;+ ' in line:
            #             keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = line.split('Total | %/:/%6<4(;)$*;+ ')[-1].strip()
            #             print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
            #         file_has_data = True
            
            elif detected_company_name == "บริษัท กาแฟพันธุ์ไทย จำกัด":
                print(f"พบบริษัท บริษัท กาแฟพันธุ์ไทย จำกัด ที่บรรทัด {i}: {line}")
                if 'ETIV' in line:
                    etiv_no = re.search(r'ETIV\d+', line)
                    if etiv_no:
                        keyword_results["เลขที่เอกสาร"] = etiv_no.group(0)
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")

                if 'สาขาที่' in line:
                    date_match = re.search(r'\d{2}\.\d{2}\.\d{4}', line)
                    if date_match:
                        formatted_date = date_match.group(0).replace('.', '/')
                        keyword_results["วันที่เอกสาร"] = formatted_date
                        print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")

                if "INVOICE/TAX INVOICE" in line:
                    floats_found = []
                    for l in lines[i:]:
                        nums = re.findall(r'\d+\.\d{2}', l)
                        for num in nums:
                            if f"{num}.202" in l or f"{num}.20" in l:
                                continue
                            try : 
                                if float(num) > 10:
                                    floats_found.append(num)
                            except: 
                                pass
                    print(f"floasts_found: {floats_found}")
                    if len(floats_found) >= 3:
                        keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = floats_found[1]
                        keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = floats_found[3]
                        keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = floats_found[2]
                        print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                        print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                        print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                    file_has_data = True

            elif detected_company_name == "บริษัท ทรู มันนี่ จำกัด":
                    if 'Document No. ' in line :
                        keyword_results["เลขที่เอกสาร"] = line.split('Document No. ')[-1].strip()
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    if 'Date ' in line:
                        thai_date_str = line.split()[-3:]
                        thai_date_str = " ".join(thai_date_str) 
                        keyword_results["วันที่เอกสาร"] = self.convert_thai_date(thai_date_str)
                    if 'Total Amount Before Vat ' in line:
                        keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = line.split('Total Amount Before Vat ')[-1].strip()
                        print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                    if 'VAT 7% ' in line:
                        keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = line.split('VAT 7% ')[-1].strip()
                        print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                    if 'Grand Total ' in line:
                        keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = line.split('Grand Total ')[-1].strip()
                        print(f"ยอดหลังรวมภาษี : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
                    file_has_data = True
            
            elif detected_company_name == "ttbbank.com":
                if 'เลขที่ใบกำากับภาษี :' in line:
                    keyword_results["เลขที่เอกสาร"] = line.split('เลขที่ใบกำากับภาษี :')[-1].strip() 
                if 'ttbbank.com' in line:
                    try:
                        for offset in range(1,6):
                            next_line = lines[i + offset].strip()
                            if'วันที่' in next_line:
                                match = re.search(r'\d{2}/\d{2}/\d{4}', next_line)
                                if match:
                                    keyword_results["วันที่เอกสาร"] = match.group()
                                break
                        line_fee = lines[i + 16].strip()
                        match = re.findall(r'[\d,]+\.\d{2}', line_fee)
                        if match and len(match) >= 1:
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = match[0].replace(',','')
                        if match and len(match) >=2:
                            keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = match[1].replace(',','')
                        if match and len(match) >=3:
                            keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = match[2].replace(',','')
                    except IndexError :
                        print(" ไม่พบข้อมูลไม่ครบถ้วนในเอกสาร ttbbank.com")
                file_has_data = True

         # ✅ สรุปผลลัพธ์
        if file_has_data:
            ordered_keys = [
                "เลขที่เอกสาร",
                "วันที่เอกสาร",
                "ยอดก่อนภาษีมูลค่าเพิ่ม",
                "ยอดก่อนภาษีมูลค่าเพิ่ม(NoneVat)",
                "ยอดภาษีมูลค่าเพิ่ม",
                "ยอดหลังบวกภาษีมูลค่าเพิ่ม"
            ]
            return "\n".join([f"{k} : {keyword_results.get(k, '')}" for k in ordered_keys])
        else:
            return f"⚠️ ไม่พบข้อมูลที่เกี่ยวข้องกับ {detected_company_name}"

    def back_to_main_window(self):
        """กลับไปหน้าหลัก"""
        self.root.destroy()  # ✅ ปิดหน้าต่างปัจจุบัน

        # ✅ ตรวจสอบว่ามีค่า pdf_managers และ cooldown_time หรือไม่
        if self.pdf_managers is not None and self.cooldown_time is not None:
            main_root = tk.Tk()
            UIManager(main_root, self.pdf_managers, self.cooldown_time)  # ✅ เรียก UIManager ใหม่พร้อมส่งค่า
            main_root.mainloop()
        else:
            messagebox.showerror("⚠️ ข้อผิดพลาด", "ไม่สามารถกลับไปหน้าหลักได้: ค่า pdf_managers หรือ cooldown_time หายไป")

class AdvancedUIManager:
    """UI Manager แบบใหม่ที่มีระบบ Log viewer และฟีเจอร์ครบถ้วน"""

    def __init__(self, root, pdf_managers, cooldown_time, line_bot=None, line_user_id=None):
        self.root = root
        self.pdf_managers = pdf_managers
        self.cooldown_time = cooldown_time
        self.current_index = 0
        self.is_running = False
        self.log_queue = queue.Queue()
        self.log_messages = []
        self.line_bot = line_bot  # ✅ เพิ่ม LINE bot
        self.line_user_id = line_user_id  # ✅ เพิ่ม LINE user ID
        
        # ตั้งค่าหน้าต่างหลัก
        self.root.title("🤖 PDF Processing Bot - Advanced UI")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # สร้าง style
        self.setup_styles()
        
        # สร้าง UI
        self.create_main_ui()
        
        # เริ่มการอัพเดท log
        self.update_log_display()
    
    def setup_styles(self):
        """ตั้งค่า style สำหรับ UI"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # กำหนดสี
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 16, 'bold'),
                       foreground='#2c3e50',
                       background='#ecf0f1')
        
        style.configure('Status.TLabel',
                       font=('Segoe UI', 10),
                       foreground='#34495e',
                       background='#ecf0f1')
        
        style.configure('Success.TLabel',
                       font=('Segoe UI', 10),
                       foreground='#27ae60',
                       background='#ecf0f1')
        
        style.configure('Error.TLabel',
                       font=('Segoe UI', 10),
                       foreground='#e74c3c',
                       background='#ecf0f1')
        
        style.configure('Control.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=10)
    
    def create_main_ui(self):
        """สร้าง UI หลัก"""
        # Header
        header_frame = ttk.Frame(self.root, style='Title.TFrame')
        header_frame.pack(fill='x', padx=20, pady=10)
        
        title_label = ttk.Label(header_frame, 
                               text="🤖 PDF Processing Bot - Advanced Control Panel",
                               style='Title.TLabel')
        title_label.pack()
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Left panel - Controls
        self.create_control_panel(main_container)
        
        # Right panel - Log viewer
        self.create_log_panel(main_container)
        
        # Bottom panel - Statistics
        self.create_stats_panel()
    
    def create_control_panel(self, parent):
        """สร้างแผงควบคุม"""
        control_frame = ttk.LabelFrame(parent, text="🎮 Control Panel", padding=15)
        control_frame.pack(side='left', fill='y', padx=(0, 10))
        
        # Status display
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill='x', pady=(0, 15))
        
        self.status_label = ttk.Label(status_frame, 
                                     text="⏸️ Ready to Start",
                                     style='Status.TLabel')
        self.status_label.pack()
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, 
                                           variable=self.progress_var,
                                           maximum=100)
        self.progress_bar.pack(fill='x', pady=(5, 0))
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill='x', pady=10)
        
        self.start_button = ttk.Button(button_frame,
                                      text="▶️ Start Processing",
                                      command=self.start_processing,
                                      style='Control.TButton')
        self.start_button.pack(fill='x', pady=2)
        
        self.stop_button = ttk.Button(button_frame,
                                     text="⛔ Stop Processing",
                                     command=self.stop_processing,
                                     state='disabled',
                                     style='Control.TButton')
        self.stop_button.pack(fill='x', pady=2)
        
        self.pause_button = ttk.Button(button_frame,
                                      text="⏸️ Pause",
                                      command=self.pause_processing,
                                      state='disabled',
                                      style='Control.TButton')
        self.pause_button.pack(fill='x', pady=2)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(control_frame, text="⚙️ Settings", padding=10)
        settings_frame.pack(fill='x', pady=10)
        
        # Cooldown setting
        cooldown_frame = ttk.Frame(settings_frame)
        cooldown_frame.pack(fill='x', pady=2)
        
        ttk.Label(cooldown_frame, text="Cooldown (seconds):").pack(side='left')
        self.cooldown_var = tk.StringVar(value=str(self.cooldown_time))
        cooldown_entry = ttk.Entry(cooldown_frame, textvariable=self.cooldown_var, width=10)
        cooldown_entry.pack(side='right')
        
        # Log level setting
        log_frame = ttk.Frame(settings_frame)
        log_frame.pack(fill='x', pady=2)
        
        ttk.Label(log_frame, text="Log Level:").pack(side='left')
        self.log_level_var = tk.StringVar(value="INFO")
        log_combo = ttk.Combobox(log_frame, textvariable=self.log_level_var,
                                 values=["DEBUG", "INFO", "WARNING", "ERROR"],
                                 state="readonly", width=10)
        log_combo.pack(side='right')
        
        # Quick actions
        actions_frame = ttk.LabelFrame(control_frame, text="🚀 Quick Actions", padding=10)
        actions_frame.pack(fill='x', pady=10)
        
        ttk.Button(actions_frame, text="📁 Open Log Folder",
                  command=self.open_log_folder).pack(fill='x', pady=2)
        
        ttk.Button(actions_frame, text="📊 View Statistics",
                  command=self.show_statistics).pack(fill='x', pady=2)
        
        ttk.Button(actions_frame, text="🔧 Settings",
                  command=self.open_settings).pack(fill='x', pady=2)
    
    def create_log_panel(self, parent):
        """สร้างแผง Log viewer"""
        log_frame = ttk.LabelFrame(parent, text="📋 Live Log Viewer", padding=15)
        log_frame.pack(side='right', fill='both', expand=True)
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill='x', pady=(0, 10))
        
        ttk.Button(log_controls, text="🗑️ Clear Log",
                  command=self.clear_log).pack(side='left', padx=(0, 5))
        
        ttk.Button(log_controls, text="💾 Save Log",
                  command=self.save_log).pack(side='left', padx=(0, 5))
        
        ttk.Button(log_controls, text="🔄 Auto-scroll",
                  command=self.toggle_auto_scroll).pack(side='left')
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        
        # Log filter
        filter_frame = ttk.Frame(log_controls)
        filter_frame.pack(side='right')
        
        ttk.Label(filter_frame, text="Filter:").pack(side='left')
        self.log_filter_var = tk.StringVar(value="ALL")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.log_filter_var,
                                   values=["ALL", "INFO", "WARNING", "ERROR", "SUCCESS"],
                                   state="readonly", width=10)
        filter_combo.pack(side='right')
        filter_combo.bind('<<ComboboxSelected>>', self.filter_log)
        
        # Log display
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                 height=25,
                                                 font=('Consolas', 9),
                                                 bg='#2c3e50',
                                                 fg='#ecf0f1',
                                                 insertbackground='#ecf0f1')
        self.log_text.pack(fill='both', expand=True)
        
        # Configure tags for different log levels
        self.log_text.tag_configure("INFO", foreground="#3498db")
        self.log_text.tag_configure("WARNING", foreground="#f39c12")
        self.log_text.tag_configure("ERROR", foreground="#e74c3c")
        self.log_text.tag_configure("SUCCESS", foreground="#27ae60")
        self.log_text.tag_configure("DEBUG", foreground="#95a5a6")
    
    def create_stats_panel(self):
        """สร้างแผงสถิติ"""
        stats_frame = ttk.LabelFrame(self.root, text="📊 Statistics", padding=10)
        stats_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        # Stats grid
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill='x')
        
        # Processed files
        processed_frame = ttk.Frame(stats_grid)
        processed_frame.pack(side='left', expand=True, padx=5)
        
        self.processed_count = tk.StringVar(value="0")
        ttk.Label(processed_frame, text="📄 Processed Files:",
                 style='Status.TLabel').pack()
        ttk.Label(processed_frame, textvariable=self.processed_count,
                 style='Success.TLabel').pack()
        
        # Success rate
        success_frame = ttk.Frame(stats_grid)
        success_frame.pack(side='left', expand=True, padx=5)
        
        self.success_rate = tk.StringVar(value="0%")
        ttk.Label(success_frame, text="✅ Success Rate:",
                 style='Status.TLabel').pack()
        ttk.Label(success_frame, textvariable=self.success_rate,
                 style='Success.TLabel').pack()
        
        # Current folder
        current_frame = ttk.Frame(stats_grid)
        current_frame.pack(side='left', expand=True, padx=5)
        
        self.current_folder = tk.StringVar(value="None")
        ttk.Label(current_frame, text="📂 Current Folder:",
                 style='Status.TLabel').pack()
        ttk.Label(current_frame, textvariable=self.current_folder,
                 style='Status.TLabel').pack()
        
        # Runtime
        runtime_frame = ttk.Frame(stats_grid)
        runtime_frame.pack(side='left', expand=True, padx=5)
        
        self.runtime = tk.StringVar(value="00:00:00")
        ttk.Label(runtime_frame, text="⏱️ Runtime:",
                 style='Status.TLabel').pack()
        ttk.Label(runtime_frame, textvariable=self.runtime,
                 style='Status.TLabel').pack()
    
    def add_log_message(self, message, level="INFO"):
        """เพิ่มข้อความ log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        
        self.log_queue.put((formatted_message, level))
        self.log_messages.append((timestamp, level, message))
    
    def update_log_display(self):
        """อัพเดทการแสดงผล log"""
        try:
            while True:
                message, level = self.log_queue.get_nowait()
                
                # ตรวจสอบ filter
                if self.log_filter_var.get() != "ALL" and level != self.log_filter_var.get():
                    continue
                
                # เพิ่มข้อความลงใน text widget
                self.log_text.insert(tk.END, message, level)
                
                # Auto-scroll
                if self.auto_scroll_var.get():
                    self.log_text.see(tk.END)
                
                # จำกัดจำนวนบรรทัด (เก็บ 1000 บรรทัดล่าสุด)
                lines = int(self.log_text.index('end-1c').split('.')[0])
                if lines > 1000:
                    self.log_text.delete('1.0', '2.0')
                
        except queue.Empty:
            pass
        
        # อัพเดททุก 100ms
        self.root.after(100, self.update_log_display)

    def start_processing(self):
        """เริ่มการประมวลผล"""
        self.is_running = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.pause_button.config(state='normal')
        
        self.add_log_message("🚀 Starting PDF processing...", "INFO")
        self.status_label.config(text="🔄 Processing...")
        
        # เริ่มการประมวลผลใน thread แยก
        self.processing_thread = threading.Thread(target=self.process_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        # เริ่มการนับเวลา
        self.start_time = time.time()
        self.update_runtime()

    def stop_processing(self):
        """หยุดการประมวลผล"""
        self.is_running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.pause_button.config(state='disabled')
        
        self.add_log_message("⛔ Processing stopped by user", "WARNING")
        self.status_label.config(text="⏸️ Stopped")
    
    def pause_processing(self):
        """หยุดชั่วคราว"""
        if hasattr(self, 'is_paused'):
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.pause_button.config(text="▶️ Resume")
                self.add_log_message("⏸️ Processing paused", "WARNING")
                self.status_label.config(text="⏸️ Paused")
            else:
                self.pause_button.config(text="⏸️ Pause")
                self.add_log_message("▶️ Processing resumed", "INFO")
                self.status_label.config(text="🔄 Processing...")
        else:
            self.is_paused = True
            self.pause_processing()
    
    def process_loop(self):
        """ลูปการประมวลผล"""
        self.current_index = 0
        processed_count = 0
        success_count = 0
        
        self.add_log_message(f"🚀 เริ่มการประมวลผล {len(self.pdf_managers)} โฟลเดอร์", "INFO")
        
        while self.is_running:
            if hasattr(self, 'is_paused') and self.is_paused:
                time.sleep(1)
                continue

            if self.current_index >= len(self.pdf_managers):
                self.current_index = 0
                self.add_log_message(f"⏳ Cooldown for {self.cooldown_time} seconds...", "INFO")
                time.sleep(int(self.cooldown_var.get()))
                continue

            manager = self.pdf_managers[self.current_index]
            folder_name = os.path.basename(manager.root_directory)
            self.current_folder.set(folder_name)
            
            self.add_log_message(f"📂 Processing folder {self.current_index + 1}/{len(self.pdf_managers)}: {manager.root_directory}", "INFO")
            
            try:
                # ประมวลผลโฟลเดอร์
                result = manager.read_pdf_from_customer_directory()
                if result:
                    valid_docs, incomplete_docs, unreadable_docs, pending_docs = result
                    total_docs = len(valid_docs) + len(incomplete_docs) + len(unreadable_docs) + len(pending_docs)
                    processed_count += total_docs
                    success_count += len(valid_docs)
                    
                    self.add_log_message(f"✅ {folder_name}: {len(valid_docs)} valid, {len(incomplete_docs)} incomplete, {len(unreadable_docs)} unreadable, {len(pending_docs)} pending", "SUCCESS")
                    
                    # อัพเดทสถิติ
                    self.processed_count.set(str(processed_count))
                    if processed_count > 0:
                        success_rate = (success_count / processed_count) * 100
                        self.success_rate.set(f"{success_rate:.1f}%")
                else:
                    self.add_log_message(f"⚠️ {folder_name}: ไม่พบเอกสารหรือเกิดข้อผิดพลาด", "WARNING")
                
            except Exception as e:
                self.add_log_message(f"❌ Error processing folder {folder_name}: {str(e)}", "ERROR")

            self.current_index += 1
            
            # อัพเดท progress bar
            progress = (self.current_index / len(self.pdf_managers)) * 100
            self.progress_var.set(progress)
    
    def update_runtime(self):
        """อัพเดทเวลาทำงาน"""
        if self.is_running:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.runtime.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_runtime)
    
    def clear_log(self):
        """ล้าง log"""
        self.log_text.delete(1.0, tk.END)
        self.log_messages.clear()
        self.add_log_message("🗑️ Log cleared", "INFO")
    
    def save_log(self):
        """บันทึก log"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.add_log_message(f"💾 Log saved to: {filename}", "SUCCESS")
            except Exception as e:
                self.add_log_message(f"❌ Error saving log: {str(e)}", "ERROR")
    
    def toggle_auto_scroll(self):
        """สลับ auto-scroll"""
        self.auto_scroll_var.set(not self.auto_scroll_var.get())
        status = "enabled" if self.auto_scroll_var.get() else "disabled"
        self.add_log_message(f"🔄 Auto-scroll {status}", "INFO")
    
    def filter_log(self, event=None):
        """กรอง log"""
        self.log_text.delete(1.0, tk.END)
        filter_level = self.log_filter_var.get()
        
        for timestamp, level, message in self.log_messages:
            if filter_level == "ALL" or level == filter_level:
                formatted = f"[{timestamp}] {level}: {message}\n"
                self.log_text.insert(tk.END, formatted, level)
        
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
    
    def open_log_folder(self):
        """เปิดโฟลเดอร์ log"""
        try:
            import subprocess
            import platform
            
            log_folder = os.path.join(os.getcwd(), "logs")
            if not os.path.exists(log_folder):
                os.makedirs(log_folder)
            
            if platform.system() == "Windows":
                subprocess.run(["explorer", log_folder])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", log_folder])
            else:  # Linux
                subprocess.run(["xdg-open", log_folder])
                
            self.add_log_message(f"📁 Opened log folder: {log_folder}", "INFO")
        except Exception as e:
            self.add_log_message(f"❌ Error opening log folder: {str(e)}", "ERROR")
    
    def show_statistics(self):
        """แสดงสถิติ"""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("📊 Detailed Statistics")
        stats_window.geometry("600x400")
        
        # สร้างสถิติรายละเอียด
        stats_text = scrolledtext.ScrolledText(stats_window, font=('Consolas', 10))
        stats_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # ข้อมูลสถิติ
        stats_info = f"""
📊 DETAILED STATISTICS
{'='*50}

📄 Processing Information:
• Total Processed: {self.processed_count.get()}
• Success Rate: {self.success_rate.get()}
• Runtime: {self.runtime.get()}
• Current Folder: {self.current_folder.get()}

📋 Log Information:
• Total Log Messages: {len(self.log_messages)}
• Log Level: {self.log_level_var.get()}
• Auto-scroll: {'Enabled' if self.auto_scroll_var.get() else 'Disabled'}

⚙️ System Information:
• Python Version: {platform.python_version()}
• Platform: {platform.system()} {platform.release()}
• Working Directory: {os.getcwd()}

🔄 Processing Status:
• Running: {self.is_running}
• Paused: {getattr(self, 'is_paused', False)}
• Current Index: {self.current_index}
• Total Managers: {len(self.pdf_managers)}
        """
        
        stats_text.insert(1.0, stats_info)
        stats_text.config(state='disabled')
    
    def open_settings(self):
        """เปิดหน้าต่างตั้งค่า"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ Settings")
        settings_window.geometry("600x500")
        
        # สร้างการตั้งค่าต่างๆ
        settings_frame = ttk.Frame(settings_window, padding=20)
        settings_frame.pack(fill='both', expand=True)
        
        # Cooldown setting
        ttk.Label(settings_frame, text="Cooldown Time (seconds):").pack(anchor='w')
        cooldown_entry = ttk.Entry(settings_frame, textvariable=self.cooldown_var)
        cooldown_entry.pack(fill='x', pady=(0, 10))
        
        # Log level setting
        ttk.Label(settings_frame, text="Default Log Level:").pack(anchor='w')
        log_combo = ttk.Combobox(settings_frame, textvariable=self.log_level_var,
                                 values=["DEBUG", "INFO", "WARNING", "ERROR"])
        log_combo.pack(fill='x', pady=(0, 10))
        
        # Auto-scroll setting
        auto_scroll_check = ttk.Checkbutton(settings_frame, text="Enable Auto-scroll",
                                           variable=self.auto_scroll_var)
        auto_scroll_check.pack(anchor='w', pady=(0, 10))
        
        # LINE Configuration Section
        ttk.Separator(settings_frame, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(settings_frame, text="📱 LINE Messaging Configuration", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(10, 5))
        
        # LINE Channel Access Token
        ttk.Label(settings_frame, text="LINE Channel Access Token:").pack(anchor='w')
        self.line_token_var = tk.StringVar(value=getattr(self.line_bot, 'channel_access_token', '') if self.line_bot else '')
        line_token_entry = ttk.Entry(settings_frame, textvariable=self.line_token_var, show='*')
        line_token_entry.pack(fill='x', pady=(0, 10))
        
        # LINE User ID
        ttk.Label(settings_frame, text="LINE User ID:").pack(anchor='w')
        self.line_user_id_var = tk.StringVar(value=self.line_user_id or '')
        line_user_id_entry = ttk.Entry(settings_frame, textvariable=self.line_user_id_var)
        line_user_id_entry.pack(fill='x', pady=(0, 10))
        
        # LINE Enable/Disable
        self.line_enabled_var = tk.BooleanVar(value=self.line_bot is not None)
        line_enable_check = ttk.Checkbutton(settings_frame, text="Enable LINE Notifications",
                                           variable=self.line_enabled_var)
        line_enable_check.pack(anchor='w', pady=(0, 10))
        
        # Save button
        ttk.Button(settings_frame, text="💾 Save Settings",
                  command=lambda: self.save_settings(settings_window)).pack(pady=10)
    
    def save_settings(self, window):
        """บันทึกการตั้งค่า"""
        try:
            # บันทึกการตั้งค่าลงไฟล์
            settings = {
                'cooldown_time': int(self.cooldown_var.get()),
                'log_level': self.log_level_var.get(),
                'auto_scroll': self.auto_scroll_var.get(),
                'line_enabled': self.line_enabled_var.get(),
                'line_token': self.line_token_var.get(),
                'line_user_id': self.line_user_id_var.get()
            }
            
            with open('bot_settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
            
            # อัพเดท LINE bot configuration
            if self.line_enabled_var.get() and self.line_token_var.get():
                self.line_bot = LineMessagingBot(
                    channel_access_token=self.line_token_var.get(),
                    channel_secret=None
                )
                self.line_user_id = self.line_user_id_var.get()
                
                # อัพเดท LINE bot ใน PDF managers
                for manager in self.pdf_managers:
                    manager.line_bot = self.line_bot
                    manager.line_user_id = self.line_user_id
                
                self.add_log_message("✅ LINE messaging configured successfully", "SUCCESS")
            else:
                self.line_bot = None
                self.line_user_id = None
                
                # อัพเดท LINE bot ใน PDF managers
                for manager in self.pdf_managers:
                    manager.line_bot = None
                    manager.line_user_id = None
                
                self.add_log_message("⚠️ LINE messaging disabled", "WARNING")
            
            self.add_log_message("💾 Settings saved successfully", "SUCCESS")
            window.destroy()
        except Exception as e:
            self.add_log_message(f"❌ Error saving settings: {str(e)}", "ERROR")

# เพิ่ม import ที่จำเป็น


    
# ✅ ตรวจสอบโฟลเดอร์หลักที่มีอยู่จริง
root_directories = [
    "V:/A.โฟร์เดอร์หลัก/",
    "V:/AA.โฟรเดอร์หลัก/",
    "V:/AAA.โฟรเดอร์หลัก/"
]

print("🔍 ตรวจสอบโฟลเดอร์หลัก:")
for directory in root_directories:
    exists = os.path.exists(directory)
    print(f"   {directory}: {'✅ มีอยู่' if exists else '❌ ไม่มีอยู่'}")

existing_directories = [d for d in root_directories if os.path.exists(d)]

if not existing_directories:
    print("❌ ไม่มีโฟลเดอร์ที่ถูกต้อง กรุณาตรวจสอบเส้นทาง")
    print("📂 โฟลเดอร์ที่ตรวจสอบ:")
    for directory in root_directories:
        print(f"   - {directory}")
    
    # ตรวจสอบโฟลเดอร์ทั้งหมดในไดรฟ์ V
    v_drive = "V:/"
    if os.path.exists(v_drive):
        print("\n📂 โฟลเดอร์ทั้งหมดในไดรฟ์ V:")
        try:
            for item in os.listdir(v_drive):
                if os.path.isdir(os.path.join(v_drive, item)):
                    print(f"   - {item}")
        except Exception as e:
            print(f"❌ ไม่สามารถอ่านไดรฟ์ V: {e}")
    
    raise ValueError("❌ ไม่มีโฟลเดอร์ที่ถูกต้อง กรุณาตรวจสอบเส้นทาง")

# ✅ สร้างหน้าต่างหลัก
root = tk.Tk()
root.title("📂 ระบบประมวลผล PDF อัตโนมัติ")

# ✅ สร้าง LINE bot (ถ้ามีการตั้งค่า)
line_bot = None
line_user_id = None

# ✅ อ่านการตั้งค่าจากไฟล์ (ถ้ามี)
try:
    with open('bot_settings.json', 'r') as f:
        settings = json.load(f)
        if settings.get('line_enabled', False) and settings.get('line_token'):
            line_bot = LineMessagingBot(
                channel_access_token=settings['line_token'],
                channel_secret=None
            )
            line_user_id = settings.get('line_user_id', '')
            print("✅ LINE messaging loaded from settings")
except FileNotFoundError:
    print("⚠️ No settings file found, using default configuration")
except Exception as e:
    print(f"⚠️ Error loading settings: {e}")

# ✅ สร้าง AdvancedUIManager ก่อน (โดยไม่มี pdf_managers)
ui_manager = AdvancedUIManager(root, [], cooldown_time=15, line_bot=line_bot, line_user_id=line_user_id)

# ✅ สร้าง instance PDF_Folder_Directory สำหรับแต่ละโฟลเดอร์หลัก และส่ง ui_manager ไปด้วย
pdf_managers = []
for path in existing_directories:
    try:
        manager = PDF_Folder_Directory(file_path=path, ui_manager=ui_manager, line_bot=line_bot, line_user_id=line_user_id)
        pdf_managers.append(manager)
        print(f"✅ สร้าง manager สำหรับ: {path}")
    except Exception as e:
        print(f"❌ ไม่สามารถสร้าง manager สำหรับ {path}: {e}")

# ✅ อัพเดท ui_manager ด้วย pdf_managers ที่สร้างเสร็จแล้ว
ui_manager.pdf_managers = pdf_managers

print(f"✅ สร้าง PDF managers สำเร็จ: {len(pdf_managers)} managers")

# ✅ แสดงข้อมูลโฟลเดอร์ที่พบ
print(f"\n📂 พบโฟลเดอร์หลัก {len(existing_directories)} โฟลเดอร์:")
for i, directory in enumerate(existing_directories, 1):
    print(f"   {i}. {directory}")

print(f"\n🚀 ระบบจะประมวลผลโฟลเดอร์ทั้งหมด {len(existing_directories)} โฟลเดอร์")
print("=" * 50)

# ✅ ตรวจสอบการตั้งค่าสุดท้าย
print(f"\n⚙️ การตั้งค่าสุดท้าย:")
print(f"   - จำนวน PDF managers: {len(pdf_managers)}")
print(f"   - LINE bot: {'✅ เปิดใช้งาน' if line_bot else '❌ ปิดใช้งาน'}")
print(f"   - UI Manager: {'✅ พร้อมใช้งาน' if ui_manager else '❌ ไม่พร้อมใช้งาน'}")

# ✅ เริ่มต้นระบบ
print("\n🎯 เริ่มต้นระบบ...")
root.mainloop()
