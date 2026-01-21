import time
from pathlib import Path
from typing import Dict, List
from config import Config
from file_manager import FileManager
from pdf_reader import PDFReader
from web_automation import WebAutomation
from data_processor import DataProcessor
from logger import BotLogger

class MainBot:
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(Config.BASE_FOLDER)
        self.file_manager = FileManager(self.base_path)
        self.pdf_reader = PDFReader()
        self.web_automation = WebAutomation()
        self.data_processor = DataProcessor()
        self.logger = BotLogger()
        
        # สถานะการทำงาน
        self.is_running = False
        self.current_folder_code = None
        
    def start_bot(self):
        """เริ่มการทำงานของบอท"""
        try:
            self.is_running = True
            self.logger.log_system_status("SUCCESS", "Bot started successfully")
            
            print("=== เริ่มการทำงานของระบบบอท ===")
            
            # ขั้นตอนที่ 1: อ่านโฟลเดอร์หลัก
            main_folders = self.file_manager.get_main_folders()
            if not main_folders:
                self.logger.log_system_status("ERROR", "ไม่พบโฟลเดอร์หลัก A.โฟร์เดอร์หลัก, AA.โฟรเดอร์หลัก, AAA.โฟรเดอร์หลัก")
                return False
            
            print(f"พบโฟลเดอร์หลัก: {[f.name for f in main_folders]}")
            print("โครงสร้างโฟลเดอร์:")
            for folder in main_folders:
                print(f"  📁 {folder.name}")
                print(f"    └── 📂 {Config.CUSTOMER_FOLDER}")
                print(f"        └── ⚙️ {Config.AUTOMATION_FOLDER}")
            
            # ขั้นตอนที่ 2: ประมวลผลแต่ละโฟลเดอร์หลัก
            for main_folder in main_folders:
                if not self.is_running:
                    break
                    
                print(f"\n--- ประมวลผลโฟลเดอร์: {main_folder.name} ---")
                self.process_main_folder(main_folder)
            
            # ขั้นตอนที่ 3: สร้างรายงาน
            self.create_final_reports()
            
            print("\n=== การทำงานของระบบบอทเสร็จสิ้น ===")
            self.logger.log_system_status("SUCCESS", "Bot completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Error in main bot execution: {e}"
            print(error_msg)
            self.logger.log_system_status("ERROR", error_msg)
            return False
        
        finally:
            self.is_running = False
            self.web_automation.close_driver()
    
    def process_main_folder(self, main_folder: Path):
        """ประมวลผลโฟลเดอร์หลัก"""
        try:
            # หาโฟลเดอร์ลูกค้าและระบบอัตโนมัติ
            automation_folders = self.file_manager.get_customer_automation_folders(main_folder)
            
            if not automation_folders:
                print(f"ไม่พบโฟลเดอร์ระบบอัตโนมัติใน {main_folder.name}")
                return
            
            # ประมวลผลแต่ละโฟลเดอร์ระบบอัตโนมัติ
            for automation_folder in automation_folders:
                if not self.is_running:
                    break
                    
                print(f"ประมวลผลโฟลเดอร์: {automation_folder}")
                self.process_automation_folder(automation_folder)
                
        except Exception as e:
            error_msg = f"Error processing main folder {main_folder.name}: {e}"
            print(error_msg)
            self.logger.log_system_status("ERROR", error_msg)
    
    def process_automation_folder(self, automation_folder: Path):
        """ประมวลผลโฟลเดอร์ระบบอัตโนมัติ"""
        try:
            # ดึงรหัสโฟลเดอร์
            folder_code = self.file_manager.get_folder_code_from_path(automation_folder)
            if not folder_code:
                print("ไม่สามารถดึงรหัสโฟลเดอร์ได้")
                return
            
            self.current_folder_code = folder_code
            print(f"รหัสโฟลเดอร์: {folder_code}")
            
            # ขั้นตอนที่ 3: อ่านไฟล์ PDF
            pdf_files = self.file_manager.get_pdf_files(automation_folder)
            if not pdf_files:
                print("ไม่พบไฟล์ PDF")
                return
            
            print(f"พบไฟล์ PDF: {len(pdf_files)} ไฟล์")
            
            # ขั้นตอนที่ 4: อ่านข้อมูลจากไฟล์ JSON config
            json_config = self.file_manager.read_json_config(folder_code)
            if not json_config:
                print("ไม่พบไฟล์ JSON config")
                return
            
            # ขั้นตอนที่ 5: อ่านข้อมูลจากไฟล์ folder_settings
            folder_settings = self.file_manager.read_folder_settings()
            
            # ขั้นตอนที่ 6: ประมวลผลไฟล์ PDF
            processed_pdfs = self.pdf_reader.process_pdf_batch(pdf_files, json_config)
            
            # เพิ่มข้อมูลรหัสโฟลเดอร์
            for pdf_data in processed_pdfs:
                pdf_data['folder_code'] = folder_code
            
            # ขั้นตอนที่ 7: ประมวลผลข้อมูลบริษัท
            processed_data = []
            for pdf_data in processed_pdfs:
                processed_item = self.data_processor.process_company_data(pdf_data, folder_settings)
                processed_data.append(processed_item)
                
                # บันทึก log
                self.logger.log_pdf_processing(
                    pdf_data.get('filename', 'Unknown'),
                    pdf_data.get('company_name', 'Unknown'),
                    'SUCCESS',
                    f"Processed successfully - Group: {processed_item.get('group', 'unknown')}"
                )
            
            # ขั้นตอนที่ 8: ทำงานกับเว็บไซต์
            if processed_data:
                self.process_web_automation(processed_data, folder_code)
            
            # ขั้นตอนที่ 9: จัดระเบียบไฟล์
            output_path = Path("output") / folder_code
            organized_files = self.data_processor.organize_files_by_group(
                pdf_files, processed_data, output_path
            )
            
            # ขั้นตอนที่ 10: ส่งออกข้อมูล
            self.data_processor.export_processing_data(processed_data, output_path)
            
            print(f"ประมวลผลโฟลเดอร์ {folder_code} เสร็จสิ้น")
            
        except Exception as e:
            error_msg = f"Error processing automation folder: {e}"
            print(error_msg)
            self.logger.log_system_status("ERROR", error_msg)
    
    def process_web_automation(self, processed_data: List[Dict], folder_code: str):
        """ประมวลผลการทำงานกับเว็บไซต์"""
        try:
            print("เริ่มการทำงานกับเว็บไซต์...")
            
            # ขั้นตอนที่ 7: อ่านข้อมูล login
            credentials = self.file_manager.read_login_credentials(folder_code)
            if not credentials:
                print("ไม่พบข้อมูล login")
                return
            
            # ขั้นตอนที่ 8: ตั้งค่า WebDriver
            if not self.web_automation.setup_driver():
                print("ไม่สามารถตั้งค่า WebDriver ได้")
                return
            
            # ขั้นตอนที่ 9: ล็อกอิน
            if not self.web_automation.login_to_peak_engine(credentials):
                print("ไม่สามารถล็อกอินได้")
                return
            
            self.logger.log_web_automation("Login", "SUCCESS", f"Logged in successfully to {folder_code}")
            
            # ขั้นตอนที่ 10: ไปยัง Link Company
            company_link = credentials.get('Link company')
            if company_link:
                if self.web_automation.navigate_to_company_link(company_link):
                    self.logger.log_web_automation("Company Link", "SUCCESS", f"Navigated to company link for {folder_code}")
                else:
                    self.logger.log_web_automation("Company Link", "ERROR", f"Failed to navigate to company link for {folder_code}")
            
            # ขั้นตอนที่ 11: ไปยัง Link Express
            express_link = credentials.get('Link Express')
            if express_link:
                if self.web_automation.navigate_to_express_link(express_link):
                    self.logger.log_web_automation("Express Link", "SUCCESS", f"Navigated to express link for {folder_code}")
                else:
                    self.logger.log_web_automation("Express Link", "ERROR", f"Failed to navigate to express link for {folder_code}")
            
            # ขั้นตอนที่ 12: ประมวลผลแต่ละไฟล์
            for pdf_data in processed_data:
                if not self.is_running:
                    break
                    
                print(f"ประมวลผลไฟล์: {pdf_data.get('filename')}")
                
                # กรอกข้อมูลในฟอร์ม
                if self.web_automation.fill_form_data(pdf_data):
                    self.logger.log_web_automation("Form Filling", "SUCCESS", f"Form filled for {pdf_data.get('filename')}")
                else:
                    self.logger.log_web_automation("Form Filling", "ERROR", f"Form filling failed for {pdf_data.get('filename')}")
                
                # อัปโหลดไฟล์
                if self.web_automation.upload_file(str(pdf_data.get('filename', ''))):
                    self.logger.log_web_automation("File Upload", "SUCCESS", f"File uploaded: {pdf_data.get('filename')}")
                else:
                    self.logger.log_web_automation("File Upload", "ERROR", f"File upload failed: {pdf_data.get('filename')}")
                
                # รอการประมวลผล
                if self.web_automation.wait_for_processing():
                    self.logger.log_web_automation("Processing", "SUCCESS", f"Processing completed for {pdf_data.get('filename')}")
                else:
                    self.logger.log_web_automation("Processing", "WARNING", f"Processing timeout for {pdf_data.get('filename')}")
                
                # รอสักครู่ก่อนไฟล์ถัดไป
                time.sleep(2)
            
        except Exception as e:
            error_msg = f"Error in web automation: {e}"
            print(error_msg)
            self.logger.log_web_automation("General", "ERROR", error_msg)
    
    def create_final_reports(self):
        """สร้างรายงานสุดท้าย"""
        try:
            print("สร้างรายงาน...")
            
            # สร้างรายงาน Excel
            if self.logger.create_excel_report():
                print("รายงาน Excel สร้างเสร็จ")
            
            # สร้างรายงานข้อความ
            if self.logger.create_text_report():
                print("รายงานข้อความสร้างเสร็จ")
            
            # แสดงสถิติสรุป
            stats = self.logger.get_summary_stats()
            if stats:
                print(f"\n=== สรุปการทำงาน ===")
                print(f"การทำงานทั้งหมด: {stats['total_actions']}")
                print(f"สำเร็จ: {stats['success_count']}")
                print(f"ผิดพลาด: {stats['error_count']}")
                print(f"อัตราความสำเร็จ: {stats['success_rate']:.1f}%")
            
        except Exception as e:
            error_msg = f"Error creating final reports: {e}"
            print(error_msg)
            self.logger.log_system_status("ERROR", error_msg)
    
    def stop_bot(self):
        """หยุดการทำงานของบอท"""
        print("กำลังหยุดการทำงานของบอท...")
        self.is_running = False
        self.web_automation.close_driver()
        self.logger.log_system_status("INFO", "Bot stopped by user")
    
    def get_status(self) -> Dict:
        """ดึงสถานะปัจจุบันของบอท"""
        return {
            'is_running': self.is_running,
            'current_folder_code': self.current_folder_code,
            'log_stats': self.logger.get_summary_stats()
        }

def main():
    """ฟังก์ชันหลักสำหรับรันบอท"""
    try:
        # สร้างบอท
        bot = MainBot()
        
        # เริ่มการทำงาน
        success = bot.start_bot()
        
        if success:
            print("บอททำงานเสร็จสิ้น")
        else:
            print("บอททำงานผิดพลาด")
            
    except KeyboardInterrupt:
        print("\nผู้ใช้หยุดการทำงาน")
        if 'bot' in locals():
            bot.stop_bot()
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    main()
