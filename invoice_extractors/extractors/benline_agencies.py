"""
Benline Agencies (Thailand) Invoice Extractor
=============================================
Extractor สำหรับดึงข้อมูลจาก BENLINE AGENCIES (THAILAND) LTD.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class BenlineAgenciesExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก BENLINE AGENCIES (THAILAND) LTD."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "BENLINE AGENCIES (THAILAND) LTD.",
        "BEN LINE AGENCIES (THAILAND) LTD.",  # รองรับรูปแบบที่มี space
        "BEN LINE,AGENCIES (THAILAND) LTD.",  # รองรับรูปแบบที่มี comma (OCR error)
        "BENLINE AGENCIES (THAILAND)",
        "BEN LINE AGENCIES (THAILAND)",  # รองรับรูปแบบที่มี space
        "BEN LINE,AGENCIES (THAILAND)",  # รองรับรูปแบบที่มี comma (OCR error)
        "BENLINE AGENCIES",
        "BEN LINE AGENCIES",  # รองรับรูปแบบที่มี space
        "BEN LINE,AGENCIES",  # รองรับรูปแบบที่มี comma (OCR error)
        "BENLINE"
    ]
    
    # Tax ID (normalized: 0 1055 17012 89 1 -> 0105517012891)
    TAX_ID = "0105517012891"
    
    def __init__(self):
        """Initialize Benline Agencies Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ BENLINE AGENCIES (THAILAND) LTD. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "BENLINE AGENCIES (THAILAND) LTD."
        2. Tax ID "0 1055 17012 89 1" หรือ "0105517012891"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Benline Agencies (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        # ตรวจสอบทั้งรูปแบบปกติและรูปแบบที่มี comma (OCR error)
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # ถ้ายังไม่เจอ ลองตรวจสอบแบบยืดหยุ่น (รองรับ comma และ space)
        if not has_company:
            # Pattern: BEN LINE,AGENCIES หรือ BENLINE AGENCIES
            company_patterns = [
                r'BEN\s*LINE[,]?\s*AGENCIES',
                r'BENLINE\s*AGENCIES',
            ]
            for pattern in company_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    has_company = True
                    logger.info(f"✅ พบชื่อบริษัท (flexible pattern): {pattern}")
                    break
        
        # เงื่อนไข 2: ต้องมี Tax ID (รองรับทั้งรูปแบบที่มี space, -, และรูปแบบที่ติดกัน)
        has_tax_id = (
            "0 1055 17012 89 1" in text or
            "0-1055 17012 89 1" in text or  # รองรับรูปแบบที่มี - ระหว่าง 0 และ 1055
            "0-1055-17012-89-1" in text or
            "0105517012891" in text or
            ("Tax ID" in text or "TAX_ID" in text or "TAX ID" in text) and "1055" in text and "17012" in text
        )
        
        # Debug logging
        if not has_tax_id:
            logger.debug(f"🔍 [is_company_document] ไม่พบ Tax ID ใน text")
            logger.debug(f"   - '0 1055 17012 89 1' in text: {'0 1055 17012 89 1' in text}")
            logger.debug(f"   - 'TAX_ID' in text: {'TAX_ID' in text}")
            logger.debug(f"   - 'TAX ID' in text: {'TAX ID' in text}")
            logger.debug(f"   - '1055' in text: {'1055' in text}")
            logger.debug(f"   - '17012' in text: {'17012' in text}")
        
        # เงื่อนไข 3: ต้องมีเอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        has_document_type = (
            "ใบเสร็จรับเงิน" in text or 
            "ใบกำกับภาษี" in text or 
            "RECEIPT" in text.upper() or 
            "TAX INVOICE" in text.upper()
        )
        
        # ต้องมีทั้ง 3 เงื่อนไขถึงจะผ่าน
        result = has_company and has_tax_id and has_document_type
        
        # Debug logging
        logger.debug(f"🔍 [is_company_document] ผลการตรวจสอบ:")
        logger.debug(f"   - has_company: {has_company}")
        logger.debug(f"   - has_tax_id: {has_tax_id}")
        logger.debug(f"   - has_document_type: {has_document_type}")
        logger.debug(f"   - result: {result}")
        
        return result
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "BENLINE AGENCIES (THAILAND) LTD."
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TAX ID 0 1055 17012 89 1 หรือ TAX_ID 0-1055 17012 89 1
        # ต้องแปลงเป็น 0105517012891 (เอา space และ - ออก)
        patterns = [
            r'TAX[_\s]+ID\s*[:.]?\s*0\s*-\s*1055\s+17012\s+89\s+1',  # TAX_ID 0-1055 17012 89 1 หรือ TAX ID 0-1055 17012 89 1
            r'Tax\s+ID\s*[:.]?\s*0\s+1055\s+17012\s+89\s+1',  # Tax ID: 0 1055 17012 89 1
            r'Tax\s+ID\s*[:.]?\s*0\s*-\s*1055\s*-\s*17012\s*-\s*89\s*-\s*1',  # Tax ID: 0-1055-17012-89-1
            r'0\s*-\s*1055\s+17012\s+89\s+1',  # 0-1055 17012 89 1
            r'0\s+1055\s+17012\s+89\s+1',  # 0 1055 17012 89 1
            r'0\s*-\s*1055\s*-\s*17012\s*-\s*89\s*-\s*1',  # 0-1055-17012-89-1
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # แปลงเป็น 0105517012891 (เอา space และ - ออก)
                tax_id = self.TAX_ID
                logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษี: {tax_id}")
                return tax_id
        
        # Fallback: ถ้าไม่พบ ให้ใช้ default
        logger.warning("⚠️ ไม่พบเลขประจำตัวผู้เสียภาษี ใช้ค่า default")
        return self.TAX_ID
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: DATE. : 04/11/2025
        patterns = [
            r'DATE\.\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DATE. : 04/11/2025
            r'DATE\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DATE : 04/11/2025
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # วันที่: 04/11/2025
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                date_str = f"{day}/{month}/{year}"
                logger.info(f"✅ พบวันที่: {date_str}")
                return date_str
        
        return None
    
    def extract_document_number(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: RECEIPT NO. : BV0037365
        patterns = [
            r'RECEIPT\s+NO\.\s*[:.]?\s*([A-Z0-9]{8,})',  # RECEIPT NO. : BV0037365
            r'Receipt\s+No\.\s*[:.]?\s*([A-Z0-9]{8,})',  # Receipt No. : BV0037365
            r'เลขที่\s*[:.]?\s*([A-Z0-9]{8,})',  # เลขที่: BV0037365
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                if len(doc_num) >= 8:
                    logger.info(f"✅ พบเลขที่เอกสาร: {doc_num}")
                    return doc_num
        
        return None
    
    def parse_html_table(self, text: str) -> Dict[str, str]:
        """
        Parse HTML table และ text format (| separated) เพื่อดึงข้อมูล
        รองรับทั้ง HTML table และ text format ที่มี | คั่น
        อ่านข้อมูลทีละบรรทัดแบบ HTML
        """
        result = {}
        
        logger.info("🔍 [Parse HTML Table] เริ่ม parse ตาราง...")
        
        # วิธีที่ 1: Parse HTML table structure
        table_pattern = r'<table[^>]*>(.*?)</table>'
        tables = re.findall(table_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if tables:
            logger.info(f"🔍 [HTML Table] พบ {len(tables)} ตาราง")
            
            for table_idx, table_html in enumerate(tables):
                # แยก rows
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
                
                logger.info(f"🔍 [HTML Table] ตาราง {table_idx+1}: พบ {len(rows)} แถว")
                
                for idx, tr_content in enumerate(rows):
                    # แยก cells
                    td_pattern = r'<td[^>]*>(.*?)</td>'
                    td_matches = re.findall(td_pattern, tr_content, re.IGNORECASE | re.DOTALL)
                    
                    if len(td_matches) >= 2:
                        # ทำความสะอาด <td> content (ลบ HTML tags แต่เก็บข้อความ)
                        td_cleaned = []
                        for td in td_matches:
                            # แทนที่ <br/> และ <br> ด้วย space
                            td_text = re.sub(r'<br\s*/?>', ' ', td, flags=re.IGNORECASE)
                            # ลบ HTML tags อื่นๆ
                            td_text = re.sub(r'<[^>]+>', '', td_text)
                            # ทำความสะอาด whitespace
                            td_text = re.sub(r'\s+', ' ', td_text).strip()
                            td_cleaned.append(td_text)
                        
                        logger.info(f"🔍 [HTML Table] แถว {idx+1} หลังทำความสะอาด: {td_cleaned}")
                        
                        # key อยู่ที่ td แรก
                        key = td_cleaned[0]
                        
                        # value อยู่ที่ td สุดท้าย (หรือ td ที่มีตัวเลข)
                        value = None
                        for td in td_cleaned[1:]:
                            # ตรวจสอบว่าเป็นตัวเลข (ยอดเงิน)
                            if re.match(r'^[\d,]+\.?\d*$', td.replace(',', '')):
                                value = td
                                break
                        
                        # ถ้าไม่พบตัวเลข ให้ใช้ td สุดท้าย
                        if value is None and len(td_cleaned) > 1:
                            value = td_cleaned[-1]
                        
                        # ทำความสะอาด key (ลบ whitespace)
                        key_clean = re.sub(r'\s+', '', key)
                        
                        if key_clean and value:
                            result[key_clean] = value
                            logger.info(f"✅ [HTML Table] Parse HTML table: {key_clean} = {value}")
        
        # วิธีที่ 2: Parse text format (| separated) - อ่านทีละบรรทัด
        # Pattern: No. | B/L # | INVOICE # | DESCRIPTION | CURR | AMOUNT
        #          1 | NOSNB25LB78258 | IBV0041631 | DOCUMENTATION FEE .. | XIN MING ZHOU | THB 1,500.00
        lines = text.split('\n')
        
        bl_column_index = -1  # เก็บ index ของ column B/L #
        
        for line_idx, line in enumerate(lines):
            line_stripped = line.strip()
            
            # ตรวจสอบว่าเป็นรูปแบบตารางที่มี | คั่น
            if '|' in line_stripped:
                parts = [part.strip() for part in line_stripped.split('|')]
                
                if len(parts) >= 2:
                    # ตรวจสอบว่าเป็น header row (มี "B/L #" หรือ "B/L NO" หรือ "INVOICE #")
                    line_upper = ' '.join(parts).upper()
                    if any(keyword in line_upper for keyword in ['B/L', 'BL', 'INVOICE', 'NO.', 'DESCRIPTION', 'AMOUNT']):
                        logger.info(f"🔍 [Text Table] พบ header row ที่บรรทัด {line_idx+1}: {line_stripped[:100]}...")
                        
                        # หา column index ของ B/L #
                        for col_idx, part in enumerate(parts):
                            part_upper = part.upper()
                            if 'B/L' in part_upper or 'BL' in part_upper:
                                bl_column_index = col_idx
                                logger.info(f"✅ [Text Table] พบ B/L # column ที่ index: {bl_column_index}")
                                break
                        continue
                    
                    # ถ้าเป็น data row (มีตัวเลขในส่วนแรก เช่น "1", "2", "3")
                    if parts[0].isdigit() and len(parts) > 1:
                        # ถ้าเรารู้ column index ของ B/L # แล้ว ให้อ่านจาก column นั้น
                        if bl_column_index >= 0 and bl_column_index < len(parts):
                            bl_number = parts[bl_column_index].strip()
                            # ตรวจสอบว่า B/L number มีความยาวอย่างน้อย 8 ตัวอักษรและไม่ใช่ตัวเลขล้วน
                            if bl_number and len(bl_number) >= 8 and not bl_number.isdigit():
                                # ตรวจสอบว่าไม่ใช่คำอื่นๆ เช่น "XIN MING ZHOU"
                                if re.match(r'^[A-Z0-9]{8,}$', bl_number):
                                    result['BL#'] = bl_number
                                    logger.info(f"✅ [Text Table] Parse text table: BL# = {bl_number} (บรรทัด {line_idx+1})")
                        # ถ้ายังไม่รู้ column index ให้ลองอ่านจาก column ที่ 2 (index 1)
                        elif len(parts) >= 2:
                            bl_number = parts[1].strip()
                            # ตรวจสอบว่า B/L number มีความยาวอย่างน้อย 8 ตัวอักษรและไม่ใช่ตัวเลขล้วน
                            if bl_number and len(bl_number) >= 8 and not bl_number.isdigit():
                                # ตรวจสอบว่าเป็นรูปแบบ B/L number (ตัวอักษรและตัวเลข)
                                if re.match(r'^[A-Z0-9]{8,}$', bl_number):
                                    result['BL#'] = bl_number
                                    logger.info(f"✅ [Text Table] Parse text table: BL# = {bl_number} (บรรทัด {line_idx+1}, fallback)")
        
        # วิธีที่ 3: Parse key-value pairs (เช่น SUB TOTAL : 2,100.00)
        # Pattern: SUB TOTAL : 2,100.00
        #          VAT 7% : 147.00
        #          NET TOTAL : 2,247.00
        # อ่านทีละบรรทัด
        for line_idx, line in enumerate(lines):
            line_stripped = line.strip()
            
            # ตรวจสอบว่าเป็น key-value pair (มี : และตัวเลข)
            if ':' in line_stripped:
                # Pattern: SUB TOTAL : 2,100.00
                key_value_match = re.match(r'^([^:]+):\s*([\d,]+\.?\d*)', line_stripped, re.IGNORECASE)
                if key_value_match:
                    key = key_value_match.group(1).strip()
                    value = key_value_match.group(2).strip()
                    
                    # ทำความสะอาด key (ลบ whitespace)
                    key_clean = re.sub(r'\s+', '', key)
                    
                    # ตรวจสอบว่าเป็น key ที่เราต้องการ
                    if 'SUBTOTAL' in key_clean.upper() or ('SUB' in key_clean.upper() and 'TOTAL' in key_clean.upper()):
                        result['SUBTOTAL'] = value
                        logger.info(f"✅ [Text Table] Parse key-value: SUBTOTAL = {value} (บรรทัด {line_idx+1})")
                    elif 'VAT' in key_clean.upper() and '7%' in line_stripped:
                        result['VAT7%'] = value
                        logger.info(f"✅ [Text Table] Parse key-value: VAT7% = {value} (บรรทัด {line_idx+1})")
                    elif 'NETTOTAL' in key_clean.upper() or ('NET' in key_clean.upper() and 'TOTAL' in key_clean.upper()):
                        result['NETTOTAL'] = value
                        logger.info(f"✅ [Text Table] Parse key-value: NETTOTAL = {value} (บรรทัด {line_idx+1})")
                    elif 'TOTAL' in key_clean.upper() and 'SUB' not in key_clean.upper() and 'NET' not in key_clean.upper():
                        result['TOTAL'] = value
                        logger.info(f"✅ [Text Table] Parse key-value: TOTAL = {value} (บรรทัด {line_idx+1})")
        
        logger.info(f"🔍 [Parse HTML Table] สรุป: พบ {len(result)} รายการ")
        for key, value in result.items():
            logger.info(f"   - {key} = {value[:100]}...")
        
        return result
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง"""
        # อ่านจากตาราง HTML: B/L # | NOSNB25LB78258
        # หรือจากชื่อไฟล์เก่า (ตัดข้อมูล VAT_, WHT_, None_vat และข้อมูลที่เริ่มต้นด้วย EXC_)
        
        # ลองหาจากตาราง HTML ก่อน
        table_data = self.parse_html_table(text)
        
        # หา BL# หรือ B/L #
        bl_key = None
        for key in table_data.keys():
            if 'BL#' in key.upper() or 'B/L#' in key.upper() or 'BL' in key.upper():
                bl_key = key
                break
        
        if bl_key:
            bl_number = table_data[bl_key].strip()
            ref = f"B/L : {bl_number}"
            logger.info(f"✅ พบอ้างอิงจากตาราง: {ref}")
            return ref
        
        # Fallback: ลองหา pattern อื่นๆ (อ่านจากตาราง HTML โดยตรง)
        # Pattern: 1 | NOSNB25LB78314 | IBV0042396 | ...
        lines = text.split('\n')
        for line in lines:
            if '|' in line:
                parts = [part.strip() for part in line.split('|')]
                # ตรวจสอบว่าเป็น data row (มีตัวเลขในส่วนแรก)
                if len(parts) >= 2 and parts[0].isdigit():
                    bl_number = parts[1].strip()
                    # ตรวจสอบว่าเป็นรูปแบบ B/L number (ตัวอักษรและตัวเลข 8 ตัวขึ้นไป)
                    if bl_number and len(bl_number) >= 8 and re.match(r'^[A-Z0-9]{8,}$', bl_number):
                        ref = f"B/L : {bl_number}"
                        logger.info(f"✅ พบอ้างอิงจากตาราง (fallback): {ref}")
                        return ref
        
        # Fallback: ลองหา pattern อื่นๆ
        patterns = [
            r'B/L\s*#\s*[:.]?\s*([A-Z0-9]{8,})',  # B/L # : NOSNB25LB78258
            r'B/L\s+NO\.\s*[:.]?\s*([A-Z0-9]{8,})',  # B/L NO. : NOSNB25LB78258
            r'BL\s*[:.]?\s*([A-Z0-9]{8,})',  # BL : NOSNB25LB78258
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bl_number = match.group(1).strip()
                # ตรวจสอบว่าเป็นรูปแบบ B/L number
                if len(bl_number) >= 8 and re.match(r'^[A-Z0-9]{8,}$', bl_number):
                    ref = f"B/L : {bl_number}"
                    logger.info(f"✅ พบอ้างอิงจาก pattern: {ref}")
                    return ref
        
        # Fallback: ลองอ่านจากชื่อไฟล์
        if filename:
            # ตัดข้อมูล VAT_, WHT_, None_vat และข้อมูลที่เริ่มต้นด้วย EXC_
            clean_filename = filename
            clean_filename = re.sub(r'VAT_', '', clean_filename, flags=re.IGNORECASE)
            clean_filename = re.sub(r'WHT_', '', clean_filename, flags=re.IGNORECASE)
            clean_filename = re.sub(r'None_vat', '', clean_filename, flags=re.IGNORECASE)
            clean_filename = re.sub(r'EXC_.*?\.pdf', '', clean_filename, flags=re.IGNORECASE)
            clean_filename = re.sub(r'\.pdf$', '', clean_filename, flags=re.IGNORECASE)
            
            # ลองหา B/L number จากชื่อไฟล์
            bl_match = re.search(r'([A-Z0-9]{8,})', clean_filename)
            if bl_match:
                bl_number = bl_match.group(1)
                ref = f"B/L : {bl_number}"
                logger.info(f"✅ พบอ้างอิงจากชื่อไฟล์: {ref}")
                return ref
        
        return None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี"""
        return {
            'account_name': 'ค่าใช้จ่ายอื่นๆในการซื้อสินค้า',
            'account_code': None
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        จาก:
        SUB TOTAL : 2,100.00
        VAT 7% : 147.00
        NET TOTAL : 2,247.00
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (2,100.00) - จาก SUB TOTAL
                'vat_amount': float,          # ยอดภาษี (147.00) - จาก VAT 7%
                'total_amount': float         # ยอดรวม (2,247.00) - จาก NET TOTAL
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        logger.info("🔍 [Extract Amounts] เริ่มดึงยอดเงิน...")
        
        # อ่านจาก HTML table
        table_data = self.parse_html_table(text)
        
        logger.info(f"🔍 [Extract Amounts] ข้อมูลจาก table: {len(table_data)} รายการ")
        for key, value in table_data.items():
            logger.info(f"   - {key} = {value}")
        
        # หายอดก่อนภาษีจาก "SUB TOTAL" หรือ "SUBTOTAL"
        subtotal_keys = ['SUBTOTAL', 'SUBTOTAL', 'SUB TOTAL', 'SUBTOTAL']
        for search_key in subtotal_keys:
            for table_key, table_value in table_data.items():
                if search_key.lower() in table_key.lower() or table_key.lower() in search_key.lower():
                    try:
                        amount_str = str(table_value).replace(',', '').replace(' ', '')
                        amount = float(amount_str)
                        if amount > 0:
                            result['amount_before_vat'] = amount
                            logger.info(f"✅ [Extract Amounts] พบยอดก่อนภาษี: {amount} (จาก key: {table_key})")
                            break
                    except (ValueError, TypeError):
                        continue
            if result['amount_before_vat'] is not None:
                break
        
        # หายอดภาษีจาก "VAT" หรือ "ภาษีมูลค่าเพิ่ม"
        vat_keys = ['VAT', 'ภาษีมูลค่าเพิ่ม', 'VAT7%', 'VAT 7%']
        for search_key in vat_keys:
            for table_key, table_value in table_data.items():
                if search_key.lower() in table_key.lower() or table_key.lower() in search_key.lower():
                    try:
                        amount_str = str(table_value).replace(',', '').replace(' ', '')
                        amount = float(amount_str)
                        if amount > 0:
                            result['vat_amount'] = amount
                            logger.info(f"✅ [Extract Amounts] พบยอดภาษี: {amount} (จาก key: {table_key})")
                            break
                    except (ValueError, TypeError):
                        continue
            if result['vat_amount'] is not None:
                break
        
        # หายอดรวมจาก "NET TOTAL" หรือ "TOTAL"
        total_keys = ['NETTOTAL', 'NET TOTAL', 'TOTAL', 'TOTAL']
        for search_key in total_keys:
            for table_key, table_value in table_data.items():
                if search_key.lower() in table_key.lower() or table_key.lower() in search_key.lower():
                    # ตรวจสอบว่าไม่ใช่ "SUB TOTAL"
                    if 'SUB' not in table_key.upper():
                        try:
                            amount_str = str(table_value).replace(',', '').replace(' ', '')
                            amount = float(amount_str)
                            if amount > 0:
                                result['total_amount'] = amount
                                logger.info(f"✅ [Extract Amounts] พบยอดรวม: {amount} (จาก key: {table_key})")
                                break
                        except (ValueError, TypeError):
                            continue
            if result['total_amount'] is not None:
                break
        
        # Fallback: ลองหาแบบ regex pattern (อ่านจาก text โดยตรง)
        logger.info("🔍 [Extract Amounts] กำลังลองหาแบบ regex pattern...")
        
        if result['amount_before_vat'] is None:
            patterns = [
                r'SUB\s+TOTAL\s*[:.]?\s*([\d,]+\.?\d*)',  # SUB TOTAL : 2,100.00
                r'SUBTOTAL\s*[:.]?\s*([\d,]+\.?\d*)',  # SUBTOTAL : 2,100.00
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '')
                        amount = float(amount_str)
                        result['amount_before_vat'] = amount
                        logger.info(f"✅ [Extract Amounts] พบยอดก่อนภาษี (regex): {amount}")
                        break
                    except (ValueError, IndexError):
                        continue
        
        if result['vat_amount'] is None:
            patterns = [
                r'VAT\s*7%\s*[:.]?\s*([\d,]+\.?\d*)',  # VAT 7% : 147.00
                r'VAT\s*[:.]?\s*([\d,]+\.?\d*)',  # VAT : 147.00
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '')
                        amount = float(amount_str)
                        result['vat_amount'] = amount
                        logger.info(f"✅ [Extract Amounts] พบยอดภาษี (regex): {amount}")
                        break
                    except (ValueError, IndexError):
                        continue
        
        if result['total_amount'] is None:
            patterns = [
                r'NET\s+TOTAL\s*[:.]?\s*([\d,]+\.?\d*)',  # NET TOTAL : 2,247.00
                r'TOTAL\s*[:.]?\s*([\d,]+\.?\d*)',  # TOTAL : 2,247.00
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '')
                        amount = float(amount_str)
                        result['total_amount'] = amount
                        logger.info(f"✅ [Extract Amounts] พบยอดรวม (regex): {amount}")
                        break
                    except (ValueError, IndexError):
                        continue
        
        return result
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        # กำหนดให้เป็น 3%
        return {
            'withholding_tax_percent': 3.0,
            'withholding_tax_amount': None
        }
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ"""
        # อ่านจากชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_
        if filename:
            if filename.upper().startswith('EXC_'):
                # ตัด "EXC_" และ ".pdf" ออก
                remark = filename.replace('EXC_', '', 1)
                remark = re.sub(r'\.pdf$', '', remark, flags=re.IGNORECASE)
                logger.info(f"✅ พบหมายเหตุจากชื่อไฟล์: {remark}")
                return remark
        
        return None
    
    def extract_address(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงที่อยู่"""
        # กำหนดให้เป็นที่อยู่ตามที่ระบุ
        full_address = "366/32 AIYARA VILLAGE, PHETKASEM 81, LIAP KHLONG PHASI CHAROEN FANG NUEA ROAD, NONG KHAEM SUBDISTRICT, NONG KHAEM DISTRICT, BANGKOK, THAILAND 10160"
        
        return {
            'full_address': full_address,
            'address_number': "366/32",
            'address_other': "VILLAGE, PHETKASEM 81",
            'street': "LIAP KHLONG PHASI CHAROEN FANG NUEA ROAD",
            'soi': None,
            'subdistrict': "NONG KHAEM SUBDISTRICT",
            'district': "NONG KHAEM DISTRICT",
            'province': "BANGKOK",
            'postal_code': "10160"
        }
    
    def detect_document_type(self, text: str) -> int:
        """ตรวจสอบประเภทเอกสาร"""
        # มีภาษีมูลค่าเพิ่ม (VAT 7%)
        return 1  # With VAT
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """ดึงข้อมูลทั้งหมด"""
        logger.info("=" * 100)
        logger.info("BENLINE AGENCIES (THAILAND) LTD. - เริ่มดึงข้อมูล...")
        logger.info("=" * 100)
        
        # ดึงข้อมูลพื้นฐาน
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        branch = self.extract_branch(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text, filename)
        reference = self.extract_reference(text, filename)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding_tax = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        address = self.extract_address(text)
        document_type = self.detect_document_type(text)
        
        # สร้างชื่อไฟล์ใหม่ (ตัดข้อมูล VAT_, WHT_, None_vat)
        new_filename = None
        if filename:
            new_filename = filename
            new_filename = re.sub(r'VAT_', '', new_filename, flags=re.IGNORECASE)
            new_filename = re.sub(r'WHT_', '', new_filename, flags=re.IGNORECASE)
            new_filename = re.sub(r'None_vat', '', new_filename, flags=re.IGNORECASE)
            new_filename = re.sub(r'\.pdf$', '', new_filename, flags=re.IGNORECASE)
        
        # แยกที่อยู่เป็นส่วนๆ
        address_full = address.get('full_address', '') if isinstance(address, dict) else (address or '')
        building_number = address.get('address_number', '') if isinstance(address, dict) else ''
        other_info = address.get('address_other', '') if isinstance(address, dict) else ''
        soi = address.get('soi', '') if isinstance(address, dict) else ''
        road = address.get('street', '') if isinstance(address, dict) else ''
        subdistrict = address.get('subdistrict', '') if isinstance(address, dict) else ''
        district = address.get('district', '') if isinstance(address, dict) else ''
        province = address.get('province', '') if isinstance(address, dict) else ''
        postal_code = address.get('postal_code', '') if isinstance(address, dict) else ''
        
        result = {
            'success': True,
            'company': 'BENLINE_AGENCIES',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'reference': reference,
            'address': address_full,
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
            'amount_before_vat': amounts.get('amount_before_vat') or 0,
            'vat_amount': amounts.get('vat_amount') or 0,
            'total_amount': amounts.get('total_amount') or 0,
            'withholding_tax_percent': withholding_tax.get('withholding_tax_percent'),
            'withholding_tax_amount': withholding_tax.get('withholding_tax_amount'),
            'remark': remark,
            'new_filename': new_filename,
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,
            'skip_amount_adjustment': False  # มี VAT ต้องให้ manager validate
        }
        
        logger.info("=" * 100)
        logger.info("✅ อ่านข้อมูลสำเร็จ: BENLINE AGENCIES (THAILAND) LTD.")
        logger.info("=" * 100)
        
        return result

