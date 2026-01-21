"""
LCMT Invoice Extractor
=======================
Extractor สำหรับดึงข้อมูลจาก บริษัท แอล ซี เอ็ม ที จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


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
        """ดึงเลขประจำตัวผู้เสียภาษีจาก 'TAX ID 0115547010161' หรือ 'เลขประจำตัวผู้เสียภาษีอากร 0115547010161'"""
        # Pattern: TAX ID 0115547010161 หรือ เลขประจำตัวผู้เสียภาษีอากร 0115547010161
        # เพิ่มความสำคัญให้กับ "เลขประจำตัวผู้เสียภาษีอากร" เป็นอันดับแรก (ตามข้อมูล OCR บรรทัด 902)
        # รองรับกรณีที่มีข้อความเพิ่มเติมหลังเลข เช่น "สำนักงานใหญ่ TAX ID 0115547010161 HEAD OFFICE"
        patterns = [
            # รูปแบบหลัก: เลขประจำตัวผู้เสียภาษีอากร 0115547010161 (รองรับข้อความต่อท้าย)
            # Pattern นี้จะจับเลข 13 หลักที่อยู่หลัง "เลขประจำตัวผู้เสียภาษีอากร" แม้จะมีข้อความต่อท้าย
            # ใช้ (?=\s|$) เพื่อจับเลขที่ตามด้วยช่องว่างหรือจบบรรทัด (แทน \b ที่ไม่ทำงานดีกับไทย)
            # รองรับกรณีที่ OCR อ่านผิด เช่น 0 เป็น O หรือ 1 เป็น l
            r'เลขประจำตัวผู้เสียภาษีอากร\s+([0-9OIl]{13})(?=\s|$|[^\d])',  # เลขประจำตัวผู้เสียภาษีอากร 0115547010161 (มีข้อความต่อท้าย)
            r'เลขประจำตัวผู้เสียภาษีอากร\s+([0-9OIl]{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0115547010161
            # รูปแบบที่มีเครื่องหมาย : หรือ . ตามหลัง
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # เลขประจำตัวผู้เสียภาษีอากร: 0115547010161
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*([0-9OIl]{13})',  # เลขประจำตัวผู้เสียภาษีอากร: 0115547010161
            # รูปแบบที่มีช่องว่างในเลข (0115 5470 10161)
            r'เลขประจำตัวผู้เสียภาษีอากร\s+([0-9OIl]{4}\s+[0-9OIl]{4}\s+[0-9OIl]{5})(?=\s|$|[^\d])',  # เลขประจำตัวผู้เสียภาษีอากร 0115 5470 10161
            r'เลขประจำตัวผู้เสียภาษีอากร\s+([0-9OIl]{4}\s+[0-9OIl]{4}\s+[0-9OIl]{5})',  # เลขประจำตัวผู้เสียภาษีอากร 0115 5470 10161
            # รูปแบบ TAX ID (รองรับกรณีที่มีข้อความต่อท้าย)
            r'TAX\s+ID\s+([0-9OIl]{13})(?=\s|$|[^\d])',  # TAX ID 0115547010161 (มีข้อความต่อท้าย)
            r'TAX\s+ID\s*[:.]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # TAX ID: 0115547010161
            r'TAX\s+ID\s*[:.]?\s*([0-9OIl]{13})',  # TAX ID: 0115547010161
            r'Tax\s+ID\s+([0-9OIl]{13})(?=\s|$|[^\d])',  # Tax ID 0115547010161
            r'Tax\s+ID\s*[:.]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # Tax ID: 0115547010161
            r'Tax\s+ID\s*[:.]?\s*([0-9OIl]{13})',  # Tax ID: 0115547010161
            r'TaxID\s*[:.]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # TaxID: 0115547010161
            r'TaxID\s*[:.]?\s*([0-9OIl]{13})',  # TaxID: 0115547010161
            r'TAXID\s*[:.]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # TAXID: 0115547010161
            r'TAXID\s*[:.]?\s*([0-9OIl]{13})',  # TAXID: 0115547010161
            r'Tax\s+ID\s+No[.:]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # Tax ID No.: 0115547010161
            r'Tax\s+ID\s+No[.:]?\s*([0-9OIl]{13})',  # Tax ID No.: 0115547010161
            # รูปแบบอื่นๆ
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*([0-9OIl]{13})(?=\s|$|[^\d])',  # เลขประจำตัวผู้เสียภาษี: 0115547010161
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*([0-9OIl]{13})',  # เลขประจำตัวผู้เสียภาษี: 0115547010161
            r'Tax\s*ID\s*[:.]?\s*([0-9OIl]{4}\s+[0-9OIl]{4}\s+[0-9OIl]{5})(?=\s|$|[^\d])',  # Tax ID: 0115 5470 10161 (มีช่องว่าง)
            r'Tax\s*ID\s*[:.]?\s*([0-9OIl]{4}\s+[0-9OIl]{4}\s+[0-9OIl]{5})',  # Tax ID: 0115 5470 10161 (มีช่องว่าง)
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*([0-9OIl]{4}\s+[0-9OIl]{4}\s+[0-9OIl]{5})(?=\s|$|[^\d])',  # เลขประจำตัวผู้เสียภาษี: 0115 5470 10161
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*([0-9OIl]{4}\s+[0-9OIl]{4}\s+[0-9OIl]{5})',  # เลขประจำตัวผู้เสียภาษี: 0115 5470 10161
            # รูปแบบทั่วไป (ต้องตรวจสอบว่าเป็น 0115547010161)
            r'([0-9OIl]{4}\s+[0-9OIl]{4}\s+[0-9OIl]{5})',  # 0115 5470 10161 (รูปแบบทั่วไป)
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                tax_id = match.group(1).replace(' ', '').replace('-', '')  # ลบช่องว่างและขีด
                # แก้ไขตัวอักษรที่ OCR อ่านผิด เช่น 0 เป็น O หรือ 1 เป็น l
                tax_id = tax_id.replace('O', '0').replace('I', '1').replace('l', '1')
                if len(tax_id) == 13:
                    # ตรวจสอบว่าเป็น Tax ID ที่ถูกต้อง
                    if tax_id == "0115547010161":
                        return tax_id
        
        # Fallback 1: ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่ (รองรับช่องว่างและขีด)
        # แก้ไขตัวอักษรที่ OCR อ่านผิด
        text_clean = text.replace(' ', '').replace('-', '').replace('O', '0').replace('I', '1').replace('l', '1')
        if "0115547010161" in text_clean:
            return "0115547010161"
        
        # Fallback 2: หาเลข 13 หลักที่อยู่ใกล้กับคำว่า "เลขประจำตัวผู้เสียภาษีอากร" หรือ "TAX ID"
        # หา "เลขประจำตัวผู้เสียภาษีอากร" หรือ "TAX ID" แล้วหาตัวเลข 13 หลักในระยะ 50 ตัวอักษร
        tax_keywords = [
            r'เลขประจำตัวผู้เสียภาษีอากร',
            r'TAX\s+ID',
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
                    if len(tax_id) == 13 and tax_id == "0115547010161":
                        return tax_id
        
        # Fallback 3: ถ้าไม่พบข้อมูล ให้ใช้ค่า default สำหรับ LCMT
        # เลขประจำตัวผู้เสียภาษีของบริษัท แอล ซี เอ็ม ที จำกัด คือ 0115547010161
        logger.info("⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: 0115547010161")
        return "0115547010161"
    
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
    
    def extract_reference(self, text: str) -> Optional[str]:
        """ดึงอ้างอิงจาก 'Booking or B/L No .: 260701300'"""
        # Pattern: Booking or B/L No .: 260701300
        patterns = [
            r'Booking\s+or\s+B/L\s+No\s*\.?\s*[:.]?\s*([A-Z0-9]+)',  # Booking or B/L No .: 260701300
            r'Booking\s+or\s+B/L\s+No\.\s*[:.]?\s*([A-Z0-9]+)',  # Booking or B/L No.: 260701300
            r'B/L\s+No\s*\.?\s*[:.]?\s*([A-Z0-9]+)',  # B/L No .: 260701300
            r'B/L\s+No\.\s*[:.]?\s*([A-Z0-9]+)',  # B/L No.: 260701300
            r'Booking\s+or\s+B/L\s*[:.]?\s*([A-Z0-9]+)',  # Booking or B/L: 260701300
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bl_no = match.group(1).strip()
                ref = f"B/L No.: {bl_no}"
                logger.info(f"✅ พบอ้างอิง: {ref}")
                return ref
        
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
            'account_name': 'ค่าใช้จ่ายอื่นๆในการซื้อสินค้า',
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
        reference = self.extract_reference(text)
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
            'reference': reference,  # อ้างอิง (B/L No.: 260701300)
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
