"""
Starline Agencies Asia (Thailand) Invoice Extractor
====================================================
Extractor สำหรับดึงข้อมูลจาก STARLINE AGENCIES ASIA (THAILAND) LTD.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class StarlineAgenciesExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก STARLINE AGENCIES ASIA (THAILAND) LTD."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "STARLINE AGENCIES ASIA (THAILAND) LTD.",
        "STARLINE AGENCIES ASIA (THAILAND)",
        "STARLINE AGENCIES ASIA",
        "STARLINE"
    ]
    
    # Tax ID (normalized: 0 - 1055 - 48069 - 37 - 2 -> 0105548069372)
    TAX_ID = "0105548069372"
    
    def __init__(self):
        """Initialize Starline Agencies Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ STARLINE AGENCIES ASIA (THAILAND) LTD. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "STARLINE AGENCIES ASIA (THAILAND) LTD."
        2. Tax ID "0 - 1055 - 48069 - 37 - 2" หรือ "0105548069372"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Starline Agencies (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID (รองรับทั้งรูปแบบที่มี - และ space และรูปแบบที่ติดกัน)
        has_tax_id = (
            "0 - 1055 - 48069 - 37 - 2" in text or
            "0-1055-48069-37-2" in text or
            "0105548069372" in text or
            "Tax ID No" in text and "1055" in text and "48069" in text
        )
        
        # เงื่อนไข 3: ต้องมีเอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        has_document_type = (
            "ใบเสร็จรับเงิน" in text or 
            "ใบกำกับภาษี" in text or 
            "RECEIPT" in text.upper() or 
            "TAX INVOICE" in text.upper() or
            "OFFICIAL RECEIPT" in text.upper()
        )
        
        # ต้องมีทั้ง 3 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id and has_document_type
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        # อ่านจาก "STARLINE AGENCIES ASIA (THAILAND) LTD. (ผู้กระทำการแทน)"
        # แต่ return แค่ "STARLINE AGENCIES ASIA (THAILAND) LTD."
        return "STARLINE AGENCIES ASIA (THAILAND) LTD."
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: Tax ID No .: 0 - 1055 - 48069 - 37 - 2 (สำนักงานใหญ่)
        # ต้องแปลงเป็น 0105548069372 (เอา - และ space ออก)
        patterns = [
            r'Tax\s+ID\s+No\s*\.?\s*[:.]?\s*0\s*-\s*1055\s*-\s*48069\s*-\s*37\s*-\s*2',  # Tax ID No .: 0 - 1055 - 48069 - 37 - 2
            r'Tax\s+ID\s*[:.]?\s*0\s*-\s*1055\s*-\s*48069\s*-\s*37\s*-\s*2',  # Tax ID: 0 - 1055 - 48069 - 37 - 2
            r'0\s*-\s*1055\s*-\s*48069\s*-\s*37\s*-\s*2',  # 0 - 1055 - 48069 - 37 - 2
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # แปลงเป็น 0105548069372 (เอา - และ space ออก)
                tax_id = self.TAX_ID
                logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษี: {tax_id}")
                return tax_id
        
        # Fallback: ลองหารูปแบบที่ติดกันแล้ว
        if self.TAX_ID in text:
            return self.TAX_ID
        
        # Fallback: ถ้าไม่พบข้อมูล ให้ใช้ค่า default
        logger.info(f"⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา"""
        # ไม่มีสาขา (ว่าง)
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: 11/11/2025
        patterns = [
            r'(\d{2}/\d{2}/\d{4})',  # 11/11/2025
            r'Date\s*[:.]?\s*(\d{2}/\d{2}/\d{4})',  # Date: 11/11/2025
            r'วันที่\s*[:.]?\s*(\d{2}/\d{2}/\d{4})',  # วันที่: 11/11/2025
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
        # Pattern: OFFICIAL RECEIPT / PANI25110121
        patterns = [
            r'OFFICIAL\s+RECEIPT\s*/\s*([A-Z0-9]+)',  # OFFICIAL RECEIPT / PANI25110121
            r'RECEIPT\s*/\s*([A-Z0-9]+)',  # RECEIPT / PANI25110121
            r'Invoice\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # Invoice No.: PANI25110121
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # Document No.: PANI25110121
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
        # อ่านจากตาราง HTML: B/L : PORUSHA251001270
        # หรือจากชื่อไฟล์เก่า (ตัดข้อมูล VAT_, WHT_, None_vat และข้อมูลที่เริ่มต้นด้วย EXC_)
        
        # ลองหาจากตาราง HTML ก่อน
        # Pattern: BILL OF LADING NO | PORUSHA251001270
        # หรือ: B/L : PORUSHA251001270
        patterns = [
            r'BILL\s+OF\s+LADING\s+NO\s*\|\s*([A-Z0-9]+)',  # BILL OF LADING NO | PORUSHA251001270
            r'B/L\s*[:.]?\s*([A-Z0-9]+)',  # B/L : PORUSHA251001270
            r'PORUSHA\d+',  # PORUSHA251001270
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ref = match.group(1).strip() if match.lastindex else match.group(0).strip()
                ref = f"B/L : {ref}"
                logger.info(f"✅ พบอ้างอิง: {ref}")
                return ref
        
        # Fallback: ลองอ่านจากชื่อไฟล์เก่า
        if filename:
            # ตัดข้อมูล VAT_, WHT_, None_vat และข้อมูลที่เริ่มต้นด้วย EXC_
            ref = filename
            ref = re.sub(r'^VAT_', '', ref, flags=re.IGNORECASE)
            ref = re.sub(r'^WHT_', '', ref, flags=re.IGNORECASE)
            ref = re.sub(r'^None_vat_', '', ref, flags=re.IGNORECASE)
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
    
    def parse_html_table(self, text: str) -> Dict[str, str]:
        """
        Parse ข้อมูลจากตาราง HTML
        หา pattern เช่น: <td>TOTAL</td><td>6,700.00</td>
        หรือ: TOTAL | 6,700.00 (text format)
        
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
            key = re.sub(r'\s+', '', key)
            
            if key and value:
                result[key] = value
                logger.info(f"✅ Parse HTML table: {key} = {value[:100]}...")
        
        # Fallback: ลองหาแบบ text format (| separated)
        # เช่น: TOTAL | 6,700.00
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
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (จาก SUBTOTAL)
                'vat_amount': float,          # ยอดภาษี (0.00)
                'total_amount': float         # ยอดรวม (จาก TOTAL)
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # Parse ข้อมูลจากตาราง HTML ก่อน
        table_data = self.parse_html_table(text)
        logger.info(f"🔍 Table data keys: {list(table_data.keys())[:20]}...")
        
        # 1. ยอดก่อนภาษี: 6,700.00 (จาก SUBTOTAL)
        # จากตาราง HTML: "SUBTOTAL = 6,700.00"
        # หรือจาก text format: "SUBTOTAL : | 6,700.00"
        subtotal_key = None
        for key in table_data.keys():
            if 'SUBTOTAL' in key.upper():
                subtotal_key = key
                break
        
        if subtotal_key:
            subtotal_str = table_data[subtotal_key].replace(',', '').strip()
            # หาเฉพาะตัวเลขแรกที่เจอ
            match = re.search(r'^([\d,]+\.?\d*)', subtotal_str)
            if match:
                subtotal_str = match.group(1).replace(',', '')
                try:
                    result['amount_before_vat'] = float(subtotal_str)
                    logger.info(f"✅ พบยอดก่อนภาษีจากตาราง ({subtotal_key}): {result['amount_before_vat']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ
        if result['amount_before_vat'] is None:
            patterns_subtotal = [
                r'SUBTOTAL\s*[:.]?\s*\|\s*([\d,]+\.?\d*)',  # SUBTOTAL : | 6,700.00
                r'SUBTOTAL\s*[:.]?\s*([\d,]+\.?\d*)',  # SUBTOTAL : 6,700.00
                r'SUBTOTAL\s*\|\s*([\d,]+\.?\d*)',  # SUBTOTAL | 6,700.00
            ]
            
            for pattern in patterns_subtotal:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    subtotal_str = match.group(1).replace(',', '')
                    try:
                        result['amount_before_vat'] = float(subtotal_str)
                        logger.info(f"✅ พบยอดก่อนภาษี: {result['amount_before_vat']}")
                        break
                    except ValueError:
                        continue
        
        # 2. ยอดรวม: 6,700.00 (จาก TOTAL)
        # จากตาราง HTML: "TOTAL = 6,700.00"
        # หรือจาก text format: "TOTAL : | 6,700.00"
        total_key = None
        for key in table_data.keys():
            # หา key ที่มี "TOTAL" แต่ไม่มี "SUBTOTAL"
            if 'TOTAL' in key.upper() and 'SUBTOTAL' not in key.upper():
                total_key = key
                break
        
        if total_key:
            total_str = table_data[total_key].replace(',', '').strip()
            # หาเฉพาะตัวเลขแรกที่เจอ
            match = re.search(r'^([\d,]+\.?\d*)', total_str)
            if match:
                total_str = match.group(1).replace(',', '')
                try:
                    result['total_amount'] = float(total_str)
                    logger.info(f"✅ พบยอดรวมจากตาราง ({total_key}): {result['total_amount']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ จาก text format
        if result['total_amount'] is None:
            # ลองหาจาก text format โดยตรง (อ่านทีละบรรทัด)
            lines = text.split('\n')
            for line in lines:
                # Pattern: "TOTAL : | 6,700.00" หรือ "TOTAL | 6,700.00"
                if 'TOTAL' in line.upper() and 'SUBTOTAL' not in line.upper():
                    # หา pattern ที่มี | และตัวเลข
                    match = re.search(r'TOTAL\s*[:.]?\s*\|\s*([\d,]+\.?\d*)', line, re.IGNORECASE)
                    if match:
                        total_str = match.group(1).replace(',', '')
                        try:
                            result['total_amount'] = float(total_str)
                            logger.info(f"✅ พบยอดรวมจาก text format: {result['total_amount']}")
                            break
                        except ValueError:
                            continue
            
            # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ
            if result['total_amount'] is None:
                patterns_total = [
                    r'TOTAL\s*[:.]?\s*\|\s*([\d,]+\.?\d*)',  # TOTAL : | 6,700.00
                    r'TOTAL\s*[:.]?\s*([\d,]+\.?\d*)',  # TOTAL : 6,700.00
                    r'TOTAL\s*\|\s*([\d,]+\.?\d*)',  # TOTAL | 6,700.00
                    r'รวมทั้งสิ้น\s*[:.]?\s*([\d,]+\.?\d*)',  # รวมทั้งสิ้น: 6,700.00
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
        return "65 Soi Sukhumvit 42 (Kluaynamthai), Sukhumvit Road, Prakanong, Klongtoey, Bangkok 10110"
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร Starline Agencies
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร Starline Agencies หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร STARLINE AGENCIES ASIA (THAILAND) LTD.'
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
        # ที่อยู่: 65 Soi Sukhumvit 42 (Kluaynamthai), Sukhumvit Road, Prakanong, Klongtoey, Bangkok 10110
        address_full = address or ''
        building_number = '65'
        other_info = ''
        soi = 'Soi Sukhumvit 42 (Kluaynamthai)'
        road = 'Sukhumvit Road'
        subdistrict = 'Prakanong'
        district = 'Klongtoey'
        province = 'Bangkok'
        postal_code = '10110'
        
        return {
            'success': True,
            'company': 'STARLINE_AGENCIES',
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

