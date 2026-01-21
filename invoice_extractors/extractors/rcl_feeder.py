"""
RCL Feeder Invoice Extractor
============================
Extractor สำหรับดึงข้อมูลจาก บริษัท อาร์ซีแอล ฟีดเดอร์ พีทีอี จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class RCLFeederExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท อาร์ซีแอล ฟีดเดอร์ พีทีอี จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "บริษัท อาร์ซีแอล ฟีดเดอร์ พีทีอี จำกัด",
        "อาร์ซีแอล ฟีดเดอร์",
        "RCL FEEDER",
        "RCL"
    ]
    
    # Tax ID
    TAX_ID = "099300008614"
    
    def __init__(self):
        """Initialize RCL Feeder Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ บริษัท อาร์ซีแอล ฟีดเดอร์ พีทีอี จำกัด หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท อาร์ซีแอล ฟีดเดอร์ พีทีอี จำกัด"
        2. Tax ID "099300008614"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร RCL Feeder (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "099300008614"
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
        return "บริษัท อาร์ซีแอล ฟีดเดอร์ พีทีอี จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: เลขประจำตัวผู้เสียภาษี 099300008614
        patterns = [
            r'เลขประจำตัวผู้เสียภาษี\s+(\d{12})',  # เลขประจำตัวผู้เสียภาษี 099300008614
            r'เลขประจำตัวผู้เสียภาษีอากร\s+(\d{12})',  # เลขประจำตัวผู้เสียภาษีอากร 099300008614
            r'TAX\s+ID\s*[:.]?\s*(\d{12})',  # TAX ID: 099300008614
            r'Tax\s+ID\s*[:.]?\s*(\d{12})',  # Tax ID: 099300008614
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id = match.group(1).strip()
                if len(tax_id) == 12 and tax_id == self.TAX_ID:
                    return tax_id
        
        # Fallback: ถ้าไม่พบข้อมูล ให้ใช้ค่า default
        logger.info(f"⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา"""
        # Pattern: สาขา 00002
        patterns = [
            r'สาขา\s+(\d{5})',  # สาขา 00002
            r'Branch\s*[:.]?\s*(\d{5})',  # Branch: 00002
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                branch = match.group(1).strip()
                return branch
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: วันที่ DATE 31/10/2025
        patterns = [
            r'วันที่\s+DATE\s+(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # วันที่ DATE 31/10/2025
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # วันที่: 31/10/2025
            r'DATE\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DATE: 31/10/2025
            r'Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # Date: 31/10/2025
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
        # Pattern: เลขที่ NO. F-825103801
        patterns = [
            r'เลขที่\s+NO[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',  # เลขที่ NO. F-825103801
            r'เลขที่\s*[:.]?\s*([A-Z0-9\-]+)',  # เลขที่: F-825103801
            r'NO[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',  # NO.: F-825103801
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',  # Document No.: F-825103801
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                return doc_num
        
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง (ชื่อไฟล์เก่า ตัด VAT_, WHT_, None_vat_ และไม่เอา EXC_ กับข้อมูลที่อยู่ด้านหลัง และไม่เอา .pdf)"""
        if not filename:
            return None
        
        # ลบ VAT_, WHT_, None_vat_ ออกจากชื่อไฟล์
        cleaned = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename, flags=re.IGNORECASE)
        
        # ตัด EXC_ และข้อมูลที่อยู่ด้านหลังออก (ไม่เอา EXC_ และข้อมูลที่อยู่ด้านหลัง)
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
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงยอดเงิน"""
        # Pattern: จำนวนเงินรวมทั้งสิ้น Grand Total 7,100.00
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        
        amount_before_vat = None
        vat_amount = 0.00  # ไม่มีภาษีมูลค่าเพิ่ม
        total_amount = None
        
        if not text:
            logger.warning("⚠️ ไม่มีข้อความสำหรับดึงยอดเงิน")
            return {
                'amount_before_vat': amount_before_vat,
                'vat_amount': vat_amount,
                'total_amount': total_amount
            }
        
        # ดึงยอดก่อนภาษี: จำนวนเงินรวมทั้งสิ้น Grand Total 7,100.00
        amount_patterns = [
            r'จำนวนเงินรวมทั้งสิ้น\s+Grand\s+Total\s+([\d,]+\.\d{2})',  # จำนวนเงินรวมทั้งสิ้น Grand Total 7,100.00
            r'จำนวนเงินรวมทั้งสิ้น\s+Grand\s+Total\s+([\d,]+\.?\d*)',  # จำนวนเงินรวมทั้งสิ้น Grand Total 7,100
            r'Grand\s+Total\s+([\d,]+\.\d{2})',  # Grand Total 7,100.00
            r'Grand\s+Total\s+([\d,]+\.?\d*)',  # Grand Total 7,100
            r'จำนวนเงินรวมทั้งสิ้น\s+([\d,]+\.\d{2})',  # จำนวนเงินรวมทั้งสิ้น 7,100.00
            r'จำนวนเงินรวมทั้งสิ้น\s+([\d,]+\.?\d*)',  # จำนวนเงินรวมทั้งสิ้น 7,100
            r'TOTAL\s+([\d,]+\.\d{2})',  # TOTAL 7,100.00
            r'TOTAL\s+([\d,]+\.?\d*)',  # TOTAL 7,100
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    amount_value = float(amount_str)
                    if amount_value > 0:
                        amount_before_vat = amount_value
                        logger.info(f"✅ พบยอดก่อนภาษี: {amount_before_vat} (จาก pattern: {pattern})")
                        break
                except ValueError as e:
                    logger.warning(f"⚠️ ไม่สามารถแปลง {amount_str} เป็น float: {e}")
                    continue
        
        if amount_before_vat is None:
            logger.warning("⚠️ ไม่พบยอดก่อนภาษีในเอกสาร")
        
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        vat_amount = 0.00
        
        # ยอดรวม = ยอดก่อนภาษี (เพราะไม่มีภาษี)
        if amount_before_vat is not None:
            total_amount = amount_before_vat
        else:
            total_amount = None
        
        return {
            'amount_before_vat': amount_before_vat,
            'vat_amount': vat_amount,
            'total_amount': total_amount
        }
    
    def extract_address(self, text: str) -> str:
        """ดึงที่อยู่"""
        # กำหนดที่อยู่เป็นค่าคงที่
        return "127/1 ถนนรัชดาภิเษก แขวงช่องนนทรี เขตยานนาวา กรุงเทพฯ 10120"
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (REF. : R2554C101631RUD และชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_)"""
        remark_parts = []
        
        # ดึง REF. : R2554C101631RUD
        ref_patterns = [
            r'REF[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # REF. : R2554C101631RUD
            r'Ref[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # Ref. : R2554C101631RUD
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ref_value = match.group(1).strip()
                remark_parts.append(f"REF. : {ref_value}")
                break
        
        # ดึงชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_ (ถ้ามี)
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
        ดึงข้อมูลทั้งหมดจากเอกสาร RCL Feeder
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร RCL Feeder หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร บริษัท อาร์ซีแอล ฟีดเดอร์ พีทีอี จำกัด'
            }
        
        # ใช้ text เดิมทั้งหมดในการดึงข้อมูล
        logger.info(f"✅ ใช้ text เดิมทั้งหมดในการดึงข้อมูล (ความยาว: {len(text)} ตัวอักษร)")
        
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
        # ที่อยู่: 127/1 ถนนรัชดาภิเษก แขวงช่องนนทรี เขตยานนาวา กรุงเทพฯ 10120
        address_full = address or ''
        building_number = '127/1'
        other_info = ''
        soi = ''
        road = 'ถนนรัชดาภิเษก'
        subdistrict = 'ช่องนนทรี'
        district = 'ยานนาวา'
        province = 'กรุงเทพมหานคร'
        postal_code = '10120'
        
        return {
            'success': True,
            'company': 'RCL_FEEDER',
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
            'filepath': filepath,  # เพิ่ม filepath
            'document_type': document_type,
            'skip_amount_adjustment': True  # สำหรับเอกสารไม่มีภาษีมูลค่าเพิ่ม - ใช้ค่าที่อ่านได้เท่านั้น (ไม่ต้องคำนวณ)
        }

