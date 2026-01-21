"""
LCB Container Terminal 1 Ltd. Invoice Extractor
================================================
Extractor สำหรับดึงข้อมูลจาก บริษัท แอลซีบี คอนเทนเนอร์ เทอร์มินัล 1 จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging
from datetime import datetime

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class LCBContainerTerminalExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท แอลซีบี คอนเทนเนอร์ เทอร์มินัล 1 จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "แอลซีบี คอนเทนเนอร์ เทอร์มินัล 1 จำกัด",
        "LCB CONTAINER TERMINAL 1 LTD.",
        "LCB CONTAINER TERMINAL 1",
        "LCB Container Terminal 1"
    ]
    
    # Tax ID
    TAX_ID = "0105538110884"
    
    def __init__(self):
        """Initialize LCB Container Terminal Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ บริษัท แอลซีบี คอนเทนเนอร์ เทอร์มินัล 1 จำกัด หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "แอลซีบี คอนเทนเนอร์ เทอร์มินัล 1 จำกัด" หรือ "LCB CONTAINER TERMINAL 1 LTD."
        2. Tax ID "0105538110884"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร LCB Container Terminal 1 (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105538110884"
        has_tax_id = self.TAX_ID in text
        
        # เงื่อนไข 3: ต้องมีเอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        has_document_type = (
            "ใบเสร็จรับเงิน" in text or 
            "ใบกำกับภาษี" in text or 
            "RECEIPT" in text.upper() or 
            "TAX INVOICE" in text.upper()
        )
        
        # ต้องมีทั้ง 3 เงื่อนไขถึงจะผ่าน
        logger.info(f"🔍 [LCB Container Terminal] ตรวจสอบเอกสาร:")
        logger.info(f"   - มีชื่อบริษัท: {has_company}")
        logger.info(f"   - มี Tax ID: {has_tax_id}")
        logger.info(f"   - มีเอกสาร: {has_document_type}")
        
        return has_company and has_tax_id and has_document_type
    
    def extract_company_name(self, text: str) -> str:
        """
        ดึงชื่อบริษัท
        อ่านจาก: บริษัท แอลซีบี คอนเทนเนอร์ เทอร์มินัล 1 จำกัด LCB CONTAINER TERMINAL 1 LTD.
        """
        logger.info("🔍 [Extract Company Name] เริ่มดึงชื่อบริษัท...")
        
        # Pattern: บริษัท แอลซีบี คอนเทนเนอร์ เทอร์มินัล 1 จำกัด LCB CONTAINER TERMINAL 1 LTD.
        patterns = [
            r'บริษัท\s+แอลซีบี\s+คอนเทนเนอร์\s+เทอร์มินัล\s+1\s+จำกัด',
            r'LCB\s+CONTAINER\s+TERMINAL\s+1\s+LTD\.?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company_name = "บริษัท แอลซีบี คอนเทนเนอร์ เทอร์มินัล 1 จำกัด"
                logger.info(f"✅ [Extract Company Name] พบชื่อบริษัท: {company_name}")
                return company_name
        
        # Fallback: ถ้าไม่พบ ให้ใช้ค่า default
        logger.warning("⚠️ [Extract Company Name] ไม่พบชื่อบริษัท - ใช้ค่า default")
        return "บริษัท แอลซีบี คอนเทนเนอร์ เทอร์มินัล 1 จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        logger.info("🔍 [Extract Tax ID] เริ่มดึงเลขประจำตัวผู้เสียภาษี...")
        
        # Pattern: 0105538110884
        patterns = [
            r'0105538110884',
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*0105538110884',
            r'Tax\s+ID\s*[:.]?\s*0105538110884',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                logger.info(f"✅ [Extract Tax ID] พบเลขประจำตัวผู้เสียภาษี: {self.TAX_ID}")
                return self.TAX_ID
        
        # Fallback: ถ้าไม่พบ ให้ใช้ค่า default
        logger.warning(f"⚠️ [Extract Tax ID] ไม่พบเลขประจำตัวผู้เสียภาษี - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา"""
        # ไม่มีสาขา (ว่าง)
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """
        ดึงวันที่ออกเอกสาร
        จาก: เอกสารเลขที่ RC680250811 หน้าที่ Page No.: 1/1 วัน เดือน ปี Date: 25/12/2025
        แปลงเป็น: 25/12/2025
        """
        logger.info("🔍 [Extract Date] เริ่มดึงวันที่...")
        
        # Pattern: Date: 25/12/2025
        patterns = [
            r'Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # Date: 25/12/2025
            r'DATE\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DATE: 25/12/2025
            r'วัน\s+เดือน\s+ปี\s+Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # วัน เดือน ปี Date: 25/12/2025
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                date_str = f"{day}/{month}/{year}"
                logger.info(f"✅ [Extract Date] พบวันที่: {date_str}")
                return date_str
        
        logger.warning("⚠️ [Extract Date] ไม่พบวันที่")
        return None
    
    def extract_document_number(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงเลขที่เอกสาร
        จาก: เอกสารเลขที่ RC680250811 หน้าที่ Page No.: 1/1 วัน เดือน ปี Date: 25/12/2025
        """
        logger.info("🔍 [Extract Document Number] เริ่มดึงเลขที่เอกสาร...")
        
        # Pattern: เอกสารเลขที่ RC680250811
        patterns = [
            r'เอกสารเลขที่\s+([A-Z0-9]+)',  # เอกสารเลขที่ RC680250811
            r'Document\s+No\.?\s*[:.]?\s*([A-Z0-9]+)',  # Document No.: RC680250811
            r'DOCUMENT\s+NO\.?\s*[:.]?\s*([A-Z0-9]+)',  # DOCUMENT NO.: RC680250811
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                logger.info(f"✅ [Extract Document Number] พบเลขที่เอกสาร: {doc_num}")
                return doc_num
        
        logger.warning("⚠️ [Extract Document Number] ไม่พบเลขที่เอกสาร")
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงข้อมูลอ้างอิง
        (ชื่อไฟล์เก่าตัดข้อมูล VAT_ WHT _ None_vat และข้อมูลที่เริ่มต้นด้วย EXC_ข้อมูลที่อยู่ด้านหลัง ไม่เอา .pdf)
        """
        if not filename:
            return None
        
        logger.info(f"🔍 [Extract Reference] เริ่มดึงข้อมูลอ้างอิงจากชื่อไฟล์: {filename}")
        
        # ตัดข้อมูล VAT_ WHT _ None_vat ออก
        reference = filename
        reference = re.sub(r'VAT_?\s*', '', reference, flags=re.IGNORECASE)
        reference = re.sub(r'WHT_?\s*', '', reference, flags=re.IGNORECASE)
        reference = re.sub(r'None_vat', '', reference, flags=re.IGNORECASE)
        
        # ตัดข้อมูลที่เริ่มต้นด้วย EXC_ และข้อมูลที่อยู่ด้านหลังออก
        reference = re.sub(r'EXC_.*', '', reference, flags=re.IGNORECASE)
        
        # ตัด .pdf ออก
        reference = re.sub(r'\.pdf$', '', reference, flags=re.IGNORECASE)
        
        # ลบช่องว่างส่วนเกิน
        reference = re.sub(r'\s+', ' ', reference).strip()
        
        if reference:
            logger.info(f"✅ [Extract Reference] พบข้อมูลอ้างอิง: {reference}")
            return reference
        
        logger.warning("⚠️ [Extract Reference] ไม่พบข้อมูลอ้างอิง")
        return None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """
        ดึงข้อมูลบัญชี
        ชื่อบัญชี: ค่าใช้จ่ายในการขนส่ง
        """
        logger.info("🔍 [Extract Account Info] เริ่มดึงข้อมูลบัญชี...")
        
        return {
            'account_name': 'ค่าใช้จ่ายในการขนส่ง',
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลหัก ณ ที่จ่าย
        เปอร์เซ็นต์หัก ณ ที่จ่าย: 3
        """
        logger.info("🔍 [Extract Withholding Tax] เริ่มดึงข้อมูลหัก ณ ที่จ่าย...")
        
        return {
            'withholding_tax_percent': 3.0,
            'withholding_tax_amount': None
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        - ยอดก่อนภาษีมูลค่าเพิ่ม: 1,000.00 (อ่านจาก "ยอดชำระ: 1,000.00")
        - ยอดภาษีมูลค่าเพิ่ม: 70.00 (อ่านจาก "Tax:70.00")
        - ยอดหลังบวกภาษีมูลค่าเพิ่ม: 1,070.00 (อ่านจาก "ยอดชำระ: 1,070.00")
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        logger.info("🔍 [Extract Amounts] เริ่มดึงยอดเงิน...")
        
        # ค้นหายอดก่อนภาษีมูลค่าเพิ่ม: ยอดชำระ: 1,000.00 (ยอดแรกที่พบ)
        patterns_before_vat = [
            r'ยอดชำระ\s*[:.]?\s*([\d,]+\.?\d*)',  # ยอดชำระ: 1,000.00
            r'ยอดชำระ\s*[:.]?\s*([\d,]+)',  # ยอดชำระ: 1,000
        ]
        
        amounts_found = []
        for pattern in patterns_before_vat:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount_str = match.group(1).replace(',', '').strip()
                    amount = float(amount_str)
                    amounts_found.append(amount)
                except (ValueError, AttributeError):
                    continue
        
        # ถ้าพบมากกว่า 1 ยอด ให้ใช้ยอดแรกเป็นยอดก่อน VAT และยอดสุดท้ายเป็นยอดรวม
        if len(amounts_found) >= 2:
            result['amount_before_vat'] = amounts_found[0]
            result['total_amount'] = amounts_found[-1]
            logger.info(f"✅ [Extract Amounts] พบยอดก่อนภาษีมูลค่าเพิ่ม: {result['amount_before_vat']}")
            logger.info(f"✅ [Extract Amounts] พบยอดหลังบวกภาษีมูลค่าเพิ่ม: {result['total_amount']}")
        elif len(amounts_found) == 1:
            result['amount_before_vat'] = amounts_found[0]
            logger.info(f"✅ [Extract Amounts] พบยอดก่อนภาษีมูลค่าเพิ่ม: {result['amount_before_vat']}")
        
        # ค้นหายอดภาษีมูลค่าเพิ่ม: Tax:70.00
        patterns_vat = [
            r'Tax\s*[:.]?\s*([\d,]+\.?\d*)',  # Tax:70.00
            r'TAX\s*[:.]?\s*([\d,]+\.?\d*)',  # TAX:70.00
            r'ภาษีมูลค่าเพิ่ม\s*[:.]?\s*([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม: 70.00
        ]
        
        for pattern in patterns_vat:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '').strip()
                    amount = float(amount_str)
                    result['vat_amount'] = amount
                    logger.info(f"✅ [Extract Amounts] พบยอดภาษีมูลค่าเพิ่ม: {amount}")
                    break
                except (ValueError, AttributeError):
                    continue
        
        # ถ้ายังไม่พบยอดรวม ให้คำนวณจากยอดก่อน VAT + VAT
        if result['total_amount'] is None and result['amount_before_vat'] is not None and result['vat_amount'] is not None:
            result['total_amount'] = result['amount_before_vat'] + result['vat_amount']
            logger.info(f"✅ [Extract Amounts] คำนวณยอดหลังบวกภาษีมูลค่าเพิ่ม: {result['total_amount']}")
        
        if result['amount_before_vat'] is None and result['vat_amount'] is None and result['total_amount'] is None:
            logger.warning("⚠️ [Extract Amounts] ไม่พบยอดเงิน")
        
        return result
    
    def extract_address(self, text: str) -> Dict[str, Optional[str]]:
        """
        ดึงข้อมูลที่อยู่
        กำหนดค่าตามที่ระบุ
        """
        logger.info("🔍 [Extract Address] เริ่มดึงข้อมูลที่อยู่...")
        
        # กำหนดค่าตามที่ระบุ
        result = {
            'address_full': 'หมู่ที่ 3 ท่าเรื่อพาณิชย์แหลมฉบัง ท่าเทียบเรือตู้สินค้าที่ 1 ถนนสุขุมวิท ตำบลทุ่งสุขลา อำเภอศรีราชา จังหวัดชลบุรี 20230',
            'address_number': None,  # เลขที่
            'address_other': 'หมู่ที่ 3 ท่าเรื่อพาณิชย์แหลมฉบัง ท่าเทียบเรือตู้สินค้าที่ 1',  # อื่นๆ
            'address_road': 'ถนนสุขุมวิท',  # ถนน
            'address_soi': None,  # ซอย
            'address_subdistrict': 'ทุ่งสุขลา',  # แขวง
            'address_district': 'ศรีราชา',  # เขต
            'address_province': 'ชลบุรี',  # จังหวัด
            'address_postal_code': '20230'  # เลขไปรษณีย์
        }
        
        logger.info(f"✅ [Extract Address] ใช้ที่อยู่ตามที่กำหนด: {result['address_full'][:50]}...")
        return result
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงหมายเหตุ
        BL-NOSNB25LB78507 (อ่านจากชื่อไฟล์: Wht_vat_BL-NOSNB25LB78507 EXC2512-268_007.pdf โดยให้ระบบดึงข้อมูลจาก คำว่า BL ข้อมูลติดต่อกันจนวรรค)
        """
        if not filename:
            return None
        
        logger.info(f"🔍 [Extract Remark] เริ่มดึงหมายเหตุจากชื่อไฟล์: {filename}")
        
        # Pattern: BL-xxxxx (ข้อมูลติดต่อกันจนวรรค)
        pattern = r'BL-([A-Z0-9]+)'
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            remark = f"BL-{match.group(1)}"
            logger.info(f"✅ [Extract Remark] พบหมายเหตุ: {remark}")
            return remark
        
        logger.warning("⚠️ [Extract Remark] ไม่พบหมายเหตุ")
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจสอบประเภทเอกสาร
        Returns:
            1 = มีภาษีมูลค่าเพิ่ม
            2 = ไม่มีภาษีมูลค่าเพิ่ม
        """
        # เอกสารนี้มีภาษีมูลค่าเพิ่ม (VAT > 0)
        if amounts.get('vat_amount') and amounts.get('vat_amount', 0) > 0:
            return 1
        return 1  # Default: มีภาษีมูลค่าเพิ่ม
    
    def clean_filename(self, filename: str) -> str:
        """
        ทำความสะอาดชื่อไฟล์
        (ชื่อไฟล์เก่าตัดข้อมูล VAT_ WHT _ None_vat)
        """
        if not filename:
            return ""
        
        logger.info(f"🔍 [Clean Filename] เริ่มทำความสะอาดชื่อไฟล์: {filename}")
        
        # ตัดข้อมูล VAT_ WHT _ None_vat ออก
        cleaned = filename
        cleaned = re.sub(r'VAT_?\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'WHT_?\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'None_vat', '', cleaned, flags=re.IGNORECASE)
        
        # ลบช่องว่างส่วนเกิน
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        logger.info(f"✅ [Clean Filename] ชื่อไฟล์ใหม่: {cleaned}")
        return cleaned
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์
            filepath: path ของไฟล์
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        logger.info("=" * 80)
        logger.info(f"🔍 [LCB Container Terminal] เริ่มดึงข้อมูลจากเอกสาร...")
        logger.info("=" * 80)
        
        # ดึงข้อมูลพื้นฐาน
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        branch = self.extract_branch(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text, filename)
        reference = self.extract_reference(text, filename)
        account_info = self.extract_account_info(text)
        withholding_tax = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        address = self.extract_address(text)
        amounts = self.extract_amounts(text)
        document_type = self.detect_document_type(text, amounts, withholding_tax)
        new_filename = self.clean_filename(filename) if filename else None
        
        # สร้างที่อยู่รวม (string) สำหรับ manager
        address_full_str = address.get('address_full') or ''
        
        # สร้าง dictionary ผลลัพธ์
        result = {
            'success': True,
            'company': company_name,
            'company_name': company_name,  # เพิ่ม field นี้สำหรับ manager
            'old_filename': filename,
            'filepath': filepath,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'reference': reference,
            'account_name': account_info.get('account_name'),
            'account_code': account_info.get('account_code'),
            'withholding_tax_percent': withholding_tax.get('withholding_tax_percent'),
            'withholding_tax_amount': withholding_tax.get('withholding_tax_amount'),
            'amount_before_vat': amounts.get('amount_before_vat'),
            'vat_amount': amounts.get('vat_amount'),
            'total_amount': amounts.get('total_amount'),
            'remark': remark,
            'new_filename': new_filename,
            'document_type': document_type,
            'skip_amount_adjustment': False,  # มี VAT ต้องคำนวณ
            # ที่อยู่
            'address': address_full_str,  # เพิ่ม field นี้สำหรับ manager (string)
            'address_full': address.get('address_full'),
            'address_number': address.get('address_number'),
            'address_other': address.get('address_other'),
            'address_road': address.get('address_road'),
            'address_soi': address.get('address_soi'),
            'address_subdistrict': address.get('address_subdistrict'),
            'address_district': address.get('address_district'),
            'address_province': address.get('address_province'),
            'address_postal_code': address.get('address_postal_code'),
        }
        
        logger.info("=" * 80)
        logger.info(f"✅ [LCB Container Terminal] ดึงข้อมูลเสร็จสิ้น")
        logger.info(f"   - บริษัท: {company_name}")
        logger.info(f"   - เลขที่ผู้เสียภาษี: {tax_id}")
        logger.info(f"   - วันที่: {date}")
        logger.info(f"   - เลขที่เอกสาร: {document_number}")
        logger.info(f"   - ยอดก่อนภาษีมูลค่าเพิ่ม: {amounts.get('amount_before_vat')}")
        logger.info(f"   - ยอดภาษีมูลค่าเพิ่ม: {amounts.get('vat_amount')}")
        logger.info(f"   - ยอดหลังบวกภาษีมูลค่าเพิ่ม: {amounts.get('total_amount')}")
        logger.info("=" * 80)
        
        return result
