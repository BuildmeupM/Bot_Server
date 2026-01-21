"""
SHANGHAI JINJIANG SHIPPING Invoice Extractor
===========================================
Extractor สำหรับดึงข้อมูลจาก SHANGHAI JINJIANG SHIPPING (GROUP) CO., LTD.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class ShanghaiJinjiangShippingExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก SHANGHAI JINJIANG SHIPPING (GROUP) CO., LTD."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "SHANGHAI JINJIANG SHIPPING (GROUP) CO., LTD.",
        "SHANGHAI JINJIANG SHIPPING",
        "Shanghai Jinjiang Shipping"
    ]
    
    # Tax ID
    TAX_ID = "0993000482565"
    
    def __init__(self):
        """Initialize SHANGHAI JINJIANG SHIPPING Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ SHANGHAI JINJIANG SHIPPING (GROUP) CO., LTD. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "SHANGHAI JINJIANG SHIPPING (GROUP) CO., LTD."
        2. Tax ID "0993000482565"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร SHANGHAI JINJIANG SHIPPING (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier.upper() in text.upper() for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0993000482565"
        has_tax_id = self.TAX_ID in text or "Tax ID:" + self.TAX_ID in text
        
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
        return "SHANGHAI JINJIANG SHIPPING (GROUP) CO., LTD."
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: Tax ID: 0993000482565 (Head Office) Tel. +66 (0) 2460-9659
        patterns = [
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0993000482565
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID: 0993000482565
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0993000482565
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี 0993000482565
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id = match.group(1).strip()
                if len(tax_id) == 13 and tax_id == self.TAX_ID:
                    return tax_id
        
        # Fallback: ถ้าไม่พบข้อมูล ให้ใช้ค่า default
        logger.info(f"⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา"""
        # ไม่มีสาขา (ว่าง)
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: DATE : 03-Nov-25
        patterns = [
            r'DATE\s*[:.]?\s*(\d{1,2})-([A-Za-z]{3})-(\d{2,4})',  # DATE : 03-Nov-25
            r'Date\s*[:.]?\s*(\d{1,2})-([A-Za-z]{3})-(\d{2,4})',  # Date : 03-Nov-25
            r'วันที่\s*Date\s*[:.]?\s*(\d{1,2})-([A-Za-z]{3})-(\d{2,4})',  # วันที่ Date : 03-Nov-25
        ]
        
        month_map = {
            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
            'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month_abbr = match.group(2).upper()
                year_str = match.group(3)
                
                month = month_map.get(month_abbr, '01')
                
                # แปลงปี
                if len(year_str) == 2:
                    year = '20' + year_str
                else:
                    year = year_str
                
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: NO. : SJJ-RC25110027
        # ต้องหลีกเลี่ยงการจับตัวเลขจากที่อยู่ (เช่น 1168/110)
        
        patterns = [
            # Pattern 1: NO. : SJJ-RC25110027 (เฉพาะเจาะจงสำหรับรูปแบบ SJJ-RC)
            r'NO\.\s*[:.]?\s*(SJJ[\-]?RC\d+)',  # NO. : SJJ-RC25110027
            r'No\.\s*[:.]?\s*(SJJ[\-]?RC\d+)',  # No. : SJJ-RC25110027
            # Pattern 2: NO. : SJJ-RC25110027 (รองรับรูปแบบที่มี -)
            r'NO\.\s*[:.]?\s*([A-Z]{2,}[\-][A-Z]{2,}\d+)',  # NO. : SJJ-RC25110027
            r'No\.\s*[:.]?\s*([A-Z]{2,}[\-][A-Z]{2,}\d+)',  # No. : SJJ-RC25110027
            # Pattern 3: รองรับรูปแบบทั่วไป (แต่ต้องมีตัวอักษรอย่างน้อย 2 ตัว)
            r'NO\.\s*[:.]?\s*([A-Z]{2,}[A-Z0-9\-]+)',  # NO. : SJJ-RC25110027
            r'No\.\s*[:.]?\s*([A-Z]{2,}[A-Z0-9\-]+)',  # No. : SJJ-RC25110027
            # Pattern 4: รองรับรูปแบบที่มีตัวเลขนำหน้า (แต่ต้องมีตัวอักษร)
            r'NO\.\s*[:.]?\s*([A-Z0-9]{3,}[A-Z][A-Z0-9\-]*)',  # NO. : SJJ-RC25110027
            r'เลขที่\s*[:.]?\s*([A-Z]{2,}[A-Z0-9\-]+)',  # เลขที่: SJJ-RC25110027
            r'Document\s+No\.\s*[:.]?\s*([A-Z]{2,}[A-Z0-9\-]+)',  # Document No. : SJJ-RC25110027
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                doc_number = match.group(1).strip()
                # ตรวจสอบว่าไม่ใช่ตัวเลขล้วนๆ (เพื่อหลีกเลี่ยงการจับจากที่อยู่)
                if re.match(r'^\d+$', doc_number):
                    continue
                # ตรวจสอบว่ามีตัวอักษรอย่างน้อย 2 ตัว
                if len(re.findall(r'[A-Z]', doc_number, re.IGNORECASE)) < 2:
                    continue
                # ตรวจสอบว่าไม่ใช่รูปแบบที่อยู่ (เช่น 1168/110)
                if re.match(r'^\d+/\d+$', doc_number):
                    continue
                # ตรวจสอบความยาว (เลขที่เอกสารควรมีความยาวอย่างน้อย 5 ตัวอักษร)
                if len(doc_number) < 5:
                    continue
                logger.info(f"✅ พบเลขที่เอกสาร: {doc_number}")
                return doc_number
        
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง (ชื่อไฟล์เก่า ตัด VAT_, WHT_, None_vat_ และไม่เอา EXC_ กับข้อมูลที่อยู่ด้านหลัง และไม่เอา .pdf)"""
        if not filename:
            return None
        
        # ลบ VAT_, WHT_, None_vat_ ออกจากชื่อไฟล์
        cleaned = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename, flags=re.IGNORECASE)
        
        # ตัด EXC_ และข้อมูลที่อยู่ด้านหลังออก
        cleaned = re.sub(r'EXC_[^\s.]*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'EXC-[^\s.]*', '', cleaned, flags=re.IGNORECASE)
        
        # ลบ .pdf
        cleaned = re.sub(r'\.pdf$', '', cleaned, flags=re.IGNORECASE)
        
        # ลบช่องว่างที่เหลือ
        cleaned = cleaned.strip()
        
        return cleaned if cleaned else None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # กำหนดชื่อบัญชีเป็น "ค่าใช้จ่ายในการขนส่ง" (ค่าคงที่)
        return {
            'account_name': 'ค่าใช้จ่ายในการขนส่ง',
            'account_code': None
        }
    
    def _extract_from_html_table(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลจากตาราง HTML โดยค้นหา AMOUNT (THB) และ TOTAL
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            Dictionary ที่มีข้อมูลที่ดึงได้
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        try:
            # หาตาราง HTML ทั้งหมด
            table_pattern = r'<table[^>]*>(.*?)</table>'
            tables = re.findall(table_pattern, text, re.DOTALL | re.IGNORECASE)
            
            if not tables:
                return result
            
            # วนลูปทุกตาราง
            for table_html in tables:
                # แยก rows
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
                
                # วนลูปทุกแถวเพื่อหาข้อมูล
                for row in rows:
                    # แยก cells
                    cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
                    
                    if not cells:
                        continue
                    
                    # ทำความสะอาด cell content
                    cleaned_cells = []
                    for cell in cells:
                        # ลบ HTML tags
                        cell_text = re.sub(r'<[^>]+>', '', cell)
                        # ลบช่องว่างส่วนเกิน
                        cell_text = re.sub(r'\s+', ' ', cell_text).strip()
                        cleaned_cells.append(cell_text)
                    
                    if len(cleaned_cells) < 2:
                        continue
                    
                    # ตรวจสอบว่าเป็นแถวที่ต้องการ
                    row_text = ' '.join(cleaned_cells)
                    row_upper = row_text.upper()
                    
                    # หา AMOUNT (THB)
                    if 'AMOUNT' in row_upper and '(THB)' in row_text and not result['amount_before_vat']:
                        # หาตัวเลขใน cell สุดท้าย
                        last_cell = cleaned_cells[-1].strip()
                        amount_match = re.search(r'([\d,]+\.\d{2})', last_cell)
                        if amount_match:
                            try:
                                result['amount_before_vat'] = float(amount_match.group(1).replace(',', ''))
                                logger.info(f"✅ ดึงยอดก่อนภาษีจากตาราง HTML: {result['amount_before_vat']}")
                            except ValueError:
                                pass
                        # ถ้ายังไม่ได้ ลองหาจาก cell อื่นๆ
                        if result['amount_before_vat'] is None:
                            for cell in cleaned_cells:
                                amount_match = re.search(r'([\d,]+\.\d{2})', cell)
                                if amount_match:
                                    try:
                                        amount = float(amount_match.group(1).replace(',', ''))
                                        if amount > 0:
                                            result['amount_before_vat'] = amount
                                            logger.info(f"✅ ดึงยอดก่อนภาษีจากตาราง HTML (จาก cell อื่น): {result['amount_before_vat']}")
                                            break
                                    except ValueError:
                                        pass
                    
                    # หา TOTAL
                    if 'TOTAL' in row_upper and not result['total_amount']:
                        # ตรวจสอบว่าไม่ใช่ "VALUE ADDED TAX"
                        if 'VALUE ADDED TAX' in row_upper:
                            continue
                        
                        # ตรวจสอบว่ามี TOTAL เป็น cell แยกต่างหาก
                        has_total = False
                        total_cell_index = -1
                        for idx, cell in enumerate(cleaned_cells):
                            cell_upper = cell.strip().upper()
                            if cell_upper == 'TOTAL' or (cell_upper.startswith('TOTAL') and len(cell.strip()) <= 10):
                                has_total = True
                                total_cell_index = idx
                                break
                        
                        if has_total:
                            # หาตัวเลขใน cell สุดท้าย
                            last_cell = cleaned_cells[-1].strip()
                            total_match = re.search(r'([\d,]+\.\d{2})', last_cell)
                            if total_match:
                                try:
                                    result['total_amount'] = float(total_match.group(1).replace(',', ''))
                                    logger.info(f"✅ ดึงยอดรวมจากตาราง HTML: {result['total_amount']}")
                                except ValueError:
                                    pass
                            # ถ้ายังไม่ได้ ลองหาจาก cell ที่อยู่หลัง TOTAL
                            elif total_cell_index >= 0 and total_cell_index + 1 < len(cleaned_cells):
                                next_cell = cleaned_cells[total_cell_index + 1].strip()
                                total_match = re.search(r'([\d,]+\.\d{2})', next_cell)
                                if total_match:
                                    try:
                                        result['total_amount'] = float(total_match.group(1).replace(',', ''))
                                        logger.info(f"✅ ดึงยอดรวมจากตาราง HTML (จาก cell ถัดไป): {result['total_amount']}")
                                    except ValueError:
                                        pass
                        # ถ้ายังไม่ได้ ลองหาจาก cell สุดท้ายของแถว
                        if result['total_amount'] is None:
                            last_cell = cleaned_cells[-1].strip()
                            total_match = re.search(r'([\d,]+\.\d{2})', last_cell)
                            if total_match:
                                try:
                                    amount = float(total_match.group(1).replace(',', ''))
                                    if amount > 0:
                                        result['total_amount'] = amount
                                        logger.info(f"✅ ดึงยอดรวมจากตาราง HTML (จาก cell สุดท้าย): {result['total_amount']}")
                                except ValueError:
                                    pass
                
                # ถ้าได้ข้อมูลครบแล้ว ให้ return
                if result['amount_before_vat'] and result['total_amount']:
                    logger.info(f"✅ ดึงยอดเงินจากตาราง HTML สำเร็จ: amount_before_vat={result['amount_before_vat']}, total_amount={result['total_amount']}")
                    return result
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงข้อมูลจากตาราง HTML: {e}")
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงยอดเงิน"""
        # Pattern: ผิด ตก ยกเว้น / E & O.E. | ผิด ตก ยกเว้น / E & O.E. | AMOUNT (THB) | 4,900.00
        # Pattern:  |  | TOTAL | 4,900.00
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        
        amount_before_vat = None
        vat_amount = 0.00  # ไม่มีภาษีมูลค่าเพิ่ม
        total_amount = None
        
        # วิธีที่ 0: ลองดึงจาก HTML table ก่อน (ถ้าหน้าเว็บอ่านได้)
        html_table_result = self._extract_from_html_table(text)
        if html_table_result.get('amount_before_vat') or html_table_result.get('total_amount'):
            logger.info(f"✅ พบข้อมูลในตาราง HTML")
            if html_table_result.get('amount_before_vat'):
                amount_before_vat = html_table_result['amount_before_vat']
                logger.info(f"✅ ดึงยอดก่อนภาษีจากตาราง HTML: {amount_before_vat}")
            if html_table_result.get('total_amount'):
                total_amount = html_table_result['total_amount']
                logger.info(f"✅ ดึงยอดรวมจากตาราง HTML: {total_amount}")
            
            # ถ้าดึงข้อมูลครบแล้ว ให้ return
            if amount_before_vat and total_amount:
                return {
                    'amount_before_vat': amount_before_vat,
                    'vat_amount': vat_amount,
                    'total_amount': total_amount
                }
        
        # ใช้วิธีแยกบรรทัดก่อน เพื่อหลีกเลี่ยงการจับตัวเลขผิดจากบรรทัดอื่น
        lines = text.split('\n')
        
        # ดึงยอดก่อนภาษี: หาบรรทัดที่มี "AMOUNT (THB)" แล้วดึงค่าจาก | ตัวสุดท้าย
        for i, line in enumerate(lines):
            line_upper = line.upper()
            line_stripped = line.strip()
            
            # ตรวจสอบว่าบรรทัดนี้มี "AMOUNT (THB)" หรือ "AMOUNT(THB)"
            if 'AMOUNT (THB)' in line_upper or 'AMOUNT(THB)' in line_upper:
                logger.debug(f"🔍 พบบรรทัดที่มี AMOUNT (THB): {line_stripped}")
                
                # Pattern 1: หา AMOUNT (THB) | แล้วดึงตัวเลขที่อยู่หลัง | (รองรับหลาย |)
                # รูปแบบ: ... | AMOUNT (THB) | 4,900.00
                amount_match = re.search(r'AMOUNT\s*\(THB\)\s*\|\s*([\d,]+\.?\d{2})', line, re.IGNORECASE)
                if amount_match:
                    amount_str = amount_match.group(1).replace(',', '').strip()
                    try:
                        amount_value = float(amount_str)
                        if amount_value > 0:
                            amount_before_vat = amount_value
                            logger.info(f"✅ พบยอดก่อนภาษี (Pattern 1): {amount_before_vat}")
                            break
                    except ValueError:
                        pass
                
                # Pattern 2: แยกด้วย | แล้วหาส่วนที่มี "AMOUNT (THB)" แล้วดึงค่าจากส่วนถัดไป
                if amount_before_vat is None:
                    parts = [p.strip() for p in line.split('|')]
                    for j, part in enumerate(parts):
                        if 'AMOUNT (THB)' in part.upper() or 'AMOUNT(THB)' in part.upper():
                            # ดึงค่าจากส่วนถัดไป (ถ้ามี)
                            if j + 1 < len(parts):
                                next_part = parts[j + 1].strip()
                                amount_match = re.search(r'([\d,]+\.\d{2})', next_part)
                                if amount_match:
                                    amount_str = amount_match.group(1).replace(',', '').strip()
                                    try:
                                        amount_value = float(amount_str)
                                        if amount_value > 0:
                                            amount_before_vat = amount_value
                                            logger.info(f"✅ พบยอดก่อนภาษี (Pattern 2): {amount_before_vat}")
                                            break
                                    except ValueError:
                                        pass
                    
                    if amount_before_vat is not None:
                        break
                
                # Pattern 3: ดึงค่าจากส่วนสุดท้ายของบรรทัด (ถ้ายังไม่พบ)
                if amount_before_vat is None:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 3:  # ต้องมีอย่างน้อย 3 ส่วน
                        last_part = parts[-1].strip()
                        # ดึงตัวเลขที่มีทศนิยม 2 ตำแหน่ง
                        amount_match = re.search(r'([\d,]+\.\d{2})', last_part)
                        if amount_match:
                            amount_str = amount_match.group(1).replace(',', '').strip()
                            try:
                                amount_value = float(amount_str)
                                if amount_value > 0:
                                    amount_before_vat = amount_value
                                    logger.info(f"✅ พบยอดก่อนภาษี (Pattern 3): {amount_before_vat}")
                                    break
                            except ValueError:
                                pass
        
        # ดึงยอดรวม: หาบรรทัดที่มี "TOTAL" แล้วดึงค่าจาก | ตัวสุดท้าย
        for i, line in enumerate(lines):
            line_upper = line.upper()
            line_stripped = line.strip()
            
            # ตรวจสอบว่าบรรทัดนี้มี "TOTAL" และมี |
            if 'TOTAL' in line_upper and '|' in line:
                # ตรวจสอบว่าไม่ใช่ "VALUE ADDED TAX" (เพราะอาจจะมี TOTAL ในคำอื่น)
                if 'VALUE ADDED TAX' in line_upper:
                    continue
                
                logger.debug(f"🔍 พบบรรทัดที่มี TOTAL: {line_stripped}")
                
                # Pattern 1: หา TOTAL | แล้วดึงตัวเลขที่อยู่หลัง | (รองรับหลาย |)
                # รูปแบบ: ... | TOTAL | 4,900.00
                total_match = re.search(r'TOTAL\s*\|\s*([\d,]+\.?\d{2})', line, re.IGNORECASE)
                if total_match:
                    amount_str = total_match.group(1).replace(',', '').strip()
                    try:
                        amount_value = float(amount_str)
                        if amount_value > 0:
                            total_amount = amount_value
                            logger.info(f"✅ พบยอดรวม (Pattern 1): {total_amount}")
                            break
                    except ValueError:
                        pass
                
                # Pattern 2: แยกด้วย | แล้วหาส่วนที่มี "TOTAL" แล้วดึงค่าจากส่วนถัดไป
                if total_amount is None:
                    parts = [p.strip() for p in line.split('|')]
                    for j, part in enumerate(parts):
                        if 'TOTAL' in part.upper() and 'VALUE ADDED TAX' not in part.upper():
                            # ดึงค่าจากส่วนถัดไป (ถ้ามี)
                            if j + 1 < len(parts):
                                next_part = parts[j + 1].strip()
                                amount_match = re.search(r'([\d,]+\.\d{2})', next_part)
                                if amount_match:
                                    amount_str = amount_match.group(1).replace(',', '').strip()
                                    try:
                                        amount_value = float(amount_str)
                                        if amount_value > 0:
                                            total_amount = amount_value
                                            logger.info(f"✅ พบยอดรวม (Pattern 2): {total_amount}")
                                            break
                                    except ValueError:
                                        pass
                    
                    if total_amount is not None:
                        break
                
                # Pattern 3: ดึงค่าจากส่วนสุดท้ายของบรรทัด (ถ้ายังไม่พบ)
                if total_amount is None:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 2:  # ต้องมีอย่างน้อย 2 ส่วน
                        last_part = parts[-1].strip()
                        # ดึงตัวเลขที่มีทศนิยม 2 ตำแหน่ง
                        amount_match = re.search(r'([\d,]+\.\d{2})', last_part)
                        if amount_match:
                            amount_str = amount_match.group(1).replace(',', '').strip()
                            try:
                                amount_value = float(amount_str)
                                if amount_value > 0:
                                    total_amount = amount_value
                                    logger.info(f"✅ พบยอดรวม (Pattern 3): {total_amount}")
                                    break
                            except ValueError:
                                pass
        
        # ถ้าพบยอดรวมแต่ไม่พบยอดก่อนภาษี ให้ใช้ยอดรวมเป็นยอดก่อนภาษี
        if total_amount is not None and amount_before_vat is None:
            amount_before_vat = total_amount
            logger.info(f"✅ ใช้ยอดรวมเป็นยอดก่อนภาษี: {amount_before_vat}")
        
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        vat_amount = 0.00
        
        return {
            'amount_before_vat': amount_before_vat,
            'vat_amount': vat_amount,
            'total_amount': total_amount
        }
    
    def extract_address(self, text: str) -> str:
        """ดึงที่อยู่"""
        # กำหนดที่อยู่เป็นค่าคงที่
        return "Lumpini Tower, 37th floor, No.1168/110, Rama 4 Road, Tungmahamek, Sathorn, Bangkok 10120"
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (REF. : R2554C101631RUD และชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_)"""
        remark_parts = []
        
        # ดึง REF. : R2554C101631RUD
        ref_patterns = [
            r'REF\.\s*[:.]?\s*([A-Z0-9]+)',  # REF. : R2554C101631RUD
            r'Ref\.\s*[:.]?\s*([A-Z0-9]+)',  # Ref. : R2554C101631RUD
            r'อ้างอิง\s*[:.]?\s*([A-Z0-9]+)',  # อ้างอิง: R2554C101631RUD
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ref_no = match.group(1).strip()
                if ref_no not in remark_parts:
                    remark_parts.append(ref_no)
                break
        
        # ดึงชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_
        if filename:
            # หาชื่อไฟล์ที่เริ่มต้นด้วย EXC_ หรือ EXC-
            exc_match = re.search(r'(EXC[_\-.][^\s.]*)', filename, re.IGNORECASE)
            if exc_match:
                exc_part = exc_match.group(1).strip()
                if exc_part not in remark_parts:
                    remark_parts.append(exc_part)
        
        # รวมหมายเหตุ
        if remark_parts:
            return ' '.join(remark_parts)
        
        return None
    
    def clean_filename(self, filename: str) -> str:
        """ทำความสะอาดชื่อไฟล์ (ลบ VAT_, WHT_, None_vat_)"""
        if not filename:
            return filename
        
        cleaned = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename, flags=re.IGNORECASE)
        return cleaned.strip()
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร"""
        # ไม่มีภาษีมูลค่าเพิ่ม (VAT = 0.00)
        return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร SHANGHAI JINJIANG SHIPPING
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร SHANGHAI JINJIANG SHIPPING หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร SHANGHAI JINJIANG SHIPPING (GROUP) CO., LTD.'
            }
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        branch = self.extract_branch(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text)
        reference = self.extract_reference(text, filename)
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, None_vat_, WHT_)
        new_filename = self.clean_filename(filename) if filename else filename
        
        # แยกที่อยู่เป็นส่วนๆ
        address_full = address or ''
        building_number = 'No.1168/110'
        other_info = 'Lumpini Tower, 37th floor'
        soi = ''
        road = 'Rama 4 Road'
        subdistrict = 'Tungmahamek'
        district = 'Sathorn'
        province = 'Bangkok'
        postal_code = '10120'
        
        # ตั้งค่า skip_amount_adjustment = True เพื่อไม่ให้ระบบปรับยอดเงิน (ใช้ค่าที่อ่านได้เท่านั้น)
        # เพราะเอกสารนี้ไม่มีภาษีมูลค่าเพิ่ม
        return {
            'success': True,
            'company': 'SHANGHAI_JINJIANG_SHIPPING',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'reference': reference,
            'address': address,
            'address_full': address_full,
            'building_number': building_number,
            'other_info': other_info,
            'soi': soi,
            'road': road,
            'subdistrict': subdistrict,
            'district': district,
            'province': province,
            'postal_code': postal_code,
            'account_name': account_info.get('account_name'),
            'account_code': account_info.get('account_code'),
            'amount_before_vat': amounts.get('amount_before_vat'),
            'vat_amount': amounts.get('vat_amount'),
            'total_amount': amounts.get('total_amount'),
            'withholding_tax_percent': withholding.get('withholding_tax_percent'),
            'withholding_tax_amount': withholding.get('withholding_tax_amount'),
            'remark': remark,
            'new_filename': new_filename,
            'old_filename': filename,  # เพิ่มชื่อไฟล์เก่า
            'document_type': document_type,
            'skip_amount_adjustment': True  # ไม่ให้ปรับยอดเงิน (ใช้ค่าที่อ่านได้เท่านั้น)
        }

