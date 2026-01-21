"""
Grab Invoice Extractor
=======================
Extractor สำหรับดึงข้อมูลจาก Grabtaxi (Thailand) Co., Ltd. (Head Office)

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class GrabExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก Grabtaxi (Thailand) Co., Ltd. (Head Office)"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "Grabtaxi (Thailand) Co., Ltd.",
        "Grabtaxi (Thailand)",
        "Grab",
        "บริษัท แกร็บแท็กซี่ (ประเทศไทย) จำกัด"
    ]
    
    # Tax ID
    TAX_ID = "0105556090377"
    
    def __init__(self):
        """Initialize Grab Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Grabtaxi (Thailand) Co., Ltd. หรือไม่
        ต้องมีทั้ง 4 เงื่อนไข:
        1. ชื่อบริษัท "Grabtaxi (Thailand) Co., Ltd. (Head Office)"
        2. Tax ID "0105556090377"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        4. รายการ "Service Fee" หรือ "Ads per click"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Grabtaxi (Thailand) (มีทั้ง 4 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105556090377"
        has_tax_id = self.TAX_ID in text
        
        # เงื่อนไข 3: ต้องมีเอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        has_document_type = (
            "ใบเสร็จรับเงิน" in text or 
            "ใบกำกับภาษี" in text or 
            "RECEIPT" in text.upper() or 
            "TAX INVOICE" in text.upper()
        )
        
        # เงื่อนไข 4: ต้องมีรายการ "Service Fee", "Ads per click", หรือ "Advertising fees"
        has_service_fee = "Service Fee" in text
        has_ads_per_click = "Ads per click" in text or "Ads Per Click" in text or "ads per click" in text.lower()
        has_advertising_fees = "Advertising fees" in text or "Advertising Fees" in text or "advertising fees" in text.lower()
        
        # ต้องมีทั้ง 4 เงื่อนไขถึงจะผ่าน (เงื่อนไข 4: ต้องมี Service Fee, Ads per click, หรือ Advertising fees)
        return has_company and has_tax_id and has_document_type and (has_service_fee or has_ads_per_click or has_advertising_fees)
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "Grabtaxi (Thailand) Co., Ltd. (Head Office)"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TAX ID 0105556090377
        patterns = [
            r'TAX\s+ID\s+(\d{13})',  # TAX ID 0105556090377
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID: 0105556090377
            r'Tax\s+ID\s+(\d{13})',  # Tax ID 0105556090377
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0105556090377
            r'TaxID\s*[:.]?\s*(\d{13})',  # TaxID: 0105556090377
            r'TAXID\s*[:.]?\s*(\d{13})',  # TAXID: 0105556090377
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี: 0105556090377
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร: 0105556090377
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id = match.group(1).replace(' ', '').replace('-', '')
                if len(tax_id) == 13 and tax_id == self.TAX_ID:
                    return tax_id
        
        # Fallback: ถ้าไม่พบข้อมูล ให้ใช้ค่า default
        logger.info(f"⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: วันที่/Date 01/11/2025
        patterns = [
            r'วันที่/Date\s+(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # วันที่/Date 01/11/2025
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # วันที่: 01/11/2025
            r'Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # Date: 01/11/2025
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
        # Pattern: เลขที่/No. IM20251101073348
        patterns = [
            r'เลขที่/No\.\s+([A-Z0-9]+)',  # เลขที่/No. IM20251101073348
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: IM20251101073348
            r'No\.\s*[:.]?\s*([A-Z0-9]+)',  # No.: IM20251101073348
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # Document No: IM20251101073348
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                if len(doc_num) >= 6:
                    return doc_num
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: 252 SPE Tower, 10th floor, Phahonyothin Rd, Samsen Nai, Phaya Thai, Bangkok 10400
        
        Returns:
            ที่อยู่รวม (string)
        """
        # ใช้ที่อยู่ที่กำหนดให้
        return "252 SPE Tower, 10th floor, Phahonyothin Rd, Samsen Nai, Phaya Thai, Bangkok 10400"
    
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
                'amount_before_vat': float,  # ยอดก่อนภาษี (261.29)
                'vat_amount': float,          # ยอดภาษี (18.29)
                'total_amount': float         # ยอดรวม (279.58)
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # Pattern 1: รวมมูลค่าสินค้าและบริการ Total Amount 261.29
        patterns_before_vat = [
            r'รวมมูลค่าสินค้าและบริการ\s+Total\s+Amount\s+([\d,]+\.?\d{2})',  # รวมมูลค่าสินค้าและบริการ Total Amount 261.29
            r'Total\s+Amount\s+([\d,]+\.?\d{2})',  # Total Amount 261.29
            r'รวมมูลค่าสินค้าและบริการ\s*[:.]?\s*([\d,]+\.?\d{2})',  # รวมมูลค่าสินค้าและบริการ: 261.29
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
        
        # Pattern 2: ภาษีมูลค่าเพิ่ม VAT 7 % 18.29
        patterns_vat = [
            r'ภาษีมูลค่าเพิ่ม\s+VAT\s+7\s*%\s+([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม VAT 7 % 18.29
            r'ภาษีมูลค่าเพิ่ม\s+VAT\s*7\s*%\s+([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม VAT 7% 18.29
            r'VAT\s+7\s*%\s+([\d,]+\.?\d{2})',  # VAT 7 % 18.29
            r'ภาษีมูลค่าเพิ่ม\s*[:.]?\s*([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม: 18.29
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
        
        # Pattern 3: จำนวนเงินรวมทั้งสิ้น Grand Total 279.58
        patterns_total = [
            r'จำนวนเงินรวมทั้งสิ้น\s+Grand\s+Total\s+([\d,]+\.?\d{2})',  # จำนวนเงินรวมทั้งสิ้น Grand Total 279.58
            r'Grand\s+Total\s+([\d,]+\.?\d{2})',  # Grand Total 279.58
            r'จำนวนเงินรวมทั้งสิ้น\s*[:.]?\s*([\d,]+\.?\d{2})',  # จำนวนเงินรวมทั้งสิ้น: 279.58
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
        """ดึงหมายเหตุ"""
        # ไม่มี remark สำหรับ Grab
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
        ดึงข้อมูลทั้งหมดจากเอกสาร Grabtaxi (Thailand)
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร Grabtaxi (Thailand) หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร Grabtaxi (Thailand)'
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
        
        # สร้างชื่อไฟล์ใหม่ตามประเภทรายการ
        # ถ้าเป็น "Ads per click" หรือ "Advertising fees" ให้ใช้ "ค่าโฆษณา Grab"
        # ถ้าเป็น "Service Fee" ให้ใช้ "ค่าบริการ Grab"
        if ("Ads per click" in text or "Ads Per Click" in text or "ads per click" in text.lower() or
            "Advertising fees" in text or "Advertising Fees" in text or "advertising fees" in text.lower()):
            new_filename = "ค่าโฆษณา Grab"
        else:
            new_filename = "ค่าบริการ Grab"
        
        # แยกที่อยู่เป็นส่วนๆ
        # ที่อยู่: 252 SPE Tower, 10th floor, Phahonyothin Rd, Samsen Nai, Phaya Thai, Bangkok 10400
        address_full = address or ''
        building_number = '252'  # เลขที่
        other_info = 'SPE Tower, 10th floor'  # อื่นๆ
        soi = ''  # ซอย/ตรอก
        road = 'Phahonyothin Rd'  # ถนน
        subdistrict = 'Samsen Nai'  # แขวง
        district = 'Phaya Thai'  # เขต
        province = 'Bangkok'  # จังหวัด
        postal_code = '10400'  # รหัสไปรษณีย์
        
        return {
            'success': True,
            'company': 'GRAB',
            'company_name': company_name,
            'tax_id': tax_id,
            'date': date,
            'document_number': document_number,
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number,  # เลขที่ (252)
            'other_info': other_info,  # อื่นๆ (SPE Tower, 10th floor)
            'soi': soi,  # ซอย/ตรอก
            'road': road,  # ถนน (Phahonyothin Rd)
            'subdistrict': subdistrict,  # แขวง (Samsen Nai)
            'district': district,  # เขต (Phaya Thai)
            'province': province,  # จังหวัด (Bangkok)
            'postal_code': postal_code,  # รหัสไปรษณีย์ (10400)
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

