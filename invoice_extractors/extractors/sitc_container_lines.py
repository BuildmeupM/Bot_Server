"""
SITC Container Lines Invoice Extractor
======================================
Extractor สำหรับดึงข้อมูลจาก บริษัท เอสไอทีซี คอนเทนเนอร์ ไลนส์ จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class SITCContainerLinesExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท เอสไอทีซี คอนเทนเนอร์ ไลนส์ จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "บริษัท เอสไอทีซี คอนเทนเนอร์ ไลนส์ จำกัด",
        "เอสไอทีซี คอนเทนเนอร์ ไลนส์ จำกัด",
        "SITC CONTAINER LINES",
        "SITC"
    ]
    
    # Tax ID
    TAX_ID = "0993000092970"
    
    def __init__(self):
        """Initialize SITC Container Lines Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ บริษัท เอสไอทีซี คอนเทนเนอร์ ไลนส์ จำกัด หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท เอสไอทีซี คอนเทนเนอร์ ไลนส์ จำกัด"
        2. Tax ID "0993000092970"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร SITC Container Lines (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0993000092970"
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
        return "บริษัท เอสไอทีซี คอนเทนเนอร์ ไลนส์ จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: เลขประจำตัวผู้เสียภาษีอากร 0993000092970
        patterns = [
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0993000092970
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี 0993000092970
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0993000092970
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
        # Pattern: วันที่ 19/11/2025
        patterns = [
            r'วันที่\s+(\d{2}/\d{2}/\d{4})',  # วันที่ 19/11/2025
            r'Date\s*[:.]?\s*(\d{2}/\d{2}/\d{4})',  # Date: 19/11/2025
            r'(\d{2}/\d{2}/\d{4})',  # 19/11/2025 (ถ้ามีอยู่แล้ว)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                logger.info(f"✅ พบวันที่: {date_str}")
                return date_str
        
        logger.warning("⚠️ ไม่พบวันที่")
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: เลขที่ 1665009 No.
        patterns = [
            r'เลขที่\s+(\d+)\s+No\.',  # เลขที่ 1665009 No.
            r'เลขที่\s+(\d+)',  # เลขที่ 1665009
            r'Invoice\s+No[.:]?\s*[:.]?\s*(\d+)',  # Invoice No.: 1665009
            r'Document\s+No[.:]?\s*[:.]?\s*(\d+)',  # Document No.: 1665009
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
        หา pattern เช่น: <td>B/L NO.</td><td>SITGW ZLCX146354</td>
        หรือ: B/L NO. | SITGW ZLCX146354 |  | (text format)
        
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
        # เช่น: B/L NO. | SITGW ZLCX146354 |  |
        # หรือ: INVOICE NO. | HIS202511188773 |  |
        lines = text.split('\n')
        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    
                    # ทำความสะอาด key (ลบ whitespace)
                    key_clean = re.sub(r'\s+', '', key)
                    
                    if key_clean and value:
                        result[key_clean] = value
                        logger.info(f"✅ Parse text table: {key_clean} = {value[:100]}...")
        
        return result
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง"""
        # อ่านจากตาราง HTML: B/L NO. | SITGW ZLCX146354 |  |
        # หรือจากชื่อไฟล์เก่า (ตัดข้อมูล VAT_, WHT_, None_vat และข้อมูลที่เริ่มต้นด้วย EXC_)
        
        # ลองหาจากตาราง HTML ก่อน
        table_data = self.parse_html_table(text)
        
        # หา BL NO. หรือ B/L NO.
        bl_key = None
        for key in table_data.keys():
            if 'BLNO' in key.upper() or 'B/LNO' in key.upper():
                bl_key = key
                break
        
        if bl_key:
            bl_number = table_data[bl_key].strip()
            # ลบ "INVOICE NO." ออกถ้ามี
            bl_number = re.sub(r'\s*INVOICE\s+NO\.\s*', '', bl_number, flags=re.IGNORECASE).strip()
            ref = f"B/L : {bl_number}"
            logger.info(f"✅ พบอ้างอิงจากตาราง: {ref}")
            return ref
        
        # Fallback: ลองหา pattern อื่นๆ
        patterns = [
            r'B/L\s+NO\.\s*[:.]?\s*([A-Z0-9\s]+?)(?:\s*INVOICE\s+NO\.|$)',  # B/L NO. : SITGW ZLCX146354 (หยุดที่ INVOICE NO.)
            r'B/L\s*[:.]?\s*([A-Z0-9\s]+?)(?:\s*INVOICE\s+NO\.|$)',  # B/L : SITGW ZLCX146354 (หยุดที่ INVOICE NO.)
            r'SITGW\s+[A-Z0-9]+',  # SITGW ZLCX146354
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bl_number = match.group(1).strip() if match.lastindex else match.group(0).strip()
                # ลบ "INVOICE NO." ออกถ้ามี
                bl_number = re.sub(r'\s*INVOICE\s+NO\.\s*', '', bl_number, flags=re.IGNORECASE).strip()
                ref = f"B/L : {bl_number}"
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
                'amount_before_vat': float,  # ยอดก่อนภาษี (จาก AMOUNT)
                'vat_amount': float,          # ยอดภาษี (0.00)
                'total_amount': float         # ยอดรวม (จาก GRAND TOTAL)
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # 1. ยอดก่อนภาษี: 7,000.00 (จาก จำนวนเงิน/AMOUNT 7,000.00)
        patterns_before_vat = [
            r'จำนวนเงิน/AMOUNT\s+([\d,]+\.?\d*)',  # จำนวนเงิน/AMOUNT 7,000.00
            r'AMOUNT\s*[:.]?\s*([\d,]+\.?\d*)',  # AMOUNT: 7,000.00
            r'จำนวนเงิน\s*[:.]?\s*([\d,]+\.?\d*)',  # จำนวนเงิน: 7,000.00
        ]
        
        for pattern in patterns_before_vat:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    result['amount_before_vat'] = float(amount_str)
                    logger.info(f"✅ พบยอดก่อนภาษี: {result['amount_before_vat']}")
                    break
                except ValueError:
                    continue
        
        # 2. ยอดรวม: 7,000.00 (จาก จำนวนเงินรวมทั้งสิ้น/GRAND TOTAL 7,000.00)
        patterns_total = [
            r'จำนวนเงินรวมทั้งสิ้น/GRAND\s+TOTAL\s+([\d,]+\.?\d*)',  # จำนวนเงินรวมทั้งสิ้น/GRAND TOTAL 7,000.00
            r'GRAND\s+TOTAL\s*[:.]?\s*([\d,]+\.?\d*)',  # GRAND TOTAL: 7,000.00
            r'รวมทั้งสิ้น\s*[:.]?\s*([\d,]+\.?\d*)',  # รวมทั้งสิ้น: 7,000.00
        ]
        
        for pattern in patterns_total:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                total_str = match.group(1).replace(',', '')
                try:
                    result['total_amount'] = float(total_str)
                    logger.info(f"✅ พบยอดรวม: {result['total_amount']}")
                    break
                except ValueError:
                    continue
        
        # 3. ยอดภาษี: 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        result['vat_amount'] = 0.00
        
        # 4. ถ้าไม่มียอดรวม แต่มียอดก่อนภาษี ให้ใช้ยอดก่อนภาษีเป็นยอดรวม
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
        # อ่านจาก "INVOICE NO. | HIS202511188773 |  |" และชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_
        remark_parts = []
        
        # ลองหาจากตาราง HTML ก่อน
        table_data = self.parse_html_table(text)
        
        # หา INVOICE NO.
        invoice_key = None
        for key in table_data.keys():
            if 'INVOICENO' in key.upper():
                invoice_key = key
                break
        
        if invoice_key:
            invoice_no = table_data[invoice_key].strip()
            remark_parts.append(f"INVOICE NO. {invoice_no}")
            logger.info(f"✅ พบ INVOICE NO. จากตาราง: {invoice_no}")
        
        # Fallback: ลองหา pattern อื่นๆ
        if not remark_parts:
            invoice_pattern = r'INVOICE\s+NO\.\s*[:.]?\s*([A-Z0-9]+)'
            match = re.search(invoice_pattern, text, re.IGNORECASE)
            if match:
                invoice_no = match.group(1).strip()
                remark_parts.append(f"INVOICE NO. {invoice_no}")
                logger.info(f"✅ พบ INVOICE NO.: {invoice_no}")
        
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
        return "31/F., SHUI ON CENTRE, 6-8 HARBOUR ROAD, WANCHAI, HONGKONG"
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร SITC Container Lines
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร SITC Container Lines หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร บริษัท เอสไอทีซี คอนเทนเนอร์ ไลนส์ จำกัด'
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
        # ที่อยู่: 31/F., SHUI ON CENTRE, 6-8 HARBOUR ROAD, WANCHAI, HONGKONG
        address_full = address or ''
        building_number = ''
        other_info = '31/F., SHUI ON CENTRE, 6-8 HARBOUR ROAD'
        soi = ''
        road = ''
        subdistrict = 'WANCHAI'
        district = ''
        province = 'HONGKONG'
        postal_code = ''
        
        return {
            'success': True,
            'company': 'SITC_CONTAINER_LINES',
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

