"""
Maersk Line (Thailand) Invoice Extractor
========================================
Extractor สำหรับดึงข้อมูลจาก Maersk A/S C/O Maersk Line(Thailand) Ltd.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
from datetime import datetime
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class MaerskLineExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก Maersk A/S C/O Maersk Line(Thailand) Ltd."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "Maersk A/S C/O Maersk Line(Thailand)",
        "Maersk A/S C/O Maersk Line(Thailand) Ltd",
        "Maersk Line(Thailand)",
        "MAERSK LINE",
        "MAERSK"
    ]
    
    # Tax ID
    TAX_ID = "0995000328493"
    
    def __init__(self):
        """Initialize Maersk Line Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Maersk A/S C/O Maersk Line(Thailand) Ltd. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "Maersk A/S C/O Maersk Line(Thailand)"
        2. Tax ID "0995000328493"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Maersk Line (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0995000328493"
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
        # อ่านจาก "Maersk A/S C/O Maersk Line(Thailand) Ltd"
        # แต่ return แค่ "Maersk A/S C/O Maersk Line(Thailand)"
        return "Maersk A/S C/O Maersk Line(Thailand)"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: Tax ID: 0995000328493
        patterns = [
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0995000328493
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0995000328493
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0995000328493
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี 0995000328493
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
        # Pattern: Receipt Date : Nov 12, 2025
        # ต้องแปลงเป็น 12/11/2025
        patterns = [
            r'Receipt\s+Date\s*[:.]?\s*([A-Za-z]{3})\s+(\d{1,2}),\s*(\d{4})',  # Receipt Date : Nov 12, 2025
            r'Date\s*[:.]?\s*([A-Za-z]{3})\s+(\d{1,2}),\s*(\d{4})',  # Date : Nov 12, 2025
            r'(\d{2}/\d{2}/\d{4})',  # 12/11/2025 (ถ้ามีอยู่แล้ว)
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
                    # Format: Nov 12, 2025
                    month_str = match.group(1).capitalize()
                    day = match.group(2).zfill(2)
                    year = match.group(3)
                    
                    if month_str in month_map:
                        month = month_map[month_str]
                        date_str = f"{day}/{month}/{year}"
                        logger.info(f"✅ พบวันที่: {date_str} (จาก: {match.group(0)})")
                        return date_str
                else:
                    # Format: 12/11/2025 (มีอยู่แล้ว)
                    date_str = match.group(1).strip()
                    logger.info(f"✅ พบวันที่: {date_str}")
                    return date_str
        
        logger.warning("⚠️ ไม่พบวันที่")
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: Receipt Number : 7003792931
        patterns = [
            r'Receipt\s+Number\s*[:.]?\s*(\d+)',  # Receipt Number : 7003792931
            r'Invoice\s+No[.:]?\s*[:.]?\s*(\d+)',  # Invoice No.: 7003792931
            r'Document\s+No[.:]?\s*[:.]?\s*(\d+)',  # Document No.: 7003792931
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                logger.info(f"✅ พบเลขที่เอกสาร: {doc_num}")
                return doc_num
        
        logger.warning("⚠️ ไม่พบเลขที่เอกสาร")
        return None
    
    def parse_html_table(self, text: str) -> Dict[str, str]:
        """
        Parse ข้อมูลจากตาราง HTML
        หา pattern เช่น: <td>BL Number</td><td>MAEU721140719</td>
        หรือ: BL Number | MAEU721140719 (text format)
        
        Returns:
            Dictionary ที่มี key-value จากตาราง
        """
        result = {}
        
        # Pattern สำหรับหา <td>key</td><td>value</td>
        pattern = r'<td[^>]*>([^<]+(?:<[^>]+>)*[^<]*)</td>\s*<td[^>]*>([^<]+(?:<[^>]+>)*[^<]*)</td>'
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            key = re.sub(r'<[^>]+>', '', match[0]).strip()
            value = re.sub(r'<[^>]+>', '', match[1]).strip()
            
            # ทำความสะอาด key (ลบ whitespace)
            key_clean = re.sub(r'\s+', '', key)
            
            if key_clean and value:
                result[key_clean] = value
                logger.info(f"✅ Parse HTML table: {key_clean} = {value[:100]}...")
        
        # Fallback: ลองหาแบบ text format (| separated)
        # เช่น: Contract Account | Document | Reference Number | BL Number | Amount | Currency
        # หรือ: 100001103048 | 1527233400 | 7610208125 | MAEU721140719 | 6,650.00 | THB
        lines = text.split('\n')
        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    # หา header row ก่อน
                    if 'BL Number' in line.upper() or 'BLNumber' in line.upper():
                        # นี่คือ header row
                        continue
                    # หา data row ที่มี BL Number
                    if len(parts) >= 4:
                        # สมมติว่า column 4 คือ BL Number
                        bl_number = parts[3].strip() if len(parts) > 3 else None
                        if bl_number and re.match(r'^[A-Z0-9]+$', bl_number):
                            result['BLNumber'] = bl_number
                            logger.info(f"✅ Parse text table: BLNumber = {bl_number}")
        
        return result
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง"""
        # อ่านจากตาราง HTML: BL Number | MAEU721140719
        # หรือจากชื่อไฟล์เก่า (ตัดข้อมูล VAT_, WHT_, None_vat และข้อมูลที่เริ่มต้นด้วย EXC_)
        
        # ลองหาจากตาราง HTML ก่อน
        table_data = self.parse_html_table(text)
        if 'BLNumber' in table_data:
            bl_number = table_data['BLNumber']
            logger.info(f"✅ พบอ้างอิงจากตาราง: {bl_number}")
            return bl_number
        
        # Fallback: ลองหา pattern อื่นๆ
        patterns = [
            r'BL\s+Number\s*[:.]?\s*([A-Z0-9]+)',  # BL Number : MAEU721140719
            r'B/L\s*[:.]?\s*([A-Z0-9]+)',  # B/L : MAEU721140719
            r'MAEU\d+',  # MAEU721140719
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ref = match.group(1).strip() if match.lastindex else match.group(0).strip()
                logger.info(f"✅ พบอ้างอิง: {ref}")
                return ref
        
        # Fallback: ลองอ่านจากชื่อไฟล์เก่า
        if filename:
            # ตัดข้อมูล VAT_, WHT_, None_vat และข้อมูลที่เริ่มต้นด้วย EXC_
            ref = filename
            ref = re.sub(r'^VAT_', '', ref, flags=re.IGNORECASE)
            ref = re.sub(r'^WHT_', '', ref, flags=re.IGNORECASE)
            ref = re.sub(r'^None_vat_', '', ref, flags=re.IGNORECASE)
            # ตัดข้อมูลที่เริ่มต้นด้วย EXC_ และข้อมูลที่อยู่ด้านหลัง
            ref = re.sub(r'EXC_[^_]*_', '', ref, flags=re.IGNORECASE)
            ref = re.sub(r'\.pdf$', '', ref, flags=re.IGNORECASE)
            if ref and ref != filename:
                logger.info(f"✅ พบอ้างอิงจากชื่อไฟล์: {ref}")
                return ref
        
        return None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # ชื่อบัญชี: ค่าใช้จ่ายในการขนส่ง
        return {
            'account_name': 'ค่าใช้จ่ายในการขนส่ง',
            'account_code': None
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (จาก Total)
                'vat_amount': float,          # ยอดภาษี (0.00)
                'total_amount': float         # ยอดรวม (จาก Total)
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # Parse ข้อมูลจากตาราง HTML ก่อน
        table_data = self.parse_html_table(text)
        
        # 1. ยอดรวม: 6,650.00 (จาก Total : 6,650.00 THB)
        # จากตาราง HTML: "Total = 6,650.00" หรือ "Amount = 6,650.00"
        total_key = None
        for key in table_data.keys():
            if 'Total' in key.upper() or 'Amount' in key.upper():
                total_key = key
                break
        
        if total_key:
            total_str = table_data[total_key].replace(',', '').strip()
            # ลบ "THB" หรือ currency code ออก
            total_str = re.sub(r'\s*[A-Z]{3}$', '', total_str, flags=re.IGNORECASE)
            # หาเฉพาะตัวเลขแรกที่เจอ
            match = re.search(r'^([\d,]+\.?\d*)', total_str)
            if match:
                total_str = match.group(1).replace(',', '')
                try:
                    result['total_amount'] = float(total_str)
                    result['amount_before_vat'] = result['total_amount']  # ไม่มีภาษี
                    logger.info(f"✅ พบยอดรวมจากตาราง ({total_key}): {result['total_amount']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ จาก text format
        if result['total_amount'] is None:
            # Pattern: Total : 6,650.00 THB
            patterns_total = [
                r'Total\s*[:.]?\s*([\d,]+\.?\d*)\s*THB',  # Total : 6,650.00 THB
                r'Total\s*[:.]?\s*([\d,]+\.?\d*)',  # Total : 6,650.00
                r'TOTAL\s*[:.]?\s*([\d,]+\.?\d*)',  # TOTAL : 6,650.00
                r'Amount\s*[:.]?\s*([\d,]+\.?\d*)',  # Amount : 6,650.00
            ]
            
            for pattern in patterns_total:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    total_str = match.group(1).replace(',', '')
                    try:
                        result['total_amount'] = float(total_str)
                        result['amount_before_vat'] = result['total_amount']  # ไม่มีภาษี
                        logger.info(f"✅ พบยอดรวม: {result['total_amount']}")
                        break
                    except ValueError:
                        continue
        
        # 2. ยอดภาษี: 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        result['vat_amount'] = 0.00
        
        # 3. ถ้าไม่มียอดรวม แต่มียอดก่อนภาษี ให้ใช้ยอดก่อนภาษีเป็นยอดรวม
        # เพราะเอกสารนี้ไม่มีภาษีมูลค่าเพิ่ม (ยอดก่อนภาษี = ยอดรวม)
        if result['total_amount'] is None and result['amount_before_vat'] is not None:
            result['total_amount'] = result['amount_before_vat']
            logger.info(f"✅ ใช้ยอดก่อนภาษีเป็นยอดรวม (ไม่มีภาษีมูลค่าเพิ่ม): {result['total_amount']}")
        
        return result
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': None,
            'withholding_tax_amount': None
        }
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ"""
        # อ่านจาก "REF. : R2554C101631RUD" และชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_
        remark_parts = []
        
        # หา REF. : R2554C101631RUD
        ref_pattern = r'REF\.\s*[:.]?\s*([A-Z0-9]+)'
        match = re.search(ref_pattern, text, re.IGNORECASE)
        if match:
            ref = match.group(1).strip()
            remark_parts.append(f"REF. : {ref}")
        
        # หาชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_
        if filename and filename.upper().startswith('EXC_'):
            exc_part = filename
            remark_parts.append(exc_part)
        
        if remark_parts:
            remark = ' '.join(remark_parts)
            logger.info(f"✅ พบหมายเหตุ: {remark}")
            return remark
        
        return None
    
    def clean_filename(self, filename: str) -> str:
        """ทำความสะอาดชื่อไฟล์"""
        if not filename:
            return ""
        
        # ตัดข้อมูล VAT_, WHT_, None_vat
        cleaned = filename
        cleaned = re.sub(r'^VAT_', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^WHT_', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^None_vat_', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร"""
        # ไม่มีภาษีมูลค่าเพิ่ม (vat_amount = 0.00)
        return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
    def extract_address(self, text: str) -> str:
        """ดึงที่อยู่"""
        # กำหนดที่อยู่เป็นค่าคงที่
        return "1 South Sathorn Road, Yannawa, Sathorn Bangkok 10120"
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร Maersk Line
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร Maersk Line หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร Maersk A/S C/O Maersk Line(Thailand) Ltd.'
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
        # ที่อยู่: 1 South Sathorn Road, Yannawa, Sathorn Bangkok 10120
        address_full = address or ''
        building_number = '1'
        other_info = ''
        soi = ''
        road = 'South Sathorn Road'
        subdistrict = 'Yannawa'
        district = 'Sathorn'
        province = 'Bangkok'
        postal_code = '10120'
        
        return {
            'success': True,
            'company': 'MAERSK_LINE',
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
            'document_type': document_type,
            'skip_amount_adjustment': True  # ไม่ให้ manager คำนวณยอดภาษีและยอดรวมใหม่ (เพราะเอกสารนี้ไม่มีภาษีมูลค่าเพิ่ม)
        }

