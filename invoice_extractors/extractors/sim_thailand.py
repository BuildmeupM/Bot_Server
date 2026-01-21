"""
SIM (Thailand) Invoice Extractor
=================================
Extractor สำหรับดึงข้อมูลจาก บริษัท ซิม (ไทยแลนด์) จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class SimThailandExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท ซิม (ไทยแลนด์) จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "บริษัท ซิม (ไทยแลนด์) จำกัด",
        "ซิม (ไทยแลนด์) จำกัด",
        "ซิม อินเทอร์เทรดเดล ซับบิ้ง เซอรวีสเซส แอลทีดี",
        "SIM (THAILAND)",
        "SIM"
    ]
    
    # Tax ID (normalized: 099-3-00038431-8 -> 0993000384318)
    TAX_ID = "0993000384318"
    
    def __init__(self):
        """Initialize SIM Thailand Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ บริษัท ซิม (ไทยแลนด์) จำกัด หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท ซิม (ไทยแลนด์) จำกัด"
        2. Tax ID "099-3-00038431-8" หรือ "0993000384318"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร SIM Thailand (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID (รองรับทั้งรูปแบบที่มี - และรูปแบบที่ติดกัน)
        has_tax_id = (
            "099-3-00038431-8" in text or
            "0993000384318" in text or
            "เลขประจำตัวผู้เสียภาษี" in text and "099" in text and "38431" in text
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
        # อ่านจาก "ซิม อินเทอร์เทรดเดล ซับบิ้ง เซอรวีสเซส แอลทีดี กระทำการแทนโดยบริษัท ซิม (ไทยแลนด์) จำกัด"
        # แต่ return แค่ "บริษัท ซิม (ไทยแลนด์) จำกัด"
        return "บริษัท ซิม (ไทยแลนด์) จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: เลขประจำตัวผู้เสียภาษี: 099-3-00038431-8
        # ต้องแปลงเป็น 0993000384318 (เอา - ออก)
        patterns = [
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*099-3-00038431-8',  # เลขประจำตัวผู้เสียภาษี: 099-3-00038431-8
            r'099-3-00038431-8',  # 099-3-00038431-8
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # แปลงเป็น 0993000384318 (เอา - ออก)
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
        # Pattern: Date / วันที่ : 14.11.2025
        # ต้องแปลงเป็น 14/11/2025 (แปลง . เป็น /)
        patterns = [
            r'Date\s*/\s*วันที่\s*[:.]?\s*(\d{2})\.(\d{2})\.(\d{4})',  # Date / วันที่ : 14.11.2025
            r'วันที่\s*[:.]?\s*(\d{2})\.(\d{2})\.(\d{4})',  # วันที่ : 14.11.2025
            r'Date\s*[:.]?\s*(\d{2})\.(\d{2})\.(\d{4})',  # Date : 14.11.2025
            r'(\d{2}/\d{2}/\d{4})',  # 14/11/2025 (ถ้ามีอยู่แล้ว)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    # Format: 14.11.2025 -> 14/11/2025
                    day = match.group(1)
                    month = match.group(2)
                    year = match.group(3)
                    date_str = f"{day}/{month}/{year}"
                    logger.info(f"✅ พบวันที่: {date_str} (จาก: {match.group(0)})")
                    return date_str
                else:
                    # Format: 14/11/2025 (มีอยู่แล้ว)
                    date_str = match.group(1).strip()
                    logger.info(f"✅ พบวันที่: {date_str}")
                    return date_str
        
        logger.warning("⚠️ ไม่พบวันที่")
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: No. / เลขที่ : 81140000206588
        patterns = [
            r'No\.\s*/\s*เลขที่\s*[:.]?\s*(\d+)',  # No. / เลขที่ : 81140000206588
            r'เลขที่\s*[:.]?\s*(\d+)',  # เลขที่ : 81140000206588
            r'Invoice\s+No[.:]?\s*[:.]?\s*(\d+)',  # Invoice No.: 81140000206588
            r'Document\s+No[.:]?\s*[:.]?\s*(\d+)',  # Document No.: 81140000206588
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
        หา pattern เช่น: <td>BL Reference</td><td>GOSUGZH0620091</td>
        หรือ: BL Reference | Invoice Reference | Description | Amount(Baht)
        หรือ: GOSUGZH0620091 | RGI189699 | THD | 4,390.00
        
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
        # เช่น: BL Reference | Invoice Reference | Description | Amount(Baht)
        # หรือ: GOSUGZH0620091 | RGI189699 | THD | 4,390.00
        lines = text.split('\n')
        header_found = False
        bl_ref_column = None
        
        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    # หา header row ก่อน
                    if 'BL Reference' in line.upper() or 'BLReference' in line.upper():
                        # นี่คือ header row - หา column index ของ BL Reference
                        for i, part in enumerate(parts):
                            if 'BL Reference' in part.upper() or 'BLReference' in part.upper():
                                bl_ref_column = i
                                header_found = True
                                logger.info(f"✅ พบ header row: BL Reference อยู่ที่ column {bl_ref_column}")
                                break
                        continue
                    
                    # ถ้าเจอ header แล้ว ให้อ่าน data row
                    if header_found and bl_ref_column is not None and len(parts) > bl_ref_column:
                        bl_number = parts[bl_ref_column].strip()
                        if bl_number and re.match(r'^[A-Z0-9]+$', bl_number):
                            # ใช้ BL Reference แรกที่เจอ
                            if 'BLReference' not in result:
                                result['BLReference'] = bl_number
                                logger.info(f"✅ Parse text table: BLReference = {bl_number}")
        
        return result
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง"""
        # อ่านจากตาราง HTML: BL Reference | GOSUGZH0620091
        # หรือจากชื่อไฟล์เก่า (ตัดข้อมูล VAT_, WHT_, None_vat และข้อมูลที่เริ่มต้นด้วย EXC_)
        
        # ลองหาจากตาราง HTML ก่อน
        table_data = self.parse_html_table(text)
        if 'BLReference' in table_data:
            bl_number = table_data['BLReference']
            ref = f"B/L : {bl_number}"
            logger.info(f"✅ พบอ้างอิงจากตาราง: {ref}")
            return ref
        
        # Fallback: ลองหา pattern อื่นๆ
        patterns = [
            r'BL\s+Reference\s*[:.]?\s*([A-Z0-9]+)',  # BL Reference : GOSUGZH0620091
            r'B/L\s*[:.]?\s*([A-Z0-9]+)',  # B/L : GOSUGZH0620091
            r'GOSUGZH\d+',  # GOSUGZH0620091
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bl_number = match.group(1).strip() if match.lastindex else match.group(0).strip()
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
                'amount_before_vat': float,  # ยอดก่อนภาษี (จาก Amount)
                'vat_amount': float,          # ยอดภาษี (0.00)
                'total_amount': float         # ยอดรวม (จาก Amount)
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # Pattern: Paid By Cash/Bank Transfer : Bank Transfer Amount/จำนวนเงิน 6,790.00 Baht/บาท
        patterns = [
            r'Paid\s+By\s+Cash/Bank\s+Transfer\s*[:.]?\s*Bank\s+Transfer\s+Amount/จำนวนเงิน\s+([\d,]+\.?\d*)\s*Baht/บาท',  # Paid By Cash/Bank Transfer : Bank Transfer Amount/จำนวนเงิน 6,790.00 Baht/บาท
            r'Bank\s+Transfer\s+Amount/จำนวนเงิน\s+([\d,]+\.?\d*)\s*Baht/บาท',  # Bank Transfer Amount/จำนวนเงิน 6,790.00 Baht/บาท
            r'Amount/จำนวนเงิน\s+([\d,]+\.?\d*)\s*Baht/บาท',  # Amount/จำนวนเงิน 6,790.00 Baht/บาท
            r'จำนวนเงิน\s+([\d,]+\.?\d*)\s*Baht/บาท',  # จำนวนเงิน 6,790.00 Baht/บาท
            r'Total\s*[:.]?\s*([\d,]+\.?\d*)\s*Baht',  # Total : 6,790.00 Baht
            r'รวมทั้งสิ้น\s*[:.]?\s*([\d,]+\.?\d*)\s*บาท',  # รวมทั้งสิ้น: 6,790.00 บาท
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                    result['amount_before_vat'] = amount
                    result['total_amount'] = amount  # ไม่มีภาษี
                    logger.info(f"✅ พบยอดเงิน: {amount}")
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
        # อ่านจากชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_
        if filename and filename.upper().startswith('EXC_'):
            remark = filename
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
        return "เลขที่ 1319 อาคารอเมหิต หาซอย ชั้น 25 ห้องเลขที่ 01-06 ถนนสุขุมวิท แขวงพลโยธินเหนือ เขตวัฒนา กรุงเทพมหานคร 10110"
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร SIM Thailand
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร SIM Thailand หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร บริษัท ซิม (ไทยแลนด์) จำกัด'
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
        # ที่อยู่: เลขที่ 1319 อาคารอเมหิต หาซอย ชั้น 25 ห้องเลขที่ 01-06 ถนนสุขุมวิท แขวงพลโยธินเหนือ เขตวัฒนา กรุงเทพมหานคร 10110
        address_full = address or ''
        building_number = '1319'
        other_info = 'อาคารอเมหิต หาซอย ชั้น 25 ห้องเลขที่ 01-06'
        soi = ''
        road = 'ถนนสุขุมวิท'
        subdistrict = 'พลโยธินเหนือ'
        district = 'วัฒนา'
        province = 'กรุงเทพมหานคร'
        postal_code = '10110'
        
        return {
            'success': True,
            'company': 'SIM_THAILAND',
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

