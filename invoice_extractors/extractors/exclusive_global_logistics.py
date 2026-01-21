"""
Exclusive Global Logistics Invoice Extractor
============================================
Extractor สำหรับดึงข้อมูลจาก บริษัท เอ็กซ์คลูซีฟ โกลบอล โลจิสติกส์ จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class ExclusiveGlobalLogisticsExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท เอ็กซ์คลูซีฟ โกลบอล โลจิสติกส์ จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "เอ็กซ์คลูซีฟ โกลบอล โลจิสติกส์",
        "Exclusive Global Logistics"
    ]
    
    def __init__(self):
        """Initialize Exclusive Global Logistics Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Exclusive Global Logistics หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท เอ็กซ์คลูซีฟ โกลบอล โลจิสติกส์ จำกัด"
        2. Tax ID "0245567001001"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Exclusive Global Logistics (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0245567001001"
        has_tax_id = "0245567001001" in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "บริษัท เอ็กซ์คลูซีฟ โกลบอล โลจิสติกส์ จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TaxID 0245567001001 หรือ Tax ID No. 0245567001001 หรือ เลขที่ผู้เสียภาษี 0245567001001
        # เพิ่มความสำคัญให้กับ "เลขที่ผู้เสียภาษี" เป็นอันดับแรก (ตามข้อมูล OCR บรรทัด 441)
        # รองรับกรณีที่ OCR อ่านผิด เช่น 0 เป็น O หรือ 1 เป็น l
        patterns = [
            # รูปแบบหลัก: เลขที่ผู้เสียภาษี 0245567001001 (ไม่มีเครื่องหมาย : หรือ .)
            r'เลขที่ผู้เสียภาษี\s+([0-9OIl]{13})(?=\s|$|[^\d])',  # เลขที่ผู้เสียภาษี 0245567001001 (มีข้อความต่อท้าย)
            r'เลขที่ผู้เสียภาษี\s+([0-9OIl]{13})',  # เลขที่ผู้เสียภาษี 0245567001001
            # รูปแบบที่มีเครื่องหมาย : หรือ . ตามหลัง
            r'เลขที่ผู้เสียภาษี\s*[:.]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # เลขที่ผู้เสียภาษี: 0245567001001
            r'เลขที่ผู้เสียภาษี\s*[:.]?\s*([0-9OIl]{13})',  # เลขที่ผู้เสียภาษี: 0245567001001
            # รูปแบบที่มีช่องว่างในเลข (0245 5670 01001)
            r'เลขที่ผู้เสียภาษี\s+([0-9OIl]{4}\s+[0-9OIl]{4}\s+[0-9OIl]{5})(?=\s|$|[^\d])',  # เลขที่ผู้เสียภาษี 0245 5670 01001
            r'เลขที่ผู้เสียภาษี\s+([0-9OIl]{4}\s+[0-9OIl]{4}\s+[0-9OIl]{5})',  # เลขที่ผู้เสียภาษี 0245 5670 01001
            # รูปแบบอื่นๆ
            r'เลขประจำตัวผู้เสียภาษีอากร\s+([0-9OIl]{13})(?=\s|$|[^\d])',  # เลขประจำตัวผู้เสียภาษีอากร 0245567001001
            r'เลขประจำตัวผู้เสียภาษีอากร\s+([0-9OIl]{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0245567001001
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # เลขประจำตัวผู้เสียภาษีอากร: 0245567001001
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*([0-9OIl]{13})',  # เลขประจำตัวผู้เสียภาษีอากร: 0245567001001
            r'TaxID\s*[:.]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # TaxID: 0245567001001
            r'TaxID\s*[:.]?\s*([0-9OIl]{13})',  # TaxID: 0245567001001
            r'Tax\s+ID\s+No[.:]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # Tax ID No.: 0245567001001
            r'Tax\s+ID\s+No[.:]?\s*([0-9OIl]{13})',  # Tax ID No.: 0245567001001
            r'Tax\s+ID\s*[:.]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # Tax ID: 0245567001001
            r'Tax\s+ID\s*[:.]?\s*([0-9OIl]{13})',  # Tax ID: 0245567001001
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # เลขประจำตัวผู้เสียภาษี: 0245567001001
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*([0-9OIl]{13})',  # เลขประจำตัวผู้เสียภาษี: 0245567001001
            r'TAX\s+ID\s*[:.]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # TAX ID: 0245567001001
            r'TAX\s+ID\s*[:.]?\s*([0-9OIl]{13})',  # TAX ID: 0245567001001
            r'TAXID\s*[:.]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # TAXID: 0245567001001
            r'TAXID\s*[:.]?\s*([0-9OIl]{13})',  # TAXID: 0245567001001
            r'Tax\s*ID\s*[:.]?\s*([0-9OIl]{4}\s+[0-9OIl]{4}\s+[0-9OIl]{5})(?=\s|$|[^\d])',  # Tax ID: 0245 5670 01001 (มีช่องว่าง)
            r'Tax\s*ID\s*[:.]?\s*([0-9OIl]{4}\s+[0-9OIl]{4}\s+[0-9OIl]{5})',  # Tax ID: 0245 5670 01001 (มีช่องว่าง)
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*([0-9OIl]{4}\s+[0-9OIl]{4}\s+[0-9OIl]{5})(?=\s|$|[^\d])',  # เลขประจำตัวผู้เสียภาษี: 0245 5670 01001
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*([0-9OIl]{4}\s+[0-9OIl]{4}\s+[0-9OIl]{5})',  # เลขประจำตัวผู้เสียภาษี: 0245 5670 01001
            # รูปแบบทั่วไป (ต้องตรวจสอบว่าเป็น 0245567001001)
            r'([0-9OIl]{4}\s+[0-9OIl]{4}\s+[0-9OIl]{5})',  # 0245 5670 01001 (รูปแบบทั่วไป)
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                tax_id = match.group(1).replace(' ', '').replace('-', '')  # ลบช่องว่างและขีด
                # แก้ไขตัวอักษรที่ OCR อ่านผิด
                tax_id = tax_id.replace('O', '0').replace('I', '1').replace('l', '1')
                if len(tax_id) == 13 and tax_id == "0245567001001":
                    return tax_id
        
        # Fallback 1: ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่ (รองรับช่องว่างและขีด)
        text_clean = text.replace(' ', '').replace('-', '').replace('O', '0').replace('I', '1').replace('l', '1')
        if "0245567001001" in text_clean:
            return "0245567001001"
        
        # Fallback 2: หาเลข 13 หลักที่อยู่ใกล้กับคำว่า "เลขที่ผู้เสียภาษี" หรือ "Tax ID"
        # หา "เลขที่ผู้เสียภาษี" หรือ "Tax ID" แล้วหาตัวเลข 13 หลักในระยะ 50 ตัวอักษร
        tax_keywords = [
            r'เลขที่ผู้เสียภาษี',
            r'เลขประจำตัวผู้เสียภาษีอากร',
            r'Tax\s+ID',
            r'เลขประจำตัวผู้เสียภาษี',
        ]
        
        for keyword_pattern in tax_keywords:
            keyword_matches = re.finditer(keyword_pattern, text, re.IGNORECASE)
            for keyword_match in keyword_matches:
                # หาตัวเลข 13 หลักในระยะ 50 ตัวอักษรหลัง keyword
                start_pos = keyword_match.end()
                search_text = text[start_pos:start_pos+50]
                # หาเลข 13 หลัก (รองรับช่องว่างและตัวอักษรที่ OCR อ่านผิด)
                number_match = re.search(r'([0-9OIl]{4}\s*[0-9OIl]{4}\s*[0-9OIl]{5})', search_text)
                if number_match:
                    tax_id = number_match.group(1).replace(' ', '').replace('-', '')
                    # แก้ไขตัวอักษรที่ OCR อ่านผิด
                    tax_id = tax_id.replace('O', '0').replace('I', '1').replace('l', '1')
                    if len(tax_id) == 13 and tax_id == "0245567001001":
                        return tax_id
        
        # Fallback 3: ถ้าไม่พบข้อมูล ให้ใช้ค่า default สำหรับ Exclusive Global Logistics
        # เลขประจำตัวผู้เสียภาษีของบริษัท เอ็กซ์คลูซีฟ โกลบอล โลจิสติกส์ จำกัด คือ 0245567001001
        logger.info("⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: 0245567001001")
        return "0245567001001"
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: 03/11/2025 หรือ Date: 03/11/2025
        pattern = r'(?:Date\s*[:.]?\s*)?(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern, text)
        
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            return f"{day}/{month}/{year}"
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: 294/7 ถนนร่มเกล้า แขวงคลองสามประเวศ เขตลาดกระบัง กรุงเทพมหานคร 10520
        
        Returns:
            ที่อยู่รวม (string) - ระบบจะแยกเป็นส่วนๆ อัตโนมัติใน parse_address()
        """
        # ที่อยู่: 294/7 ถนนร่มเกล้า แขวงคลองสามประเวศ เขตลาดกระบัง กรุงเทพมหานคร 10520
        # ส่งคืนเป็น string เดียว ระบบจะแยกเป็นส่วนๆ อัตโนมัติใน parse_address()
        return "294/7 ถนนร่มเกล้า แขวงคลองสามประเวศ เขตลาดกระบัง กรุงเทพมหานคร 10520"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': None,
            'account_code': None
        }
    
    def has_wht_3_percent(self, text: str) -> bool:
        """
        ตรวจสอบว่าเอกสารมี "หัก ภาษี ณ ที่จ่าย WHT 3%" หรือไม่
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้ามี WHT 3%
        """
        if not text:
            return False
        
        # Pattern: หัก ภาษี ณ ที่จ่าย WHT 3%
        patterns = [
            r'หัก\s*ภาษี\s*ณ\s*ที่จ่าย\s*WHT\s*3%',
            r'หัก\s*ภาษี\s*ณ\s*ที่จ่าย\s*WHT\s*3\s*%',
            r'WHT\s*3%',
            r'WHT\s*3\s*%',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลหัก ณ ที่จ่าย
        
        ถ้ามี "หัก ภาษี ณ ที่จ่าย WHT 3%" ให้ดึง 3% มา
        """
        result = {
            'withholding_tax_percent': 0.0,
            'withholding_tax_amount': 0.0
        }
        
        # ตรวจสอบว่ามี WHT 3% หรือไม่
        if self.has_wht_3_percent(text):
            # Pattern: หัก ภาษี ณ ที่จ่าย WHT 3%
            patterns = [
                r'หัก\s*ภาษี\s*ณ\s*ที่จ่าย\s*WHT\s*3\s*%',
                r'หัก\s*ภาษี\s*ณ\s*ที่จ่าย\s*WHT\s*3%',
                r'WHT\s*3\s*%',
                r'WHT\s*3%',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result['withholding_tax_percent'] = 3.0
                    logger.info(f"✅ พบ WHT 3%")
                    break
        
        return result
    
    def _extract_from_html_table(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลจากตาราง HTML โดยจับจากคอลัมน์ AMOUNT
        
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
                
                # หา header row เพื่อหาคอลัมน์ AMOUNT
                header_row = None
                amount_col_index = None
                
                for i, row in enumerate(rows[:5]):  # ตรวจสอบ 5 แถวแรก
                    cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL | re.IGNORECASE)
                    cleaned_cells = []
                    for cell in cells:
                        cell_text = re.sub(r'<[^>]+>', '', cell)
                        cell_text = re.sub(r'\s+', ' ', cell_text).strip()
                        cleaned_cells.append(cell_text)
                    
                    # ตรวจสอบว่าเป็น header row หรือไม่ (มีคำว่า AMOUNT)
                    row_text = ' '.join(cleaned_cells).upper()
                    if 'AMOUNT' in row_text:
                        header_row = cleaned_cells
                        # หา index ของคอลัมน์ AMOUNT
                        for idx, cell in enumerate(cleaned_cells):
                            if 'AMOUNT' in cell.upper():
                                amount_col_index = idx
                                break
                        break
                
                if amount_col_index is None:
                    continue
                
                # วนลูปแถวข้อมูล (ข้าม header row)
                total_amount = 0.0
                for row in rows[1:]:
                    cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL | re.IGNORECASE)
                    if len(cells) <= amount_col_index:
                        continue
                    
                    # ดึงค่า AMOUNT จากคอลัมน์ที่กำหนด
                    amount_cell = cells[amount_col_index]
                    amount_text = re.sub(r'<[^>]+>', '', amount_cell)
                    amount_text = re.sub(r'\s+', ' ', amount_text).strip()
                    
                    # หาตัวเลขใน cell
                    numbers = re.findall(r'([\d,]+\.?\d{2})', amount_text)
                    if numbers:
                        try:
                            amount = float(numbers[0].replace(',', '').replace(' ', ''))
                            if amount > 0:
                                total_amount += amount
                        except ValueError:
                            continue
                
                if total_amount > 0:
                    result['amount_before_vat'] = total_amount
                    result['vat_amount'] = 0.0  # ไม่มีภาษี
                    result['total_amount'] = total_amount
                    logger.info(f"✅ ดึงยอดเงินจากตาราง HTML (คอลัมน์ AMOUNT): {total_amount}")
                    return result
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงข้อมูลจากตาราง HTML: {e}")
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        ถ้ามี WHT 3% ให้ดึงข้อมูลตามรูปแบบ:
        - TAXABLE AMOUNT: 3,300.00
        - ภาษีมูลค่าเพิ่ม VAT 7% | 231.00
        - Total | 3,531.00
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี
                'vat_amount': float,          # ยอดภาษี
                'total_amount': float         # ยอดรวม
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # ตรวจสอบว่ามี WHT 3% หรือไม่
        has_wht = self.has_wht_3_percent(text)
        
        if has_wht:
            # กรณีมี WHT 3% - ดึงข้อมูลตามรูปแบบใหม่
            logger.info("🔍 พบ WHT 3% - ใช้รูปแบบการดึงข้อมูลใหม่")
            logger.info(f"📄 Text length: {len(text)} characters")
            logger.info(f"📄 Text preview (first 1000 chars): {text[:1000]}")
            
            # ทำความสะอาด text สำหรับการค้นหา
            text_clean = re.sub(r'\s+', ' ', text)
            logger.info(f"📄 Text clean length: {len(text_clean)} characters")
            # Log ส่วนที่เกี่ยวข้องกับ VAT และ Total เพื่อ debug
            if 'ภาษีมูลค่าเพิ่ม' in text_clean:
                vat_pos = text_clean.find('ภาษีมูลค่าเพิ่ม')
                vat_section = text_clean[vat_pos:vat_pos+200]
            else:
                vat_section = 'ไม่พบ'
            if 'Total' in text_clean.upper():
                total_pos = text_clean.upper().find('TOTAL')
                total_section = text_clean[total_pos:total_pos+100]
            else:
                total_section = 'ไม่พบ'
            logger.info(f"🔍 VAT section: {vat_section}")
            logger.info(f"🔍 Total section: {total_section}")
            
            # Pattern 1: TAXABLE AMOUNT: 3,300.00 หรือ (TAXABLE AMOUNT: 3,300.00)
            patterns_before_vat = [
                r'TAXABLE\s*AMOUNT\s*[:.]?\s*\(?([\d,]+\.?\d{2})\)?',
                r'\(TAXABLE\s*AMOUNT\s*[:.]?\s*([\d,]+\.?\d{2})\)',
                r'ยอดก่อนบวกภาษีมูลค่าเพิ่ม\s*[:.]?\s*\(?([\d,]+\.?\d{2})\)?',
                r'ก่อนบวกภาษีมูลค่าเพิ่ม\s*[:.]?\s*\(?([\d,]+\.?\d{2})\)?',
                r'ยอดก่อนภาษี\s*[:.]?\s*\(?([\d,]+\.?\d{2})\)?',
            ]
            
            for idx, pattern in enumerate(patterns_before_vat):
                match = re.search(pattern, text_clean, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.info(f"🔍 Pattern {idx+1} matched: '{pattern}' -> matched text: '{match.group(0)}' -> amount_str: '{amount_str}'")
                    try:
                        amount = float(amount_str)
                        if amount > 0:
                            result['amount_before_vat'] = amount
                            logger.info(f"✅ พบยอดก่อนภาษี: {result['amount_before_vat']} (pattern: {pattern})")
                            break
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                        continue
                else:
                    logger.debug(f"🔍 Pattern {idx+1} ไม่ match: '{pattern}'")
            
            if not result['amount_before_vat']:
                logger.warning(f"⚠️ ไม่พบยอดก่อนภาษี - ลองหาด้วยวิธีอื่น...")
                # ลองหาคำว่า TAXABLE หรือ AMOUNT ใน text
                if 'TAXABLE' in text_clean.upper() or 'AMOUNT' in text_clean.upper():
                    logger.info(f"🔍 พบคำว่า TAXABLE หรือ AMOUNT ใน text")
                    # ลองหา pattern ที่ยืดหยุ่นกว่า
                    flexible_patterns = [
                        r'TAXABLE[^:]*[:]\s*([\d,]+\.?\d{2})',
                        r'AMOUNT[^:]*[:]\s*([\d,]+\.?\d{2})',
                        r'([\d,]+\.?\d{2})\s*(?:บาท|Baht)?\s*(?:TAXABLE|AMOUNT)',
                    ]
                    for pattern in flexible_patterns:
                        match = re.search(pattern, text_clean, re.IGNORECASE)
                        if match:
                            amount_str = match.group(1).replace(',', '').replace(' ', '')
                            try:
                                amount = float(amount_str)
                                if amount > 0:
                                    result['amount_before_vat'] = amount
                                    logger.info(f"✅ พบยอดก่อนภาษี (flexible pattern): {result['amount_before_vat']}")
                                    break
                            except ValueError:
                                continue
            
            # Pattern 2: ภาษีมูลค่าเพิ่ม VAT 7% | 231.00 หรือ (ภาษีมูลค่าเพิ่ม VAT 7% | 231.00)
            patterns_vat = [
                r'ภาษีมูลค่าเพิ่ม\s+VAT\s+7\s*%\s*\|\s+([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม VAT 7% | 231.00 (space หลัง |)
                r'ภาษีมูลค่าเพิ่ม\s*VAT\s*7\s*%\s*\|\s+([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม VAT 7% | 231.00 (space หลัง |)
                r'ภาษีมูลค่าเพิ่ม\s*VAT\s*7%\s*\|\s+([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม VAT 7% | 231.00 (space หลัง |)
                r'ภาษีมูลค่าเพิ่ม\s*VAT\s*7\s*%\s*\|\s*([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม VAT 7% | 231.00
                r'ภาษีมูลค่าเพิ่ม\s*VAT\s*7%\s*\|\s*([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม VAT 7% | 231.00
                r'ภาษีมูลค่าเพิ่ม\s*VAT\s*7\s*%\s*\|\s*\(?([\d,]+\.?\d{2})\)?',
                r'ภาษีมูลค่าเพิ่ม\s*VAT\s*7%\s*\|\s*\(?([\d,]+\.?\d{2})\)?',
                r'\(ภาษีมูลค่าเพิ่ม\s*VAT\s*7\s*%\s*\|\s*([\d,]+\.?\d{2})\)',
                r'VAT\s+7\s*%\s*\|\s+([\d,]+\.?\d{2})',  # VAT 7% | 231.00 (space หลัง |)
                r'VAT\s*7\s*%\s*\|\s+([\d,]+\.?\d{2})',  # VAT 7% | 231.00 (space หลัง |)
                r'VAT\s*7%\s*\|\s+([\d,]+\.?\d{2})',  # VAT 7% | 231.00 (space หลัง |)
                r'VAT\s*7\s*%\s*\|\s*([\d,]+\.?\d{2})',  # VAT 7% | 231.00
                r'VAT\s*7%\s*\|\s*([\d,]+\.?\d{2})',  # VAT 7% | 231.00
                r'VAT\s*7\s*%\s*\|\s*\(?([\d,]+\.?\d{2})\)?',
                r'VAT\s*7%\s*\|\s*\(?([\d,]+\.?\d{2})\)?',
                r'ยอดภาษีมูลค่าเพิ่ม\s*[:.]?\s*\(?([\d,]+\.?\d{2})\)?',
                r'ภาษีมูลค่าเพิ่ม\s*[:.]?\s*\(?([\d,]+\.?\d{2})\)?',
            ]
            
            # ลองหาใน text เดิมก่อน (ไม่ใช่ text_clean) เพราะ text_clean อาจเปลี่ยนข้อความ
            logger.info(f"🔍 ลองหา VAT ใน text เดิม...")
            for idx, pattern in enumerate(patterns_vat):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    vat_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.info(f"🔍 VAT Pattern {idx+1} matched (ใน text เดิม): '{pattern}' -> matched text: '{match.group(0)}' -> vat_str: '{vat_str}'")
                    try:
                        vat = float(vat_str)
                        if vat > 0:
                            result['vat_amount'] = vat
                            logger.info(f"✅ พบยอดภาษี (ใน text เดิม): {result['vat_amount']} (pattern: {pattern})")
                            break
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{vat_str}', Error: {e}")
                        continue
                else:
                    logger.debug(f"🔍 VAT Pattern {idx+1} ไม่ match (ใน text เดิม): '{pattern}'")
            
            # ถ้ายังไม่พบ ให้ลองหาใน text_clean
            if not result['vat_amount']:
                logger.info(f"🔍 ลองหา VAT ใน text_clean...")
                for idx, pattern in enumerate(patterns_vat):
                    match = re.search(pattern, text_clean, re.IGNORECASE)
                    if match:
                        vat_str = match.group(1).replace(',', '').replace(' ', '')
                        logger.info(f"🔍 VAT Pattern {idx+1} matched (ใน text_clean): '{pattern}' -> matched text: '{match.group(0)}' -> vat_str: '{vat_str}'")
                        try:
                            vat = float(vat_str)
                            if vat > 0:
                                result['vat_amount'] = vat
                                logger.info(f"✅ พบยอดภาษี (ใน text_clean): {result['vat_amount']} (pattern: {pattern})")
                                break
                        except ValueError as e:
                            logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{vat_str}', Error: {e}")
                            continue
                    else:
                        logger.debug(f"🔍 VAT Pattern {idx+1} ไม่ match (ใน text_clean): '{pattern}'")
            
            if not result['vat_amount']:
                logger.warning(f"⚠️ ไม่พบยอดภาษี - ลองหาด้วยวิธีอื่น...")
                # ลองหาคำว่า VAT หรือ ภาษีมูลค่าเพิ่ม ใน text
                if 'VAT' in text_clean.upper() or 'ภาษีมูลค่าเพิ่ม' in text_clean:
                    logger.info(f"🔍 พบคำว่า VAT หรือ ภาษีมูลค่าเพิ่ม ใน text")
                    # ลองหา pattern ที่ยืดหยุ่นกว่า - รองรับทั้ง | และ HTML table format
                    flexible_patterns = [
                        # HTML table format: <td>ภาษีมูลค่าเพิ่ม VAT 7%</td><td>231.00</td>
                        r'ภาษีมูลค่าเพิ่ม\s*VAT\s*7\s*%[^<]*</td>\s*<td>\s*([\d,]+\.?\d{2})\s*</td>',
                        r'VAT\s*7\s*%[^<]*</td>\s*<td>\s*([\d,]+\.?\d{2})\s*</td>',
                        # Pipe format: ภาษีมูลค่าเพิ่ม VAT 7% | 231.00
                        r'VAT[^|]*\|\s+([\d,]+\.?\d{2})',  # VAT...| 231.00 (space หลัง |)
                        r'VAT[^|]*\|\s*([\d,]+\.?\d{2})',
                        r'ภาษีมูลค่าเพิ่ม[^|]*\|\s+([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม...| 231.00 (space หลัง |)
                        r'ภาษีมูลค่าเพิ่ม[^|]*\|\s*([\d,]+\.?\d{2})',
                        r'7\s*%[^|]*\|\s+([\d,]+\.?\d{2})',  # 7%...| 231.00 (space หลัง |)
                        r'7\s*%[^|]*\|\s*([\d,]+\.?\d{2})',
                        r'([\d,]+\.?\d{2})\s*(?:บาท|Baht)?\s*(?:VAT|ภาษี)',
                    ]
                    # ลองหาใน text เดิมก่อน
                    for pattern in flexible_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            vat_str = match.group(1).replace(',', '').replace(' ', '')
                            logger.info(f"🔍 Flexible VAT Pattern matched (ใน text เดิม): '{pattern}' -> matched text: '{match.group(0)}' -> vat_str: '{vat_str}'")
                            try:
                                vat = float(vat_str)
                                if vat > 0:
                                    result['vat_amount'] = vat
                                    logger.info(f"✅ พบยอดภาษี (flexible pattern ใน text เดิม): {result['vat_amount']}")
                                    break
                            except ValueError:
                                continue
                    
                    # ถ้ายังไม่พบ ให้ลองหาใน text_clean
                    if not result['vat_amount']:
                        for pattern in flexible_patterns:
                            match = re.search(pattern, text_clean, re.IGNORECASE)
                            if match:
                                vat_str = match.group(1).replace(',', '').replace(' ', '')
                                logger.info(f"🔍 Flexible VAT Pattern matched (ใน text_clean): '{pattern}' -> matched text: '{match.group(0)}' -> vat_str: '{vat_str}'")
                                try:
                                    vat = float(vat_str)
                                    if vat > 0:
                                        result['vat_amount'] = vat
                                        logger.info(f"✅ พบยอดภาษี (flexible pattern ใน text_clean): {result['vat_amount']}")
                                        break
                                except ValueError:
                                    continue
            
            # Pattern 3: Total | 3,531.00 หรือ (Total | 3,531.00) หรือ (จำนวนเงินรวม/Grand Total 1,337.50)
            # ใช้ pattern ที่ยืดหยุ่นกว่า โดยไม่ต้องระบุ space หลัง | อย่างชัดเจน
            patterns_total = [
                r'Total\s+\|\s*([\d,]+\.?\d{2})',  # Total | 3,531.00
                r'Total\s*\|\s*([\d,]+\.?\d{2})',  # Total | 3,531.00
                r'Total\s*\|\s*\(?([\d,]+\.?\d{2})\)?',
                r'\(Total\s*\|\s*([\d,]+\.?\d{2})\)',
                r'จำนวนเงินรวม\s*[:/]?\s*Grand\s*Total\s*\(?([\d,]+\.?\d{2})\)?',
                r'Grand\s*Total\s*\(?([\d,]+\.?\d{2})\)?',
                r'ยอดหลังบวกภาษีมูลค่าเพิ่ม\s*[:.]?\s*\(?([\d,]+\.?\d{2})\)?',
                r'หลังบวกภาษีมูลค่าเพิ่ม\s*[:.]?\s*\(?([\d,]+\.?\d{2})\)?',
                r'ยอดรวม\s*[:.]?\s*\(?([\d,]+\.?\d{2})\)?',
            ]
            
            # ลองหาใน text เดิมก่อน (ไม่ใช่ text_clean) เพราะ text_clean อาจเปลี่ยนข้อความ
            logger.info(f"🔍 ลองหา Total ใน text เดิม...")
            for idx, pattern in enumerate(patterns_total):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    total_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.info(f"🔍 Total Pattern {idx+1} matched (ใน text เดิม): '{pattern}' -> matched text: '{match.group(0)}' -> total_str: '{total_str}'")
                    try:
                        total = float(total_str)
                        if total > 0:
                            result['total_amount'] = total
                            logger.info(f"✅ พบยอดรวม (ใน text เดิม): {result['total_amount']} (pattern: {pattern})")
                            break
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{total_str}', Error: {e}")
                        continue
                else:
                    logger.debug(f"🔍 Total Pattern {idx+1} ไม่ match (ใน text เดิม): '{pattern}'")
            
            # ถ้ายังไม่พบ ให้ลองหาใน text_clean
            if not result['total_amount']:
                logger.info(f"🔍 ลองหา Total ใน text_clean...")
                for idx, pattern in enumerate(patterns_total):
                    match = re.search(pattern, text_clean, re.IGNORECASE)
                    if match:
                        total_str = match.group(1).replace(',', '').replace(' ', '')
                        logger.info(f"🔍 Total Pattern {idx+1} matched (ใน text_clean): '{pattern}' -> matched text: '{match.group(0)}' -> total_str: '{total_str}'")
                        try:
                            total = float(total_str)
                            if total > 0:
                                result['total_amount'] = total
                                logger.info(f"✅ พบยอดรวม (ใน text_clean): {result['total_amount']} (pattern: {pattern})")
                                break
                        except ValueError as e:
                            logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{total_str}', Error: {e}")
                            continue
                    else:
                        logger.debug(f"🔍 Total Pattern {idx+1} ไม่ match (ใน text_clean): '{pattern}'")
            
            if not result['total_amount']:
                logger.warning(f"⚠️ ไม่พบยอดรวม - ลองหาด้วยวิธีอื่น...")
                # ลองหาคำว่า Total หรือ รวม ใน text
                if 'TOTAL' in text_clean.upper() or 'รวม' in text_clean:
                    logger.info(f"🔍 พบคำว่า Total หรือ รวม ใน text")
                    # ลองหา pattern ที่ยืดหยุ่นกว่า - รองรับทั้ง | และ HTML table format
                    flexible_patterns = [
                        # HTML table format: <td>Total</td><td>3,531.00</td>
                        r'<td>\s*Total\s*</td>\s*<td>\s*([\d,]+\.?\d{2})\s*</td>',
                        r'Total[^<]*</td>\s*<td>\s*([\d,]+\.?\d{2})\s*</td>',
                        # Pipe format: Total | 3,531.00
                        r'TOTAL[^|]*\|\s+([\d,]+\.?\d{2})',  # TOTAL...| 3,531.00 (space หลัง |)
                        r'TOTAL[^|]*\|\s*([\d,]+\.?\d{2})',
                        r'รวม[^:]*[:]\s*([\d,]+\.?\d{2})',
                        r'([\d,]+\.?\d{2})\s*(?:บาท|Baht)?\s*(?:TOTAL|รวม)',
                    ]
                    # ลองหาใน text เดิมก่อน
                    for pattern in flexible_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            total_str = match.group(1).replace(',', '').replace(' ', '')
                            logger.info(f"🔍 Flexible Total Pattern matched (ใน text เดิม): '{pattern}' -> matched text: '{match.group(0)}' -> total_str: '{total_str}'")
                            try:
                                total = float(total_str)
                                if total > 0:
                                    result['total_amount'] = total
                                    logger.info(f"✅ พบยอดรวม (flexible pattern ใน text เดิม): {result['total_amount']}")
                                    break
                            except ValueError:
                                continue
                    
                    # ถ้ายังไม่พบ ให้ลองหาใน text_clean
                    if not result['total_amount']:
                        for pattern in flexible_patterns:
                            match = re.search(pattern, text_clean, re.IGNORECASE)
                            if match:
                                total_str = match.group(1).replace(',', '').replace(' ', '')
                                logger.info(f"🔍 Flexible Total Pattern matched (ใน text_clean): '{pattern}' -> matched text: '{match.group(0)}' -> total_str: '{total_str}'")
                                try:
                                    total = float(total_str)
                                    if total > 0:
                                        result['total_amount'] = total
                                        logger.info(f"✅ พบยอดรวม (flexible pattern ใน text_clean): {result['total_amount']}")
                                        break
                                except ValueError:
                                    continue
            
            # ถ้ายังไม่มี total_amount ให้คำนวณจาก amount_before_vat + vat_amount
            if result['total_amount'] is None:
                if result['amount_before_vat'] and result['vat_amount']:
                    result['total_amount'] = result['amount_before_vat'] + result['vat_amount']
                    logger.info(f"✅ คำนวณยอดรวม: {result['total_amount']} = {result['amount_before_vat']} + {result['vat_amount']}")
            
            # Log สรุปผลลัพธ์
            logger.info(f"📊 ผลลัพธ์การดึงข้อมูล (WHT 3%):")
            logger.info(f"   ยอดก่อนภาษี: {result['amount_before_vat']}")
            logger.info(f"   ยอดภาษี: {result['vat_amount']}")
            logger.info(f"   ยอดรวม: {result['total_amount']}")
            
            return result
        
        # กรณีไม่มี WHT 3% - ใช้รูปแบบเดิม
        # ลองดึงข้อมูลจากตาราง HTML ก่อน
        table_data = self._extract_from_html_table(text)
        if table_data:
            if table_data.get('amount_before_vat'):
                result['amount_before_vat'] = table_data['amount_before_vat']
            if table_data.get('vat_amount') is not None:
                result['vat_amount'] = table_data['vat_amount']
            if table_data.get('total_amount'):
                result['total_amount'] = table_data['total_amount']
            
            if result['amount_before_vat'] and result['total_amount']:
                return result
        
        # Fallback: ลองหาจาก pattern matching
        # Pattern: AMOUNT column ในตาราง
        pattern_amount = r'AMOUNT[^|]*\|\s*([\d,]+\.?\d{2})'
        match = re.search(pattern_amount, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                result['amount_before_vat'] = amount
                result['vat_amount'] = 0.0
                result['total_amount'] = amount
                return result
            except ValueError:
                pass
        
        return result
    
    def extract_reference(self, text: str) -> Optional[str]:
        """ดึงอ้างอิง (BL เท่านั้น) - รูปแบบ: B/L : MEDUYQ420646"""
        logger.info("🔍 [EXCLUSIVE Reference] เริ่มค้นหา BL...")
        
        # ===== หา BL (รองรับหลายรูปแบบ) =====
        bl_patterns = [
            r'BL\s*[:.]?\s*([A-Z0-9\-]+)',  # BL: MEDUYQ420646
            r'B/L\s*[:.]?\s*([A-Z0-9\-]+)',  # B/L: MEDUYQ420646
            r'BL\s*NO\s*[:.]?\s*([A-Z0-9\-]+)',  # BL NO: MEDUYQ420646
            r'BILL\s*OF\s*LADING\s*[:.]?\s*([A-Z0-9\-]+)',  # BILL OF LADING: MEDUYQ420646
        ]
        
        for idx, pattern in enumerate(bl_patterns):
            logger.info(f"🔍 [EXCLUSIVE Reference] ทดสอบ pattern #{idx+1}: {pattern}")
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bl = match.group(1).strip()
                matched_text = match.group(0)
                logger.info(f"  ✅ Pattern #{idx+1} MATCH!")
                logger.info(f"     Matched text: '{matched_text}'")
                logger.info(f"     BL: '{bl}'")
                # เพิ่ม "B/L : " นำหน้าค่า BL
                reference = f"B/L : {bl}"
                logger.info(f"✅ พบ BL (จาก pattern #{idx+1}): {bl}")
                logger.info(f"✅ Reference ที่จะ return: {reference}")
                return reference
            else:
                logger.info(f"  ❌ Pattern #{idx+1} ไม่ match")
        
        logger.info("🔍 [EXCLUSIVE Reference] ไม่พบ BL")
        return None
    
    def extract_remark(self, text: str) -> Optional[str]:
        """ดึงหมายเหตุ (INV NO เท่านั้น - ไม่รวม BL แล้ว)"""
        logger.info("🔍 [EXCLUSIVE Remark] เริ่มค้นหา INV NO...")
        
        # ===== หา INV NO (รองรับหลายรูปแบบ) =====
        inv_no_patterns = [
            r'INV\s*NO\s*[:.]?\s*([A-Z0-9\-]+)',  # INV NO: TGBU9334880
            r'INVOICE\s*NO\s*[:.]?\s*([A-Z0-9\-]+)',  # INVOICE NO: TGBU9334880
            r'INV\.\s*NO\s*[:.]?\s*([A-Z0-9\-]+)',  # INV. NO: TGBU9334880
            r'INVOICE\s*[:.]?\s*([A-Z0-9\-]+)',  # INVOICE: TGBU9334880
        ]
        
        for idx, pattern in enumerate(inv_no_patterns):
            logger.info(f"🔍 [EXCLUSIVE Remark] ทดสอบ pattern #{idx+1}: {pattern}")
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                inv_no = match.group(1).strip()
                matched_text = match.group(0)
                logger.info(f"  ✅ Pattern #{idx+1} MATCH!")
                logger.info(f"     Matched text: '{matched_text}'")
                logger.info(f"     INV NO: '{inv_no}'")
                logger.info(f"✅ พบ INV NO (จาก pattern #{idx+1}): {inv_no}")
                return f"INV NO: {inv_no}"
            else:
                logger.info(f"  ❌ Pattern #{idx+1} ไม่ match")
        
        logger.info("🔍 [EXCLUSIVE Remark] ไม่พบ INV NO")
        return None
    
    def parse_html_table(self, text: str) -> Dict[str, str]:
        """
        Parse ข้อมูลจากตาราง HTML
        หา pattern เช่น: <tr><td>NO</td><td>202511-008</td></tr>
        หรือ: NO | 202511-008 (text format)
        
        Returns:
            Dictionary ที่มี key-value จากตาราง
        """
        result = {}
        
        # Pattern สำหรับหา <tr>...</tr> ที่มีหลาย <td>
        tr_pattern = r'<tr[^>]*>(.*?)</tr>'
        tr_matches = re.findall(tr_pattern, text, re.IGNORECASE | re.DOTALL)
        
        for tr_content in tr_matches:
            # หา <td> ทั้งหมดในแถว
            td_pattern = r'<td[^>]*>([^<]+(?:<[^>]+>)*[^<]*)</td>'
            td_matches = re.findall(td_pattern, tr_content, re.IGNORECASE | re.DOTALL)
            
            if len(td_matches) >= 2:
                # key อยู่ที่ td แรก
                key = re.sub(r'<[^>]+>', '', td_matches[0]).strip()
                
                # value อยู่ที่ td สุดท้ายที่มีข้อมูล
                value = None
                for td in reversed(td_matches):
                    td_clean = re.sub(r'<[^>]+>', '', td).strip()
                    if td_clean and td_clean not in ['-', '']:
                        value = td_clean
                        break
                
                if key and value:
                    # ทำความสะอาด key (ลบ whitespace)
                    key_clean = re.sub(r'\s+', '', key)
                    result[key_clean] = value
                    logger.info(f"✅ Parse HTML table row: {key_clean} = {value[:100]}...")
        
        # Fallback: ลองหาแบบ text format (| separated)
        lines = text.split('\n')
        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    key = parts[0].strip()
                    for part in reversed(parts):
                        if part.strip() and part.strip() not in ['-', '']:
                            value = part.strip()
                            break
                    else:
                        continue
                    
                    key_clean = re.sub(r'\s+', '', key)
                    if key_clean and value:
                        result[key_clean] = value
                        logger.info(f"✅ Parse text table: {key_clean} = {value[:100]}...")
        
        return result
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """
        ดึงเลขที่เอกสาร
        
        รูปแบบ: NO: 202511-008, EXC2511-008, EXC-2511-008 หรือรูปแบบอื่นๆ
        """
        logger.info("🔍 [EXCLUSIVE Document Number] เริ่มค้นหาเลขที่เอกสาร...")
        logger.info(f"🔍 [EXCLUSIVE Document Number] ตัวอย่าง text (500 ตัวอักษรแรก): {text[:500].replace(chr(10), '\\n')}...")
        
        # ลองหาจาก HTML table ก่อน
        logger.info("🔍 [EXCLUSIVE Document Number] กำลังค้นหาจาก HTML table...")
        table_data = self.parse_html_table(text)
        logger.info(f"🔍 [EXCLUSIVE Document Number] พบข้อมูลใน table: {len(table_data)} รายการ")
        if table_data:
            logger.info(f"🔍 [EXCLUSIVE Document Number] Keys ใน table: {', '.join(table_data.keys())}")
        
        for key in table_data.keys():
            logger.info(f"🔍 [EXCLUSIVE Document Number] ตรวจสอบ key: {key}")
            if 'NO' in key.upper() or 'INVOICE' in key.upper() or 'DOCUMENT' in key.upper():
                doc_num = table_data[key].strip()
                logger.info(f"🔍 [EXCLUSIVE Document Number] พบ key ที่เกี่ยวข้อง: {key} = {doc_num}")
                # ตรวจสอบว่าไม่ใช่ "AMOUNT" หรือคำอื่นๆ ที่ไม่ใช่เลขที่เอกสาร
                if doc_num.upper() in ['AMOUNT', 'TOTAL', 'VAT', 'TAX', 'DATE', 'INVOICE']:
                    logger.warning(f"⚠️ [EXCLUSIVE Document Number] ข้ามค่า '{doc_num}' เพราะไม่ใช่เลขที่เอกสาร")
                    continue
                # หาเฉพาะตัวเลขและตัวอักษร (รองรับทั้ง XXXXXX-XXX และรูปแบบอื่นๆ)
                match = re.search(r'([A-Z0-9\-]+)', doc_num)
                if match:
                    doc_num = match.group(1).strip()
                    # ตรวจสอบอีกครั้งว่าไม่ใช่ "AMOUNT"
                    if doc_num.upper() not in ['AMOUNT', 'TOTAL', 'VAT', 'TAX', 'DATE', 'INVOICE']:
                        logger.info(f"✅ พบเลขที่เอกสารจาก HTML table (key: {key}): {doc_num}")
                        return doc_num
                    else:
                        logger.warning(f"⚠️ [EXCLUSIVE Document Number] ข้ามค่า '{doc_num}' เพราะไม่ใช่เลขที่เอกสาร")
        
        # อ่านทีละบรรทัดเพื่อหา NO หรือ EXC
        lines = text.split('\n')
        logger.info(f"🔍 [EXCLUSIVE Document Number] กำลังค้นหา 'NO' หรือ 'EXC' ใน {len(lines)} บรรทัด...")
        for idx, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # ตรวจสอบว่ามี "NO" หรือ "EXC" ในบรรทัดนี้หรือไม่
            if ('NO' in line_clean.upper() and ':' in line_clean) or 'EXC' in line_clean.upper():
                logger.info(f"🔍 [EXCLUSIVE Document Number] บรรทัด {idx+1} พบ 'NO' หรือ 'EXC': {line_clean[:150]}...")
        
        # Pattern: รองรับทั้ง NO: 202511-008, EXC2511-008, EXC-2511-008
        patterns = [
            # Pattern 1: EXC2511-008 หรือ EXC-2511-008 (รูปแบบ EXC) - เพิ่ม pattern นี้ก่อน
            # ต้อง capture ทั้ง EXC และตัวเลข (ไม่ตัด EXC ออก)
            r'(EXC\s*\d{4}[-]\d{3})',  # EXC2511-008 (ไม่มีช่องว่าง)
            r'(EXC[-]\d{4}[-]\d{3})',  # EXC-2511-008 (มีขีดระหว่าง EXC กับตัวเลข)
            r'(EXC\s+[-]?\s*\d{4}[-]\d{3})',  # EXC 2511-008 หรือ EXC -2511-008 (มีช่องว่าง)
            # Pattern 2: NO: 202511-008 (รูปแบบเดิม)
            r'NO\s*[:]\s*([A-Z0-9\-]+)',  # NO: 202511-008
            r'NO\s*[:.]?\s*([A-Z0-9\-]+)',  # NO. 202511-008 หรือ NO: 202511-008
            # Pattern 3: เลขที่: 202511-008
            r'เลขที่\s*[:.]?\s*([A-Z0-9\-]+)',  # เลขที่: 202511-008
            # Pattern 4: Invoice No.: XXX
            r'Invoice\s+No\.\s*[:.]?\s*([A-Z0-9\-]+)',  # Invoice No.: XXX
            r'INVOICE\s+NO\.\s*[:.]?\s*([A-Z0-9\-]+)',  # INVOICE NO.: XXX
        ]
        
        logger.info(f"🔍 [EXCLUSIVE Document Number] กำลังทดสอบ {len(patterns)} patterns...")
        for idx, pattern in enumerate(patterns):
            logger.info(f"🔍 [EXCLUSIVE Document Number] ทดสอบ pattern #{idx+1}: {pattern}")
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                matched_text = match.group(0)
                logger.info(f"  ✅ Pattern #{idx+1} MATCH!")
                logger.info(f"     Matched text: '{matched_text}'")
                logger.info(f"     Document number: '{doc_num}'")
                # ทำความสะอาด: ลบช่องว่างที่เหลือ (สำหรับกรณี EXC 2511-008)
                doc_num = re.sub(r'\s+', '', doc_num)  # ลบช่องว่างทั้งหมด
                logger.info(f"     Document number (cleaned): '{doc_num}'")
                # ตรวจสอบว่าไม่ใช่ "AMOUNT" หรือคำอื่นๆ ที่ไม่ใช่เลขที่เอกสาร
                if doc_num.upper() in ['AMOUNT', 'TOTAL', 'VAT', 'TAX', 'DATE', 'INVOICE']:
                    logger.warning(f"  ⚠️ Pattern #{idx+1} match แต่ค่า '{doc_num}' ไม่ใช่เลขที่เอกสาร - ข้าม")
                    continue
                logger.info(f"✅ พบเลขที่เอกสาร (จาก pattern #{idx+1}): {doc_num}")
                return doc_num
            else:
                logger.info(f"  ❌ Pattern #{idx+1} ไม่ match")
        
        logger.warning("⚠️ ไม่พบเลขที่เอกสาร")
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจจับประเภทเอกสาร
        
        ถ้ามี WHT 3% ให้ return 1 (มีภาษีมูลค่าเพิ่ม) - เพราะถ้ามี WHT 3% แสดงว่าต้องมี VAT
        ถ้าไม่มี WHT 3% ให้ return 2 (ไม่มีภาษีมูลค่าเพิ่ม)
        
        Returns:
            1 = เอกสารมีภาษีมูลค่าเพิ่ม (VAT)
            2 = เอกสารไม่มีภาษีมูลค่าเพิ่ม (NoneVat)
        """
        # ตรวจสอบว่ามี WHT 3% หรือไม่
        if self.has_wht_3_percent(text):
            # ถ้ามี WHT 3% ให้ return 1 (มีภาษีมูลค่าเพิ่ม) - เพราะถ้ามี WHT 3% แสดงว่าต้องมี VAT
            logger.info("✅ พบ WHT 3% → กำหนด document_type = 1 (มีภาษีมูลค่าเพิ่ม)")
            return 1  # มีภาษีมูลค่าเพิ่ม
        
        return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร Exclusive Global Logistics
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร Exclusive Global Logistics หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร Exclusive Global Logistics'
            }
        
        # หาส่วนต้นฉบับของใบกำกับภาษีก่อน
        original_section = self.extract_original_invoice_section(text)
        if original_section:
            # ใช้เฉพาะส่วนต้นฉบับในการดึงข้อมูล
            text = original_section
            logger.info("✅ ใช้เฉพาะส่วนต้นฉบับของใบกำกับภาษีในการดึงข้อมูล")
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text)
        logger.info(f"🔍 [EXCLUSIVE Extract All Data] document_number ที่ดึงได้: {document_number}")
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text)
        reference = self.extract_reference(text)  # เพิ่มการดึง reference (BL)
        logger.info(f"🔍 [EXCLUSIVE Extract All Data] reference ที่ดึงได้: {reference}")
        logger.info(f"🔍 [EXCLUSIVE Extract All Data] remark ที่ดึงได้: {remark}")
        document_type = self.detect_document_type(text, amounts, withholding)
        
        return {
            'success': True,
            'company': 'EXCLUSIVE',
            'company_name': company_name,
            'tax_id': tax_id,
            'date': date,
            'document_number': document_number,  # เลขที่เอกสาร
            'address': address,
            'account_name': account_info['account_name'],
            'account_code': account_info['account_code'],
            'withholding_tax_percent': withholding['withholding_tax_percent'],
            'withholding_tax_amount': withholding['withholding_tax_amount'],
            'amount_before_vat': amounts['amount_before_vat'],
            'vat_amount': amounts['vat_amount'],
            'total_amount': amounts['total_amount'],
            'remark': remark,  # INV NO เท่านั้น (ไม่รวม BL แล้ว)
            'reference': reference,  # BL เท่านั้น
            'new_filename': filename,  # ใช้ชื่อไฟล์เดิม
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,  # 2 = ไม่มีภาษีมูลค่าเพิ่ม
        }
