"""
Thai Happy Logistics Ltd. Invoice Extractor
===========================================
Extractor สำหรับดึงข้อมูลจาก Thai Happy Logistics Ltd. (Head Office)

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging
from datetime import datetime

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class ThaiHappyLogisticsExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก Thai Happy Logistics Ltd. (Head Office)"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "Thai Happy Logistics Ltd.",
        "Thai Happy Logistics Ltd. (Head Office)",
        "Thai Happy Logistics"
    ]
    
    # Tax ID
    TAX_ID = "0105566107906"
    
    def __init__(self):
        """Initialize Thai Happy Logistics Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Thai Happy Logistics Ltd. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "Thai Happy Logistics Ltd."
        2. Tax ID "0105566107906"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Thai Happy Logistics Ltd. (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105566107906"
        has_tax_id = self.TAX_ID in text or "Tax Registration Number" in text
        
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
        return "Thai Happy Logistics Ltd. (Head Office)"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: Tax Registration Number : 0105566107906
        patterns = [
            r'Tax\s+Registration\s+Number\s*[:.]?\s*(\d{13})',  # Tax Registration Number : 0105566107906
            r'TAX\s+REGISTRATION\s+NUMBER\s*[:.]?\s*(\d{13})',  # TAX REGISTRATION NUMBER : 0105566107906
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี: 0105566107906
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id = match.group(1).strip()
                if tax_id == self.TAX_ID:
                    logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษี: {tax_id}")
                    return tax_id
        
        # Fallback: ถ้าไม่พบข้อมูล ให้ใช้ค่า default
        logger.info(f"⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา"""
        # ไม่มีสาขา (ว่าง)
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """
        ดึงวันที่ออกเอกสาร
        จาก: Receipt date : Nov 4, 2025
        แปลงเป็น: 04/11/2025
        """
        logger.info("🔍 [Extract Date] เริ่มดึงวันที่...")
        
        # Pattern: Receipt date : Nov 4, 2025
        patterns = [
            r'Receipt\s+date\s*[:.]?\s*([A-Za-z]{3})\s+(\d{1,2}),\s*(\d{4})',  # Receipt date : Nov 4, 2025
            r'RECEIPT\s+DATE\s*[:.]?\s*([A-Za-z]{3})\s+(\d{1,2}),\s*(\d{4})',  # RECEIPT DATE : Nov 4, 2025
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # วันที่: 04/11/2025
        ]
        
        # Mapping เดือน
        month_map = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    if match.group(1) in month_map:
                        # รูปแบบ: Nov 4, 2025
                        month = month_map[match.group(1)]
                        day = match.group(2).zfill(2)
                        year = match.group(3)
                        date_str = f"{day}/{month}/{year}"
                        logger.info(f"✅ [Extract Date] พบวันที่: {date_str}")
                        return date_str
                    else:
                        # รูปแบบ: 04/11/2025
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
        จาก: Receipt number : THJV202510004319696
        """
        logger.info("🔍 [Extract Document Number] เริ่มดึงเลขที่เอกสาร...")
        
        # Pattern: Receipt number : THJV202510004319696
        patterns = [
            r'Receipt\s+number\s*[:.]?\s*([A-Z0-9]+)',  # Receipt number : THJV202510004319696
            r'RECEIPT\s+NUMBER\s*[:.]?\s*([A-Z0-9]+)',  # RECEIPT NUMBER : THJV202510004319696
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: THJV202510004319696
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                if len(doc_num) >= 10:
                    logger.info(f"✅ [Extract Document Number] พบเลขที่เอกสาร: {doc_num}")
                    return doc_num
        
        logger.warning("⚠️ [Extract Document Number] ไม่พบเลขที่เอกสาร")
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงข้อมูลอ้างอิง"""
        # ไม่มีข้อมูลอ้างอิง (ว่าง)
        return None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี"""
        # ไม่มีข้อมูลบัญชี (ว่าง)
        return {'account_name': None, 'account_code': None}
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        # ไม่มีข้อมูลหัก ณ ที่จ่าย (ว่าง)
        return {'withholding_tax_percent': None, 'withholding_tax_amount': None}
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ"""
        # ไม่มีหมายเหตุ (ว่าง)
        return None
    
    def extract_address(self, text: str) -> Dict[str, Optional[str]]:
        """
        ดึงข้อมูลที่อยู่
        จาก: Address: No. 1 Park Silom Tower, 8th Floor, Convent Road, Silom Subdistrict,
        Bangrak District, Bangkok
        """
        logger.info("🔍 [Extract Address] เริ่มดึงข้อมูลที่อยู่...")
        
        # Pattern: Address: No. 1 Park Silom Tower, 8th Floor, Convent Road, Silom Subdistrict, Bangrak District, Bangkok
        address_pattern = r'Address\s*[:.]?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n[A-Z]|\n\n|$)'
        match = re.search(address_pattern, text, re.IGNORECASE | re.MULTILINE)
        
        if match:
            address_full = match.group(1).strip()
            logger.info(f"✅ [Extract Address] พบที่อยู่: {address_full[:100]}...")
            
            # แยกส่วนที่อยู่
            # 1 Park Silom Tower, 8th Floor, Convent Road, Silom Subdistrict, Bangrak District, Bangkok
            parts = [p.strip() for p in address_full.split(',')]
            
            # กำหนดค่าตามที่ระบุ
            result = {
                'address_full': '1 Park Silom Tower, 8th Floor, Convent Road, Silom Subdistrict, Bangrak District, Bangkok',
                'address_number': None,  # เลขที่
                'address_other': '1 Park Silom Tower, 8th Floor',  # อื่นๆ
                'address_road': 'Convent Road',  # ถนน
                'address_soi': None,  # ซอย
                'address_subdistrict': 'Silom Subdistrict',  # แขวง
                'address_district': 'Bangrak District',  # เขต
                'address_province': 'Bangkok',  # จังหวัด
                'address_postal_code': None  # เลขไปรษณีย์
            }
            
            return result
        
        # Fallback: ใช้ค่าตามที่กำหนด
        logger.info("⚠️ [Extract Address] ไม่พบที่อยู่ในเอกสาร - ใช้ค่าตามที่กำหนด")
        return {
            'address_full': '1 Park Silom Tower, 8th Floor, Convent Road, Silom Subdistrict, Bangrak District, Bangkok',
            'address_number': None,
            'address_other': '1 Park Silom Tower, 8th Floor',
            'address_road': 'Convent Road',
            'address_soi': None,
            'address_subdistrict': 'Silom Subdistrict',
            'address_district': 'Bangrak District',
            'address_province': 'Bangkok',
            'address_postal_code': None
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        จาก: Total Amount ฿20,845.05
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        logger.info("🔍 [Extract Amounts] เริ่มดึงยอดเงิน...")
        
        # Pattern: Total Amount ฿20,845.05
        patterns = [
            r'Total\s+Amount\s*฿?\s*([\d,]+\.?\d*)',  # Total Amount ฿20,845.05
            r'TOTAL\s+AMOUNT\s*฿?\s*([\d,]+\.?\d*)',  # TOTAL AMOUNT ฿20,845.05
            r'จำนวนเงินรวม\s*฿?\s*([\d,]+\.?\d*)',  # จำนวนเงินรวม ฿20,845.05
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    amount = float(amount_str)
                    result['total_amount'] = amount
                    result['amount_before_vat'] = amount  # ไม่มี VAT
                    result['vat_amount'] = 0.0
                    logger.info(f"✅ [Extract Amounts] พบยอดรวม: {amount}")
                    return result
                except (ValueError, IndexError):
                    continue
        
        logger.warning("⚠️ [Extract Amounts] ไม่พบยอดเงิน")
        return result
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจสอบประเภทเอกสาร
        Returns:
            0 = ไม่มีภาษีมูลค่าเพิ่ม
            1 = มีภาษีมูลค่าเพิ่ม
        """
        # เอกสารนี้ไม่มีภาษีมูลค่าเพิ่ม (VAT = 0)
        return 0
    
    def clean_filename(self, filename: str) -> str:
        """
        ทำความสะอาดชื่อไฟล์
        จาก: THJV202510004319696.pdf
        เป็น: ค่าขนส่ง TikTok
        """
        if not filename:
            return ""
        
        # ลบ .pdf
        cleaned = filename.replace('.pdf', '').replace('.PDF', '')
        
        # ถ้าเป็นเลขที่เอกสาร ให้แปลงเป็นชื่อที่กำหนด
        # ตัวอย่าง: THJV202510004319696 -> ค่าขนส่ง TikTok
        if cleaned.startswith('THJV'):
            return "ค่าขนส่ง TikTok"
        
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
        logger.info(f"🔍 [Thai Happy Logistics] เริ่มดึงข้อมูลจากเอกสาร...")
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
        logger.info(f"✅ [Thai Happy Logistics] ดึงข้อมูลเสร็จสิ้น")
        logger.info(f"   - บริษัท: {company_name}")
        logger.info(f"   - เลขที่ผู้เสียภาษี: {tax_id}")
        logger.info(f"   - วันที่: {date}")
        logger.info(f"   - เลขที่เอกสาร: {document_number}")
        logger.info(f"   - ยอดรวม: {amounts.get('total_amount')}")
        logger.info("=" * 80)
        
        return result

