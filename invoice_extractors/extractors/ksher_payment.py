"""
Ksher Payment Co., Ltd. Invoice Extractor
==========================================
Extractor สำหรับดึงข้อมูลจาก Ksher Payment Co., Ltd.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class KsherPaymentExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก Ksher Payment Co., Ltd."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "Ksher Payment Co., Ltd.",
        "Ksher Payment",
        "Ksher"
    ]
    
    # Tax ID
    TAX_ID = "0125565028247"
    
    def __init__(self):
        """Initialize Ksher Payment Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Ksher Payment Co., Ltd. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "Ksher Payment Co., Ltd."
        2. Tax ID "0125565028247"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Ksher Payment Co., Ltd. (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0125565028247"
        has_tax_id = self.TAX_ID in text
        
        # เงื่อนไข 3: ต้องมีเอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        has_document_type = (
            "ใบเสร็จรับเงิน" in text or 
            "ใบกำกับภาษี" in text or 
            "RECEIPT" in text.upper() or 
            "TAX INVOICE" in text.upper()
        )
        
        # ต้องมีทั้ง 3 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id and has_document_type
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "Ksher Payment Co., Ltd."
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: Tax ID: 0125565028247 หรือ เลขประจำตัวผู้เสียภาษี / Tax ID : 0125565028247
        patterns = [
            r'เลขประจำตัวผู้เสียภาษี\s*/?\s*Tax\s+ID\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี / Tax ID : 0125565028247
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0125565028247
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID: 0125565028247
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี: 0125565028247
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id = match.group(1).strip()
                if tax_id == self.TAX_ID:
                    logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษี: {tax_id}")
                    return tax_id
        
        # Fallback: ถ้าไม่พบข้อมูล ให้ใช้ค่า default
        logger.info(f"⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา"""
        # ไม่มีสาขา (ว่าง)
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """
        ดึงวันที่และแปลงเป็น dd/mm/yyyy
        
        รองรับรูปแบบต่างๆ:
        - วันที่/Date. 27/11/2025
        - วันที่/Date 27/11/2025
        - วันที่: 27/11/2025
        - Date: 27/11/2025
        - Date. 27/11/2025
        """
        # Pattern ที่ครอบคลุมมากขึ้น
        patterns = [
            # รูปแบบ: วันที่/Date. 27/11/2025 (มีจุดหลัง Date)
            r'วันที่\s*/?\s*Date\s*[.:]\s*(\d{1,2})/(\d{1,2})/(\d{4})',
            # รูปแบบ: วันที่/Date 27/11/2025 (ไม่มีจุด)
            r'วันที่\s*/?\s*Date\s+(\d{1,2})/(\d{1,2})/(\d{4})',
            # รูปแบบ: วันที่: 27/11/2025 หรือ วันที่. 27/11/2025
            r'วันที่\s*[:.]\s*(\d{1,2})/(\d{1,2})/(\d{4})',
            # รูปแบบ: Date: 27/11/2025 หรือ Date. 27/11/2025
            r'Date\s*[:.]\s*(\d{1,2})/(\d{1,2})/(\d{4})',
            # รูปแบบ: Date 27/11/2025 (ไม่มีเครื่องหมาย)
            r'Date\s+(\d{1,2})/(\d{1,2})/(\d{4})',
            # รูปแบบ: เลขที่/No. ... วันที่/Date 27/11/2025 (อาจมีข้อความก่อนหน้า)
            r'วันที่\s*/?\s*Date\s*[.:]?\s*(\d{1,2})/(\d{1,2})/(\d{4})',
            # รูปแบบทั่วไป: ตัวเลข/ตัวเลข/ตัวเลข 4 หลัก (fallback)
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
        ]
        
        # ลองหาแบบละเอียดก่อน (pattern ที่เฉพาะเจาะจง)
        for i, pattern in enumerate(patterns[:-1]):  # ไม่ใช้ pattern สุดท้าย (fallback) ในรอบแรก
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    day = match.group(1).zfill(2)
                    month = match.group(2).zfill(2)
                    year = match.group(3)
                    
                    # ตรวจสอบความถูกต้องของวันที่
                    day_int = int(day)
                    month_int = int(month)
                    year_int = int(year)
                    
                    # ตรวจสอบว่าเป็นวันที่ที่สมเหตุสมผล
                    if 1 <= day_int <= 31 and 1 <= month_int <= 12 and 2000 <= year_int <= 2100:
                        date_str = f"{day}/{month}/{year}"
                        logger.info(f"✅ พบวันที่: {date_str} (pattern {i+1})")
                        return date_str
                except (ValueError, IndexError) as e:
                    logger.debug(f"⚠️ Error parsing date with pattern {i+1}: {e}")
                    continue
        
        # ถ้ายังไม่พบ ลองหาแบบ fallback (pattern สุดท้าย)
        # แต่ต้องตรวจสอบว่าอยู่ใกล้กับคำว่า "วันที่" หรือ "Date"
        fallback_pattern = patterns[-1]
        matches = list(re.finditer(fallback_pattern, text))
        
        for match in matches:
            try:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                
                # ตรวจสอบความถูกต้องของวันที่
                day_int = int(day)
                month_int = int(month)
                year_int = int(year)
                
                if 1 <= day_int <= 31 and 1 <= month_int <= 12 and 2000 <= year_int <= 2100:
                    # ตรวจสอบว่าอยู่ใกล้กับคำว่า "วันที่" หรือ "Date" (ภายใน 50 ตัวอักษร)
                    start_pos = match.start()
                    context_start = max(0, start_pos - 50)
                    context_end = min(len(text), start_pos + 50)
                    context = text[context_start:context_end]
                    
                    # ถ้ามีคำว่า "วันที่" หรือ "Date" ในบริบท ให้ใช้ค่านี้
                    if 'วันที่' in context or 'Date' in context or 'DATE' in context:
                        date_str = f"{day}/{month}/{year}"
                        logger.info(f"✅ พบวันที่ (fallback): {date_str}")
                        return date_str
            except (ValueError, IndexError):
                continue
        
        logger.warning("⚠️ ไม่พบวันที่ในเอกสาร")
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: เลขที่/No. TP-13-202511-00455
        patterns = [
            r'เลขที่\s*/?\s*No[.:]?\s*([A-Z0-9\-]+)',  # เลขที่/No. TP-13-202511-00455
            r'No[.:]?\s*([A-Z0-9\-]+)',  # No. TP-13-202511-00455
            r'(TP-\d+-\d+-\d+)',  # TP-13-202511-00455
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_no = match.group(1).strip()
                if doc_no and len(doc_no) > 5:
                    logger.info(f"✅ พบเลขที่เอกสาร: {doc_no}")
                    return doc_no
        
        return None
    
    def parse_html_table(self, text: str) -> Dict[str, str]:
        """
        Parse HTML table structure และอ่านข้อมูลทีละบรรทัด
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            Dictionary ที่มีข้อมูลที่ parse ได้
        """
        result = {}
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Pattern 1: Pipe-separated values (เช่น: ค่าธรรมเนียม Commission |  | 8.13 |)
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                # ข้าม header row
                if any(keyword in line.upper() for keyword in ['DESCRIPTION', 'MERCHANT', 'TRANS', 'AMOUNT', 'TRUE MONEY', 'ยอดขาย']):
                    continue
                
                # หา "ค่าธรรมเนียม Commission" หรือ "Commission"
                if 'ค่าธรรมเนียม' in line or 'Commission' in line:
                    # หาตัวเลขในบรรทัดนี้ (ยอดค่าธรรมเนียม) - มักจะอยู่ในคอลัมน์ที่ 3 (index 2)
                    # เช่น: ค่าธรรมเนียม Commission |  | 8.13 |
                    for i, part in enumerate(parts):
                        part_clean = part.replace(',', '').strip()
                        # ตรวจสอบว่าเป็นตัวเลข
                        if re.match(r'^\d+\.?\d*$', part_clean):
                            result['commission'] = part_clean
                            logger.info(f"📋 [Parse HTML Table] พบ Commission: {part_clean} (คอลัมน์ {i+1})")
                            break
                
                # หา "ภาษีมูลค่าเพิ่ม Vat" หรือ "Vat"
                if 'ภาษีมูลค่าเพิ่ม' in line or ('Vat' in line and 'ภาษี' in line) or ('VAT' in line and 'ภาษี' in line):
                    # หาตัวเลขในบรรทัดนี้ (ยอดภาษี) - มักจะอยู่ในคอลัมน์สุดท้าย
                    # เช่น: ภาษีมูลค่าเพิ่ม Vat |  |  | 0.57
                    for i, part in enumerate(parts):
                        part_clean = part.replace(',', '').strip()
                        # ตรวจสอบว่าเป็นตัวเลข
                        if re.match(r'^\d+\.?\d*$', part_clean):
                            result['vat'] = part_clean
                            logger.info(f"📋 [Parse HTML Table] พบ VAT: {part_clean} (คอลัมน์ {i+1})")
                            break
            
            # Pattern 2: Key: Value หรือ Key Value
            colon_match = re.search(r'^(.+?)\s*[:.]?\s*(.+)$', line)
            if colon_match:
                key = colon_match.group(1).strip()
                value = colon_match.group(2).strip()
                if value and not any(keyword in line.upper() for keyword in ['DESCRIPTION', 'MERCHANT', 'TRANS', 'AMOUNT']):
                    result[key] = value
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลยอดเงิน
        
        รองรับหลายรูปแบบ:
        1. จากบรรทัด "จำนวนเงินรวมทั้งสิ้น / GrandTotal": 290.00 8.13 0.57 281.30
        2. จากตาราง HTML ที่มี pipe separator
        3. จากตารางที่มี header ภาษาไทย: "ยอดก่อนภาษีมูลค่าเพิ่ม", "ยอดภาษีมูลค่าเพิ่ม", "ยอดหลังบวกภาษีมูลค่าเพิ่ม"
        4. จากบรรทัดที่มีคำว่า "ค่าธรรมเนียม Commission" หรือ "ภาษีมูลค่าเพิ่ม Vat"
        """
        amounts = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        lines = text.split('\n')
        
        # Helper function: แปลง string เป็น float และตรวจสอบความถูกต้อง
        def safe_float(value_str: str, min_val: float = 0, max_val: float = 999999999) -> Optional[float]:
            """แปลง string เป็น float และตรวจสอบความถูกต้อง"""
            try:
                value_str_clean = value_str.replace(',', '').strip()
                if not re.match(r'^\d+\.?\d*$', value_str_clean):
                    return None
                value = float(value_str_clean)
                if min_val <= value <= max_val:
                    return value
            except (ValueError, AttributeError):
                pass
            return None
        
        # ===== วิธีที่ 1: อ่านจากบรรทัด "จำนวนเงินรวมทั้งสิ้น / GrandTotal" =====
        grand_total_line = None
        for line in lines:
            line = line.strip()
            if 'จำนวนเงินรวมทั้งสิ้น' in line and 'GrandTotal' in line:
                grand_total_line = line
                logger.info(f"📋 [Extract Amounts] พบ GrandTotal line: {grand_total_line}")
                break
        
        if grand_total_line:
            # Pattern: จำนวนเงินรวมทั้งสิ้น / GrandTotal 7,940.00 111.32 7.79 7,820.89
            # หาตัวเลขทั้งหมดในบรรทัด (รองรับ comma ในตัวเลข)
            # Pattern: รองรับทั้ง 7,940.00 และ 111.32
            # รูปแบบ: \d{1,3}(?:,\d{3})*(?:\.\d{2})? หรือ \d+\.?\d*
            numbers_raw = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+\.?\d*', grand_total_line)
            logger.info(f"📋 [Extract Amounts] พบตัวเลขจาก GrandTotal (raw): {numbers_raw}")
            
            # ทำความสะอาดตัวเลข (ลบ comma ออก)
            numbers = []
            for num_str in numbers_raw:
                # ลบ comma ออก
                num_clean = num_str.replace(',', '').strip()
                if num_clean:
                    numbers.append(num_clean)
            
            logger.info(f"📋 [Extract Amounts] พบตัวเลขจาก GrandTotal (cleaned): {numbers}")
            
            # จากโครงสร้าง: 7,940.00 111.32 7.79 7,820.89
            # numbers[0] = 7940.00 (Trans. Amount)
            # numbers[1] = 111.32 (Commission - ยอดก่อนภาษี)
            # numbers[2] = 7.79 (Vat - ยอดภาษี)
            # numbers[3] = 7820.89 (Credit Amount)
            
            if len(numbers) >= 3:
                # ยอดก่อนภาษี: 111.32 (ค่าที่ 2, index 1)
                if amounts['amount_before_vat'] is None:
                    val = safe_float(numbers[1])
                    if val is not None:
                        amounts['amount_before_vat'] = val
                        logger.info(f"✅ พบยอดก่อนภาษี (Commission): {amounts['amount_before_vat']} จาก GrandTotal")
                
                # ยอดภาษี: 7.79 (ค่าที่ 3, index 2)
                if amounts['vat_amount'] is None:
                    val = safe_float(numbers[2])
                    if val is not None:
                        amounts['vat_amount'] = val
                        logger.info(f"✅ พบยอดภาษี (VAT): {amounts['vat_amount']} จาก GrandTotal")
        
        # ===== วิธีที่ 2: อ่านจากตารางที่มี header ภาษาไทย =====
        # หาตารางที่มี header: "ยอดก่อนภาษีมูลค่าเพิ่ม", "ยอดภาษีมูลค่าเพิ่ม", "ยอดหลังบวกภาษีมูลค่าเพิ่ม"
        if amounts['amount_before_vat'] is None or amounts['vat_amount'] is None or amounts['total_amount'] is None:
            header_found = False
            header_line_idx = -1
            
            # หา header line ที่มีคำว่า "ยอดก่อน" หรือ "ยอดภาษี" หรือ "ยอดหลัง"
            for i, line in enumerate(lines):
                line = line.strip()
                if ('ยอดก่อน' in line and 'ภาษี' in line) or ('ยอดภาษี' in line) or ('ยอดหลัง' in line and 'ภาษี' in line):
                    header_found = True
                    header_line_idx = i
                    logger.info(f"📋 [Extract Amounts] พบ header ภาษาไทยที่บรรทัด {i+1}: {line}")
                    break
            
            # ถ้าพบ header ให้อ่านข้อมูลจากบรรทัดถัดไป
            if header_found and header_line_idx >= 0:
                # ลองหาข้อมูลจากบรรทัดถัดไป (อาจเป็น data row)
                for offset in [1, 2, 3]:  # ตรวจสอบ 3 บรรทัดถัดไป
                    if header_line_idx + offset < len(lines):
                        data_line = lines[header_line_idx + offset].strip()
                        if not data_line or len(data_line) < 5:
                            continue
                        
                        # หาตัวเลขในบรรทัดนี้ (รองรับ comma ในตัวเลข)
                        numbers_raw = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+\.?\d*', data_line)
                        logger.info(f"📋 [Extract Amounts] พบตัวเลขจาก data line (offset {offset}, raw): {numbers_raw}")
                        
                        # ทำความสะอาดตัวเลข (ลบ comma ออก)
                        numbers = []
                        for num_str in numbers_raw:
                            num_clean = num_str.replace(',', '').strip()
                            if num_clean:
                                numbers.append(num_clean)
                        
                        logger.info(f"📋 [Extract Amounts] พบตัวเลขจาก data line (offset {offset}, cleaned): {numbers}")
                        
                        # ถ้ามีตัวเลขอย่างน้อย 2 ตัว ให้ลองใช้
                        if len(numbers) >= 2:
                            # ถ้ายังไม่เจอยอดก่อนภาษี
                            if amounts['amount_before_vat'] is None:
                                val = safe_float(numbers[0])
                                if val is not None and val > 0:
                                    amounts['amount_before_vat'] = val
                                    logger.info(f"✅ พบยอดก่อนภาษี: {amounts['amount_before_vat']} จากตารางภาษาไทย (คอลัมน์ 1)")
                            
                            # ถ้ายังไม่เจอยอดภาษี
                            if amounts['vat_amount'] is None and len(numbers) >= 2:
                                val = safe_float(numbers[1])
                                if val is not None and val > 0:
                                    amounts['vat_amount'] = val
                                    logger.info(f"✅ พบยอดภาษี: {amounts['vat_amount']} จากตารางภาษาไทย (คอลัมน์ 2)")
                            
                            # ถ้ายังไม่เจอยอดรวม
                            if amounts['total_amount'] is None and len(numbers) >= 3:
                                val = safe_float(numbers[2])
                                if val is not None and val > 0:
                                    amounts['total_amount'] = val
                                    logger.info(f"✅ พบยอดรวม: {amounts['total_amount']} จากตารางภาษาไทย (คอลัมน์ 3)")
                            
                            # ถ้าเจอข้อมูลครบแล้ว ให้หยุด
                            if amounts['amount_before_vat'] and amounts['vat_amount']:
                                break
        
        # ===== วิธีที่ 3: อ่านจากตาราง HTML ที่มี pipe separator =====
        if amounts['amount_before_vat'] is None or amounts['vat_amount'] is None:
            # หาบรรทัด header เพื่อดูโครงสร้างตาราง
            header_line = None
            data_line = None
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or '|' not in line:
                    continue
                
                # หา header line ที่มี "รายการสินค้า" หรือ "Description"
                if ('รายการสินค้า' in line or 'Description' in line) and '|' in line:
                    header_line = line
                    # หา data line ถัดไป (ข้าม header)
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if '|' in next_line and ('รายการ' in next_line or 'Transaction' in next_line):
                            data_line = next_line
                            break
            
            # ถ้าไม่พบ header/data line แบบข้างต้น ลองหาจาก pattern อื่น
            if not data_line:
                for line in lines:
                    line = line.strip()
                    if '|' in line and ('รายการรับชำระเงิน' in line or 'Transaction for' in line):
                        data_line = line
                        break
            
            # Parse data line
            if data_line and '|' in data_line:
                parts = [p.strip() for p in data_line.split('|')]
                logger.info(f"📋 [Extract Amounts] พบ data line: {len(parts)} คอลัมน์")
                logger.info(f"📋 [Extract Amounts] Parts: {parts}")
                
                # จากโครงสร้างตาราง:
                # คอลัมน์ 0: Description (รายการสินค้า)
                # คอลัมน์ 1: Merchant no. (44110)
                # คอลัมน์ 2: Trans. Amount (290.00)
                # คอลัมน์ 3: Commission (8.13) <- ยอดก่อนภาษี
                # คอลัมน์ 4: Vat (0.57) <- ยอดภาษี
                # คอลัมน์ 5: Credit Amount (281.30)
                
                # อ่าน Commission (ยอดก่อนภาษี) จากคอลัมน์ที่ 3 (index 3)
                if len(parts) > 3 and amounts['amount_before_vat'] is None:
                    val = safe_float(parts[3])
                    if val is not None:
                        amounts['amount_before_vat'] = val
                        logger.info(f"✅ พบยอดก่อนภาษี (Commission): {amounts['amount_before_vat']} (คอลัมน์ 3)")
                
                # อ่าน Vat (ยอดภาษี) จากคอลัมน์ที่ 4 (index 4)
                if len(parts) > 4 and amounts['vat_amount'] is None:
                    val = safe_float(parts[4])
                    if val is not None:
                        amounts['vat_amount'] = val
                        logger.info(f"✅ พบยอดภาษี (VAT): {amounts['vat_amount']} (คอลัมน์ 4)")
        
        # ===== วิธีที่ 4: อ่านจากบรรทัดที่มีคำว่า "ค่าธรรมเนียม" หรือ "Commission" =====
        if amounts['amount_before_vat'] is None:
            # Pattern: ค่าธรรมเนียม Commission 8.13 หรือ ค่าธรรมเนียม 8.13
            commission_patterns = [
                r'ค่าธรรมเนียม\s+Commission[^0-9]*(\d+\.?\d*)',
                r'Commission[^0-9]*(\d+\.?\d*)',
                r'ค่าธรรมเนียม[^0-9]*(\d+\.?\d*)',
            ]
            
            for pattern in commission_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    val = safe_float(match.group(1))
                    if val is not None:
                        amounts['amount_before_vat'] = val
                        logger.info(f"✅ พบยอดก่อนภาษี (Commission - pattern): {amounts['amount_before_vat']}")
                        break
        
        # ===== วิธีที่ 5: อ่านจากบรรทัดที่มีคำว่า "ภาษีมูลค่าเพิ่ม" หรือ "Vat" =====
        if amounts['vat_amount'] is None:
            # Pattern: ภาษีมูลค่าเพิ่ม Vat 0.57 หรือ ภาษีมูลค่าเพิ่ม 0.57
            vat_patterns = [
                r'ภาษีมูลค่าเพิ่ม\s+Vat[^0-9]*(\d+\.?\d*)',
                r'ภาษีมูลค่าเพิ่ม\s+VAT[^0-9]*(\d+\.?\d*)',
                r'Vat[^0-9]*(\d+\.?\d*)',
                r'ภาษีมูลค่าเพิ่ม[^0-9]*(\d+\.?\d*)',
            ]
            
            for pattern in vat_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    val = safe_float(match.group(1))
                    if val is not None:
                        amounts['vat_amount'] = val
                        logger.info(f"✅ พบยอดภาษี (VAT - pattern): {amounts['vat_amount']}")
                        break
        
        # ===== วิธีที่ 6: Fallback - อ่านจากตาราง HTML (pattern matching จาก header) =====
        if amounts['amount_before_vat'] is None or amounts['vat_amount'] is None:
            # หาบรรทัดที่มี "ค่าธรรมเนียม" หรือ "Commission" ใน header
            for line in lines:
                line = line.strip()
                if '|' not in line:
                    continue
                
                # หา header ที่มี "ค่าธรรมเนียม" และ "Commission"
                if 'ค่าธรรมเนียม' in line and 'Commission' in line:
                    # หา data line ถัดไป
                    line_idx = lines.index(line) if line in lines else -1
                    if line_idx >= 0 and line_idx + 1 < len(lines):
                        data_line = lines[line_idx + 1].strip()
                        if '|' in data_line:
                            parts = [p.strip() for p in data_line.split('|')]
                            # หา Commission จากคอลัมน์ที่ 3 (index 3)
                            if len(parts) > 3:
                                val = safe_float(parts[3])
                                if val is not None:
                                    amounts['amount_before_vat'] = val
                                    logger.info(f"✅ พบยอดก่อนภาษี (Commission): {amounts['amount_before_vat']}")
                            break
                
                # หา header ที่มี "ภาษีมูลค่าเพิ่ม" และ "Vat"
                if 'ภาษีมูลค่าเพิ่ม' in line and ('Vat' in line or 'VAT' in line):
                    # หา data line ถัดไป
                    line_idx = lines.index(line) if line in lines else -1
                    if line_idx >= 0 and line_idx + 1 < len(lines):
                        data_line = lines[line_idx + 1].strip()
                        if '|' in data_line:
                            parts = [p.strip() for p in data_line.split('|')]
                            # หา Vat จากคอลัมน์ที่ 4 (index 4)
                            if len(parts) > 4:
                                val = safe_float(parts[4])
                                if val is not None:
                                    amounts['vat_amount'] = val
                                    logger.info(f"✅ พบยอดภาษี (VAT): {amounts['vat_amount']}")
                            break
        
        # ===== วิธีที่ 7: Fallback - อ่านจากบรรทัดที่มี "รายการรับชำระเงิน" =====
        if amounts['amount_before_vat'] is None:
            # Pattern: หา 8.13 จากบรรทัดที่มี "รายการรับชำระเงิน" และมี pipe
            pattern = r'รายการรับชำระเงิน[^|]*\|\s*[^|]*\|\s*[^|]*\|\s*([\d,]+\.?\d*)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = safe_float(match.group(1))
                if val is not None:
                    amounts['amount_before_vat'] = val
                    logger.info(f"✅ พบยอดก่อนภาษี (Commission - fallback): {amounts['amount_before_vat']}")
        
        if amounts['vat_amount'] is None:
            # Pattern: หา 0.57 จากบรรทัดที่มี "รายการรับชำระเงิน" และมี pipe
            pattern = r'รายการรับชำระเงิน[^|]*\|\s*[^|]*\|\s*[^|]*\|\s*[^|]*\|\s*([\d,]+\.?\d*)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = safe_float(match.group(1))
                if val is not None:
                    amounts['vat_amount'] = val
                    logger.info(f"✅ พบยอดภาษี (VAT - fallback): {amounts['vat_amount']}")
        
        # ===== คำนวณยอดหลังบวกภาษีมูลค่าเพิ่ม =====
        # ถ้ามียอดก่อนภาษีและยอดภาษี ให้คำนวณยอดรวม
        if amounts['amount_before_vat'] is not None and amounts['vat_amount'] is not None:
            calculated_total = amounts['amount_before_vat'] + amounts['vat_amount']
            
            # ถ้ายังไม่มียอดรวม หรือยอดรวมที่อ่านมาไม่ตรงกับที่คำนวณ ให้ใช้ค่าที่คำนวณได้
            if amounts['total_amount'] is None:
                amounts['total_amount'] = calculated_total
                logger.info(f"✅ คำนวณยอดหลังบวกภาษีมูลค่าเพิ่ม: {amounts['total_amount']} ({amounts['amount_before_vat']} + {amounts['vat_amount']})")
            else:
                # ถ้ามียอดรวมแล้ว ให้ตรวจสอบว่าตรงกับที่คำนวณหรือไม่
                diff = abs(amounts['total_amount'] - calculated_total)
                if diff > 0.01:  # ถ้าต่างกันมากกว่า 0.01 ให้ใช้ค่าที่คำนวณได้
                    logger.warning(f"⚠️ ยอดรวมที่อ่านมา ({amounts['total_amount']}) ไม่ตรงกับที่คำนวณ ({calculated_total}) - ใช้ค่าที่คำนวณ")
                    amounts['total_amount'] = calculated_total
        
        # สรุปผลการอ่านข้อมูล
        logger.info(f"📊 [Extract Amounts] สรุปผล:")
        logger.info(f"   - ยอดก่อนภาษีมูลค่าเพิ่ม: {amounts['amount_before_vat']}")
        logger.info(f"   - ยอดภาษีมูลค่าเพิ่ม: {amounts['vat_amount']}")
        logger.info(f"   - ยอดหลังบวกภาษีมูลค่าเพิ่ม: {amounts['total_amount']}")
        
        return amounts
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        result = {
            'withholding_tax_percent': None,
            'withholding_tax_amount': None
        }
        
        # ไม่มีข้อมูลหัก ณ ที่จ่าย (ว่าง)
        return result
    
    def extract_address(self, text: str) -> Dict[str, Optional[str]]:
        """
        ดึงข้อมูลที่อยู่
        
        ที่อยู่รวม: หมู่บ้าน บ้านกลางเมืองดิเอร่า ปิ่นเกล้าเจรัญ เลขที่ 197/115 หมู่ที่ 7 ตำบลบางกรวย อำเภอบางกรวย จังหวัดนนทบุรี 11130
        """
        address_data = {
            'address_full': '',
            'building_number': '',
            'other_info': '',
            'soi': '',
            'road': '',
            'subdistrict': '',
            'district': '',
            'province': '',
            'postal_code': ''
        }
        
        # Pattern: ที่อยู่ / Address : หมู่บ้าน บ้านกลางเมืองดิเอร่า ปิ่นเกล้าเจรัญ เลขที่ 197/115 หมู่ที่ 7 ตำบลบางกรวย อำเภอบางกรวย จังหวัดนนทบุรี 11130
        address_patterns = [
            r'ที่อยู่\s*/?\s*Address\s*[:.]?\s*(.+)',
            r'Address\s*[:.]?\s*(.+)',
            r'ที่อยู่\s*[:.]?\s*(.+)',
        ]
        
        address_full = None
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                address_full = match.group(1).strip()
                # ตัดข้อมูลที่อยู่หลังรหัสไปรษณีย์ออก
                address_full = re.sub(r'\s+11130.*$', ' 11130', address_full)
                break
        
        if address_full:
            address_data['address_full'] = address_full
            
            # แยกส่วนต่างๆ ของที่อยู่
            # เลขที่: 197/115
            building_match = re.search(r'เลขที่\s+(\d+/\d+)', address_full)
            if building_match:
                address_data['building_number'] = building_match.group(1)
            
            # อื่นๆ: หมู่บ้าน บ้านกลางเมืองดิเอร่า ปิ่นเกล้าเจรัญ หมู่ที่ 7
            # หาจาก "หมู่บ้าน" ถึง "หมู่ที่ 7"
            other_match = re.search(r'(หมู่บ้าน[^เลข]*?หมู่ที่\s+\d+)', address_full)
            if other_match:
                address_data['other_info'] = other_match.group(1).strip()
            else:
                # ถ้าไม่พบรูปแบบเต็ม ลองหาแค่ "หมู่บ้าน" ถึง "หมู่ที่"
                other_match2 = re.search(r'(หมู่บ้าน[^ตำบล]+?หมู่ที่\s+\d+)', address_full)
                if other_match2:
                    address_data['other_info'] = other_match2.group(1).strip()
            
            # แขวง: บางกรวย (จาก "ตำบลบางกรวย")
            subdistrict_match = re.search(r'ตำบล\s+([^\s]+)', address_full)
            if subdistrict_match:
                address_data['subdistrict'] = subdistrict_match.group(1).strip()
            
            # เขต: บางกรวย (จาก "อำเภอบางกรวย")
            district_match = re.search(r'อำเภอ\s+([^\s]+)', address_full)
            if district_match:
                address_data['district'] = district_match.group(1).strip()
            
            # จังหวัด: นนทบุรี (จาก "จังหวัดนนทบุรี")
            province_match = re.search(r'จังหวัด\s+([^\s]+)', address_full)
            if province_match:
                address_data['province'] = province_match.group(1).strip()
            
            # เลขไปรษณีย์: 11130 (หาจากตัวเลข 5 หลักที่อยู่ท้าย)
            postal_match = re.search(r'(\d{5})\s*$', address_full)
            if postal_match:
                address_data['postal_code'] = postal_match.group(1)
        
        return address_data
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # ไม่มีข้อมูลบัญชี (ว่าง)
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ"""
        # ไม่มีหมายเหตุ (ว่าง)
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร (1 = มีภาษีมูลค่าเพิ่ม, 2 = ไม่มีภาษีมูลค่าเพิ่ม)"""
        # ถ้ามียอดภาษี แสดงว่ามีภาษีมูลค่าเพิ่ม
        if amounts.get('vat_amount') and amounts['vat_amount'] > 0:
            return 1  # มีภาษีมูลค่าเพิ่ม
        
        return 1  # มีภาษีมูลค่าเพิ่ม (ตามที่ระบุ)
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ (optional)
            filepath: path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        branch = self.extract_branch(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text)
        address_data = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่: ค่าธรรมเนียม_Ksher
        new_filename = "ค่าธรรมเนียม_Ksher"
        if filename:
            # เพิ่มนามสกุลไฟล์ถ้ามี
            if '.' in filename:
                ext = filename.split('.')[-1]
                new_filename = f"{new_filename}.{ext}"
        
        return {
            'success': True,
            'company': 'KSHER',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'address': address_data.get('address_full', ''),
            'address_full': address_data.get('address_full', ''),
            'building_number': address_data.get('building_number', ''),
            'other_info': address_data.get('other_info', ''),
            'soi': address_data.get('soi', ''),
            'road': address_data.get('road', ''),
            'subdistrict': address_data.get('subdistrict', ''),
            'district': address_data.get('district', ''),
            'province': address_data.get('province', ''),
            'postal_code': address_data.get('postal_code', ''),
            'account_name': account_info['account_name'],
            'account_code': account_info['account_code'],
            'withholding_tax_percent': withholding['withholding_tax_percent'],
            'withholding_tax_amount': withholding['withholding_tax_amount'],
            'amount_before_vat': amounts['amount_before_vat'],
            'vat_amount': amounts['vat_amount'],
            'total_amount': amounts['total_amount'],
            'remark': remark,
            'new_filename': new_filename,
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,
        }

