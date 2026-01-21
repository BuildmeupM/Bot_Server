#!/usr/bin/env python3
"""
BotV3 Main System - Multi-Folder Scanner & Processor
สแกนหลายโฟลเดอร์หลักและประมวลผล PDF ในแต่ละโฟลเดอร์ย่อย
"""

import sys
from pathlib import Path
from typing import List, Dict
import time
from datetime import datetime

# Import modules
from config import Config
from pdf_reader import PDFReader
from web_automation_playwright import WebAutomationPlaywright
from file_manager import FileManager

# Global variable to store system state reference
_system_state = None

def set_system_state(state_dict):
    """Set global system state reference"""
    global _system_state
    _system_state = state_dict

def update_system_status(folder=None, file=None, step=None):
    """Update system status in global state"""
    global _system_state
    if _system_state:
        if folder is not None:
            _system_state['current_folder'] = folder
        if file is not None:
            _system_state['current_file'] = file
        if step is not None:
            _system_state['current_step'] = step


class MainSystemOrchestrator:
    """จัดการการสแกนและประมวลผลหลายโฟลเดอร์หลัก"""
    
    def __init__(self, base_path: str = "V:/A.โฟร์เดอร์หลัก"):
        """
        Initialize orchestrator
        
        Args:
            base_path: พาธฐานสำหรับการสแกน (ค่าเริ่มต้นคือ V:/A.โฟร์เดอร์หลัก)
        """
        self.base_path = Path(base_path)
        self.pdf_reader = PDFReader()
        self.file_manager = FileManager()
        self.results = []
        
        print(f"🤖 เริ่มต้นระบบหลัก BotV3")
        print(f"📂 พาธฐาน: {self.base_path}")
    
    def find_main_folders(self, root_path: Path) -> List[Path]:
        """
        ค้นหาโฟลเดอร์หลักทั้งหมดที่ตรงกับรูปแบบ (Build*)
        
        Args:
            root_path: โฟลเดอร์รากที่จะเริ่มค้นหา (เช่น V:/A.โฟร์เดอร์หลัก)
            
        Returns:
            รายการโฟลเดอร์หลักทั้งหมด (Build*)
        """
        main_folders = []
        
        if not root_path.exists():
            print(f"⚠️ ไม่พบโฟลเดอร์: {root_path}")
            return main_folders
        
        # สแกนโฟลเดอร์ Build* ในโฟลเดอร์รากโดยตรง
        for folder in root_path.glob("Build*"):
            if folder.is_dir():
                main_folders.append(folder)
                print(f"✅ พบโฟลเดอร์หลัก: {folder.name}")
        
        # ถ้าไม่พบ Build* ให้สแกนโฟลเดอร์ย่อยที่ขึ้นต้นด้วย A., AA., AAA.
        if not main_folders:
            patterns = ["A.*", "AA.*", "AAA.*"]
            
            for pattern in patterns:
                for subfolder in root_path.glob(pattern):
                    if not subfolder.is_dir():
                        continue
                    
                    # ข้ามโฟลเดอร์ที่อยู่ในรายการข้าม
                    if subfolder.name in Config.SKIP_FOLDERS:
                        print(f"⏭️ ข้ามโฟลเดอร์: {subfolder.name}")
                        continue
                    
                    # สแกนหา Build* ในโฟลเดอร์ย่อย
                    for folder in subfolder.glob("Build*"):
                        if folder.is_dir():
                            main_folders.append(folder)
                            print(f"✅ พบโฟลเดอร์หลัก: {folder.relative_to(root_path)}")
        
        return sorted(main_folders)
    
    def find_automation_folders(self, main_folder: Path) -> List[Path]:
        """
        ค้นหาโฟลเดอร์ 'ลูกค้า/ระบบอัตโนมัติ' ในโฟลเดอร์หลัก
        
        Args:
            main_folder: โฟลเดอร์หลักที่จะค้นหา
            
        Returns:
            รายการโฟลเดอร์ระบบอัตโนมัติทั้งหมด
        """
        automation_folders = []
        
        # ค้นหาโฟลเดอร์ "ลูกค้า" ในโฟลเดอร์หลัก
        customer_folders = list(main_folder.glob(f"*{Config.CUSTOMER_FOLDER}*"))
        
        for customer_folder in customer_folders:
            if not customer_folder.is_dir():
                continue
            
            # ค้นหาโฟลเดอร์ "ระบบอัตโนมัติ" ในโฟลเดอร์ลูกค้า
            automation_paths = list(customer_folder.glob(f"*{Config.AUTOMATION_FOLDER}*"))
            
            for auto_path in automation_paths:
                if auto_path.is_dir():
                    automation_folders.append(auto_path)
                    print(f"  📁 พบโฟลเดอร์อัตโนมัติ: {auto_path.relative_to(main_folder)}")
        
        return automation_folders
    
    def find_pdf_files_in_folder(self, folder: Path) -> List[Path]:
        """
        ค้นหาไฟล์ PDF ในโฟลเดอร์โดยตรง (ไม่เข้าโฟลเดอร์ย่อย)
        
        Args:
            folder: โฟลเดอร์ที่จะค้นหา (ระบบอัตโนมัติ)
            
        Returns:
            รายการไฟล์ PDF
        """
        pdf_files = []
        
        # ค้นหาเฉพาะไฟล์ PDF ในโฟลเดอร์โดยตรง (ไม่ recursive)
        for pdf_file in folder.glob("*.pdf"):
            if pdf_file.is_file():
                pdf_files.append(pdf_file)
        
        return sorted(pdf_files)
    
    def process_folder(self, automation_folder: Path, main_folder_name: str) -> Dict:
        """
        ประมวลผลโฟลเดอร์เดียว
        
        Args:
            automation_folder: โฟลเดอร์ระบบอัตโนมัติที่จะประมวลผล
            main_folder_name: ชื่อโฟลเดอร์หลัก (สำหรับรายงาน)
            
        Returns:
            ผลลัพธ์การประมวลผล
        """
        result = {
            "main_folder": main_folder_name,
            "automation_folder": str(automation_folder),
            "start_time": datetime.now(),
            "status": "pending",
            "pdf_count": 0,
            "success_count": 0,
            "error": None,
            "pdf_files_found": [],  # รายการไฟล์ PDF ที่พบ
            "pdf_files_read_success": [],  # รายการไฟล์ที่อ่านสำเร็จ
            "pdf_files_read_failed": []  # รายการไฟล์ที่อ่านไม่ได้
        }
        
        try:
            print(f"\n{'='*60}")
            print(f"📂 ประมวลผล: {automation_folder.relative_to(automation_folder.parent.parent.parent)}")
            print(f"{'='*60}")
            
            # ค้นหาไฟล์ PDF
            pdf_files = self.find_pdf_files_in_folder(automation_folder)
            result["pdf_count"] = len(pdf_files)
            result["pdf_files_found"] = [str(pdf_file.name) for pdf_file in pdf_files]
            
            # Update system status
            update_system_status(
                folder=str(automation_folder),
                step=f'กำลังอ่านไฟล์ PDF ({len(pdf_files)} ไฟล์)'
            )
            
            if not pdf_files:
                print("⚠️ ไม่พบไฟล์ PDF ในโฟลเดอร์นี้")
                result["status"] = "no_files"
                return result
            
            print(f"📄 พบไฟล์ PDF จำนวน: {len(pdf_files)} ไฟล์")
            print(f"📋 รายการไฟล์ที่พบ:")
            for i, pdf_file in enumerate(pdf_files, 1):
                print(f"   {i}. {pdf_file.name}")
            
            # อ่านและประมวลผล PDF
            print("\n🔍 เริ่มอ่าน PDF...")
            update_system_status(step='กำลังอ่านข้อมูล PDF')
            
            # อัปเดตสถานะไฟล์ที่กำลังอ่าน
            for i, pdf_file in enumerate(pdf_files):
                update_system_status(
                    file=f'กำลังอ่าน: {pdf_file.name} ({i+1}/{len(pdf_files)})',
                    step='กำลังอ่านข้อมูล PDF'
                )
                time.sleep(0.1)  # หน่วงเวลาเล็กน้อยเพื่อให้เห็นการอัปเดต
            
            pdf_data_list = self.pdf_reader.process_pdf_batch(
                pdf_files=pdf_files
            )
            
            # บันทึกรายการไฟล์ที่อ่านสำเร็จ
            result["pdf_files_read_success"] = [pdf_data.get('filename', 'ไม่ทราบชื่อ') for pdf_data in pdf_data_list if pdf_data]
            
            # คำนวณไฟล์ที่อ่านไม่ได้
            success_filenames = set(result["pdf_files_read_success"])
            all_filenames = set(result["pdf_files_found"])
            failed_filenames = all_filenames - success_filenames
            result["pdf_files_read_failed"] = list(failed_filenames)
            
            if not pdf_data_list:
                print("⚠️ ไม่มีไฟล์ที่อ่านสำเร็จ")
                result["status"] = "read_failed"
                return result
            
            print(f"✅ อ่านสำเร็จ: {len(pdf_data_list)} ไฟล์")
            print(f"📋 รายการไฟล์ที่อ่านสำเร็จ:")
            for i, pdf_data in enumerate(pdf_data_list, 1):
                filename = pdf_data.get('filename', 'ไม่ทราบชื่อ')
                company = pdf_data.get('company_name', 'ไม่ทราบบริษัท')
                print(f"   {i}. {filename} (บริษัท: {company})")
            
            if result["pdf_files_read_failed"]:
                print(f"❌ อ่านไม่ได้: {len(result['pdf_files_read_failed'])} ไฟล์")
                print(f"📋 รายการไฟล์ที่อ่านไม่ได้:")
                for i, filename in enumerate(result["pdf_files_read_failed"], 1):
                    print(f"   {i}. {filename}")
            
            # เริ่มระบบ Web Automation
            print("\n🌐 เริ่มระบบ Web Automation...")
            update_system_status(step='กำลังประมวลผล Web Automation')
            
            # อัปเดตสถานะไฟล์ที่กำลังประมวลผล
            for i, pdf_data in enumerate(pdf_data_list):
                if pdf_data and 'company_name' in pdf_data:
                    update_system_status(
                        file=f'กำลังประมวลผล: {pdf_data["company_name"]} ({i+1}/{len(pdf_data_list)})',
                        step='กำลังประมวลผล Web Automation'
                    )
                    time.sleep(0.1)  # หน่วงเวลาเล็กน้อยเพื่อให้เห็นการอัปเดต
            
            automation = WebAutomationPlaywright()
            
            success = automation.execute_peak_engine_workflow(
                pdf_data_list=pdf_data_list,
                main_folder=str(automation_folder)
            )
            
            if success:
                result["status"] = "success"
                result["success_count"] = len(pdf_data_list)
                print(f"✅ ประมวลผลสำเร็จ")
            else:
                result["status"] = "partial_success"
                print(f"⚠️ ประมวลผลบางส่วน")
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")
            result["status"] = "error"
            result["error"] = str(e)
        
        finally:
            result["end_time"] = datetime.now()
            result["duration"] = (result["end_time"] - result["start_time"]).total_seconds()
        
        return result
    
    def run_single_folder(self, folder_path: str) -> None:
        """
        รันระบบสำหรับโฟลเดอร์เดียว
        
        Args:
            folder_path: พาธของโฟลเดอร์ที่จะประมวลผล
        """
        folder = Path(folder_path)
        
        if not folder.exists() or not folder.is_dir():
            print(f"❌ ไม่พบโฟลเดอร์: {folder_path}")
            return
        
        print(f"\n🚀 เริ่มประมวลผลโฟลเดอร์เดียว")
        print(f"📂 โฟลเดอร์: {folder}")
        
        result = self.process_folder(folder, folder.name)
        self.results.append(result)
        
        self.print_summary()
    
    def run_all_main_folders(self) -> None:
        """รันระบบสำหรับทุกโฟลเดอร์หลักที่พบ"""
        print(f"\n🚀 เริ่มสแกนและประมวลผลทุกโฟลเดอร์หลัก")
        print(f"{'='*60}\n")
        
        # ค้นหาโฟลเดอร์หลักทั้งหมด
        main_folders = self.find_main_folders(self.base_path)
        
        if not main_folders:
            print("❌ ไม่พบโฟลเดอร์หลักที่ตรงเงื่อนไข")
            return
        
        print(f"\n📊 พบโฟลเดอร์หลักทั้งหมด: {len(main_folders)} โฟลเดอร์\n")
        
        # วนลูปประมวลผลแต่ละโฟลเดอร์หลัก
        for i, main_folder in enumerate(main_folders, 1):
            print(f"\n{'='*60}")
            print(f"📁 [{i}/{len(main_folders)}] กำลังประมวลผลโฟลเดอร์หลัก: {main_folder.name}")
            print(f"{'='*60}")
            
            # ค้นหาโฟลเดอร์อัตโนมัติในโฟลเดอร์หลัก
            automation_folders = self.find_automation_folders(main_folder)
            
            if not automation_folders:
                print(f"⚠️ ไม่พบโฟลเดอร์ระบบอัตโนมัติใน {main_folder.name}")
                continue
            
            print(f"📂 พบโฟลเดอร์อัตโนมัติ: {len(automation_folders)} โฟลเดอร์")
            
            # ประมวลผลแต่ละโฟลเดอร์อัตโนมัติ
            for j, auto_folder in enumerate(automation_folders, 1):
                print(f"\n  📁 [{j}/{len(automation_folders)}] ประมวลผลโฟลเดอร์: {auto_folder.name}")
                
                result = self.process_folder(auto_folder, main_folder.name)
                self.results.append(result)
                
                # ไม่พักระหว่างโฟลเดอร์ (รันต่อเนื่อง)
                # if j < len(automation_folders):
                #     print("\n  ⏸️ พักระหว่างโฟลเดอร์ 5 วินาที...")
                #     time.sleep(5)
            
            # ไม่พักระหว่างโฟลเดอร์หลัก (รันต่อเนื่อง)
            # if i < len(main_folders):
            #     print(f"\n⏸️ พักระหว่างโฟลเดอร์หลัก 10 วินาที...")
            #     time.sleep(10)
        
        # แสดงสรุปผลทั้งหมด
        self.print_summary()
    
    def print_summary(self) -> None:
        """แสดงสรุปผลการประมวลผลทั้งหมด"""
        print(f"\n\n{'='*60}")
        print("📊 สรุปผลการประมวลผลทั้งหมด")
        print(f"{'='*60}\n")
        
        if not self.results:
            print("⚠️ ไม่มีผลลัพธ์")
            return
        
        total_folders = len(self.results)
        total_pdfs = sum(r["pdf_count"] for r in self.results)
        success_folders = sum(1 for r in self.results if r["status"] == "success")
        partial_folders = sum(1 for r in self.results if r["status"] == "partial_success")
        failed_folders = sum(1 for r in self.results if r["status"] == "error")
        no_files_folders = sum(1 for r in self.results if r["status"] == "no_files")
        
        print(f"📁 โฟลเดอร์ทั้งหมด: {total_folders}")
        print(f"📄 ไฟล์ PDF ทั้งหมด: {total_pdfs}")
        print(f"✅ ประมวลผลสำเร็จ: {success_folders}")
        print(f"⚠️ ประมวลผลบางส่วน: {partial_folders}")
        print(f"❌ ประมวลผลล้มเหลว: {failed_folders}")
        print(f"📂 ไม่มีไฟล์: {no_files_folders}")
        
        print(f"\n{'='*60}")
        print("รายละเอียดแต่ละโฟลเดอร์:")
        print(f"{'='*60}\n")
        
        for i, result in enumerate(self.results, 1):
            status_icon = {
                "success": "✅",
                "partial_success": "⚠️",
                "error": "❌",
                "no_files": "📂",
                "read_failed": "⚠️",
                "pending": "⏳"
            }.get(result["status"], "❓")
            
            duration_str = f"{result.get('duration', 0):.1f}s" if 'duration' in result else "N/A"
            
            print(f"{i}. {status_icon} {result['main_folder']}")
            print(f"   📂 {result['automation_folder']}")
            print(f"   📄 PDF: {result['pdf_count']} | สถานะ: {result['status']} | เวลา: {duration_str}")
            
            if result.get("error"):
                print(f"   ❌ ข้อผิดพลาด: {result['error']}")
            
            print()
        
        total_duration = sum(r.get("duration", 0) for r in self.results)
        print(f"⏱️ เวลาทั้งหมด: {total_duration:.1f} วินาที ({total_duration/60:.1f} นาที)")
        print(f"{'='*60}\n")
    
    def run_continuous_loop(self) -> None:
        """รันระบบแบบลูปต่อเนื่อง"""
        print(f"🔄 เริ่มระบบลูปต่อเนื่อง...")
        loop_count = 0
        
        while True:
            try:
                loop_count += 1
                print(f"\n{'='*80}")
                print(f"🔄 รอบที่ {loop_count} - เริ่มสแกนและประมวลผล")
                print(f"{'='*80}")
                
                # รีเซ็ตผลลัพธ์สำหรับรอบใหม่
                self.results = []
                
                # สแกนและประมวลผล
                self.run_all_main_folders()
                
                print(f"\n✅ รอบที่ {loop_count} เสร็จสิ้น")
                print(f"⏳ รอ 15 วินาที ก่อนเริ่มรอบถัดไป...")
                time.sleep(15)
                
            except KeyboardInterrupt:
                print(f"\n🛑 หยุดการทำงานด้วย Ctrl+C")
                break
            except Exception as e:
                print(f"\n❌ เกิดข้อผิดพลาดในรอบที่ {loop_count}: {e}")
                print(f"⏳ รอ 15 วินาที ก่อนลองใหม่...")
                time.sleep(15)


def main():
    """ฟังก์ชันหลัก"""
    print("🤖 BotV3 Main System - Multi-Folder Scanner & Processor")
    print("="*60)
    
    # ตรวจสอบ arguments
    if len(sys.argv) > 1:
        # รันโฟลเดอร์เดียวตาม argument
        folder_path = sys.argv[1]
        print(f"🎯 โหมดโฟลเดอร์เดียว: {folder_path}")
        
        orchestrator = MainSystemOrchestrator()
        orchestrator.run_single_folder(folder_path)
    else:
        # รันทุกโฟลเดอร์หลักตาม config
        print(f"🎯 โหมดสแกนทุกโฟลเดอร์หลัก")
        print(f"📂 พาธฐาน: V:/A.โฟร์เดอร์หลัก, V:/AA.โฟรเดอร์หลัก, V:/AAA.โฟรเดอร์หลัก\n")
        
        # สแกนและประมวลผลทุกโฟลเดอร์หลัก
        base_paths = [
            "V:/A.โฟร์เดอร์หลัก",
            "V:/AA.โฟรเดอร์หลัก",
            "V:/AAA.โฟรเดอร์หลัก"
        ]
        
        all_results = []
        
        for base_path in base_paths:
            orchestrator = MainSystemOrchestrator(base_path)
            orchestrator.run_all_main_folders()
            all_results.extend(orchestrator.results)
        
        # แสดงสรุปรวมทั้งหมด
        print(f"\n\n{'='*60}")
        print("📊 สรุปผลการประมวลผลทั้งหมดจากทุก Base Path")
        print(f"{'='*60}\n")
        
        if all_results:
            total_folders = len(all_results)
            total_pdfs = sum(r["pdf_count"] for r in all_results)
            success_folders = sum(1 for r in all_results if r["status"] == "success")
            
            print(f"📁 โฟลเดอร์ทั้งหมด: {total_folders}")
            print(f"📄 ไฟล์ PDF ทั้งหมด: {total_pdfs}")
            print(f"✅ ประมวลผลสำเร็จ: {success_folders}")
            print(f"{'='*60}\n")
    
    print("✅ ระบบทำงานเสร็จสิ้น")
    print("👋 สวัสดี!")


if __name__ == "__main__":
    main()

