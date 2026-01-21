import os
import json
import re
import shutil
import time
from pathlib import Path
from typing import List, Dict, Optional
from config import Config
from datetime import datetime

class FileManager:
    """จัดการไฟล์ การสร้างไฟล์ PDF และการย้ายไฟล์"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(Config.BASE_FOLDER)
        self.test_system_path = self.base_path / Config.TEST_SYSTEM_FOLDER
        self.temp_files = []  # เก็บรายการไฟล์ชั่วคราว
        
    def get_main_folders(self) -> List[Path]:
        """อ่านโฟลเดอร์หลัก A.โฟร์เดอร์หลัก, AA.โฟรเดอร์หลัก, AAA.โฟรเดอร์หลัก"""
        main_folders = []
        if self.base_path.exists():
            for item in self.base_path.iterdir():
                if item.is_dir():
                    # ตรวจสอบว่าเป็นโฟลเดอร์หลักตามที่กำหนดใน Config หรือไม่
                    if item.name in Config.MAIN_FOLDERS and not self.should_skip_folder(item.name):
                        main_folders.append(item)
                        print(f"Found main folder: {item.name}")
        return sorted(main_folders)
    
    def should_skip_folder(self, folder_name: str) -> bool:
        """ตรวจสอบว่าควรข้ามโฟลเดอร์หรือไม่"""
        return folder_name in Config.SKIP_FOLDERS
    
    def get_customer_automation_folders(self, main_folder: Path) -> List[Path]:
        """หาโฟลเดอร์ลูกค้าและระบบอัตโนมัติ"""
        automation_folders = []
        
        for root, dirs, files in os.walk(main_folder):
            root_path = Path(root)
            
            # ข้ามโฟลเดอร์ที่ไม่ต้องการ
            dirs[:] = [d for d in dirs if not self.should_skip_folder(d)]
            
            # หาโฟลเดอร์ลูกค้า
            if root_path.name == Config.CUSTOMER_FOLDER:
                # หาโฟลเดอร์ระบบอัตโนมัติ
                automation_path = root_path / Config.AUTOMATION_FOLDER
                if automation_path.exists():
                    automation_folders.append(automation_path)
                    
        return automation_folders
    
    def get_pdf_files(self, folder_path: Path) -> List[Path]:
        """หาไฟล์ PDF ในโฟลเดอร์แบบ recursive และข้ามโฟลเดอร์ผลลัพธ์"""
        pdf_files: List[Path] = []
        if not folder_path.exists():
            return pdf_files
        skip_dirs = {
            Config.OUTPUT_FOLDERS.get('original', 'เอกสารต้นฉบับ'),
            Config.OUTPUT_FOLDERS.get('processed', 'เอกสารบันทึกแล้ว'),
            'เอกสารซ้ำรอตรวจ'
        }
        for file_path in folder_path.rglob('*.pdf'):
            try:
                # ข้ามไฟล์ที่อยู่ในโฟลเดอร์ผลลัพธ์
                if any(part in skip_dirs for part in file_path.parts):
                    continue
                pdf_files.append(file_path)
            except Exception:
                continue
        # เรียงตามชื่อไฟล์เพื่อให้ผลลัพธ์คงที่
        return sorted(pdf_files)
    
    def read_json_config(self, folder_code: str) -> Dict:
        """อ่านไฟล์ JSON config ตามรหัสโฟลเดอร์"""
        json_path = self.test_system_path / folder_code / f"{folder_code}.json"
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading JSON config: {e}")
        return {}
    
    def read_folder_settings(self) -> Dict:
        """อ่านไฟล์ folder_settings.json"""
        # อ่านจากตำแหน่งที่ผู้ใช้สร้างไว้
        settings_path = Path("V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/folder_settings/folder_settings.json")
        if settings_path.exists():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading folder settings: {e}")
        return {}
    
    def read_login_credentials(self, folder_code: str) -> Dict:
        """อ่านข้อมูล login จากไฟล์ txt"""
        txt_path = self.test_system_path / folder_code / f"{folder_code}.txt"
        credentials = {}
        
        if txt_path.exists():
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if ':' in line:
                            key, value = line.split(':', 1)
                            credentials[key.strip()] = value.strip()
            except Exception as e:
                print(f"Error reading login credentials: {e}")
                
        return credentials
    
    def create_output_folders(self, base_output_path: Path):
        """สร้างโฟลเดอร์ผลลัพธ์"""
        for folder_name in Config.OUTPUT_FOLDERS.values():
            folder_path = base_output_path / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)
    
    def move_file_to_output(self, source_file: Path, output_type: str, base_output_path: Path):
        """ย้ายไฟล์ไปยังโฟลเดอร์ผลลัพธ์"""
        if output_type in Config.OUTPUT_FOLDERS:
            dest_folder = base_output_path / Config.OUTPUT_FOLDERS[output_type]
            dest_file = dest_folder / source_file.name
            
            try:
                shutil.copy2(source_file, dest_file)
                return dest_file
            except Exception as e:
                print(f"Error moving file: {e}")
                return None
        return None
    
    def get_folder_code_from_path(self, folder_path: Path) -> Optional[str]:
        """ดึงรหัสโฟลเดอร์จาก path"""
        # หาโฟลเดอร์ที่มีรหัส (เช่น 001, 002, Build000, Build001)
        for part in folder_path.parts:
            token = str(part)
            # เคสตัวเลข 3 หลักแบบตรงตัว
            if token.isdigit() and len(token) == 3:
                return token
            # ดึงรหัสแบบ Build000 ที่อยู่ต้นสตริง เช่น "Build000 ทดสอบระบบ"
            m = re.match(r'^(Build\d{3})\b', token)
            if m:
                return m.group(1)
            # ดึงรหัสตัวเลข 3 หลักที่อยู่ต้นสตริง เช่น "001 โฟลเดอร์"
            m2 = re.match(r'^(\d{3})\b', token)
            if m2:
                return m2.group(1)
        return None

    def get_files_in_folder(self, folder_name):
        """Get files in a specific folder"""
        try:
            folder_path = self.base_path / folder_name
            if not folder_path.exists():
                return []
            
            files = []
            for root, dirs, filenames in os.walk(folder_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for filename in filenames:
                    if filename.startswith('.'):
                        continue
                        
                    file_path = Path(root) / filename
                    try:
                        stat = file_path.stat()
                        relative_path = str(file_path.relative_to(folder_path))
                        
                        file_info = {
                            'name': filename,
                            'path': relative_path,
                            'size': f"{stat.st_size / 1024:.1f} KB",
                            'type': self._get_file_type(filename),
                            'lastModified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        }
                        files.append(file_info)
                        
                    except Exception as e:
                        print(f"Error processing file {filename}: {e}")
                        continue
            
            return files
            
        except Exception as e:
            print(f"Error getting files in folder {folder_name}: {e}")
            return []

    def _get_file_type(self, filename):
        """Determine file type based on extension"""
        ext = Path(filename).suffix.lower()
        if ext in ['.py', '.pyc']:
            return 'Python'
        elif ext in ['.json', '.xml', '.yaml', '.yml']:
            return 'Config'
        elif ext in ['.txt', '.log']:
            return 'Text'
        elif ext in ['.pdf']:
            return 'PDF'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
            return 'Image'
        elif ext in ['.mp4', '.avi', '.mov']:
            return 'Video'
        elif ext in ['.xlsx', '.xls']:
            return 'Excel'
        elif ext in ['.docx', '.doc']:
            return 'Word'
        else:
            return 'Other'

    def create_pdf_from_form_data(self, pdf_data: Dict, iptnumber_text: str, source_folder: str = None, folder_settings: Dict = None) -> Optional[str]:
        """สร้างไฟล์ PDF ใหม่จากข้อมูลที่กรอกในฟอร์ม"""
        try:
            print(f" เริ่มสร้างไฟล์ PDF ใหม่...")
            
            # 1. ดึงเลขที่เอกสารจาก iptnumber
            print(f"🔍 กำลังดึงเลขที่เอกสารจาก iptnumber...")
            
            # ทำความสะอาดข้อมูล iptnumber
            cleaned_text = ' '.join(iptnumber_text.split()) if iptnumber_text else ""
            print(f"🧹 ข้อมูล iptnumber หลังทำความสะอาด: '{cleaned_text}'")
            
            if not cleaned_text:
                print(f"⚠️ ไม่พบข้อมูลจาก iptnumber")
                return None
            
            # ใช้ข้อมูลจาก iptnumber โดยตรง
            document_number = cleaned_text
            print(f" เลขที่เอกสารที่ดึงได้: '{document_number}'")
            
            # 2. ดึงวันที่จากข้อมูล PDF
            document_date = pdf_data.get('document_date', '')
            if not document_date:
                print(f"⚠️ ไม่พบวันที่ในข้อมูล PDF")
                return None
            
            # วันที่ไม่ใช้ในชื่อไฟล์แล้ว (ลบการสร้าง formatted_date)
            
            # 3. กำหนดกลุ่มและชื่อบริการ
            company_name = pdf_data.get('company_name', '')
            service_name = self._get_service_name(company_name, folder_settings, pdf_data)
            
            # ตรวจสอบประเภทภาษีของบริษัท
            company_vat_status = Config.COMPANY_VAT_STATUS.get(company_name, 'VAT')
            
            print(f"🏢 ชื่อบริษัท: '{company_name}'")
            print(f"🏷️ ชื่อบริการ: '{service_name}'")
            print(f"🏷️ ประเภทภาษี: '{company_vat_status}'")
            
            # 4. สร้างชื่อไฟล์ใหม่ (VAT มีวันที่, NoneVat ไม่มีวันที่)
            safe_document_number = self.sanitize_filename(document_number)
            
            # ตรวจสอบ folder_group เพื่อกำหนดรูปแบบชื่อไฟล์
            folder_group = pdf_data.get('group', 'unknown')
            
            if company_vat_status == 'VAT':
                # VAT: ใส่วันที่ในชื่อไฟล์ (รูปแบบ: DD.MM.YYYY เลขที่เอกสาร ชื่อบริการ)
                # แปลงวันที่จาก DD/MM/YYYY เป็น DD.MM.YYYY
                try:
                    if '/' in document_date:
                        date_parts = document_date.split('/')
                        if len(date_parts) == 3:
                            day, month, year = date_parts
                            formatted_date = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
                        else:
                            formatted_date = document_date.replace('/', '.')
                    else:
                        formatted_date = document_date
                except Exception as e:
                    print(f"⚠️ ไม่สามารถแปลงวันที่ได้: {e}")
                    formatted_date = document_date
                
                new_filename = f"{formatted_date} {safe_document_number} {service_name}"
                print(f"📝 ชื่อไฟล์ใหม่ (VAT มีวันที่): '{new_filename}.pdf'")
            else:
                # NoneVat: ไม่ใส่วันที่ในชื่อไฟล์
                new_filename = f"{safe_document_number} {service_name}"
                print(f"📝 ชื่อไฟล์ใหม่ (NoneVat ไม่มีวันที่): '{new_filename}.pdf'")
            
            new_pdf_filename = f"{new_filename}.pdf"
            
            # 4. กำหนดโฟลเดอร์ที่จะสร้างไฟล์
            if source_folder:
                # สร้างไฟล์ในโฟลเดอร์เดียวกับที่อ่านไฟล์ต้นฉบับ
                target_folder = Path(source_folder)
                new_file_path = target_folder / new_pdf_filename
                print(f"📁 สร้างไฟล์ในโฟลเดอร์: {target_folder}")
            else:
                # ถ้าไม่ระบุโฟลเดอร์ ให้สร้างในโฟลเดอร์ปัจจุบัน
                new_file_path = Path(new_pdf_filename)
                target_folder = new_file_path.parent
                print(f"📁 สร้างไฟล์ในโฟลเดอร์ปัจจุบัน")
            
            # 5/6. สร้างไฟล์ PDF ใหม่ในโฟลเดอร์ที่กำหนด
            try:
                # สร้างโฟลเดอร์ถ้ายังไม่มี
                target_folder.mkdir(parents=True, exist_ok=True)
                
                # ถ้ามีไฟล์ต้นฉบับ ให้คัดลอกเป็นไฟล์ใหม่ตามชื่อที่ตั้ง (ตามแนวทาง BotV2)
                source_pdf_path = pdf_data.get('file_path') or pdf_data.get('pdf_path')
                if source_pdf_path and os.path.exists(source_pdf_path):
                    if not self._copy_with_retry(source_pdf_path, str(new_file_path)):
                        print(f"❌ ไม่สามารถคัดลอกไฟล์ต้นฉบับได้ (file in use?): {source_pdf_path} -> {new_file_path}")
                        return None
                else:
                    # กรณีไม่มีไฟล์ต้นฉบับ ให้สร้างไฟล์ข้อความเป็น .pdf แทน
                    pdf_content = f"""ข้อมูลที่กรอกในฟอร์ม:

    Customer ID: {pdf_data.get('customer_id', '')}
    Account Code: {pdf_data.get('account_code', '')}
    เลขที่เอกสาร: {pdf_data.get('document_number', '')}
    วันที่เอกสาร: {pdf_data.get('document_date', '')}
    ยอดก่อนภาษีมูลค่าเพิ่ม: {pdf_data.get('total_ex_vat', '')}
    ยอดก่อนภาษีมูลค่าเพิ่ม (NoneVat): {pdf_data.get('total_ex_vat_none', '')}
    ยอดภาษีมูลค่าเพิ่ม: {pdf_data.get('vat_value', '')}
    ยอดหลังบวกภาษีมูลค่าเพิ่ม: {pdf_data.get('total_in_vat', '')}
    ชื่อบริษัท: {pdf_data.get('company_name', '')}

    เลขที่เอกสารใหม่: {document_number}
    วันที่เอกสาร: {document_date}
    เวลาที่สร้าง: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
                    if not self._write_text_with_retry(str(new_file_path), pdf_content):
                        print(f"❌ ไม่สามารถสร้างไฟล์ข้อความ .pdf ได้: {new_file_path}")
                        return None
                
                print(f"✅ สร้างไฟล์ PDF ใหม่สำเร็จ: {new_file_path}")
                
                # ตรวจสอบว่าไฟล์ใหม่ถูกสร้างขึ้นหรือไม่
                if new_file_path.exists():
                    print(f"✅ ไฟล์ใหม่ถูกสร้างขึ้น: {new_file_path}")
                    
                    # เพิ่มไฟล์ลงในรายการไฟล์ชั่วคราว
                    self.temp_files.append(str(new_file_path))
                    
                    # ส่งข้อมูลการสร้างไฟล์กลับไป
                    file_info = {
                        'filename': new_pdf_filename,
                        'file_path': str(new_file_path.absolute()),
                        'file_size': new_file_path.stat().st_size,
                        'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'document_number': document_number,
                        'document_date': document_date
                    }
                    
                    print(f" ข้อมูลไฟล์ที่สร้าง: {file_info}")
                    return str(new_file_path.absolute())
                else:
                    print(f"❌ ไม่สามารถสร้างไฟล์ใหม่ได้")
                    return None
                    
            except Exception as create_error:
                print(f"❌ ไม่สามารถสร้างไฟล์ PDF ใหม่ได้: {create_error}")
                return None
                
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการสร้างไฟล์ PDF: {e}")
            return None

    def _copy_with_retry(self, src: str, dst: str, attempts: int = 5, delay: float = 0.4) -> bool:
        """คัดลอกไฟล์แบบมี retry เพื่อหลบ WinError 32 (ไฟล์ถูกใช้งานโดยโปรเซสอื่น)"""
        last_error: Optional[Exception] = None
        for i in range(attempts):
            try:
                shutil.copy2(src, dst)
                return True
            except Exception as e:
                last_error = e
                try:
                    winerr = getattr(e, 'winerror', None)
                except Exception:
                    winerr = None
                if winerr == 32:
                    print(f"⚠️ ไฟล์กำลังถูกใช้งานโดยโปรเซสอื่น (WinError 32) ลองใหม่ {i+1}/{attempts}...")
                else:
                    print(f"⚠️ คัดลอกไฟล์ล้มเหลว: {e} ลองใหม่ {i+1}/{attempts}...")
                time.sleep(delay * (i + 1))
        print(f"❌ คัดลอกไฟล์ไม่สำเร็จหลัง retry ทั้งหมด: {last_error}")
        return False

    def _write_text_with_retry(self, path: str, content: str, attempts: int = 5, delay: float = 0.4) -> bool:
        """เขียนไฟล์แบบมี retry เพื่อหลบ WinError 32 บน Windows"""
        last_error: Optional[Exception] = None
        for i in range(attempts):
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except Exception as e:
                last_error = e
                try:
                    winerr = getattr(e, 'winerror', None)
                except Exception:
                    winerr = None
                if winerr == 32:
                    print(f"⚠️ ไฟล์ปลายทางถูกใช้งาน (WinError 32) ลองใหม่ {i+1}/{attempts}...")
                else:
                    print(f"⚠️ เขียนไฟล์ล้มเหลว: {e} ลองใหม่ {i+1}/{attempts}...")
                time.sleep(delay * (i + 1))
        print(f"❌ เขียนไฟล์ไม่สำเร็จหลัง retry ทั้งหมด: {last_error}")
        return False

    def _move_with_retry(self, src: str, dst: str, attempts: int = 5, delay: float = 0.4) -> bool:
        """ย้ายไฟล์แบบมี retry เพื่อหลบ WinError 32 (ไฟล์ถูกใช้งาน)"""
        last_error: Optional[Exception] = None
        for i in range(attempts):
            try:
                shutil.move(src, dst)
                return True
            except Exception as e:
                last_error = e
                try:
                    winerr = getattr(e, 'winerror', None)
                except Exception:
                    winerr = None
                if winerr == 32:
                    print(f"⚠️ ไฟล์กำลังถูกใช้งาน (WinError 32) ลองย้ายใหม่ {i+1}/{attempts}...")
                else:
                    print(f"⚠️ ย้ายไฟล์ล้มเหลว: {e} ลองใหม่ {i+1}/{attempts}...")
                time.sleep(delay * (i + 1))
        print(f"❌ ย้ายไฟล์ไม่สำเร็จหลัง retry ทั้งหมด: {last_error}")
        return False

    def move_file_to_duplicate_folder(self, file_path: str) -> Optional[str]:
        """ย้ายไฟล์ไปยังโฟลเดอร์ 'เอกสารซ้ำรอตรวจ' ภายในโฟลเดอร์เดียวกับไฟล์นั้น (ใช้ชื่อเดิมไม่เปลี่ยนแปลง)"""
        try:
            if not file_path or not os.path.exists(file_path):
                print(f"⚠️ ไม่พบไฟล์ที่จะย้าย: {file_path}")
                return None
            parent_dir = os.path.dirname(file_path)
            dup_dir = os.path.join(parent_dir, 'เอกสารซ้ำรอตรวจ')
            os.makedirs(dup_dir, exist_ok=True)

            base_name = os.path.basename(file_path)
            dest_path = os.path.join(dup_dir, base_name)

            # ถ้ามีไฟล์ชื่อเดียวกันอยู่แล้ว ให้ลบไฟล์เก่าทิ้งแล้วย้ายไฟล์ใหม่เข้าไป
            if os.path.exists(dest_path):
                print(f"⚠️ พบไฟล์ชื่อเดียวกันอยู่แล้ว จะลบไฟล์เก่าและใช้ไฟล์ใหม่แทน")
                try:
                    os.remove(dest_path)
                    print(f"🗑️ ลบไฟล์เก่าสำเร็จ: {dest_path}")
                except Exception as e:
                    print(f"⚠️ ไม่สามารถลบไฟล์เก่าได้: {e}")
                    # ถ้าลบไม่ได้ ให้เพิ่ม timestamp (เป็น fallback)
                    name, ext = os.path.splitext(base_name)
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    dest_path = os.path.join(dup_dir, f"{name}_dup_{ts}{ext}")

            if self._move_with_retry(file_path, dest_path):
                print(f"✅ ย้ายไฟล์ไปยังโฟลเดอร์ 'เอกสารซ้ำรอตรวจ' สำเร็จ: {dest_path}")
                return dest_path
            else:
                print(f"❌ ย้ายไฟล์ไปยังโฟลเดอร์ 'เอกสารซ้ำรอตรวจ' ไม่สำเร็จ")
                return None
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการย้ายไฟล์ไปยังโฟลเดอร์เอกสารซ้ำรอตรวจ: {e}")
            return None

    def _get_service_name(self, company_name: str, folder_settings: Dict = None, pdf_data: Dict = None) -> str:
        """กำหนดชื่อบริการตามกลุ่มบริษัท"""
        try:
            # กำหนดกลุ่มจาก folder_settings
            group = 'unknown'
            if folder_settings and pdf_data:
                folder_code = pdf_data.get('folder_code', '')
                if folder_code in folder_settings:
                    folder_info = folder_settings[folder_code]
                    group = folder_info.get('group', 'unknown')
            
            # ใช้ group จาก folder_settings เป็นหลัก (ไม่ใช่ company_vat_status)
            print(f"🔍 กลุ่มที่กำหนด: '{group}' สำหรับ '{company_name}'")
            
            # กำหนดชื่อบริการตาม group จาก folder_settings
            if group == 'special':
                # special group → ใช้ GROUP3_COMPANY_MAPPING (NoneVat)
                if company_name in Config.GROUP3_COMPANY_MAPPING:
                    service_name = Config.GROUP3_COMPANY_MAPPING[company_name]
                    print(f"✅ ใช้ mapping จาก GROUP3 (special): '{service_name}'")
                else:
                    service_name = f"ค่าบริการ {company_name}"
                    print(f"⚠️ ไม่พบใน GROUP3 mapping ใช้ชื่อเต็ม: '{service_name}'")
            elif group == 'regular':
                # regular group → ใช้ GROUP1_COMPANY_MAPPING (VAT)
                if company_name in Config.GROUP1_COMPANY_MAPPING:
                    service_name = Config.GROUP1_COMPANY_MAPPING[company_name]
                    print(f"✅ ใช้ mapping จาก GROUP1 (regular): '{service_name}'")
                else:
                    service_name = f"ค่าบริการ {company_name} VAT"
                    print(f"⚠️ ไม่พบใน GROUP1 mapping ใช้ชื่อเต็ม: '{service_name}'")
            else:
                # fallback: ใช้ company_vat_status ถ้า group ไม่รู้จัก
                company_vat_status = Config.COMPANY_VAT_STATUS.get(company_name, 'VAT')
                print(f"⚠️ group='{group}' (unknown) → ใช้ company_vat_status='{company_vat_status}' เป็น fallback")
                
                if company_vat_status == 'VAT':
                    if company_name in Config.GROUP1_COMPANY_MAPPING:
                        service_name = Config.GROUP1_COMPANY_MAPPING[company_name]
                        print(f"✅ ใช้ mapping จาก GROUP1 (fallback VAT): '{service_name}'")
                    else:
                        service_name = f"ค่าบริการ {company_name} VAT"
                        print(f"⚠️ ไม่พบใน GROUP1 mapping ใช้ชื่อเต็ม: '{service_name}'")
                else:  # NoneVat
                    if company_name in Config.GROUP3_COMPANY_MAPPING:
                        service_name = Config.GROUP3_COMPANY_MAPPING[company_name]
                        print(f"✅ ใช้ mapping จาก GROUP3 (fallback NoneVat): '{service_name}'")
                    else:
                        service_name = f"ค่าบริการ {company_name}"
                        print(f"⚠️ ไม่พบใน GROUP3 mapping ใช้ชื่อเต็ม: '{service_name}'")
            
            print(f"🏷️ ชื่อบริการที่ได้: '{service_name}'")
            return service_name
            
        except Exception as e:
            print(f"⚠️ เกิดข้อผิดพลาดในการกำหนดชื่อบริการ: {e}")
            return f"ค่าบริการ {company_name}"

    def sanitize_filename(self, filename: str) -> str:
        """ทำความสะอาดชื่อไฟล์ (ลบอักขระที่ไม่สามารถใช้เป็นชื่อไฟล์ได้)"""
        try:
            # อักขระที่ไม่สามารถใช้เป็นชื่อไฟล์ได้
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\n', '\r', '\t']
            
            # แทนที่อักขระที่ไม่ถูกต้อง
            for char in invalid_chars:
                filename = filename.replace(char, ' ')
            
            # ลบช่องว่างที่ซ้ำกัน
            filename = ' '.join(filename.split())
            
            # จำกัดความยาวชื่อไฟล์ (ไม่เกิน 100 ตัวอักษร)
            if len(filename) > 100:
                filename = filename[:100]
            
            print(f"�� ชื่อไฟล์หลังทำความสะอาด: '{filename}'")
            return filename
            
        except Exception as e:
            print(f"⚠️ เกิดข้อผิดพลาดในการทำความสะอาดชื่อไฟล์: {e}")
            return "document"
    
    def copy_file_to_destination(self, source_file: str, destination_folder: str, new_filename: str = None) -> bool:
        """คัดลอกไฟล์ไปยังโฟลเดอร์ปลายทาง"""
        try:
            print(f"📁 กำลังคัดลอกไฟล์ไปยังโฟลเดอร์ปลายทาง...")
            
            # ตรวจสอบว่าไฟล์ต้นฉบับมีอยู่หรือไม่
            if not os.path.exists(source_file):
                print(f"❌ ไม่พบไฟล์ต้นฉบับ: {source_file}")
                return False
            
            # สร้างโฟลเดอร์ปลายทางถ้ายังไม่มี
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)
                print(f"📁 สร้างโฟลเดอร์ปลายทาง: {destination_folder}")
            
            # กำหนดชื่อไฟล์ปลายทาง
            if new_filename:
                destination_file = os.path.join(destination_folder, new_filename)
            else:
                destination_file = os.path.join(destination_folder, os.path.basename(source_file))
            
            # คัดลอกไฟล์
            shutil.copy2(source_file, destination_file)
            print(f"✅ คัดลอกไฟล์สำเร็จ: {source_file} -> {destination_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการคัดลอกไฟล์: {e}")
            return False
    
    def move_file_to_destination(self, source_file: str, destination_folder: str, new_filename: str = None) -> bool:
        """ย้ายไฟล์ไปยังโฟลเดอร์ปลายทาง"""
        try:
            print(f"📁 กำลังย้ายไฟล์ไปยังโฟลเดอร์ปลายทาง...")
            
            # ตรวจสอบว่าไฟล์ต้นฉบับมีอยู่หรือไม่
            if not os.path.exists(source_file):
                print(f"❌ ไม่พบไฟล์ต้นฉบับ: {source_file}")
                return False
            
            # สร้างโฟลเดอร์ปลายทางถ้ายังไม่มี
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)
                print(f"📁 สร้างโฟลเดอร์ปลายทาง: {destination_folder}")
            
            # กำหนดชื่อไฟล์ปลายทาง
            if new_filename:
                destination_file = os.path.join(destination_folder, new_filename)
            else:
                destination_file = os.path.join(destination_folder, os.path.basename(source_file))
            
            # ย้ายไฟล์
            shutil.move(source_file, destination_file)
            print(f"✅ ย้ายไฟล์สำเร็จ: {source_file} -> {destination_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการย้ายไฟล์: {e}")
            return False
    
    def cleanup_temp_files(self) -> bool:
        """ลบไฟล์ชั่วคราวทั้งหมด"""
        try:
            print(f"🗑️ กำลังลบไฟล์ชั่วคราว...")
            
            deleted_count = 0
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        print(f"🗑️ ลบไฟล์ชั่วคราวสำเร็จ: {temp_file}")
                        deleted_count += 1
                    else:
                        print(f"⚠️ ไม่พบไฟล์ชั่วคราว: {temp_file}")
                except Exception as e:
                    print(f"⚠️ ไม่สามารถลบไฟล์ชั่วคราวได้: {temp_file} - {e}")
            
            # ล้างรายการไฟล์ชั่วคราว
            self.temp_files.clear()
            
            print(f"✅ ลบไฟล์ชั่วคราวเสร็จสิ้น: {deleted_count} ไฟล์")
            return True
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการลบไฟล์ชั่วคราว: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Dict:
        """ดึงข้อมูลของไฟล์"""
        try:
            if not os.path.exists(file_path):
                return {"error": "ไฟล์ไม่พบ"}
            
            file_stat = os.stat(file_path)
            
            return {
                "filename": os.path.basename(file_path),
                "file_path": file_path,
                "file_size": file_stat.st_size,
                "created_time": time.ctime(file_stat.st_ctime),
                "modified_time": time.ctime(file_stat.st_mtime),
                "is_file": os.path.isfile(file_path),
                "is_directory": os.path.isdir(file_path)
            }
            
        except Exception as e:
            return {"error": f"เกิดข้อผิดพลาด: {e}"}
    
    def list_files_in_folder(self, folder_path: str, file_extension: str = None) -> list:
        """แสดงรายการไฟล์ในโฟลเดอร์"""
        try:
            if not os.path.exists(folder_path):
                print(f"❌ ไม่พบโฟลเดอร์: {folder_path}")
                return []
            
            files = []
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                
                if os.path.isfile(item_path):
                    if file_extension:
                        if item.lower().endswith(file_extension.lower()):
                            files.append(item)
                    else:
                        files.append(item)
            
            return sorted(files)
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการแสดงรายการไฟล์: {e}")
            return []
    
    def create_backup(self, source_file: str, backup_folder: str = "backup") -> bool:
        """สร้างไฟล์สำรอง"""
        try:
            print(f"💾 กำลังสร้างไฟล์สำรอง...")
            
            if not os.path.exists(source_file):
                print(f"❌ ไม่พบไฟล์ต้นฉบับ: {source_file}")
                return False
            
            # สร้างโฟลเดอร์สำรองถ้ายังไม่มี
            if not os.path.exists(backup_folder):
                os.makedirs(backup_folder)
                print(f"📁 สร้างโฟลเดอร์สำรอง: {backup_folder}")
            
            # สร้างชื่อไฟล์สำรอง
            filename = os.path.basename(source_file)
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{name}_{timestamp}{ext}"
            backup_path = os.path.join(backup_folder, backup_filename)
            
            # คัดลอกไฟล์สำรอง
            shutil.copy2(source_file, backup_path)
            print(f"✅ สร้างไฟล์สำรองสำเร็จ: {backup_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการสร้างไฟล์สำรอง: {e}")
            return False

    def move_original_and_processed(self, original_file: str, processed_file: str, group: str = 'unknown') -> bool:
        """ย้ายไฟล์ต้นฉบับไป 'เอกสารต้นฉบับ' และไฟล์ที่บันทึกแล้วไป 'เอกสาร Vat' หรือ 'เอกสาร NoneVat' ตามกลุ่ม
        คืนค่า True ถ้าย้ายสำเร็จอย่างน้อยหนึ่งรายการ
        """
        try:
            moved_any = False
            # หาโฟลเดอร์อ้างอิง
            parent = ''
            if original_file:
                parent = os.path.dirname(original_file)
            if not parent and processed_file:
                parent = os.path.dirname(processed_file)
            if not parent:
                print("⚠️ ไม่พบโฟลเดอร์ต้นทางสำหรับการย้ายไฟล์")
                return False

            # เอกสารต้นฉบับ (ไฟล์เดิมที่ไม่ได้เปลี่ยนชื่อ)
            if original_file and os.path.exists(original_file):
                dest_dir_o = os.path.join(parent, Config.OUTPUT_FOLDERS.get('original', 'เอกสารต้นฉบับ'))
                os.makedirs(dest_dir_o, exist_ok=True)
                dest_o = os.path.join(dest_dir_o, os.path.basename(original_file))
                if self._move_with_retry(original_file, dest_o):
                    print(f"✅ ย้ายไฟล์ต้นฉบับไป: {dest_o}")
                    moved_any = True
                else:
                    print("❌ ย้ายไฟล์ต้นฉบับไม่สำเร็จ")

            # เอกสารบันทึกแล้ว (แยกตามกลุ่ม) → ซ้อนภายใต้ "เอกสารบันทึกแล้ว/เอกสาร Vat|NoneVat"
            if processed_file and os.path.exists(processed_file):
                # กำหนดโฟลเดอร์ปลายทางตามกลุ่ม
                processed_root = Config.OUTPUT_FOLDERS.get('processed', 'เอกสารบันทึกแล้ว')
                if group == 'regular':
                    child = Config.OUTPUT_FOLDERS.get('vat', 'เอกสาร Vat')
                elif group == 'special':
                    child = Config.OUTPUT_FOLDERS.get('none_vat', 'เอกสาร NoneVat')
                else:
                    child = ''

                # โครงสร้าง: parent/เอกสารบันทึกแล้ว/(เอกสาร Vat|เอกสาร NoneVat)
                dest_dir_p = os.path.join(parent, processed_root)
                if child:
                    dest_dir_p = os.path.join(dest_dir_p, child)
                os.makedirs(dest_dir_p, exist_ok=True)
                dest_p = os.path.join(dest_dir_p, os.path.basename(processed_file))
                processed_label = processed_root if not child else f"{processed_root}/{child}"
                
                if self._move_with_retry(processed_file, dest_p):
                    print(f"✅ ย้ายไฟล์บันทึกแล้วไป {processed_label}: {dest_p}")
                    moved_any = True
                else:
                    print(f"⚠️ ย้ายไฟล์บันทึกแล้วไม่สำเร็จ ลองคัดลอกแทน")
                    try:
                        if self._copy_with_retry(processed_file, dest_p):
                            print(f"✅ คัดลอกไฟล์บันทึกแล้วไป {processed_label}: {dest_p}")
                            moved_any = True
                        else:
                            print("❌ คัดลอกไฟล์บันทึกแล้วไม่สำเร็จ")
                    except Exception as _:
                        print("❌ คัดลอกไฟล์บันทึกแล้วไม่สำเร็จ (ยกเว้น)")

            return moved_any
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการย้ายไฟล์ต้นฉบับ/บันทึกแล้ว: {e}")
            return False

    def move_file_to_processing_result(self, file_path: str, error_type: str = 'unreadable') -> Optional[str]:
        """ย้ายไฟล์ไปยังโฟลเดอร์ 'ผลการประมวลผล' ตามประเภทข้อผิดพลาด
        
        Args:
            file_path: พาธของไฟล์ที่จะย้าย
            error_type: ประเภทข้อผิดพลาด
                - 'database_error': ฐานข้อมูลไม่เรียบร้อย (Customer ID/Account Code ไม่มี)
                - 'pending_action': เอกสารรอดำเนินการ (อ่านข้อมูลได้บางส่วน)
                - 'unreadable': เอกสารอ่านข้อมูลไม่ได้ (ทั่วไป)
                - 'unreadable_image': เอกสาร PDF ภาพ
                - 'unreadable_not_implemented': ยังไม่ได้นำเข้าระบบ (ไม่มีโค้ดอ่าน)
        
        Returns:
            พาธปลายทางถ้าสำเร็จ, None ถ้าล้มเหลว
        """
        try:
            if not file_path or not os.path.exists(file_path):
                print(f"⚠️ ไม่พบไฟล์ที่จะย้าย: {file_path}")
                return None
            
            parent_dir = os.path.dirname(file_path)
            base_name = os.path.basename(file_path)
            
            # สร้างโฟลเดอร์ "ผลการประมวลผล" และโฟลเดอร์ย่อยตามประเภท
            processing_result_dir = os.path.join(parent_dir, Config.OUTPUT_FOLDERS.get('processing_result', 'ผลการประมวลผล'))
            
            # กำหนดโฟลเดอร์ย่อยตามประเภทข้อผิดพลาด
            if error_type == 'database_error':
                sub_folder = Config.OUTPUT_FOLDERS.get('database_error', '1. ฐานข้อมูลไม่เรียบร้อย')
            elif error_type == 'pending_action':
                sub_folder = Config.OUTPUT_FOLDERS.get('pending_action', '2. เอกสารรอดำเนินการ')
            elif error_type == 'unreadable_image':
                # ซ้อนภายใต้ "3. เอกสารอ่านข้อมูลไม่ได้/3.1 เอกสาร PDF ภาพ"
                parent_folder = Config.OUTPUT_FOLDERS.get('unreadable', '3. เอกสารอ่านข้อมูลไม่ได้')
                child_folder = Config.OUTPUT_FOLDERS.get('unreadable_image', '3.1 เอกสาร PDF ภาพ')
                sub_folder = f"{parent_folder}/{child_folder}"
            elif error_type == 'unreadable_not_implemented':
                # ซ้อนภายใต้ "3. เอกสารอ่านข้อมูลไม่ได้/3.2 ยังไม่ได้นำเข้าระบบ"
                parent_folder = Config.OUTPUT_FOLDERS.get('unreadable', '3. เอกสารอ่านข้อมูลไม่ได้')
                child_folder = Config.OUTPUT_FOLDERS.get('unreadable_not_implemented', '3.2 ยังไม่ได้นำเข้าระบบ')
                sub_folder = f"{parent_folder}/{child_folder}"
            else:  # 'unreadable'
                sub_folder = Config.OUTPUT_FOLDERS.get('unreadable', '3. เอกสารอ่านข้อมูลไม่ได้')
            
            dest_dir = os.path.join(processing_result_dir, sub_folder)
            os.makedirs(dest_dir, exist_ok=True)
            
            dest_path = os.path.join(dest_dir, base_name)
            
            # ถ้ามีไฟล์ชื่อเดียวกันอยู่แล้ว ให้ลบไฟล์เก่าทิ้ง
            if os.path.exists(dest_path):
                print(f"⚠️ พบไฟล์ชื่อเดียวกันอยู่แล้ว จะลบไฟล์เก่าและใช้ไฟล์ใหม่แทน")
                try:
                    os.remove(dest_path)
                    print(f"🗑️ ลบไฟล์เก่าสำเร็จ")
                except Exception as e:
                    print(f"⚠️ ไม่สามารถลบไฟล์เก่าได้: {e}")
                    # ถ้าลบไม่ได้ ให้เพิ่ม timestamp
                    name, ext = os.path.splitext(base_name)
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    dest_path = os.path.join(dest_dir, f"{name}_{ts}{ext}")
            
            if self._move_with_retry(file_path, dest_path):
                print(f"✅ ย้ายไฟล์ไปยัง '{sub_folder}' สำเร็จ: {dest_path}")
                return dest_path
            else:
                print(f"❌ ย้ายไฟล์ไปยัง '{sub_folder}' ไม่สำเร็จ")
                return None
                
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการย้ายไฟล์ไปยังผลการประมวลผล: {e}")
            return None
