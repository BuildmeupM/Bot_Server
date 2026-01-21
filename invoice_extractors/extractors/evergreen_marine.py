"""
Evergreen Marine Invoice Extractor
==================================
Extractor สำหรับดึงข้อมูลจาก เอเวอร์กรีน มารีน (ฮ่องกง) ลิมิเต็ด - สำนักงานใหญ่

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class EvergreenMarineExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก เอเวอร์กรีน มารีน (ฮ่องกง) ลิมิเต็ด - สำนักงานใหญ่"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "เอเวอร์กรีน มารีน (ฮ่องกง) ลิมิเต็ด",
        "เอเวอร์กรีน มารีน",
        "Evergreen Marine",
        "EVERGREEN MARINE"
    ]
    
    # Tax ID
    TAX_ID = "0993000373570"
    
    def __init__(self):
        """Initialize Evergreen Marine Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ เอเวอร์กรีน มารีน (ฮ่องกง) ลิมิเต็ด หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "เอเวอร์กรีน มารีน (ฮ่องกง) ลิมิเต็ด"
        2. Tax ID "0993000373570"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Evergreen Marine (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0993000373570"
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
        return "เอเวอร์กรีน มารีน (ฮ่องกง) ลิมิเต็ด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: เลขประจำตัวผู้เสียภาษีอากร 0993000373570
        patterns = [
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0993000373570
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี 0993000373570
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID: 0993000373570
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0993000373570
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
        # Pattern: วันที่ Date 20251104 (รูปแบบ YYYYMMDD)
        patterns = [
            r'วันที่\s+Date\s+(\d{4})(\d{2})(\d{2})',  # วันที่ Date 20251104
            r'Date\s+(\d{4})(\d{2})(\d{2})',  # Date 20251104
            r'วันที่\s*[:.]?\s*(\d{4})(\d{2})(\d{2})',  # วันที่: 20251104
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = match.group(1)
                month = match.group(2)
                day = match.group(3)
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: NO. BKK-251153092
        patterns = [
            r'NO\.\s+([A-Z]{3}-\d{9})',  # NO. BKK-251153092
            r'No\.\s+([A-Z]{3}-\d{9})',  # No. BKK-251153092
            r'เลขที่\s*[:.]?\s*([A-Z]{3}-\d{9})',  # เลขที่: BKK-251153092
            r'Document\s+No\.\s+([A-Z]{3}-\d{9})',  # Document No. BKK-251153092
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง (ชื่อไฟล์เก่า ตัด VAT_, WHT_, None_vat_ และไม่เอา EXC_ กับข้อมูลที่อยู่ด้านหลัง)"""
        if not filename:
            return None
        
        # ลบ VAT_, WHT_, None_vat_ ออกจากชื่อไฟล์
        cleaned = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename, flags=re.IGNORECASE)
        
        # ตัด EXC_ และข้อมูลที่อยู่ด้านหลังออก
        # เช่น EXC-2511-03 → ตัดออกทั้งหมด
        # รูปแบบ: EXC_xxxx หรือ EXC-xxxx (ตัดทั้งหมด)
        cleaned = re.sub(r'EXC_[^\s.]*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'EXC-[^\s.]*', '', cleaned, flags=re.IGNORECASE)
        
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
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงยอดเงิน"""
        # Pattern: Taxable Amount 6,300.00
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        # Total = Taxable Amount
        
        amount_before_vat = None
        vat_amount = 0.00  # ไม่มีภาษีมูลค่าเพิ่ม
        total_amount = None
        
        # ดึงยอดก่อนภาษี: Taxable Amount 6,300.00
        taxable_amount_patterns = [
            r'Taxable\s+Amount\s*[:.]?\s*([\d,]+\.?\d*)',  # Taxable Amount 6,300.00
            r'Taxable\s+amount\s*[:.]?\s*([\d,]+\.?\d*)',  # Taxable amount 6,300.00
            r'ยอดก่อนภาษี\s*[:.]?\s*([\d,]+\.?\d*)',  # ยอดก่อนภาษี: 6,300.00
        ]
        
        for pattern in taxable_amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    amount_before_vat = float(amount_str)
                    logger.info(f"✅ พบยอดก่อนภาษี: {amount_before_vat}")
                    break
                except ValueError:
                    continue
        
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        vat_amount = 0.00
        
        # Total = Taxable Amount (ถ้าไม่พบยอดรวม)
        if amount_before_vat is not None:
            total_amount = amount_before_vat
        
        return {
            'amount_before_vat': amount_before_vat,
            'vat_amount': vat_amount,
            'total_amount': total_amount
        }
    
    def extract_address(self, text: str) -> str:
        """ดึงที่อยู่"""
        # กำหนดที่อยู่เป็นค่าคงที่
        return "3656/81 ชั้น 24-25 อาคารกรีนทาวเวอร์ ถนนพระราม 4 แขวงคลองตัน เขตคลองเตย กรุงเทพมหานคร 10110"
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (BKK-251153092 และชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_)"""
        remark_parts = []
        
        # ดึงเลขที่เอกสาร
        document_number = self.extract_document_number(text)
        if document_number:
            remark_parts.append(document_number)
        
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
        ดึงข้อมูลทั้งหมดจากเอกสาร Evergreen Marine
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร Evergreen Marine หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร เอเวอร์กรีน มารีน (ฮ่องกง) ลิมิเต็ด'
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
        building_number = '3656/81'
        other_info = 'ชั้น 24-25 อาคารกรีนทาวเวอร์'
        soi = ''
        road = 'ถนนพระราม 4'
        subdistrict = 'คลองตัน'
        district = 'คลองเตย'
        province = 'กรุงเทพมหานคร'
        postal_code = '10110'
        
        return {
            'success': True,
            'company': 'EVERGREEN_MARINE',
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
            'document_type': document_type
        }

