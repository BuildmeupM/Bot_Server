"""
Thailand Post Invoice Extractor
================================
Extractor สำหรับดึงข้อมูลจาก บริษัท ไปรษณีย์ไทย จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class ThailandPostExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท ไปรษณีย์ไทย จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "บริษัท ไปรษณีย์ไทย จำกัด",
        "ไปรษณีย์ไทย",
        "THAILAND POST",
        "THAILAND POST CO., LTD."
    ]
    
    # Tax ID
    TAX_ID = "0105546095724"
    
    def __init__(self):
        """Initialize Thailand Post Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ บริษัท ไปรษณีย์ไทย จำกัด หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท ไปรษณีย์ไทย จำกัด"
        2. Tax ID "0105546095724"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Thailand Post (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105546095724"
        has_tax_id = self.TAX_ID in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "บริษัท ไปรษณีย์ไทย จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TAX ID. 0105546095724
        patterns = [
            r'TAX\s+ID[.:]\s*(\d{13})',  # TAX ID. 0105546095724
            r'Tax\s+ID[.:]\s*(\d{13})',  # Tax ID. 0105546095724
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0105546095724
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี 0105546095724
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
        # Pattern: สาขา 00355 หรือ Branch 00355
        patterns = [
            r'สาขา\s*[:.]?\s*(\d{5})',  # สาขา: 00355
            r'Branch\s*[:.]?\s*(\d{5})',  # Branch: 00355
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                branch = match.group(1).strip()
                logger.info(f"✅ พบสาขา: {branch}")
                return branch
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: 04/11/2568 15:50:43 USER#pamjit.po
        # ต้องแปลงปี พ.ศ. เป็น ค.ศ.
        patterns = [
            r'(\d{2})/(\d{2})/(\d{4})\s+\d{2}:\d{2}:\d{2}',  # 04/11/2568 15:50:43
            r'(\d{2})/(\d{2})/(\d{4})',  # 04/11/2568
            r'วันที่\s*[:.]?\s*(\d{2})/(\d{2})/(\d{4})',  # วันที่: 04/11/2568
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                
                # แปลงปี พ.ศ. เป็น ค.ศ. (ถ้าปีมากกว่า 2500 ให้ลบ 543)
                try:
                    year_int = int(year)
                    if year_int > 2500:
                        year_int = year_int - 543
                        year = str(year_int)
                except ValueError:
                    logger.warning(f"⚠️ ไม่สามารถแปลงปี: {year}")
                
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: Refer ABB Rcpt#798450
        patterns = [
            r'Refer\s+ABB\s+Rcpt#(\d+)',  # Refer ABB Rcpt#798450
            r'Rcpt#(\d+)',  # Rcpt#798450
            r'Receipt\s*#?\s*(\d+)',  # Receipt#798450
            r'เลขที่\s*[:.]?\s*(\d+)',  # เลขที่: 798450
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                logger.info(f"✅ พบเลขที่เอกสาร: {doc_num}")
                return doc_num
        
        logger.warning("⚠️ ไม่พบเลขที่เอกสาร")
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง"""
        # อ้างอิงว่าง
        return None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # ชื่อบัญชีว่าง
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี
                'vat_amount': float,          # ยอดภาษี
                'total_amount': float         # ยอดรวม
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': 0.00,  # ไม่มีภาษีมูลค่าเพิ่ม
            'total_amount': None
        }
        
        # Pattern: รวมทั้งสิ้น B21.00
        # ต้องลบ "B" ออก
        patterns = [
            r'รวมทั้งสิ้น\s+B([\d,]+\.?\d*)',  # รวมทั้งสิ้น B21.00
            r'รวมทั้งสิ้น\s*[:.]?\s*B?([\d,]+\.?\d*)',  # รวมทั้งสิ้น: B21.00
            r'Total\s*[:.]?\s*B?([\d,]+\.?\d*)',  # Total: B21.00
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                    result['amount_before_vat'] = amount
                    result['total_amount'] = amount  # ยอดรวมเท่ากับยอดก่อนภาษี (ไม่มีภาษี)
                    logger.info(f"✅ พบยอดเงิน: {amount}")
                    break
                except ValueError:
                    continue
        
        return result
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': None,
            'withholding_tax_amount': None
        }
    
    def extract_address(self, text: str) -> str:
        """ดึงที่อยู่"""
        # กำหนดที่อยู่เป็นค่าคงที่
        return "167 ถ.ตากสันนทาราม ต.ทาประดู่ อ.เมือง จ.ระยอง 21001"
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ"""
        # Pattern: Refer ABB Rcpt#798450
        patterns = [
            r'Refer\s+ABB\s+Rcpt#(\d+)',  # Refer ABB Rcpt#798450
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                remark = match.group(0).strip()  # ใช้ทั้งข้อความ "Refer ABB Rcpt#798450"
                logger.info(f"✅ พบหมายเหตุ: {remark}")
                return remark
        
        return None
    
    def clean_filename(self, filename: str) -> str:
        """ทำความสะอาดชื่อไฟล์"""
        if not filename:
            return "ค่าขนส่งไปรษณีย์"
        
        # กำหนดชื่อไฟล์ใหม่เป็น "ค่าขนส่งไปรษณีย์"
        return "ค่าขนส่งไปรษณีย์"
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร"""
        # ไม่มีภาษีมูลค่าเพิ่ม (vat_amount = 0)
        return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร Thailand Post
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร Thailand Post หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร บริษัท ไปรษณีย์ไทย จำกัด'
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
        
        # สร้างชื่อไฟล์ใหม่
        new_filename = self.clean_filename(filename)
        
        # แยกที่อยู่เป็นส่วนๆ
        # ที่อยู่: 167 ถ.ตากสันนทาราม ต.ทาประดู่ อ.เมือง จ.ระยอง 21001
        address_full = address or ''
        building_number = '167'
        other_info = ''
        soi = ''
        road = 'ถนนจากสันนทาราใ'  # ตามที่ผู้ใช้ระบุ
        subdistrict = 'ทาประดู่'
        district = 'เมือง'
        province = 'ระยอง'
        postal_code = '21001'
        
        return {
            'success': True,
            'company': 'THAILAND_POST',
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
            'amount_before_vat': amounts.get('amount_before_vat') or 0,
            'vat_amount': amounts.get('vat_amount') or 0,
            'total_amount': amounts.get('total_amount') or 0,
            'withholding_tax_percent': withholding.get('withholding_tax_percent'),
            'withholding_tax_amount': withholding.get('withholding_tax_amount'),
            'remark': remark,
            'new_filename': new_filename,
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type
        }

