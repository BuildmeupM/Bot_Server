from playwright.sync_api import sync_playwright, Page, Browser
import time
import os
import re
from typing import Dict, Optional
from pathlib import Path
from config import Config
from report_manager import get_global_report_manager, line_notify, line_oa_push
from file_manager import FileManager

class WebAutomationPlaywright:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.is_logged_in = False
        self.credentials = {}
        self.company_link = ""
        self.express_link = ""
        self.file_manager = FileManager()  # สร้าง FileManager instance
        self.latest_iptnumber_text = None  # เก็บค่า iptnumber ล่าสุดที่อ่านได้ระหว่างกรอกฟอร์ม
        self.latest_created_file_path = None  # เก็บพาธไฟล์ที่สร้างล่าสุด เพื่อนำไปย้ายเมื่อพบแจ้งเตือนเอกสารซ้ำ
        self._current_pdf_data_for_retry = None  # เก็บ pdf_data ปัจจุบันเพื่อใช้กรอกใหม่เมื่อมีแจ้งเตือนบังคับกรอก
        self._refill_attempt_count = 0  # นับจำนวนครั้งที่กรอกใหม่จากแจ้งเตือนเพื่อกันวนไม่สิ้นสุด
        
    def read_config_from_txt(self, txt_file_path: str) -> bool:
        """อ่านข้อมูลการตั้งค่าจากไฟล์ Build000.txt"""
        try:
            print(f"📖 กำลังอ่านข้อมูลการตั้งค่าจาก: {txt_file_path}")
            
            with open(txt_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # แยกข้อมูลตามบรรทัด
            lines = content.strip().split('\n')
            print(f"🔍 เนื้อหาที่อ่านได้ ({len(lines)} บรรทัด):")
            for i, line in enumerate(lines):
                print(f"   บรรทัด {i+1}: '{line}'")
            
            for line in lines:
                line = line.strip()
                print(f"🔍 ตรวจสอบบรรทัด: '{line}'")
                
                if line.startswith('Username :'):
                    username = line.split(':', 1)[-1].strip()
                    self.credentials['Username'] = username
                    print(f"✅ อ่าน Username: {username}")
                    
                elif line.startswith('Password :'):
                    password = line.split(':', 1)[-1].strip()
                    self.credentials['Password'] = password
                    print(f"✅ อ่าน Password: {password}")
                    
                elif line.startswith('Link company :'):
                    company_link = line.split(':', 1)[-1].strip()
                    self.company_link = company_link
                    print(f"✅ อ่าน Company Link: {company_link}")
                    
                elif line.startswith('Link Express :'):
                    express_link = line.split(':', 1)[-1].strip()
                    self.express_link = express_link
                    print(f"✅ อ่าน Express Link: {express_link}")
                else:
                    print(f"⚠️ ไม่ตรงกับรูปแบบที่กำหนด: '{line}'")
            
            # แสดงข้อมูลที่อ่านได้
            print(f"📊 สรุปข้อมูลที่อ่านได้:")
            print(f"   Username: '{self.credentials.get('Username', 'ไม่พบ')}'")
            print(f"   Password: '{self.credentials.get('Password', 'ไม่พบ')}'")
            print(f"   Company Link: '{self.company_link}'")
            print(f"   Express Link: '{self.express_link}'")
            
            # ตรวจสอบว่าอ่านข้อมูลครบหรือไม่
            if (self.credentials.get('Username') and 
                self.credentials.get('Password') and 
                self.company_link and 
                self.express_link):
                print(f"✅ อ่านข้อมูลการตั้งค่าเสร็จสิ้น")
                return True
            else:
                print(f"❌ อ่านข้อมูลการตั้งค่าไม่ครบ")
                return False
                
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์การตั้งค่า: {e}")
            return False
        
    def setup_driver(self):
        """ตั้งค่า Playwright Browser"""
        try:
            self.playwright = sync_playwright().start()
            
            # เลือก browser (chromium, firefox, webkit)
            self.browser = self.playwright.chromium.launch(
                headless=False,  # แสดงหน้าต่าง browser
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--start-maximized',  # เปิดเต็มจอตั้งแต่แรก
                    '--window-size=1920,1080'
                ]
            )
            
            # สร้าง page ใหม่
            self.page = self.browser.new_page()
            
            # ตั้งค่า viewport ให้เต็มจอ
            self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            # ตั้งค่า timeout
            self.page.set_default_timeout(Config.SELENIUM_TIMEOUT * 1000)  # แปลงเป็น milliseconds
            
            print("Playwright setup completed successfully")
            return True
            
        except Exception as e:
            print(f"Error setting up Playwright: {e}")
            return False
    
    def login_to_peak_engine(self, credentials: Dict) -> bool:
        """ล็อกอินเข้า Peak Engine และคลิกปุ่มกลับไปยัง Peak เก่า"""
        try:
            if not self.page:
                print("Playwright page not initialized")
                return False
            
            # ไปยังหน้า login
            self.page.goto(Config.PEAK_ENGINE_URL)
            print(f"Navigating to: {Config.PEAK_ENGINE_URL}")
            
            # รอให้หน้าโหลดเสร็จ
            
            
            # หาและกรอก username
            username_field = self.page.locator('input[name="username"]')
            username_field.fill(credentials.get('Username', ''))
            
            # หาและกรอก password
            password_field = self.page.locator('input[name="password"]')
            password_field.fill(credentials.get('Password', ''))
            
            # กดปุ่ม login
            login_button = self.page.locator('button[type="submit"]')
            login_button.click()
            
            # รอให้ล็อกอินสำเร็จ
            
            time.sleep(0.5)
            
            # ตรวจสอบว่าล็อกอินสำเร็จหรือไม่
            current_url = self.page.url
            if "login" not in current_url.lower():
                self.is_logged_in = True
                print("Login successful")
                
                # หลังจากล็อกอินสำเร็จ ให้คลิกปุ่ม "กลับไปยัง Peak เก่าสำเร็จ")
                print(f"🔄 กำลังคลิกปุ่มกลับไปยัง Peak เก่าสำเร็จ")
                try:
                    # รอให้ปุ่มปรากฏ
                    self.page.wait_for_selector('#btnBackToOldPeak', timeout=10000)
                    
                    # คลิกปุ่มด้วยวิธีที่ถูกต้อง
                    back_button = self.page.locator('#btnBackToOldPeak')
                    if back_button.count() > 0:
                        # รอให้ปุ่มพร้อมใช้งาน
                        back_button.first.wait_for(state='visible')
                        
                        # คลิกปุ่ม
                        back_button.first.click()
                        print(f"✅ คลิกปุ่มกลับไปยัง Peak เก่าสำเร็จ")
                        
                        # รอให้หน้าโหลดเสร็จ
                        
                        
                        
                        # ตรวจสอบ URL หลังคลิกปุ่ม
                        current_url = self.page.url
                        print(f"📍 URL หลังคลิกปุ่มกลับ: {current_url}")
                        
                    else:
                        print(f"⚠️ ไม่พบปุ่มกลับไปยัง Peak เก่า")
                        
                except Exception as e:
                    print(f"⚠️ เกิดข้อผิดพลาดในการคลิกปุ่มกลับ: {e}")
                    # ลองใช้วิธีอื่น
                    try:
                        print(f"🔍 ลองใช้วิธีอื่นในการคลิกปุ่ม...")
                        self.page.click('#btnBackToOldPeak')
                        print(f"✅ คลิกปุ่มสำเร็จด้วยวิธีอื่น")
                        
                        # รอให้หน้าโหลดเสร็จ
                        
                        
                        
                        # ตรวจสอบ URL หลังคลิกปุ่ม
                        current_url = self.page.url
                        print(f"📍 URL หลังคลิกปุ่มกลับ: {current_url}")
                        
                    except Exception as e2:
                        print(f"❌ ไม่สามารถคลิกปุ่มได้ด้วยวิธีใดเลย: {e2}")
                
                return True
            else:
                print("Login failed - still on login page")
                return False
                
        except Exception as e:
            print(f"Error during login: {e}")
            return False
    
    def navigate_to_company_link(self, company_link: str) -> bool:
        """ไปยัง Link Company"""
        try:
            if not self.is_logged_in:
                print("Not logged in")
                return False
            
            print(f"Navigating to company link: {company_link}")
            self.page.goto(company_link)
            
            
            return True
            
        except Exception as e:
            print(f"Error navigating to company link: {e}")
            return False
    
    def navigate_to_express_link(self, express_link: str) -> bool:
        """ไปยัง Link Express"""
        try:
            if not self.is_logged_in:
                print("Not logged in")
                return False
            
            print(f"Navigating to express link: {express_link}")
            self.page.goto(express_link)
            
            
            return True
            
        except Exception as e:
            print(f"Error navigating to express link: {e}")
            return False
    
    def fill_form_data(self, pdf_data: Dict) -> bool:
        """กรอกข้อมูลในฟอร์มด้วยข้อมูลจาก PDF"""
        try:
            if not self.is_logged_in:
                print("Not logged in")
                return False
            
            print(f"📝 กรอกข้อมูลในฟอร์ม: {pdf_data.get('filename', 'ไม่ทราบชื่อ')}")
            print(f"📊 ข้อมูลที่จะกรอก:")
            print(f"   Company: {pdf_data.get('company_name', '')}")
            print(f"   Group: {pdf_data.get('group', 'unknown')}")
            print(f"   Service name: {pdf_data.get('service_name', '')}")
            print(f"   Customer ID: {pdf_data.get('customer_id', '')}")
            print(f"   Account Code: {pdf_data.get('account_code', '')}")
            print(f"   เลขที่เอกสาร: {pdf_data.get('document_number', '')}")
            print(f"   วันที่เอกสาร: {pdf_data.get('document_date', '')}")
            print(f"   ยอดก่อนภาษีมูลค่าเพิ่ม: {pdf_data.get('total_ex_vat', '')}")
            print(f"   ยอดก่อนภาษีมูลค่าเพิ่ม (NoneVat): {pdf_data.get('total_ex_vat_none', '')}")
            print(f"   ยอดภาษีมูลค่าเพิ่ม: {pdf_data.get('vat_value', '')}")
            print(f"   ยอดหลังบวกภาษีมูลค่าเพิ่ม: {pdf_data.get('total_in_vat', '')}")
            
            # รอให้ฟอร์มโหลดเสร็จ
            time.sleep(0.5)
            
            # กรอกข้อมูลในฟอร์มตามข้อมูลจาก PDF
            try:
                # 1. กรอก Customer ID - //*[@id="iptcontactname"] >> เลื่อน Arrow down >> enter
                print(f"🔍 กำลังกรอก Customer ID...")
                try:
                    customer_field = self.page.locator('//*[@id="iptcontactname"]')
                    if customer_field.count() > 0:
                        customer_field.first.fill(pdf_data.get('customer_id', ''))
                        print(f"✅ กรอก Customer ID: {pdf_data.get('customer_id', '')}")
                    
                    # รอให้ดรอปดาวน์ปรากฏ
                    print(f"⏳ รอให้ดรอปดาวน์ปรากฏ...")
                    time.sleep(1)
                    
                    # ลองหาตัวเลือกรายการที่ตรงกับ Customer ID
                    customer_id = pdf_data.get('customer_id', '')
                    print(f"🔍 กำลังหาตัวเลือกที่มี '{customer_id}'...")
                    
                    # วิธีที่ 1: หาด้วย text content ที่มี Customer ID
                    customer_option = self.page.locator(f'text={customer_id}')
                    if customer_option.count() > 0:
                        print(f"✅ พบตัวเลือกที่มี '{customer_id}'")
                        customer_option.first.click()
                        print(f"✅ คลิกตัวเลือกสำเร็จ")
                    else:
                        # วิธีที่ 2: กดลง 1 ครั้งเพื่อเลือกรายการที่ 2 (ข้าม "+ เพิ่มผู้ติดต่อ")
                        print(f"🔽 ลองใช้วิธีกดลง 1 ครั้ง...")
                        customer_field.first.press('ArrowDown')
                        time.sleep(0.5)
                        
                        # ตรวจสอบว่าตัวเลือกที่เลือกถูกต้องหรือไม่
                        try:
                            selected_text = customer_field.first.input_value()
                            print(f"📋 ตัวเลือกที่เลือก: '{selected_text}'")
                            
                            if customer_id in str(selected_text):
                                print(f"✅ เลือกรายการที่ถูกต้อง: {selected_text}")
                            else:
                                # วิธีที่ 3: กดลงอีก 1 ครั้ง (รวมเป็น 2 ครั้ง)
                                print(f"🔽 กดลงครั้งที่ 2...")
                                customer_field.first.press('ArrowDown')
                                time.sleep(0.5)
                                
                                # ตรวจสอบอีกครั้ง
                                selected_text_2 = customer_field.first.input_value()
                                print(f"📋 ตัวเลือกหลังกดลง 2 ครั้ง: '{selected_text_2}'")
                                
                                if customer_id in str(selected_text_2):
                                    print(f"✅ เลือกรายการที่ถูกต้องหลังกดลง 2 ครั้ง: {selected_text_2}")
                                else:
                                    print(f"⚠️ ไม่สามารถเลือกรายการที่ถูกต้องได้")
                        except Exception as e:
                            print(f"⚠️ ไม่สามารถตรวจสอบตัวเลือกที่เลือกได้: {e}")
                    
                        # กด Enter เพื่อยืนยันการเลือก
                        print(f"⏎ กด Enter เพื่อยืนยัน...")
                        customer_field.first.press('Enter')
                        time.sleep(0.5)
                        print(f"✅ กด Enter สำเร็จ")
                except Exception as e:
                    print(f"⚠️ เกิดข้อผิดพลาดในการกรอก Customer ID: {e}")
                    # ลองใช้วิธี fallback
                    try:
                        customer_field = self.page.locator('#iptcontactname')
                        if customer_field.count() > 0:
                            customer_field.first.fill(pdf_data.get('customer_id', ''))
                            customer_field.first.press("ArrowDown")
                            time.sleep(0.5)
                            customer_field.first.press("Enter")
                            print(f"✅ ใช้วิธี fallback สำเร็จ")
                    except Exception as e2:
                        print(f"❌ ไม่สามารถกรอก Customer ID ได้: {e2}")
                        return False
                    
                # รอ 1 วินาทีหลังกรอก Customer ID
                print(f"⏳ รอ 1 วินาทีหลังกรอก Customer ID...")
                time.sleep(0.5)
                
                # ตรวจสอบที่อยู่ //*[@id="lbcontactaddress"] ต้องไม่เป็น "-"
                print(f"🔍 ตรวจสอบที่อยู่...")
                address_field = self.page.locator('//*[@id="lbcontactaddress"]')
                if address_field.count() > 0:
                    address_text = address_field.first.text_content()
                    print(f"📍 ที่อยู่ปัจจุบัน: '{address_text}'")
                    
                    if address_text and address_text.strip() != "-" and address_text.strip() != "":
                        print(f"✅ ที่อยู่ถูกต้อง: {address_text}")
                    else:
                        print(f"⚠️ ที่อยู่ยังไม่ถูกต้อง (เป็น '-' หรือว่างเปล่า)")
                        # รอเพิ่มเติมให้ที่อยู่โหลดเสร็จ
                        print(f"⏳ รอให้ที่อยู่โหลดเสร็จ...")
                        time.sleep(1)
                        
                        # ตรวจสอบอีกครั้ง
                        address_text_retry = address_field.first.text_content()
                        print(f"📍 ที่อยู่หลังรอ: '{address_text_retry}'")
                        
                        if address_text_retry and address_text_retry.strip() != "-" and address_text_retry.strip() != "":
                            print(f"✅ ที่อยู่ถูกต้องหลังรอ: {address_text_retry}")
                        else:
                            print(f"❌ ที่อยู่ยังไม่ถูกต้อง แม้จะรอแล้ว")
                else:
                    print(f"⚠️ ไม่พบฟิลด์ที่อยู่ (lbcontactaddress)")
                
                # 2. กรอก Account Code - //*[@id="iptaccountcode1"] >> enter
                print(f"🔍 กำลังกรอก Account Code...")
                try:
                    account_field = self.page.locator('//*[@id="iptaccountcode1"]')
                    if account_field.count() > 0:
                        account_field.first.fill(pdf_data.get('account_code', ''))
                        print(f"✅ กรอก Account Code: {pdf_data.get('account_code', '')}")
                        account_field.first.press('Enter')
                        print(f"✅ กด Enter สำเร็จ")
                    else:
                        print(f"⚠️ ไม่พบฟิลด์ Account Code (iptaccountcode1)")
                except Exception as e:
                    print(f"⚠️ เกิดข้อผิดพลาดในการกรอก Account Code: {e}")
                
                # 3. กรอกวันที่เอกสาร - //*[@id="iptdate"] (ย้ายขึ้นมาก่อน)
                print(f"🔍 กำลังกรอกวันที่เอกสาร...")
                try:
                    date_field = self.page.locator('//*[@id="iptdate"]')
                    if date_field.count() > 0:
                        date_field.first.fill(pdf_data.get('document_date', ''))
                        print(f"✅ กรอกวันที่เอกสาร: {pdf_data.get('document_date', '')}")
                        # ถ้าวันที่ยังว่าง ให้กรอก Customer ID ใหม่ทันที (ไม่ต้องรอ)
                        try:
                            current_date_val = date_field.first.input_value()
                        except Exception:
                            current_date_val = ''
                        if not current_date_val:
                            print("⚠️ ไม่พบค่าวันที่หลังกรอก จะกรอก Customer ID ใหม่ทันที...")
                            self.fill_customer_id_again(pdf_data)
                    else:
                        print(f"⚠️ ไม่พบฟิลด์วันที่เอกสาร (iptdate)")
                except Exception as e:
                    print(f"⚠️ เกิดข้อผิดพลาดในการกรอกวันที่เอกสาร: {e}")
                
                # 4. กรอกเลขที่เอกสาร (เฉพาะบริษัท VAT เท่านั้น)
                try:
                    company_name = pdf_data.get('company_name', '')
                    company_vat_status = Config.COMPANY_VAT_STATUS.get(company_name, 'VAT')
                    folder_group = pdf_data.get('group') or 'unknown'
                    
                    print(f"🔍 ตรวจสอบเงื่อนไข: folder_group='{folder_group}', company_vat_status='{company_vat_status}'")
                    
                    # ตรวจสอบจาก folder_group ก่อน (special = NoneVat, regular = VAT)
                    if folder_group == 'special':
                        print(f"ℹ️ โฟลเดอร์ special (NoneVat): ข้ามขั้นตอนกรอกเลขที่เอกสาร")
                        skip_invoice = True
                    elif company_vat_status == 'NoneVat':
                        print(f"ℹ️ บริษัท {company_name}: ทำงานแบบ NoneVat - ข้ามขั้นตอนกรอกเลขที่เอกสาร")
                        skip_invoice = True
                    else:
                        print(f"ℹ️ บริษัท {company_name}: ทำงานแบบ VAT - กรอกเลขที่เอกสาร")
                        skip_invoice = False
                except Exception as e:
                    print(f"⚠️ เกิดข้อผิดพลาดในการตรวจสอบเงื่อนไข: {e}")
                    skip_invoice = False
                
                # 5. กรอกเลขที่เอกสาร (เฉพาะบริษัท VAT เท่านั้น)
                if not skip_invoice:
                    print(f"🔍 กำลังกรอกเลขที่เอกสาร...")
                    try:
                        invoice_button = self.page.locator('//*[@id="receivedTaxInvoiceAddButton"]')
                        if invoice_button.count() > 0:
                            invoice_button.first.click()
                            print(f"✅ คลิกปุ่ม receivedTaxInvoiceAddButton สำเร็จ")
                            
                            # รอป๊อปอัป
                            time.sleep(1)
                            
                            # กรอกเลขที่เอกสารในป๊อปอัป
                            invoice_input = self.page.locator('//*[@id="inputModalReceivedTaxInvoiceNumber"]')
                            if invoice_input.count() > 0:
                                invoice_input.first.fill(pdf_data.get('document_number', ''))
                                print(f"✅ กรอกเลขที่เอกสาร: {pdf_data.get('document_number', '')}")
                                
                                # คลิกปุ่มในป๊อปอัป
                                popup_button = self.page.locator('//*[@id="receivedTaxInvoiceAddModalSize"]/div/div[3]/div[2]')
                                if popup_button.count() > 0:
                                    popup_button.first.click()
                                    print(f"✅ คลิกปุ่มในป๊อปอัปสำเร็จ")
                                else:
                                    print(f"⚠️ ไม่พบปุ่มในป๊อปอัป")
                            else:
                                print(f"⚠️ ไม่พบฟิลด์เลขที่เอกสารในป๊อปอัป")
                        else:
                            print(f"⚠️ ไม่พบปุ่ม receivedTaxInvoiceAddButton")
                    except Exception as e:
                        print(f"⚠️ เกิดข้อผิดพลาดในการกรอกเลขที่เอกสาร: {e}")
                else:
                    print(f"⏭️ ข้ามการกรอกเลขที่เอกสาร (NoneVat)")
                
                # 5. กรอกยอดหลังบวกภาษีมูลค่าเพิ่ม - //*[@id="iptprice1"]
                print(f"🔍 กำลังกรอกยอดหลังบวกภาษีมูลค่าเพิ่ม...")
                price_field = self.page.locator('//*[@id="iptprice1"]')
                if price_field.count() > 0:
                    price_field.first.fill(str(pdf_data.get('total_in_vat', '')))
                    print(f"✅ กรอกยอดหลังบวกภาษีมูลค่าเพิ่ม: {pdf_data.get('total_in_vat', '')}")
                else:
                    print(f"⚠️ ไม่พบฟิลด์ยอดหลังบวกภาษีมูลค่าเพิ่ม (iptprice1)")
                
                # 6. เลือกดรอปดาวน์ภาษี (แตกต่างกันตาม folder_group และ company_vat_status)
                # ใช้ตัวแปรที่คำนวณไว้ด้านบน (company_vat_status, folder_group)
                # ให้ความสำคัญกับ folder_group ก่อน
                if folder_group == 'special' or company_vat_status == 'NoneVat':
                    # สำหรับ NoneVat: เลือก "ไม่มี" (value="1") ใน ddlvattypeid1
                    print(f"🔍 [NoneVat] กำลังเลือกดรอปดาวน์ประเภทภาษี (ddlvattypeid1) เป็น 'ไม่มี'...")
                    vat_type_dropdown = self.page.locator('//*[@id="ddlvattypeid1"]')
                    if vat_type_dropdown.count() > 0:
                        # วิธีที่ 1: เลือกด้วย value="1"
                        try:
                            self.page.select_option('//*[@id="ddlvattypeid1"]', value='1')
                            print(f"✅ เลือก 'ไม่มี' สำเร็จด้วยวิธีที่ 1 (value='1')")
                        except:
                            # วิธีที่ 2: ใช้ JavaScript
                            try:
                                self.page.evaluate("""
                                    const dropdown = document.querySelector('#ddlvattypeid1');
                                    if (dropdown) {
                                        dropdown.value = '1';
                                        dropdown.dispatchEvent(new Event('change', {bubbles: true}));
                                    }
                                """)
                                print(f"✅ เลือก 'ไม่มี' สำเร็จด้วยวิธีที่ 2 (JavaScript)")
                            except:
                                # วิธีที่ 3: คลิกแล้วเลือกด้วย text
                                try:
                                    vat_type_dropdown.first.click()
                                    time.sleep(0.5)
                                    no_vat_option = self.page.locator('text=ไม่มี')
                                    if no_vat_option.count() > 0:
                                        no_vat_option.first.click()
                                        print(f"✅ เลือก 'ไม่มี' สำเร็จด้วยวิธีที่ 3 (text)")
                                    else:
                                        # วิธีที่ 4: เลือกด้วย index
                                        self.page.select_option('//*[@id="ddlvattypeid1"]', index=1)
                                        print(f"✅ เลือก 'ไม่มี' สำเร็จด้วยวิธีที่ 4 (index=1)")
                                except Exception as e:
                                    print(f"⚠️ ไม่สามารถเลือก 'ไม่มี' ได้: {e}")
                    else:
                        print(f"⚠️ ไม่พบดรอปดาวน์ประเภทภาษี (ddlvattypeid1)")
                    
                    # ตรวจสอบว่าการเลือกสำเร็จหรือไม่ (สำหรับ NoneVat)
                    try:
                        selected_value = vat_type_dropdown.first.input_value()
                        print(f"📋 ค่าประเภทภาษีที่เลือกได้: '{selected_value}'")
                        if selected_value == '1':
                            print(f"✅ เลือก 'ไม่มี' สำเร็จ!")
                        else:
                            print(f"⚠️ ค่าที่เลือกไม่ตรงกับที่ต้องการ: '{selected_value}'")
                    except Exception as e:
                        print(f"📋 ไม่สามารถอ่านค่าที่เลือกได้: {e}")

                else:
                    # สำหรับ VAT: เลือก "รวมภาษี" ใน ddltaxstatus
                    print(f"🔍 [VAT] กำลังเลือกดรอปดาวน์รวมภาษี (ddltaxstatus)...")
                    tax_status_dropdown = self.page.locator('//*[@id="ddltaxstatus"]')
                    if tax_status_dropdown.count() > 0:
                        # คลิกดรอปดาวน์เพื่อเปิดตัวเลือก
                        tax_status_dropdown.first.click()
                        print(f"✅ เปิดดรอปดาวน์รวมภาษีสำเร็จ")
                        
                        # รอให้ดรอปดาวน์เปิดและรายการปรากฏ
                        print(f"⏳ รอให้รายการดรอปดาวน์ปรากฏ...")
                        time.sleep(1)  # รอให้ดรอปดาวน์เปิดสมบูรณ์
                        
                        # ลองหาตัวเลือก "รวมภาษี" ด้วยหลายวิธี
                        tax_included_option = None
                        
                        # วิธีที่ 1: หาด้วย text content
                        tax_included_option = self.page.locator('text=รวมภาษี, text=Include Tax')
                        if tax_included_option.count() > 0:
                            tax_included_option.first.click()
                            print(f"✅ เลือกรวมภาษีสำเร็จด้วยวิธีที่ 1")
                        else:
                            # วิธีที่ 2: เลือกด้วย index
                            try:
                                self.page.select_option('//*[@id="ddltaxstatus"]', index=1)
                                print(f"✅ เลือกรวมภาษีสำเร็จด้วยวิธีที่ 2 (index=1)")
                            except:
                                # วิธีที่ 3: ใช้ JavaScript
                                try:
                                    self.page.evaluate("""
                                        const dropdown = document.querySelector('#ddltaxstatus');
                                        if (dropdown) {
                                            for (let i = 0; i < dropdown.options.length; i++) {
                                                if (dropdown.options[i].text.includes('รวมภาษี') || 
                                                    dropdown.options[i].text.includes('Include Tax')) {
                                                    dropdown.selectedIndex = i;
                                                    dropdown.dispatchEvent(new Event('change'));
                                                    break;
                                                }
                                            }
                                        }
                                    """)
                                    print(f"✅ เลือกรวมภาษีสำเร็จด้วยวิธีที่ 3 (JavaScript)")
                                except:
                                    # วิธีที่ 4: กดลง 2 ครั้ง แล้วกด Enter
                                    print(f"🔽 ลองใช้วิธีกดลง 2 ครั้ง...")
                                    tax_status_dropdown.first.press('ArrowDown')
                                    time.sleep(0.3)
                                    
                                    print(f"🔽 กดลงครั้งที่ 2...")
                                    tax_status_dropdown.first.press('ArrowDown')
                                    time.sleep(0.3)
                                    
                                    print(f"⏎ กด Enter...")
                                    tax_status_dropdown.first.press('Enter')
                                    time.sleep(0.3)
                                    
                                    print(f"✅ เลือกรวมภาษีสำเร็จด้วยวิธีที่ 4 (กดลง 2 ครั้ง + Enter)")
                    else:
                        print(f"⚠️ ไม่พบดรอปดาวน์รวมภาษี (ddltaxstatus)")
                        

                
                # 6.1 อ่านเลขเอกสารจาก iptnumber ล่วงหน้า ก่อนคลิกปุ่มสุดท้าย
                try:
                    ipt_loc = self.page.locator('//*[@id="iptnumber"]')
                    if ipt_loc.count() > 0:
                        try:
                            txt = (ipt_loc.first.input_value() or '').strip()
                        except Exception:
                            txt = (ipt_loc.first.text_content() or '').strip()
                        self.latest_iptnumber_text = txt if txt else None
                        print(f"📄 บันทึก iptnumber ล่วงหน้า: '{self.latest_iptnumber_text or ''}'")
                    else:
                        print("⚠️ ไม่พบ element iptnumber สำหรับบันทึกล่วงหน้า")
                except Exception as _:
                    print("⚠️ อ่าน iptnumber ล่วงหน้าไม่สำเร็จ")
                except Exception as e:
                    print(f"⚠️ เกิดข้อผิดพลาดในการกรอกเลขที่เอกสาร: {e}")

                # 7. คลิกปุ่ม hidePaymentModal - //*[@id="hidePaymentModal"]
                print(f"🔍 กำลังคลิกปุ่ม hidePaymentModal...")
                try:
                    hide_payment_button = self.page.locator('//*[@id="hidePaymentModal"]')
                    if hide_payment_button.count() > 0:
                        hide_payment_button.first.click()
                        print(f"✅ คลิกปุ่ม hidePaymentModal สำเร็จ")
                    else:
                        print(f"⚠️ ไม่พบปุ่ม hidePaymentModal")
                except Exception as e:
                    print(f"⚠️ เกิดข้อผิดพลาดในการคลิกปุ่ม hidePaymentModal: {e}")
                
                # 8. คลิกปุ่มสุดท้าย - //*[@id="content"]/div[6]/div[6]/div/div[2]/div[2]/div[1]
                print(f"🔍 กำลังกดปุ่มสุดท้าย...")
                try:
                    final_button = self.page.locator('//*[@id="content"]/div[6]/div[6]/div/div[2]/div[2]/div[1]')
                    if final_button.count() > 0:
                        final_button.first.click()
                        print(f"✅ คลิกปุ่มสุดท้ายสำเร็จ")
                    else:
                        print(f"⚠️ ไม่พบปุ่มสุดท้าย")
                except Exception as e:
                    print(f"⚠️ เกิดข้อผิดพลาดในการคลิกปุ่มสุดท้าย: {e}")

                print(f"✅ กรอกข้อมูลในฟอร์มสำเร็จ!")
                return True
                
            except Exception as e:
                print(f"⚠️ เกิดข้อผิดพลาดในการกรอกฟิลด์เฉพาะ: {e}")
                print(f"🔍 ลองใช้วิธีกรอกฟอร์มทั่วไป...")
                # ถ้ากรอกฟิลด์เฉพาะไม่ได้ ให้ลองกรอกฟอร์มทั่วไป
                try:
                    return self.fill_form_generic(pdf_data)
                except Exception as e2:
                    print(f"❌ เกิดข้อผิดพลาดในการกรอกฟอร์มทั่วไป: {e2}")
                    return False
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการกรอกข้อมูล: {e}")
            return False
    
    def fill_form_generic(self, pdf_data: Dict) -> bool:
        """กรอกฟอร์มแบบทั่วไป (fallback)"""
        try:
            print(f"🔍 ใช้วิธีกรอกฟอร์มทั่วไป...")
            
            # หา input fields ทั้งหมด
            input_fields = self.page.locator('input[type="text"], input[type="number"], textarea')
            print(f"📊 พบ input fields: {input_fields.count()} ฟิลด์")
            
            # กรอกข้อมูลตามลำดับจาก PDF (ตรงกับ pdf_reader.py)
            data_to_fill = [
                pdf_data.get('customer_id', ''),         # Customer ID
                pdf_data.get('account_code', ''),        # Account Code
                pdf_data.get('account_code2', ''),       # Account Code2
                pdf_data.get('document_number', ''),     # เลขที่เอกสาร
                pdf_data.get('document_date', ''),       # วันที่เอกสาร
                str(pdf_data.get('total_ex_vat', '')),   # ยอดก่อนภาษีมูลค่าเพิ่ม
                str(pdf_data.get('total_ex_vat_none', '')), # ยอดก่อนภาษีมูลค่าเพิ่ม (NoneVat)
                str(pdf_data.get('vat_value', '')),      # ยอดภาษีมูลค่าเพิ่ม
                str(pdf_data.get('total_in_vat', '')),   # ยอดหลังบวกภาษีมูลค่าเพิ่ม
                pdf_data.get('company_name', '')         # ชื่อบริษัท
            ]
            
            # แสดงข้อมูลที่จะกรอกในรูปแบบที่กำหนด
            print(f"📝 ข้อมูลที่จะกรอก:")
            print(f"   Customer ID: {pdf_data.get('customer_id', '')}")
            print(f"   Account Code: {pdf_data.get('account_code', '')}")
            print(f"   เลขที่เอกสาร: {pdf_data.get('document_number', '')}")
            print(f"   วันที่เอกสาร: {pdf_data.get('document_date', '')}")
            print(f"   ยอดก่อนภาษีมูลค่าเพิ่ม: {pdf_data.get('total_ex_vat', '')}")
            print(f"   ยอดก่อนภาษีมูลค่าเพิ่ม (NoneVat): {pdf_data.get('total_ex_vat_none', '')}")
            print(f"   ยอดภาษีมูลค่าเพิ่ม: {pdf_data.get('vat_value', '')}")
            print(f"   ยอดหลังบวกภาษีมูลค่าเพิ่ม: {pdf_data.get('total_in_vat', '')}")
            print(f"   ชื่อบริษัท: {pdf_data.get('company_name', '')}")
            
            print(f"📝 ข้อมูลที่จะกรอก: {data_to_fill}")
            
            filled_count = 0
            for i, data in enumerate(data_to_fill):
                if i < input_fields.count() and data:
                    try:
                        input_fields.nth(i).fill(data)
                        print(f"✅ กรอกฟิลด์ที่ {i+1}: {data}")
                        filled_count += 1
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"⚠️ ไม่สามารถกรอกฟิลด์ที่ {i+1}: {e}")
            
            print(f"✅ กรอกข้อมูลสำเร็จ {filled_count}/{len([d for d in data_to_fill if d])} ฟิลด์")
            return filled_count > 0
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการกรอกฟอร์มทั่วไป: {e}")
            return False
    
    def upload_file(self, file_path: str) -> bool:
        """อัปโหลดไฟล์"""
        try:
            if not self.is_logged_in:
                print("Not logged in")
                return False
            
            print(f"Uploading file: {file_path}")
            
            # 1. เปิดเต็มจอ
            print(f"🖥️ กำลังเปิดเต็มจอ...")
            self.page.bring_to_front()
            self.page.evaluate("document.documentElement.requestFullscreen()")
            time.sleep(1)
            
            # 2. รอให้หน้าเว็บโหลดเสร็จ (ลด timeout และใช้วิธีอื่น)
            print(f"⏳ รอให้หน้าเว็บโหลดเสร็จ...")
            try:
                # ลองรอ networkidle แต่ลด timeout
                self.page.wait_for_load_state('networkidle', timeout=5000)
                print(f"✅ หน้าเว็บโหลดเสร็จ (networkidle)")
            except:
                # ถ้า timeout ให้รอแค่ DOM content loaded
                try:
                    self.page.wait_for_load_state('domcontentloaded', timeout=3000)
                    print(f"✅ หน้าเว็บโหลดเสร็จ (domcontentloaded)")
                except:
                    print(f"⚠️ รอหน้าเว็บโหลด timeout ใช้การรอแบบธรรมดา")
                
            time.sleep(2)  # รอเพิ่มเติมให้แน่ใจว่าโหลดเสร็จแล้ว
            
            # 3. เลื่อนลงไปหาปุ่ม "เพิ่มไฟล์" ที่อยู่ด้านล่าง
            print(f"🔍 กำลังเลื่อนลงไปหาปุ่มเพิ่มไฟล์...")
            
            # วิธีที่ 1: เลื่อนลงไปด้านล่างของหน้า
            print(f"📜 วิธีที่ 1: เลื่อนลงไปด้านล่างของหน้า...")
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            
            # วิธีที่ 2: เลื่อนทีละส่วน
            print(f"📜 วิธีที่ 2: เลื่อนทีละส่วน...")
            self.page.evaluate("window.scrollBy(0, 500)")
            time.sleep(0.5)
            self.page.evaluate("window.scrollBy(0, 500)")
            time.sleep(0.5)
            self.page.evaluate("window.scrollBy(0, 500)")
            time.sleep(0.5)
            
            # วิธีที่ 3: เลื่อนไปยัง element ที่มีคำว่า "เพิ่มไฟล์"
            print(f"📜 วิธีที่ 3: เลื่อนไปยัง element ที่มีคำว่า 'เพิ่มไฟล์'...")
            try:
                add_file_elements = self.page.locator('text=เพิ่มไฟล์, text=Add file, text=Upload, text=อัปโหลด')
                if add_file_elements.count() > 0:
                    # เลื่อนไปยัง element แรกที่พบ
                    add_file_elements.first.scroll_into_view_if_needed()
                    print(f"✅ เลื่อนไปยัง element 'เพิ่มไฟล์' สำเร็จ")
                    time.sleep(1)
                else:
                    print(f"⚠️ ไม่พบ element ที่มีคำว่า 'เพิ่มไฟล์'")
            except Exception as scroll_error:
                print(f"⚠️ ไม่สามารถเลื่อนไปยัง element ได้: {scroll_error}")
            
            # วิธีที่ 4: เลื่อนไปยังปุ่มชำระเงิน (ถ้ามี)
            print(f"📜 วิธีที่ 4: เลื่อนไปยังปุ่มชำระเงิน...")
            try:
                pay_button = self.page.locator('button:has-text("ชำระเงิน"), button:has-text("Pay"), button:has-text("Payment")')
                if pay_button.count() > 0:
                    pay_button.first.scroll_into_view_if_needed()
                    print(f"✅ เลื่อนไปยังปุ่มชำระเงินสำเร็จ")
                    time.sleep(1)
                else:
                    print(f"⚠️ ไม่พบปุ่มชำระเงิน")
            except Exception as scroll_error:
                print(f"⚠️ ไม่สามารถเลื่อนไปยังปุ่มชำระเงินได้: {scroll_error}")
            
            # 2. หาปุ่ม "เพิ่มไฟล์" โดยใช้ XPath ที่ระบุ
            print(f"🔍 กำลังหาปุ่มเพิ่มไฟล์...")
            
            # ใช้ XPath ที่ผู้ใช้ระบุ
            specific_xpath = '//*[@id="content"]/div[6]/div[1]/div[4]/div[7]/div[3]/div[2]/div[3]/div'
            
                        # หาปุ่มด้วย XPath ที่ระบุ
            add_file_button = self.page.locator(f'xpath={specific_xpath}')
            
            if add_file_button.count() > 0:
                print(f"✅ พบปุ่มเพิ่มไฟล์ที่ XPath: {specific_xpath}")
                
                # เลื่อนไปยังปุ่มนั้น
                print(f"📜 เลื่อนไปยังปุ่มเพิ่มไฟล์...")
                add_file_button.first.scroll_into_view_if_needed()
                time.sleep(1)
                
                # คลิกปุ่มเพิ่มไฟล์
                print(f"🖱️ กำลังคลิกปุ่มเพิ่มไฟล์...")
                add_file_button.first.click()
                time.sleep(1)  # รอให้ dialog เปิด
                print(f"✅ คลิกปุ่มเพิ่มไฟล์สำเร็จ")
                
            else:
                print(f"❌ ไม่พบปุ่มเพิ่มไฟล์ที่ XPath: {specific_xpath}")
                
                # ลองหาปุ่มเพิ่มไฟล์ด้วยวิธีเดิม (เป็น fallback)
                print(f"🔍 ลองหาปุ่มเพิ่มไฟล์ด้วยวิธีอื่น...")
                add_file_button = self.page.locator('button:has-text("เพิ่มไฟล์"), button:has-text("Add file"), button:has-text("Upload"), button:has-text("อัปโหลด")')
                
                if add_file_button.count() > 0:
                    print(f"✅ พบปุ่มเพิ่มไฟล์ (fallback): {add_file_button.count()} ปุ่ม")
                    
                    # คลิกปุ่มเพิ่มไฟล์
                    print(f"🖱️ กำลังคลิกปุ่มเพิ่มไฟล์ (fallback)...")
                    add_file_button.first.click()
                    time.sleep(1)  # รอให้ dialog เปิด
                    print(f"✅ คลิกปุ่มเพิ่มไฟล์สำเร็จ")
                else:
                    print(f"❌ ไม่พบปุ่มเพิ่มไฟล์")
                    return False
            
            # 3. หา file input field หลังจากคลิกปุ่ม
            print(f"🔍 กำลังหาฟิลด์อัปโหลดหลังจากคลิกปุ่ม...")
            file_input = None
            
            # วิธีที่ 1: หาด้วย type="file"
            file_input = self.page.locator('input[type="file"]')
            if file_input.count() > 0:
                print(f"✅ พบฟิลด์อัปโหลดด้วยวิธีที่ 1: input[type='file']")
            else:
                # วิธีที่ 2: หาด้วย id ที่มีคำว่า file, upload, attachment
                file_input = self.page.locator('input[id*="file"], input[id*="upload"], input[id*="attachment"]')
                if file_input.count() > 0:
                    print(f"✅ พบฟิลด์อัปโหลดด้วยวิธีที่ 2: id ที่มีคำว่า file/upload/attachment")
                else:
                    # วิธีที่ 3: หาด้วย name ที่มีคำว่า file, upload, attachment
                    file_input = self.page.locator('input[name*="file"], input[name*="upload"], input[name*="attachment"]')
                    if file_input.count() > 0:
                        print(f"✅ พบฟิลด์อัปโหลดด้วยวิธีที่ 3: name ที่มีคำว่า file/upload/attachment")
                    else:
                        # วิธีที่ 4: หาด้วย class ที่มีคำว่า file, upload, attachment
                        file_input = self.page.locator('input[class*="file"], input[name*="upload"], input[name*="attachment"]')
                        if file_input.count() > 0:
                            print(f"✅ พบฟิลด์อัปโหลดด้วยวิธีที่ 4: class ที่มีคำว่า file/upload/attachment")
                        else:
                            # วิธีที่ 5: หาด้วย placeholder ที่มีคำว่า file, upload, attachment
                            file_input = self.page.locator('input[placeholder*="file"], input[placeholder*="upload"], input[placeholder*="attachment"]')
                            if file_input.count() > 0:
                                print(f"✅ พบฟิลด์อัปโหลดด้วยวิธีที่ 5: placeholder ที่มีคำว่า file/upload/attachment")
                            else:
                                # วิธีที่ 6: หาด้วย label ที่มีคำว่า file, upload, attachment
                                file_labels = self.page.locator('label:has-text("file"), label:has-text("upload"), label:has-text("attachment"), label:has-text("ไฟล์"), label:has-text("อัปโหลด")')
                                if file_labels.count() > 0:
                                    # หา input ที่เกี่ยวข้องกับ label
                                    for i in range(file_labels.count()):
                                        label_text = file_labels.nth(i).text_content()
                                        print(f"🔍 พบ label: '{label_text}'")
                                        # หา input ที่เกี่ยวข้อง
                                        related_input = self.page.locator(f'input[aria-label*="{label_text}"], input[title*="{label_text}"]')
                                        if related_input.count() > 0:
                                            file_input = related_input
                                            print(f"✅ พบฟิลด์อัปโหลดด้วยวิธีที่ 6: label ที่เกี่ยวข้อง")
                                            break
                                else:
                                    # วิธีที่ 7: หาด้วย XPath ที่อาจเป็นฟิลด์อัปโหลด
                                    file_input = self.page.locator('//input[contains(@id, "file") or contains(@name, "file") or contains(@class, "file")]')
                                    if file_input.count() > 0:
                                        print(f"✅ พบฟิลด์อัปโหลดด้วยวิธีที่ 7: XPath")
                                    else:
                                        print(f"⚠️ ไม่พบฟิลด์อัปโหลดด้วยวิธีใดเลย")
                                        return False
            
            if file_input and file_input.count() > 0:
                print(f"📁 พบฟิลด์อัปโหลด: {file_input.count()} ฟิลด์")
                
                # แสดงข้อมูลของฟิลด์ที่พบ
                for i in range(min(file_input.count(), 3)):  # แสดงแค่ 3 ฟิลด์แรก
                    try:
                        input_id = file_input.nth(i).get_attribute('id')
                        input_name = file_input.nth(i).get_attribute('name')
                        input_class = file_input.nth(i).get_attribute('class')
                        print(f"   ฟิลด์ที่ {i+1}: id='{input_id}', name='{input_name}', class='{input_class}'")
                    except:
                        pass
                
                # อัปโหลดไฟล์
                print(f"📤 กำลังอัปโหลดไฟล์: {file_path}")
                file_input.first.set_input_files(file_path)
                
                # รอให้อัปโหลดเสร็จ
                time.sleep(1)
                
                print("✅ File uploaded successfully")
                return True
            else:
                print("❌ No file input field found")
                return False
            
        except Exception as e:
            print(f"❌ Error uploading file: {e}")
            return False
    
    def wait_for_processing(self, timeout: int = 60) -> bool:
        """รอให้การประมวลผลเสร็จสิ้น"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # ตรวจสอบแจ้งเตือนสำเร็จ (dvgreenalert) ถ้ามีถือว่าเสร็จงานทันที
                try:
                    success_alert = self.page.locator('//*[@id="dvgreenalert"]')
                    if success_alert.count() > 0 and success_alert.first.is_visible():
                        try:
                            alert_label = self.page.locator('//*[@id="lbgreenalert"]')
                            alert_text = (alert_label.first.text_content() or '').strip() if alert_label.count() > 0 else (success_alert.first.text_content() or '').strip()
                        except Exception:
                            alert_text = (success_alert.first.text_content() or '').strip()
                        # เคสอัปโหลดสำเร็จปกติ
                        if any(keyword in alert_text for keyword in ['เพิ่มไฟล์สำเร็จ', 'อัปโหลดสำเร็จ', 'อัปไฟล์สำเร็จ', 'Upload', 'Uploaded']):
                            print("✅ พบการแจ้งเตือนสำเร็จ: เพิ่มไฟล์สำเร็จ → จบการทำงาน")
                            return True
                        # เคสเอกสารซ้ำ ให้ย้ายไฟล์ที่สร้างไปไว้ในโฟลเดอร์ 'เอกสารซ้ำรอตรวจ'
                        if 'เลขที่ใบกำกับภาษีอ้างอิงนี้สำหรับผู้ติดต่อนี้เคยถูกใช้งานแล้ว' in alert_text or 'ผู้ติดต่อนี้เคยถูกใช้งานแล้ว' in alert_text:
                            print('⚠️ พบแจ้งเตือนเอกสารซ้ำ → ย้ายไฟล์ไปยังโฟลเดอร์ เอกสารซ้ำรอตรวจ')
                            try:
                                if getattr(self, 'latest_created_file_path', None):
                                    moved_to = self.file_manager.move_file_to_duplicate_folder(self.latest_created_file_path)
                                    if moved_to:
                                        print(f"✅ ย้ายไฟล์ไปยังโฟลเดอร์เอกสารซ้ำรอตรวจแล้ว: {moved_to}")
                                    else:
                                        print("❌ ย้ายไฟล์ไปยังโฟลเดอร์เอกสารซ้ำรอตรวจไม่สำเร็จ")
                                else:
                                    print("⚠️ ไม่มีพาธไฟล์ล่าสุดให้ย้าย (latest_created_file_path ว่าง)")
                            except Exception as move_err:
                                print(f"⚠️ ย้ายไฟล์ไปโฟลเดอร์เอกสารซ้ำรอตรวจล้มเหลว: {move_err}")
                            return True
                except Exception:
                    pass

                # ตรวจสอบแจ้งเตือน error สีแดง (dvredalert) สำหรับเอกสารซ้ำ
                try:
                    error_alert = self.page.locator('//*[@id="dvredalert"]')
                    if error_alert.count() > 0 and error_alert.first.is_visible():
                        try:
                            alert_label = self.page.locator('//*[@id="lbredalert"]')
                            alert_text = (alert_label.first.text_content() or '').strip() if alert_label.count() > 0 else (error_alert.first.text_content() or '').strip()
                        except Exception:
                            alert_text = (error_alert.first.text_content() or '').strip()
                        if 'เลขที่ใบกำกับภาษีอ้างอิงนี้สำหรับผู้ติดต่อนี้เคยถูกใช้งานแล้ว' in alert_text or 'ผู้ติดต่อนี้เคยถูกใช้งานแล้ว' in alert_text:
                            print('⚠️ พบแจ้งเตือนเอกสารซ้ำ (แดง) → ย้ายไฟล์ไปยังโฟลเดอร์ เอกสารซ้ำรอตรวจ')
                            try:
                                if getattr(self, 'latest_created_file_path', None):
                                    moved_to = self.file_manager.move_file_to_duplicate_folder(self.latest_created_file_path)
                                    if moved_to:
                                        print(f"✅ ย้ายไฟล์ไปยังโฟลเดอร์เอกสารซ้ำรอตรวจแล้ว: {moved_to}")
                                    else:
                                        print("❌ ย้ายไฟล์ไปยังโฟลเดอร์เอกสารซ้ำรอตรวจไม่สำเร็จ")
                                else:
                                    print("⚠️ ไม่มีพาธไฟล์ล่าสุดให้ย้าย (latest_created_file_path ว่าง)")
                            except Exception as move_err:
                                print(f"⚠️ ย้ายไฟล์ไปโฟลเดอร์เอกสารซ้ำรอตรวจล้มเหลว: {move_err}")
                            return True
                except Exception:
                    pass
                
                # ตรวจสอบสถานะการประมวลผล
                try:
                    # หา element ที่แสดงสถานะ
                    status_element = self.page.locator('.status, .progress, [data-status]')
                    
                    if status_element.count() > 0:
                        status_text = status_element.first.text_content()
                        
                        if 'complete' in status_text.lower() or 'เสร็จสิ้น' in status_text:
                            print("Processing completed")
                            return True
                        elif 'error' in status_text.lower() or 'ผิดพลาด' in status_text:
                            print("Processing error detected")
                            return False
                    
                    # ตรวจสอบ URL ว่ามีการเปลี่ยนหรือไม่
                    current_url = self.page.url
                    if 'success' in current_url.lower() or 'complete' in current_url.lower():
                        print("Processing completed (URL change detected)")
                        return True
                    
                except Exception as e:
                    print(f"Error checking status: {e}")
                
                time.sleep(0.5)
            
            print("Processing timeout")
            return False
            
        except Exception as e:
            print(f"Error waiting for processing: {e}")
            return False
    
    def create_new_pdf_and_rename(self, pdf_data: Dict) -> bool:
        """สร้างไฟล์ PDF ใหม่และเปลี่ยนชื่อไฟล์ตามรูปแบบที่กำหนด"""
        try:
            print(f"📄 กำลังสร้างไฟล์ PDF ใหม่...")
            
            # 1. ดึงข้อมูลจาก h3 element
            print(f"🔍 กำลังดึงข้อมูลจาก h3 element...")
            h3_element = self.page.locator('//*[@id="content"]/div[6]/div[1]/div[3]/div[1]/h3/text()')
            
            if h3_element.count() > 0:
                h3_text = h3_element.first.text_content()
                print(f"📋 ข้อมูลจาก h3: '{h3_text}'")
                
                # 2. ใช้ FileManager สร้างไฟล์ PDF ใหม่
                new_pdf_filename = self.file_manager.create_pdf_from_form_data(pdf_data, h3_text)
                
                if new_pdf_filename:
                    print(f"✅ สร้างไฟล์ PDF ใหม่สำเร็จ: {new_pdf_filename}")
                    
                    # 3. อัปโหลดไฟล์ใหม่
                    print(f"📤 กำลังอัปโหลดไฟล์ใหม่...")
                    if self.upload_file(new_pdf_filename):
                        print(f"✅ อัปโหลดไฟล์ใหม่สำเร็จ: {new_pdf_filename}")
                        
                        # 4. ลบไฟล์ชั่วคราว
                        self.file_manager.cleanup_temp_files()
                        
                        return True
                    else:
                        print(f"❌ ไม่สามารถอัปโหลดไฟล์ใหม่ได้")
                        return False
                else:
                    print(f"❌ ไม่สามารถสร้างไฟล์ PDF ใหม่ได้")
                    return False
                    
            else:
                print(f"⚠️ ไม่พบ h3 element")
                return False
                
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการสร้างไฟล์ PDF ใหม่: {e}")
            return False
    
    def create_and_upload_pdf(self, pdf_data: Dict) -> bool:
        """สร้างไฟล์ PDF ใหม่และอัปโหลด"""
        try:
            print(f"📄 เริ่มกระบวนการสร้างและอัปโหลดไฟล์ PDF...")
            
            # 1. สร้างไฟล์ PDF ใหม่
            if self.create_new_pdf_and_rename(pdf_data):
                print(f"✅ สร้างไฟล์ PDF ใหม่สำเร็จ")
                return True
            else:
                print(f"❌ ไม่สามารถสร้างไฟล์ PDF ใหม่ได้")
                return False
                
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการสร้างและอัปโหลดไฟล์ PDF: {e}")
            return False
    
    def close_driver(self):
        """ปิด Playwright"""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            print("Playwright closed")
        except Exception as e:
            print(f"Error closing Playwright: {e}")
    
    def is_page_loaded(self) -> bool:
        """ตรวจสอบว่าเพจโหลดเสร็จแล้วหรือไม่"""
        try:
            return self.page.evaluate("document.readyState") == "complete"
        except:
            return False
    
    def take_screenshot(self, filename: str = "screenshot.png"):
        """ถ่ายภาพหน้าจอ"""
        try:
            if self.page:
                self.page.screenshot(path=filename)
                print(f"Screenshot saved: {filename}")
                return True
        except Exception as e:
            print(f"Error taking screenshot: {e}")
        return False
    
    def wait_for_element(self, selector: str, timeout: int = 30) -> bool:
        """รอให้ element ปรากฏ"""
        try:
            self.page.wait_for_selector(selector, timeout=timeout * 1000)
            return True
        except Exception as e:
            print(f"Element {selector} not found within {timeout} seconds")
            return False
    
    def click_element(self, selector: str) -> bool:
        """คลิก element"""
        try:
            element = self.page.locator(selector)
            if element.count() > 0:
                element.first.click()
                return True
            return False
        except Exception as e:
            print(f"Error clicking element {selector}: {e}")
            return False
    
    def get_page_content(self) -> str:
        """ดึงเนื้อหาของหน้าเว็บ"""
        try:
            return self.page.content()
        except Exception as e:
            print(f"Error getting page content: {e}")
            return ""
    
    def execute_script(self, script: str):
        """รัน JavaScript"""
        try:
            return self.page.evaluate(script)
        except Exception as e:
            print(f"Error executing script: {e}")
            return None
    
    def peak_engine_workflow(self, pdf_data_list: list, start_index: int = 0):
        """ทำงานกับ PeakEngine ตามข้อมูลจาก PDF"""
        try:
            if not self.page:
                print("❌ Playwright page not initialized")
                return False
            
            print(f"🚀 เริ่มต้นการทำงานกับ PeakEngine...")
            print(f"📊 ข้อมูล PDF ที่จะประมวลผล: {len(pdf_data_list)} ไฟล์")
            
            # 1. เข้าหน้า Login
            print(f"🔐 เข้าหน้า Login...")
            self.page.goto("https://secure.peakengine.com/Home/Login")
            
            
            # 2. ล็อกอิน (ปรับให้ตรงกับโครงสร้างเว็บไซต์ PeakEngine)
            print(f"🔑 กำลังล็อกอิน...")
            try:
                # หาและกรอกอีเมล (Username)
                print(f"📧 กำลังกรอกอีเมล...")
                email_field = self.page.locator('input[placeholder="อีเมล"], input[type="email"], input[name="email"]')
                if email_field.count() > 0:
                    email_field.first.fill(self.credentials.get('Username', ''))
                    print(f"✅ กรอกอีเมลสำเร็จ: {self.credentials.get('Username', '')}")
                else:
                    print(f"⚠️ ไม่พบฟิลด์อีเมล")
                    return False
                
                # หาและกรอกรหัสผ่าน (Password)
                print(f"🔒 กำลังกรอกรหัสผ่าน...")
                password_field = self.page.locator('input[placeholder="รหัสผ่าน"], input[type="password"], input[name="password"]')
                if password_field.count() > 0:
                    password_field.first.fill(self.credentials.get('Password', ''))
                    print(f"✅ กรอกรหัสผ่านสำเร็จ")
                else:
                    print(f"⚠️ ไม่พบฟิลด์รหัสผ่าน")
                    return False
                
                # กดปุ่ม "เข้าใช้งาน" (Login) - ใช้ ID ที่ระบุ
                print(f"🚀 กำลังกดปุ่มเข้าใช้งาน...")
                # หาปุ่มด้วย ID loginbtn ที่ระบุ
                login_button = self.page.locator('#loginbtn, button#loginbtn, input#loginbtn')
                if login_button.count() > 0:
                    login_button.first.click()
                    print(f"✅ กดปุ่มเข้าใช้งานสำเร็จ (ID: loginbtn)")
                else:
                    # ถ้าไม่พบ ID ให้ลองหาด้วยวิธีอื่น
                    print(f"🔍 ไม่พบ ID loginbtn ลองหาด้วยวิธีอื่น...")
                    login_button = self.page.locator('button:has-text("เข้าใช้งาน"), button:has-text("Login"), button[type="submit"], button.teal, button[class*="teal"], button:has-text("เข้าสู่ระบบ")')
                    if login_button.count() > 0:
                        login_button.first.click()
                        print(f"✅ กดปุ่มเข้าใช้งานสำเร็จ")
                    else:
                        # ถ้าไม่พบปุ่ม ให้ลองหาด้วย text content
                        print(f"🔍 ลองหาปุ่มด้วยวิธีอื่น...")
                        all_buttons = self.page.locator('button')
                        for i in range(all_buttons.count()):
                            button_text = all_buttons.nth(i).text_content()
                            print(f"   ปุ่มที่ {i+1}: '{button_text}'")
                            if "เข้าใช้งาน" in button_text or "Login" in button_text or "เข้าสู่ระบบ" in button_text:
                                all_buttons.nth(i).click()
                                print(f"✅ กดปุ่มสำเร็จ: '{button_text}'")
                                break
                        else:
                            print(f"❌ ไม่พบปุ่มเข้าใช้งาน")
                            return False
                                    # รอให้ล็อกอินเสร็จ
                print(f"⏳ รอการล็อกอิน...")
                
                try:
                    # รอให้ network idle และ redirect เสร็จสิ้น
                    self.page.wait_for_load_state('networkidle', timeout=10000)
                    
                    
                    # รอให้ redirect เสร็จสิ้น (เพิ่มการรอ)
                    print(f"🔄 รอการ redirect...")
                    max_wait = 10  # รอสูงสุด 10 วินาที
                    wait_count = 0
                    
                    while wait_count < max_wait:
                        current_url = self.page.url
                        if current_url != "https://secure.peakengine.com/Home/Login":
                            print(f"✅ Redirect เสร็จสิ้น: {current_url}")
                            break
                        time.sleep(0.5)
                        wait_count += 1
                        print(f"   รอ redirect... {wait_count}/{max_wait}")
                    
                    # ตรวจสอบว่าล็อกอินสำเร็จหรือไม่
                    current_url = self.page.url
                    print(f"📍 URL ปัจจุบัน: {current_url}")
                    
                    # ตรวจสอบหลายเงื่อนไข
                    print(f"🔍 ตรวจสอบเงื่อนไขการล็อกอิน...")
                    print(f"   URL ปัจจุบัน: {current_url}")
                    print(f"   มี 'login' ใน URL: {'login' in current_url.lower()}")
                    print(f"   มี 'home/login' ใน URL: {'home/login' in current_url.lower()}")
                    print(f"   เท่ากับ URL เริ่มต้น: {current_url == 'https://secure.peakengine.com/Home/Login'}")
                    
                    # ตรวจสอบว่าล็อกอินสำเร็จหรือไม่ (ปรับเงื่อนไขให้ยืดหยุ่นขึ้น)
                    login_success = False
                    
                    # เงื่อนไขที่ 1: URL เปลี่ยนไปแล้ว
                    if ("login" not in current_url.lower() and 
                        "home/login" not in current_url.lower() and
                        current_url != "https://secure.peakengine.com/Home/Login"):
                        login_success = True
                        print(f"✅ ล็อกอินสำเร็จ (เงื่อนไขที่ 1): URL เปลี่ยนไปแล้ว")
                    
                    # เงื่อนไขที่ 2: ไม่มีฟิลด์ login อยู่แล้ว
                    try:
                        login_fields = self.page.locator('input[type="email"], input[type="password"]')
                        if login_fields.count() == 0:
                            login_success = True
                            print(f"✅ ล็อกอินสำเร็จ (เงื่อนไขที่ 2): ไม่มีฟิลด์ login อยู่แล้ว")
                    except:
                        pass
                    
                    # เงื่อนไขที่ 3: มีข้อความแสดงว่าล็อกอินสำเร็จ
                    try:
                        success_messages = self.page.locator('text=ยินดีด้วย, text=พร้อมเริ่มต้น, text=PEAK')
                        if success_messages.count() > 0:
                            login_success = True
                            print(f"✅ ล็อกอินสำเร็จ (เงื่อนไขที่ 3): พบข้อความแสดงความสำเร็จ")
                    except:
                        pass
                    
                    if login_success:
                        self.is_logged_in = True
                        print(f"✅ ล็อกอินสำเร็จ! ย้ายไปหน้า: {current_url}")
                        
                        # หลังจากล็อกอินสำเร็จ ให้ไปที่ลิงค์ Peak เก่าโดยตรง
                        print(f"🔄 กำลังไปยัง Peak เก่า...")
                        try:
                            # ไปที่ลิงค์ Peak เก่าโดยตรง
                            old_peak_url = "https://secure.peakengine.com/selectlist"
                            print(f"📍 ไปยังลิงค์: {old_peak_url}")
                            
                            self.page.goto(old_peak_url, timeout=10000)  # ลด timeout เป็น 10 วินาที
                            time.sleep(0.5)  # รอแค่ 0.5 วินาที
                            
                            
                            # ตรวจสอบ URL หลังไปยังลิงค์
                            current_url = self.page.url
                            print(f"📍 URL หลังไปยัง Peak เก่า: {current_url}")
                            
                            if "selectlist" in current_url.lower():
                                print(f"✅ ไปยัง Peak เก่าสำเร็จ!")
                                
                                # ต่อไปให้ไปที่ Link Company
                                if self.company_link:
                                    print(f"🏢 ไปยังหน้า Company: {self.company_link}")
                                    self.page.goto(self.company_link)
                                    
                                    
                                    print(f"✅ ไปยังหน้า Company สำเร็จ!")
                                    
                                    # ต่อไปให้ไปที่ Link Express
                                    if self.express_link:
                                        print(f"📝 ไปยังหน้า Express: {self.express_link}")
                                        self.page.goto(self.express_link)
                                        
                                        
                                        print(f"✅ ไปยังหน้า Express สำเร็จ!")
                                        
                                        # ตรวจสอบ URL สุดท้าย
                                        final_url = self.page.url
                                        print(f"📍 URL สุดท้าย: {final_url}")
                                        print(f"🎯 ระบบพร้อมทำงานกับข้อมูล PDF แล้ว!")
                                        
                                        # เริ่มทำงานกับข้อมูล PDF ทันที
                                        print(f"🚀 เริ่มทำงานกับข้อมูล PDF...")
                                        # ไม่ return ออกมา ให้ทำงานต่อใน workflow
                                        pdf_processing_result = self.process_pdf_data(pdf_data_list, start_index=start_index)
                                        print(f"📊 ผลการประมวลผล PDF: {'สำเร็จ' if pdf_processing_result else 'ไม่สำเร็จ'}")
                                        return True
                                    else:
                                        print(f"❌ ไม่พบ Express Link")
                                else:
                                    print(f"❌ ไม่พบ Company Link")
                            else:
                                print(f"⚠️ ไปยัง Peak เก่าไม่สำเร็จ")
                                
                        except Exception as e:
                            print(f"⚠️ เกิดข้อผิดพลาดในการไปยัง Peak เก่า: {e}")
                            print(f"🔍 ลองใช้วิธีอื่น...")
                            try:
                                # ลองใช้ JavaScript navigate
                                self.page.evaluate("window.location.href = 'https://secure.peakengine.com/selectlist'")
                                print(f"✅ ไปยัง Peak เก่าสำเร็จด้วย JavaScript")
                                
                                # รอให้หน้าโหลดเสร็จ
                                
                                
                                
                                # ตรวจสอบ URL หลังไปยังลิงค์
                                current_url = self.page.url
                                print(f"📍 URL หลังไปยัง Peak เก่า: {current_url}")
                                
                                # ต่อไปให้ไปที่ Link Company
                                if self.company_link:
                                    print(f"🏢 ไปยังหน้า Company: {self.company_link}")
                                    self.page.goto(self.company_link)
                                    
                                    
                                    print(f"✅ ไปยังหน้า Company สำเร็จ!")
                                    
                                    # ต่อไปให้ไปที่ Link Express
                                    if self.express_link:
                                        print(f"📝 ไปยังหน้า Express: {self.express_link}")
                                        self.page.goto(self.express_link)
                                        
                                        
                                        print(f"✅ ไปยังหน้า Express สำเร็จ!")
                                        
                                        # ตรวจสอบ URL สุดท้าย
                                        final_url = self.page.url
                                        print(f"📍 URL สุดท้าย: {final_url}")
                                        print(f"🎯 ระบบพร้อมทำงานกับข้อมูล PDF แล้ว!")
                                    else:
                                        print(f"❌ ไม่พบ Express Link")
                                else:
                                    print(f"❌ ไม่พบ Company Link")
                                
                            except Exception as e2:
                                print(f"❌ ไม่สามารถไปยัง Peak เก่าได้ด้วยวิธีใดเลย: {e2}")
                        
                        return True
                    else:
                        print(f"⚠️ เงื่อนไขการล็อกอินไม่ผ่าน - ยังอยู่ที่หน้า login")
                        # ลองตรวจสอบ error message หรือ validation
                        print(f"🔍 ตรวจสอบข้อผิดพลาด...")
                        try:
                            error_messages = self.page.locator('.error, .alert, .message, [class*="error"], [class*="alert"]')
                            if error_messages.count() > 0:
                                error_text = error_messages.first.text_content()
                                print(f"⚠️ พบข้อผิดพลาด: {error_text}")
                        except:
                            print(f"⚠️ ไม่สามารถตรวจสอบ error message ได้")
                        
                        # ตรวจสอบว่ายังมีฟิลด์ login อยู่หรือไม่
                        try:
                            login_fields = self.page.locator('input[type="email"], input[type="password"]')
                            if login_fields.count() > 0:
                                print(f"⚠️ ยังมีฟิลด์ login อยู่ - ล็อกอินไม่สำเร็จ")
                            else:
                                print(f"✅ ไม่มีฟิลด์ login - ล็อกอินอาจสำเร็จ")
                                self.is_logged_in = True
                                return True
                        except:
                            print(f"⚠️ ไม่สามารถตรวจสอบฟิลด์ login ได้")
                        
                        print(f"⚠️ ล็อกอินไม่สำเร็จ - ยังอยู่ที่หน้า login")
                        return False
                        
                except Exception as e:
                    print(f"⚠️ เกิดข้อผิดพลาดในการตรวจสอบล็อกอิน: {e}")
                    # ลองตรวจสอบ URL อีกครั้ง
                    try:
                        current_url = self.page.url
                        print(f"📍 URL หลัง error: {current_url}")
                        if "login" not in current_url.lower():
                            self.is_logged_in = True
                            print(f"✅ ล็อกอินสำเร็จ! (ตรวจสอบจาก URL)")
                            return True
                    except:
                        pass
                    
                    return False
                    
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาดในการล็อกอิน: {e}")
                return False
            
            print(f"✅ ล็อกอินสำเร็จ!")
            
            # 4. ข้ามขั้นตอนการไปยัง Company และ Express (ทำไปแล้วในขั้นตอนการล็อกอิน)
            print(f"✅ ข้ามขั้นตอนการไปยัง Company และ Express (ทำไปแล้ว)")
            
            # 5. ข้อมูล PDF จะถูกประมวลผลใน process_pdf_data method
            print(f"✅ ระบบพร้อมทำงานกับข้อมูล PDF แล้ว!")
            return True
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการทำงานกับ PeakEngine: {e}")
            return False
    
    def get_peak_engine_status(self):
        """ตรวจสอบสถานะการทำงานของ PeakEngine"""
        try:
            if not self.page:
                return "ไม่มีการเชื่อมต่อ"
            
            current_url = self.page.url
            page_title = self.page.title()
            
            return {
                "current_url": current_url,
                "page_title": page_title,
                "is_logged_in": self.is_logged_in,
                "browser_status": "เปิดใช้งาน" if self.browser else "ปิด"
            }
            
        except Exception as e:
            return f"เกิดข้อผิดพลาด: {e}"
    
    def process_pdf_data(self, pdf_data_list: list, start_index: int = 0) -> bool:
        """ประมวลผลข้อมูล PDF ทันทีหลังจากไปยัง Express Link สำเร็จ"""
        try:
            # จำกัดจำนวนการประมวลผลสูงสุด (สามารถปรับได้จาก config)
            max_items = getattr(Config, 'MAX_PROCESSING_ITEMS', 60)
            total_items = len(pdf_data_list)
            
            if total_items > max_items:
                print(f"⚠️ จำนวนรายการ ({total_items}) เกินกำหนดสูงสุด ({max_items})")
                print(f"📊 จะประมวลผลเฉพาะ {max_items} รายการแรก")
                pdf_data_list = pdf_data_list[:max_items]
            
            print(f"📊 เริ่มประมวลผลข้อมูล PDF: {len(pdf_data_list)} ไฟล์ (สูงสุด {max_items} รายการ)")
            
            # ประมวลผลข้อมูล PDF แต่ละไฟล์
            for i, pdf_data in enumerate(pdf_data_list, 1):
                if i < max(1, int(start_index)):
                    continue
                # แสดงความคืบหน้าการประมวลผล
                progress_percent = (i / len(pdf_data_list)) * 100
                print(f"📊 ความคืบหน้า: {i}/{len(pdf_data_list)} ({progress_percent:.1f}%)")
                
                # แจ้งเตือนเมื่อใกล้ครบ 60 รายการ
                if i >= max_items - 5:
                    remaining = max_items - i + 1
                    print(f"⚠️ เหลืออีก {remaining} รายการ จะสิ้นสุดการประมวลผล")
                
                # รีหน้า Express ทุกครั้งก่อนเริ่มไฟล์ใหม่ เพื่อความสะอาดของสถานะ
                self.refresh_express_page()
                print(f"\n ประมวลผลไฟล์ที่ {i}: {pdf_data.get('filename', 'ไม่ทราบชื่อ')}")
                
                # บันทึกข้อมูลปัจจุบันสำหรับ retry กรณีเจอแจ้งเตือนบังคับกรอก
                self._current_pdf_data_for_retry = pdf_data
                self._refill_attempt_count = 0
                
                # 0. ระบุ group จาก folder_settings + folder_code และบันทึกลง pdf_data
                try:
                    folder_settings = self.file_manager.read_folder_settings()
                    source_folder = pdf_data.get('source_folder') or os.path.dirname(pdf_data.get('file_path', '') or pdf_data.get('pdf_path', '') or '')
                    folder_code = self.file_manager.get_folder_code_from_path(Path(source_folder)) if source_folder else None
                    if folder_code and 'folder_code' not in pdf_data:
                        pdf_data['folder_code'] = folder_code
                    group = 'unknown'
                    if folder_code and folder_code in folder_settings:
                        group = folder_settings[folder_code].get('group', 'unknown')
                    pdf_data['group'] = group
                    # คำนวณชื่อบริการจาก mapping เพื่อใช้แสดงผล
                    try:
                        comp = pdf_data.get('company_name', '')
                        service_name = self.file_manager._get_service_name(comp, folder_settings, pdf_data)
                    except Exception:
                        service_name = ''
                    if service_name:
                        pdf_data['service_name'] = service_name
                    print(f"🗂️ จัดกลุ่มไฟล์: folder_code='{folder_code or ''}', group='{group}'")
                except Exception as _:
                    group = pdf_data.get('group') or 'unknown'

                # 1. กรอกข้อมูลในฟอร์ม (กรณี NoneVat จะไม่กรอกเลขที่เอกสาร ตาม pdf_data['group'])
                if self.fill_form_data(pdf_data):
                    print(f"✅ กรอกข้อมูลสำเร็จ")
                    
                    # 2. รอผลบันทึก/ยืนยัน (อนุมัติ หรือ เอกสารซ้ำ)
                    print(f"⏳ รอผลบันทึก/ยืนยัน...")
                    result = self.wait_for_save_result(timeout=20)
                    print(f"📊 ผลการบันทึก: {result}")
                    
                    if result == 'duplicate':
                        # อัปเดตตัวนับในรายงาน: เอกสารซ้ำ
                        try:
                            rm = get_global_report_manager()
                            if rm:
                                rm.add_duplicate(1)
                        except Exception:
                            pass
                        # ย้ายไฟล์ต้นฉบับไปโฟลเดอร์ เอกสารซ้ำรอตรวจ แล้วไปไฟล์ถัดไป
                        original_path = pdf_data.get('file_path') or pdf_data.get('pdf_path')
                        if original_path:
                            moved = self.file_manager.move_file_to_duplicate_folder(original_path)
                            if moved:
                                print(f"✅ ย้ายไฟล์ต้นฉบับไปยัง 'เอกสารซ้ำรอตรวจ': {moved}")
                            else:
                                print("❌ ย้ายไฟล์ต้นฉบับไปยังโฟลเดอร์เอกสารซ้ำรอตรวจไม่สำเร็จ")
                        else:
                            print("⚠️ ไม่พบพาธไฟล์ต้นฉบับใน pdf_data")
                        time.sleep(0.2)
                        continue
                    elif result == 'timeout':
                        print("⚠️ ไม่พบผลบันทึกภายในเวลา 20 วินาที")
                        print("🔍 ตรวจสอบสถานะหน้าเว็บ...")
                        
                        # ตรวจสอบว่าหน้าเว็บยังทำงานอยู่หรือไม่
                        try:
                            # ตรวจสอบว่ามี error message หรือไม่
                            error_elements = [
                                '//*[@id="dvredalert"]',
                                '//*[@id="dvgreenalert"]',
                                '[class*="error"]',
                                '[class*="alert"]'
                            ]
                            
                            found_error = False
                            for selector in error_elements:
                                try:
                                    element = self.page.locator(selector)
                                    if element.count() > 0 and element.first.is_visible():
                                        text = element.first.text_content() or ''
                                        if text.strip():
                                            print(f"🔍 พบข้อความ: {text.strip()}")
                                            found_error = True
                                except Exception:
                                    pass
                            
                            if not found_error:
                                print("ℹ️ ไม่พบ alert box หรือ error message")
                                print("🔄 ลองรีเฟรชหน้าเว็บ...")
                                self.refresh_express_page()
                                time.sleep(2)
                        except Exception as e:
                            print(f"⚠️ ตรวจสอบสถานะหน้าเว็บไม่สำเร็จ: {e}")
                        
                        print("⏭️ ข้ามไฟล์นี้ไปไฟล์ถัดไป")
                        time.sleep(0.2)
                        continue
                    # result == 'approved' → ค่อยสร้างไฟล์ใหม่และอัปโหลด
                    try:
                        rm = get_global_report_manager()
                        if rm:
                            rm.add_processed_success(1)
                    except Exception:
                        pass
                    
                    # 2.x สำหรับบริษัท VAT เท่านั้นจึงตรวจ/แก้ VAT
                    company_name = pdf_data.get('company_name', '')
                    company_vat_status = Config.COMPANY_VAT_STATUS.get(company_name, 'VAT')
                    folder_group = pdf_data.get('group') or group or 'unknown'
                    
                    print(f"🔍 ตรวจสอบเงื่อนไข: folder_group='{folder_group}', company_vat_status='{company_vat_status}'")
                    
                    # ให้ความสำคัญกับ folder_group ก่อน
                    if folder_group == 'special' or company_vat_status == 'NoneVat':
                        print(f"ℹ️ โฟลเดอร์ special (NoneVat): ข้ามขั้นตอนตรวจ/แก้ไข VAT")
                    elif company_vat_status == 'VAT':
                        # 2.1 หน่วง 1 วิ และเลื่อนลงก่อนตรวจ VAT (หลังอนุมัติสำเร็จ)
                        print(f"ℹ️ บริษัท {company_name}: ทำงานแบบ VAT - ตรวจ/แก้ไข VAT")
                        time.sleep(1)
                        try:
                            self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        except Exception:
                            pass
                        # 2.2 ตรวจและแก้ไข VAT ถ้าจำเป็น (ก่อนสร้างไฟล์/อัปโหลด)
                        try:
                            vat_ok = self.check_and_fix_vat_value(str(pdf_data.get('vat_value', '')))
                            if not vat_ok:
                                print('❌ แก้ไข VAT ไม่สำเร็จ ข้ามไฟล์นี้เพื่อป้องกันข้อมูลผิดพลาด')
                                time.sleep(0.2)
                                continue
                        except Exception as _:
                            print('⚠️ ข้ามขั้นตอนตรวจ/แก้ไข VAT เนื่องจากเกิดข้อยกเว้น')
                            time.sleep(0.2)
                            continue
                    else:
                        print(f"ℹ️ บริษัท {company_name}: ทำงานแบบ NoneVat - ข้ามขั้นตอนตรวจ/แก้ไข VAT")
                    
                    # 3. สร้างไฟล์ PDF ใหม่จากข้อมูลที่กรอกในฟอร์ม
                    print(f" เริ่มสร้างไฟล์ใหม่จากข้อมูลที่กรอก...")
                    new_pdf_filename = self.create_new_pdf_from_form_data(pdf_data)
                    
                    if new_pdf_filename:
                        print(f"✅ สร้างไฟล์ใหม่สำเร็จ: {new_pdf_filename}")
                        
                        # 4. โยนไฟล์เข้าเว็บโดยตรง (ไม่ต้องกดปุ่มอัปโหลด)
                        print(f" โยนไฟล์เข้าเว็บโดยตรง...")
                        if self.upload_file_directly(new_pdf_filename):
                            print(f"✅ โยนไฟล์เข้าเว็บสำเร็จ: {new_pdf_filename}")
                            
                            # 5. รอการประมวลผลหลังจากโยนไฟล์
                            print(f"⏳ รอการประมวลผลหลังจากโยนไฟล์...")
                            if self.wait_for_processing():
                                print(f"✅ ประมวลผลเสร็จสิ้น")
                                
                                # 6. ย้ายไฟล์ก่อน: ต้นฉบับ → เอกสารต้นฉบับ, ไฟล์ที่สร้าง/อัปโหลด → เอกสาร Vat/NoneVat
                                try:
                                    original_path = pdf_data.get('file_path') or pdf_data.get('pdf_path')
                                    processed_path = new_pdf_filename  # new_pdf_filename คือพาธเต็มจาก create_new_pdf_from_form_data
                                    
                                    # ใช้ folder_group และ company_vat_status ในการกำหนดโฟลเดอร์ปลายทาง
                                    # กรณีพิเศษ: folder_group = 'regular' แต่ company_vat_status = 'NoneVat'
                                    # → ทำงานแบบ NoneVat แต่ย้ายไฟล์ไป "เอกสาร Vat" (ตามโฟลเดอร์)
                                    
                                    # ตรวจสอบว่าต้องทำงานแบบ NoneVat หรือไม่
                                    is_nonevat_workflow = (folder_group == 'special' or company_vat_status == 'NoneVat')
                                    
                                    if is_nonevat_workflow:
                                        # ถ้าทำงานแบบ NoneVat ให้ย้ายไฟล์ตาม company_vat_status
                                        if company_vat_status == 'NoneVat':
                                            move_group = 'special'  # ย้ายไป "เอกสาร NoneVat"
                                        else:
                                            move_group = 'regular'  # ย้ายไป "เอกสาร Vat"
                                    else:
                                        # ถ้าทำงานแบบ VAT ให้ย้ายไฟล์ตาม folder_group
                                        if folder_group in ['regular', 'special']:
                                            move_group = folder_group
                                        else:
                                            move_group = 'regular'  # fallback
                                    
                                    print(f"🔍 ย้ายไฟล์: folder_group='{folder_group}', company_vat_status='{company_vat_status}', move_group='{move_group}'")
                                    self.file_manager.move_original_and_processed(original_path, processed_path, move_group)
                                except Exception as _:
                                    print('⚠️ ย้ายไฟล์หลังอัปโหลดไม่สำเร็จ')
                                
                                # 7. จากนั้นค่อยลบไฟล์ชั่วคราว (ป้องกันลบไฟล์ที่ต้องย้าย)
                                self.file_manager.cleanup_temp_files()
                                print(f"️ ลบไฟล์ชั่วคราวเสร็จสิ้น")
                            else:
                                print(f"⚠️ การประมวลผลไม่เสร็จสิ้นหรือเกิดข้อผิดพลาด")
                        else:
                            print(f"❌ โยนไฟล์เข้าเว็บไม่สำเร็จ")
                    else:
                        print(f"❌ ไม่สามารถสร้างไฟล์ใหม่ได้")
                    
                    # รอสักครู่ก่อนไฟล์ถัดไป
                    time.sleep(0.5)
                else:
                    print(f"❌ กรอกข้อมูลไม่สำเร็จ")
            
            print(f"\n🎯 สรุป: ประมวลผลข้อมูล PDF {len(pdf_data_list)} ไฟล์ เสร็จสิ้น!")
            
            # แจ้งเตือนถ้าจำนวนรายการเกิน 60
            if total_items > max_items:
                remaining_items = total_items - max_items
                print(f"⚠️ หมายเหตุ: ยังมีรายการที่เหลืออีก {remaining_items} รายการ")
                print(f"💡 แนะนำ: รันระบบใหม่เพื่อประมวลผลรายการที่เหลือ")
            
            return True
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการประมวลผลข้อมูล PDF: {e}")
            return False
        
    def create_new_pdf_from_form_data(self, pdf_data: Dict) -> Optional[str]:
        """สร้างไฟล์ PDF ใหม่จากข้อมูลที่กรอกในฟอร์ม"""
        try:
            print(f" เริ่มสร้างไฟล์ PDF ใหม่...")
            # ใช้ค่า iptnumber ที่บันทึกล่วงหน้าถ้ามี มิฉะนั้นอ่านจาก DOM
            iptnumber_text = getattr(self, 'latest_iptnumber_text', None)
            if not iptnumber_text:
                print(f"🔍 กำลังดึงข้อมูลจาก iptnumber element...")
                iptnumber_element = self.page.locator('//*[@id="iptnumber"]')
                if iptnumber_element.count() > 0:
                    print(f"✅ พบ iptnumber element: {iptnumber_element.count()} ตัว")
                    try:
                        iptnumber_text = (iptnumber_element.first.input_value() or '').strip()
                    except Exception:
                        iptnumber_text = (iptnumber_element.text_content() or '').strip()
                else:
                    print(f"❌ ไม่พบ iptnumber element")
                    return None
            print(f"📄 ข้อมูลจาก iptnumber (ล่าสุด/DOM): '{iptnumber_text or ''}'")

            # ถ้า iptnumber ว่างหรือเป็น '-' ให้ยกเลิกทันที (ไม่ retry)
            if not iptnumber_text or iptnumber_text == '-':
                print(f"⚠️ ไม่พบข้อมูลใน iptnumber (เป็น '-' หรือว่างเปล่า) ยกเลิกการสร้างไฟล์สำหรับรายการนี้")
                return None

            # อ่านวันที่จากเว็บเพื่อให้ตรงกับข้อมูลที่กรอก
            print(f"🔍 กำลังอ่านวันที่จากเว็บ...")
            date_from_web = None
            try:
                date_field = self.page.locator('//*[@id="iptdate"]')
                if date_field.count() > 0:
                    date_from_web = (date_field.first.input_value() or '').strip()
                    if date_from_web:
                        print(f"📅 อ่านวันที่จากเว็บสำเร็จ: {date_from_web}")
                        # อัปเดตวันที่ใน pdf_data ให้ตรงกับที่กรอกในเว็บ
                        pdf_data['document_date'] = date_from_web
                    else:
                        print(f"⚠️ วันที่บนเว็บว่างเปล่า ใช้วันที่เดิมจาก PDF")
                else:
                    print(f"⚠️ ไม่พบ element วันที่บนเว็บ (#iptdate) ใช้วันที่เดิมจาก PDF")
            except Exception as e:
                print(f"⚠️ อ่านวันที่จากเว็บไม่ได้: {e} ใช้วันที่เดิมจาก PDF")

            # มีค่า iptnumber → สร้างไฟล์
            print(f"✅ ข้อมูล iptnumber มีเนื้อหา: '{iptnumber_text}'")
            print(f"📤 ส่งข้อมูลไปยัง FileManager...")
            source_folder = pdf_data.get('source_folder')
            if not source_folder:
                src_path = pdf_data.get('file_path', '')
                source_folder = os.path.dirname(src_path) if src_path else ''
            # อ่าน folder_settings เพื่อส่งไปยัง create_pdf_from_form_data
            folder_settings = self.file_manager.read_folder_settings()
            
            # เพิ่ม folder_code ลงใน pdf_data ถ้ายังไม่มี
            if 'folder_code' not in pdf_data:
                # พยายามดึง folder_code จาก source_folder
                if source_folder:
                    folder_code = self.file_manager.get_folder_code_from_path(Path(source_folder))
                    if folder_code:
                        pdf_data['folder_code'] = folder_code
                        print(f"🔍 เพิ่ม folder_code: '{folder_code}'")
            
            new_pdf_path = self.file_manager.create_pdf_from_form_data(pdf_data, iptnumber_text, source_folder, folder_settings)
            if new_pdf_path:
                print(f"✅ สร้างไฟล์ PDF ใหม่สำเร็จ: {new_pdf_path}")
                self.latest_created_file_path = new_pdf_path
                return new_pdf_path
            print(f"❌ ไม่สามารถสร้างไฟล์ PDF ใหม่ได้")
            return None
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการสร้างไฟล์ PDF ใหม่: {e}")
            return None

    def fill_customer_id_again(self, pdf_data: Dict) -> bool:
        """กรอก Customer ID ใหม่"""
        try:
            print(f"🔄 กรอก Customer ID ใหม่: {pdf_data.get('customer_id', '')}")
            
            # หา input field สำหรับ Customer ID โดยลองหลาย selector แบบแยกกัน (CSS/XPath)
            selector_candidates = [
                '#iptcontactname',
                'input#iptcontactname',
                'xpath=//*[@id="iptcontactname"]',
                'input[name="customer_id"]',
                'input#customer_id',
                '#customer_id'
            ]

            customer_locator = None
            for sel in selector_candidates:
                loc = self.page.locator(sel)
                if loc.count() > 0:
                    customer_locator = loc.first
                    break

            if not customer_locator:
                print(f"❌ ไม่พบ input field สำหรับ Customer ID")
                return False

            # ลบข้อมูลเก่าและกรอกใหม่
            try:
                customer_locator.fill('')
            except Exception:
                pass
            customer_locator.fill(pdf_data.get('customer_id', ''))

            # ยืนยันการกรอก
            try:
                customer_locator.press('Enter')
            except Exception:
                try:
                    customer_locator.press('Tab')
                except Exception:
                    pass

            print(f"✅ กรอก Customer ID ใหม่สำเร็จ")
            return True
                
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการกรอก Customer ID ใหม่: {e}")
            return False
        
    def upload_file_directly(self, file_path: str) -> bool:
        """โยนไฟล์เข้าเว็บโดยตรงโดยไม่ต้องกดปุ่มอัปโหลด"""
        try:
            if not self.is_logged_in:
                print("Not logged in")
                return False
            
            print(f"�� โยนไฟล์เข้าเว็บโดยตรง: {file_path}")
            
            # 1. หา file input field ที่ซ่อนอยู่
            print(f"�� กำลังหาฟิลด์อัปโหลดที่ซ่อนอยู่...")
            file_input = self.page.locator('input[type="file"]')
            
            if file_input.count() > 0:
                print(f"✅ พบฟิลด์อัปโหลด: {file_input.count()} ฟิลด์")
                
                # โยนไฟล์เข้าไปโดยตรง
                print(f"�� โยนไฟล์เข้าเว็บ...")
                file_input.first.set_input_files(file_path)
                
                # รอให้อัปโหลดเสร็จ
                time.sleep(1)
                
                print(f"✅ โยนไฟล์เข้าเว็บสำเร็จ: {file_path}")
                return True
            else:
                print(f"❌ ไม่พบฟิลด์อัปโหลด")
                return False
                
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการโยนไฟล์: {e}")
            return False
        
    def execute_peak_engine_workflow(self, pdf_data_list: list, main_folder: str) -> bool:
        """จัดการการทำงานทั้งหมดของ PeakEngine (รวมการเปิด/ปิด Playwright)"""
        try:
            print(f"🚀 เริ่มต้นการทำงานด้วย Playwright...")
            success = self.setup_driver()
            
            if not success:
                print(f"❌ ไม่สามารถเปิด Playwright ได้")
                return False
            
            print(f"✅ เปิด Playwright สำเร็จ")
            print(f"📊 รวบรวมข้อมูล PDF: {len(pdf_data_list)} ไฟล์")
            
            # อ่านข้อมูลการตั้งค่าจากไฟล์ txt ที่ตรงกับชื่อโฟลเดอร์ Build*
            # หาโฟลเดอร์ Build* จาก main_folder
            main_folder_path = Path(main_folder)
            build_folder = None
            current_path = main_folder_path
            while current_path != current_path.parent:
                if current_path.name.startswith('Build'):
                    build_folder = current_path
                    break
                current_path = current_path.parent
            
            if build_folder:
                # ใช้แค่หมายเลข BuildXXX (เช่น Build000 ทดสอบระบบ → Build000)
                folder_name = build_folder.name
                build_number = folder_name.split()[0]  # แยกเอาแค่ "Build000"
                # ตำแหน่งหลักภายในโฟลเดอร์งาน
                local_txt = Path(build_folder) / "รหัส" / f"{build_number}.txt"
                # ตำแหน่งสำรองศูนย์รวมในไดรฟ์ V: ภายใต้ A./AA./AAA.โฟรเดอร์หลัก/Build000 ทดสอบระบบ/รหัส
                drive_root = Path(f"{Config.BASE_FOLDER}:/")
                candidates = [local_txt]
                for main_name in getattr(Config, 'MAIN_FOLDERS', ["A.โฟร์เดอร์หลัก", "AA.โฟรเดอร์หลัก", "AAA.โฟรเดอร์หลัก"]):
                    candidates.append(
                        drive_root / main_name / f"Build{Config.TEST_SYSTEM_FOLDER}" / "รหัส" / f"{build_number}.txt"
                    )
                # เผื่อมีโครงสร้าง V:/Build000 ทดสอบระบบ/รหัส ด้วย
                candidates.append(drive_root / f"Build{Config.TEST_SYSTEM_FOLDER}" / "รหัส" / f"{build_number}.txt")

                # เลือกไฟล์แรกที่มีอยู่จริง
                chosen = None
                for c in candidates:
                    if c.exists():
                        chosen = c
                        break
                # debug แสดง path ที่ลองหา
                try:
                    print("🔎 ค้นหา TXT จากตำแหน่งต่อไปนี้ (ลำดับความสำคัญ):")
                    for i, c in enumerate(candidates, start=1):
                        print(f"  {i}) {c}")
                    print(f"➡️ ใช้งาน: {chosen if chosen else 'ไม่พบไฟล์ที่ตรงกัน'}")
                except Exception:
                    pass

                config_file_path = str(chosen) if chosen else str(local_txt)
            else:
                print(f"❌ ไม่พบโฟลเดอร์ Build* จาก: {main_folder}")
                self.close_driver()
                return False
            if not self.read_config_from_txt(config_file_path):
                print(f"❌ ไม่สามารถอ่านข้อมูลการตั้งค่าได้")
                self.close_driver()
                return False
            
            # เรียกใช้ PeakEngine Workflow
            # รองรับการเริ่มต้นจากไฟล์ลำดับที่กำหนดผ่าน pdf_data_list meta: pdf_data_list.__start_index__
            start_index = 0
            try:
                start_index = int(getattr(pdf_data_list, '__start_index__', 0))
            except Exception:
                start_index = 0
            workflow_success = self.peak_engine_workflow(pdf_data_list, start_index=start_index)
            
            if workflow_success:
                print(f"✅ PeakEngine Workflow สำเร็จ!")
                
                # ตรวจสอบสถานะ
                status = self.get_peak_engine_status()
                print(f"📊 สถานะ PeakEngine: {status}")
                
            else:
                print(f"❌ PeakEngine Workflow ไม่สำเร็จ")
            
            # แจ้งเตือนจบงานผ่าน LINE (ครบถ้วน/บางส่วน) หากมี ReportManager จากขั้นตอนอ่าน
            try:
                rm = get_global_report_manager()
            except Exception:
                rm = None
            if rm is not None:
                # ประเมินความสำเร็จ: ถ้าทำงานผ่านเว็บสำเร็จให้ถือว่าครบถ้วน, ไม่เช่นนั้นบางส่วน
                end_message = rm.end_success() if workflow_success else rm.end_partial()
                sent_end = False
                try:
                    if getattr(Config, 'LINE_OA_CHANNEL_ACCESS_TOKEN', '') and getattr(Config, 'LINE_OA_DEFAULT_TO', ''):
                        sent_end = line_oa_push(end_message)
                    elif getattr(Config, 'LINE_NOTIFY_TOKEN', ''):
                        sent_end = line_notify(end_message)
                except Exception:
                    sent_end = False
                if not sent_end:
                    print("ℹ️ ไม่ได้ส่ง LINE end (ไม่มี token OA/Notify หรือล้มเหลว)")

                # สร้างรายงานฉบับสุดท้าย (รวมผลอัปโหลด/ซ้ำ/รอดำเนินการ/อ่านไม่ได้/ฐานข้อมูล)
                try:
                    report_path = rm.write_txt_report()
                    if report_path:
                        print(f"📝 สร้างไฟล์รายงานการทำงาน: {report_path}")
                    else:
                        print("⚠️ สร้างไฟล์รายงานการทำงานไม่สำเร็จ")
                except Exception:
                    print("⚠️ เกิดข้อผิดพลาดระหว่างสร้างไฟล์รายงานฉบับสุดท้าย")

            # ปิด Playwright
            self.close_driver()
            print(f"🔒 ปิด Playwright แล้ว")
            
            return workflow_success
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการทำงานกับ PeakEngine: {e}")
            try:
                self.close_driver()
            except:
                pass
            return False

    def _check_and_handle_duplicate_before_upload(self) -> bool:
        """ตรวจจับแจ้งเตือน 'เลขที่ใบกำกับภาษีอ้างอิงนี้สำหรับผู้ติดต่อนี้เคยถูกใช้งานแล้ว' ก่อนอัปโหลด ถ้าพบให้ย้ายไฟล์ไปโฟลเดอร์ 'เอกสารซ้ำรอตรวจ' และคืนค่า True"""
        try:
            duplicate_texts = [
                'เลขที่ใบกำกับภาษีอ้างอิงนี้สำหรับผู้ติดต่อนี้เคยถูกใช้งานแล้ว',
                'ผู้ติดต่อนี้เคยถูกใช้งานแล้ว'
            ]
            # ตรวจกรอบแดงก่อน
            red = self.page.locator('//*[@id="dvredalert"]')
            if red.count() > 0 and red.first.is_visible():
                try:
                    lb = self.page.locator('//*[@id="lbredalert"]')
                    msg = (lb.first.text_content() or '').strip() if lb.count() > 0 else (red.first.text_content() or '').strip()
                except Exception:
                    msg = (red.first.text_content() or '').strip()
                if any(t in msg for t in duplicate_texts):
                    print('⚠️ พบแจ้งเตือนเอกสารซ้ำ (แดง) ก่อนอัปโหลด')
                    if getattr(self, 'latest_created_file_path', None):
                        moved_to = self.file_manager.move_file_to_duplicate_folder(self.latest_created_file_path)
                        if moved_to:
                            print(f"✅ ย้ายไฟล์ไปยัง 'เอกสารซ้ำรอตรวจ': {moved_to}")
                        else:
                            print('❌ ย้ายไฟล์ไปยังโฟลเดอร์เอกสารซ้ำรอตรวจไม่สำเร็จ')
                    else:
                        print('⚠️ ไม่มีพาธไฟล์ล่าสุดให้ย้าย')
                    return True
            # เผื่อบางระบบแจ้งในกรอบเขียวด้วยข้อความเดียวกัน
            green = self.page.locator('//*[@id="dvgreenalert"]')
            if green.count() > 0 and green.first.is_visible():
                try:
                    lb = self.page.locator('//*[@id="lbgreenalert"]')
                    msg = (lb.first.text_content() or '').strip() if lb.count() > 0 else (green.first.text_content() or '').strip()
                except Exception:
                    msg = (green.first.text_content() or '').strip()
                if any(t in msg for t in duplicate_texts):
                    print('⚠️ พบแจ้งเตือนเอกสารซ้ำ (เขียว) ก่อนอัปโหลด')
                    if getattr(self, 'latest_created_file_path', None):
                        moved_to = self.file_manager.move_file_to_duplicate_folder(self.latest_created_file_path)
                        if moved_to:
                            print(f"✅ ย้ายไฟล์ไปยัง 'เอกสารซ้ำรอตรวจ': {moved_to}")
                        else:
                            print('❌ ย้ายไฟล์ไปยังโฟลเดอร์เอกสารซ้ำรอตรวจไม่สำเร็จ')
                    else:
                        print('⚠️ ไม่มีพาธไฟล์ล่าสุดให้ย้าย')
                    return True
        except Exception as e:
            print(f"⚠️ ตรวจแจ้งเตือนเอกสารซ้ำก่อนอัปโหลดล้มเหลว: {e}")
        return False

    def wait_for_save_result(self, timeout: int = 20) -> str:
        """รอผลการกดบันทึก/ยืนยัน: คืนค่า 'approved' | 'duplicate' | 'timeout'"""
        try:
            start_time = time.time()
            print(f"⏳ เริ่มรอผลบันทึก (timeout: {timeout} วินาที)...")
            while time.time() - start_time < timeout:
                # เช็คกรอบแดง: เอกสารซ้ำ
                try:
                    red = self.page.locator('//*[@id="dvredalert"]')
                    if red.count() > 0 and red.first.is_visible():
                        try:
                            lb = self.page.locator('//*[@id="lbredalert"]')
                            msg = (lb.first.text_content() or '').strip() if lb.count() > 0 else (red.first.text_content() or '').strip()
                        except Exception:
                            msg = (red.first.text_content() or '').strip()
                        if 'เลขที่ใบกำกับภาษีอ้างอิงนี้สำหรับผู้ติดต่อนี้เคยถูกใช้งานแล้ว' in msg or 'ผู้ติดต่อนี้เคยถูกใช้งานแล้ว' in msg:
                            print('⚠️ ผลบันทึก: เอกสารซ้ำ (แดง)')
                            return 'duplicate'
                        if 'โปรดกรอกข้อมูลในช่อง' in msg:
                            print('⚠️ แจ้งเตือน: โปรดกรอกข้อมูลในช่อง → กรอกข้อมูลทั้งหมดใหม่อีกครั้ง')
                            if getattr(self, '_current_pdf_data_for_retry', None) and self._refill_attempt_count < 2:
                                try:
                                    self._refill_attempt_count += 1
                                    # รีหน้าแล้วกรอกใหม่ทั้งชุด
                                    self.refresh_express_page()
                                    self.fill_form_data(self._current_pdf_data_for_retry)
                                    # หลังกรอกใหม่ จะยังคงวนในลูปรอผลต่อ
                                    continue
                                except Exception as _:
                                    print('⚠️ รีฟิลไม่สำเร็จ จะรอตรวจผลต่อ')
                            else:
                                print('⚠️ ข้ามการรีฟิล (ไม่มีข้อมูล หรือพยายามเกินกำหนด)')
                except Exception:
                    pass

                # เช็คกรอบเขียว: อนุมัติบันทึกรายจ่าย ... สำเร็จ
                try:
                    green = self.page.locator('//*[@id="dvgreenalert"]')
                    if green.count() > 0 and green.first.is_visible():
                        try:
                            lb = self.page.locator('//*[@id="lbgreenalert"]')
                            msg = (lb.first.text_content() or '').strip() if lb.count() > 0 else (green.first.text_content() or '').strip()
                        except Exception:
                            msg = (green.first.text_content() or '').strip()
                        if ('อนุมัติบันทึกรายจ่าย' in msg and 'สำเร็จ' in msg) or ('Approved expense' in msg):
                            print('✅ ผลบันทึก: อนุมัติสำเร็จ')
                            return 'approved'
                except Exception:
                    pass

                # ตรวจสอบว่าหน้าเว็บยังโหลดอยู่หรือไม่
                try:
                    # ตรวจสอบว่ามี loading indicator หรือไม่
                    loading = self.page.locator('[class*="loading"], [class*="spinner"], [id*="loading"]')
                    if loading.count() > 0 and loading.first.is_visible():
                        print(f"⏳ หน้าเว็บกำลังโหลด...")
                    
                    # ตรวจสอบว่าหน้าเว็บยังตอบสนองหรือไม่
                    try:
                        # ลองหาองค์ประกอบพื้นฐานของหน้าเว็บ
                        basic_elements = [
                            '//*[@id="iptcontactname"]',
                            '//*[@id="iptaccountcode1"]',
                            '//*[@id="iptdate"]'
                        ]
                        
                        found_basic = False
                        for selector in basic_elements:
                            try:
                                element = self.page.locator(selector)
                                if element.count() > 0:
                                    found_basic = True
                                    break
                            except Exception:
                                pass
                        
                        if not found_basic:
                            print(f"⚠️ หน้าเว็บอาจไม่ตอบสนอง - ไม่พบองค์ประกอบพื้นฐาน")
                    except Exception:
                        pass
                except Exception:
                    pass

                # แสดงความคืบหน้า
                elapsed = int(time.time() - start_time)
                if elapsed % 3 == 0:  # แสดงทุก 3 วินาที
                    print(f"⏳ รอผลบันทึก... ({elapsed}/{timeout} วินาที)")
                
                time.sleep(0.3)
            
            print('⌛ ผลบันทึก: timeout (ไม่พบ alert box)')
            return 'timeout'
        except Exception as e:
            print(f"⚠️ ตรวจผลบันทึกล้มเหลว: {e}")
            return 'timeout'

    def check_and_fix_vat_value(self, expected_vat_text: str) -> bool:
        """ตรวจสอบยอดภาษีมูลค่าเพิ่มบนหน้ารวม และแก้ไขถ้าไม่ตรงกับค่าที่คาดหวัง
        expected_vat_text: ข้อความตัวเลขจาก pdf_data['vat_value'] เช่น '324.29'
        คืนค่า True ถ้าถูกต้องแล้วหรือแก้ไขสำเร็จ
        """
        try:
            # ดึงตัวเลขจาก expected
            try:
                expected_val = float(re.sub(r"[^0-9\.]+", "", expected_vat_text).replace(",", "")) if expected_vat_text else None
            except Exception:
                expected_val = None
            if expected_val is None:
                print("⚠️ ไม่มีค่า VAT ที่คาดหวัง ไม่ทำการตรวจสอบ")
                return True

            # 0) เลื่อนลงไปด้านล่างเพื่อดูส่วนสรุป VAT ให้แน่ใจว่า element อยู่ในวิวนักพัฒนาก่อนอ่านค่า
            try:
                self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(0.2)
            except Exception:
                pass

            # อ่าน VAT ที่แสดงบนหน้า (ใช้ selector หลายแบบเพื่อความทนทาน)
            def _select_vat_locator():
                candidates = [
                    'p[data-cypress="transactionVatAmount"]',
                    '//*[@data-cypress="transactionVatAmount"]',
                    'xpath=//p[@data-cypress="transactionVatAmount"]',
                    'css=[data-cypress="transactionVatAmount"]',
                    'xpath=//p[contains(normalize-space(.), "ภาษีมูลค่าเพิ่ม")]/following-sibling::p[1]',
                    'xpath=//div[@name="fromCurrencyBox"]//div[contains(@class, "subtotal")]/p[2]',
                    '//*[@id="content"]/div[6]/div[1]/div[3]/div[7]/div[2]/div[2]/div[3]/p[2]',
                ]
                for sel in candidates:
                    try:
                        loc = self.page.locator(sel)
                        if loc.count() > 0:
                            return loc
                    except Exception:
                        pass
                return None

            display_loc = _select_vat_locator()
            if not display_loc or display_loc.count() == 0:
                print("⚠️ ไม่พบตำแหน่งแสดง VAT บนหน้า (ลองใช้ data-cypress แล้ว)")
                return True
            display_text = (display_loc.first.text_content() or '').strip()
            try:
                display_val = float(re.sub(r"[^0-9\.]+", "", display_text).replace(",", "")) if display_text else None
            except Exception:
                display_val = None
            print(f"📊 ตรวจ VAT: คาดหวัง {expected_val} | หน้าจอ {display_val}")

            if display_val is not None and abs(display_val - expected_val) < 0.001:
                print("✅ VAT บนหน้าตรงกับข้อมูล ไม่ต้องแก้ไข")
                return True

            print("⚠️ VAT ไม่ตรง เริ่มกระบวนการแก้ไข")

            for attempt in range(1):
                print("🛠️ แก้ไข VAT: เตรียมกรอกค่าใหม่ 2 รอบ แล้วบันทึกครั้งเดียว")

                # 1) เลื่อนกลับขึ้นบนสุดเพื่อเข้าถึงปุ่ม 'ตัวเลือก' และหน่วง 0.8 วิ (ให้ element เสถียร)
                try:
                    self.page.evaluate('window.scrollTo(0, 0)')
                except Exception:
                    pass
                time.sleep(0.8)

                # 2) คลิกปุ่ม 'ตัวเลือก' แล้วเปิดเมนู
                options_btn_xpath = '//*[@id="content"]/div[6]/div[1]/div[3]/div[1]/div/div[3]'
                options_menu_xpath = '//*[@id="content"]/div[6]/div[1]/div[3]/div[1]/div/div[3]/div'
                try:
                    candidates_btn = [
                        options_btn_xpath,
                        "css=div.ui.button.dropdown.option-button.button-blue",
                        "css=div.option-button.button-blue",
                        "css=div.option-button",
                        "css=div.ui.button.dropdown:has-text('ตัวเลือก')",
                        "text=ตัวเลือก"
                    ]
                    options_btn = None
                    for sel in candidates_btn:
                        try:
                            loc = self.page.locator(sel)
                            if loc.count() > 0:
                                options_btn = loc.first
                                break
                        except Exception:
                            continue
                    if not options_btn:
                        print("⚠️ ไม่พบปุ่มตัวเลือก (options)")
                        return False
                    try:
                        options_btn.scroll_into_view_if_needed()
                        time.sleep(0.2)
                    except Exception:
                        pass
                    options_btn.click()
                    menu_visible = False
                    try:
                        self.page.locator("css=div.menu.transition:not(.hidden)").first.wait_for(state='visible', timeout=3000)
                        menu_visible = True
                    except Exception:
                        try:
                            self.page.wait_for_selector(options_menu_xpath, timeout=3000)
                            menu_visible = True
                        except Exception:
                            time.sleep(0.5)
                    if not menu_visible:
                        try:
                            options_btn.click()
                            time.sleep(0.5)
                        except Exception:
                            pass
                except Exception:
                    print("⚠️ คลิกตัวเลือกไม่สำเร็จ")
                    return False

                # 3) คลิก 'แก้ไข'
                try:
                    edit_item = self.page.locator('text=แก้ไข')
                    if edit_item.count() == 0:
                        edit_item = self.page.locator('//*[@id="content"]/div[6]/div[1]/div[3]/div[1]/div/div[3]/div/div[2]')
                    if edit_item.count() > 0:
                        edit_item.first.click()
                    else:
                        print("⚠️ ไม่พบเมนู 'แก้ไข'")
                        return False
                except Exception:
                    print("⚠️ คลิก 'แก้ไข' ไม่สำเร็จ")
                    return False

                # 4) รอโหลดหน้าแก้ไข
                try:
                    self.page.wait_for_load_state('domcontentloaded', timeout=7000)
                except Exception:
                    pass
                time.sleep(0.3)

                # 5) เลื่อนลงไปยังช่อง VAT
                try:
                    self.page.evaluate('window.scrollBy(0, 800)')
                except Exception:
                    pass
                try:
                    self.page.wait_for_selector('//*[@id="iptTransactionCESummaryVat"]', timeout=5000)
                except Exception:
                    time.sleep(0.2)

                # 6) กรอก VAT ใหม่
                vat_input = None
                for sel in [
                    '//*[@id="iptTransactionCESummaryVat"]',
                    'css=#iptTransactionCESummaryVat',
                    'css=input#iptTransactionCESummaryVat',
                    'css=input[name="iptTransactionCESummaryVat"]',
                    'xpath=//input[contains(@id, "TransactionCESummaryVat") or contains(@name, "TransactionCESummaryVat")]'
                ]:
                    try:
                        loc = self.page.locator(sel)
                        if loc.count() > 0:
                            vat_input = loc
                            break
                    except Exception:
                        continue
                if vat_input and vat_input.count() > 0:
                    for fill_round in range(2):
                        try:
                            vat_input.first.fill("")
                            vat_input.first.fill(f"{expected_val:.2f}")
                        except Exception:
                            try:
                                vat_input.first.click()
                                vat_input.first.fill("")
                                vat_input.first.fill(f"{expected_val:.2f}")
                            except Exception:
                                pass
                        print(f"✏️ อัปเดต VAT รอบที่ {fill_round+1}/2 เป็น {expected_val:.2f}")
                        try:
                            self.page.evaluate(
                                "(sel)=>{ const el = document.querySelector(sel); if(!el) return; el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true})); el.blur && el.blur(); }",
                                '#iptTransactionCESummaryVat'
                            )
                        except Exception:
                            pass
                        try:
                            self.page.evaluate("()=>{ if (document.activeElement && document.activeElement.blur) { document.activeElement.blur(); } }")
                        except Exception:
                            pass
                        time.sleep(1.0)
                        try:
                            loading = self.page.locator('//*[@id="tagTransactionLoading"], #tagTransactionLoading')
                            if loading.count() > 0:
                                try:
                                    loading.first.wait_for(state='visible', timeout=1500)
                                except Exception:
                                    pass
                                try:
                                    loading.first.wait_for(state='hidden', timeout=6000)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                else:
                    print("⚠️ ไม่พบช่องกรอก VAT (iptTransactionCESummaryVat/fallback)")
                    return False

                # 7) คลิกบันทึก/แก้ไข ตาม XPaths ที่ระบุ
                clicked_save = False
                click_source = None
                try:
                    # อัปเดตตำแหน่งตามที่ให้มา และระบุเป็น xpath= เพื่อหลีกเลี่ยงการตีความเป็น CSS
                    container_xpath = 'xpath=//*[@id="content"]/div[6]/div[1]/div[6]/div/div[2]'
                    abs_save_xpath = 'xpath=//*[@id="content"]/div[6]/div[1]/div[6]/div/div[2]/div[1]'
                    try:
                        self.page.evaluate('document.querySelector("body").scrollTop = document.body.scrollHeight;')
                    except Exception:
                        try:
                            self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        except Exception:
                            pass
                    try:
                        self.page.wait_for_selector(container_xpath, timeout=5000)
                    except Exception:
                        pass
                    try:
                        container_loc = self.page.locator(container_xpath)
                        if container_loc.count() > 0:
                            try:
                                container_loc.first.scroll_into_view_if_needed()
                                container_loc.first.wait_for(state='visible', timeout=2000)
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        self.page.wait_for_selector(abs_save_xpath, timeout=4000)
                    except Exception:
                        pass
                    abs_btn = self.page.locator(abs_save_xpath)
                    if abs_btn.count() > 0:
                        print("🔘 พบปุ่มแก้ไขแบบ absolute กำลังกด…")
                        try:
                            abs_btn.first.scroll_into_view_if_needed()
                        except Exception:
                            pass
                        # 1) ปกติ
                        try:
                            abs_btn.first.click()
                            clicked_save = True
                            click_source = 'absolute_xpath.click()'
                        except Exception as e1:
                            print(f"   ↪︎ ปุ่ม absolute.click() ล้มเหลว: {e1}")
                            # 2) force click
                            try:
                                abs_btn.first.click(force=True)
                                clicked_save = True
                                click_source = 'absolute_xpath.click(force)'
                            except Exception as e2:
                                print(f"   ↪︎ ปุ่ม absolute.click(force) ล้มเหลว: {e2}")
                                # 3) JS click
                                try:
                                    self.page.evaluate("el=>el.click()", abs_btn.first)
                                    clicked_save = True
                                    click_source = 'absolute_xpath.js_click'
                                except Exception as e3:
                                    print(f"   ↪︎ ปุ่ม absolute.js_click ล้มเหลว: {e3}")
                                    # 4) mouse click by bounding box
                                    try:
                                        box = abs_btn.first.bounding_box()
                                        if box:
                                            self.page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                            clicked_save = True
                                            click_source = 'absolute_xpath.mouse_click'
                                    except Exception as e4:
                                        print(f"   ↪︎ ปุ่ม absolute.mouse_click ล้มเหลว: {e4}")
                                        # 5) focus + Enter
                                        try:
                                            abs_btn.first.focus()
                                            self.page.keyboard.press('Enter')
                                            clicked_save = True
                                            click_source = 'absolute_xpath.focus+Enter'
                                        except Exception as e5:
                                            print(f"   ↪︎ ปุ่ม absolute.focus+Enter ล้มเหลว: {e5}")
                                            # 6) submit form
                                            try:
                                                self.page.evaluate("el=>{const f=el.closest('form'); if(f){(f.requestSubmit||f.submit).call(f)} }", abs_btn.first)
                                                clicked_save = True
                                                click_source = 'absolute_xpath.form_submit'
                                            except Exception as e6:
                                                print(f"   ↪︎ ปุ่ม absolute.form_submit ล้มเหลว: {e6}")
                    if not clicked_save:
                        # ให้ความสำคัญกับปุ่ม 'แก้ไข' ที่มี onclick=editAndApproveInvoice
                        special_targets = [
                            'xpath=//div[contains(@class, "ui button button-blue") and contains(@onclick, "editAndApproveInvoice(")]',
                            'css=div.ui.button.button-blue[onclick*="editAndApproveInvoice("]',
                            'text=แก้ไข'
                        ]
                        for sel in special_targets:
                            sp = self.page.locator(sel)
                            if sp.count() > 0:
                                print(f"🔘 พบปุ่มแก้ไขแบบ onclick ({sel}) กำลังกด…")
                                try:
                                    sp.first.scroll_into_view_if_needed()
                                    sp.first.wait_for(state='visible', timeout=3000)
                                except Exception:
                                    pass
                                try:
                                    sp.first.click()
                                    clicked_save = True
                                    click_source = f'{sel}.click()'
                                    break
                                except Exception as e1:
                                    print(f"   ↪︎ {sel}.click() ล้มเหลว: {e1}")
                                    try:
                                        sp.first.click(force=True)
                                        clicked_save = True
                                        click_source = f'{sel}.click(force)'
                                        break
                                    except Exception as e2:
                                        print(f"   ↪︎ {sel}.click(force) ล้มเหลว: {e2}")
                                        try:
                                            self.page.evaluate("() => { if (typeof window.editAndApproveInvoice === 'function') { window.editAndApproveInvoice(1, 3, true); } }")
                                            clicked_save = True
                                            click_source = 'call_editAndApproveInvoice()'
                                            break
                                        except Exception as e3:
                                            print(f"   ↪︎ call_editAndApproveInvoice() ล้มเหลว: {e3}")
                        if not clicked_save:
                            fallback_sels = [
                                'text=บันทึก',
                                'button:has-text("บันทึก")',
                                'css=button[type="submit"]',
                                'text=แก้ไข',
                                'css=div.ui.button.button-blue',
                                'xpath=//div[contains(@class, "ui button button-blue") and contains(normalize-space(.), "แก้ไข")]'
                            ]
                            for sel in fallback_sels:
                                btn = self.page.locator(sel)
                                if btn.count() > 0:
                                    print(f"🔘 พบปุ่ม ({sel}) กำลังกด…")
                                    try:
                                        btn.first.scroll_into_view_if_needed()
                                        time.sleep(0.2)
                                    except Exception:
                                        pass
                                    try:
                                        btn.first.click()
                                        clicked_save = True
                                        click_source = f'{sel}.click()'
                                        break
                                    except Exception as e1:
                                        print(f"   ↪︎ {sel}.click() ล้มเหลว: {e1}")
                                        try:
                                            btn.first.click(force=True)
                                            clicked_save = True
                                            click_source = f'{sel}.click(force)'
                                            break
                                        except Exception as e2:
                                            print(f"   ↪︎ {sel}.click(force) ล้มเหลว: {e2}")
                                            try:
                                                self.page.evaluate("el=>el.click()", btn.first)
                                                clicked_save = True
                                                click_source = f'{sel}.js_click'
                                                break
                                            except Exception as e3:
                                                print(f"   ↪︎ {sel}.js_click ล้มเหลว: {e3}")
                                                try:
                                                    box = btn.first.bounding_box()
                                                    if box:
                                                        self.page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                                        clicked_save = True
                                                        click_source = f'{sel}.mouse_click'
                                                        break
                                                except Exception as e4:
                                                    print(f"   ↪︎ {sel}.mouse_click ล้มเหลว: {e4}")
                    if clicked_save:
                        print(f"💾 สั่งคลิกปุ่มแก้ไข/บันทึกแล้ว (source={click_source})")
                    else:
                        print("🚫 ไม่พบปุ่มแก้ไข/บันทึกให้คลิก (ตรวจทั้ง absolute, onclick และ fallback แล้ว)")
                        return False
                except Exception as e:
                    print(f"⚠️ เกิดข้อผิดพลาดระหว่างคลิกปุ่มแก้ไข/บันทึก: {e}")
                    return False

                # 8) รอให้หน้าโหลดเสร็จ
                try:
                    self.page.wait_for_load_state('networkidle', timeout=8000)
                except Exception:
                    try:
                        self.page.wait_for_load_state('domcontentloaded', timeout=5000)
                    except Exception:
                        pass
                time.sleep(0.6)

                # 9) เลื่อนลงไปยังส่วนสรุปอีกครั้งและตรวจซ้ำ
                try:
                    self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    time.sleep(0.2)
                except Exception:
                    pass
                display_loc2 = _select_vat_locator()
                display_text2 = (display_loc2.first.text_content() or '').strip() if display_loc2 and display_loc2.count() > 0 else ''
                try:
                    display_val2 = float(re.sub(r"[^0-9\.]+", "", display_text2).replace(",", "")) if display_text2 else None
                except Exception:
                    display_val2 = None
                if display_val2 is not None and abs(display_val2 - expected_val) < 0.001:
                    print("✅ VAT หลังแก้ไขตรงตามคาด")
                    return True
                print("⚠️ VAT หลังแก้ไขยังไม่ตรง ลองอีกครั้งถ้ายังมีรอบเหลือ")

            # ถ้าลองครบ 2 รอบแล้วยังไม่ตรง
            return False
        except Exception as e:
            print(f"❌ ตรวจ/แก้ไข VAT ล้มเหลว: {e}")
            return False

    def refresh_express_page(self):
        """รีหน้า Express เพื่อเริ่มกรอกใหม่ให้สะอาด"""
        try:
            if self.express_link:
                print(f"🔄 รีหน้า Express: {self.express_link}")
                self.page.goto(self.express_link, timeout=10000)
                try:
                    self.page.wait_for_load_state('domcontentloaded', timeout=5000)
                except Exception:
                    pass
                time.sleep(0.3)
                return True
            print("⚠️ ไม่มี express_link สำหรับรีหน้า")
            return False
        except Exception as e:
            print(f"⚠️ รีหน้า Express ล้มเหลว: {e}")
            return False
