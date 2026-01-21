"""
Union World Shipping Invoice Extractor
======================================
Extractor สำหรับดึงข้อมูลจาก UNION WORLD SHIPPING (THAILAND) CO., LTD.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class UnionWorldShippingExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก UNION WORLD SHIPPING (THAILAND) CO., LTD."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "UNION WORLD SHIPPING (THAILAND) CO., LTD.",
        "UNION WORLD SHIPPING (THAILAND)",
        "UNION WORLD SHIPPING",
        "UNION WORLD"
    ]
    
    # Tax ID
    TAX_ID = "0105568036909"
    
    def __init__(self):
        """Initialize Union World Shipping Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ UNION WORLD SHIPPING (THAILAND) CO., LTD. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "UNION WORLD SHIPPING (THAILAND) CO., LTD."
        2. Tax ID "0105568036909"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร UNION WORLD SHIPPING (THAILAND) (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105568036909"
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
        # หาชื่อบริษัทจาก "UNION WORLD SHIPPING (THAILAND) CO., LTD. (HEAD OFFICE)"
        # แต่ return เป็น "UNION WORLD SHIPPING (THAILAND)"
        return "UNION WORLD SHIPPING (THAILAND)"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TAX ID : 0105568036909
        patterns = [
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID : 0105568036909
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID : 0105568036909
            r'TaxID\s*[:.]?\s*(\d{13})',  # TaxID: 0105568036909
            r'TAXID\s*[:.]?\s*(\d{13})',  # TAXID: 0105568036909
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี: 0105568036909
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร: 0105568036909
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
        # Pattern: DATE : 17-Nov-25
        # ต้องแปลงจาก 17-Nov-25 เป็น 17/11/2025
        patterns = [
            r'DATE\s*[:.]?\s*(\d{1,2})[-/](\w{3})[-/](\d{2,4})',  # DATE : 17-Nov-25 หรือ DATE: 17-Nov-2025
            r'วันที่\s*[:.]?\s*(\d{1,2})[-/](\w{3})[-/](\d{2,4})',  # วันที่: 17-Nov-25
        ]
        
        # Mapping เดือน
        month_map = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month_str = match.group(2).lower()[:3]  # เอา 3 ตัวแรก
                year_str = match.group(3)
                
                # แปลงเดือน
                month = month_map.get(month_str, '01')
                
                # แปลงปี (ถ้าเป็น 2 หลัก ให้แปลงเป็น 4 หลัก)
                if len(year_str) == 2:
                    year = '20' + year_str
                else:
                    year = year_str
                
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: TAX INVOICE NO. : RC25110310
        patterns = [
            r'TAX\s+INVOICE\s+NO[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # TAX INVOICE NO. : RC25110310
            r'Tax\s+Invoice\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # Tax Invoice No: RC25110310
            r'INVOICE\s+NO[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # INVOICE NO: RC25110310
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: RC25110310
            r'No\.\s*[:.]?\s*([A-Z0-9]+)',  # No.: RC25110310
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
        
        ที่อยู่: 19/65 SUKHUMVIT SUITE BUILDING, 9TH FLOOR, SOI SUKHMVIT 13 (SAENGCHAN), KHLONG TOEI NUEA, VADHANA, BANGKOK 10110
        
        Returns:
            ที่อยู่รวม (string)
        """
        # ใช้ที่อยู่ที่กำหนดให้
        return "19/65 SUKHUMVIT SUITE BUILDING, 9TH FLOOR, SOI SUKHMVIT 13 (SAENGCHAN), KHLONG TOEI NUEA, VADHANA, BANGKOK 10110"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # ชื่อบัญชี: ค่าใช้จ่ายในการขนส่ง (ค่าคงที่)
        return {
            'account_name': 'ค่าใช้จ่ายในการขนส่ง',
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        # เปอร์เซ็นต์หัก ณ ที่จ่าย: 3% (ค่าคงที่)
        return {
            'withholding_tax_percent': 3.0,
            'withholding_tax_amount': 0.0  # จะคำนวณจากยอดก่อนภาษี * 3%
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (8,550.00)
                'vat_amount': float,          # ยอดภาษี (598.50)
                'total_amount': float         # ยอดรวม (9,148.50)
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # Pattern 1: จำนวนเงินก่อนภาษี (AMOUNT) 8,550.00
        patterns_before_vat = [
            r'จำนวนเงินก่อนภาษี\s*\(AMOUNT\)\s+([\d,]+\.?\d{0,2})',  # จำนวนเงินก่อนภาษี (AMOUNT) 8,550.00
            r'AMOUNT\s+([\d,]+\.?\d{0,2})',  # AMOUNT 8,550.00
            r'จำนวนเงินก่อนภาษี\s*[:.]?\s*([\d,]+\.?\d{0,2})',  # จำนวนเงินก่อนภาษี: 8,550.00
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
        
        # Pattern 2: ภาษีมูลค่าเพิ่ม (VAT 7%) 598.50
        patterns_vat = [
            r'ภาษีมูลค่าเพิ่ม\s*\(VAT\s+7%\)\s+([\d,]+\.?\d{0,2})',  # ภาษีมูลค่าเพิ่ม (VAT 7%) 598.50
            r'ภาษีมูลค่าเพิ่ม\s*\(VAT\s*7\s*%\)\s+([\d,]+\.?\d{0,2})',  # ภาษีมูลค่าเพิ่ม (VAT 7 %) 598.50
            r'VAT\s+7%\s+([\d,]+\.?\d{0,2})',  # VAT 7% 598.50
            r'ภาษีมูลค่าเพิ่ม\s*[:.]?\s*([\d,]+\.?\d{0,2})',  # ภาษีมูลค่าเพิ่ม: 598.50
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
        
        # Pattern 3: จำนวนเงินรวมทั้งสิ้น (TOTAL) 9,148.50
        patterns_total = [
            r'จำนวนเงินรวมทั้งสิ้น\s*\(TOTAL\)\s+([\d,]+\.?\d{0,2})',  # จำนวนเงินรวมทั้งสิ้น (TOTAL) 9,148.50
            r'TOTAL\s+([\d,]+\.?\d{0,2})',  # TOTAL 9,148.50
            r'จำนวนเงินรวมทั้งสิ้น\s*[:.]?\s*([\d,]+\.?\d{0,2})',  # จำนวนเงินรวมทั้งสิ้น: 9,148.50
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
        # Pattern: REF. INVOICE NO. : IN25110309
        patterns = [
            r'REF\.\s+INVOICE\s+NO[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # REF. INVOICE NO. : IN25110309
            r'Ref\.\s+Invoice\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # Ref. Invoice No: IN25110309
            r'REF\s+INVOICE\s+NO[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # REF INVOICE NO: IN25110309
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                remark = match.group(1).strip()
                if len(remark) >= 6:
                    return remark
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจจับประเภทเอกสาร
        
        Returns:
            1 = เอกสารมีภาษีมูลค่าเพิ่ม (VAT)
        """
        return 1  # มีภาษีมูลค่าเพิ่ม
    
    def clean_filename(self, filename: str) -> str:
        """
        ทำความสะอาดชื่อไฟล์ (ลบ VAT_, WHT_, None_vat)
        
        Args:
            filename: ชื่อไฟล์เดิม
        
        Returns:
            ชื่อไฟล์ที่ทำความสะอาดแล้ว
        """
        if not filename:
            return filename
        
        # ลบ VAT_, WHT_, None_vat
        cleaned = filename
        cleaned = re.sub(r'VAT_', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'WHT_', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'None_vat', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'None_VAT', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'none_vat', '', cleaned, flags=re.IGNORECASE)
        
        # ลบช่องว่างที่เหลือ
        cleaned = cleaned.strip()
        
        return cleaned
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร UNION WORLD SHIPPING (THAILAND)
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร UNION WORLD SHIPPING (THAILAND) หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร UNION WORLD SHIPPING (THAILAND)'
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
        
        # สร้างชื่อไฟล์ใหม่: ชื่อไฟล์เก่า (ไม่เอา VAT_, WHT_, None_vat)
        new_filename = self.clean_filename(filename) if filename else filename
        
        # อ้างอิง: ชื่อไฟล์เก่า (ไม่เอา VAT_, WHT_, None_vat)
        reference = self.clean_filename(filename) if filename else None
        
        # คำนวณหัก ณ ที่จ่าย (3% ของยอดก่อนภาษี)
        if amounts['amount_before_vat'] and withholding['withholding_tax_percent']:
            withholding['withholding_tax_amount'] = amounts['amount_before_vat'] * (withholding['withholding_tax_percent'] / 100)
        
        # แยกที่อยู่เป็นส่วนๆ
        # ที่อยู่: 19/65 SUKHUMVIT SUITE BUILDING, 9TH FLOOR, SOI SUKHMVIT 13 (SAENGCHAN), KHLONG TOEI NUEA, VADHANA, BANGKOK 10110
        address_full = address or ''
        building_number = '19/65'  # เลขที่
        other_info = 'SUKHUMVIT SUITE BUILDING, 9TH FLOOR'  # อื่นๆ
        soi = 'SOI SUKHMVIT 13 (SAENGCHAN)'  # ซอย
        road = ''  # ถนน (ว่าง)
        subdistrict = 'KHLONG TOEI NUEA'  # แขวง
        district = 'VADHANA'  # เขต
        province = 'BANGKOK'  # จังหวัด
        postal_code = '10110'  # รหัสไปรษณีย์
        
        return {
            'success': True,
            'company': 'UNION_WORLD_SHIPPING',
            'company_name': company_name,
            'tax_id': tax_id,
            'date': date,
            'document_number': document_number,
            'reference': reference,  # อ้างอิง
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number,  # เลขที่ (19/65)
            'other_info': other_info,  # อื่นๆ (SUKHUMVIT SUITE BUILDING, 9TH FLOOR)
            'soi': soi,  # ซอย (SOI SUKHMVIT 13 (SAENGCHAN))
            'road': road,  # ถนน (ว่าง)
            'subdistrict': subdistrict,  # แขวง (KHLONG TOEI NUEA)
            'district': district,  # เขต (VADHANA)
            'province': province,  # จังหวัด (BANGKOK)
            'postal_code': postal_code,  # รหัสไปรษณีย์ (10110)
            'account_name': account_info['account_name'],  # ค่าใช้จ่ายในการขนส่ง
            'account_code': account_info['account_code'],
            'withholding_tax_percent': withholding['withholding_tax_percent'],  # 3%
            'withholding_tax_amount': withholding['withholding_tax_amount'],  # คำนวณจากยอดก่อนภาษี * 3%
            'amount_before_vat': amounts['amount_before_vat'],
            'vat_amount': amounts['vat_amount'],
            'total_amount': amounts['total_amount'],
            'remark': remark,  # REF. INVOICE NO.
            'new_filename': new_filename,  # ชื่อไฟล์เก่า (ไม่เอา VAT_, WHT_, None_vat)
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,  # 1 = มีภาษีมูลค่าเพิ่ม
        }

