"""
WAN HAI LINES Invoice Extractor
================================
Extractor สำหรับดึงข้อมูลจาก WAN HAI LINES LTD. C/O WAN HAI LINES (THAILAND) LTD.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class WanHaiLinesExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก WAN HAI LINES LTD. C/O WAN HAI LINES (THAILAND) LTD."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "WAN HAI LINES LTD. C/O WAN HAI LINES (THAILAND) LTD.",
        "WAN HAI LINES LTD.",
        "WAN HAI LINES (THAILAND) LTD.",
        "WAN HAI LINES"
    ]
    
    # Tax ID
    TAX_ID = "0993000052463"
    
    def __init__(self):
        """Initialize WAN HAI LINES Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ WAN HAI LINES LTD. C/O WAN HAI LINES (THAILAND) LTD. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "WAN HAI LINES LTD. C/O WAN HAI LINES (THAILAND) LTD."
        2. Tax ID "0993000052463"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร WAN HAI LINES (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier.upper() in text.upper() for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0993000052463"
        has_tax_id = self.TAX_ID in text or "TAX ID NO." + self.TAX_ID in text.upper()
        
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
        return "WAN HAI LINES LTD. C/O WAN HAI LINES (THAILAND) LTD."
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TAX ID NO.0993000052463
        patterns = [
            r'TAX\s+ID\s+NO\.\s*(\d{13})',  # TAX ID NO.0993000052463
            r'Tax\s+ID\s+No\.\s*(\d{13})',  # Tax ID No.0993000052463
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID: 0993000052463
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0993000052463
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0993000052463
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี 0993000052463
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
        # Pattern: DATE 04/11/2025
        patterns = [
            r'DATE\s+(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DATE 04/11/2025
            r'Date\s+(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # Date 04/11/2025
            r'วันที่\s+Date\s+(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # วันที่ Date 04/11/2025
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # วันที่: 04/11/2025
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
        """ดึงเลขที่เอกสาร"""
        # Pattern: RECEIPT NO. TI25111032
        patterns = [
            r'RECEIPT\s+NO\.\s*([A-Z0-9]+)',  # RECEIPT NO. TI25111032
            r'Receipt\s+No\.\s*([A-Z0-9]+)',  # Receipt No. TI25111032
            r'ใบเสร็จเลขที่\s*[:.]?\s*([A-Z0-9]+)',  # ใบเสร็จเลขที่: TI25111032
            r'เลขที่เอกสาร\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่เอกสาร: TI25111032
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง (B/L NO. และชื่อไฟล์เก่า ตัด VAT_, WHT_, None_vat_ และไม่เอา EXC_ กับข้อมูลที่อยู่ด้านหลัง)"""
        reference_parts = []
        
        # ดึง B/L NO.
        bl_patterns = [
            r'B/L\s+NO\.\s*([A-Z0-9]+)',  # B/L NO. 025E805626
            r'B\/L\s+NO\.\s*([A-Z0-9]+)',  # B/L NO. 025E805626
            r'B/L\s+No\.\s*([A-Z0-9]+)',  # B/L No. 025E805626
        ]
        
        for pattern in bl_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bl_no = match.group(1).strip()
                reference_parts.append(f"B/L NO. {bl_no}")
                break
        
        # ดึงชื่อไฟล์เก่า (ตัด VAT_, WHT_, None_vat_ และไม่เอา EXC_ กับข้อมูลที่อยู่ด้านหลัง)
        if filename:
            # ลบ VAT_, WHT_, None_vat_ ออกจากชื่อไฟล์
            cleaned = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename, flags=re.IGNORECASE)
            
            # ตัด EXC_ และข้อมูลที่อยู่ด้านหลังออก
            cleaned = re.sub(r'EXC_[^\s.]*', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'EXC-[^\s.]*', '', cleaned, flags=re.IGNORECASE)
            
            # ลบ .pdf
            cleaned = re.sub(r'\.pdf$', '', cleaned, flags=re.IGNORECASE)
            
            # ลบช่องว่างที่เหลือ
            cleaned = cleaned.strip()
            
            if cleaned and cleaned not in reference_parts:
                reference_parts.append(cleaned)
        
        # รวมอ้างอิง
        if reference_parts:
            return ' '.join(reference_parts)
        
        return None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # กำหนดชื่อบัญชีเป็น "ค่าใช้จ่ายในการขนส่ง" (ค่าคงที่)
        return {
            'account_name': 'ค่าใช้จ่ายในการขนส่ง',
            'account_code': None
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงยอดเงิน"""
        # Pattern: TT_SCB 7,000.00 TOTAL 7,000.00 (อ่านข้อมูลหลังจาก TOTAL)
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        # Total = Amount after TOTAL
        
        amount_before_vat = None
        vat_amount = 0.00  # ไม่มีภาษีมูลค่าเพิ่ม
        total_amount = None
        
        # ดึงยอดรวม: TOTAL 7,000.00 (อ่านข้อมูลหลังจาก TOTAL)
        total_patterns = [
            r'TOTAL\s+([\d,]+\.?\d*)',  # TOTAL 7,000.00
            r'Total\s+([\d,]+\.?\d*)',  # Total 7,000.00
            r'TOTAL\s*[:.]?\s*([\d,]+\.?\d*)',  # TOTAL: 7,000.00
            r'ยอดรวม\s*[:.]?\s*([\d,]+\.?\d*)',  # ยอดรวม: 7,000.00
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    total_amount = float(amount_str)
                    logger.info(f"✅ พบยอดรวม: {total_amount}")
                    break
                except ValueError:
                    continue
        
        # ถ้าพบยอดรวม ให้ใช้เป็นยอดก่อนภาษีและยอดรวม (เพราะไม่มีภาษีมูลค่าเพิ่ม)
        if total_amount is not None:
            amount_before_vat = total_amount
        
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
        return "1168/56,61 21st FLOOR, LUMPINI TOWER, RAMA 4 RD., THUNGMAHAMEK, SATHORN, BANGKOK 10120"
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (TI25111032 และ REF. : R2554C101631RUD และชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_)"""
        remark_parts = []
        
        # ดึงเลขที่เอกสาร (RECEIPT NO. TI25111032)
        document_number = self.extract_document_number(text)
        if document_number:
            remark_parts.append(document_number)
        
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
        ดึงข้อมูลทั้งหมดจากเอกสาร WAN HAI LINES
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร WAN HAI LINES หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร WAN HAI LINES LTD. C/O WAN HAI LINES (THAILAND) LTD.'
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
        building_number = '1168/56'
        other_info = '61 21st FLOOR, LUMPINI TOWER'
        soi = ''
        road = 'RAMA 4 RD.'
        subdistrict = 'THUNGMAHAMEK'
        district = 'SATHORN'
        province = 'BANGKOK'
        postal_code = '10120'
        
        # ตั้งค่า skip_amount_adjustment = True เพื่อไม่ให้ระบบปรับยอดเงิน (ใช้ค่าที่อ่านได้เท่านั้น)
        # เพราะเอกสารนี้ไม่มีภาษีมูลค่าเพิ่ม
        return {
            'success': True,
            'company': 'WAN_HAI_LINES',
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

