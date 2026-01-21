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
    _system_state = state_dict or {}
    # รองรับ callback ที่ส่งมาจากภายนอก
    if _system_state is not None:
        _system_state.setdefault('progress_callback', None)
        _system_state.setdefault('status_callback', None)
        _system_state.setdefault('log_callback', None)

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
    
    def __init__(
        self,
        base_path: str = "V:/A.โฟลเดอร์หลัก",
        progress_callback=None,
        status_callback=None,
        log_callback=None
    ):
        """
        Initialize orchestrator
        
        Args:
            base_path: พาธฐานสำหรับการสแกน (ค่าเริ่มต้นคือ V:/A.โฟร์เดอร์หลัก)
        """
        self.base_path = Path(base_path)
        self.pdf_reader = PDFReader()
        self.file_manager = FileManager()
        self.results = []
        self.progress_callback = progress_callback or (_system_state.get('progress_callback') if _system_state else None)
        self.status_callback = status_callback or (_system_state.get('status_callback') if _system_state else None)
        self.log_callback = log_callback or (_system_state.get('log_callback') if _system_state else None)
        
        self._log(f"🤖 เริ่มต้นระบบหลัก BotV3")
        self._log(f"📂 พาธฐาน: {self.base_path}")

    def _notify_progress(self, *, total_delta=0, success_delta=0, failure_delta=0, duplicate_delta=0, reset=False):
        if self.progress_callback:
            try:
                self.progress_callback(
                    total_delta=total_delta,
                    success_delta=success_delta,
                    failure_delta=failure_delta,
                    duplicate_delta=duplicate_delta,
                    reset=reset
                )
            except Exception as e:
                print(f"⚠️ ไม่สามารถอัพเดตความคืบหน้าได้: {e}")

    def _update_status(self, *, folder=None, file=None, step=None):
        if self.status_callback:
            try:
                self.status_callback(folder=folder, file=file, step=step)
            except Exception as e:
                print(f"⚠️ ไม่สามารถอัพเดตสถานะได้: {e}")

    def _log(self, message: str, level: str = "info"):
        try:
            print(message)
        except Exception:
            pass
        if self.log_callback:
            try:
                self.log_callback(message, level)
            except Exception:
                pass
    
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
            max_loops = getattr(Config, 'PDF_PROCESSING_MAX_LOOPS', 3)
            loop_index = 0
            processed_any = False
            result["attempts"] = []
            while loop_index < max_loops:
                pdf_files = self.find_pdf_files_in_folder(automation_folder)
                pdf_files = [p for p in pdf_files if p.exists()]
                if not pdf_files:
                    if processed_any:
                        if result["status"] not in ("partial_success", "error"):
                            result["status"] = "success"
                    else:
                        result["status"] = "no_files"
                    break
                
                loop_index += 1
                self._log(f"\n{'='*60}")
                self._log(f"📂 ประมวลผลรอบที่ {loop_index}: {automation_folder.relative_to(automation_folder.parent.parent.parent)}")
                self._log(f"{'='*60}")
                
                result["attempts"].append({
                    "attempt": loop_index,
                    "files": [str(pdf.name) for pdf in pdf_files]
                })
                result["pdf_count"] += len(pdf_files)
                result["pdf_files_found"].extend(str(pdf.name) for pdf in pdf_files)
                self._notify_progress(total_delta=len(pdf_files))
                
                self._update_status(
                    folder=str(automation_folder),
                    step=f'กำลังอ่านไฟล์ PDF ({len(pdf_files)} ไฟล์) - รอบที่ {loop_index}',
                    file='-'
                )
                
                self._log(f"📄 พบไฟล์ PDF จำนวน: {len(pdf_files)} ไฟล์ (รอบที่ {loop_index})")
                self._log("📋 รายการไฟล์ที่พบ:")
                for i, pdf_file in enumerate(pdf_files, 1):
                    self._log(f"   {i}. {pdf_file.name}")
                
                # อ่านข้อมูล PDF
                self._log("\n🔍 เริ่มอ่าน PDF...")
                self._update_status(step=f'กำลังอ่านข้อมูล PDF (รอบที่ {loop_index})')
                for i, pdf_file in enumerate(pdf_files):
                    self._update_status(
                        file=f'กำลังอ่าน: {pdf_file.name} ({i+1}/{len(pdf_files)})',
                        step=f'กำลังอ่านข้อมูล PDF (รอบที่ {loop_index})'
                    )
                    time.sleep(0.05)
                
                pdf_data_list = self.pdf_reader.process_pdf_batch(pdf_files=pdf_files)
                success_names = [pdf_data.get('filename', 'ไม่ทราบชื่อ') for pdf_data in pdf_data_list if pdf_data]
                result["pdf_files_read_success"].extend(success_names)
                
                all_filenames = set(str(pdf.name) for pdf in pdf_files)
                failed_filenames = all_filenames - set(success_names)
                if failed_filenames:
                    result["pdf_files_read_failed"].extend(failed_filenames)
                    self._notify_progress(failure_delta=len(failed_filenames))
                
                if not pdf_data_list:
                    self._log("⚠️ ไม่มีไฟล์ที่อ่านสำเร็จในรอบนี้", "warning")
                    result["status"] = "read_failed"
                    break
                
                self._log(f"✅ อ่านสำเร็จ: {len(pdf_data_list)} ไฟล์", "success")
                self._log("📋 รายการไฟล์ที่อ่านสำเร็จ:")
                for i, pdf_data in enumerate(pdf_data_list, 1):
                    filename = pdf_data.get('filename', 'ไม่ทราบชื่อ')
                    company = pdf_data.get('company_name', 'ไม่ทราบบริษัท')
                    self._log(f"   {i}. {filename} (บริษัท: {company})")
                
                if failed_filenames:
                    self._log(f"❌ อ่านไม่ได้: {len(failed_filenames)} ไฟล์", "error")
                    for i, filename in enumerate(failed_filenames, 1):
                        self._log(f"   {i}. {filename}")
                
                # เริ่ม Web Automation
                self._log("\n🌐 เริ่มระบบ Web Automation...")
                self._update_status(step=f'กำลังประมวลผล Web Automation (รอบที่ {loop_index})')
                for i, pdf_data in enumerate(pdf_data_list):
                    if pdf_data and 'company_name' in pdf_data:
                        self._update_status(
                            file=f'กำลังประมวลผล: {pdf_data["company_name"]} ({i+1}/{len(pdf_data_list)})',
                            step=f'กำลังประมวลผล Web Automation (รอบที่ {loop_index})'
                        )
                        time.sleep(0.05)
                
                automation = WebAutomationPlaywright(
                    progress_callback=self._notify_progress,
                    status_callback=self._update_status,
                    log_callback=self._log,
                    force_sync_mode=True
                )
                
                success = automation.execute_peak_engine_workflow(
                    pdf_data_list=pdf_data_list,
                    main_folder=str(automation_folder)
                )
                
                if success:
                    processed_any = True
                    result["success_count"] += len(pdf_data_list)
                    self._log("✅ ประมวลผลรอบนี้สำเร็จ", "success")
                    # ตรวจสอบว่าเหลือไฟล์ค้างไหม ถ้ามีจะวนลูปต่อ
                    continue
                else:
                    result["status"] = "partial_success"
                    self._log("⚠️ ประมวลผลรอบนี้ไม่สมบูรณ์ หยุดการวนลูป", "warning")
                    break
            
            # หลังจากวนครบ ตรวจสอบไฟล์ค้างอีกครั้ง
            leftover_pdf_files = self.find_pdf_files_in_folder(automation_folder)
            leftover_pdf_files = [p for p in leftover_pdf_files if p.exists()]
            if leftover_pdf_files:
                self._log("⚠️ พบไฟล์ PDF ที่ยังคงค้างหลังจากพยายามประมวลผล:", "warning")
                for pending_file in leftover_pdf_files:
                    self._log(f"   - {pending_file}")
                if result["status"] == "pending":
                    result["status"] = "partial_success"
                result.setdefault("leftover_files", [])
                result["leftover_files"].extend(str(pending_file) for pending_file in leftover_pdf_files)
            elif result["status"] == "pending":
                result["status"] = "success" if processed_any else "no_files"
            
        except Exception as e:
            self._log(f"❌ เกิดข้อผิดพลาด: {e}", "error")
            result["status"] = "error"
            result["error"] = str(e)
        
        finally:
            result["end_time"] = datetime.now()
            result["duration"] = (result["end_time"] - result["start_time"]).total_seconds()
            result["pdf_files_found"] = list(dict.fromkeys(result["pdf_files_found"]))
            result["pdf_files_read_success"] = list(dict.fromkeys(result["pdf_files_read_success"]))
            result["pdf_files_read_failed"] = list(dict.fromkeys(result["pdf_files_read_failed"]))
            if "leftover_files" in result:
                result["leftover_files"] = list(dict.fromkeys(result["leftover_files"]))
        
        return result
    
    def run_single_folder(self, folder_path: str) -> None:
        """
        รันระบบสำหรับโฟลเดอร์เดียว
        
        Args:
            folder_path: พาธของโฟลเดอร์ที่จะประมวลผล
        """
        folder = Path(folder_path)
        
        if not folder.exists() or not folder.is_dir():
            self._log(f"❌ ไม่พบโฟลเดอร์: {folder_path}", "error")
            return
        
        self._log(f"\n🚀 เริ่มประมวลผลโฟลเดอร์เดียว")
        self._log(f"📂 โฟลเดอร์: {folder}")
        
        result = self.process_folder(folder, folder.name)
        self.results.append(result)
        
        self.print_summary()
    
    def run_all_main_folders(self) -> None:
        """รันระบบสำหรับทุกโฟลเดอร์หลักที่พบ"""
        self._log(f"\n🚀 เริ่มสแกนและประมวลผลทุกโฟลเดอร์หลัก")
        self._log(f"{'='*60}\n")
        
        # ค้นหาโฟลเดอร์หลักทั้งหมด
        main_folders = self.find_main_folders(self.base_path)
        
        if not main_folders:
            self._log("❌ ไม่พบโฟลเดอร์หลักที่ตรงเงื่อนไข", "error")
            return
        
        self._log(f"\n📊 พบโฟลเดอร์หลักทั้งหมด: {len(main_folders)} โฟลเดอร์\n")
        
        # วนลูปประมวลผลแต่ละโฟลเดอร์หลัก
        for i, main_folder in enumerate(main_folders, 1):
            self._log(f"\n{'='*60}")
            self._log(f"📁 [{i}/{len(main_folders)}] กำลังประมวลผลโฟลเดอร์หลัก: {main_folder.name}")
            self._log(f"{'='*60}")
            
            # ค้นหาโฟลเดอร์อัตโนมัติในโฟลเดอร์หลัก
            automation_folders = self.find_automation_folders(main_folder)
            
            if not automation_folders:
                print(f"⚠️ ไม่พบโฟลเดอร์ระบบอัตโนมัติใน {main_folder.name}")
                continue
            
            print(f"📂 พบโฟลเดอร์อัตโนมัติ: {len(automation_folders)} โฟลเดอร์")
            
            # ประมวลผลแต่ละโฟลเดอร์อัตโนมัติ
            for j, auto_folder in enumerate(automation_folders, 1):
                self._log(f"\n  📁 [{j}/{len(automation_folders)}] ประมวลผลโฟลเดอร์: {auto_folder.name}")
                
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
        self._log(f"\n\n{'='*60}")
        self._log("📊 สรุปผลการประมวลผลทั้งหมด")
        self._log(f"{'='*60}\n")
        
        if not self.results:
            self._log("⚠️ ไม่มีผลลัพธ์", "warning")
            return
        
        total_folders = len(self.results)
        total_pdfs = sum(r["pdf_count"] for r in self.results)
        success_folders = sum(1 for r in self.results if r["status"] == "success")
        partial_folders = sum(1 for r in self.results if r["status"] == "partial_success")
        failed_folders = sum(1 for r in self.results if r["status"] == "error")
        no_files_folders = sum(1 for r in self.results if r["status"] == "no_files")
        
        self._log(f"📁 โฟลเดอร์ทั้งหมด: {total_folders}")
        self._log(f"📄 ไฟล์ PDF ทั้งหมด: {total_pdfs}")
        self._log(f"✅ ประมวลผลสำเร็จ: {success_folders}")
        self._log(f"⚠️ ประมวลผลบางส่วน: {partial_folders}")
        self._log(f"❌ ประมวลผลล้มเหลว: {failed_folders}")
        self._log(f"📂 ไม่มีไฟล์: {no_files_folders}")
        
        self._log(f"\n{'='*60}")
        self._log("รายละเอียดแต่ละโฟลเดอร์:")
        self._log(f"{'='*60}\n")
        
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
            
            self._log(f"{i}. {status_icon} {result['main_folder']}")
            self._log(f"   📂 {result['automation_folder']}")
            self._log(f"   📄 PDF: {result['pdf_count']} | สถานะ: {result['status']} | เวลา: {duration_str}")
            
            if result.get("error"):
                self._log(f"   ❌ ข้อผิดพลาด: {result['error']}", "error")
            if result.get("attempts"):
                attempts_info = ", ".join(f"รอบ {att['attempt']} ({len(att['files'])} ไฟล์)" for att in result["attempts"])
                self._log(f"   🔁 รอบที่ประมวลผล: {attempts_info}")
            if result.get("leftover_files"):
                self._log(f"   ⚠️ ไฟล์ที่ยังค้าง: {len(result['leftover_files'])}", "warning")
            
            self._log("")
        
        total_duration = sum(r.get("duration", 0) for r in self.results)
        self._log(f"⏱️ เวลาทั้งหมด: {total_duration:.1f} วินาที ({total_duration/60:.1f} นาที)")
        self._log(f"{'='*60}\n")
    
    def run_continuous_loop(self) -> None:
        """รันระบบแบบลูปต่อเนื่อง"""
        self._log("🔄 เริ่มระบบลูปต่อเนื่อง...")
        loop_count = 0
        
        while True:
            try:
                loop_count += 1
                self._log(f"\n{'='*80}")
                self._log(f"🔄 รอบที่ {loop_count} - เริ่มสแกนและประมวลผล")
                self._log(f"{'='*80}")
                
                # รีเซ็ตผลลัพธ์สำหรับรอบใหม่
                self.results = []
                
                # สแกนและประมวลผล
                self.run_all_main_folders()
                
                self._log(f"\n✅ รอบที่ {loop_count} เสร็จสิ้น", "success")
                self._log("⏳ รอ 15 วินาที ก่อนเริ่มรอบถัดไป...")
                time.sleep(15)
                
            except KeyboardInterrupt:
                self._log("\n🛑 หยุดการทำงานด้วย Ctrl+C", "warning")
                break
            except Exception as e:
                self._log(f"\n❌ เกิดข้อผิดพลาดในรอบที่ {loop_count}: {e}", "error")
                self._log("⏳ รอ 15 วินาที ก่อนลองใหม่...")
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

