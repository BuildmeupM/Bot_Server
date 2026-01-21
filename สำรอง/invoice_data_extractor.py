"""
Invoice Data Extractor
=====================
ระบบดึงข้อมูลจากใบแจ้งหนี้ของบริษัทต่างๆ
และจัดรูปแบบสำหรับส่งไปยัง Excel

รองรับบริษัท:
- MSC Mediterranean Shipping Company S.A.
- (เพิ่มบริษัทอื่นๆ ได้ในอนาคต)

Author: BotV3
Version: 2.0.0
"""

import re
from datetime import datetime
from typing import Dict, Optional, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# ===== Base Extractor Class =====
class BaseInvoiceExtractor:
    """Base class สำหรับ Extractor ทั้งหมด"""
    
    def __init__(self):
        """Initialize Base Extractor"""
        self.company_identifiers = []
    
    def is_company_document(self, text: str) -> bool:
        """ตรวจสอบว่าเป็นเอกสารของบริษัทนี้หรือไม่"""
        raise NotImplementedError
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """ดึงข้อมูลทั้งหมดจากเอกสาร"""
        raise NotImplementedError


# ===== MSC Extractor =====
class MSCInvoiceExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก MSC Mediterranean Shipping Company"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "MSC Mediterranean Shipping Company",
        "Mediterranean Shipping (Thailand)"
    ]
    
    def __init__(self):
        """Initialize MSC Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ MSC หรือไม่
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร MSC
        """
        if not text:
            return False
        
        text_upper = text.upper()
        for identifier in self.COMPANY_IDENTIFIERS:
            if identifier.upper() in text_upper:
                return True
        return False
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท MSC"""
        lines = text.split('\n')
        for line in lines:
            if 'MSC Mediterranean Shipping Company' in line:
                company_name = line.strip()
                if 'S.A.' not in company_name:
                    company_name = 'MSC Mediterranean Shipping Company S.A.'
                return company_name
        
        return 'MSC Mediterranean Shipping Company S.A.'
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern 1: TaxID 9930000036677
        pattern1 = r'TaxID\s*[:.]?\s*(\d{13})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            tax_id = match.group(1)
            if tax_id.startswith('99'):
                tax_id = '0' + tax_id[1:]
            return tax_id
        
        # Pattern 2: Tax ID No. 9930000036677
        pattern2 = r'Tax\s+ID\s+No[.:]?\s*(\d{13})'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            tax_id = match.group(1)
            if tax_id.startswith('99'):
                tax_id = '0' + tax_id[1:]
            return tax_id
        
        # Pattern 3: เลขที่มีจุลภาค
        pattern3 = r'TaxID\s*[:.]?\s*([\d,]{15,})'
        match = re.search(pattern3, text, re.IGNORECASE)
        if match:
            tax_id = match.group(1).replace(',', '')
            if len(tax_id) == 13 and tax_id.startswith('99'):
                tax_id = '0' + tax_id[1:]
                return tax_id
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        pattern = r'Date\s*[/:]?\s*วันที่\s*[:.]?\s*(\d{1,2})-([A-Z]{3})-(\d{4})'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            day = match.group(1).zfill(2)
            month_abbr = match.group(2).upper()
            year = match.group(3)
            
            month_map = {
                'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
            }
            
            month = month_map.get(month_abbr, '01')
            return f"{day}/{month}/{year}"
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท (ที่อยู่รวม)
        
        Returns:
            ที่อยู่บริษัท (string) หรือ None
        """
        lines = text.split('\n')
        address_lines = []
        collecting = False
        
        # หาตำแหน่งที่เริ่มต้นที่อยู่ (มักจะอยู่หลังชื่อบริษัท)
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # หา "Head Office:" หรือ "Address:" หรือ "ที่อยู่"
            if any(keyword in line_clean for keyword in ['Head Office:', 'Address:', 'ที่อยู่:', 'Address']):
                collecting = True
                # เก็บบรรทัดนี้ด้วย (ถ้ามีข้อมูล)
                if ':' in line_clean:
                    addr_part = line_clean.split(':', 1)[1].strip()
                    if addr_part:
                        address_lines.append(addr_part)
                continue
            
            # ถ้ากำลังเก็บข้อมูลที่อยู่
            if collecting:
                # หยุดเมื่อเจอ TaxID, Tax ID, Date, หรือ No.
                if any(keyword in line_clean for keyword in ['TaxID', 'Tax ID', 'Date', 'No.', 'TAX INVOICE']):
                    break
                
                # เก็บบรรทัดที่มีข้อมูล (ไม่ใช่บรรทัดว่าง)
                if line_clean and len(line_clean) > 5:
                    address_lines.append(line_clean)
        
        # รวมที่อยู่ทั้งหมด
        if address_lines:
            address = ' '.join(address_lines).strip()
            # ทำความสะอาด: ลบ space หลายตัว
            address = re.sub(r'\s+', ' ', address)
            return address if len(address) > 10 else None
        
        return None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """
        ดึงข้อมูลบัญชี (Account Name / Account Code)
        
        Returns:
            {'account_name': str, 'account_code': str}
        """
        # สำหรับ MSC ยังไม่มีข้อมูลบัญชีในเอกสาร
        # ต้องดึงจาก Chart of Accounts
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลหัก ณ ที่จ่าย
        
        Returns:
            {
                'withholding_tax_percent': float,  # เปอร์เซ็นต์
                'withholding_tax_amount': float    # จำนวนเงิน
            }
        """
        result = {
            'withholding_tax_percent': 0.0,
            'withholding_tax_amount': 0.0
        }
        
        # Pattern: หัก ณ ที่จ่าย 3% หรือ Withholding Tax 3%
        pattern_percent = r'(?:หัก\s*ณ\s*ที่จ่าย|Withholding\s*Tax)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*%'
        match = re.search(pattern_percent, text, re.IGNORECASE)
        if match:
            result['withholding_tax_percent'] = float(match.group(1))
        
        # Pattern: จำนวนเงินหัก ณ ที่จ่าย
        pattern_amount = r'(?:หัก\s*ณ\s*ที่จ่าย|Withholding\s*Tax)\s*(?:Amount)?\s*[:=]?\s*([\d,]+\.?\d*)'
        match = re.search(pattern_amount, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                result['withholding_tax_amount'] = float(amount_str)
            except ValueError:
                pass
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
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
        
        # สำหรับ MSC: Non-Taxable Amount (ไม่มีภาษี)
        # Pattern: Non-Taxable Amount / ไม่มีภาษีมูลค่าเพิ่ม 6,000.00
        pattern_non_vat = r'Non-Taxable Amount\s*[/:]?\s*ไม่มีภาษีมูลค่าเพิ่ม\s*([\d,]+\.?\d*)'
        match = re.search(pattern_non_vat, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                result['amount_before_vat'] = float(amount_str)
                result['vat_amount'] = 0.0  # ไม่มีภาษี
            except ValueError:
                pass
        
        # Total / รวม
        pattern_total = r'Total\s*[/:]?\s*รวม\s*([\d,]+\.?\d*)'
        match = re.search(pattern_total, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                result['total_amount'] = float(amount_str)
            except ValueError:
                pass
        
        return result
    
    def extract_document_number(self, filename: str) -> Optional[str]:
        """ดึงเลขที่เอกสารจากชื่อไฟล์"""
        name_without_ext = filename.replace('.pdf', '').replace('.PDF', '')
        parts = name_without_ext.split('_')
        return parts[0] if parts else name_without_ext
    
    def extract_invoice_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่ใบแจ้งหนี้"""
        pattern = r'No\.\s*(\d{10,})'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def extract_bl_number(self, text: str) -> Optional[str]:
        """ดึงเลข BL (Bill of Lading)"""
        # Pattern: BL(s) : MEDUW0265381
        pattern = r'BL\(s\)\s*[:]\s*([A-Z0-9]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Pattern 2: BL: MEDUW0265381
        pattern2 = r'BL\s*[:]\s*([A-Z0-9]+)'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจจับประเภทเอกสาร
        
        Args:
            text: ข้อความ
            amounts: ยอดเงิน
            withholding: ข้อมูลหัก ณ ที่จ่าย
        
        Returns:
            1 = เอกสารมีภาษีมูลค่าเพิ่ม
            2 = เอกสารไม่มีภาษีมูลค่าเพิ่ม
        """
        # ตรวจสอบว่ามี VAT หรือไม่
        vat_amount = amounts.get('vat_amount') or 0
        has_vat = vat_amount > 0
        
        # ใช้แค่ 2 ประเภท: มีภาษี (1) หรือไม่มีภาษี (2)
        if has_vat:
            return 1  # มีภาษีมูลค่าเพิ่ม
        else:
            return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร MSC
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร MSC หรือไม่
        is_msc = self.is_company_document(text)
        
        if not is_msc:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร MSC'
            }
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        date = self.extract_date(text)
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        document_number = self.extract_document_number(filename)
        invoice_number = self.extract_invoice_number(text)
        bl_number = self.extract_bl_number(text)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # หมายเหตุ: BL + document_number (ถ้ามี BL) หรือ document_number อย่างเดียว
        if bl_number:
            remark = f"{bl_number} {document_number}" if document_number else bl_number
        else:
            remark = document_number
        
        return {
            'success': True,
            'company': 'MSC',
            'company_name': company_name,
            'tax_id': tax_id,
            'date': date,
            'address': address,
            'account_name': account_info['account_name'],
            'account_code': account_info['account_code'],
            'withholding_tax_percent': withholding['withholding_tax_percent'],
            'withholding_tax_amount': withholding['withholding_tax_amount'],
            'amount_before_vat': amounts['amount_before_vat'],
            'vat_amount': amounts['vat_amount'],
            'total_amount': amounts['total_amount'],
            'remark': remark,
            'new_filename': f"{invoice_number}.pdf" if invoice_number else None,
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,  # 1-4
            'bl_number': bl_number
        }


# ===== Exclusive Global Logistics Extractor =====
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
        # Pattern: TaxID 0245567001001 หรือ Tax ID No. 0245567001001
        pattern1 = r'TaxID\s*[:.]?\s*(\d{13})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        pattern2 = r'Tax\s+ID\s+No[.:]?\s*(\d{13})'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # ถ้าไม่พบ pattern ให้ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่
        if "0245567001001" in text:
            return "0245567001001"
        
        return None
    
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
    
    def extract_remark(self, text: str) -> Optional[str]:
        """ดึงหมายเหตุ (INV NO และ BL)"""
        # รองรับหลายรูปแบบ:
        # - "INV NO: TGBU9334880 BL: MEDUYQ420646"
        # - "BL: MEDUYQ420646 INV NO: TGBU9334880"
        # - "INV NO: TGBU9334880\nBL: MEDUYQ420646" (ต่างบรรทัด)
        # - "BL: MEDUYQ420646\nINV NO: TGBU9334880" (ต่างบรรทัด)
        # - "INVOICE NO", "INV.NO", "BL NO", "B/L" ฯลฯ
        
        inv_no = None
        bl = None
        
        # ===== หา INV NO (รองรับหลายรูปแบบ) =====
        inv_no_patterns = [
            r'INV\s*NO\s*[:.]?\s*([A-Z0-9\-]+)',  # INV NO: TGBU9334880
            r'INVOICE\s*NO\s*[:.]?\s*([A-Z0-9\-]+)',  # INVOICE NO: TGBU9334880
            r'INV\.\s*NO\s*[:.]?\s*([A-Z0-9\-]+)',  # INV. NO: TGBU9334880
            r'INVOICE\s*[:.]?\s*([A-Z0-9\-]+)',  # INVOICE: TGBU9334880
        ]
        
        for pattern in inv_no_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                inv_no = match.group(1).strip()
                break
        
        # ===== หา BL (รองรับหลายรูปแบบ) =====
        bl_patterns = [
            r'BL\s*[:.]?\s*([A-Z0-9\-]+)',  # BL: MEDUYQ420646
            r'B/L\s*[:.]?\s*([A-Z0-9\-]+)',  # B/L: MEDUYQ420646
            r'BL\s*NO\s*[:.]?\s*([A-Z0-9\-]+)',  # BL NO: MEDUYQ420646
            r'BILL\s*OF\s*LADING\s*[:.]?\s*([A-Z0-9\-]+)',  # BILL OF LADING: MEDUYQ420646
        ]
        
        for pattern in bl_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bl = match.group(1).strip()
                break
        
        # ===== รวมผลลัพธ์ =====
        if inv_no and bl:
            return f"INV NO: {inv_no} BL: {bl}"
        elif inv_no:
            return f"INV NO: {inv_no}"
        elif bl:
            return f"BL: {bl}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """
        ดึงเลขที่เอกสาร
        
        รูปแบบ: NO: 202511-008
        ข้อมูลที่ต้องการ: 202511-008
        """
        # Pattern: NO: 202511-008
        patterns = [
            r'NO\s*[:]\s*(\d{6}-\d{3})',  # NO: 202511-008
            r'NO\s*[:.]?\s*(\d{6}-\d{3})',  # NO. 202511-008 หรือ NO: 202511-008
            r'เลขที่\s*[:.]?\s*(\d{6}-\d{3})',  # เลขที่: 202511-008
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                # ตรวจสอบรูปแบบที่ถูกต้อง (ต้องมีรูปแบบ XXXXXX-XXX)
                if re.match(r'^\d{6}-\d{3}$', doc_num):
                    return doc_num
        
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
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text)
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text)
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
            'remark': remark,
            'new_filename': filename,  # ใช้ชื่อไฟล์เดิม
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,  # 2 = ไม่มีภาษีมูลค่าเพิ่ม
        }


# ===== MST (Mediterranean Shipping Thailand) Extractor =====
class MSTInvoiceExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก Mediterranean Shipping (Thailand) Co., Ltd."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "Mediterranean Shipping (Thailand)",
        "Mediterranean Shipping Co., Ltd."
    ]
    
    def __init__(self):
        """Initialize MST Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ MST หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "Mediterranean Shipping (Thailand) Co., Ltd."
        2. Tax ID "0105544019079"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร MST (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมี "Mediterranean Shipping (Thailand) Co., Ltd."
        has_company = "Mediterranean Shipping (Thailand) Co., Ltd." in text
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105544019079"
        has_tax_id = "0105544019079" in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท MST"""
        # หาบรรทัดที่มี Mediterranean Shipping (Thailand)
        lines = text.split('\n')
        for line in lines:
            if 'Mediterranean Shipping (Thailand)' in line:
                # Clean up
                company_name = line.strip()
                # ถ้าไม่มี Co., Ltd. ให้เพิ่ม
                if 'Co., Ltd.' not in company_name:
                    company_name = 'Mediterranean Shipping (Thailand) Co., Ltd.'
                return company_name
        
        return 'Mediterranean Shipping (Thailand) Co., Ltd.'
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TaxID 0105544019079
        pattern1 = r'TaxID\s*[:.]?\s*(\d{13})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Pattern 2: Tax ID No. 0105544019079
        pattern2 = r'Tax\s+ID\s+No[.:]?\s*(\d{13})'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: Date / วันที่ 15-OCT-2025 Branch No : 00000
        pattern = r'Date\s*[/:]?\s*วันที่\s*[:.]?\s*(\d{1,2})-([A-Z]{3})-(\d{4})'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            day = match.group(1).zfill(2)
            month_abbr = match.group(2).upper()
            year = match.group(3)
            
            month_map = {
                'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
            }
            
            month = month_map.get(month_abbr, '01')
            return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสารจาก No. 2510104513"""
        # Pattern: No. 2510104513
        pattern = r'No\.\s*(\d+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        Returns:
            ที่อยู่บริษัท (string) หรือ None
        """
        lines = text.split('\n')
        address_lines = []
        collecting = False
        
        # หาตำแหน่งที่เริ่มต้นที่อยู่ (มักจะอยู่หลังชื่อบริษัท)
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # หา "Head Office:" หรือ "Address:" หรือ "ที่อยู่" หรือ "Branch No"
            if any(keyword in line_clean for keyword in ['Head Office:', 'Address:', 'ที่อยู่:', 'Address', 'Branch No']):
                collecting = True
                # เก็บบรรทัดนี้ด้วย (ถ้ามีข้อมูล)
                if ':' in line_clean:
                    addr_part = line_clean.split(':', 1)[1].strip()
                    if addr_part and not addr_part.startswith('00000'):  # ไม่เก็บ Branch No
                        address_lines.append(addr_part)
                continue
            
            # ถ้ากำลังเก็บข้อมูลที่อยู่
            if collecting:
                # หยุดเมื่อเจอ TaxID, Tax ID, Date, หรือ No.
                if any(keyword in line_clean for keyword in ['TaxID', 'Tax ID', 'Date', 'No.', 'TAX INVOICE', 'Branch No']):
                    break
                
                # เก็บบรรทัดที่มีข้อมูล (ไม่ใช่บรรทัดว่าง)
                if line_clean and len(line_clean) > 5:
                    # ข้ามบรรทัดที่มี Branch No
                    if 'Branch No' in line_clean:
                        continue
                    address_lines.append(line_clean)
        
        # รวมที่อยู่ทั้งหมด
        if address_lines:
            address = ' '.join(address_lines).strip()
            # ทำความสะอาด: ลบ space หลายตัว
            address = re.sub(r'\s+', ' ', address)
            return address if len(address) > 10 else None
        
        return None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # สำหรับ MST ยังไม่มีข้อมูลบัญชีในเอกสาร
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': 0.0,
            'withholding_tax_amount': 0.0
        }
    
    def _extract_from_html_table(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลจากตาราง HTML โดยตรง
        
        รูปแบบตาราง:
        - Taxable Amount / ก่อนภาษีมูลค่าเพิ่ม | 1,800.00
        - Non-Taxable Amount / ไม่มีภาษีมูลค่าเพิ่ม | 1,500.00
        - 7% VAT / ภาษีมูลค่าเพิ่ม | 126.00
        - Total / รวม | 3,426.00
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            Dictionary ที่มีข้อมูลที่ดึงได้ หรือ None ถ้าไม่พบ
        """
        result = {
            'amount_before_vat': None,
            'amount_before_vat_2': None,
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
                
                # เก็บข้อมูลชั่วคราวสำหรับเลือกค่าที่ถูกต้อง
                taxable_candidates = []  # เก็บค่าที่เป็นไปได้สำหรับ Taxable Amount
                
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
                    
                    # หาตัวเลขในแถว (มักจะอยู่ cell สุดท้าย)
                    amount_str = None
                    for cell in reversed(cleaned_cells):
                        # หาตัวเลขใน cell
                        numbers = re.findall(r'([\d,]+\.?\d{2})', cell)
                        if numbers:
                            amount_str = numbers[0]
                            break
                    
                    if not amount_str:
                        continue
                    
                    try:
                        amount = float(amount_str.replace(',', '').replace(' ', ''))
                        
                        # ตรวจสอบว่าเป็นแถวไหน
                        # แถวที่ 1: ก่อนภาษีมูลค่าเพิ่ม (Taxable Amount) - ต้องไม่มีคำว่า "ยอด" ข้างหน้า
                        if ('ก่อนภาษีมูลค่าเพิ่ม' in row_text or 'Taxable Amount' in row_text) and 'ยอด' not in row_text:
                            # ตรวจสอบว่าไม่ใช่แถว header (ไม่มีตัวเลขลำดับ เช่น "1 |", "2 |")
                            # และไม่ใช่แถวรายการ (ไม่มีคำว่า "CY CHARGE", "CLEANING" ฯลฯ)
                            is_header_row = bool(re.search(r'^\d+\s*\|', row_text)) or 'Description' in row_text or 'รายละเอียด' in row_text
                            is_item_row = bool(re.search(r'(CY CHARGE|CLEANING|GENERAL)', row_text, re.IGNORECASE))
                            
                            # ถ้าเป็นแถวสรุป (ไม่ใช่ header และไม่ใช่รายการ) หรือเป็นแถวที่มี "Taxable Amount" และ "ก่อนภาษีมูลค่าเพิ่ม" พร้อมกัน
                            is_summary_row = ('Taxable Amount' in row_text and 'ก่อนภาษีมูลค่าเพิ่ม' in row_text) or \
                                            (not is_header_row and not is_item_row and 'Taxable Amount' in row_text)
                            
                            if 100 <= amount < 100000000:
                                # เก็บค่าที่เป็นไปได้ทั้งหมด
                                taxable_candidates.append({
                                    'amount': amount,
                                    'is_summary': is_summary_row,
                                    'row_text': row_text
                                })
                                logger.info(f"🔍 พบยอดก่อนภาษี (บรรทัด 1) ในตาราง HTML: {amount} (is_summary: {is_summary_row})")
                        
                        # แถวที่ 2: ไม่มีภาษีมูลค่าเพิ่ม (Non-Taxable Amount)
                        elif 'ไม่มีภาษีมูลค่าเพิ่ม' in row_text or 'Non-Taxable Amount' in row_text:
                            if 100 <= amount < 100000000:
                                result['amount_before_vat_2'] = amount
                                logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 2) ในตาราง HTML: {amount}")
                        
                        # ภาษีมูลค่าเพิ่ม (VAT) - ต้องไม่มีคำว่า "ก่อน" หรือ "ไม่มี" ข้างหน้า
                        elif ('ภาษีมูลค่าเพิ่ม' in row_text or 'VAT' in row_text) and 'ก่อน' not in row_text and 'ไม่มี' not in row_text:
                            if 0 < amount < 100000000:
                                result['vat_amount'] = amount
                                logger.info(f"✅ พบยอดภาษีในตาราง HTML: {amount}")
                        
                        # รวม (Total)
                        elif 'รวม' in row_text or 'Total' in row_text:
                            if 100 <= amount < 100000000:
                                result['total_amount'] = amount
                                logger.info(f"✅ พบยอดรวมในตาราง HTML: {amount}")
                    
                    except ValueError:
                        continue
                
                # หลังจากวนลูปทุกแถวแล้ว ให้เลือกค่าที่ถูกต้องสำหรับ Taxable Amount
                if taxable_candidates:
                    # เรียงลำดับ: แถวสรุปมาก่อน, แล้วเลือกค่าที่มากที่สุด
                    summary_rows = [c for c in taxable_candidates if c['is_summary']]
                    if summary_rows:
                        # ถ้ามีแถวสรุป ให้เลือกค่าที่มากที่สุดจากแถวสรุป
                        best_candidate = max(summary_rows, key=lambda x: x['amount'])
                        result['amount_before_vat'] = best_candidate['amount']
                        logger.info(f"✅ เลือกยอดก่อนภาษี (บรรทัด 1) จากแถวสรุป: {best_candidate['amount']}")
                    else:
                        # ถ้าไม่มีแถวสรุป ให้เลือกค่าที่มากที่สุด (เพราะยอดรวมควรจะมากกว่ายอดรายการ)
                        best_candidate = max(taxable_candidates, key=lambda x: x['amount'])
                        result['amount_before_vat'] = best_candidate['amount']
                        logger.info(f"✅ เลือกยอดก่อนภาษี (บรรทัด 1) จากค่าที่มากที่สุด: {best_candidate['amount']}")
            
            # ตรวจสอบว่าดึงข้อมูลได้หรือไม่
            if any(result.values()):
                return result
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงข้อมูลจากตาราง HTML: {e}")
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด (MST มี 2 บรรทัด)
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (บรรทัดที่ 1)
                'amount_before_vat_2': float, # ยอดก่อนภาษี (บรรทัดที่ 2 - ไม่มีภาษี)
                'vat_amount': float,          # ยอดภาษี
                'total_amount': float         # ยอดรวม
            }
        """
        result = {
            'amount_before_vat': None,
            'amount_before_vat_2': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # Log ข้อความที่ได้รับ (สำหรับ debug)
        logger.debug(f"🔍 MST extract_amounts - Text length: {len(text)}")
        logger.debug(f"🔍 MST extract_amounts - First 500 chars: {text[:500]}")
        
        # ลองดึงข้อมูลจากตาราง HTML ก่อน
        table_data = self._extract_from_html_table(text)
        if table_data:
            logger.info(f"✅ พบข้อมูลในตาราง HTML")
            if table_data.get('amount_before_vat'):
                result['amount_before_vat'] = table_data['amount_before_vat']
                logger.info(f"✅ ดึงยอดก่อนภาษี (บรรทัด 1) จากตาราง HTML: {result['amount_before_vat']}")
            if table_data.get('amount_before_vat_2'):
                result['amount_before_vat_2'] = table_data['amount_before_vat_2']
                logger.info(f"✅ ดึงยอดก่อนภาษี (บรรทัด 2) จากตาราง HTML: {result['amount_before_vat_2']}")
            if table_data.get('vat_amount'):
                result['vat_amount'] = table_data['vat_amount']
                logger.info(f"✅ ดึงยอดภาษีจากตาราง HTML: {result['vat_amount']}")
            if table_data.get('total_amount'):
                result['total_amount'] = table_data['total_amount']
                logger.info(f"✅ ดึงยอดรวมจากตาราง HTML: {result['total_amount']}")
            
            # ถ้าดึงข้อมูลครบแล้ว ให้ return
            if result['amount_before_vat'] and result['amount_before_vat_2'] and result['vat_amount'] and result['total_amount']:
                logger.info(f"✅ ดึงข้อมูลครบทุกตัวจากตาราง HTML")
                return result
        
        # ลบ newline ที่อาจแทรกอยู่ในคำ
        text_clean = re.sub(r'(\S)\s*\n\s*(\S)', r'\1\2', text)
        # ลบ space หลายตัวในคำ (เช่น "มูลค่   าเพิ่ม" -> "มูลค่าเพิ่ม")
        text_clean = re.sub(r'([ก-๙])\s+([ก-๙])', r'\1\2', text_clean)
        # เพิ่ม space ระหว่างตัวเลขกับตัวอักษร (เช่น "1,800.00Taxable" -> "1,800.00 Taxable")
        text_clean = re.sub(r'([\d,]+\.?\d*)([A-Za-zก-๙])', r'\1 \2', text_clean)
        
        logger.debug(f"🔍 Text after cleaning (first 1000 chars): {text_clean[:1000]}")
        
        # ตรวจสอบว่ามีคีย์เวิร์ดในข้อความหรือไม่
        if 'ก่อนภาษีมูลค่าเพิ่ม' in text_clean:
            logger.info(f"✅ พบ 'ก่อนภาษีมูลค่าเพิ่ม' ในข้อความ")
            # หาตำแหน่งที่พบ
            idx = text_clean.find('ก่อนภาษีมูลค่าเพิ่ม')
            logger.info(f"   ตำแหน่ง: {idx}, ข้อความรอบๆ: '{text_clean[max(0, idx-50):idx+100]}'")
        else:
            logger.warning(f"❌ ไม่พบ 'ก่อนภาษีมูลค่าเพิ่ม' ในข้อความเลย")
        
        # Pattern 1: ก่อนภาษีมูลค่าเพิ่ม (Taxable Amount)
        # วิธี: หาคีย์เวิร์ด "ก่อนภาษีมูลค่าเพิ่ม" แล้วหาตัวเลขที่อยู่หลัง | ตัวถัดไป
        # รองรับรูปแบบต่างๆ: "ก่อนภาษีมูลค่าเพิ่ม | 1,800.00", "ก่อนภาษีมูลค่าเพิ่ม | / | 1,800.00", "Taxable Amount", "ก่อนภาษี" ฯลฯ
        patterns_before_vat = [
            # รูปแบบเต็ม: ก่อนภาษีมูลค่าเพิ่ม (รองรับ space หลายตัว) - ต้องไม่มีคำว่า "ยอด" ข้างหน้า
            r'(?<!ยอด)ก่อนภาษี\s*มูลค่า\s*เพิ่ม\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # ก่อนภาษี มูลค่า เพิ่ม | / | 1,800.00
            r'(?<!ยอด)ก่อนภาษี\s*มูลค่า\s*เพิ่ม\s*\|\s*([\d,]+\.?\d*)',  # ก่อนภาษี มูลค่า เพิ่ม | 1,800.00
            r'(?<!ยอด)ก่อนภาษีมูลค่าเพิ่ม\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # ก่อนภาษีมูลค่าเพิ่ม | / | 1,800.00
            r'(?<!ยอด)ก่อนภาษีมูลค่าเพิ่ม\s*\|\s*([\d,]+\.?\d*)',  # ก่อนภาษีมูลค่าเพิ่ม | 1,800.00
            r'(?<!ยอด)ก่อนภาษีมูลค่าเพิ่ม\s*:\s*([\d,]+\.?\d*)',  # ก่อนภาษีมูลค่าเพิ่ม : 1,800.00
            r'(?<!ยอด)ก่อนภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d*)',  # ก่อนภาษีมูลค่าเพิ่ม 1,800.00
            r'(?<!ยอด)ก่อนภาษีมูลค่าเพิ่ม[^|:]*[|:]\s*([\d,]+\.?\d*)',  # ก่อนภาษีมูลค่าเพิ่ม...|...1,800.00
            r'(?<!ยอด)ก่อนภาษีมูลค่าเพิ่ม[^|]*\|\s*([\d,]+\.?\d*)',  # ก่อนภาษีมูลค่าเพิ่ม...|...1,800.00 (fallback - ต้องมี |)
            # รูปแบบย่อ: ก่อนภาษี - ต้องไม่มีคำว่า "ยอด" ข้างหน้า
            r'(?<!ยอด)ก่อนภาษี\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # ก่อนภาษี | / | 1,800.00
            r'(?<!ยอด)ก่อนภาษี\s*\|\s*([\d,]+\.?\d*)',  # ก่อนภาษี | 1,800.00
            r'(?<!ยอด)ก่อนภาษี\s*:\s*([\d,]+\.?\d*)',  # ก่อนภาษี : 1,800.00
            r'(?<!ยอด)ก่อนภาษี\s+([\d,]+\.?\d*)',  # ก่อนภาษี 1,800.00
            r'(?<!ยอด)ก่อนภาษี[^|:]*[|:]\s*([\d,]+\.?\d*)',  # ก่อนภาษี...|...1,800.00
            # รูปแบบภาษาอังกฤษ: Taxable Amount (รองรับ space หลายตัว)
            r'Taxable\s+Amount\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # Taxable Amount | / | 1,800.00
            r'Taxable\s+Amount\s*\|\s*([\d,]+\.?\d*)',  # Taxable Amount | 1,800.00
            r'Taxable\s+Amount\s*:\s*([\d,]+\.?\d*)',  # Taxable Amount : 1,800.00
            r'Taxable\s+Amount\s+([\d,]+\.?\d*)',  # Taxable Amount 1,800.00
            r'Taxable\s+Amount[^|:]*[|:]\s*([\d,]+\.?\d*)',  # Taxable Amount...|...1,800.00
            r'Taxable[^|:]*[|:]\s*([\d,]+\.?\d*)',  # Taxable...|...1,800.00
        ]
        # ถ้ายังไม่ดึงข้อมูลจากตาราง HTML ให้ใช้ pattern matching
        if not result['amount_before_vat']:
            for idx, pattern in enumerate(patterns_before_vat):
                match = re.search(pattern, text_clean, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.info(f"✅ Pattern {idx+1} matched: '{pattern}' -> '{match.group(0)}' -> amount: '{amount_str}'")
                    try:
                        amount = float(amount_str)
                        # ตรวจสอบว่าเป็นตัวเลขที่สมเหตุสมผล (มากกว่า 100 เพื่อหลีกเลี่ยงตัวเลขเล็กๆ และไม่เกิน 100 ล้าน)
                        if 100 <= amount < 100000000:
                            result['amount_before_vat'] = amount
                            logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 1): {result['amount_before_vat']}")
                            break
                        else:
                            logger.warning(f"⚠️ ตัวเลขไม่สมเหตุสมผล: {amount} (ต้องมากกว่า 100)")
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: {amount_str}, Error: {e}")
                else:
                    logger.debug(f"🔍 Pattern {idx+1} ไม่ match: '{pattern}'")
        else:
            logger.info(f"⏭️ ข้าม pattern matching สำหรับยอดก่อนภาษี (บรรทัด 1) เพราะดึงจากตาราง HTML ได้แล้ว: {result['amount_before_vat']}")
        
        # ถ้ายังไม่พบ ลองหาด้วยวิธีอื่น: หาคีย์เวิร์ดแล้วหาตัวเลขที่อยู่ใกล้ๆ
        if not result['amount_before_vat']:
            logger.warning(f"⚠️ ไม่พบยอดก่อนภาษี (บรรทัด 1) - ลองหาด้วยวิธีอื่น...")
            # ลองหาคีย์เวิร์ดหลายแบบ
            keywords = ['ก่อนภาษีมูลค่าเพิ่ม', 'ก่อนภาษี', 'Taxable Amount', 'Taxable']
            for keyword in keywords:
                keyword_pos = text_clean.find(keyword)
                if keyword_pos != -1:
                    logger.info(f"   พบคีย์เวิร์ด '{keyword}' ที่ตำแหน่ง {keyword_pos}")
                    # หาตัวเลขที่อยู่หลังคีย์เวิร์ด (ภายใน 300 ตัวอักษร)
                    search_text = text_clean[keyword_pos:keyword_pos+300]
                    logger.debug(f"   ข้อความรอบๆ: '{search_text[:150]}'")
                    
                    # วิธีที่ 1: หาตัวเลขที่อยู่หลัง | หรือ : ตัวแรกที่อยู่หลังคีย์เวิร์ด (สำคัญที่สุด)
                    # หา | หรือ : ตัวแรกที่อยู่หลังคีย์เวิร์ด (ต้องอยู่หลังคีย์เวิร์ดเท่านั้น และต้องไม่มีคำว่า "ยอด" ข้างหน้า)
                    # ใช้ pattern ที่หาคีย์เวิร์ดแล้วตามด้วย | หรือ : และตัวเลข
                    # ตรวจสอบว่าไม่มีคำว่า "ยอด" ข้างหน้า (ภายใน 20 ตัวอักษร)
                    before_text = text_clean[max(0, keyword_pos-20):keyword_pos]
                    if 'ยอด' not in before_text:
                        direct_pattern = re.compile(rf'(?<!ยอด){re.escape(keyword)}\s*[^|:]*?[|:]\s*([\d,]+\.?\d*)', re.IGNORECASE)
                        direct_match = direct_pattern.search(text_clean, keyword_pos)
                        if direct_match:
                            num_str = direct_match.group(1)
                            try:
                                amount = float(num_str.replace(',', '').replace(' ', ''))
                                if 100 <= amount < 100000000:
                                    result['amount_before_vat'] = amount
                                    logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 1) ด้วยวิธีหา | ตัวแรกหลังคีย์เวิร์ด '{keyword}': {result['amount_before_vat']}")
                                break
                            except ValueError:
                                pass
                        else:
                            logger.debug(f"   ข้ามเพราะมีคำว่า 'ยอด' ข้างหน้า '{keyword}'")
                    
                    # วิธีที่ 2: หาตัวเลขที่อยู่หลัง | หรือ : (เรียงตามตำแหน่ง) - ถ้าวิธีที่ 1 ไม่ได้
                    if not result['amount_before_vat']:
                        matches = list(re.finditer(r'[|:]\s*([\d,]+\.?\d*)', search_text))
                        if matches:
                            # เลือกตัวเลขแรกที่สมเหตุสมผล (มากกว่า 100)
                            for match in matches:
                                num_str = match.group(1)
                                try:
                                    amount = float(num_str.replace(',', '').replace(' ', ''))
                                    if 100 <= amount < 100000000:
                                        result['amount_before_vat'] = amount
                                        logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 1) ด้วยวิธีหาใกล้ๆ '{keyword}': {result['amount_before_vat']}")
                                        break
                                except ValueError:
                                    continue
                            if result['amount_before_vat']:
                                break
                    
                    # วิธีที่ 3: หาตัวเลขที่อยู่หลังคีย์เวิร์ดโดยตรง (ไม่ต้องมี | หรือ :) - ใช้เป็น fallback สุดท้าย
                    # ต้องไม่มีคำว่า "ยอด" ข้างหน้า
                    if not result['amount_before_vat']:
                        before_text = text_clean[max(0, keyword_pos-20):keyword_pos]
                        if 'ยอด' not in before_text:
                            # หาตัวเลขที่อยู่หลังคีย์เวิร์ดโดยตรง (ภายใน 50 ตัวอักษรแรก)
                            direct_match = re.search(r'(?<!ยอด)ก่อนภาษีมูลค่าเพิ่ม\s*[^|:]*?([\d,]+\.?\d{2})', search_text[:100])
                            if direct_match:
                                num_str = direct_match.group(1)
                                try:
                                    amount = float(num_str.replace(',', '').replace(' ', ''))
                                    if 100 <= amount < 100000000:
                                        result['amount_before_vat'] = amount
                                        logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 1) ด้วยวิธีหาตัวเลขหลังคีย์เวิร์ดโดยตรง '{keyword}': {result['amount_before_vat']}")
                                        break
                                except ValueError:
                                    pass
                    
                    # วิธีที่ 3: หาตัวเลขที่อยู่ก่อนคีย์เวิร์ด (ในกรณีที่ตัวเลขอยู่ข้างหน้า)
                    if not result['amount_before_vat']:
                        before_text = text_clean[max(0, keyword_pos-100):keyword_pos]
                        # หาตัวเลขที่อยู่ก่อนคีย์เวิร์ด (มากกว่า 100)
                        before_numbers = re.findall(r'([\d,]+\.?\d{2})', before_text)
                        for num_str in reversed(before_numbers):  # เริ่มจากตัวเลขที่อยู่ใกล้คีย์เวิร์ดที่สุด
                            try:
                                amount = float(num_str.replace(',', '').replace(' ', ''))
                                if 100 <= amount < 100000000:
                                    result['amount_before_vat'] = amount
                                    logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 1) ด้วยวิธีหาตัวเลขก่อนคีย์เวิร์ด '{keyword}': {result['amount_before_vat']}")
                                    break
                            except ValueError:
                                continue
                        if result['amount_before_vat']:
                            break
                    
                    # ถ้ายังไม่พบ ให้ใช้ตัวเลขแรกที่มากกว่า 0
                    if not result['amount_before_vat']:
                        matches = list(re.finditer(r'[|:]\s*([\d,]+\.?\d*)', search_text))
                        if matches:
                            for match in matches:
                                num_str = match.group(1)
                                try:
                                    amount = float(num_str.replace(',', '').replace(' ', ''))
                                    if 0 < amount < 100000000:
                                        result['amount_before_vat'] = amount
                                        logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 1) ด้วยวิธีหาใกล้ๆ (fallback) '{keyword}': {result['amount_before_vat']}")
                                        break
                                except ValueError:
                                    continue
                        if result['amount_before_vat']:
                            break
        
        # Pattern 2: ไม่มีภาษีมูลค่าเพิ่ม (Non-Taxable Amount)
        # วิธี: หาคีย์เวิร์ด "ไม่มีภาษีมูลค่าเพิ่ม" แล้วหาตัวเลขที่อยู่หลัง | ตัวถัดไป
        # รองรับรูปแบบต่างๆ: "ไม่มีภาษีมูลค่าเพิ่ม | 1,500.00", "ไม่มีภาษีมูลค่าเพิ่ม | / | 1,500.00", "Non-Taxable Amount" ฯลฯ
        patterns_non_vat = [
            # รูปแบบเต็ม: ไม่มีภาษีมูลค่าเพิ่ม
            r'ไม่มีภาษีมูลค่าเพิ่ม\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # ไม่มีภาษีมูลค่าเพิ่ม | / | 1,500.00
            r'ไม่มีภาษีมูลค่าเพิ่ม\s*\|\s*([\d,]+\.?\d*)',  # ไม่มีภาษีมูลค่าเพิ่ม | 1,500.00
            r'ไม่มีภาษีมูลค่าเพิ่ม\s*:\s*([\d,]+\.?\d*)',  # ไม่มีภาษีมูลค่าเพิ่ม : 1,500.00
            r'ไม่มีภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d*)',  # ไม่มีภาษีมูลค่าเพิ่ม 1,500.00
            r'ไม่มีภาษีมูลค่าเพิ่ม[^|:]*[|:]\s*([\d,]+\.?\d*)',  # ไม่มีภาษีมูลค่าเพิ่ม...|...1,500.00
            r'ไม่มีภาษีมูลค่าเพิ่ม.*?([\d,]+\.?\d*)',  # ไม่มีภาษีมูลค่าเพิ่ม...1,500.00 (fallback)
            # รูปแบบย่อ: ไม่มีภาษี
            r'ไม่มีภาษี\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # ไม่มีภาษี | / | 1,500.00
            r'ไม่มีภาษี\s*\|\s*([\d,]+\.?\d*)',  # ไม่มีภาษี | 1,500.00
            r'ไม่มีภาษี\s*:\s*([\d,]+\.?\d*)',  # ไม่มีภาษี : 1,500.00
            r'ไม่มีภาษี\s+([\d,]+\.?\d*)',  # ไม่มีภาษี 1,500.00
            r'ไม่มีภาษี[^|:]*[|:]\s*([\d,]+\.?\d*)',  # ไม่มีภาษี...|...1,500.00
            # รูปแบบภาษาอังกฤษ: Non-Taxable Amount
            r'Non-Taxable\s+Amount\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # Non-Taxable Amount | / | 1,500.00
            r'Non-Taxable\s+Amount\s*\|\s*([\d,]+\.?\d*)',  # Non-Taxable Amount | 1,500.00
            r'Non-Taxable\s+Amount\s*:\s*([\d,]+\.?\d*)',  # Non-Taxable Amount : 1,500.00
            r'Non-Taxable\s+Amount\s+([\d,]+\.?\d*)',  # Non-Taxable Amount 1,500.00
            r'Non-Taxable\s+Amount[^|:]*[|:]\s*([\d,]+\.?\d*)',  # Non-Taxable Amount...|...1,500.00
            r'Non[-\s]?Taxable[^|:]*[|:]\s*([\d,]+\.?\d*)',  # Non-Taxable หรือ Non Taxable
        ]
        # ถ้ายังไม่ดึงข้อมูลจากตาราง HTML ให้ใช้ pattern matching
        if not result['amount_before_vat_2']:
            for idx, pattern in enumerate(patterns_non_vat):
                match = re.search(pattern, text_clean, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.info(f"✅ Pattern {idx+1} matched: '{pattern}' -> '{match.group(0)}' -> amount: '{amount_str}'")
                    try:
                        amount = float(amount_str)
                        if 100 <= amount < 100000000:
                            result['amount_before_vat_2'] = amount
                            logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 2): {result['amount_before_vat_2']}")
                            break
                        else:
                            logger.warning(f"⚠️ ตัวเลขไม่สมเหตุสมผล: {amount} (ต้องมากกว่า 100)")
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: {amount_str}, Error: {e}")
                else:
                    logger.debug(f"🔍 Pattern {idx+1} ไม่ match: '{pattern}'")
        else:
            logger.info(f"⏭️ ข้าม pattern matching สำหรับยอดก่อนภาษี (บรรทัด 2) เพราะดึงจากตาราง HTML ได้แล้ว: {result['amount_before_vat_2']}")
        
        # ถ้ายังไม่พบ ลองหาด้วยวิธีอื่น
        if not result['amount_before_vat_2']:
            logger.warning(f"⚠️ ไม่พบยอดก่อนภาษี (บรรทัด 2) - ลองหาด้วยวิธีอื่น...")
            keyword_pos = text_clean.find('ไม่มีภาษีมูลค่าเพิ่ม')
            if keyword_pos != -1:
                search_text = text_clean[keyword_pos:keyword_pos+200]
                matches = list(re.finditer(r'\|\s*([\d,]+\.?\d*)', search_text))
                if matches:
                    # เลือกตัวเลขแรกที่สมเหตุสมผล (มากกว่า 100)
                    for match in matches:
                        num_str = match.group(1)
                        try:
                            amount = float(num_str.replace(',', '').replace(' ', ''))
                            if 100 <= amount < 100000000:
                                result['amount_before_vat_2'] = amount
                                logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 2) ด้วยวิธีหาใกล้ๆ: {result['amount_before_vat_2']}")
                            break
                        except ValueError:
                            continue
                    # ถ้ายังไม่พบ ให้ใช้ตัวเลขแรก
                    if not result['amount_before_vat_2']:
                        for match in matches:
                            num_str = match.group(1)
                            try:
                                amount = float(num_str.replace(',', '').replace(' ', ''))
                                if 0 < amount < 100000000:
                                    result['amount_before_vat_2'] = amount
                                    logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 2) ด้วยวิธีหาใกล้ๆ (fallback): {result['amount_before_vat_2']}")
                                    break
                            except ValueError:
                                continue
        
        # Pattern 3: ภาษีมูลค่าเพิ่ม (7% VAT)
        # วิธี: หาคีย์เวิร์ด "ภาษีมูลค่าเพิ่ม" แล้วหาตัวเลขที่อยู่หลัง | ตัวถัดไป
        # ต้องไม่มีคำว่า "ก่อน" หรือ "ไม่มี" ข้างหน้า
        # รองรับรูปแบบต่างๆ: "ภาษีมูลค่าเพิ่ม | 126.00", "ภาษีมูลค่าเพิ่ม | / | 126.00", "7% VAT", "VAT" ฯลฯ
        patterns_vat = [
            # รูปแบบเต็ม: ภาษีมูลค่าเพิ่ม (ต้องไม่มี "ก่อน" หรือ "ไม่มี" ข้างหน้า)
            r'(?<!ก่อน)(?<!ไม่มี)ภาษีมูลค่าเพิ่ม\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม | / | 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษีมูลค่าเพิ่ม\s*\|\s*([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม | 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษีมูลค่าเพิ่ม\s*:\s*([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม : 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษีมูลค่าเพิ่ม[^|:]*[|:]\s*([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม...|...126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษีมูลค่าเพิ่ม.*?([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม...126.00 (fallback)
            # รูปแบบย่อ: ภาษี (ต้องไม่มี "ก่อน" หรือ "ไม่มี" ข้างหน้า)
            r'(?<!ก่อน)(?<!ไม่มี)ภาษี\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # ภาษี | / | 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษี\s*\|\s*([\d,]+\.?\d*)',  # ภาษี | 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษี\s*:\s*([\d,]+\.?\d*)',  # ภาษี : 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษี\s+([\d,]+\.?\d*)',  # ภาษี 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษี[^|:]*[|:]\s*([\d,]+\.?\d*)',  # ภาษี...|...126.00
            # รูปแบบภาษาอังกฤษ: 7% VAT หรือ VAT
            r'(?:7%|7\s*%)\s*VAT\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # 7% VAT | / | 126.00
            r'(?:7%|7\s*%)\s*VAT\s*\|\s*([\d,]+\.?\d*)',  # 7% VAT | 126.00
            r'(?:7%|7\s*%)\s*VAT\s*:\s*([\d,]+\.?\d*)',  # 7% VAT : 126.00
            r'(?:7%|7\s*%)\s*VAT\s+([\d,]+\.?\d*)',  # 7% VAT 126.00
            r'VAT\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # VAT | / | 126.00 (ต้องไม่มี "ก่อน" หรือ "ไม่มี" ข้างหน้า)
            r'VAT\s*\|\s*([\d,]+\.?\d*)',  # VAT | 126.00
            r'VAT\s*:\s*([\d,]+\.?\d*)',  # VAT : 126.00
            r'VAT\s+([\d,]+\.?\d*)',  # VAT 126.00
        ]
        # ถ้ายังไม่ดึงข้อมูลจากตาราง HTML ให้ใช้ pattern matching
        if not result['vat_amount']:
            for idx, pattern in enumerate(patterns_vat):
                match = re.search(pattern, text_clean, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.info(f"✅ Pattern {idx+1} matched: '{pattern}' -> '{match.group(0)}' -> amount: '{amount_str}'")
                    try:
                        amount = float(amount_str)
                        if 0 < amount < 100000000:
                            result['vat_amount'] = amount
                            logger.info(f"✅ พบยอดภาษี: {result['vat_amount']}")
                            break
                        else:
                            logger.warning(f"⚠️ ตัวเลขไม่สมเหตุสมผล: {amount}")
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: {amount_str}, Error: {e}")
                else:
                    logger.debug(f"🔍 Pattern {idx+1} ไม่ match: '{pattern}'")
        else:
            logger.info(f"⏭️ ข้าม pattern matching สำหรับยอดภาษี เพราะดึงจากตาราง HTML ได้แล้ว: {result['vat_amount']}")
        
        # ถ้ายังไม่พบ ลองหาด้วยวิธีอื่น (ต้องไม่มีคำว่า "ก่อน" หรือ "ไม่มี" ข้างหน้า)
        if not result['vat_amount']:
            logger.warning(f"⚠️ ไม่พบยอดภาษี - ลองหาด้วยวิธีอื่น...")
            # หาทุกตำแหน่งของ "ภาษีมูลค่าเพิ่ม" ที่ไม่มี "ก่อน" หรือ "ไม่มี" ข้างหน้า
            for match in re.finditer(r'ภาษีมูลค่าเพิ่ม', text_clean, re.IGNORECASE):
                start_pos = match.start()
                # ตรวจสอบว่าไม่มี "ก่อน" หรือ "ไม่มี" ข้างหน้า (ภายใน 20 ตัวอักษร)
                before_text = text_clean[max(0, start_pos-20):start_pos]
                if 'ก่อน' not in before_text and 'ไม่มี' not in before_text:
                    search_text = text_clean[start_pos:start_pos+200]
                    numbers = re.findall(r'\|\s*([\d,]+\.?\d*)', search_text)
                    if numbers:
                        for num_str in numbers:
                            try:
                                amount = float(num_str.replace(',', '').replace(' ', ''))
                                if 0 < amount < 100000000:
                                    result['vat_amount'] = amount
                                    logger.info(f"✅ พบยอดภาษีด้วยวิธีหาใกล้ๆ: {result['vat_amount']}")
                                break
                            except ValueError:
                                continue
                    if result['vat_amount']:
                        break
        
        # Pattern 4: รวม (Total)
        # วิธี: หาคีย์เวิร์ด "รวม" แล้วหาตัวเลขที่อยู่หลัง | ตัวถัดไป
        # รองรับรูปแบบต่างๆ: "รวม | 3,426.00", "รวม | / | 3,426.00", "Total" ฯลฯ
        patterns_total = [
            # รูปแบบภาษาไทย: รวม
            r'รวม\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # รวม | / | 3,426.00
            r'รวม\s*\|\s*([\d,]+\.?\d*)',  # รวม | 3,426.00
            r'รวม\s*:\s*([\d,]+\.?\d*)',  # รวม : 3,426.00
            r'รวม\s+([\d,]+\.?\d*)',  # รวม 3,426.00
            r'รวม[^|:]*[|:]\s*([\d,]+\.?\d*)',  # รวม...|...3,426.00
            r'รวม.*?([\d,]+\.?\d*)',  # รวม...3,426.00 (fallback)
            # รูปแบบภาษาอังกฤษ: Total
            r'Total\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # Total | / | 3,426.00
            r'Total\s*\|\s*([\d,]+\.?\d*)',  # Total | 3,426.00
            r'Total\s*:\s*([\d,]+\.?\d*)',  # Total : 3,426.00
            r'Total\s+([\d,]+\.?\d*)',  # Total 3,426.00
            r'Total[^|:]*[|:]\s*([\d,]+\.?\d*)',  # Total...|...3,426.00
            r'Total.*?([\d,]+\.?\d*)',  # Total...3,426.00 (fallback)
        ]
        # ถ้ายังไม่ดึงข้อมูลจากตาราง HTML ให้ใช้ pattern matching
        if not result['total_amount']:
            for idx, pattern in enumerate(patterns_total):
                match = re.search(pattern, text_clean, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.info(f"✅ Pattern {idx+1} matched: '{pattern}' -> '{match.group(0)}' -> amount: '{amount_str}'")
                    try:
                        amount = float(amount_str)
                        if 0 < amount < 100000000:
                            result['total_amount'] = amount
                            logger.info(f"✅ พบยอดรวม: {result['total_amount']}")
                            break
                        else:
                            logger.warning(f"⚠️ ตัวเลขไม่สมเหตุสมผล: {amount}")
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: {amount_str}, Error: {e}")
                else:
                    logger.debug(f"🔍 Pattern {idx+1} ไม่ match: '{pattern}'")
        else:
            logger.info(f"⏭️ ข้าม pattern matching สำหรับยอดรวม เพราะดึงจากตาราง HTML ได้แล้ว: {result['total_amount']}")
        
        # ถ้ายังไม่พบ ลองหาด้วยวิธีอื่น
        if not result['total_amount']:
            logger.warning(f"⚠️ ไม่พบยอดรวม - ลองหาด้วยวิธีอื่น...")
            keyword_pos = text_clean.find('รวม')
            if keyword_pos != -1:
                search_text = text_clean[keyword_pos:keyword_pos+200]
                numbers = re.findall(r'\|\s*([\d,]+\.?\d*)', search_text)
                if numbers:
                    for num_str in numbers:
                        try:
                            amount = float(num_str.replace(',', '').replace(' ', ''))
                            if 0 < amount < 100000000:
                                result['total_amount'] = amount
                                logger.info(f"✅ พบยอดรวมด้วยวิธีหาใกล้ๆ: {result['total_amount']}")
                            break
                        except ValueError:
                            continue
        
        # Log สรุปผลลัพธ์
        logger.info(f"📊 MST extract_amounts Results:")
        logger.info(f"   amount_before_vat (Line 1): {result['amount_before_vat']}")
        logger.info(f"   amount_before_vat_2 (Line 2): {result['amount_before_vat_2']}")
        logger.info(f"   vat_amount: {result['vat_amount']}")
        logger.info(f"   total_amount: {result['total_amount']}")
        
        return result
    
    def extract_bl_number(self, text: str) -> Optional[str]:
        """ดึงเลข BL (Bill of Lading)"""
        # Pattern: BL(s) : MEDUW0265381
        pattern = r'BL\(s\)\s*[:]\s*([A-Z0-9]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Pattern 2: BL: MEDUW0265381
        pattern2 = r'BL\s*[:]\s*([A-Z0-9]+)'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจจับประเภทเอกสาร
        
        Returns:
            1 = เอกสารมีภาษีมูลค่าเพิ่ม
            2 = เอกสารไม่มีภาษีมูลค่าเพิ่ม
        """
        # MST: มีทั้งยอดมี VAT และไม่มี VAT
        vat_amount = amounts.get('vat_amount') or 0
        has_vat = vat_amount > 0
        
        # ใช้แค่ 2 ประเภท: มีภาษี (1) หรือไม่มีภาษี (2)
        if has_vat:
            return 1  # มีภาษีมูลค่าเพิ่ม
        else:
            return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร MST
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร MST หรือไม่
        is_mst = self.is_company_document(text)
        
        if not is_mst:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร Mediterranean Shipping (Thailand)'
            }
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        date = self.extract_date(text)
        address = self.extract_address(text)
        document_number = self.extract_document_number(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        
        # Log ข้อมูลที่ดึงได้
        logger.info(f"📊 MST Extractor Results:")
        logger.info(f"   Company: {company_name}")
        logger.info(f"   Tax ID: {tax_id}")
        logger.info(f"   Date: {date}")
        logger.info(f"   Address: {address}")
        logger.info(f"   Document Number: {document_number}")
        logger.info(f"   Amount Line 1: {amounts.get('amount_before_vat')}")
        logger.info(f"   Amount Line 2: {amounts.get('amount_before_vat_2')}")
        logger.info(f"   VAT: {amounts.get('vat_amount')}")
        logger.info(f"   Total: {amounts.get('total_amount')}")
        
        withholding = self.extract_withholding_tax(text)
        bl_number = self.extract_bl_number(text)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # คำนวณยอดรวมก่อนภาษี (รวม 2 บรรทัด)
        line1_amount = amounts.get('amount_before_vat') or 0
        line2_amount = amounts.get('amount_before_vat_2') or 0
        vat_amount = amounts.get('vat_amount') or 0
        
        total_before_vat = line1_amount + line2_amount
        
        # คำนวณยอดรวมทั้งหมด (ก่อนภาษี + ภาษี)
        # ใช้ total_amount จากที่อ่านได้ หรือคำนวณเอง
        total_amount = amounts.get('total_amount')
        if not total_amount:
            # ถ้าไม่มี ให้คำนวณเอง: ยอดก่อนภาษีทั้งหมด + ภาษี
            total_amount = total_before_vat + vat_amount
        
        # หมายเหตุ: BL + ชื่อไฟล์เก่า
        remark = f"{bl_number} {filename}" if bl_number else filename
        
        return {
            'success': True,
            'company': 'MST',
            'company_name': company_name,
            'tax_id': tax_id,
            'date': date,
            'address': address,
            'document_number': document_number,
            'account_name': account_info['account_name'],
            'account_code': account_info['account_code'],
            'withholding_tax_percent': withholding['withholding_tax_percent'],
            'withholding_tax_amount': withholding['withholding_tax_amount'],
            'amount_before_vat': total_before_vat,  # รวมทั้ง 2 บรรทัด
            'vat_amount': vat_amount,
            'total_amount': total_amount,  # ยอดรวมทั้งหมด (คำนวณแล้ว)
            'remark': remark,
            'new_filename': filename,  # ใช้ชื่อเดิม
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,
            # ข้อมูลเพิ่มเติมสำหรับ MST (สำหรับสร้าง 2 แถว)
            'bl_number': bl_number,
            'amount_before_vat_line1': line1_amount,  # บรรทัดที่ 1
            'amount_before_vat_line2': line2_amount   # บรรทัดที่ 2 (ไม่มีภาษี)
        }


# ===== Customs Department (กรมศุลกากร) Extractor =====
class CustomsDepartmentExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก กรมศุลกากร"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "กรมศุลกากร",
        "Customs Department"
    ]
    
    def __init__(self):
        """Initialize Customs Department Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของกรมศุลกากรหรือไม่
        
        เงื่อนไขที่ 1: ไม่มีภาษีมูลค่าเพิ่ม
        - ต้องมี "กรมศุลกากร" และ "ค่าธรรมเนียมการผ่านพิธีการศุลกากร"
        
        เงื่อนไขที่ 2: มีภาษีมูลค่าเพิ่ม
        - ต้องมี "กรมศุลกากร" และ "ภาษีมูลค่าเพิ่ม"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสารกรมศุลกากร
        """
        if not text:
            return False
        
        # ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        if not has_company:
            return False
        
        # เงื่อนไขที่ 1: ไม่มีภาษีมูลค่าเพิ่ม
        condition1 = "ค่าธรรมเนียมการผ่านพิธีการศุลกากร" in text
        
        # เงื่อนไขที่ 2: มีภาษีมูลค่าเพิ่ม
        condition2 = "ภาษีมูลค่าเพิ่ม" in text
        
        # ต้องมีอย่างน้อย 1 เงื่อนไข
        return condition1 or condition2
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "กรมศุลกากร"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # กรมศุลกากร: ใช้เลขประจำตัวผู้เสียภาษีเป็น 0000000000000
        # ลองหาดูก่อนว่ามี Tax ID ในเอกสารหรือไม่
        pattern1 = r'TaxID\s*[:.]?\s*(\d{13})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        pattern2 = r'Tax\s+ID\s+No[.:]?\s*(\d{13})'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # ถ้าไม่พบ ให้ใช้ค่า default สำหรับกรมศุลกากร
        return "0000000000000"
    
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
        
        ที่อยู่: เลขที่ 1 ถ.สุนทรโกษา เขตคลองเตย แขวงคลองเตย กทม. 10110
        
        Returns:
            ที่อยู่รวม (string) - ระบบจะแยกเป็นส่วนๆ อัตโนมัติใน parse_address()
        """
        return "เลขที่ 1 ถ.สุนทรโกษา เขตคลองเตย แขวงคลองเตย กทม. 10110"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """
        ดึงข้อมูลบัญชี (Account Name / Account Code)
        
        สำหรับกรณีมีภาษีมูลค่าเพิ่ม บรรทัดที่ 1 จะเป็น "บัญชีพัก"
        """
        # ตรวจสอบว่ามีภาษีมูลค่าเพิ่มหรือไม่ (ใช้ฟังก์ชัน has_vat() ที่ตรวจสอบจากรายการจริง)
        has_vat = self.has_vat(text)
        
        if has_vat:
            return {
                'account_name': 'บัญชีพัก',
                'account_code': None
            }
        
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': 0.0,
            'withholding_tax_amount': 0.0
        }
    
    def has_vat(self, text: str) -> bool:
        """
        ตรวจสอบว่าเอกสารมีภาษีมูลค่าเพิ่มหรือไม่
        
        เงื่อนไขที่ 1 (ไม่มีภาษี): 
        - ต้องมี "ค่าธรรมเนียมการผ่านพิธีการศุลกากร"
        - และไม่มี "ค่าภาษีมูลค่าเพิ่ม" หรือ "ค่าอากรขาเข้า" ในส่วนรายการ
        
        เงื่อนไขที่ 2 (มีภาษี):
        - ต้องมี "ค่าภาษีมูลค่าเพิ่ม" หรือ "ค่าอากรขาเข้า" ในส่วนรายการ
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้ามีภาษีมูลค่าเพิ่ม (มี "ค่าภาษีมูลค่าเพิ่ม" หรือ "ค่าอากรขาเข้า" ในส่วนรายการ)
            False ถ้าไม่มีภาษีมูลค่าเพิ่ม (มีแค่ "ค่าธรรมเนียมการผ่านพิธีการศุลกากร")
        """
        # ตรวจสอบว่ามี "ค่าธรรมเนียมการผ่านพิธีการศุลกากร" หรือไม่
        has_fee = "ค่าธรรมเนียมการผ่านพิธีการศุลกากร" in text
        
        # ตรวจสอบว่ามี "ค่าภาษีมูลค่าเพิ่ม" หรือ "ค่าอากรขาเข้า" ในส่วนรายการหรือไม่
        # หาตำแหน่งของ "ได้รับเงินตามรายการข้างล่างนี้ไว้แล้ว" เพื่อจำกัดขอบเขต
        has_vat_in_items = False
        
        # หาตำแหน่งของ "ได้รับเงินตามรายการข้างล่างนี้ไว้แล้ว"
        items_start = text.find("ได้รับเงินตามรายการข้างล่างนี้ไว้แล้ว")
        if items_start != -1:
            # หาตำแหน่งของ "รวมเงินทั้งสิ้น" เพื่อจำกัดขอบเขตของรายการ
            total_start = text.find("รวมเงินทั้งสิ้น", items_start)
            if total_start != -1:
                # ตรวจสอบในส่วนรายการ (ระหว่าง "ได้รับเงิน..." ถึง "รวมเงินทั้งสิ้น")
                items_section = text[items_start:total_start]
                # ตรวจสอบว่ามี "ค่าภาษีมูลค่าเพิ่ม" หรือ "ค่าอากรขาเข้า" ในส่วนรายการ
                has_vat_in_items = ("ค่าภาษีมูลค่าเพิ่ม" in items_section) or ("ค่าอากรขาเข้า" in items_section)
            else:
                # ถ้าไม่พบ "รวมเงินทั้งสิ้น" ให้ตรวจสอบในส่วนหลัง "ได้รับเงิน..."
                items_section = text[items_start:items_start+500]  # ตรวจสอบ 500 ตัวอักษรแรก
                has_vat_in_items = ("ค่าภาษีมูลค่าเพิ่ม" in items_section) or ("ค่าอากรขาเข้า" in items_section)
        else:
            # ถ้าไม่พบ "ได้รับเงิน..." ให้ตรวจสอบทั้ง text (fallback)
            has_vat_in_items = ("ค่าภาษีมูลค่าเพิ่ม" in text) or ("ค่าอากรขาเข้า" in text)
        
        # ถ้ามี "ค่าธรรมเนียมการผ่านพิธีการศุลกากร" และไม่มี "ค่าภาษีมูลค่าเพิ่ม" หรือ "ค่าอากรขาเข้า" ในส่วนรายการ = ไม่มีภาษี
        if has_fee and not has_vat_in_items:
            return False
        
        # ถ้ามี "ค่าภาษีมูลค่าเพิ่ม" หรือ "ค่าอากรขาเข้า" ในส่วนรายการ = มีภาษี
        return has_vat_in_items
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        เงื่อนไขที่ 1: ไม่มีภาษีมูลค่าเพิ่ม
        - ยอดก่อนภาษี: ดึงจาก "รวมเงินทั้งสิ้น (บาท) | 200.00"
        - ยอดภาษี: 0
        - ยอดรวม: เท่ากับยอดก่อนภาษี
        
        เงื่อนไขที่ 2: มีภาษีมูลค่าเพิ่ม
        - บรรทัดที่ 1:
          - ยอดก่อนภาษี: คำนวณจาก ยอดภาษี / 0.07
          - ยอดภาษี: ดึงจาก "ค่าภาษีมูลค่าเพิ่ม | | 13,961.00"
          - ยอดรวม: ยอดก่อนภาษี + ยอดภาษี
        - บรรทัดที่ 2:
          - ยอดก่อนภาษี: ดึงจาก "ค่าอากรขาเข้า | 18,131.00 |"
          - ยอดภาษี: 0
          - ยอดรวม: เท่ากับยอดก่อนภาษี
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (บรรทัดที่ 1 หรือยอดรวม)
                'amount_before_vat_2': float, # ยอดก่อนภาษี (บรรทัดที่ 2 - ถ้ามี)
                'vat_amount': float,          # ยอดภาษี
                'total_amount': float         # ยอดรวม
            }
        """
        result = {
            'amount_before_vat': None,
            'amount_before_vat_2': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        has_vat = self.has_vat(text)
        
        # Log สำหรับ debug
        logger.debug(f"🔍 กรมศุลกากร extract_amounts - has_vat: {has_vat}")
        logger.debug(f"🔍 กรมศุลกากร extract_amounts - Text length: {len(text)}")
        if 'รวมเงินทั้งสิ้น' in text:
            total_pos = text.find('รวมเงินทั้งสิ้น')
            logger.debug(f"🔍 กรมศุลกากร - พบ 'รวมเงินทั้งสิ้น' ที่ตำแหน่ง {total_pos}")
            logger.debug(f"🔍 กรมศุลกากร - ข้อความรอบๆ: '{text[max(0, total_pos-50):total_pos+100]}'")
        
        if not has_vat:
            # เงื่อนไขที่ 1: ไม่มีภาษีมูลค่าเพิ่ม
            # ไม่ต้องคำนวณอะไร เพียงแค่อ่านยอดเงินจาก "รวมเงินทั้งสิ้น (บาท) | 200.00"
            # รองรับหลายรูปแบบ: มี/ไม่มี space, มี/ไม่มี pipe, มี/ไม่มีวงเล็บ, มี/ไม่มี newline
            logger.info(f"🔍 กรมศุลกากร (ไม่มีภาษี) - เริ่มอ่านข้อมูล...")
            
            # ทำความสะอาด text สำหรับการค้นหา (รวม newline เป็น space)
            text_clean = re.sub(r'\s+', ' ', text)
            
            # Pattern: รวมเงินทั้งสิ้น (บาท) | 200.00
            # รองรับหลายรูปแบบ
            patterns = [
                # รูปแบบที่มี pipe และ space
                r'รวมเงินทั้งสิ้น\s*\(บาท\)\s*\|\s*([\d,]+\.?\d{2})',  # รวมเงินทั้งสิ้น (บาท) | 200.00
                r'รวมเงินทั้งสิ้น\s*\(บาท\)\s*\|\s*([\d,]+\.?\d*)',  # รวมเงินทั้งสิ้น (บาท) | 200
                # รูปแบบที่มี pipe แต่ไม่มี space
                r'รวมเงินทั้งสิ้น\s*\(บาท\)\s*\|\s*([\d,]+\.?\d{2})',  # รวมเงินทั้งสิ้น (บาท)|200.00
                # รูปแบบที่ไม่มี pipe
                r'รวมเงินทั้งสิ้น\s*\(บาท\)\s+([\d,]+\.?\d{2})',  # รวมเงินทั้งสิ้น (บาท) 200.00
                r'รวมเงินทั้งสิ้น\s*\(บาท\)\s*[:.]?\s*([\d,]+\.?\d{2})',  # รวมเงินทั้งสิ้น (บาท): 200.00
                # รูปแบบที่ไม่มีวงเล็บ
                r'รวมเงินทั้งสิ้น\s*\|\s*([\d,]+\.?\d{2})',  # รวมเงินทั้งสิ้น | 200.00
                r'รวมเงินทั้งสิ้น\s+([\d,]+\.?\d{2})',  # รวมเงินทั้งสิ้น 200.00
                # รูปแบบยืดหยุ่น (fallback)
                r'รวมเงินทั้งสิ้น[^0-9]*([\d,]+\.?\d{2})',  # รวมเงินทั้งสิ้น...200.00
            ]
            
            # ลองหาใน text เดิมก่อน
            logger.debug(f"🔍 กรมศุลกากร (ไม่มีภาษี) - ลองหาใน text เดิม...")
            for idx, pattern in enumerate(patterns):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.debug(f"🔍 Pattern {idx+1} matched (text เดิม): '{pattern}' -> matched: '{match.group(0)}' -> amount_str: '{amount_str}'")
                    try:
                        amount = float(amount_str)
                        if amount > 0:
                            result['amount_before_vat'] = amount
                            result['vat_amount'] = 0.0
                            result['total_amount'] = amount
                            logger.info(f"✅ กรมศุลกากร (ไม่มีภาษี): ยอดก่อนภาษี = {amount} (pattern {idx+1} ใน text เดิม)")
                            break
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                        continue
                else:
                    logger.debug(f"🔍 Pattern {idx+1} ไม่ match (text เดิม): '{pattern}'")
            
            # ถ้ายังไม่พบ ให้ลองหาใน text_clean
            if not result['amount_before_vat']:
                logger.debug(f"🔍 กรมศุลกากร (ไม่มีภาษี) - ลองหาใน text_clean...")
                for idx, pattern in enumerate(patterns):
                    match = re.search(pattern, text_clean, re.IGNORECASE)
                    if match:
                        amount_str = match.group(1).replace(',', '').replace(' ', '')
                        logger.debug(f"🔍 Pattern {idx+1} matched (text_clean): '{pattern}' -> matched: '{match.group(0)}' -> amount_str: '{amount_str}'")
                        try:
                            amount = float(amount_str)
                            if amount > 0:
                                result['amount_before_vat'] = amount
                                result['vat_amount'] = 0.0
                                result['total_amount'] = amount
                                logger.info(f"✅ กรมศุลกากร (ไม่มีภาษี): ยอดก่อนภาษี = {amount} (pattern {idx+1} ใน text_clean)")
                                break
                        except ValueError as e:
                            logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                            continue
            
            # ถ้ายังไม่พบ ให้ลองหาด้วยวิธีอื่น: หาคำว่า "รวมเงินทั้งสิ้น" แล้วหาตัวเลขที่อยู่ใกล้ๆ
            if not result['amount_before_vat']:
                logger.warning(f"⚠️ กรมศุลกากร (ไม่มีภาษี) - ไม่พบยอดเงินจาก patterns, ลองหาด้วยวิธีอื่น...")
                # หาคำว่า "รวมเงินทั้งสิ้น" ใน text เดิม
                total_pos = text.find('รวมเงินทั้งสิ้น')
                if total_pos != -1:
                    # หาตัวเลขที่อยู่หลัง "รวมเงินทั้งสิ้น" (ภายใน 150 ตัวอักษร)
                    search_text = text[total_pos:total_pos+150]
                    logger.info(f"🔍 ข้อความรอบๆ 'รวมเงินทั้งสิ้น' (ตำแหน่ง {total_pos}): '{search_text}'")
                    # หาตัวเลขที่มีรูปแบบ 200.00 หรือ 200,00 หรือ 200
                    numbers = re.findall(r'([\d,]+\.?\d{2})', search_text)
                    if not numbers:
                        # ลองหาแบบไม่มี .00
                        numbers = re.findall(r'([\d,]+\.?\d*)', search_text)
                    if numbers:
                        logger.info(f"🔍 พบตัวเลข {len(numbers)} ตัว: {numbers}")
                        for num_str in numbers:
                            try:
                                amount = float(num_str.replace(',', '').replace(' ', ''))
                                if amount > 0:
                                    result['amount_before_vat'] = amount
                                    result['vat_amount'] = 0.0
                                    result['total_amount'] = amount
                                    logger.info(f"✅ กรมศุลกากร (ไม่มีภาษี): ยอดก่อนภาษี = {amount} (หาใกล้ๆ 'รวมเงินทั้งสิ้น')")
                                    break
                            except ValueError as e:
                                logger.debug(f"🔍 ข้ามตัวเลข '{num_str}': {e}")
                                continue
        else:
            # เงื่อนไขที่ 2: มีภาษีมูลค่าเพิ่ม
            logger.debug(f"🔍 กรมศุลกากร (มีภาษี) - ลองหาข้อมูล...")
            
            # บรรทัดที่ 1: ดึงยอดภาษีมูลค่าเพิ่ม
            # Pattern: ค่าภาษีมูลค่าเพิ่ม | | 13,961.00
            # รองรับหลายรูปแบบ: มี/ไม่มี space, มี/ไม่มี pipe
            vat_patterns = [
                r'ค่าภาษีมูลค่าเพิ่ม\s*\|\s*\|\s*([\d,]+\.?\d{2})',  # ค่าภาษีมูลค่าเพิ่ม | | 13,961.00
                r'ค่าภาษีมูลค่าเพิ่ม\s*\|\s+([\d,]+\.?\d{2})',  # ค่าภาษีมูลค่าเพิ่ม | 13,961.00 (space หลัง |)
                r'ค่าภาษีมูลค่าเพิ่ม\s*\|\s*([\d,]+\.?\d{2})',  # ค่าภาษีมูลค่าเพิ่ม | 13,961.00
                r'ค่าภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d{2})',  # ค่าภาษีมูลค่าเพิ่ม 13,961.00
                r'ค่าภาษีมูลค่าเพิ่ม[^0-9]*([\d,]+\.?\d{2})',  # ค่าภาษีมูลค่าเพิ่ม...13,961.00 (flexible)
                r'ภาษีมูลค่าเพิ่ม\s*\|\s*\|\s*([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม | | 13,961.00
                r'ภาษีมูลค่าเพิ่ม\s*\|\s+([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม | 13,961.00
                r'ภาษีมูลค่าเพิ่ม\s*\|\s*([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม | 13,961.00
            ]
            
            vat_amount = None
            logger.debug(f"🔍 กรมศุลกากร (มีภาษี) - ลองหา 'ค่าภาษีมูลค่าเพิ่ม'...")
            if 'ค่าภาษีมูลค่าเพิ่ม' in text:
                vat_pos = text.find('ค่าภาษีมูลค่าเพิ่ม')
                logger.debug(f"🔍 พบ 'ค่าภาษีมูลค่าเพิ่ม' ที่ตำแหน่ง {vat_pos}")
                logger.debug(f"🔍 ข้อความรอบๆ: '{text[max(0, vat_pos-30):vat_pos+100]}'")
            
            for idx, pattern in enumerate(vat_patterns):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    vat_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.debug(f"🔍 VAT Pattern {idx+1} matched: '{pattern}' -> matched: '{match.group(0)}' -> vat_str: '{vat_str}'")
                    try:
                        vat_amount = float(vat_str)
                        if vat_amount > 0:
                            result['vat_amount'] = vat_amount
                            logger.info(f"✅ กรมศุลกากร (มีภาษี): ยอดภาษี = {vat_amount} (pattern {idx+1})")
                            break
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{vat_str}', Error: {e}")
                        continue
                else:
                    logger.debug(f"🔍 VAT Pattern {idx+1} ไม่ match: '{pattern}'")
            
            # ถ้ายังไม่พบ ให้ลองหาด้วยวิธีอื่น
            if not vat_amount:
                logger.warning(f"⚠️ กรมศุลกากร (มีภาษี) - ไม่พบยอดภาษีจาก patterns, ลองหาด้วยวิธีอื่น...")
                vat_pos = text.find('ค่าภาษีมูลค่าเพิ่ม')
                if vat_pos != -1:
                    # หาตัวเลขที่อยู่หลัง "ค่าภาษีมูลค่าเพิ่ม" (ภายใน 100 ตัวอักษร)
                    search_text = text[vat_pos:vat_pos+100]
                    logger.debug(f"🔍 ข้อความรอบๆ 'ค่าภาษีมูลค่าเพิ่ม': '{search_text}'")
                    # หาตัวเลขที่มีรูปแบบ 13,961.00
                    numbers = re.findall(r'([\d,]+\.?\d{2})', search_text)
                    if numbers:
                        # เลือกตัวเลขแรกที่มากกว่า 0
                        for num_str in numbers:
                            try:
                                amount = float(num_str.replace(',', '').replace(' ', ''))
                                if amount > 0:
                                    vat_amount = amount
                                    result['vat_amount'] = vat_amount
                                    logger.info(f"✅ กรมศุลกากร (มีภาษี): ยอดภาษี = {vat_amount} (หาใกล้ๆ)")
                                    break
                            except ValueError:
                                continue
            
            # คำนวณยอดก่อนภาษี (บรรทัดที่ 1) จากยอดภาษี / 0.07
            if vat_amount and vat_amount > 0:
                result['amount_before_vat'] = vat_amount / 0.07
                logger.info(f"✅ กรมศุลกากร (มีภาษี): ยอดก่อนภาษี (บรรทัด 1) = {result['amount_before_vat']:.2f} (คำนวณจาก {vat_amount} / 0.07)")
            
            # บรรทัดที่ 2: ดึงค่าอากรขาเข้า
            # Pattern: ค่าอากรขาเข้า | 18,131.00 |
            # รองรับหลายรูปแบบ: มี/ไม่มี space, มี/ไม่มี pipe
            import_patterns = [
                r'ค่าอากรขาเข้า\s*\|\s*([\d,]+\.?\d{2})\s*\|',  # ค่าอากรขาเข้า | 18,131.00 |
                r'ค่าอากรขาเข้า\s*\|\s+([\d,]+\.?\d{2})\s*\|',  # ค่าอากรขาเข้า | 18,131.00 | (space หลัง |)
                r'ค่าอากรขาเข้า\s*\|\s*([\d,]+\.?\d{2})',  # ค่าอากรขาเข้า | 18,131.00
                r'ค่าอากรขาเข้า\s+([\d,]+\.?\d{2})',  # ค่าอากรขาเข้า 18,131.00
                r'ค่าอากรขาเข้า[^0-9]*([\d,]+\.?\d{2})',  # ค่าอากรขาเข้า...18,131.00 (flexible)
                r'อากรขาเข้า\s*\|\s*([\d,]+\.?\d{2})\s*\|',  # อากรขาเข้า | 18,131.00 |
                r'อากรขาเข้า\s*\|\s*([\d,]+\.?\d{2})',  # อากรขาเข้า | 18,131.00
            ]
            
            logger.debug(f"🔍 กรมศุลกากร (มีภาษี) - ลองหา 'ค่าอากรขาเข้า'...")
            if 'ค่าอากรขาเข้า' in text:
                import_pos = text.find('ค่าอากรขาเข้า')
                logger.debug(f"🔍 พบ 'ค่าอากรขาเข้า' ที่ตำแหน่ง {import_pos}")
                logger.debug(f"🔍 ข้อความรอบๆ: '{text[max(0, import_pos-30):import_pos+100]}'")
            
            for idx, pattern in enumerate(import_patterns):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.debug(f"🔍 Import Pattern {idx+1} matched: '{pattern}' -> matched: '{match.group(0)}' -> amount_str: '{amount_str}'")
                    try:
                        amount = float(amount_str)
                        if amount > 0:
                            result['amount_before_vat_2'] = amount
                            logger.info(f"✅ กรมศุลกากร (มีภาษี): ยอดก่อนภาษี (บรรทัด 2) = {amount} (pattern {idx+1})")
                            break
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                        continue
                else:
                    logger.debug(f"🔍 Import Pattern {idx+1} ไม่ match: '{pattern}'")
            
            # ถ้ายังไม่พบ ให้ลองหาด้วยวิธีอื่น
            if not result['amount_before_vat_2']:
                logger.warning(f"⚠️ กรมศุลกากร (มีภาษี) - ไม่พบค่าอากรขาเข้าจาก patterns, ลองหาด้วยวิธีอื่น...")
                import_pos = text.find('ค่าอากรขาเข้า')
                if import_pos != -1:
                    # หาตัวเลขที่อยู่หลัง "ค่าอากรขาเข้า" (ภายใน 100 ตัวอักษร)
                    search_text = text[import_pos:import_pos+100]
                    logger.debug(f"🔍 ข้อความรอบๆ 'ค่าอากรขาเข้า': '{search_text}'")
                    # หาตัวเลขที่มีรูปแบบ 18,131.00
                    numbers = re.findall(r'([\d,]+\.?\d{2})', search_text)
                    if numbers:
                        # เลือกตัวเลขแรกที่มากกว่า 0
                        for num_str in numbers:
                            try:
                                amount = float(num_str.replace(',', '').replace(' ', ''))
                                if amount > 0:
                                    result['amount_before_vat_2'] = amount
                                    logger.info(f"✅ กรมศุลกากร (มีภาษี): ยอดก่อนภาษี (บรรทัด 2) = {amount} (หาใกล้ๆ)")
                                    break
                            except ValueError:
                                continue
            
            # คำนวณยอดรวม
            line1_before_vat = result.get('amount_before_vat') or 0
            line1_vat = result.get('vat_amount') or 0
            line1_total = line1_before_vat + line1_vat
            
            line2_before_vat = result.get('amount_before_vat_2') or 0
            line2_total = line2_before_vat
            
            result['total_amount'] = line1_total + line2_total
            logger.info(f"✅ กรมศุลกากร (มีภาษี): ยอดรวม = {result['total_amount']:.2f} (บรรทัด 1: {line1_total:.2f} + บรรทัด 2: {line2_total:.2f})")
        
        return result
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงหมายเหตุ (ชื่อไฟล์เก่า)
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF (optional)
        
        Returns:
            หมายเหตุ (ชื่อไฟล์เก่า)
        """
        if filename:
            # ตัด VAT_, WHT_, None_vat_ และ .pdf
            filename_clean = re.sub(r'(VAT_|None_vat_|WHT_)', '', filename, flags=re.IGNORECASE)
            filename_clean = re.sub(r'\.pdf$', '', filename_clean, flags=re.IGNORECASE)
            return filename_clean.strip()
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """
        ดึงเลขที่ชำระอากร (สำหรับกรณีมีภาษีมูลค่าเพิ่ม)
        
        รูปแบบ: เลขที่ชำระอากร/วันเดือนปี 2801-090986/04-11-68
        ข้อมูลที่ต้องการ: 2801-090986
        """
        # Pattern: เลขที่ชำระอากร/วันเดือนปี 2801-090986/04-11-68
        patterns = [
            r'เลขที่ชำระอากร\s*/?\s*วันเดือนปี\s+(\d{4}-\d{6})',  # เลขที่ชำระอากร/วันเดือนปี 2801-090986/04-11-68
            r'เลขที่ชำระอากร\s*[:.]?\s*[^0-9]*(\d{4}-\d{6})',  # เลขที่ชำระอากร: ... 2801-090986
            r'เลขที่ชำระอากร[^0-9]*(\d{4}-\d{6})',  # เลขที่ชำระอากร... 2801-090986
            r'(\d{4}-\d{6})\s*/?\s*\d{2}-\d{2}-\d{2}',  # 2801-090986/04-11-68 (fallback)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                doc_num = match.group(1).strip()
                # ตรวจสอบรูปแบบที่ถูกต้อง (ต้องมีรูปแบบ XXXX-XXXXXX)
                if re.match(r'^\d{4}-\d{6}$', doc_num):
                    return doc_num
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจจับประเภทเอกสาร
        
        Returns:
            1 = เอกสารมีภาษีมูลค่าเพิ่ม (VAT)
            2 = เอกสารไม่มีภาษีมูลค่าเพิ่ม (NoneVat)
        """
        if self.has_vat(text):
            return 1  # มีภาษีมูลค่าเพิ่ม
        else:
            return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสารกรมศุลกากร
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสารกรมศุลกากรหรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสารกรมศุลกากร'
            }
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text)
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, WHT_, None_vat_)
        new_filename = filename
        if new_filename:
            new_filename = re.sub(r'(VAT_|None_vat_|WHT_)', '', new_filename, flags=re.IGNORECASE)
        
        has_vat = self.has_vat(text)
        
        # สำหรับกรณีมีภาษีมูลค่าเพิ่ม: คำนวณยอดรวม
        if has_vat:
            line1_before_vat = amounts.get('amount_before_vat') or 0
            line1_vat = amounts.get('vat_amount') or 0
            line2_before_vat = amounts.get('amount_before_vat_2') or 0
            
            # ยอดรวมทั้งหมด
            total_before_vat = line1_before_vat + line2_before_vat
            total_vat = line1_vat
            total_amount = amounts.get('total_amount') or (total_before_vat + total_vat)
            
            return {
                'success': True,
                'company': 'CUSTOMS_DEPARTMENT',
                'company_name': company_name,
                'tax_id': tax_id,
                'date': date,
                'document_number': document_number,  # เลขที่ชำระอากร
                'address': address,
                'account_name': account_info['account_name'],
                'account_code': account_info['account_code'],
                'withholding_tax_percent': withholding['withholding_tax_percent'],
                'withholding_tax_amount': withholding['withholding_tax_amount'],
                'amount_before_vat': total_before_vat,  # รวมทั้ง 2 บรรทัด
                'vat_amount': total_vat,
                'total_amount': total_amount,
                'remark': remark,
                'new_filename': new_filename,
                'old_filename': filename,
                'filepath': filepath,
                'document_type': document_type,
                # ข้อมูลเพิ่มเติมสำหรับกรณีมีภาษี (สำหรับสร้าง 2 แถว)
                'amount_before_vat_line1': line1_before_vat,  # บรรทัดที่ 1
                'amount_before_vat_line2': line2_before_vat,  # บรรทัดที่ 2
                'vat_amount_line1': line1_vat,  # ภาษีบรรทัดที่ 1
                'vat_amount_line2': 0.0,  # ภาษีบรรทัดที่ 2 (ไม่มี)
            }
        else:
            # กรณีไม่มีภาษีมูลค่าเพิ่ม
            return {
                'success': True,
                'company': 'CUSTOMS_DEPARTMENT',
                'company_name': company_name,
                'tax_id': tax_id,
                'date': date,
                'document_number': document_number,  # เลขที่ชำระอากร
                'address': address,
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
                'document_type': document_type,  # 2 = ไม่มีภาษีมูลค่าเพิ่ม
            }


# ===== KLN Seaport Extractor =====
class KLNSeaportExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท เคแอลเอ็น ซีพอร์ต จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "เคแอลเอ็น ซีพอร์ต",
        "KLN Seaport"
    ]
    
    def __init__(self):
        """Initialize KLN Seaport Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ KLN Seaport หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท เคแอลเอ็น ซีพอร์ต จำกัด"
        2. Tax ID "0105533017118"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร KLN Seaport (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105533017118"
        has_tax_id = "0105533017118" in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "บริษัท เคแอลเอ็น ซีพอร์ต จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TaxID 0105533017118 หรือ Tax ID No. 0105533017118
        pattern1 = r'TaxID\s*[:.]?\s*(\d{13})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        pattern2 = r'Tax\s+ID\s+No[.:]?\s*(\d{13})'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # ถ้าไม่พบ pattern ให้ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่
        if "0105533017118" in text:
            return "0105533017118"
        
        return None
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา"""
        # Pattern: สาขา : 00004 หรือ สาขาที่ 00004
        patterns = [
            r'สาขา\s*[:.]?\s*(\d{5})',  # สาขา : 00004
            r'สาขาที่\s*(\d{5})',  # สาขาที่ 00004
            r'Branch\s*[:.]?\s*(\d{5})',  # Branch : 00004
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern 1: วันที่/Date 04-Nov-2025
        pattern1 = r'วันที่\s*/?\s*Date\s+(\d{1,2})-([A-Z]{3})-(\d{4})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            day = match.group(1).zfill(2)
            month_abbr = match.group(2).upper()
            year = match.group(3)
            
            month_map = {
                'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
            }
            
            month = month_map.get(month_abbr, '01')
            return f"{day}/{month}/{year}"
        
        # Pattern 2: 03/11/2025 หรือ Date: 03/11/2025
        pattern2 = r'(?:Date\s*[:.]?\s*)?(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern2, text)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: เลขที่/No. ICD2E250138180
        patterns = [
            r'เลขที่\s*/?\s*No\.\s+([A-Z0-9]+)',  # เลขที่/No. ICD2E250138180
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: ICD2E250138180
            r'No\.\s+([A-Z0-9]+)',  # No. ICD2E250138180
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: 113/40 หมู่ที่ 1 ต.ทุ่งสุขลา อ.ศรีราชา จ.ชลบุรี 20230
        
        Returns:
            ที่อยู่รวม (string) - ระบบจะแยกเป็นส่วนๆ อัตโนมัติใน parse_address()
        """
        # ที่อยู่: 113/40 หมู่ที่ 1 ต.ทุ่งสุขลา อ.ศรีราชา จ.ชลบุรี 20230
        # ส่งคืนเป็น string เดียว ระบบจะแยกเป็นส่วนๆ อัตโนมัติใน parse_address()
        return "113/40 หมู่ที่ 1 ต.ทุ่งสุขลา อ.ศรีราชา จ.ชลบุรี 20230"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': 0.0,
            'withholding_tax_amount': 0.0
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (1,250.00)
                'vat_amount': float,          # ยอดภาษี (87.50)
                'total_amount': float         # ยอดรวม (1,337.50)
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # Pattern 1: รวม/SUB TOTAL 1,250.00
        pattern_subtotal = r'(?:รวม|SUB\s*TOTAL)\s*[:.]?\s*([\d,]+\.?\d{2})'
        match = re.search(pattern_subtotal, text, re.IGNORECASE)
        if match:
            try:
                amount_str = match.group(1).replace(',', '').replace(' ', '')
                result['amount_before_vat'] = float(amount_str)
            except ValueError:
                pass
        
        # Pattern 2: ภาษีมูลค่าเพิ่ม 7%/VAT 87.50
        pattern_vat = r'(?:ภาษีมูลค่าเพิ่ม|VAT)\s*(?:7%|[:.])?\s*([\d,]+\.?\d{2})'
        match = re.search(pattern_vat, text, re.IGNORECASE)
        if match:
            try:
                vat_str = match.group(1).replace(',', '').replace(' ', '')
                result['vat_amount'] = float(vat_str)
            except ValueError:
                pass
        
        # Pattern 3: จำนวนเงินรวม/Grand Total 1,337.50
        pattern_total = r'(?:จำนวนเงินรวม|Grand\s*Total)\s*[:.]?\s*([\d,]+\.?\d{2})'
        match = re.search(pattern_total, text, re.IGNORECASE)
        if match:
            try:
                total_str = match.group(1).replace(',', '').replace(' ', '')
                result['total_amount'] = float(total_str)
            except ValueError:
                pass
        
        # ถ้ายังไม่มี total_amount ให้คำนวณจาก amount_before_vat + vat_amount
        if result['total_amount'] is None:
            if result['amount_before_vat'] and result['vat_amount']:
                result['total_amount'] = result['amount_before_vat'] + result['vat_amount']
        
        return result
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงหมายเหตุ (MEDUYQ420646 + ชื่อไฟล์เก่าที่ตัด VAT_/None_vat_/WHT_ แล้ว)
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF (optional)
        
        Returns:
            หมายเหตุในรูปแบบ "MEDUYQ420646 EXC-2511-008"
        """
        bl = None
        
        # Pattern: MEDUYQ420646 (BL number)
        # รองรับหลายรูปแบบ: BL: MEDUYQ420646, B/L: MEDUYQ420646, BL NO: MEDUYQ420646
        bl_patterns = [
            r'BL\s*[:.]?\s*([A-Z0-9]+)',  # BL: MEDUYQ420646
            r'B/L\s*[:.]?\s*([A-Z0-9]+)',  # B/L: MEDUYQ420646
            r'BL\s*NO\s*[:.]?\s*([A-Z0-9]+)',  # BL NO: MEDUYQ420646
            r'([A-Z]{4,}\d{6,})',  # Pattern สำหรับ BL number (ตัวอักษร 4+ ตัวเลข 6+)
        ]
        
        for pattern in bl_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bl_candidate = match.group(1).strip()
                # ตรวจสอบว่าเป็น BL number ที่ถูกต้อง (มีตัวอักษรและตัวเลข)
                if len(bl_candidate) >= 8 and any(c.isalpha() for c in bl_candidate) and any(c.isdigit() for c in bl_candidate):
                    bl = bl_candidate
                    break
        
        # ดึงชื่อไฟล์เก่าที่ตัด VAT_/None_vat_/WHT_ แล้ว
        filename_clean = None
        if filename:
            # ตัด VAT_, None_vat_, WHT_ และ .pdf
            filename_clean = re.sub(r'(VAT_|None_vat_|WHT_)', '', filename, flags=re.IGNORECASE)
            filename_clean = re.sub(r'\.pdf$', '', filename_clean, flags=re.IGNORECASE)
            filename_clean = filename_clean.strip()
        
        # รวมผลลัพธ์
        if bl and filename_clean:
            return f"{bl} {filename_clean}"
        elif bl:
            return bl
        elif filename_clean:
            return filename_clean
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจจับประเภทเอกสาร
        
        Returns:
            1 = เอกสารมีภาษีมูลค่าเพิ่ม (VAT)
        """
        return 1  # มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร KLN Seaport
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร KLN Seaport หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร KLN Seaport'
            }
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        branch = self.extract_branch(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text)
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)  # ส่ง filename ไปด้วย
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, None_vat_, WHT_)
        new_filename = filename
        if new_filename:
            new_filename = re.sub(r'(VAT_|None_vat_|WHT_)', '', new_filename, flags=re.IGNORECASE)
        
        return {
            'success': True,
            'company': 'KLN_SEAPORT',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,  # สาขา
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
            'remark': remark,
            'new_filename': new_filename,
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,  # 1 = มีภาษีมูลค่าเพิ่ม
        }


# ===== Eastern Sea Lamchabang Terminal Extractor =====
class EasternSeaLamchabangTerminalExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท อีสเทิร์นซี แหลมฉบัง เทอร์มินัล จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "อีสเทิร์นซี แหลมฉบัง เทอร์มินัล",
        "Eastern Sea Lamchabang Terminal"
    ]
    
    def __init__(self):
        """Initialize Eastern Sea Lamchabang Terminal Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Eastern Sea Lamchabang Terminal หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท อีสเทิร์นซี แหลมฉบัง เทอร์มินัล จำกัด"
        2. Tax ID "0105533144471"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Eastern Sea Lamchabang Terminal (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105533144471"
        has_tax_id = "0105533144471" in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "บริษัท อีสเทิร์นซี แหลมฉบัง เทอร์มินัล จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TaxID 0105533144471 หรือ Tax ID No. 0105533144471
        pattern1 = r'TaxID\s*[:.]?\s*(\d{13})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        pattern2 = r'Tax\s+ID\s+No[.:]?\s*(\d{13})'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # ถ้าไม่พบ pattern ให้ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่
        if "0105533144471" in text:
            return "0105533144471"
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern 1: === วันที่ === แล้วตามด้วย 04/11/2025 (ในบรรทัดเดียวกัน)
        pattern1 = r'===?\s*วันที่\s*===?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            return f"{day}/{month}/{year}"
        
        # Pattern 2: === วันที่ === แล้ววันที่อยู่ในบรรทัดถัดไป
        pattern2 = r'===?\s*วันที่\s*===?\s*\n\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern2, text, re.IGNORECASE | re.MULTILINE)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            return f"{day}/{month}/{year}"
        
        # Pattern 3: หา "=== วันที่ ===" แล้วหาวันที่ในบรรทัดถัดไป (รองรับหลายรูปแบบ)
        date_header_match = re.search(r'===?\s*วันที่\s*===?', text, re.IGNORECASE)
        if date_header_match:
            # หาวันที่ในบรรทัดถัดไป (ภายใน 100 ตัวอักษร) - รองรับ space และ newline
            start_pos = date_header_match.end()
            next_text = text[start_pos:start_pos+100]
            # หาวันที่ (รองรับ space นำหน้าและหลัง)
            date_match = re.search(r'\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})\s*', next_text)
            if date_match:
                day = date_match.group(1).zfill(2)
                month = date_match.group(2).zfill(2)
                year = date_match.group(3)
                return f"{day}/{month}/{year}"
        
        # Pattern 4: วันที่: 04/11/2025
        pattern4 = r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern4, text)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern 1: === เลขที่ === แล้วตามด้วย A25111491 (ในบรรทัดเดียวกัน)
        pattern1 = r'===?\s*เลขที่\s*===?\s*([A-Z0-9]+)'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Pattern 2: === เลขที่ === แล้วเลขที่อยู่ในบรรทัดถัดไป
        pattern2 = r'===?\s*เลขที่\s*===?\s*\n\s*([A-Z0-9]+)'
        match = re.search(pattern2, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # Pattern 3: หา "=== เลขที่ ===" แล้วหาเลขที่ในบรรทัดถัดไป (รองรับหลายรูปแบบ)
        doc_header_match = re.search(r'===?\s*เลขที่\s*===?', text, re.IGNORECASE)
        if doc_header_match:
            # หาเลขที่ในบรรทัดถัดไป (ภายใน 50 ตัวอักษร) - รองรับ space และ newline
            start_pos = doc_header_match.end()
            next_text = text[start_pos:start_pos+50]
            # หา pattern ที่เริ่มด้วยตัวอักษรหรือตัวเลข (A-Z0-9) - รองรับ space นำหน้า
            # รูปแบบ: " A25111491" หรือ "A25111491"
            doc_match = re.search(r'\s*([A-Z0-9]{6,})', next_text)  # ต้องมีอย่างน้อย 6 ตัวอักษร/ตัวเลข
            if doc_match:
                doc_num = doc_match.group(1).strip()
                # ตรวจสอบว่าเป็นเลขที่เอกสารที่ถูกต้อง (ต้องมีตัวอักษรหรือตัวเลข)
                if len(doc_num) >= 6:
                    return doc_num
        
        # Pattern 4: เลขที่: A25111491 (รูปแบบเดิม)
        patterns = [
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: A25111491
            r'Document\s+No\s*[:.]?\s*([A-Z0-9]+)',  # Document No: A25111491
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: อาคารท่าเทียบเรือพาณิชย์แหลมฉบัง ท่าเทียบเรือตู้สินค้า หมายเลข 3 ถนนสุขุมวิท ตำบลทุ่งสุขลา อำเภอศรีราชา จังหวัดชลบุรี 20230
        
        Returns:
            ที่อยู่รวม (string) - ระบบจะแยกเป็นส่วนๆ อัตโนมัติใน parse_address()
        """
        # ลองหาที่อยู่จาก text ก่อน (มักจะอยู่หลังชื่อบริษัท)
        lines = text.split('\n')
        address_lines = []
        collecting = False
        
        # หาตำแหน่งที่เริ่มต้นที่อยู่ (มักจะอยู่หลังชื่อบริษัท)
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # หา "บริษัท อีสเทิร์นซี แหลมฉบัง เทอร์มินัล จำกัด" แล้วเก็บบรรทัดถัดไปที่เป็นที่อยู่
            if 'อีสเทิร์นซี แหลมฉบัง เทอร์มินัล' in line_clean and 'บริษัท' in line_clean:
                # เริ่มเก็บบรรทัดถัดไป
                collecting = True
                continue
            
            # ถ้ากำลังเก็บข้อมูลที่อยู่
            if collecting:
                # หยุดเมื่อเจอ TaxID, Tax ID, เลขประจำตัวผู้เสียภาษี, หรือ header อื่นๆ
                if any(keyword in line_clean for keyword in ['TaxID', 'Tax ID', 'เลขประจำตัวผู้เสียภาษี', 'ใบเสร็จ', 'ใบกำกับ', '===']):
                    break
                
                # เก็บบรรทัดที่มีข้อมูล (ไม่ใช่บรรทัดว่าง และมีความยาวมากกว่า 20 ตัวอักษร)
                if line_clean and len(line_clean) > 20:
                    # ตรวจสอบว่ามีรูปแบบที่อยู่ (มีคำว่า "อาคาร", "ถนน", "ตำบล", "อำเภอ", "จังหวัด" หรือ "หมายเลข")
                    if any(keyword in line_clean for keyword in ['อาคาร', 'ถนน', 'ตำบล', 'อำเภอ', 'จังหวัด', 'หมายเลข', 'ชลบุรี']):
                        address_lines.append(line_clean)
                        break  # หาได้แล้ว ให้หยุด
        
        # รวมที่อยู่ทั้งหมด
        if address_lines:
            address = ' '.join(address_lines).strip()
            # ทำความสะอาด: ลบ space หลายตัว
            address = re.sub(r'\s+', ' ', address)
            if len(address) > 20:
                return address
        
        # Fallback: ใช้ที่อยู่ default
        return "อาคารท่าเทียบเรือพาณิชย์แหลมฉบัง ท่าเทียบเรือตู้สินค้า หมายเลข 3 ถนนสุขุมวิท ตำบลทุ่งสุขลา อำเภอศรีราชา จังหวัดชลบุรี 20230"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': 0.0,
            'withholding_tax_amount': 0.0
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (1,000.00)
                'vat_amount': float,          # ยอดภาษี (70.00)
                'total_amount': float         # ยอดรวม (1,070.00)
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # Pattern 1: รวมเงิน | 1,000.00 (รองรับหลายรูปแบบ)
        patterns_before_vat = [
            r'รวมเงิน\s*\|\s*([\d,]+\.?\d{2})',  # รวมเงิน | 1,000.00
            r'รวมเงิน\s*:\s*([\d,]+\.?\d{2})',  # รวมเงิน : 1,000.00
            r'รวมเงิน\s+([\d,]+\.?\d{2})',  # รวมเงิน 1,000.00
            r'รวมเงิน[^0-9]*([\d,]+\.?\d{2})',  # รวมเงิน...1,000.00 (flexible)
        ]
        
        for pattern in patterns_before_vat:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    amount = float(amount_str)
                    if amount > 0:
                        result['amount_before_vat'] = amount
                        break
                except ValueError:
                    continue
        
        # Pattern 2: ภาษีมูลค่าเพิ่ม | 70.00 (รองรับหลายรูปแบบ)
        patterns_vat = [
            r'ภาษีมูลค่าเพิ่ม\s*\|\s*([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม | 70.00
            r'ภาษีมูลค่าเพิ่ม\s*:\s*([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม : 70.00
            r'ภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม 70.00
            r'ภาษีมูลค่าเพิ่ม[^0-9]*([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม...70.00 (flexible)
        ]
        
        for pattern in patterns_vat:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    vat_str = match.group(1).replace(',', '').replace(' ', '')
                    vat = float(vat_str)
                    if vat > 0:
                        result['vat_amount'] = vat
                        break
                except ValueError:
                    continue
        
        # Pattern 3: ยอดเงินสุทธิ | 1,070.00 (รองรับหลายรูปแบบ)
        patterns_total = [
            r'ยอดเงินสุทธิ\s*\|\s*([\d,]+\.?\d{2})',  # ยอดเงินสุทธิ | 1,070.00
            r'ยอดเงินสุทธิ\s*:\s*([\d,]+\.?\d{2})',  # ยอดเงินสุทธิ : 1,070.00
            r'ยอดเงินสุทธิ\s+([\d,]+\.?\d{2})',  # ยอดเงินสุทธิ 1,070.00
            r'ยอดเงินสุทธิ[^0-9]*([\d,]+\.?\d{2})',  # ยอดเงินสุทธิ...1,070.00 (flexible)
        ]
        
        for pattern in patterns_total:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    total_str = match.group(1).replace(',', '').replace(' ', '')
                    total = float(total_str)
                    if total > 0:
                        result['total_amount'] = total
                        break
                except ValueError:
                    continue
        
        # ถ้ายังไม่มี total_amount ให้คำนวณจาก amount_before_vat + vat_amount
        if result['total_amount'] is None:
            if result['amount_before_vat'] and result['vat_amount']:
                result['total_amount'] = result['amount_before_vat'] + result['vat_amount']
        
        return result
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงหมายเหตุ (Ref. No. + เบอร์ตู้ + ชื่อไฟล์เก่า)
        
        รูปแบบ: Ref. No.: 125110410439 เบอร์ตู้ NBYYU8153857 {ชื่อไฟล์เก่า}
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF (optional)
        
        Returns:
            หมายเหตุในรูปแบบ "Ref. No.: 125110410439 เบอร์ตู้ NBYYU8153857 {ชื่อไฟล์เก่า}"
        """
        ref_no = None
        container_no = None
        
        # Pattern 1: Ref. No.: 125110410439
        ref_patterns = [
            r'Ref\.\s*No\.\s*[:.]?\s*([0-9]+)',  # Ref. No.: 125110410439
            r'Ref\s*No\s*[:.]?\s*([0-9]+)',  # Ref No: 125110410439
            r'Reference\s*No\.\s*[:.]?\s*([0-9]+)',  # Reference No.: 125110410439
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ref_no = match.group(1).strip()
                break
        
        # Pattern 2: เบอร์ตู้ NBYYU8153857
        container_patterns = [
            r'เบอร์ตู้\s+([A-Z0-9]+)',  # เบอร์ตู้ NBYYU8153857
            r'Container\s+No\.\s*[:.]?\s*([A-Z0-9]+)',  # Container No.: NBYYU8153857
            r'Container\s*[:.]?\s*([A-Z0-9]+)',  # Container: NBYYU8153857
        ]
        
        for pattern in container_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                container_no = match.group(1).strip()
                break
        
        # ดึงชื่อไฟล์เก่าที่ตัด VAT_/None_vat_/WHT_ แล้ว
        filename_clean = None
        if filename:
            # ตัด VAT_, None_vat_, WHT_ และ .pdf
            filename_clean = re.sub(r'(VAT_|None_vat_|WHT_)', '', filename, flags=re.IGNORECASE)
            filename_clean = re.sub(r'\.pdf$', '', filename_clean, flags=re.IGNORECASE)
            filename_clean = filename_clean.strip()
        
        # รวมผลลัพธ์
        parts = []
        if ref_no:
            parts.append(f"Ref. No.: {ref_no}")
        if container_no:
            parts.append(f"เบอร์ตู้ {container_no}")
        if filename_clean:
            parts.append(filename_clean)
        
        return ' '.join(parts) if parts else None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจจับประเภทเอกสาร
        
        Returns:
            1 = เอกสารมีภาษีมูลค่าเพิ่ม (VAT)
        """
        return 1  # มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร Eastern Sea Lamchabang Terminal
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร Eastern Sea Lamchabang Terminal หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร อีสเทิร์นซี แหลมฉบัง เทอร์มินัล'
            }
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text)
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)  # ส่ง filename ไปด้วย
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, None_vat_, WHT_)
        new_filename = filename
        if new_filename:
            new_filename = re.sub(r'(VAT_|None_vat_|WHT_)', '', new_filename, flags=re.IGNORECASE)
        
        # แยกที่อยู่เป็นส่วนๆ สำหรับ Eastern Sea Lamchabang Terminal
        # ที่อยู่: อาคารท่าเทียบเรือพาณิชย์แหลมฉบัง ท่าเทียบเรือตู้สินค้า หมายเลข 3 ถนนสุขุมวิท ตำบลทุ่งสุขลา อำเภอศรีราชา จังหวัดชลบุรี 20230
        # เลขที่ = 3, อื่นๆ = อาคารท่าเทียบเรือพาณิชย์แหลมฉบัง ท่าเทียบเรือตู้สินค้า, จังหวัด = ชลบุรี
        address_full = address or ''
        building_number = ''
        other_info = ''
        soi = ''  # ซอย/ตรอก
        road = ''
        subdistrict = ''
        district = ''
        province = ''
        postal_code = ''
        
        if address:
            # ดึงเลขที่จาก "หมายเลข 3" (ดึงแค่เลข 3)
            # Pattern: "หมายเลข 3" -> "3"
            building_match = re.search(r'หมายเลข\s+(\d+)', address)
            if building_match:
                building_number = building_match.group(1).strip()
            
            # ดึงอื่นๆ = "อาคารท่าเทียบเรือพาณิชย์แหลมฉบัง ท่าเทียบเรือตู้สินค้า"
            # หาส่วนที่อยู่ก่อน "หมายเลข" (ดึงทุกอย่างก่อน "หมายเลข")
            # Pattern: "อาคาร... หมายเลข" -> "อาคาร..."
            other_match = re.search(r'^(.+?)(?=\s*หมายเลข)', address)
            if other_match:
                other_info = other_match.group(1).strip()
            
            # ดึงถนนจาก "ถนนสุขุมวิท"
            # Pattern: "ถนนสุขุมวิท" -> "ถนนสุขุมวิท"
            road_match = re.search(r'(ถนน[ก-๙A-Za-z]+?)(?:\s+ตำบล|\s+อำเภอ|\s+จังหวัด|\s+\d{5}|$)', address)
            if road_match:
                road = road_match.group(1).strip()
            
            # ดึงตำบลจาก "ตำบลทุ่งสุขลา"
            # Pattern: "ตำบลทุ่งสุขลา" -> "ทุ่งสุขลา"
            subdistrict_match = re.search(r'ตำบล\s*([ก-๙A-Za-z]+?)(?:\s+อำเภอ|\s+จังหวัด|\s+\d{5}|$)', address)
            if subdistrict_match:
                subdistrict = subdistrict_match.group(1).strip()
            
            # ดึงอำเภอจาก "อำเภอศรีราชา"
            # Pattern: "อำเภอศรีราชา" -> "ศรีราชา"
            district_match = re.search(r'อำเภอ\s*([ก-๙A-Za-z]+?)(?:\s+จังหวัด|\s+\d{5}|$)', address)
            if district_match:
                district = district_match.group(1).strip()
            
            # ดึงจังหวัดจาก "จังหวัดชลบุรี"
            # Pattern: "จังหวัดชลบุรี" -> "ชลบุรี"
            province_match = re.search(r'จังหวัด\s*(ชลบุรี)', address)
            if province_match:
                province = province_match.group(1).strip()
            
            # ดึงรหัสไปรษณีย์ (5 หลัก) - หาเลข 5 หลักที่อยู่ท้ายสุด
            # Pattern: "20230" -> "20230"
            postal_match = re.search(r'(\d{5})\s*$', address)
            if postal_match:
                postal_code = postal_match.group(1).strip()
        
        return {
            'success': True,
            'company': 'EASTERN_SEA_LAMCHABANG_TERMINAL',
            'company_name': company_name,
            'tax_id': tax_id,
            'date': date,
            'document_number': document_number,  # เลขที่เอกสาร
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number,  # เลขที่ (3)
            'other_info': other_info,  # อื่นๆ (อาคารท่าเทียบเรือพาณิชย์แหลมฉบัง ท่าเทียบเรือตู้สินค้า)
            'soi': soi,  # ซอย/ตรอก
            'road': road,  # ถนน
            'subdistrict': subdistrict,  # ตำบล
            'district': district,  # อำเภอ
            'province': province,  # จังหวัด (ชลบุรี)
            'postal_code': postal_code,  # รหัสไปรษณีย์
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
            'document_type': document_type,  # 1 = มีภาษีมูลค่าเพิ่ม
        }


# ===== Siam Commercial Seaport Extractor =====
class SiamCommercialSeaportExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท สยามคอมเมอร์เชียล ซีพอร์ท จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "สยามคอมเมอร์เชียล ซีพอร์ท",
        "Siam Commercial Seaport"
    ]
    
    def __init__(self):
        """Initialize Siam Commercial Seaport Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Siam Commercial Seaport หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท สยามคอมเมอร์เชียล ซีพอร์ท จำกัด"
        2. Tax ID "0105518012712"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Siam Commercial Seaport (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105518012712"
        has_tax_id = "0105518012712" in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "บริษัท สยามคอมเมอร์เชียล ซีพอร์ท จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษีจาก 'เลขประจำตัวผู้เสียภาษี : 0105518012712'"""
        # Pattern: เลขประจำตัวผู้เสียภาษี : 0105518012712
        patterns = [
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # ถ้าไม่พบ pattern ให้ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่
        if "0105518012712" in text:
            return "0105518012712"
        
        return None
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขาจาก 'สำนักงานสาขา : 00001'"""
        # Pattern: สำนักงานสาขา : 00001
        patterns = [
            r'สำนักงานสาขา\s*[:.]?\s*(\d{5})',
            r'Branch\s*[:.]?\s*(\d{5})',
            r'สาขา\s*[:.]?\s*(\d{5})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่จาก 'Date : 04/11/2025 15:08' และแปลงเป็น dd/mm/yyyy (ตัดเวลาออก)"""
        # Pattern: Date : 04/11/2025 15:08
        patterns = [
            r'Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})(?:\s+\d{1,2}:\d{2})?',  # Date : 04/11/2025 15:08
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})(?:\s+\d{1,2}:\d{2})?',  # วันที่ : 04/11/2025 15:08
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสารจาก 'Receipt No. : SCSP-2025-047338'"""
        # Pattern: Receipt No. : SCSP-2025-047338
        patterns = [
            r'Receipt\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
            r'เลขที่\s*[:.]?\s*([A-Z0-9\-]+)',
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: 113/30 ม.1 ถ.สุขุมวิท กม.123 ต.ทุ่งสุขลา อ.ศรีราชา จ.ชลบุรี 20230
        
        Returns:
            ที่อยู่รวม (string)
        """
        # ใช้ที่อยู่ที่กำหนดให้เลย
        return "113/30 ม.1 ถ.สุขุมวิท กม.123 ต.ทุ่งสุขลา อ.ศรีราชา จ.ชลบุรี 20230"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย (กำหนดเปอร์เซ็นต์เป็น 3%)"""
        return {
            'withholding_tax_percent': 3.0,  # กำหนดเป็น 3%
            'withholding_tax_amount': None  # คำนวณทีหลัง
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลยอดเงิน
        
        - Gross Amount 1,000.00 -> amount_before_vat
        - VAT 7% 70.00 -> vat_amount
        - Total Amount 1,070.00 -> total_amount
        """
        amounts = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # ดึง Gross Amount (ยอดก่อนภาษี)
        gross_patterns = [
            r'Gross\s+Amount\s+([\d,]+\.?\d*)',
            r'รวมเงิน\s+([\d,]+\.?\d*)',
        ]
        for pattern in gross_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amounts['amount_before_vat'] = float(amount_str)
                    break
                except ValueError:
                    pass
        
        # ดึง VAT 7% (ยอดภาษี)
        vat_patterns = [
            r'VAT\s+7%\s+([\d,]+\.?\d*)',
            r'ภาษีมูลค่าเพิ่ม\s+7%\s+([\d,]+\.?\d*)',
            r'ภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d*)',
        ]
        for pattern in vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amounts['vat_amount'] = float(amount_str)
                    break
                except ValueError:
                    pass
        
        # ดึง Total Amount (ยอดรวม)
        total_patterns = [
            r'Total\s+Amount\s+([\d,]+\.?\d*)',
            r'ยอดเงินสุทธิ\s+([\d,]+\.?\d*)',
        ]
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amounts['total_amount'] = float(amount_str)
                    break
                except ValueError:
                    pass
        
        # ถ้าไม่มี total_amount แต่มี amount_before_vat และ vat_amount ให้คำนวณ
        if amounts['total_amount'] is None and amounts['amount_before_vat'] is not None and amounts['vat_amount'] is not None:
            amounts['total_amount'] = amounts['amount_before_vat'] + amounts['vat_amount']
        
        return amounts
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงหมายเหตุ: B/L No. : SZXCB25090716 {ชื่อไฟล์เก่า}
        ตัด VAT_, WHT_, None_vat_ ออกจากชื่อไฟล์
        """
        remark_parts = []
        
        # ดึง B/L No.
        bl_patterns = [
            r'B/L\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',
            r'B\/L\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',
        ]
        for pattern in bl_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bl_no = match.group(1).strip()
                remark_parts.append(f"B/L No. : {bl_no}")
                break
        
        # เพิ่มชื่อไฟล์ (ตัด VAT_, WHT_, None_vat_ ออก)
        if filename:
            filename_clean = filename
            # ตัด VAT_, WHT_, None_vat_ ออก
            filename_clean = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename_clean, flags=re.IGNORECASE)
            # ตัด .pdf ออก
            filename_clean = re.sub(r'\.pdf$', '', filename_clean, flags=re.IGNORECASE)
            if filename_clean:
                remark_parts.append(filename_clean)
        
        if remark_parts:
            return ' '.join(remark_parts)
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร (1 = มีภาษีมูลค่าเพิ่ม)"""
        return 1  # มีภาษีมูลค่าเพิ่ม
    
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
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, None_vat_, WHT_)
        new_filename = filename
        if new_filename:
            new_filename = re.sub(r'(VAT_|None_vat_|WHT_)', '', new_filename, flags=re.IGNORECASE)
        
        # แยกที่อยู่เป็นส่วนๆ
        # ที่อยู่: 113/30 ม.1 ถ.สุขุมวิท กม.123 ต.ทุ่งสุขลา อ.ศรีราชา จ.ชลบุรี 20230
        address_full = address or ''
        building_number = ''
        other_info = ''
        soi = ''  # ซอย/ตรอก
        road = ''
        subdistrict = ''
        district = ''
        province = ''
        postal_code = ''
        
        if address:
            # ดึงเลขที่จาก "113/30" (อยู่ต้นที่อยู่)
            building_match = re.search(r'^(\d+(?:/\d+)?)', address.strip())
            if building_match:
                building_number = building_match.group(1).strip()
            
            # ดึงอื่นๆ จาก "ม.1"
            moo_match = re.search(r'ม\.(\d+)', address)
            if moo_match:
                other_info = f"ม.{moo_match.group(1)}"
            
            # ดึงถนนจาก "ถ.สุขุมวิท กม.123"
            # หาชื่อถนนจาก "ถ.สุขุมวิท"
            road_name_match = re.search(r'ถ\.([ก-๙A-Za-z]+)', address)
            if road_name_match:
                road_name = road_name_match.group(1).strip()
                # หา "กม.123" ถ้ามี
                km_match = re.search(r'กม\.(\d+)', address)
                if km_match:
                    road = f"ถนน{road_name} กม.{km_match.group(1)}"
                else:
                    road = f"ถนน{road_name}"
            
            # ดึงตำบลจาก "ต.ทุ่งสุขลา"
            subdistrict_match = re.search(r'ต\.([ก-๙A-Za-z]+?)(?:\s+อ\.|จ\.|\d{5}|$)', address)
            if subdistrict_match:
                subdistrict = subdistrict_match.group(1).strip()
            
            # ดึงอำเภอจาก "อ.ศรีราชา"
            district_match = re.search(r'อ\.([ก-๙A-Za-z]+?)(?:\s+จ\.|\d{5}|$)', address)
            if district_match:
                district = district_match.group(1).strip()
            
            # ดึงจังหวัดจาก "จ.ชลบุรี"
            province_match = re.search(r'จ\.(ชลบุรี)', address)
            if province_match:
                province = province_match.group(1).strip()
            
            # ดึงรหัสไปรษณีย์ (5 หลัก)
            postal_match = re.search(r'(\d{5})\s*$', address)
            if postal_match:
                postal_code = postal_match.group(1).strip()
        
        return {
            'success': True,
            'company': 'SIAM_COMMERCIAL_SEAPORT',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,  # สาขา
            'date': date,
            'document_number': document_number,
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number,  # เลขที่ (113/30)
            'other_info': other_info,  # อื่นๆ (ม.1)
            'soi': soi,  # ซอย/ตรอก
            'road': road,  # ถนน (ถนนสุขุมวิท กม.123)
            'subdistrict': subdistrict,  # ตำบล (ทุ่งสุขลา)
            'district': district,  # อำเภอ (ศรีราชา)
            'province': province,  # จังหวัด (ชลบุรี)
            'postal_code': postal_code,  # รหัสไปรษณีย์ (20230)
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
            'document_type': document_type,  # 1 = มีภาษีมูลค่าเพิ่ม
        }


# ===== LCMT Extractor =====
class LCMTExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท แอล ซี เอ็ม ที จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "แอล ซี เอ็ม ที",
        "LCMT"
    ]
    
    def __init__(self):
        """Initialize LCMT Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ LCMT หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท แอล ซี เอ็ม ที จำกัด"
        2. Tax ID "0115547010161"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร LCMT (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0115547010161"
        has_tax_id = "0115547010161" in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "บริษัท แอล ซี เอ็ม ที จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษีจาก 'TAX ID 0115547010161'"""
        # Pattern: TAX ID 0115547010161
        patterns = [
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # ถ้าไม่พบ pattern ให้ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่
        if "0115547010161" in text:
            return "0115547010161"
        
        return None
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา (ถ้ามี)"""
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่จาก 'Date: 10/11/2025' และแปลงเป็น dd/mm/yyyy"""
        # Pattern: Date: 10/11/2025 หรือ วัน เดือน ปี Date: 10/11/2025
        patterns = [
            r'Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'วัน\s*เดือน\s*ปี\s*Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสารจาก 'เอกสารเลขที่ RC250247949'"""
        # Pattern: เอกสารเลขที่ RC250247949
        patterns = [
            r'เอกสารเลขที่\s*([A-Z0-9]+)',
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: ทำเรือแหลมฉบัง ท่าเทียบเรือ เอ0 ถนน สุขุมวิท ตำบล ทุ่งสุขลา อำเภอ ศรีราชา จังหวัด ชลบุรี 20230
        
        Returns:
            ที่อยู่รวม (string)
        """
        # ใช้ที่อยู่ที่กำหนดให้เลย
        return "ทำเรือแหลมฉบัง ท่าเทียบเรือ เอ0 ถนน สุขุมวิท ตำบล ทุ่งสุขลา อำเภอ ศรีราชา จังหวัด ชลบุรี 20230"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย (กำหนดเปอร์เซ็นต์เป็น 3%)"""
        return {
            'withholding_tax_percent': 3.0,  # กำหนดเป็น 3%
            'withholding_tax_amount': None  # คำนวณทีหลัง
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลยอดเงิน
        
        - Total Charge: | 1,250.00 -> amount_before_vat
        - Value Added Tax: | 87.50 -> vat_amount
        - Grand Total: | 1,337.50 -> total_amount
        """
        amounts = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # ดึง Total Charge (ยอดก่อนภาษี)
        total_charge_patterns = [
            r'Total\s+Charge\s*[:|]\s*([\d,]+\.?\d*)',
            r'รวมราคาทั้งสิ้น\s*[:|]\s*([\d,]+\.?\d*)',
            r'DVรวมราคาทั้งสิ้น\s*/\s*Total\s+Charge\s*[:|]\s*([\d,]+\.?\d*)',
        ]
        for pattern in total_charge_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amounts['amount_before_vat'] = float(amount_str)
                    break
                except ValueError:
                    pass
        
        # ดึง Value Added Tax (ยอดภาษี)
        vat_patterns = [
            r'Value\s+Added\s+Tax\s*[:|]\s*([\d,]+\.?\d*)',
            r'จำนวนภาษีมูลค่าเพิ่ม\s*[:|]\s*([\d,]+\.?\d*)',
            r'ภาษีมูลค่าเพิ่ม\s*[:|]\s*([\d,]+\.?\d*)',
        ]
        for pattern in vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amounts['vat_amount'] = float(amount_str)
                    break
                except ValueError:
                    pass
        
        # ดึง Grand Total (ยอดรวม)
        grand_total_patterns = [
            r'Grand\s+Total\s*[:|]\s*([\d,]+\.?\d*)',
            r'รวมเงินทั้งสิ้น\s*[:|]\s*([\d,]+\.?\d*)',
            r'ยอดเงินสุทธิ\s*[:|]\s*([\d,]+\.?\d*)',
        ]
        for pattern in grand_total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amounts['total_amount'] = float(amount_str)
                    break
                except ValueError:
                    pass
        
        # ถ้าไม่มี total_amount แต่มี amount_before_vat และ vat_amount ให้คำนวณ
        if amounts['total_amount'] is None and amounts['amount_before_vat'] is not None and amounts['vat_amount'] is not None:
            amounts['total_amount'] = amounts['amount_before_vat'] + amounts['vat_amount']
        
        return amounts
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงหมายเหตุ: Ref. Invoice No.: IC250249029 B/L No.: 260701300 {ชื่อไฟล์เก่า}
        ตัด WHT_, VAT_, None_vat_ ออกจากชื่อไฟล์
        """
        remark_parts = []
        
        # ดึง Ref. Invoice No.
        invoice_patterns = [
            r'Ref\.\s*Invoice\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',
            r'Invoice\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',
        ]
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_no = match.group(1).strip()
                remark_parts.append(f"Ref. Invoice No.: {invoice_no}")
                break
        
        # ดึง B/L No.
        bl_patterns = [
            r'B/L\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',
            r'B\/L\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',
        ]
        for pattern in bl_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bl_no = match.group(1).strip()
                remark_parts.append(f"B/L No.: {bl_no}")
                break
        
        # เพิ่มชื่อไฟล์ (ตัด WHT_, VAT_, None_vat_ ออก)
        if filename:
            filename_clean = filename
            # ตัด WHT_, VAT_, None_vat_ ออก
            filename_clean = re.sub(r'(WHT_|VAT_|None_vat_)', '', filename_clean, flags=re.IGNORECASE)
            # ตัด .pdf ออก
            filename_clean = re.sub(r'\.pdf$', '', filename_clean, flags=re.IGNORECASE)
            if filename_clean:
                remark_parts.append(filename_clean)
        
        if remark_parts:
            return ' '.join(remark_parts)
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร (1 = มีภาษีมูลค่าเพิ่ม)"""
        return 1  # มีภาษีมูลค่าเพิ่ม
    
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
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, None_vat_, WHT_)
        new_filename = filename
        if new_filename:
            new_filename = re.sub(r'(VAT_|None_vat_|WHT_)', '', new_filename, flags=re.IGNORECASE)
        
        # แยกที่อยู่เป็นส่วนๆ
        # ที่อยู่: ทำเรือแหลมฉบัง ท่าเทียบเรือ เอ0 ถนน สุขุมวิท ตำบล ทุ่งสุขลา อำเภอ ศรีราชา จังหวัด ชลบุรี 20230
        address_full = address or ''
        building_number = ''  # เลขที่ว่าง
        other_info = 'ทำเรือแหลมฉบัง ท่าเทียบเรือ เอ0 ถนน สุขุมวิท'  # อื่นๆ
        soi = ''  # ซอย/ตรอก
        road = ''  # ถนน (ว่างเพราะรวมอยู่ใน other_info แล้ว)
        subdistrict = 'ทุ่งสุขลา'  # ตำบล
        district = 'ศรีราชา'  # อำเภอ
        province = 'ชลบุรี'  # จังหวัด
        postal_code = '20230'  # รหัสไปรษณีย์
        
        # ถ้ามีที่อยู่ ให้ parse จากที่อยู่จริง
        if address:
            # ดึงตำบล
            subdistrict_match = re.search(r'ตำบล\s*([ก-๙A-Za-z]+)', address)
            if subdistrict_match:
                subdistrict = subdistrict_match.group(1).strip()
            
            # ดึงอำเภอ
            district_match = re.search(r'อำเภอ\s*([ก-๙A-Za-z]+)', address)
            if district_match:
                district = district_match.group(1).strip()
            
            # ดึงจังหวัด
            province_match = re.search(r'จังหวัด\s*(ชลบุรี)', address)
            if province_match:
                province = province_match.group(1).strip()
            
            # ดึงรหัสไปรษณีย์
            postal_match = re.search(r'(\d{5})\s*$', address)
            if postal_match:
                postal_code = postal_match.group(1).strip()
            
            # ดึงอื่นๆ = "ทำเรือแหลมฉบัง ท่าเทียบเรือ เอ0 ถนน สุขุมวิท"
            # หาส่วนที่อยู่ก่อน "ตำบล"
            other_match = re.search(r'^(.+?)(?=\s+ตำบล)', address)
            if other_match:
                other_info = other_match.group(1).strip()
        
        return {
            'success': True,
            'company': 'LCMT',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number,  # เลขที่ (ว่าง)
            'other_info': other_info,  # อื่นๆ (ทำเรือแหลมฉบัง ท่าเทียบเรือ เอ0 ถนน สุขุมวิท)
            'soi': soi,  # ซอย/ตรอก
            'road': road,  # ถนน (ว่าง)
            'subdistrict': subdistrict,  # ตำบล (ทุ่งสุขลา)
            'district': district,  # อำเภอ (ศรีราชา)
            'province': province,  # จังหวัด (ชลบุรี)
            'postal_code': postal_code,  # รหัสไปรษณีย์ (20230)
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
            'document_type': document_type,  # 1 = มีภาษีมูลค่าเพิ่ม
        }


# ===== Ngow Hok Extractor =====
class NgowHokExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท โงวฮก จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "โงวฮก",
        "Ngow Hok"
    ]
    
    def __init__(self):
        """Initialize Ngow Hok Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Ngow Hok หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท โงวฮก จำกัด"
        2. Tax ID "0105472000024"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Ngow Hok (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105472000024"
        has_tax_id = "0105472000024" in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "บริษัท โงวฮก จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษีจาก 'เลขประจำตัวผู้เสียภาษี 0105472000024'"""
        # Pattern: เลขประจำตัวผู้เสียภาษี 0105472000024
        patterns = [
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # ถ้าไม่พบ pattern ให้ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่
        if "0105472000024" in text:
            return "0105472000024"
        
        return None
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขาจาก 'สาขา 00004'"""
        # Pattern: สาขา 00004
        patterns = [
            r'สาขา\s*[:.]?\s*(\d{5})',
            r'Branch\s*[:.]?\s*(\d{5})',
            r'สำนักงานสาขา\s*[:.]?\s*(\d{5})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่จาก 'วันที่ DATE 31/10/2025' และแปลงเป็น dd/mm/yyyy"""
        # Pattern: วันที่ DATE 31/10/2025
        patterns = [
            r'วันที่\s+DATE\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'DATE\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสารจาก 'เลขที่ NO. N-B25103946'"""
        # Pattern: เลขที่ NO. N-B25103946
        patterns = [
            r'เลขที่\s+NO[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
            r'NO[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: 127/1 ถนนรัชดาภิเษก แขวงอ่อนนุช เขตยานนาวา กรุงเทพฯ 10120
        
        Returns:
            ที่อยู่รวม (string)
        """
        # ลองหาที่อยู่จาก text ก่อน (มักจะอยู่ในส่วนสาขา)
        lines = text.split('\n')
        address_lines = []
        collecting = False
        
        # หาตำแหน่งที่เริ่มต้นที่อยู่ (มักจะอยู่หลังสาขา)
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # หา "สาขา" หรือ "โงวฮก" แล้วเก็บบรรทัดถัดไปที่เป็นที่อยู่
            if ('โงวฮก' in line_clean and 'บริษัท' in line_clean) or ('สาขา' in line_clean and 'อาคาร' in line_clean):
                collecting = True
                continue
            
            # ถ้ากำลังเก็บข้อมูลที่อยู่
            if collecting:
                # หยุดเมื่อเจอ TaxID, Tax ID, เลขประจำตัวผู้เสียภาษี, หรือ header อื่นๆ
                if any(keyword in line_clean for keyword in ['TaxID', 'Tax ID', 'เลขประจำตัวผู้เสียภาษี', 'ใบเสร็จ', 'ใบกำกับ', 'DATE', 'NO.']):
                    break
                
                # เก็บบรรทัดที่มีข้อมูล (ไม่ใช่บรรทัดว่าง และมีความยาวมากกว่า 15 ตัวอักษร)
                if line_clean and len(line_clean) > 15:
                    # ตรวจสอบว่ามีรูปแบบที่อยู่ (มี "ถนน", "แขวง", "เขต", "กรุงเทพ", หรือรหัสไปรษณีย์ 5 หลัก)
                    if any(keyword in line_clean for keyword in ['ถนน', 'แขวง', 'เขต', 'กรุงเทพ', '10120', '127/1']):
                        # ลบส่วนที่ไม่ใช่ที่อยู่ (เช่น โทร., แฟกซ์)
                        line_clean = re.sub(r'\s*(โทร\.|แฟกซ์\.|Fax\.|Tel\.).*$', '', line_clean, flags=re.IGNORECASE)
                        address_lines.append(line_clean.strip())
                        break  # หาได้แล้ว ให้หยุด
        
        # รวมที่อยู่ทั้งหมด
        if address_lines:
            address = ' '.join(address_lines).strip()
            # ทำความสะอาด: ลบ space หลายตัว
            address = re.sub(r'\s+', ' ', address)
            if len(address) > 15:
                return address
        
        # Fallback: ใช้ที่อยู่ default
        return "127/1 ถนนรัชดาภิเษก แขวงอ่อนนุช เขตยานนาวา กรุงเทพฯ 10120"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': None,
            'withholding_tax_amount': None
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลยอดเงิน
        
        - Net Total: 600.00 -> amount_before_vat
        - ภาษีมูลค่าเพิ่ม 7%: 42.00 -> vat_amount
        - Grand Total: 642.00 -> total_amount
        """
        amounts = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # ดึง Net Total (ยอดก่อนภาษี)
        net_total_patterns = [
            r'Net\s+Total\s*[:.]?\s*([\d,]+\.?\d*)',
            r'รวมราคา\s+Net\s+Total\s*[:.]?\s*([\d,]+\.?\d*)',
            r'รวมราคา\s*[:.]?\s*([\d,]+\.?\d*)',
        ]
        for pattern in net_total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amounts['amount_before_vat'] = float(amount_str)
                    break
                except ValueError:
                    pass
        
        # ดึงภาษีมูลค่าเพิ่ม 7% (ยอดภาษี)
        vat_patterns = [
            r'ภาษีมูลค่าเพิ่ม\s+7%\s*[:.]?\s*([\d,]+\.?\d*)',
            r'VAT\s+7%\s*[:.]?\s*([\d,]+\.?\d*)',
            r'ภาษีมูลค่าเพิ่ม\s*[:.]?\s*([\d,]+\.?\d*)',
        ]
        for pattern in vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amounts['vat_amount'] = float(amount_str)
                    break
                except ValueError:
                    pass
        
        # ดึง Grand Total (ยอดรวม)
        grand_total_patterns = [
            r'Grand\s+Total\s*[:.]?\s*([\d,]+\.?\d*)',
            r'จำนวนเงินรวมทั้งสิ้น\s+Grand\s+Total\s*[:.]?\s*([\d,]+\.?\d*)',
            r'จำนวนเงินรวมทั้งสิ้น\s*[:.]?\s*([\d,]+\.?\d*)',
        ]
        for pattern in grand_total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amounts['total_amount'] = float(amount_str)
                    break
                except ValueError:
                    pass
        
        # ถ้าไม่มี total_amount แต่มี amount_before_vat และ vat_amount ให้คำนวณ
        if amounts['total_amount'] is None and amounts['amount_before_vat'] is not None and amounts['vat_amount'] is not None:
            amounts['total_amount'] = amounts['amount_before_vat'] + amounts['vat_amount']
        
        return amounts
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงหมายเหตุ: B/L SZXGC25090716 {ชื่อไฟล์เก่า}
        อ่านข้อมูลจากบรรทัดที่มี "เลขที่เอกสาร / REF. No. | รายการ / Description | จำนวนเงิน / Amount"
        แล้วตามด้วย "ICN25103563 SZXGC25090716 | CLEANING SERVICES | 600.00"
        """
        remark_parts = []
        
        # หาบรรทัดที่มี "เลขที่เอกสาร / REF. No." หรือ "REF. No."
        lines = text.split('\n')
        bl_no = None
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # หาบรรทัดที่มี header "เลขที่เอกสาร / REF. No." หรือ "REF. No."
            if 'เลขที่เอกสาร' in line_clean and 'REF. No.' in line_clean:
                # ดูบรรทัดถัดไป
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # ตัวอย่าง: "ICN25103563 SZXGC25090716 | CLEANING SERVICES | 600.00"
                    # ดึงส่วนก่อน | (ส่วนแรก)
                    if '|' in next_line:
                        first_part = next_line.split('|')[0].strip()
                        # แยกด้วย space และหา B/L No. (ตัวที่ 2 หลังเลขที่เอกสาร)
                        parts = first_part.split()
                        if len(parts) >= 2:
                            # ตัวที่ 2 น่าจะเป็น B/L No. (เช่น SZXGC25090716)
                            candidate = parts[1]
                            # ตรวจสอบว่าเป็นรูปแบบ B/L No. (ตัวอักษร + ตัวเลข)
                            if re.match(r'^[A-Z]{2,}[0-9]{6,}$', candidate):
                                bl_no = candidate
                                break
                    
                    # ถ้ายังไม่เจอ ลองหาจาก pattern ทั่วไปในบรรทัดถัดไป
                    if not bl_no:
                        # หา B/L No. ที่เป็นตัวอักษรและตัวเลข (เช่น SZXGC25090716)
                        # หาทุกตัวที่ match pattern แล้วเลือกตัวที่ยาวที่สุด (เพราะ B/L No. มักจะยาว)
                        all_matches = re.findall(r'\b([A-Z]{3,}[0-9]{8,})\b', next_line)
                        if all_matches:
                            bl_no = max(all_matches, key=len)
                            break
            
            # หรือหาจากบรรทัดที่มี | และมีรูปแบบ "ICN25103563 SZXGC25090716 |"
            if not bl_no and '|' in line_clean and 'เลขที่เอกสาร' not in line_clean:
                # หา pattern ที่มีตัวอักษรและตัวเลขคั่นด้วย space ก่อน |
                parts = line_clean.split('|')
                if len(parts) > 0:
                    first_part = parts[0].strip()
                    # แยกด้วย space และหา B/L No. (ตัวที่ 2)
                    words = first_part.split()
                    if len(words) >= 2:
                        candidate = words[1]
                        if re.match(r'^[A-Z]{2,}[0-9]{6,}$', candidate):
                            bl_no = candidate
                            break
        
        # ถ้ายังไม่เจอ ลองหาจาก pattern ทั่วไปใน text ทั้งหมด
        if not bl_no:
            # หา pattern ที่เป็น B/L No. format (ตัวอักษร 3-10 ตัว + ตัวเลข 8-12 ตัว)
            bl_patterns = [
                r'\b([A-Z]{3,}[0-9]{8,})\b',  # SZXGC25090716
                r'B/L\s*No[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # B/L No: SZXGC25090716
            ]
            for pattern in bl_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # เลือกตัวที่ยาวที่สุด (เพราะ B/L No. มักจะยาวกว่า)
                    bl_no = max(matches, key=len)
                    break
        
        # เพิ่ม B/L No. ใน remark
        if bl_no:
            remark_parts.append(f"B/L {bl_no}")
        
        # เพิ่มชื่อไฟล์ (ตัด WHT_, VAT_, None_vat_ ออก)
        if filename:
            filename_clean = filename
            # ตัด WHT_, VAT_, None_vat_ ออก
            filename_clean = re.sub(r'(WHT_|VAT_|None_vat_)', '', filename_clean, flags=re.IGNORECASE)
            # ตัด .pdf ออก
            filename_clean = re.sub(r'\.pdf$', '', filename_clean, flags=re.IGNORECASE)
            if filename_clean:
                remark_parts.append(filename_clean)
        
        if remark_parts:
            return ' '.join(remark_parts)
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร (1 = มีภาษีมูลค่าเพิ่ม)"""
        return 1  # มีภาษีมูลค่าเพิ่ม
    
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
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, None_vat_, WHT_)
        new_filename = filename
        if new_filename:
            new_filename = re.sub(r'(VAT_|None_vat_|WHT_)', '', new_filename, flags=re.IGNORECASE)
        
        # แยกที่อยู่เป็นส่วนๆ
        # ที่อยู่: 127/1 ถนนรัชดาภิเษก แขวงอ่อนนุช เขตยานนาวา กรุงเทพฯ 10120
        address_full = address or ''
        building_number = ''
        other_info = ''
        soi = ''
        road = ''
        subdistrict = ''
        district = ''
        province = ''
        postal_code = ''
        
        if address:
            # ดึงเลขที่จาก "127/1" (อยู่ต้นที่อยู่)
            building_match = re.search(r'^(\d+(?:/\d+)?)', address.strip())
            if building_match:
                building_number = building_match.group(1).strip()
            
            # ดึงถนนจาก "ถนนรัชดาภิเษก"
            road_match = re.search(r'ถนน\s*([ก-๙A-Za-z]+)', address)
            if road_match:
                road = f"ถนน{road_match.group(1)}"
            
            # ดึงแขวงจาก "แขวงอ่อนนุช"
            subdistrict_match = re.search(r'แขวง\s*([ก-๙A-Za-z]+)', address)
            if subdistrict_match:
                subdistrict = subdistrict_match.group(1).strip()
            
            # ดึงเขตจาก "เขตยานนาวา"
            district_match = re.search(r'เขต\s*([ก-๙A-Za-z]+)', address)
            if district_match:
                district = district_match.group(1).strip()
            
            # ดึงจังหวัดจาก "กรุงเทพฯ" หรือ "กรุงเทพมหานคร"
            if 'กรุงเทพ' in address:
                province = 'กรุงเทพมหานคร'
            
            # ดึงรหัสไปรษณีย์
            postal_match = re.search(r'(\d{5})\s*$', address)
            if postal_match:
                postal_code = postal_match.group(1).strip()
        
        return {
            'success': True,
            'company': 'NGOW_HOK',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number,  # เลขที่ (127/1)
            'other_info': other_info,  # อื่นๆ (ว่าง)
            'soi': soi,  # ซอย/ตรอก
            'road': road,  # ถนน (ถนนรัชดาภิเษก)
            'subdistrict': subdistrict,  # แขวง (อ่อนนุช)
            'district': district,  # เขต (ยานนาวา)
            'province': province,  # จังหวัด (กรุงเทพมหานคร)
            'postal_code': postal_code,  # รหัสไปรษณีย์ (10120)
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
            'document_type': document_type,  # 1 = มีภาษีมูลค่าเพิ่ม
        }


# ===== TIPS Extractor =====
class TIPSExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท ที ไอ พี เอส จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "ที ไอ พี เอส",
        "TIPS",
        "T I P S"
    ]
    
    def __init__(self):
        """Initialize TIPS Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ TIPS หรือไม่
        ตรวจสอบจากชื่อบริษัทและรูปแบบเอกสารเฉพาะ
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร TIPS
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท "ที ไอ พี เอส" หรือ "TIPS"
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมีรูปแบบเอกสารเฉพาะ เช่น "TIPS CO . LTD." หรือ "Receipt /Tax Invoice No."
        has_specific_format = (
            "TIPS CO" in text or 
            "Receipt /Tax Invoice No" in text or
            "LAEM CHABANG PORT" in text
        )
        
        # ต้องมีทั้งชื่อบริษัทและรูปแบบเอกสารเฉพาะถึงจะผ่าน
        return has_company and has_specific_format
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "บริษัท ที ไอ พี เอส จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี (กำหนดให้ระบบกรอกให้เองอัตโนมัติ)"""
        return "0105532051576"
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา (กำหนดให้ระบบกรอกให้เองอัตโนมัติ)"""
        return "00001"
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่จาก 'วันที่ Date 13.11.2025' และแปลงเป็น dd/mm/yyyy (เช่น 13/11/2025)"""
        # Pattern: วันที่ Date 13.11.2025
        patterns = [
            r'วันที่\s+Date\s*[:.]?\s*(\d{1,2})\.(\d{1,2})\.(\d{4})',  # วันที่ Date 13.11.2025
            r'วันที่\s*[:.]?\s*(\d{1,2})\.(\d{1,2})\.(\d{4})',  # วันที่ 13.11.2025
            r'Date\s*[:.]?\s*(\d{1,2})\.(\d{1,2})\.(\d{4})',  # Date 13.11.2025
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสารจาก 'Receipt /Tax Invoice No. : CS14251108486'"""
        # Pattern: Receipt /Tax Invoice No. : CS14251108486
        patterns = [
            r'Receipt\s*/?\s*Tax\s+Invoice\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
            r'Receipt\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
            r'Invoice\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
            r'เลขที่\s*[:.]?\s*([A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_no = match.group(1).strip()
                if doc_no:
                    return doc_no
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท (กำหนดให้ระบบกรอกให้เองอัตโนมัติ)
        
        ที่อยู่: ซอยท่าบี 4 ท่าเรือแหลมฉบัง ตำบลทุ่งสุขลา อำเภอศรีราชา จ.ชลบุรี 20230
        
        Returns:
            ที่อยู่รวม (string)
        """
        return "ซอยท่าบี 4 ท่าเรือแหลมฉบัง ตำบลทุ่งสุขลา อำเภอศรีราชา จ.ชลบุรี 20230"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': None,
            'withholding_tax_amount': None
        }
    
    def _extract_from_html_table(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลจากตาราง HTML โดยค้นหา Total After Disc, VAT, และ Grand Total
        
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
                    
                    # หา Total After Disc
                    if 'TOTAL' in row_upper and 'AFTER' in row_upper and 'DISC' in row_upper and not result['amount_before_vat']:
                        # หาตัวเลขใน cell สุดท้าย
                        last_cell = cleaned_cells[-1].strip()
                        amount_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_cell)
                        if amount_match:
                            try:
                                result['amount_before_vat'] = float(amount_match.group(1).replace(',', ''))
                            except ValueError:
                                pass
                    
                    # หา VAT
                    if 'VAT' in row_upper and not result['vat_amount']:
                        # หาตัวเลขใน cell สุดท้าย
                        last_cell = cleaned_cells[-1].strip()
                        vat_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_cell)
                        if vat_match:
                            try:
                                result['vat_amount'] = float(vat_match.group(1).replace(',', ''))
                            except ValueError:
                                pass
                    
                    # หา Grand Total
                    if 'GRAND' in row_upper and 'TOTAL' in row_upper and not result['total_amount']:
                        # หาตัวเลขใน cell สุดท้าย
                        last_cell = cleaned_cells[-1].strip()
                        total_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_cell)
                        if total_match:
                            try:
                                result['total_amount'] = float(total_match.group(1).replace(',', ''))
                            except ValueError:
                                pass
                
                # ถ้าได้ข้อมูลครบแล้ว ให้ return
                if result['amount_before_vat'] and result['vat_amount'] and result['total_amount']:
                    logger.info(f"✅ ดึงยอดเงินจากตาราง HTML สำเร็จ: amount_before_vat={result['amount_before_vat']}, vat_amount={result['vat_amount']}, total_amount={result['total_amount']}")
                    return result
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงข้อมูลจากตาราง HTML: {e}")
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลยอดเงิน
        
        - ยอดก่อนภาษีมูลค่าเพิ่ม: Total After Disc 1,000.00
        - ภาษีมูลค่าเพิ่ม: VAT 70.00
        - ยอดหลังบวกภาษีมูลค่าเพิ่ม: Grand Total 1,070.00
        """
        amounts = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # วิธีที่ 0: ลองดึงจาก HTML table ก่อน (ถ้าหน้าเว็บอ่านได้)
        html_table_result = self._extract_from_html_table(text)
        if html_table_result.get('amount_before_vat') or html_table_result.get('vat_amount') or html_table_result.get('total_amount'):
            amounts.update(html_table_result)
            # ถ้าได้ข้อมูลครบแล้ว ให้ return
            if amounts['amount_before_vat'] and amounts['vat_amount'] and amounts['total_amount']:
                return amounts
        
        # ยอดก่อนภาษีมูลค่าเพิ่ม: Total After Disc 1,000.00
        amount_patterns = [
            r'Total\s+After\s+Disc\s+([\d,]+\.?\d*)',
            r'Total\s+After\s+Discount\s+([\d,]+\.?\d*)',
            r'Total\s+([\d,]+\.?\d*)',
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    amount_val = float(amount_str)
                    if amount_val > 0:
                        amounts['amount_before_vat'] = amount_val
                        break
                except ValueError:
                    pass
        
        # ภาษีมูลค่าเพิ่ม: VAT 70.00
        vat_patterns = [
            r'VAT\s+([\d,]+\.?\d*)',
            r'ภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d*)',
            r'VAT\s+7%\s+([\d,]+\.?\d*)',
        ]
        for pattern in vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vat_str = match.group(1).replace(',', '').strip()
                try:
                    vat_val = float(vat_str)
                    if vat_val > 0:
                        amounts['vat_amount'] = vat_val
                        break
                except ValueError:
                    pass
        
        # ยอดหลังบวกภาษีมูลค่าเพิ่ม: Grand Total 1,070.00
        total_patterns = [
            r'Grand\s+Total\s+([\d,]+\.?\d*)',
            r'GRAND\s+TOTAL\s+([\d,]+\.?\d*)',
            r'Total\s+Amount\s+([\d,]+\.?\d*)',
        ]
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                total_str = match.group(1).replace(',', '').strip()
                try:
                    total_val = float(total_str)
                    if total_val > 0:
                        amounts['total_amount'] = total_val
                        break
                except ValueError:
                    pass
        
        return amounts
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (ถ้ามี)"""
        remark_parts = []
        
        # เพิ่มชื่อไฟล์ (ตัด WHT_, VAT_, None_vat_ ออก)
        if filename:
            filename_clean = filename
            filename_clean = re.sub(r'(WHT_|VAT_|None_vat_)', '', filename_clean, flags=re.IGNORECASE)
            filename_clean = re.sub(r'\.pdf$', '', filename_clean, flags=re.IGNORECASE)
            if filename_clean:
                remark_parts.append(filename_clean)
        
        if remark_parts:
            return ' '.join(remark_parts)
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร (1 = มีภาษีมูลค่าเพิ่ม)"""
        return 1  # มีภาษีมูลค่าเพิ่ม
    
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
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, None_vat_, WHT_)
        new_filename = filename
        if new_filename:
            new_filename = re.sub(r'(VAT_|None_vat_|WHT_)', '', new_filename, flags=re.IGNORECASE)
        
        # แยกที่อยู่เป็นส่วนๆ
        # ที่อยู่: ซอยท่าบี 4 ท่าเรือแหลมฉบัง ตำบลทุ่งสุขลา อำเภอศรีราชา จ.ชลบุรี 20230
        address_full = address or ''
        building_number = ''  # (ว่าง)
        other_info = ''  # ซอยท่าบี 4 ท่าเรือแหลมฉบัง
        soi = ''  # ซอย/ตรอก
        road = ''  # (ว่าง)
        subdistrict = ''  # ตำบลทุ่งสุขลา
        district = ''  # อำเภอศรีราชา
        province = ''  # จังหวัดชลบุรี
        postal_code = ''  # รหัสไปรษณีย์ 20230
        
        if address:
            # ดึงอื่นๆ จาก "ซอยท่าบี 4 ท่าเรือแหลมฉบัง" (ก่อนตำบล)
            other_match = re.search(r'^(.+?)(?=\s+ตำบล)', address)
            if other_match:
                other_info = other_match.group(1).strip()
            
            # ดึงตำบลจาก "ตำบลทุ่งสุขลา"
            subdistrict_match = re.search(r'ตำบล\s*([ก-๙A-Za-z]+)', address)
            if subdistrict_match:
                subdistrict = subdistrict_match.group(1).strip()
            
            # ดึงอำเภอจาก "อำเภอศรีราชา"
            district_match = re.search(r'อำเภอ\s*([ก-๙A-Za-z]+)', address)
            if district_match:
                district = district_match.group(1).strip()
            
            # ดึงจังหวัดจาก "จ.ชลบุรี" หรือ "ชลบุรี"
            province_match = re.search(r'จ\.?\s*(ชลบุรี)', address)
            if province_match:
                province = province_match.group(1).strip()
            elif 'ชลบุรี' in address:
                province = 'ชลบุรี'
            
            # ดึงรหัสไปรษณีย์ (5 หลัก)
            postal_match = re.search(r'(\d{5})\s*$', address)
            if postal_match:
                postal_code = postal_match.group(1).strip()
        
        return {
            'success': True,
            'company': 'TIPS',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number or '',  # เลขที่ (ว่าง)
            'other_info': other_info or '',  # อื่นๆ (ซอยท่าบี 4 ท่าเรือแหลมฉบัง)
            'soi': soi or '',  # ซอย/ตรอก
            'road': road or '',  # ถนน (ว่าง)
            'subdistrict': subdistrict or '',  # ตำบล (ทุ่งสุขลา)
            'district': district or '',  # อำเภอ (ศรีราชา)
            'province': province or '',  # จังหวัด (ชลบุรี)
            'postal_code': postal_code or '',  # รหัสไปรษณีย์ (20230)
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
            'document_type': document_type,  # 1 = มีภาษีมูลค่าเพิ่ม
        }


# ===== CK Line (Thailand) Extractor =====
class CKLineThailandExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท ซีเค ไลน์ (ประเทศไทย) จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "ซีเค ไลน์",
        "CK Line",
        "CK LINE"
    ]
    
    def __init__(self):
        """Initialize CK Line (Thailand) Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ CK Line (Thailand) หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท ซีเค ไลน์ (ประเทศไทย) จำกัด"
        2. Tax ID "0105554036049"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร CK Line (Thailand) (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105554036049"
        has_tax_id = "0105554036049" in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "บริษัท ซีเค ไลน์ (ประเทศไทย) จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษีจาก 'เลขประจำตัวผู้เสียภาษีอากร 0105554036049'"""
        # Pattern: เลขประจำตัวผู้เสียภาษีอากร 0105554036049
        patterns = [
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # ถ้าไม่พบ pattern ให้ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่
        if "0105554036049" in text:
            return "0105554036049"
        
        return None
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา (ถ้ามี)"""
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่จาก 'วันที่ Date 07/11/2025' และแปลงเป็น dd/mm/yyyy"""
        # Pattern: วันที่ Date 07/11/2025
        patterns = [
            r'วันที่\s+Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสารจาก 'เลขที่ CKTRT25110387'"""
        # Pattern: เลขที่ CKTRT25110387
        patterns = [
            r'เลขที่\s*[:.]?\s*([A-Z0-9\-]+)',
            r'เลขที่เอกสาร\s*[:.]?\s*([A-Z0-9\-]+)',
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_no = match.group(1).strip()
                if doc_no:
                    return doc_no
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: 628 ชั้น 3 อาคารทริปเพลสไอ ซอยกลับเข็ม ถนนนนทรี แขวงช่องนนทรี เขตยานนาวา กรุงเทพฯ 10120
        
        Returns:
            ที่อยู่รวม (string)
        """
        # หาที่อยู่จาก text
        lines = text.split('\n')
        address_lines = []
        
        # หาตำแหน่งที่เริ่มต้นที่อยู่
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # หา keyword ที่เกี่ยวข้องกับที่อยู่
            if any(keyword in line_clean for keyword in ['628', 'อาคารทริปเพลสไอ', 'ถนนนนทรี', 'แขวงช่องนนทรี', 'เขตยานนาวา', 'กรุงเทพฯ 10120']):
                # ลบข้อมูลที่ไม่จำเป็น
                line_clean = re.sub(r'\s*(โทร\.|แฟกซ์\.|Fax\.|Tel\.).*$', '', line_clean, flags=re.IGNORECASE)
                address_lines.append(line_clean)
                break
            
            # ถ้ามี keyword ที่เกี่ยวข้อง
            if any(keyword in line_clean for keyword in ['628', 'อาคาร', 'ถนนนนทรี', 'กรุงเทพ', '10120']):
                # ตรวจสอบว่ามีรูปแบบที่อยู่ (มีเลขที่, ถนน, แขวง, เขต)
                if re.search(r'\d{3}', line_clean) and ('ถนน' in line_clean or 'แขวง' in line_clean or 'เขต' in line_clean):
                    address_lines.append(line_clean)
                    break
        
        # รวมที่อยู่ทั้งหมด
        if address_lines:
            address = ' '.join(address_lines).strip()
            # ทำความสะอาด: ลบ space หลายตัว
            address = re.sub(r'\s+', ' ', address)
            if len(address) > 10:
                return address
        
        # Fallback: ใช้ที่อยู่ default
        return "628 ชั้น 3 อาคารทริปเพลสไอ ซอยกลับเข็ม ถนนนนทรี แขวงช่องนนทรี เขตยานนาวา กรุงเทพฯ 10120"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': None,
            'withholding_tax_amount': None
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลยอดเงิน
        
        - ยอดก่อนภาษีมูลค่าเพิ่ม: จำนวนเงิน TOTAL 1,308.41
        - ภาษีมูลค่าเพิ่ม: ภาษีมูลค่าเพิ่ม VALUE ADDED TAX 91.59
        - ยอดหลังบวกภาษีมูลค่าเพิ่ม: จำนวนเงินรวมทั้งสิ้น GRAND TOTAL 1,400.00
        """
        amounts = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # ยอดก่อนภาษีมูลค่าเพิ่ม: จำนวนเงิน TOTAL 1,308.41
        amount_patterns = [
            r'จำนวนเงิน\s+TOTAL\s+([\d,]+\.?\d*)',
            r'TOTAL\s+([\d,]+\.?\d*)',
            r'จำนวนเงิน\s+([\d,]+\.?\d*)',
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    amount_val = float(amount_str)
                    if amount_val > 0:
                        amounts['amount_before_vat'] = amount_val
                        break
                except ValueError:
                    pass
        
        # ภาษีมูลค่าเพิ่ม: ภาษีมูลค่าเพิ่ม VALUE ADDED TAX 91.59
        vat_patterns = [
            r'ภาษีมูลค่าเพิ่ม\s+VALUE\s+ADDED\s+TAX\s+([\d,]+\.?\d*)',
            r'ภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d*)',
            r'VALUE\s+ADDED\s+TAX\s+([\d,]+\.?\d*)',
        ]
        for pattern in vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vat_str = match.group(1).replace(',', '').strip()
                try:
                    vat_val = float(vat_str)
                    if vat_val > 0:
                        amounts['vat_amount'] = vat_val
                        break
                except ValueError:
                    pass
        
        # ยอดหลังบวกภาษีมูลค่าเพิ่ม: จำนวนเงินรวมทั้งสิ้น GRAND TOTAL 1,400.00
        total_patterns = [
            r'จำนวนเงินรวมทั้งสิ้น\s+GRAND\s+TOTAL\s+([\d,]+\.?\d*)',
            r'GRAND\s+TOTAL\s+([\d,]+\.?\d*)',
            r'จำนวนเงินรวมทั้งสิ้น\s+([\d,]+\.?\d*)',
        ]
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                total_str = match.group(1).replace(',', '').strip()
                try:
                    total_val = float(total_str)
                    if total_val > 0:
                        amounts['total_amount'] = total_val
                        break
                except ValueError:
                    pass
        
        return amounts
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงหมายเหตุ: B/L NO. CKCONSA0002312 INVOICE NO. CKTIN25110052 {ชื่อไฟล์เก่า}
        อ่านข้อมูลจาก:
        - B/L NO. และ JOB NO. (CKCONS A0002312) -> CKCONSA0002312
        - INVOICE NO. CKTIN25110052
        """
        remark_parts = []
        
        # หา B/L NO. และ JOB NO.
        # รูปแบบ: B/L NO. JOB NO.
        #         CKCONS A0002312
        bl_no = None
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            # หาบรรทัดที่มี "B/L NO." และ "JOB NO."
            if 'B/L NO.' in line_clean.upper() and 'JOB NO.' in line_clean.upper():
                # ดูบรรทัดถัดไป
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # แยกด้วย space และรวมเป็น B/L No. (เช่น CKCONS A0002312 -> CKCONSA0002312)
                    parts = next_line.split()
                    if len(parts) >= 2:
                        # รวมส่วนแรกและส่วนที่สอง (CKCONS + A0002312 = CKCONSA0002312)
                        bl_no = ''.join(parts[:2])
                        break
        
        # ถ้ายังไม่เจอ ลองหาจาก pattern ทั่วไป
        if not bl_no:
            bl_patterns = [
                r'B/L\s+NO[.:]?\s*[:.]?\s*([A-Z0-9]+)',
                r'JOB\s+NO[.:]?\s*[:.]?\s*([A-Z0-9]+)',
            ]
            for pattern in bl_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    bl_no = matches[0]
                    break
        
        # หา INVOICE NO.
        invoice_no = None
        invoice_patterns = [
            r'INVOICE\s+NO[.:]?\s*[:.]?\s*([A-Z0-9]+)',
            r'Invoice\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',
        ]
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_no = match.group(1).strip()
                break
        
        # เพิ่ม B/L NO. และ INVOICE NO. ใน remark
        if bl_no:
            remark_parts.append(f"B/L NO. {bl_no}")
        if invoice_no:
            remark_parts.append(f"INVOICE NO. {invoice_no}")
        
        # เพิ่มชื่อไฟล์ (ตัด WHT_, VAT_, None_vat_ ออก)
        if filename:
            filename_clean = filename
            filename_clean = re.sub(r'(WHT_|VAT_|None_vat_)', '', filename_clean, flags=re.IGNORECASE)
            filename_clean = re.sub(r'\.pdf$', '', filename_clean, flags=re.IGNORECASE)
            if filename_clean:
                remark_parts.append(filename_clean)
        
        if remark_parts:
            return ' '.join(remark_parts)
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร (1 = มีภาษีมูลค่าเพิ่ม)"""
        return 1  # มีภาษีมูลค่าเพิ่ม
    
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
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, None_vat_, WHT_)
        new_filename = filename
        if new_filename:
            new_filename = re.sub(r'(VAT_|None_vat_|WHT_)', '', new_filename, flags=re.IGNORECASE)
        
        # แยกที่อยู่เป็นส่วนๆ
        # ที่อยู่: 628 ชั้น 3 อาคารทริปเพลสไอ ซอยกลับเข็ม ถนนนนทรี แขวงช่องนนทรี เขตยานนาวา กรุงเทพฯ 10120
        address_full = address or ''
        building_number = ''  # 628
        other_info = ''  # ชั้น 3 อาคารทริปเพลสไอ ซอยกลับเข็ม
        soi = ''  # ซอย/ตรอก
        road = ''  # ถนนนนทรี
        subdistrict = ''  # แขวงช่องนนทรี
        district = ''  # เขตยานนาวา
        province = ''  # จังหวัดกรุงเทพมหานคร
        postal_code = ''  # รหัสไปรษณีย์ 10120
        
        if address:
            # ดึงเลขที่จาก "628" (อยู่ต้นที่อยู่)
            building_match = re.search(r'^(\d+)', address.strip())
            if building_match:
                building_number = building_match.group(1).strip()
            
            # ดึงอื่นๆ จาก "ชั้น 3 อาคารทริปเพลสไอ ซอยกลับเข็ม"
            # หาส่วนหลังเลขที่และก่อน "ถนน"
            other_match = re.search(r'^\d+\s+(.+?)(?=\s+ถนน)', address)
            if other_match:
                other_info = other_match.group(1).strip()
            
            # ดึงถนนจาก "ถนนนนทรี"
            road_match = re.search(r'ถนน\s*([ก-๙A-Za-z]+)', address)
            if road_match:
                road = f"ถนน{road_match.group(1).strip()}"
            
            # ดึงแขวงจาก "แขวงช่องนนทรี"
            subdistrict_match = re.search(r'แขวง\s*([ก-๙A-Za-z]+)', address)
            if subdistrict_match:
                subdistrict = subdistrict_match.group(1).strip()
            
            # ดึงเขตจาก "เขตยานนาวา"
            district_match = re.search(r'เขต\s*([ก-๙A-Za-z]+)', address)
            if district_match:
                district = district_match.group(1).strip()
            
            # ดึงจังหวัดจาก "กรุงเทพฯ" หรือ "กรุงเทพมหานคร"
            if 'กรุงเทพ' in address:
                province = 'กรุงเทพมหานคร'
            
            # ดึงรหัสไปรษณีย์ (5 หลัก)
            postal_match = re.search(r'(\d{5})\s*$', address)
            if postal_match:
                postal_code = postal_match.group(1).strip()
        
        return {
            'success': True,
            'company': 'CK_LINE_THAILAND',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number or '',  # เลขที่ (628)
            'other_info': other_info or '',  # อื่นๆ (ชั้น 3 อาคารทริปเพลสไอ ซอยกลับเข็ม)
            'soi': soi or '',  # ซอย/ตรอก
            'road': road or '',  # ถนน (ถนนนนทรี)
            'subdistrict': subdistrict or '',  # แขวง (ช่องนนทรี)
            'district': district or '',  # เขต (ยานนาวา)
            'province': province or '',  # จังหวัด (กรุงเทพมหานคร)
            'postal_code': postal_code or '',  # รหัสไปรษณีย์ (10120)
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
            'document_type': document_type,  # 1 = มีภาษีมูลค่าเพิ่ม
        }


# ===== Jinjiang Shipping Agency Extractor =====
class JinjiangShippingAgencyExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก JINJIANG SHIPPING AGENCY (THAILAND) CO., LTD."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "JINJIANG SHIPPING AGENCY",
        "JINJIANG SHIPPING",
        "Jinjiang Shipping"
    ]
    
    def __init__(self):
        """Initialize Jinjiang Shipping Agency Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Jinjiang Shipping Agency หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "JINJIANG SHIPPING AGENCY"
        2. Tax ID "0105565190389"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Jinjiang Shipping Agency (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier.upper() in text.upper() for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105565190389"
        has_tax_id = "0105565190389" in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "JINJIANG SHIPPING AGENCY (THAILAND) CO., LTD."
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษีจาก 'Tax ID: 0105565190389'"""
        # Pattern: Tax ID: 0105565190389
        patterns = [
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # ถ้าไม่พบ pattern ให้ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่
        if "0105565190389" in text:
            return "0105565190389"
        
        return None
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา (ถ้ามี)"""
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่จาก 'DATE : 03-Nov-25' และแปลงเป็น d/m/yyyy (เช่น 3/11/2025)"""
        # Pattern: DATE : 03-Nov-25
        patterns = [
            r'DATE\s*[:.]?\s*(\d{1,2})-([A-Za-z]{3})-(\d{2,4})',
            r'Date\s*[:.]?\s*(\d{1,2})-([A-Za-z]{3})-(\d{2,4})',
        ]
        
        month_map = {
            'JAN': '1', 'FEB': '2', 'MAR': '3', 'APR': '4',
            'MAY': '5', 'JUN': '6', 'JUL': '7', 'AUG': '8',
            'SEP': '9', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).lstrip('0') or '0'  # ตัด 0 นำหน้า (3 ไม่ใช่ 03)
                month_abbr = match.group(2).upper()
                year_str = match.group(3)
                
                # แปลงเดือน
                month = month_map.get(month_abbr, '1')
                
                # แปลงปี (25 -> 2025, 2025 -> 2025)
                if len(year_str) == 2:
                    # สมมติว่า 25 = 2025 (สามารถปรับได้ถ้าต้องการ)
                    year = '20' + year_str
                else:
                    year = year_str
                
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขใบกำกับภาษีจาก 'NO. : JJT-TX25110085'"""
        # Pattern: NO. : JJT-TX25110085
        patterns = [
            r'NO[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
            r'No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
            r'Invoice\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_no = match.group(1).strip()
                # ตรวจสอบว่าเป็นรูปแบบ JJT-TX... หรือไม่ (หรือรูปแบบอื่นๆ)
                if doc_no:
                    return doc_no
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: Lumpini Tower, 37th floor, No.1168/110, Rama 4 Road, Tungmahamek, Sathorn, Bangkok 10120 Thailand.
        
        Returns:
            ที่อยู่รวม (string)
        """
        # หาที่อยู่จาก text (มักจะอยู่หลังชื่อบริษัทหรือ Tax ID)
        lines = text.split('\n')
        address_lines = []
        collecting = False
        
        # หาตำแหน่งที่เริ่มต้นที่อยู่
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # หา "Lumpini Tower" หรือ "Rama 4 Road" หรือ "Bangkok 10120"
            if any(keyword in line_clean for keyword in ['Lumpini Tower', 'Rama 4 Road', 'Bangkok 10120', 'Sathorn', 'Tungmahamek']):
                # ลบ "Thailand." หรือข้อมูลอื่นๆ ที่ไม่จำเป็น
                line_clean = re.sub(r'\s*Thailand[.,]?\s*$', '', line_clean, flags=re.IGNORECASE)
                address_lines.append(line_clean)
                break
            
            # ถ้ามี keyword ที่เกี่ยวข้อง
            if any(keyword in line_clean for keyword in ['Tower', 'Road', 'Bangkok', 'floor']):
                # ตรวจสอบว่ามีรูปแบบที่อยู่ (มี comma, number, road)
                if ',' in line_clean or re.search(r'\d{5}', line_clean):
                    address_lines.append(line_clean)
                    break
        
        # รวมที่อยู่ทั้งหมด
        if address_lines:
            address = ' '.join(address_lines).strip()
            # ทำความสะอาด: ลบ space หลายตัว
            address = re.sub(r'\s+', ' ', address)
            if len(address) > 10:
                return address
        
        # Fallback: ใช้ที่อยู่ default
        return "Lumpini Tower, 37th floor, No.1168/110, Rama 4 Road, Tungmahamek, Sathorn, Bangkok 10120"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': None,
            'withholding_tax_amount': None
        }
    
    def _extract_from_html_table(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลจากตาราง HTML โดยค้นหา AMOUNT (THB), VALUE ADDED TAX 7%, และ TOTAL
        
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
                        amount_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_cell)
                        if amount_match:
                            try:
                                result['amount_before_vat'] = float(amount_match.group(1).replace(',', ''))
                            except ValueError:
                                pass
                    
                    # หา VALUE ADDED TAX 7%
                    if 'VALUE ADDED TAX' in row_upper and '7%' in row_text and not result['vat_amount']:
                        # หาตัวเลขใน cell สุดท้าย
                        last_cell = cleaned_cells[-1].strip()
                        vat_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_cell)
                        if vat_match:
                            try:
                                result['vat_amount'] = float(vat_match.group(1).replace(',', ''))
                            except ValueError:
                                pass
                    
                    # หา TOTAL
                    if 'TOTAL' in row_upper and not result['total_amount']:
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
                            # หาตัวเลขใน cell สุดท้าย (อาจเป็นคอลัมน์สุดท้ายที่เป็น TOTAL column)
                            last_cell = cleaned_cells[-1].strip()
                            total_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_cell)
                            if total_match:
                                try:
                                    result['total_amount'] = float(total_match.group(1).replace(',', ''))
                                except ValueError:
                                    pass
                            # ถ้ายังไม่ได้ ลองหาจาก cell ที่อยู่หลัง TOTAL
                            elif total_cell_index >= 0 and total_cell_index + 1 < len(cleaned_cells):
                                next_cell = cleaned_cells[total_cell_index + 1].strip()
                                total_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', next_cell)
                                if total_match:
                                    try:
                                        result['total_amount'] = float(total_match.group(1).replace(',', ''))
                                    except ValueError:
                                        pass
                
                # ถ้าได้ข้อมูลครบแล้ว ให้ return
                if result['amount_before_vat'] and result['vat_amount'] and result['total_amount']:
                    logger.info(f"✅ ดึงยอดเงินจากตาราง HTML สำเร็จ: amount_before_vat={result['amount_before_vat']}, vat_amount={result['vat_amount']}, total_amount={result['total_amount']}")
                    return result
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงข้อมูลจากตาราง HTML: {e}")
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลยอดเงิน
        
        - ยอดก่อนภาษีมูลค่าเพิ่ม: AMOUNT (THB) | 1,800.00
        - ภาษีมูลค่าเพิ่ม: VALUE ADDED TAX 7% | 126.00
        - ยอดหลังบวกภาษีมูลค่าเพิ่ม: TOTAL | 1,926.00
        
        รูปแบบในเอกสารจริง:
        - ผิด ตก ยกเว้น / E & O.E. | ผิด ตก ยกเว้น / E & O.E. | AMOUNT (THB) | 1,800.00
        - หมายเหตุ | หมายเหตุ | VALUE ADDED TAX 7% | 126.00
        - 03/11/25 | 11:02:04 | TOTAL | 1,926.00
        """
        amounts = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # วิธีที่ 0: ลองดึงจาก HTML table ก่อน (ถ้าหน้าเว็บอ่านได้)
        html_table_result = self._extract_from_html_table(text)
        if html_table_result.get('amount_before_vat') or html_table_result.get('vat_amount') or html_table_result.get('total_amount'):
            amounts.update(html_table_result)
            # ถ้าได้ข้อมูลครบแล้ว ให้ return
            if amounts['amount_before_vat'] and amounts['vat_amount'] and amounts['total_amount']:
                return amounts
        
        # วิธีที่ 1: แยกแต่ละบรรทัดและตรวจสอบแบบง่ายๆ
        lines = text.split('\n')
        for line in lines:
            line_clean = line.strip()
            if '|' not in line_clean:
                continue
            
            # แยกคอลัมน์ด้วย |
            parts = [p.strip() for p in line_clean.split('|')]
            
            if len(parts) < 2:
                continue
            
            # ตรวจสอบทุกคอลัมน์และหาค่าจากคอลัมน์สุดท้าย
            line_upper = line_clean.upper()
            
            # หา AMOUNT (THB)
            if 'AMOUNT' in line_upper and '(THB)' in line_upper and not amounts['amount_before_vat']:
                # หาตัวเลขในคอลัมน์สุดท้าย
                last_col = parts[-1].strip()
                amount_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_col)
                if amount_match:
                    try:
                        amounts['amount_before_vat'] = float(amount_match.group(1).replace(',', ''))
                    except ValueError:
                        pass
            
            # หา VALUE ADDED TAX 7%
            if 'VALUE ADDED TAX' in line_upper and '7%' in line_clean and not amounts['vat_amount']:
                # หาตัวเลขในคอลัมน์สุดท้าย
                last_col = parts[-1].strip()
                vat_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_col)
                if vat_match:
                    try:
                        amounts['vat_amount'] = float(vat_match.group(1).replace(',', ''))
                    except ValueError:
                        pass
            
            # หา TOTAL
            if 'TOTAL' in line_upper and not amounts['total_amount']:
                # ตรวจสอบว่ามี TOTAL เป็นคอลัมน์แยกต่างหาก
                has_total = False
                for part in parts:
                    if part.strip().upper() == 'TOTAL':
                        has_total = True
                        break
                
                if has_total:
                    # หาตัวเลขในคอลัมน์สุดท้าย
                    last_col = parts[-1].strip()
                    total_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_col)
                    if total_match:
                        try:
                            amounts['total_amount'] = float(total_match.group(1).replace(',', ''))
                        except ValueError:
                            pass
        
        # ถ้ายังไม่ได้ข้อมูล ให้ลองหาแบบ regex patterns (backup method)
        # รูปแบบจริง: ผิด ตก ยกเว้น / E & O.E. | ผิด ตก ยกเว้น / E & O.E. | AMOUNT (THB) | 1,800.00
        if not amounts['amount_before_vat']:
            # Pattern: ... | AMOUNT (THB) | 1,800.00
            patterns_amount = [
                r'\|\s*AMOUNT\s*\(THB\)\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # | AMOUNT (THB) | 1,800.00
                r'AMOUNT\s*\(THB\)\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # AMOUNT (THB) | 1,800.00
                r'AMOUNT\s*\(THB\)[^|]*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # AMOUNT (THB) ... | 1,800.00
            ]
            for pattern in patterns_amount:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    try:
                        amounts['amount_before_vat'] = float(match.group(1).replace(',', ''))
                        break
                    except ValueError:
                        pass
        
        if not amounts['vat_amount']:
            # Pattern: ... | VALUE ADDED TAX 7% | 126.00
            patterns_vat = [
                r'\|\s*VALUE\s+ADDED\s+TAX\s+7%\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # | VALUE ADDED TAX 7% | 126.00
                r'VALUE\s+ADDED\s+TAX\s+7%\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # VALUE ADDED TAX 7% | 126.00
                r'VALUE\s+ADDED\s+TAX\s+7%[^|]*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # VALUE ADDED TAX 7% ... | 126.00
            ]
            for pattern in patterns_vat:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    try:
                        amounts['vat_amount'] = float(match.group(1).replace(',', ''))
                        break
                    except ValueError:
                        pass
        
        if not amounts['total_amount']:
            # Pattern: ... | TOTAL | 1,926.00 (รองรับคอลัมน์ว่าง)
            # รูปแบบจริง: 03/11/25 | 11:02:04 | TOTAL | 1,926.00
            patterns_total = [
                r'\|\s*TOTAL\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # | TOTAL | 1,926.00
                r'\|\s*\|\s*TOTAL\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # |  | TOTAL | 1,926.00
                r'TOTAL\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # TOTAL | 1,926.00
                r'[^|]*\|\s*TOTAL\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # ... | TOTAL | 1,926.00
            ]
            for pattern in patterns_total:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    try:
                        amounts['total_amount'] = float(match.group(1).replace(',', ''))
                        break
                    except ValueError:
                        pass
        
        return amounts
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (ถ้ามี)"""
        remark_parts = []
        
        # เพิ่มชื่อไฟล์ (ตัด VAT_, WHT_, None_vat_ ออก)
        if filename:
            filename_clean = filename
            filename_clean = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename_clean, flags=re.IGNORECASE)
            filename_clean = re.sub(r'\.pdf$', '', filename_clean, flags=re.IGNORECASE)
            if filename_clean:
                remark_parts.append(filename_clean)
        
        if remark_parts:
            return ' '.join(remark_parts)
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร (1 = มีภาษีมูลค่าเพิ่ม)"""
        return 1  # มีภาษีมูลค่าเพิ่ม
    
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
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, None_vat_, WHT_)
        new_filename = filename
        if new_filename:
            new_filename = re.sub(r'(VAT_|None_vat_|WHT_)', '', new_filename, flags=re.IGNORECASE)
        
        # แยกที่อยู่เป็นส่วนๆ
        # ที่อยู่: Lumpini Tower, 37th floor, No.1168/110, Rama 4 Road, Tungmahamek, Sathorn, Bangkok 10120 Thailand.
        address_full = address or ''
        building_number = ''  # 1168/110
        other_info = ''  # Lumpini Tower, 37th floor
        soi = ''  # ซอย/ตรอก
        road = ''  # Rama 4 Road
        subdistrict = ''  # แขวง (Tungmahamek)
        district = ''  # ตำบล (Sathorn)
        province = ''  # จังหวัด (Bangkok)
        postal_code = ''  # รหัสไปรษณีย์ (10120)
        
        if address:
            # ดึงเลขที่จาก "No.1168/110" หรือ "1168/110"
            # Pattern: No.1168/110 หรือ 1168/110
            building_match = re.search(r'(?:No\.?\s*)?(\d+(?:/\d+)?)', address, re.IGNORECASE)
            if building_match:
                building_number = building_match.group(1).strip()
            
            # ดึงอื่นๆ จาก "Lumpini Tower, 37th floor"
            # หาส่วนก่อน "No.1168/110" หรือ ", No.1168/110"
            # ที่อยู่: "Lumpini Tower, 37th floor, No.1168/110, ..."
            # ต้องการ: "Lumpini Tower, 37th floor"
            other_match = re.search(r'^(.+?)(?=\s*,?\s*(?:No\.?\s*)?\d+(?:/\d+)?)', address)
            if other_match:
                other_info = other_match.group(1).strip()
                # ลบ comma ที่ท้าย
                other_info = re.sub(r',\s*$', '', other_info).strip()
            
            # ถ้ายังไม่มี other_info ลองหาจาก "Lumpini Tower" และ "37th floor"
            if not other_info:
                tower_match = re.search(r'(Lumpini Tower[^,]*?37th floor)', address, re.IGNORECASE)
                if tower_match:
                    other_info = tower_match.group(1).strip()
            
            # ดึงถนนจาก "Rama 4 Road"
            road_match = re.search(r'([A-Za-z0-9\s]+Road)', address, re.IGNORECASE)
            if road_match:
                road = road_match.group(1).strip()
            
            # ดึงแขวงจาก "Tungmahamek" (ค้นหาโดยตรง)
            tungmahamek_match = re.search(r'\b(Tungmahamek)\b', address, re.IGNORECASE)
            if tungmahamek_match:
                subdistrict = tungmahamek_match.group(1).strip()
            
            # ดึงตำบลจาก "Sathorn" (ค้นหาโดยตรง)
            sathorn_match = re.search(r'\b(Sathorn)\b', address, re.IGNORECASE)
            if sathorn_match:
                district = sathorn_match.group(1).strip()
            
            # ดึงจังหวัดจาก "Bangkok"
            province_match = re.search(r'Bangkok', address, re.IGNORECASE)
            if province_match:
                province = 'Bangkok'
            
            # ดึงรหัสไปรษณีย์ (5 หลัก) จาก "10120"
            postal_match = re.search(r'\b(\d{5})\b', address)
            if postal_match:
                postal_code = postal_match.group(1).strip()
        
        return {
            'success': True,
            'company': 'JINJIANG_SHIPPING_AGENCY',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number or '',  # เลขที่ (1168/110)
            'other_info': other_info or '',  # อื่นๆ (Lumpini Tower, 37th floor)
            'soi': soi or '',  # ซอย/ตรอก
            'road': road or '',  # ถนน (Rama 4 Road)
            'subdistrict': subdistrict or '',  # แขวง (Tungmahamek)
            'district': district or '',  # ตำบล (Sathorn)
            'province': province or '',  # จังหวัด (Bangkok)
            'postal_code': postal_code or '',  # รหัสไปรษณีย์ (10120)
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
            'document_type': document_type,  # 1 = มีภาษีมูลค่าเพิ่ม
        }


# ===== Main Extractor Manager =====
class InvoiceExtractorManager:
    """ตัวจัดการ Extractor ทั้งหมด"""
    
    def __init__(self):
        """Initialize Manager"""
        self.extractors = [
            CustomsDepartmentExtractor(),  # กรมศุลกากร ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
            KLNSeaportExtractor(),  # KLN Seaport ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
            EasternSeaLamchabangTerminalExtractor(),  # Eastern Sea Lamchabang Terminal ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
            LCMTExtractor(),  # LCMT ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
            NgowHokExtractor(),  # Ngow Hok ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
            SiamCommercialSeaportExtractor(),  # Siam Commercial Seaport ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
            TIPSExtractor(),  # TIPS ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
            CKLineThailandExtractor(),  # CK Line (Thailand) ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
            JinjiangShippingAgencyExtractor(),  # Jinjiang Shipping Agency ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
            ExclusiveGlobalLogisticsExtractor(),  # Exclusive Global Logistics ต้องอยู่ก่อนเพราะเฉพาะเจาะจง
            MSTInvoiceExtractor(),  # MST ต้องอยู่ก่อน MSC เพราะเฉพาะเจาะจงกว่า
            MSCInvoiceExtractor(),
            # เพิ่ม Extractor อื่นๆ ที่นี่
        ]
    
    def extract_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลจากเอกสารโดยอัตโนมัติ
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ลองแต่ละ Extractor
        for extractor in self.extractors:
            if extractor.is_company_document(text):
                logger.info(f"🔍 ตรวจพบเอกสารของ: {extractor.__class__.__name__}")
                return extractor.extract_all_data(text, filename, filepath)
        
        # ไม่พบ Extractor ที่เหมาะสม
        return {
            'success': False,
            'company': None,
            'error': 'ไม่สามารถระบุประเภทเอกสารได้ (ยังไม่รองรับบริษัทนี้)'
        }
    
    def get_supported_companies(self) -> List[Dict[str, Any]]:
        """
        ดึงรายชื่อบริษัทที่ระบบรองรับ
        
        Returns:
            List of dictionaries containing company information
        """
        companies = []
        for extractor in self.extractors:
            try:
                # เรียก extract_company_name เพื่อดึงชื่อบริษัท (ใช้ข้อความตัวอย่าง)
                # สำหรับ extractor บางตัวที่ต้องการ parse text ใช้ข้อความตัวอย่าง
                sample_text = "Sample text for company name extraction"
                company_name = extractor.extract_company_name(sample_text)
                extractor_name = extractor.__class__.__name__
                
                # ถ้าได้ None หรือ empty ให้ลองด้วยข้อความว่าง
                if not company_name:
                    company_name = extractor.extract_company_name("")
                
                companies.append({
                    'extractor_name': extractor_name,
                    'company_name': company_name or 'ไม่ระบุชื่อ',
                    'identifiers': getattr(extractor, 'COMPANY_IDENTIFIERS', [])
                })
            except Exception as e:
                logger.warning(f"ไม่สามารถดึงข้อมูลบริษัทจาก {extractor.__class__.__name__}: {e}")
                # ถ้ามีปัญหา ให้ใช้ชื่อ extractor แทน
                companies.append({
                    'extractor_name': extractor.__class__.__name__,
                    'company_name': extractor.__class__.__name__.replace('Extractor', ''),
                    'identifiers': getattr(extractor, 'COMPANY_IDENTIFIERS', [])
                })
                continue
        
        return companies


# ===== Helper Functions =====

def extract_invoice_data(text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
    """
    Helper function สำหรับดึงข้อมูลจากใบแจ้งหนี้
    
    Args:
        text: ข้อความที่อ่านจาก OCR
        filename: ชื่อไฟล์ PDF
        filepath: Path ของไฟล์ (optional)
    
    Returns:
        Dictionary ที่มีข้อมูลทั้งหมด
    """
    manager = InvoiceExtractorManager()
    return manager.extract_data(text, filename, filepath)


# ===== Usage Example =====
if __name__ == "__main__":
    # ตัวอย่างการใช้งาน
    sample_text = """
    MSC Mediterranean Shipping Company S.A.
    C/O Mediterranean Shipping (Thailand) Co., Ltd.
    Head Office: MSC Building, 571 Sukhumvit 71 Rd., Klongton-Nua, Vadhana,
    Bangkok 10,110 Tel: +66(0)2,460-6,400
    
    TaxID 9930000036677
    
    TAX INVOICE/RECEIPT
    ต้นฉบับใบกำกับภาษี / ต้นฉบับใบเสร็จรับเงิน
    
    No. 2511200301
    
    Date / วันที่ 03-NOV-2025 Branch No : 0
    
    Non-Taxable Amount / ไม่มีภาษีมูลค่าเพิ่ม 6,000.00
    Total / รวม 6,000.00
    """
    
    filename = "EXC-2511-008_007.pdf"
    
    result = extract_invoice_data(sample_text, filename)
    
    print("=" * 80)
    print("🔍 Invoice Data Extraction Result")
    print("=" * 80)
    print(f"Success: {result.get('success')}")
    print(f"Company: {result.get('company')}")
    print(f"Company Name: {result.get('company_name')}")
    print(f"Tax ID: {result.get('tax_id')}")
    print(f"Date: {result.get('date')}")
    print(f"Account Name: {result.get('account_name')}")
    print(f"Account Code: {result.get('account_code')}")
    print(f"Amount Before VAT: {result.get('amount_before_vat')}")
    print(f"VAT Amount: {result.get('vat_amount')}")
    print(f"Total Amount: {result.get('total_amount')}")
    print(f"Document Type: {result.get('document_type')}")
    print(f"Remark: {result.get('remark')}")
    print(f"New Filename: {result.get('new_filename')}")
    print(f"Old Filename: {result.get('old_filename')}")
    print("=" * 80)

