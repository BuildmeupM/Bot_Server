"""
KLN Seaport Invoice Extractor
==============================
Extractor สำหรับดึงข้อมูลจาก บริษัท เคแอลเอ็น ซีพอร์ต จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class KLNSeaportExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท เคแอลเอ็น ซีพอร์ต จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "เคแอลเอ็น ซีพอร์ต",
        "KLN Seaport",
        "เดแอลเอ็น ซีพีเออร์ต",
        "DLN Seaport"
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
        
        # หาส่วนต้นฉบับของใบกำกับภาษีก่อน
        original_section = self.extract_original_invoice_section(text)
        if original_section:
            # ใช้เฉพาะส่วนต้นฉบับในการดึงข้อมูล
            text = original_section
            logger.info("✅ ใช้เฉพาะส่วนต้นฉบับของใบกำกับภาษีในการดึงข้อมูล")
        
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
