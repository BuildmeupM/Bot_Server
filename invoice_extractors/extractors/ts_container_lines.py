"""
TS Container Lines Invoice Extractor
====================================
Extractor สำหรับดึงข้อมูลจาก บริษัท ที เอส คอนเทนเนอร์ ไลน์ (ประเทศไทย) จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class TSContainerLinesExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท ที เอส คอนเทนเนอร์ ไลน์ (ประเทศไทย) จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "บริษัท ที เอส คอนเทนเนอร์ ไลน์ (ประเทศไทย) จำกัด",
        "บริษัท ทีเอส คอนเทนเนอร์ ไลน์ พีทีอี จำกัด",
        "TS CONTAINER LINES PTE. LTD. C/O T'S CONTAINER LINES (THAILAND) CO.,LTD.",
        "TS CONTAINER LINES",
        "T'S CONTAINER LINES (THAILAND)"
    ]
    
    # Tax ID (รูปแบบที่มี -)
    TAX_ID_WITH_DASH = "099-3-00051215-4"
    # Tax ID (รูปแบบที่เอา - ออก)
    TAX_ID = "0993000512154"
    
    def __init__(self):
        """Initialize TS Container Lines Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ บริษัท ที เอส คอนเทนเนอร์ ไลน์ (ประเทศไทย) จำกัด หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท ที เอส คอนเทนเนอร์ ไลน์ (ประเทศไทย) จำกัด"
        2. Tax ID "099-3-00051215-4"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร TS Container Lines (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier.upper() in text.upper() for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "099-3-00051215-4" หรือ "0993000512154"
        has_tax_id = self.TAX_ID_WITH_DASH in text or self.TAX_ID in text or "099-3-00051215-4" in text
        
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
        return "บริษัท ที เอส คอนเทนเนอร์ ไลน์ (ประเทศไทย) จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี (เอา - ออก)"""
        # Pattern: เลขประจำตัวผู้เสียภาษี / Tax Identification Number 099-3-00051215-4 สำนักงานใหญ่/Head Office
        patterns = [
            r'เลขประจำตัวผู้เสียภาษี\s*/\s*Tax\s+Identification\s+Number\s*(\d{3}[\-]\d[\-]\d{8}[\-]\d)',  # เลขประจำตัวผู้เสียภาษี / Tax Identification Number 099-3-00051215-4
            r'Tax\s+Identification\s+Number\s*(\d{3}[\-]\d[\-]\d{8}[\-]\d)',  # Tax Identification Number 099-3-00051215-4
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{3}[\-]\d[\-]\d{8}[\-]\d)',  # เลขประจำตัวผู้เสียภาษี: 099-3-00051215-4
            r'(\d{3}[\-]\d[\-]\d{8}[\-]\d)',  # 099-3-00051215-4
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id_with_dash = match.group(1).strip()
                # เอา - ออก
                tax_id = tax_id_with_dash.replace('-', '')
                if tax_id == self.TAX_ID or tax_id_with_dash == self.TAX_ID_WITH_DASH:
                    logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษี: {tax_id_with_dash} → {tax_id}")
                    return tax_id
        
        # Fallback: ถ้าไม่พบข้อมูล ให้ใช้ค่า default
        logger.info(f"⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา"""
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: วันที่ : DATE 2025/11/05
        patterns = [
            r'วันที่\s*[:.]?\s*DATE\s*(\d{4})/(\d{1,2})/(\d{1,2})',  # วันที่ : DATE 2025/11/05
            r'DATE\s*(\d{4})/(\d{1,2})/(\d{1,2})',  # DATE 2025/11/05
            r'วันที่\s*[:.]?\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # วันที่: 05/11/2025
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    # รูปแบบ 2025/11/05
                    if len(match.group(1)) == 4:
                        year = match.group(1)
                        month = match.group(2).zfill(2)
                        day = match.group(3).zfill(2)
                        return f"{day}/{month}/{year}"
                    # รูปแบบ 05/11/2025
                    else:
                        day = match.group(1).zfill(2)
                        month = match.group(2).zfill(2)
                        year = match.group(3)
                        return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: เลขที่ : NO. 3202511BRCT00282
        patterns = [
            r'เลขที่\s*[:.]?\s*NO\.\s*([A-Z0-9]+)',  # เลขที่ : NO. 3202511BRCT00282
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: 3202511BRCT00282
            r'NO\.\s*[:.]?\s*([A-Z0-9]+)',  # NO. : 3202511BRCT00282
            r'Document\s+No\.\s*[:.]?\s*([A-Z0-9]+)',  # Document No. : 3202511BRCT00282
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_number = match.group(1).strip()
                # ตรวจสอบว่าไม่ใช่ตัวเลขล้วนๆ
                if re.match(r'^\d+$', doc_number):
                    continue
                logger.info(f"✅ พบเลขที่เอกสาร: {doc_number}")
                return doc_number
        
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง (ชื่อไฟล์เก่า)"""
        reference_parts = []
        
        # ดึงชื่อไฟล์เก่า (ตัด VAT_, WHT_, None_vat_ และไม่เอา EXC_ กับข้อมูลที่อยู่ด้านหลัง และไม่เอา .pdf)
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
            
            if cleaned:
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
        # Pattern: จำนวนเงินรวมทั้งสิ้น GRAND TOTAL 17250.00
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        
        amount_before_vat = None
        vat_amount = 0.00  # ไม่มีภาษีมูลค่าเพิ่ม
        total_amount = None
        
        # ดึงยอดรวม: จำนวนเงินรวมทั้งสิ้น GRAND TOTAL 17250.00
        total_patterns = [
            r'จำนวนเงินรวมทั้งสิ้น\s+GRAND\s+TOTAL\s*([\d,]+\.?\d{2})',  # จำนวนเงินรวมทั้งสิ้น GRAND TOTAL 17250.00
            r'GRAND\s+TOTAL\s*([\d,]+\.?\d{2})',  # GRAND TOTAL 17250.00
            r'TOTAL\s*[:.]?\s*([\d,]+\.?\d{2})',  # TOTAL: 17250.00
            r'ยอดรวม\s*[:.]?\s*([\d,]+\.?\d{2})',  # ยอดรวม: 17250.00
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
        
        # ถ้าพบยอดรวม ให้ใช้เป็นยอดก่อนภาษีด้วย (เพราะไม่มีภาษี)
        if total_amount is not None:
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
        return "193/87-88 Lake Rama 6, Office Complex, 21st Fl., Rachadapisek Rd., Klongtoey, Bangkok 10110"
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (ชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_)"""
        remark_parts = []
        
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
        ดึงข้อมูลทั้งหมดจากเอกสาร TS Container Lines
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร TS Container Lines หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร บริษัท ที เอส คอนเทนเนอร์ ไลน์ (ประเทศไทย) จำกัด'
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
        building_number = '193/87-88'
        other_info = 'Lake Rama 6, Office Complex, 21st Fl.'
        soi = ''
        road = 'Rachadapisek Rd.'
        subdistrict = 'Klongtoey'
        district = 'Klongtoey'
        province = 'Bangkok'
        postal_code = '10110'
        
        # ตั้งค่า skip_amount_adjustment = True เพื่อไม่ให้ระบบปรับยอดเงิน (ใช้ค่าที่อ่านได้เท่านั้น)
        # เพราะเอกสารนี้ไม่มีภาษีมูลค่าเพิ่ม
        return {
            'success': True,
            'company': 'TS_CONTAINER_LINES',
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

