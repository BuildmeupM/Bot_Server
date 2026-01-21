"""
Laem Chabang International Terminal Invoice Extractor
=====================================================
Extractor สำหรับดึงข้อมูลจาก Laem Chabang International Terminal Co.,Ltd.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class LaemChabangInternationalTerminalExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก Laem Chabang International Terminal Co.,Ltd."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "Laem Chabang International Terminal Co.,Ltd.",
        "Laem Chabang International Terminal",
        "Laem Chabang International",
        "LCIT"
    ]
    
    # Tax ID
    TAX_ID = "0105539006231"
    
    def __init__(self):
        """Initialize Laem Chabang International Terminal Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Laem Chabang International Terminal Co.,Ltd. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "Laem Chabang International Terminal Co.,Ltd."
        2. Tax ID "0105539006231"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Laem Chabang International Terminal (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105539006231" หรือ "010553906231" (รองรับทั้งสองรูปแบบ)
        has_tax_id = (
            self.TAX_ID in text or 
            "010553906231" in text or
            "Tax Register No" in text and "0105539" in text.replace(' ', '').replace('-', '')
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
        return "Laem Chabang International Terminal Co.,Ltd."
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: Tax Register No .: 0105539006231
        patterns = [
            r'Tax\s+Register\s+No\s*\.?\s*[:.]?\s*(\d{13})',  # Tax Register No .: 0105539006231
            r'TAX\s+REGISTER\s+NO\s*\.?\s*[:.]?\s*(\d{13})',  # TAX REGISTER NO: 0105539006231
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID: 0105539006231
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0105539006231
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี: 0105539006231
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร: 0105539006231
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id = match.group(1).replace(' ', '').replace('-', '')
                if len(tax_id) == 13:
                    # รองรับทั้ง Tax ID เดิมและใหม่
                    if tax_id in ["0105539006231", "010553906231"]:
                        return tax_id
        
        # Fallback: ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่ (รองรับช่องว่างและขีด)
        text_clean = text.replace(' ', '').replace('-', '')
        if "0105539006231" in text_clean:
            return "0105539006231"
        if "010553906231" in text_clean:
            return "010553906231"
        
        # ถ้าไม่พบข้อมูล ให้ใช้ค่า default
        logger.info(f"⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขาจาก 'Branch No.00001' หรือ 'Branch: HEAD OFFICE'"""
        # Pattern: Branch No.00001 หรือ Branch: HEAD OFFICE
        patterns = [
            r'Branch\s+No[.:]?\s*(\d{5})',  # Branch No.00001
            r'Branch\s*[:.]?\s*HEAD\s+OFFICE',  # Branch: HEAD OFFICE
            r'Branch\s*[:.]?\s*(\d{5})',  # Branch: 00001
            r'สาขา\s*[:.]?\s*(\d{5})',  # สาขา: 00001
            r'สำนักงานสาขา\s*[:.]?\s*(\d{5})',  # สำนักงานสาขา: 00001
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'HEAD OFFICE' in pattern.upper():
                    return '00000'  # HEAD OFFICE = 00000
                branch = match.group(1).strip() if match.lastindex else None
                if branch:
                    return branch.zfill(5)  # เติม 0 นำหน้าให้ครบ 5 หลัก
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: Date : 04-NOV-2025 หรือ Date: : 12-DEC-2025
        # ต้องแปลงจาก 04-NOV-2025 เป็น 04/11/2025
        patterns = [
            r'Date\s*[:.]?\s*[:.]?\s*(\d{1,2})[-/](\w{3})[-/](\d{2,4})',  # Date: : 12-DEC-2025
            r'Date\s*[:.]?\s*(\d{1,2})[-/](\w{3})[-/](\d{2,4})',  # Date : 04-NOV-2025 หรือ Date: 04-Nov-25
            r'วันที่\s*[:.]?\s*[:.]?\s*(\d{1,2})[-/](\w{3})[-/](\d{2,4})',  # วันที่: : 12-DEC-2025
            r'วันที่\s*[:.]?\s*(\d{1,2})[-/](\w{3})[-/](\d{2,4})',  # วันที่: 04-NOV-2025
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
        # Pattern: Receipt No : RB52073890 หรือ Receipt No : RC31981812
        patterns = [
            r'Receipt\s+No\s*[:.]?\s*[:.]?\s*([A-Z0-9]+)',  # Receipt No : RC31981812
            r'Receipt\s+No\s*[:.]?\s*([A-Z0-9]+)',  # Receipt No : RB52073890
            r'RECEIPT\s+NO\s*[:.]?\s*[:.]?\s*([A-Z0-9]+)',  # RECEIPT NO: RC31981812
            r'RECEIPT\s+NO\s*[:.]?\s*([A-Z0-9]+)',  # RECEIPT NO: RB52073890
            r'เลขที่\s*[:.]?\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: : RC31981812
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: RB52073890
            r'No\.\s*[:.]?\s*[:.]?\s*([A-Z0-9]+)',  # No.: : RC31981812
            r'No\.\s*[:.]?\s*([A-Z0-9]+)',  # No.: RB52073890
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                if doc_num and len(doc_num) >= 6:
                    return doc_num
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: Laem Chabang Port B5 Thungsukla Sriracha Chonburi 20231 (Head Office)
        
        Returns:
            ที่อยู่รวม (string)
        """
        # ใช้ที่อยู่ที่กำหนดให้
        return "Laem Chabang Port B5 Thungsukla Sriracha Chonburi 20231 (Head Office)"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # ชื่อบัญชี: ค่าใช้จ่ายอื่นๆในการซื้อสินค้า (ค่าคงที่)
        return {
            'account_name': 'ค่าใช้จ่ายอื่นๆในการซื้อสินค้า',
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
        
        logger.info("🔍 [Laem Chabang International Terminal] เริ่มดึงยอดเงิน...")
        
        # ทำความสะอาด text: ลบ emoji และ label ที่อาจรบกวนการอ่านข้อมูล
        text_clean = text
        # ลบ emoji 💰 และ label "ยอดชำระ:" ถ้ามี
        text_clean = re.sub(r'💰\s*ยอดชำระ\s*[:.]?\s*', '', text_clean)
        text_clean = re.sub(r'ยอดชำระ\s*[:.]?\s*', '', text_clean)
        # ลบช่องว่างส่วนเกิน
        text_clean = re.sub(r'\s+', ' ', text_clean)
        
        logger.debug(f"📄 [Laem Chabang International Terminal] Text length: {len(text_clean)} characters")
        
        # Pattern 1: Sub Total : 1,000.00
        patterns_before_vat = [
            r'Sub\s+Total\s*[:.]?\s*([\d,]+\.?\d{0,2})',  # Sub Total : 1,000.00
            r'SUB\s+TOTAL\s*[:.]?\s*([\d,]+\.?\d{0,2})',  # SUB TOTAL: 1,000.00
            r'ยอดก่อนภาษี\s*[:.]?\s*([\d,]+\.?\d{0,2})',  # ยอดก่อนภาษี: 1,000.00
        ]
        
        for pattern in patterns_before_vat:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '').replace(' ', '').strip()
                    amount = float(amount_str)
                    if amount > 0:
                        result['amount_before_vat'] = amount
                        logger.info(f"✅ [Laem Chabang International Terminal] พบยอดก่อนภาษี: {amount}")
                        break
                except ValueError as e:
                    logger.debug(f"⚠️ [Laem Chabang International Terminal] ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                    continue
        
        # Pattern 2: VAT (7%) : 70.00
        patterns_vat = [
            r'VAT\s*\(7%\)\s*[:.]?\s*([\d,]+\.?\d{0,2})',  # VAT (7%) : 70.00
            r'VAT\s*\(7\s*%\)\s*[:.]?\s*([\d,]+\.?\d{0,2})',  # VAT (7 %) : 70.00
            r'ภาษีมูลค่าเพิ่ม\s*[:.]?\s*([\d,]+\.?\d{0,2})',  # ภาษีมูลค่าเพิ่ม: 70.00
        ]
        
        for pattern in patterns_vat:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                try:
                    vat_str = match.group(1).replace(',', '').replace(' ', '').strip()
                    vat = float(vat_str)
                    if vat > 0:
                        result['vat_amount'] = vat
                        logger.info(f"✅ [Laem Chabang International Terminal] พบยอดภาษี: {vat}")
                        break
                except ValueError as e:
                    logger.debug(f"⚠️ [Laem Chabang International Terminal] ไม่สามารถแปลงเป็นตัวเลข: '{vat_str}', Error: {e}")
                    continue
        
        # Pattern 3: Net Pay (THB) : 1,070.00
        patterns_total = [
            r'Net\s+Pay\s*\(THB\)\s*[:.]?\s*([\d,]+\.?\d{0,2})',  # Net Pay (THB) : 1,070.00
            r'NET\s+PAY\s*\(THB\)\s*[:.]?\s*([\d,]+\.?\d{0,2})',  # NET PAY (THB): 1,070.00
            r'Net\s+Pay\s*[:.]?\s*([\d,]+\.?\d{0,2})',  # Net Pay: 1,070.00
            r'จำนวนเงินรวมทั้งสิ้น\s*[:.]?\s*([\d,]+\.?\d{0,2})',  # จำนวนเงินรวมทั้งสิ้น: 1,070.00
        ]
        
        for pattern in patterns_total:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                try:
                    total_str = match.group(1).replace(',', '').replace(' ', '').strip()
                    total = float(total_str)
                    if total > 0:
                        result['total_amount'] = total
                        logger.info(f"✅ [Laem Chabang International Terminal] พบยอดรวม: {total}")
                        break
                except ValueError as e:
                    logger.debug(f"⚠️ [Laem Chabang International Terminal] ไม่สามารถแปลงเป็นตัวเลข: '{total_str}', Error: {e}")
                    continue
        
        # Fallback: ถ้ายังไม่มี total_amount ให้คำนวณจาก amount_before_vat + vat_amount
        if result['total_amount'] is None:
            if result['amount_before_vat'] and result['vat_amount']:
                result['total_amount'] = result['amount_before_vat'] + result['vat_amount']
                logger.info(f"✅ [Laem Chabang International Terminal] คำนวณยอดรวม: {result['total_amount']} = {result['amount_before_vat']} + {result['vat_amount']}")
        
        # Fallback: ถ้าไม่มี amount_before_vat แต่มี total_amount และ vat_amount ให้คำนวณ
        if result['amount_before_vat'] is None and result['total_amount'] is not None and result['vat_amount'] is not None:
            result['amount_before_vat'] = result['total_amount'] - result['vat_amount']
            logger.info(f"✅ [Laem Chabang International Terminal] คำนวณยอดก่อนภาษี: {result['amount_before_vat']} = {result['total_amount']} - {result['vat_amount']}")
        
        # Fallback: ถ้าไม่มี vat_amount แต่มี total_amount และ amount_before_vat ให้คำนวณ
        if result['vat_amount'] is None and result['total_amount'] is not None and result['amount_before_vat'] is not None:
            result['vat_amount'] = result['total_amount'] - result['amount_before_vat']
            logger.info(f"✅ [Laem Chabang International Terminal] คำนวณยอดภาษี: {result['vat_amount']} = {result['total_amount']} - {result['amount_before_vat']}")
        
        logger.info(f"📊 [Laem Chabang International Terminal] ผลลัพธ์: amount_before_vat={result['amount_before_vat']}, vat_amount={result['vat_amount']}, total_amount={result['total_amount']}")
        
        return result
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ"""
        # ไม่มี remark สำหรับ Laem Chabang International Terminal
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
        ดึงข้อมูลทั้งหมดจากเอกสาร Laem Chabang International Terminal
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร Laem Chabang International Terminal หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร Laem Chabang International Terminal'
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
        # ที่อยู่: Laem Chabang Port B5 Thungsukla Sriracha Chonburi 20231 (Head Office)
        address_full = address or ''
        building_number = ''  # เลขที่ (ว่าง)
        other_info = 'Laem Chabang Port B5'  # อื่นๆ
        soi = ''  # ซอย (ว่าง)
        road = ''  # ถนน (ว่าง)
        subdistrict = 'Thungsukla'  # แขวง
        district = 'Sriracha'  # เขต
        province = 'Chonburi'  # จังหวัด
        postal_code = '20231'  # รหัสไปรษณีย์
        
        return {
            'success': True,
            'company': 'LAEM_CHABANG_INTERNATIONAL_TERMINAL',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,  # สาขา (00001 หรือ 00000 สำหรับ HEAD OFFICE)
            'date': date,
            'document_number': document_number,
            'reference': reference,  # อ้างอิง
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number,  # เลขที่ (ว่าง)
            'other_info': other_info,  # อื่นๆ (Laem Chabang Port B5)
            'soi': soi,  # ซอย (ว่าง)
            'road': road,  # ถนน (ว่าง)
            'subdistrict': subdistrict,  # แขวง (Thungsukla)
            'district': district,  # เขต (Sriracha)
            'province': province,  # จังหวัด (Chonburi)
            'postal_code': postal_code,  # รหัสไปรษณีย์ (20231)
            'account_name': account_info['account_name'],  # ค่าใช้จ่ายอื่นๆในการซื้อสินค้า
            'account_code': account_info['account_code'],
            'withholding_tax_percent': withholding['withholding_tax_percent'],  # 3%
            'withholding_tax_amount': withholding['withholding_tax_amount'],  # คำนวณจากยอดก่อนภาษี * 3%
            'amount_before_vat': amounts['amount_before_vat'],
            'vat_amount': amounts['vat_amount'],
            'total_amount': amounts['total_amount'],
            'remark': remark,  # (ว่าง)
            'new_filename': new_filename,  # ชื่อไฟล์เก่า (ไม่เอา VAT_, WHT_, None_vat)
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,  # 1 = มีภาษีมูลค่าเพิ่ม
        }

