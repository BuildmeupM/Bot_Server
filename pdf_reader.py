import PyPDF2
import re
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from config import Config
from report_manager import ReportManager, line_notify, line_oa_push, set_global_report_manager, get_global_report_manager

class PDFReader:
    def __init__(self, pdf_directory=None):
        self.extracted_data = {}
        self.pdf_directory = pdf_directory
        self.last_batch_report = {
            'total': 0,
            'read_success': 0,
            'read_failed': 0,
            'skipped': []  # list of {'file': str, 'reason': str}
        }
        # เพิ่ม FileManager สำหรับย้ายไฟล์
        from file_manager import FileManager
        self.file_manager = FileManager()
        
    def _detect_company_by_patterns(self, lines: List[str], pdf_file: str) -> Optional[str]:
        """พยายามเดาชื่อบริษัทจากชื่อไฟล์/ข้อความ เมื่อไม่มีไฟล์ JSON
        คืนค่าเป็นชื่อบริษัทแบบเดียวกับที่ระบบใช้ในสาขาต่างๆ ด้านล่าง
        """
        try:
            joined = "\n".join(lines)
            low_text = joined.lower()
            low_name = (pdf_file or "").lower()

            # ตรวจสอบชื่อบริษัทจากข้อมูลจริงใน PDF ก่อน
            # ตรวจหา "Merchant Name" หรือ "Bill To" section
            for line in lines:
                if "merchant name" in line.lower() or "bill to" in line.lower():
                    # หาบรรทัดถัดไปที่อาจมีชื่อบริษัท
                    current_index = lines.index(line)
                    for i in range(current_index + 1, min(current_index + 5, len(lines))):
                        next_line = lines[i].strip()
                        if next_line and not next_line.lower().startswith(('address', 'tax number', 'billing')):
                            # ตรวจสอบว่าเป็นชื่อบริษัทไทยหรืออังกฤษ
                            if any(keyword in next_line.lower() for keyword in ['บริษัท', 'co.,', 'ltd', 'limited', 'inc']):
                                print(f"🔍 พบชื่อบริษัทจาก PDF: {next_line}")
                                return next_line
            
            # ตรวจสอบชื่อบริษัทจากรูปแบบอื่นๆ ในเอกสาร
            for line in lines:
                # ตรวจหาชื่อบริษัทที่ขึ้นต้นด้วย "บริษัท"
                if line.strip().startswith('บริษัท') and ('จำกัด' in line or 'มหาชน' in line):
                    print(f"🔍 พบชื่อบริษัทไทยจาก PDF: {line.strip()}")
                    return line.strip()
                
                # ตรวจหาชื่อบริษัทภาษาอังกฤษ
                if any(keyword in line.lower() for keyword in ['co., ltd', 'limited', 'inc.']) and len(line.strip()) > 10:
                    print(f"🔍 พบชื่อบริษัทอังกฤษจาก PDF: {line.strip()}")
                    return line.strip()

            # Shopee
            if ("trsp" in low_name) or ("shopee" in low_name) or ("shopee" in low_text):
                return "Shopee (Thailand) Co., Ltd."

            # SPX Express
            if ("rcspx" in low_name) or ("spx" in low_name) or ("spx express" in low_text):
                return "SPX Express (Thailand) Co., Ltd."

            # Lazada Express vs Lazada
            if ("lazada express" in low_text) or ("lazada express" in low_name):
                return "Lazada Express Limited"
            if ("lazada" in low_text) or ("lazada" in low_name):
                return "Lazada Limited (Head Office)"

            # TikTok logistics - ตรวจสอบให้แน่ใจว่ามี "thai happy logistics" จริงๆ
            if "thai happy logistics" in low_text:
                return "Thai Happy Logistics Ltd. (Head Office)"
            # ไม่ให้เดาจาก "tiktok" เพียงอย่างเดียว เพราะอาจเป็นบริษัทอื่น

            # LINE MAN
            if ("line man" in low_text) or ("lineman" in low_text):
                return "บริษัท ไลน์แมน (ประเทศไทย) จำกัด (สำนักงานใหญ่)"

            # Foodpanda
            if "delivery hero (thailand) co., ltd" in low_text or "foodpanda" in low_text:
                return "Delivery Hero (Thailand) Co., Ltd."

            # Grab
            if "grab" in low_text or "gf.th.ar@grab.com" in low_text:
                return "gf.th.ar@grab.com"

            # K-BIZ (Kasikorn)
            if "k-biz" in low_text or "kbiz" in low_text or "k-biz contact" in low_text:
                return "K-BIZ Contact"

            # TrueMoney
            if "true money" in low_text or "truemoney" in low_text or "บริษัท ทรู มันนี่ จำกัด" in low_text:
                return "บริษัท ทรู มันนี่ จำกัด"

            # Purple Ventures (Robinhood)
            if "purple ventures" in low_text or "robinhood" in low_text:
                return "Purple Ventures Company Limited"

            # LINE Company (corporate)
            if "line company (thailand) limited" in low_text or ("tax invoice" in low_text and "line" in low_text):
                return "LINE Company (THAILAND) LIMITED"

            # AIS (Advanced Wireless Network)
            if "advanced wireless network" in low_text or "ais" in low_text or "บริษัท แอดวานซ์ ไวร์เลส เน็ทเวอร์ค จํากัด" in low_text:
                return "บริษัท แอดวานซ์ ไวร์เลส เน็ทเวอร์ค จํากัด"

            # กาแฟพันธุ์ไทย
            if "กาแฟพันธุ์ไทย" in joined:
                return "บริษัท กาแฟพันธุ์ไทย จำกัด"

            # Maxcard
            if "max card" in low_text or "maxcard" in low_text or "บริษัท แมกซ์ การ์ด จำกัด" in low_text:
                return "บริษัท แมกซ์ การ์ด จำกัด"

            # Ksher Payment
            if "ksher" in low_text:
                return "Ksher Payment Co., Ltd."

            # Shippop (both Thai and Eng names)
            if "shippop co., ltd" in low_text or "บริษัท ชิปป๊อป" in joined:
                # เลือกชื่อที่ระบบใช้สองแบบ ถ้าพบภาษาไทยให้คืนชื่อไทย
                if "บริษัท ชิปป๊อป" in joined:
                    return "บริษัท ชิปป๊อป จำกัด (สำนักงานใหญ่)"
                return "Shippop Co., Ltd. (Headquarter)"

            # TTB Bank
            if "ttbbank.com" in low_text or ("ttb" in low_text and "bank" in low_text):
                return "ttbbank.com"

            # Kerry Express (KEX)
            if "kerry express" in low_text or "เคอีเอ็กซ์" in joined or "kex" in low_text:
                return "บริษัท เคอีเอ็กซ์ เอ็กซ์เพรส (ประเทศไทย) จำกัด (มหาชน)"

            # TikTok Shop (Head Office)
            if "tiktok shop" in low_text:
                return "TikTok Shop (Thailand) Ltd. (Head Office)"

            return None
        except Exception:
            return None

    def _is_pdf_text_empty(self, pdf_path: Path) -> bool:
        """ตรวจว่าไฟล์ PDF เป็นแบบรูปภาพ (ไม่มี text layer) หรือไม่"""
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []
                for pg in getattr(reader, 'pages', []) or []:
                    try:
                        t = pg.extract_text() or ""
                    except Exception:
                        t = ""
                    if t:
                        text_parts.append(t)
                return len(("\n".join(text_parts)).strip()) == 0
        except Exception:
            # ถ้าเปิดอ่านไม่ได้ ให้ถือว่าไม่ใช่ภาพ (จะถูกจัดเป็น not_implemented ต่อไป)
            return False

    def read_pdf(self, pdf_path: Path, custom_keywords: Dict = None) -> Dict:
        """อ่านไฟล์ PDF และดึงข้อมูลที่ต้องการ"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""
                
                # อ่านข้อความจากทุกหน้า
                for page in pdf_reader.pages:
                    text_content += page.extract_text()
                
                # แบ่งข้อความเป็นบรรทัด
                lines = text_content.split('\n')
                
                # ใช้ method extract_keyword_from_text ที่มีการอ่านข้อมูลจริง
                # หาโฟลเดอร์รหัสจากพาธของไฟล์ PDF
                pdf_parent = pdf_path.parent
                # หาโฟลเดอร์ Build* จากพาธ
                build_folder = None
                current_path = pdf_parent
                while current_path != current_path.parent:
                    if current_path.name.startswith('Build'):
                        build_folder = current_path
                        break
                    current_path = current_path.parent
                
                if build_folder:
                    # ใช้แค่หมายเลข BuildXXX (เช่น Build000 ทดสอบระบบ → Build000)
                    folder_name = build_folder.name
                    build_number = folder_name.split()[0]  # แยกเอาแค่ "Build000"
                    # เส้นทางหลักภายในโฟลเดอร์ Build ปัจจุบัน
                    local_json_path = Path(build_folder) / "รหัส" / f"{build_number}.json"
                    
                    # เส้นทางสำรองศูนย์รวมที่ Build000 ทดสอบระบบ (ลอง A., AA., AAA.)
                    drive_root = Path(f"{Config.BASE_FOLDER}:/")
                    central_candidates = []
                    for main_name in getattr(Config, 'MAIN_FOLDERS', ["A.โฟร์เดอร์หลัก", "AA.โฟรเดอร์หลัก", "AAA.โฟรเดอร์หลัก"]):
                        central_candidates.append(
                            drive_root / main_name / f"Build{Config.TEST_SYSTEM_FOLDER}" / "รหัส" / f"{build_number}.json"
                        )
                    # ยังคงลองตำแหน่งเดิม (เผื่อมี V:/Build000 ทดสอบระบบ/รหัส)
                    central_candidates.append(
                        drive_root / f"Build{Config.TEST_SYSTEM_FOLDER}" / "รหัส" / f"{build_number}.json"
                    )
                    
                    # เลือกไฟล์ที่มีอยู่จริงตามลำดับ
                    chosen_json = None
                    if local_json_path.exists():
                        chosen_json = local_json_path
                    else:
                        for c in central_candidates:
                            if c.exists():
                                chosen_json = c
                                break
                    
                    # debug แสดง candidate ทั้งหมด
                    try:
                        print("🔎 ค้นหา JSON จากตำแหน่งต่อไปนี้ (ลำดับความสำคัญ):")
                        print(f"  1) {local_json_path} (local)")
                        for idx, c in enumerate(central_candidates, start=2):
                            print(f"  {idx}) {c}")
                        print(f"➡️ ใช้งาน: {chosen_json if chosen_json else 'ไม่พบไฟล์ที่ตรงกัน'}")
                    except Exception:
                        pass

                    json_file_path = str(chosen_json) if chosen_json else str(central_candidates[0])
                    # ตั้งค่า pdf_directory ให้ extract_keyword_from_text ใช้ได้
                    self.pdf_directory = str(build_folder)
                    result = self.extract_keyword_from_text(lines, json_file_path, pdf_path.name)
                else:
                    result = None
                
                if result:
                    return result
                else:
                    # ถ้าไม่พบข้อมูลจาก extract_keyword_from_text ให้ใช้วิธีเดิม
                    return self.extract_invoice_data(text_content, pdf_path.name, custom_keywords)
                
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return {}  

    def process_pdf_batch(self, pdf_files: List[Path], json_config: Dict = None) -> List[Dict]:
        """อ่านไฟล์ PDF เป็นชุด พร้อมบันทึกเหตุผลที่อ่านไม่ได้/ข้าม
        คืนค่ารายการ pdf_data ที่อ่านสำเร็จเท่านั้น และอัปเดตรายงานไว้ใน self.last_batch_report
        """
        results: List[Dict] = []
        self.last_batch_report = {
            'total': len(pdf_files or []),
            'read_success': 0,
            'read_failed': 0,
            'skipped': []
        }

        if not pdf_files:
            print("⚠️ ไม่มีไฟล์ PDF ในชุดที่จะอ่าน")
            return results

        # ---------- เตรียม ReportManager และส่งข้อความเริ่มงาน ----------
        try:
            # คำนวณ main_folder จากโครงสร้าง: .../<main_folder>/ลูกค้า/ระบบอัตโนมัติ/xxx.pdf
            first_pdf = Path(pdf_files[0])
            main_folder = None
            for parent in first_pdf.parents:
                if parent.name == Config.CUSTOMER_FOLDER and parent.parent:
                    main_folder = parent.parent
                    break
            if not main_folder:
                # fallback: ใช้โฟลเดอร์ของไฟล์แรก
                main_folder = first_pdf.parent

            rm = ReportManager(str(main_folder))

            # ระบุ group จาก folder_settings โดยดูจาก folder_code
            try:
                folder_settings = self.file_manager.read_folder_settings()
            except Exception:
                folder_settings = {}
            try:
                folder_code = self.file_manager.get_folder_code_from_path(main_folder)
            except Exception:
                folder_code = None
            group = 'unknown'
            if folder_code and folder_settings and folder_code in folder_settings:
                group = folder_settings[folder_code].get('group', 'unknown')
            rm.set_group(folder_code or '', group)

            # ตั้งค่าโฟลเดอร์สำหรับวางรายงาน .txt
            automation_folder = Path(main_folder) / Config.CUSTOMER_FOLDER / Config.AUTOMATION_FOLDER
            rm.set_automation_folder(automation_folder)

            # เตรียมข้อมูลเบื้องต้นแล้วส่งข้อความเริ่มต้น
            rm.prepare_from_batch({'total': len(pdf_files), 'read_success': 0, 'read_failed': 0}, pdf_files, None)
            # เริ่มต้นตัวนับสถานะอื่นให้แสดง 0/x ในช่วง start
            try:
                rm.pending_action_count = 0
                rm.unreadable_image_count = 0
                rm.unreadable_not_implemented_count = 0
                rm.database_error_count = 0
            except Exception:
                pass
            start_message = rm.start()
            # เก็บเป็น global สำหรับโมดูลอื่นใช้งานตอนจบงาน
            try:
                set_global_report_manager(rm)
            except Exception:
                pass
            # ส่งผ่าน OA ถ้าตั้งค่าไว้ มิฉะนั้นลอง Notify
            sent = False
            try:
                if getattr(Config, 'LINE_OA_CHANNEL_ACCESS_TOKEN', '') and getattr(Config, 'LINE_OA_DEFAULT_TO', ''):
                    sent = line_oa_push(start_message)
                elif getattr(Config, 'LINE_NOTIFY_TOKEN', ''):
                    sent = line_notify(start_message)
            except Exception:
                sent = False
            if not sent:
                print("ℹ️ ไม่ได้ส่ง LINE start (ไม่มี token OA/Notify หรือล้มเหลว)")
        except Exception as _:
            rm = None

        for idx, pdf_path in enumerate(pdf_files, 1):
            try:
                if not pdf_path.exists():
                    reason = 'ไฟล์ไม่พบ'
                    print(f"❌ [{idx}] ข้าม {pdf_path.name}: {reason}")
                    self.last_batch_report['read_failed'] += 1
                    self.last_batch_report['skipped'].append({'file': str(pdf_path), 'reason': reason})
                    continue

                data = self.read_pdf(pdf_path)
                if not data:
                    reason = 'อ่านไม่สำเร็จหรือไม่พบข้อมูลที่ต้องการ'
                    print(f"❌ [{idx}] ข้าม {pdf_path.name}: {reason}")
                    self.last_batch_report['read_failed'] += 1
                    self.last_batch_report['skipped'].append({'file': str(pdf_path), 'reason': reason})
                    # ย้ายไฟล์ไปยังหมวดย่อยของ "เอกสารอ่านข้อมูลไม่ได้"
                    if self._is_pdf_text_empty(pdf_path):
                        print("📦 จัดเป็น: 3.1 เอกสาร PDF ภาพ")
                        self.file_manager.move_file_to_processing_result(str(pdf_path), error_type='unreadable_image')
                        try:
                            rm = get_global_report_manager()
                            if rm:
                                rm.add_unreadable_image(1)
                        except Exception:
                            pass
                    else:
                        print("📦 จัดเป็น: 3.2 ยังไม่ได้นำเข้าระบบ")
                        self.file_manager.move_file_to_processing_result(str(pdf_path), error_type='unreadable_not_implemented')
                        try:
                            rm = get_global_report_manager()
                            if rm:
                                rm.add_unreadable_not_implemented(1)
                        except Exception:
                            pass
                    continue

                # ทำให้คีย์เป็นมาตรฐานที่ระบบเว็บใช้งาน
                normalized = {
                    'filename': data.get('filename') or pdf_path.name,
                    'file_path': str(pdf_path),
                    'company_name': data.get('company_name') or data.get('company_info', {}).get('company_name', ''),
                    'customer_id': data.get('customer_id') or data.get('customer_code') or data.get('company_info', {}).get('customer_id', ''),
                    'account_code': data.get('account_code') or data.get('company_info', {}).get('account_code', ''),
                    'account_code2': data.get('account_code2') or data.get('company_info', {}).get('account_code2', ''),
                    'document_number': data.get('document_number') or data.get('document_info', {}).get('document_number', ''),
                    'document_date': data.get('document_date') or data.get('document_info', {}).get('date', ''),
                    'total_ex_vat': data.get('total_ex_vat') or data.get('financial_info', {}).get('excluded_vat', ''),
                    'total_ex_vat_none': data.get('total_ex_vat_none') or data.get('financial_info', {}).get('excluded_vat_none', ''),
                    'vat_value': data.get('vat_value') or data.get('financial_info', {}).get('vat_amount', ''),
                    'total_in_vat': data.get('total_in_vat') or data.get('financial_info', {}).get('included_vat', ''),
                }

                # ตรวจขั้นต่ำว่าเพียงพอสำหรับเว็บอัตโนมัติไหม
                required_keys = ['customer_id', 'account_code', 'document_number', 'document_date', 'total_in_vat']
                missing = [k for k in required_keys if not normalized.get(k)]
                
                if missing:
                    reason = f"ข้อมูลไม่ครบ: {', '.join(missing)}"
                    print(f"❌ [{idx}] ข้าม {pdf_path.name}: {reason}")
                    self.last_batch_report['read_failed'] += 1
                    self.last_batch_report['skipped'].append({'file': str(pdf_path), 'reason': reason})
                    
                    # จัดประเภทข้อผิดพลาดและย้ายไฟล์
                    company_name = normalized.get('company_name', '')
                    customer_id = normalized.get('customer_id', '')
                    account_code = normalized.get('account_code', '')
                    
                    # เงื่อนไข 1: ไม่มี company_name เลย → เอกสารอ่านข้อมูลไม่ได้ (ย่อย: ภาพ/ยังไม่ได้นำเข้าระบบ)
                    if not company_name:
                        if self._is_pdf_text_empty(pdf_path):
                            print(f"📦 ย้ายไปยัง: 3. เอกสารอ่านข้อมูลไม่ได้/3.1 เอกสาร PDF ภาพ")
                            self.file_manager.move_file_to_processing_result(str(pdf_path), error_type='unreadable_image')
                            try:
                                rm = get_global_report_manager()
                                if rm:
                                    rm.add_unreadable_image(1)
                            except Exception:
                                pass
                        else:
                            print(f"📦 ย้ายไปยัง: 3. เอกสารอ่านข้อมูลไม่ได้/3.2 ยังไม่ได้นำเข้าระบบ")
                            self.file_manager.move_file_to_processing_result(str(pdf_path), error_type='unreadable_not_implemented')
                            try:
                                rm = get_global_report_manager()
                                if rm:
                                    rm.add_unreadable_not_implemented(1)
                            except Exception:
                                pass
                    
                    # เงื่อนไข 2: มี company_name แต่ไม่มี customer_id หรือ account_code → ฐานข้อมูลไม่เรียบร้อย
                    elif not customer_id or not account_code:
                        print(f"📦 ย้ายไปยัง: 1. ฐานข้อมูลไม่เรียบร้อย (มีบริษัทแต่ไม่มีข้อมูลในฐาน)")
                        self.file_manager.move_file_to_processing_result(str(pdf_path), error_type='database_error')
                        try:
                            rm = get_global_report_manager()
                            if rm:
                                rm.add_database_error(1)
                        except Exception:
                            pass
                    
                    # เงื่อนไข 3: มี customer_id, account_code แต่ขาดข้อมูลอื่น → เอกสารรอดำเนินการ
                    else:
                        print(f"📦 ย้ายไปยัง: 2. เอกสารรอดำเนินการ (อ่านได้บางส่วน)")
                        self.file_manager.move_file_to_processing_result(str(pdf_path), error_type='pending_action')
                        try:
                            rm = get_global_report_manager()
                            if rm:
                                rm.add_pending_action(1)
                        except Exception:
                            pass
                    
                    continue

                results.append(normalized)
                self.last_batch_report['read_success'] += 1
                print(f"✅ [{idx}] อ่านสำเร็จ: {pdf_path.name}")
            except Exception as e:
                reason = f"ข้อยกเว้นขณะอ่าน: {e}"
                print(f"❌ [{idx}] ข้าม {pdf_path.name}: {reason}")
                self.last_batch_report['read_failed'] += 1
                self.last_batch_report['skipped'].append({'file': str(pdf_path), 'reason': reason})
                # ย้ายไฟล์ไป "3. เอกสารอ่านข้อมูลไม่ได้"
                self.file_manager.move_file_to_processing_result(str(pdf_path), error_type='unreadable')

        # สรุป batch
        total = self.last_batch_report['total']
        ok = self.last_batch_report['read_success']
        fail = self.last_batch_report['read_failed']
        print(f"\n📊 สรุปการอ่าน PDF ชุดนี้: {ok}/{total} ไฟล์สำเร็จ, ข้าม {fail} ไฟล์")
        if fail:
            print("สาเหตุไฟล์ที่ถูกข้าม:")
            for item in self.last_batch_report['skipped']:
                print(f" - {Path(item['file']).name}: {item['reason']}")

        # ---------- อัปเดต ReportManager ด้วยผลลัพธ์ และบันทึกรายงาน (ไม่ส่งสรุป LINE ที่ผู้ใช้ไม่ต้องการ) ----------
        # เรียงลำดับผลลัพธ์ตามวันที่เอกสาร (จากต้นเดือน → สิ้นเดือน)
        def _parse_document_date(value: Optional[str]) -> datetime:
            if not value:
                return datetime.max
            text = str(value).strip()
            if not text:
                return datetime.max
            date_formats = (
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%Y-%m-%d",
                "%d.%m.%Y",
                "%Y/%m/%d",
            )
            for fmt in date_formats:
                try:
                    return datetime.strptime(text, fmt)
                except Exception:
                    continue
            digits_only = re.sub(r"\D", "", text)
            if len(digits_only) == 8:
                try:
                    day = int(digits_only[0:2])
                    month = int(digits_only[2:4])
                    year = int(digits_only[4:8])
                    return datetime(year, month, day)
                except Exception:
                    pass
            return datetime.max

        try:
            results.sort(
                key=lambda item: (
                    _parse_document_date(item.get('document_date')),
                    item.get('document_number') or '',
                    item.get('filename') or ''
                )
            )
        except Exception as sort_err:
            print(f"⚠️ ไม่สามารถเรียงลำดับตามวันที่ได้: {sort_err}")

        try:
            if rm is not None:
                # นับจำนวนไฟล์ต่อบริษัทจากผลลัพธ์
                comp_counts: Dict[str, int] = {}
                for r in results:
                    comp = (r.get('company_name') or '').strip()
                    if not comp:
                        continue
                    comp_counts[comp] = comp_counts.get(comp, 0) + 1

                rm.prepare_from_batch(self.last_batch_report, pdf_files, comp_counts or None)
                # (ย้ายไปสร้างรายงานฉบับสุดท้ายตอนจบ workflow ใน web_automation_playwright)
                # ที่นี่ไม่สร้างเพื่อหลีกเลี่ยงรายงานกลางงานที่สรุปผลอัปโหลดไม่ครบ
        except Exception as _:
            pass
        return results

    def get_last_batch_report(self) -> Dict:
        """คืนค่ารายงานรอบล่าสุดของการอ่าน PDF แบบชุด"""
        return self.last_batch_report

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
    
    def read_txt_file(self, file_path):
        """อ่านไฟล์ TXT"""
        if not os.path.exists(file_path):
            print(f"❌ ไม่พบไฟล์ TXT: {file_path}")
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดขณะอ่าน TXT: {e}")
            return None
    
    def read_company_data_from_json(self, company_name):
        """อ่านข้อมูลบริษัทจากไฟล์ JSON"""
        try:
            # กำหนด path ไปยังไฟล์ JSON หลัก
            json_file_path = "V:/A.โฟร์เดอร์หลัก/Build000 ทดสอบระบบ/รหัส/Build000.json"
            
            if not os.path.exists(json_file_path):
                print(f"❌ ไม่พบไฟล์ JSON: {json_file_path}")
                return None
                
            json_data = self.read_json_file(json_file_path)
            if not json_data:
                return None
                
            # ค้นหาข้อมูลบริษัทในไฟล์ JSON
            for key, data in json_data.items():
                json_company_name = data.get("company_name", "")
                # ตรวจสอบชื่อบริษัทแบบไม่เคร่งครัดเรื่องตัวพิมพ์เล็ก-ใหญ่
                if company_name.lower() in json_company_name.lower() or json_company_name.lower() in company_name.lower():
                    return {
                        "customer_id": data.get("customer_id", "ไม่พบ"),
                        "account_code": data.get("account_code", "ไม่พบ"),
                        "account_code2": data.get("account_code2", "ไม่พบ")
                    }
            
            print(f"❌ ไม่พบข้อมูลบริษัท '{company_name}' ในไฟล์ JSON")
            return None
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการอ่านข้อมูลจาก JSON: {e}")
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
    
    def extract_invoice_data(self, text_content: str, pdf_filename: str, custom_keywords: Dict = None) -> Dict:
        """ดึงข้อมูลใบแจ้งหนี้จากข้อความ PDF ตามคีย์เวิร์ดที่กำหนด"""
        try:
            if not text_content.strip():
                print(f"ไฟล์ PDF {pdf_filename} ไม่มีข้อความ")
                return {}
            
            # แบ่งข้อความเป็นบรรทัด
            lines = text_content.split('\n')
            
            # ดึงข้อมูลพื้นฐาน
            extracted_data = {
                "filename": pdf_filename,
                "total_lines": len(lines),
                "text_content": text_content[:500] + "..." if len(text_content) > 500 else text_content,
                "keywords_found": [],
                "company_info": {},
                "document_info": {},
                "financial_info": {}
            }
            
            # ใช้คีย์เวิร์ดที่ส่งมาจากการเรียกใช้งาน หรือใช้ค่าเริ่มต้น
            if custom_keywords:
                company_keywords = custom_keywords.get("company_keywords", [])
                document_keywords = custom_keywords.get("document_keywords", [])
                financial_keywords = custom_keywords.get("financial_keywords", [])
                date_keywords = custom_keywords.get("date_keywords", [])
            else:
                # ค่าเริ่มต้นเมื่อไม่มีการกำหนดคีย์เวิร์ด
                company_keywords = []
                document_keywords = []
                financial_keywords = []
                date_keywords = []  
            
            # ค้นหาข้อมูลบริษัท
            for keyword in company_keywords:
                if keyword.lower() in text_content.lower():
                    extracted_data["company_info"]["company_name"] = keyword
                    extracted_data["keywords_found"].append(f"company: {keyword}")
                    break
            
            # ค้นหาเลขที่เอกสาร
            for keyword in document_keywords:
                if keyword in text_content:
                    extracted_data["document_info"]["document_type"] = keyword
                    extracted_data["keywords_found"].append(f"document: {keyword}")
                    
                    # ค้นหาตัวเลขเพิ่มเติมสำหรับเลขที่เอกสาร
                    import re
                    if "TRSP" in keyword:
                        # ค้นหาตัวเลขที่ตามหลัง TRSP pattern
                        pattern = r'\d{4}-\d{6,7}'
                        matches = re.findall(pattern, text_content)
                        if matches:
                            # ต่อเลขที่เอกสารแบบไม่มีช่องว่าง
                            extracted_data["document_info"]["document_number"] = f"{keyword}{matches[0]}"
                        else:
                            extracted_data["document_info"]["document_number"] = keyword
                    elif "EXP-" in keyword:
                        # ค้นหาเลขที่เอกสาร EXP
                        pattern = r'EXP-\d{8}\d{5}'
                        matches = re.findall(pattern, text_content)
                        if matches:
                            extracted_data["document_info"]["document_number"] = matches[0]
                        else:
                            extracted_data["document_info"]["document_number"] = keyword
                    break
            
            # ค้นหาวันที่
            for keyword in date_keywords:
                if keyword in text_content:
                    # ดึงวันที่ที่อยู่หลังคีย์เวิร์ด
                    for line in lines:
                        if keyword in line:
                            date_part = line.split(keyword)[-1].strip()
                            if date_part:
                                extracted_data["document_info"]["date"] = date_part
                                extracted_data["keywords_found"].append(f"date: {date_part}")
                            break
                    break
            
            # ค้นหาข้อมูลทางการเงิน
            for keyword in financial_keywords:
                if keyword in text_content:
                    for line in lines:
                        if keyword in line:
                            # ดึงจำนวนเงินที่อยู่หลังคีย์เวิร์ด
                            amount_part = line.split(keyword)[-1].strip()
                            if amount_part:
                                if "VAT" in keyword and "Excluded" not in keyword and "Included" not in keyword:
                                    extracted_data["financial_info"]["vat_amount"] = amount_part
                                elif "Excluded VAT" in keyword and "after discount" in keyword:
                                    extracted_data["financial_info"]["excluded_vat"] = amount_part
                                elif "Excluded VAT" in keyword and "after discount" not in keyword:
                                    extracted_data["financial_info"]["excluded_vat_none"] = amount_part
                                elif "Included VAT" in keyword:
                                    extracted_data["financial_info"]["included_vat"] = amount_part
                                elif "Total" in keyword and "Amount" in keyword:
                                    extracted_data["financial_info"]["total_amount"] = amount_part
                                
                                extracted_data["keywords_found"].append(f"financial: {keyword} = {amount_part}")
                            break
            
            # ค้นหาตัวเลขที่เป็นจำนวนเงิน (เฉพาะที่เกี่ยวข้อง)
            import re
            amount_patterns = [
                r'\d+\.?\d*\s*บาท',  # จำนวนเงินในบาท
                r'฿\s*\d+\.?\d*',   # จำนวนเงินในสัญลักษณ์บาท
                r'\$\s*\d+\.?\d*',  # จำนวนเงินในดอลลาร์
            ]
            
            amounts_found = []
            for pattern in amount_patterns:
                matches = re.findall(pattern, text_content)
                amounts_found.extend(matches)
            
            if amounts_found:
                extracted_data["financial_info"]["amounts_found"] = amounts_found[:5]  # แสดงแค่ 5 รายการแรก
            
            # อ่านข้อมูลเพิ่มเติมจากไฟล์ JSON หากมีบริษัท
            company_name = extracted_data["company_info"].get("company_name")
            if company_name and self.pdf_directory:
                json_data = self.read_company_data_from_json(company_name)
                if json_data:
                    extracted_data["company_info"].update(json_data)
            
            # แสดงผลในรูปแบบที่กำหนด
            print(f"✅ ดึงข้อมูลจาก PDF สำเร็จ: {pdf_filename}")
            print(f"Customer_id : {extracted_data['company_info'].get('customer_id', 'ไม่พบ')}")
            print(f"Account_code : {extracted_data['company_info'].get('account_code', 'ไม่พบ')}")
            print(f"Account_code2 : {extracted_data['company_info'].get('account_code2', 'ไม่พบ')}")
            print(f"เลขที่เอกสาร : {extracted_data['document_info'].get('document_number', 'ไม่พบ')}")
            print(f"วันที่เอกสาร : {extracted_data['document_info'].get('date', 'ไม่พบ')}")
            print(f"ยอดก่อนภาษีมูลค่าเพิ่ม : {extracted_data['financial_info'].get('excluded_vat', 'ไม่พบ')}")
            print(f"ยอดก่อนภาษีมูลค่าเพิ่ม (NoneVat) : {extracted_data['financial_info'].get('excluded_vat_none', 'ไม่พบ')}")
            print(f"ยอดภาษีมูลค่าเพิ่ม : {extracted_data['financial_info'].get('vat_amount', 'ไม่พบ')}")
            print(f"ยอดหลังบวกภาษีมูลค่าเพิ่ม : {extracted_data['financial_info'].get('included_vat', 'ไม่พบ')}")
            
            return extracted_data
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
            return {"error": str(e), "filename": pdf_filename}
    
    def extract_keyword_from_text(self, lines, json_file_path, pdf_file):
        print(f"เช็คสถานะการอ่าน PDF: {self.pdf_directory}")
        if not self.pdf_directory:
            print("ระบบไม่สามารถอ่านไฟล์ PDF ได้ไฟล์ว่าง")
            return None
        print(f"กำลังอ่านไฟล์ผังบัญชี {json_file_path}")
        json_data = self.read_json_file(json_file_path)
        if not json_data:
            print(f"ไม่พบข้อมูลผังบัญชีในไฟล์ Json {json_file_path}")
            # แทนที่จะเลิกทำงาน ให้พยายามเดาบริษัทจากไฟล์/ข้อความต่อไป
            json_data = {}
        else:
            # พิมพ์ตัวอย่างข้อมูลจาก JSON เพื่อ debug
            try:
                sample_items = list(json_data.items())[:3]
                print("📘 ตัวอย่างข้อมูลจาก JSON (3 รายการแรก):")
                for key, data in sample_items:
                    print(f" - {data.get('company_name', key)} | customer_id={data.get('customer_id', '')} | account_code={data.get('account_code', '')}")
            except Exception:
                pass
        print("ข้อมูลจากการอ่านไฟล์ Json")
        for company_key, data in json_data.items():
            company_name = data.get("company_name", "ไม่พบชื่อที่ระบบริษัท")
            customer_id = data.get("customer_id", "ไม่พบข้อมูลโค้ดลูกค้า")
            account_code = data.get("account_code", "ไม่พบข้อมูลโค้ดบัญชีตัวแรก")
            account_code2 = data.get("account_code2", "ไม่พบข้อมูลโค้ดบัญชีตัวสอง")
            
        text_file_path = json_file_path.replace('.json', '.txt')
        txt_data = self.read_txt_file(text_file_path)
        txt_content = txt_data if txt_data else "ไม่มีข้อมูล TXT"
        if txt_data:
            # แสดงบรรทัดแรกๆ เพื่อ debug
            try:
                lines_preview = "\n".join(txt_data.splitlines()[:5])
                print("📝 ตัวอย่างข้อมูลจาก TXT (5 บรรทัดแรก):\n" + lines_preview)
            except Exception:
                pass
        
        detected_company_name = None
        customer_id = ""
        account_code = ""
        keyword_results = {
            "เลขที่เอกสาร": "",
            "วันที่เอกสาร": "",
            "ยอดก่อนภาษีมูลค่าเพิ่ม": "",
            "ยอดก่อนภาษีมูลค่าเพิ่ม (NoneVat)": "",
            "ยอดภาษีมูลค่าเพิ่ม": "",
            "ยอดหลังบวกภาษีมูลค่าเพิ่ม": ""
        }
        file_has_data = False
        
        # 1) ลองจับคู่จาก JSON (ถ้ามี)
        if json_data:
            for line in lines: 
                clean_line = re.sub(r'\s+', '', line).lower()
                
                for company, data in json_data.items():
                    json_company_name = data.get("company_name", "ไม่พบชื่อที่ระบบริษัท")
                    clean_json_company = re.sub(r'\s+', '', json_company_name).lower()
                    if clean_json_company in clean_line:
                        detected_company_name = json_company_name  # ใช้ชื่อบริษัทจาก JSON แทน
                        customer_id = data.get("customer_id", "ไม่พบข้อมูลโค้ดลูกค้า").strip()
                        account_code = data.get("account_code", "ไม่พบข้อมูลโค้ดบัญชีตัวแรก").strip()
                        print(f"พบข้อมูลบริษัท: {detected_company_name}")
                        print(f"Customer ID: {customer_id}")
                        print(f"Account Code: {account_code}")
                        break
                if detected_company_name:
                    break

        # 2) ถ้าไม่พบจาก JSON ให้เดาจากรูปแบบไฟล์/ข้อความ
        if not detected_company_name:
            detected_company_name = self._detect_company_by_patterns(lines, pdf_file)
            if detected_company_name:
                print(f"🔎 เดาชื่อบริษัทจากรูปแบบไฟล์: {detected_company_name}")
            else:
                print(f"ไม่พบข้อมูลบริษัทในไฟล์ {pdf_file}")
                return None
            
        for i, line in enumerate(lines):
            # ใช้การเช็คแบบ flexible สำหรับชื่อบริษัท
            if "Shopee" in detected_company_name:
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
                    print("✅ พบ TRSPEFHM00-00000-25")
                    next_line = lines[i + 1].strip()        
                    print(f"next_line: {next_line}")               
                    match = re.search(r'\d{4}-\d{6,7}', next_line)
                    if match:
                        additional_info = match.group(0)
                        combined_info = f"TRSPEFHM00-00000-25{additional_info}"
                        keyword_results["เลขที่เอกสาร"] = combined_info
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    else:
                        print("❌ ไม่พบ pattern \\d{4}-\\d{6,7} ใน next_line")
                elif 'TRSPESPF00-00000-25' in line and i + 1 < len(lines): 
                    print("✅ พบ TRSPESPF00-00000-25")
                    next_line = lines[i + 1].strip()        
                    print(f"next_line: {next_line}")               
                    match = re.search(r'\d{4}-\d{6,7}', next_line)
                    if match:
                        additional_info = match.group(0)
                        combined_info = f"TRSPESPF00-00000-25{additional_info}"
                        keyword_results["เลขที่เอกสาร"] = combined_info
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    else:
                        print("❌ ไม่พบ pattern \\d{4}-\\d{6,7} ใน next_line")
                elif 'TRSPEMKP00-00000-26' in line and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    match = re.search(r'\d{4}-\d{7}', next_line)
                    if match:
                        additional_info = match.group(0)
                        combined_info = f"TRSPEMKP00-00000-26{additional_info}"
                        keyword_results["เลขที่เอกสาร"] = combined_info
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")

                elif 'TRSPECPS00-00000-26' in line and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    match = re.search(r'\d{4}-\d{7}',next_line)
                    if match:
                        additional_info = match.group(0)
                        combined_info = f"TRSPECPS00-00000-26{additional_info}"
                        keyword_results["เลขที่เอกสาร"] = combined_info
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                elif 'TRSPEFHM00-00000-26' in line and i + 1 < len(lines): 
                    print("✅ พบ TRSPEFHM00-00000-26")
                    next_line = lines[i + 1].strip()        
                    print(f"next_line: {next_line}")               
                    match = re.search(r'\d{4}-\d{6,7}', next_line)
                    if match:
                        additional_info = match.group(0)
                        combined_info = f"TRSPEFHM00-00000-26{additional_info}"
                        keyword_results["เลขที่เอกสาร"] = combined_info
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    else:
                        print("❌ ไม่พบ pattern \\d{4}-\\d{6,7} ใน next_line")
                elif 'TRSPESPF00-00000-26' in line and i + 1 < len(lines): 
                    print("✅ พบ TRSPESPF00-00000-26")
                    next_line = lines[i + 1].strip()        
                    print(f"next_line: {next_line}")               
                    match = re.search(r'\d{4}-\d{6,7}', next_line)
                    if match:
                        additional_info = match.group(0)
                        combined_info = f"TRSPESPF00-00000-26{additional_info}"
                        keyword_results["เลขที่เอกสาร"] = combined_info
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                    else:
                        print("❌ ไม่พบ pattern \\d{4}-\\d{6,7} ใน next_line")

                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
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
                            combined_info = f"RCSPXSPB00-00000-25{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                            pass
                    elif 'RCSPXSPW00-00000-25' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"RCSPXSPB00-00000-25{additional_info}"
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
                    elif 'NRSPXSPB00-00000-25' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"NRSPXSPB00-00000-25{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร :{keyword_results['เลขที่เอกสาร']}")
                            pass
                    elif 'RCSPXSPW00-00000-2' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"RCSPXSPW00-00000-2{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร :{keyword_results['เลขที่เอกสาร']}")
                            pass
                    elif 'RCSPXSPB00-00000-26' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"RCSPXSPB00-00000-26{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                            pass
                    elif 'RCSPXSPR00-00000-26' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"RCSPXSPB00-00000-26{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                            pass
                    elif 'RCSPXSPW00-00000-26' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"RCSPXSPB00-00000-26{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                            pass
                    elif 'RCSPXSPB00-00000-26' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"RCSPXSPB00-00000-26{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                            pass
                    elif 'RCSPXSPR00-00000-26' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"RCSPXSPB00-00000-26{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                            pass
                    elif 'NRSPXSPW00-00000-26' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"NRSPXSPW00-00000-26{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร :{keyword_results['เลขที่เอกสาร']}")
                            pass
                    elif 'NRSPXSPB00-00000-26' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"NRSPXSPB00-00000-26{additional_info}"
                            keyword_results["เลขที่เอกสาร"] = combined_info
                            print(f"เลขที่เอกสาร :{keyword_results['เลขที่เอกสาร']}")
                            pass
                    elif 'RCSPXSPW00-00000-26' in line and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        match = re.search(r'\d{4}-\d{7}', next_line)
                        if match:
                            additional_info = match.group(0)
                            combined_info = f"RCSPXSPW00-00000-26{additional_info}"
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
            
            elif detected_company_name == "K-BIZ Contact":
                    if 'Document number' in line and i + 1 < len(lines):
                        # Extract document number and date from the same line
                        # Format: "011025E00016908 01/10/2025หน้าที่ (PAGE/OF) 1/1"
                        next_line = lines[i + 1].strip()
                        # Extract document number - look for pattern like 011025E00016908
                        doc_match = re.search(r'\d+E\d+', next_line)
                        if doc_match:
                            keyword_results["เลขที่เอกสาร"] = doc_match.group()
                        else:
                            # Fallback to original logic
                            parts = next_line.split()
                            keyword_results["เลขที่เอกสาร"] = parts[0] if len(parts) > 0 else next_line
                        print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
                        # Extract date - look for pattern like 01/10/2025 and remove "หน้าที่"
                        date_match = re.search(r'\d{2}/\d{2}/\d{4}', next_line)
                        if date_match:
                            keyword_results["วันที่เอกสาร"] = date_match.group()
                            print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                    # Keep Issued Date as fallback if Document number parsing didn't work
                    if 'Issued Date' in line and "วันที่เอกสาร" not in keyword_results and i + 1 < len(lines):
                        keyword_results["วันที่เอกสาร"] = lines[i + 1].strip().split()[0]
                        print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                    if 'บัตรเครดิต/เดบิต' in line:
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            # parts[2] = FEE/COMMISION AMOUNT (51.79) = total_ex_vat
                            # parts[3] = VAT (3.63) = vat_value
                            keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = parts[2]
                            print(f"ยอดก่อนภาษี : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
                            keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = parts[3]
                            print(f"ยอดภาษี : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
                            try:
                                fee = float(parts[2].replace(',', ''))
                                vat = float(parts[3].replace(',', ''))
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
                # ===== 1) เลขที่เอกสาร + วันที่เอกสาร จากบรรทัด ETIV =====
                if 'ETIV' in line:
                    # ดึงเลขที่เอกสารจากบรรทัด ETIV
                    keyword_results["เลขที่เอกสาร"] = line.strip().split()[-1]
                    print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")

                    # เลื่อนไป 3 บรรทัดหลังจาก ETIV เพื่ออ่านวันที่เอกสาร
                    date_index = i + 3
                    if date_index < len(lines):
                        date_line = lines[date_index]
                        date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', date_line)
                        if date_match:
                            day, month, year = date_match.groups()
                            keyword_results["วันที่เอกสาร"] = f"{day}/{month}/{year}"
                            print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
                        else:
                            print(f"[DEBUG] ไม่พบรูปแบบวันที่ในบรรทัด: {date_line!r}")
                    else:
                        print("[DEBUG] ไม่มีบรรทัด i+3 สำหรับอ่านวันที่")

                # ===== 2) ยอดก่อนภาษี / ภาษี / ยอดรวมภาษี จาก RECEIPT/TAX INVOICE =====
                if 'RECEIPT/TAX INVOICE' in line:
                    base_index = i  # index ของบรรทัดที่เจอคำว่า RECEIPT/TAX INVOICE

                    def get_amount_at_offset(offset: int):
                        idx = base_index + offset
                        if idx < len(lines):
                            target_line = lines[idx]
                            m = re.search(r'(\d+\.\d{2})', target_line)
                            if m:
                                return m.group(1), target_line
                            else:
                                print(f"[DEBUG] ไม่เจอจำนวนเงินในบรรทัด offset {offset}: {target_line!r}")
                        else:
                            print(f"[DEBUG] index {idx} เกินจำนวนบรรทัด (len={len(lines)})")
                        return None, None

                    # ตามเงื่อนไขที่คุณกำหนด:
                    # +3 = total_in_vat
                    # +4 = vat_value
                    # +5 = total_ex_vat
                    total_in_vat, line_total = get_amount_at_offset(2)
                    vat_value, line_vat = get_amount_at_offset(3)
                    total_ex_vat, line_ex = get_amount_at_offset(4)

                    if total_in_vat:
                        keyword_results["ยอดหลังบวกภาษีมูลค่าเพิ่ม"] = total_in_vat
                        print(f"ยอดหลังรวมภาษี (i+4) : {total_in_vat}  จากบรรทัด: {line_total!r}")

                    if vat_value:
                        keyword_results["ยอดภาษีมูลค่าเพิ่ม"] = vat_value
                        print(f"ยอดภาษี (i+3)       : {vat_value} จากบรรทัด: {line_vat!r}")

                    if total_ex_vat:
                        keyword_results["ยอดก่อนภาษีมูลค่าเพิ่ม"] = total_ex_vat
                        print(f"ยอดก่อนภาษี (i+2)   : {total_ex_vat} จากบรรทัด: {line_ex!r}")

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
                    
        if file_has_data:
            print(f"\n✅ ดึงข้อมูลสำเร็จจากไฟล์: {pdf_file}")
            print(f"Customer_id : {customer_id}")
            print(f"Account_code : {account_code}")
            print(f"Account_code2 : ")  # ตั้งค่าว่างไว้ก่อน
            print(f"เลขที่เอกสาร : {keyword_results['เลขที่เอกสาร']}")
            print(f"วันที่เอกสาร : {keyword_results['วันที่เอกสาร']}")
            print(f"ยอดก่อนภาษีมูลค่าเพิ่ม : {keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม']}")
            print(f"ยอดก่อนภาษีมูลค่าเพิ่ม (NoneVat) : {keyword_results.get('ยอดก่อนภาษีมูลค่าเพิ่ม (NoneVat)', keyword_results['ยอดก่อนภาษีมูลค่าเพิ่ม'])}")
            print(f"ยอดภาษีมูลค่าเพิ่ม : {keyword_results['ยอดภาษีมูลค่าเพิ่ม']}")
            print(f"ยอดหลังบวกภาษีมูลค่าเพิ่ม : {keyword_results['ยอดหลังบวกภาษีมูลค่าเพิ่ม']}")
            
            # ไม่ต้องเปิดเว็บไซต์ที่นี่ จะเปิดหลังจากอ่านไฟล์ทั้งหมดเสร็จแล้ว
            print(f"📋 ข้อมูลถูกอ่านเรียบร้อยแล้ว รอการเปิดเว็บไซต์หลังจากอ่านไฟล์ทั้งหมดเสร็จ...")
            
            return {
                "filename": pdf_file,
                "company_name": detected_company_name,
                "customer_code": customer_id,  # ✅ ส่ง Customer ID จาก JSON
                "account_code": account_code,  # ✅ ส่ง Account Code จาก JSON
                "account_code2": "",  # จาก JSON
                "txt_data": txt_content,
                "document_number": keyword_results.get('เลขที่เอกสาร', ''),  # ✅ ส่งเลขที่เอกสารจาก PDF
                "document_date": keyword_results.get('วันที่เอกสาร', ''),    # ✅ ส่งวันที่เอกสารจาก PDF
                "total_ex_vat": keyword_results.get('ยอดก่อนภาษีมูลค่าเพิ่ม', ''),  # ✅ ส่งยอดก่อนภาษีจาก PDF
                "total_ex_vat_none": keyword_results.get('ยอดก่อนภาษีมูลค่าเพิ่ม (NoneVat)', ''),  # ✅ ส่งยอดก่อนภาษี (NoneVat) จาก PDF
                "vat_value": keyword_results.get('ยอดภาษีมูลค่าเพิ่ม', ''),  # ✅ ส่งยอดภาษีจาก PDF
                "total_in_vat": keyword_results.get('ยอดหลังบวกภาษีมูลค่าเพิ่ม', ''),  # ✅ ส่งยอดหลังบวกภาษีจาก PDF
                "file_path": pdf_file
            }
        print(f"ไม่พบข้อมูลที่ต้องการในไฟล์ {pdf_file}")
        return None