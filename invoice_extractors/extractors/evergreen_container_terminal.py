"""
Evergreen Container Terminal Invoice Extractor
==============================================
Extractor สำหรับดึงข้อมูลจาก บริษัท เอเวอร์กรีน คอนเทนเนอร์ เทอร์มินัล (ประเทศไทย) จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class EvergreenContainerTerminalExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท เอเวอร์กรีน คอนเทนเนอร์ เทอร์มินัล (ประเทศไทย) จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "บริษัท เอเวอร์กรีน คอนเทนเนอร์ เทอร์มินัล (ประเทศไทย) จำกัด",
        "เอเวอร์กรีน คอนเทนเนอร์ เทอร์มินัล",
        "Evergreen Container Terminal",
        "EVERGREEN"
    ]
    
    # Tax ID
    TAX_ID = "0105534033699"  # 0 10 5534 03369 9 (ลบช่องว่าง)
    
    def __init__(self):
        """Initialize Evergreen Container Terminal Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ บริษัท เอเวอร์กรีน คอนเทนเนอร์ เทอร์มินัล (ประเทศไทย) จำกัด หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท เอเวอร์กรีน คอนเทนเนอร์ เทอร์มินัล (ประเทศไทย) จำกัด"
        2. Tax ID "0 10 5534 03369 9" หรือ "0105534033699"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Evergreen Container Terminal (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0 10 5534 03369 9" หรือ "0105534033699"
        # รองรับทั้งรูปแบบที่มีช่องว่างและไม่มีช่องว่าง
        text_clean = text.replace(' ', '').replace('-', '')
        has_tax_id = (
            "0 10 5534 03369 9" in text or 
            "0105534033699" in text_clean or
            "0105534033699" in text
        )
        
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
        return "บริษัท เอเวอร์กรีน คอนเทนเนอร์ เทอร์มินัล (ประเทศไทย) จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: เลขประจำตัวผู้เสียภาษี : 0 10 5534 03369 9
        patterns = [
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*0\s*10\s*5534\s*03369\s*9',  # เลขประจำตัวผู้เสียภาษี : 0 10 5534 03369 9
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{1}\s+\d{2}\s+\d{4}\s+\d{5}\s+\d{1})',  # รูปแบบทั่วไป
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี: 0105534033699
            r'TAX\s+ID\s*[:.]?\s*0\s*10\s*5534\s*03369\s*9',  # TAX ID : 0 10 5534 03369 9
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID: 0105534033699
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0105534033699
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # ถ้าเป็นรูปแบบที่มีช่องว่าง
                if ' ' in match.group(0):
                    tax_id = match.group(0).replace(' ', '').replace(':', '').replace('.', '')
                    # ลบคำว่า "เลขประจำตัวผู้เสียภาษี" หรือ "TAX ID" ออก
                    tax_id = re.sub(r'[^\d]', '', tax_id)
                    if len(tax_id) == 13 and tax_id == self.TAX_ID:
                        return tax_id
                else:
                    tax_id = match.group(1).replace(' ', '').replace('-', '')
                    if len(tax_id) == 13 and tax_id == self.TAX_ID:
                        return tax_id
        
        # Fallback: ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่ (รองรับช่องว่าง)
        text_clean = text.replace(' ', '').replace('-', '')
        if self.TAX_ID in text_clean:
            return self.TAX_ID
        
        # Fallback: ถ้าไม่พบข้อมูล ให้ใช้ค่า default
        logger.info(f"⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา"""
        # Pattern: สาขาที่ออกใบกำกับภาษี : 00003 (Laemchabang B2)
        patterns = [
            r'สาขาที่ออกใบกำกับภาษี\s*[:.]?\s*(\d{5})',  # สาขาที่ออกใบกำกับภาษี : 00003
            r'สาขา\s*[:.]?\s*(\d{5})',  # สาขา: 00003
            r'Branch\s*[:.]?\s*(\d{5})',  # Branch: 00003
            r'สาขาที่ออกใบกำกับภาษี\s*[:.]?\s*(\d{1,5})',  # สาขาที่ออกใบกำกับภาษี : 3
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                branch = match.group(1).strip()
                branch_formatted = branch.zfill(5)  # เติม 0 นำหน้าให้ครบ 5 หลัก
                logger.info(f"✅ พบสาขา: {branch_formatted} (จาก: {branch})")
                return branch_formatted
        
        logger.warning("⚠️ ไม่พบสาขาในเอกสาร")
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: Date: 06/11/2025
        patterns = [
            r'Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # Date: 06/11/2025
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # วันที่: 06/11/2025
            r'Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2})',  # Date: 06/11/25
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                
                # ถ้าปีเป็น 2 หลัก ให้แปลงเป็น 4 หลัก
                if len(year) == 2:
                    year = '20' + year
                
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: No: RLI25017411 หรือ No: RL125017411
        patterns = [
            r'No\s*[:.]?\s*(RLI\d{8})',  # No: RLI25017411
            r'No\s*[:.]?\s*(RL\d{8})',  # No: RL125017411
            r'No\s*[:.]?\s*([A-Z]{2,3}\d{8,9})',  # No: RLI25017411 หรือ No: RL125017411
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: RLI25017411
            r'Document\s+No\s*[:.]?\s*([A-Z0-9]+)',  # Document No: RLI25017411
            r'Invoice\s+No\s*[:.]?\s*([A-Z0-9]+)',  # Invoice No: RLI25017411
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_number = match.group(1).strip()
                # ตรวจสอบว่าไม่ใช่ "B2" หรือตัวเลขสั้นๆ ที่ไม่ใช่เลขที่เอกสารจริง
                if len(doc_number) >= 8 and not doc_number.upper().startswith('B'):
                    return doc_number
        
        return None
    
    def extract_reference(self, text: str) -> Optional[str]:
        """ดึงอ้างอิง (Booking or B/L No)"""
        # Pattern: Booking or B/L No : | EGLV141500964551
        # รองรับทั้งรูปแบบที่มี | และไม่มี |
        patterns = [
            # รูปแบบที่มี | หลัง :
            r'Booking\s+or\s+B/L\s+No\s*[:.]?\s*\|\s*([A-Z0-9]+)',  # Booking or B/L No : | EGLV141500964551
            r'Booking\s+or\s+B/L\s+No\s*[:.]?\s*[^\w]*\|\s*([A-Z0-9]+)',  # Booking or B/L No : | EGLV141500964551 (มีตัวอักษรอื่นๆ)
            # รูปแบบที่ไม่มี | แต่มี : ตามด้วยช่องว่าง
            r'Booking\s+or\s+B/L\s+No\s*[:.]?\s+([A-Z0-9]+)',  # Booking or B/L No : EGLV141500964551
            r'Booking\s+or\s+B/L\s+No\s*[:.]?\s*([A-Z0-9]+)',  # Booking or B/L No: EGLV141500964551
            # รูปแบบ B/L No
            r'B/L\s+No\s*[:.]?\s*\|\s*([A-Z0-9]+)',  # B/L No : | EGLV141500964551
            r'B/L\s+No\s*[:.]?\s*[^\w]*\|\s*([A-Z0-9]+)',  # B/L No : | EGLV141500964551 (มีตัวอักษรอื่นๆ)
            r'B/L\s+No\s*[:.]?\s+([A-Z0-9]+)',  # B/L No : EGLV141500964551
            r'B/L\s+No\s*[:.]?\s*([A-Z0-9]+)',  # B/L No: EGLV141500964551
            # รูปแบบ Booking No
            r'Booking\s+No\s*[:.]?\s*\|\s*([A-Z0-9]+)',  # Booking No : | EGLV141500964551
            r'Booking\s+No\s*[:.]?\s*[^\w]*\|\s*([A-Z0-9]+)',  # Booking No : | EGLV141500964551 (มีตัวอักษรอื่นๆ)
            r'Booking\s+No\s*[:.]?\s+([A-Z0-9]+)',  # Booking No : EGLV141500964551
            r'Booking\s+No\s*[:.]?\s*([A-Z0-9]+)',  # Booking No: EGLV141500964551
            # รูปแบบทั่วไป (fallback)
            r'Booking[^\n]*?([A-Z]{4}\d{12})',  # Booking ... EGLV141500964551
            r'B/L[^\n]*?([A-Z]{4}\d{12})',  # B/L ... EGLV141500964551
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                reference = match.group(1).strip()
                # ตรวจสอบว่าเป็นรูปแบบที่ถูกต้อง (อย่างน้อย 10 ตัวอักษร)
                if len(reference) >= 10:
                    logger.info(f"✅ พบอ้างอิง: {reference}")
                    return reference
        
        logger.warning("⚠️ ไม่พบอ้างอิง (Booking or B/L No) ในเอกสาร")
        return None
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        # Pattern: WITHHOLDING TAX : 73.01 หรือ WITHHODING TAX : 73.01 (มี typo)
        # ถ้าไม่เท่ากับ 0.00 ให้เปอร์เซ็นต์หัก ณ ที่จ่ายเป็น 3
        patterns = [
            r'WITHHODING\s+TAX\s*[:.]?\s*([\d,]+\.?\d*)',  # WITHHODING TAX : 73.01 (มี typo)
            r'WITHHOLDING\s+TAX\s*[:.]?\s*([\d,]+\.?\d*)',  # WITHHOLDING TAX : 73.01
            r'Withholding\s+Tax\s*[:.]?\s*([\d,]+\.?\d*)',  # Withholding Tax : 73.01
            r'หัก\s+ภาษี\s*ณ\.?\s*ที่จ่าย\s*[:.]?\s*([\d,]+\.?\d*)',  # หักภาษี ณ. ที่จ่าย : 73.01
            r'WHT\s*[:.]?\s*([\d,]+\.?\d*)',  # WHT : 73.01
        ]
        
        withholding_tax_amount = None
        withholding_tax_percent = None
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    withholding_tax_amount = float(amount_str)
                    # ถ้าไม่เท่ากับ 0.00 ให้เปอร์เซ็นต์หัก ณ ที่จ่ายเป็น 3
                    if withholding_tax_amount != 0.00:
                        withholding_tax_percent = 3.0
                    else:
                        withholding_tax_percent = None
                    logger.info(f"✅ พบหัก ณ ที่จ่าย: {withholding_tax_amount} บาท, เปอร์เซ็นต์: {withholding_tax_percent}%")
                    break
                except ValueError:
                    continue
        
        return {
            'withholding_tax_amount': withholding_tax_amount,
            'withholding_tax_percent': withholding_tax_percent
        }
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # กำหนดชื่อบัญชีเป็น "ค่าใช้จ่ายอื่นๆในการซื้อสินค้า" (ค่าคงที่)
        return {
            'account_name': 'ค่าใช้จ่ายอื่นๆในการซื้อสินค้า',
            'account_code': None
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงยอดเงิน"""
        # Pattern: TOTAL CHARGE : 2,433.64
        # Pattern: VAT 7% : 170.35
        # Pattern: GRAND TOTAL : 2,603.99
        
        amount_before_vat = None
        vat_amount = None
        total_amount = None
        
        # ดึงยอดก่อนภาษี: TOTAL CHARGE : 2,433.64
        total_charge_patterns = [
            r'TOTAL\s+CHARGE\s*[:.]?\s*([\d,]+\.?\d*)',  # TOTAL CHARGE : 2,433.64
            r'Total\s+Charge\s*[:.]?\s*([\d,]+\.?\d*)',  # Total Charge : 2,433.64
            r'ยอดก่อนภาษี\s*[:.]?\s*([\d,]+\.?\d*)',  # ยอดก่อนภาษี: 2,433.64
        ]
        
        for pattern in total_charge_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    amount_before_vat = float(amount_str)
                    logger.info(f"✅ พบยอดก่อนภาษี: {amount_before_vat}")
                    break
                except ValueError:
                    continue
        
        # ดึงภาษีมูลค่าเพิ่ม: VAT 7% : 170.35
        vat_patterns = [
            r'VAT\s+7%\s*[:.]?\s*([\d,]+\.?\d*)',  # VAT 7% : 170.35
            r'VAT\s*[:.]?\s*([\d,]+\.?\d*)',  # VAT : 170.35
            r'ภาษีมูลค่าเพิ่ม\s*[:.]?\s*([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม: 170.35
        ]
        
        for pattern in vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    vat_amount = float(amount_str)
                    logger.info(f"✅ พบภาษีมูลค่าเพิ่ม: {vat_amount}")
                    break
                except ValueError:
                    continue
        
        # ดึงยอดรวม: GRAND TOTAL : 2,603.99
        grand_total_patterns = [
            r'GRAND\s+TOTAL\s*[:.]?\s*([\d,]+\.?\d*)',  # GRAND TOTAL : 2,603.99
            r'Grand\s+Total\s*[:.]?\s*([\d,]+\.?\d*)',  # Grand Total : 2,603.99
            r'ยอดรวม\s*[:.]?\s*([\d,]+\.?\d*)',  # ยอดรวม: 2,603.99
        ]
        
        for pattern in grand_total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    total_amount = float(amount_str)
                    logger.info(f"✅ พบยอดรวม: {total_amount}")
                    break
                except ValueError:
                    continue
        
        # ถ้าไม่พบยอดรวม แต่มียอดก่อนภาษีและภาษีมูลค่าเพิ่ม ให้คำนวณ
        if total_amount is None and amount_before_vat is not None and vat_amount is not None:
            total_amount = amount_before_vat + vat_amount
            logger.info(f"✅ คำนวณยอดรวม: {total_amount} (จาก {amount_before_vat} + {vat_amount})")
        
        return {
            'amount_before_vat': amount_before_vat,
            'vat_amount': vat_amount,
            'total_amount': total_amount
        }
    
    def extract_address(self, text: str) -> str:
        """ดึงที่อยู่"""
        # กำหนดที่อยู่เป็นค่าคงที่
        return "อาคารท่าเทียบเรือพาณิชย์แหลมฉบัง ท่าหมายเลข 2 ต.ทุ่งสุขลา อ.ศรีราชา จ.ชลบุรี 20230"
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (เอาชื่อไฟล์เก่า ไม่เอา VAT_ WHT_ None_vat)"""
        if not filename:
            return None
        
        # ลบ VAT_, WHT_, None_vat_ ออกจากชื่อไฟล์
        cleaned = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename, flags=re.IGNORECASE)
        return cleaned.strip() if cleaned else None
    
    def clean_filename(self, filename: str) -> str:
        """ทำความสะอาดชื่อไฟล์ (ลบ VAT_, WHT_, None_vat_)"""
        if not filename:
            return filename
        
        cleaned = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename, flags=re.IGNORECASE)
        return cleaned.strip()
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร"""
        # ถ้ามี VAT หรือ WHT แสดงว่ามีภาษีมูลค่าเพิ่ม
        vat_amount = amounts.get('vat_amount', 0) or 0
        withholding_tax_percent = withholding.get('withholding_tax_percent', 0) or 0
        
        if vat_amount > 0 or withholding_tax_percent > 0:
            return 1  # มีภาษีมูลค่าเพิ่ม
        
        return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร Evergreen Container Terminal
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร Evergreen Container Terminal หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร บริษัท เอเวอร์กรีน คอนเทนเนอร์ เทอร์มินัล (ประเทศไทย) จำกัด'
            }
        
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
        new_filename = self.clean_filename(filename) if filename else filename
        
        # แยกที่อยู่เป็นส่วนๆ
        address_full = address or ''
        building_number = ''
        other_info = 'อาคารท่าเทียบเรือพาณิชย์แหลมฉบัง ท่าหมายเลข 2'
        soi = ''
        road = ''
        subdistrict = 'ทุ่งสุขลา'
        district = 'ศรีราชา'
        province = 'ชลบุรี'
        postal_code = '20230'
        
        return {
            'success': True,
            'company': 'EVERGREEN',
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

