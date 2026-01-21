"""
Beam Data Co., Ltd. Invoice Extractor
======================================
Extractor สำหรับดึงข้อมูลจาก Beam Data Co., Ltd (Head Office)

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging
from datetime import datetime

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class BeamDataExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก Beam Data Co., Ltd (Head Office)"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "Beam Data Co., Ltd",
        "Beam Data Co., Ltd (Head Office)",
        "Beam Data",
        "BEAM DATA"
    ]
    
    # Tax ID (normalized: ลบ - ออก)
    TAX_ID = "0105562181354"
    
    def __init__(self):
        """Initialize Beam Data Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Beam Data Co., Ltd. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "Beam Data Co., Ltd"
        2. Tax ID "0-1055-62181-354" หรือ "0105562181354"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Beam Data Co., Ltd. (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0-1055-62181-354" หรือ "0105562181354"
        has_tax_id = (
            "0-1055-62181-354" in text or 
            self.TAX_ID in text or
            ("Tax ID" in text or "เลขประจำตัวผู้เสียภาษี" in text) and 
            ("1055" in text and "62181" in text and "354" in text)
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
        return "Beam Data Co., Ltd (Head Office)"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: เลขประจำตัวผู้เสียภาษี (Tax ID): 0-1055-62181-354
        patterns = [
            r'เลขประจำตัวผู้เสียภาษี\s*\(Tax\s+ID\)\s*[:.]?\s*0\s*-\s*1055\s*-\s*62181\s*-\s*354',
            r'Tax\s+ID\s*[:.]?\s*0\s*-\s*1055\s*-\s*62181\s*-\s*354',
            r'0\s*-\s*1055\s*-\s*62181\s*-\s*354',
            r'0105562181354',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษี: {self.TAX_ID}")
                return self.TAX_ID
        
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
        จาก: Date Issued: 01 November 2025
        แปลงเป็น: 01/11/2025
        """
        logger.info("🔍 [Extract Date] เริ่มดึงวันที่...")
        
        # Pattern: Date Issued: 01 November 2025
        patterns = [
            r'Date\s+Issued\s*[:.]?\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})',  # Date Issued: 01 November 2025
            r'DATE\s+ISSUED\s*[:.]?\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})',  # DATE ISSUED: 01 November 2025
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # วันที่: 01/11/2025
        ]
        
        # Mapping เดือน
        month_map = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04',
            'May': '05', 'June': '06', 'July': '07', 'August': '08',
            'September': '09', 'October': '10', 'November': '11', 'December': '12',
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    day = match.group(1).zfill(2)
                    month_str = match.group(2).strip()
                    year = match.group(3)
                    
                    # แปลงชื่อเดือนเป็นตัวเลข
                    if month_str in month_map:
                        month = month_map[month_str]
                    else:
                        # ถ้าเป็นรูปแบบ dd/mm/yyyy
                        try:
                            month = match.group(2).zfill(2)
                        except:
                            continue
                    
                    date_str = f"{day}/{month}/{year}"
                    logger.info(f"✅ [Extract Date] พบวันที่: {date_str}")
                    return date_str
        
        logger.warning("⚠️ [Extract Date] ไม่พบวันที่")
        return None
    
    def extract_document_number(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงเลขที่เอกสาร
        จาก: Number: 251101000278
        """
        logger.info("🔍 [Extract Document Number] เริ่มดึงเลขที่เอกสาร...")
        
        # Pattern: Number: 251101000278
        patterns = [
            r'Number\s*[:.]?\s*(\d+)',  # Number: 251101000278
            r'NUMBER\s*[:.]?\s*(\d+)',  # NUMBER: 251101000278
            r'เลขที่\s*[:.]?\s*(\d+)',  # เลขที่: 251101000278
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                if len(doc_num) >= 8:
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
    
    def parse_html_table(self, text: str) -> Dict[str, str]:
        """
        แปลงข้อมูลจาก HTML table structure หรือ pipe-separated text
        อ่านทีละบรรทัด
        """
        result = {}
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Pattern 1: Key: Value หรือ Key Value (เช่น: Subtotal (excluding VAT): 0.45)
            colon_match = re.search(r'^(.+?)\s*[:.]?\s*(.+)$', line)
            if colon_match:
                key = colon_match.group(1).strip()
                value = colon_match.group(2).strip()
                # ข้ามถ้า value เป็น empty หรือเป็น header
                if value and not any(keyword in line.upper() for keyword in ['DESCRIPTION', 'AMOUNT IN THB', 'TAX AMOUNT']):
                    result[key] = value
                    logger.info(f"📋 [Parse HTML Table] พบ: {key} = {value}")
            
            # Pattern 2: === Key === หรือ === Value === (เช่น: === 0.48 บาท ===)
            triple_equal_match = re.search(r'^===\s*(.+?)\s*===$', line)
            if triple_equal_match:
                content = triple_equal_match.group(1).strip()
                # ถ้าเป็นตัวเลขหรือจำนวนเงิน ให้เก็บไว้
                if re.search(r'[\d.]+', content):
                    # ลบ "บาท" ออกและเก็บเฉพาะตัวเลข
                    amount_str = content.replace('บาท', '').replace(',', '').strip()
                    result['Total'] = amount_str
                    logger.info(f"📋 [Parse HTML Table] พบ Total: {amount_str}")
            
            # Pattern 3: Pipe-separated values
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    # ถ้าเป็น header row ให้ข้าม
                    if any(keyword in line.upper() for keyword in ['DESCRIPTION', 'AMOUNT', 'TAX', 'HEADER']):
                        continue
                    # ถ้าเป็น data row ให้เก็บข้อมูล
                    for i, part in enumerate(parts):
                        if part and not part.startswith('-'):
                            result[f'Column_{i}'] = part
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        จาก: Subtotal (excluding VAT): 0.45
        จาก: Discount: 0.00
        จาก: Value Added Tax: 0.03
        จาก: Total: 0.48 บาท (จาก === 0.48 บาท ===)
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        logger.info("🔍 [Extract Amounts] เริ่มดึงยอดเงิน...")
        
        # อ่านข้อมูลจาก HTML table structure
        table_data = self.parse_html_table(text)
        
        # ค้นหายอดก่อนภาษีมูลค่าเพิ่ม: Subtotal (excluding VAT) - Discount
        subtotal = None
        discount = None
        
        for key, value in table_data.items():
            if 'subtotal' in key.lower() and 'excluding' in key.lower() and 'vat' in key.lower():
                try:
                    amount_str = value.replace(',', '').replace(' ', '').strip()
                    subtotal = float(amount_str)
                    logger.info(f"✅ [Extract Amounts] พบ Subtotal: {subtotal}")
                except (ValueError, AttributeError):
                    continue
            
            if 'discount' in key.lower():
                try:
                    amount_str = value.replace(',', '').replace(' ', '').replace('-', '').strip()
                    discount = float(amount_str)
                    logger.info(f"✅ [Extract Amounts] พบ Discount: {discount}")
                except (ValueError, AttributeError):
                    continue
        
        # คำนวณยอดก่อนภาษีมูลค่าเพิ่ม
        if subtotal is not None:
            if discount is not None:
                result['amount_before_vat'] = subtotal - discount
            else:
                result['amount_before_vat'] = subtotal
            logger.info(f"✅ [Extract Amounts] ยอดก่อนภาษีมูลค่าเพิ่ม: {result['amount_before_vat']}")
        
        # ค้นหายอดภาษีมูลค่าเพิ่ม: Value Added Tax
        for key, value in table_data.items():
            if 'value added tax' in key.lower() or ('vat' in key.lower() and 'tax' in key.lower()):
                try:
                    amount_str = value.replace(',', '').replace(' ', '').strip()
                    amount = float(amount_str)
                    result['vat_amount'] = amount
                    logger.info(f"✅ [Extract Amounts] พบยอดภาษีมูลค่าเพิ่ม: {amount}")
                    break
                except (ValueError, AttributeError):
                    continue
        
        # ค้นหายอดหลังบวกภาษีมูลค่าเพิ่ม: Total (จาก === 0.48 บาท ===)
        for key, value in table_data.items():
            if 'total' in key.lower() and 'บาท' not in key.lower():
                try:
                    # ลบ "บาท" ออก
                    amount_str = value.replace('บาท', '').replace(',', '').replace(' ', '').strip()
                    amount = float(amount_str)
                    result['total_amount'] = amount
                    logger.info(f"✅ [Extract Amounts] พบยอดหลังบวกภาษีมูลค่าเพิ่ม: {amount}")
                    break
                except (ValueError, AttributeError):
                    continue
        
        # Fallback: ใช้ regex patterns ถ้าไม่พบจาก table
        if result['amount_before_vat'] is None:
            # หา Subtotal และ Discount
            subtotal_match = re.search(r'Subtotal\s+\(excluding\s+VAT\)\s*[:.]?\s*([\d.]+)', text, re.IGNORECASE)
            discount_match = re.search(r'Discount\s*[:.]?\s*-?\s*([\d.]+)', text, re.IGNORECASE)
            
            if subtotal_match:
                try:
                    subtotal = float(subtotal_match.group(1))
                    discount = 0.0
                    if discount_match:
                        discount = float(discount_match.group(1))
                    result['amount_before_vat'] = subtotal - discount
                    logger.info(f"✅ [Extract Amounts] พบยอดก่อนภาษีมูลค่าเพิ่ม (regex): {result['amount_before_vat']}")
                except (ValueError, IndexError):
                    pass
        
        if result['vat_amount'] is None:
            patterns = [
                r'Value\s+Added\s+Tax\s*[:.]?\s*([\d.]+)',
                r'VALUE\s+ADDED\s+TAX\s*[:.]?\s*([\d.]+)',
                r'ภาษีมูลค่าเพิ่ม\s*[:.]?\s*([\d.]+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '').strip()
                        amount = float(amount_str)
                        result['vat_amount'] = amount
                        logger.info(f"✅ [Extract Amounts] พบยอดภาษีมูลค่าเพิ่ม (regex): {amount}")
                        break
                    except (ValueError, IndexError):
                        continue
        
        if result['total_amount'] is None:
            # Pattern: === 0.48 บาท === หรือ Total: 0.48
            patterns = [
                r'===\s*([\d.]+)\s*บาท\s*===',
                r'Total\s*[:.]?\s*([\d.]+)',
                r'TOTAL\s*[:.]?\s*([\d.]+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '').strip()
                        amount = float(amount_str)
                        result['total_amount'] = amount
                        logger.info(f"✅ [Extract Amounts] พบยอดหลังบวกภาษีมูลค่าเพิ่ม (regex): {amount}")
                        break
                    except (ValueError, IndexError):
                        continue
        
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
            'address_full': 'เลขที่ 140 อาคาร 140 ไวร์เลส ชั้น 22 ยูนิต ซี ถนนวิทยุ แขวงลุมพินี เขตปทุมวัน กรุงเทพมหานคร 10330',
            'address_number': '140',  # เลขที่
            'address_other': 'อาคาร 140 ไวร์เลส ชั้น 22 ยูนิต ซี',  # อื่นๆ
            'address_road': 'ถนนวิทยุ',  # ถนน
            'address_soi': None,  # ซอย
            'address_subdistrict': 'ลุมพินี',  # แขวง
            'address_district': 'ปทุมวัน',  # เขต
            'address_province': 'กรุงเทพมหานคร',  # จังหวัด
            'address_postal_code': '10330'  # เลขไปรษณีย์
        }
        
        logger.info(f"✅ [Extract Address] ใช้ที่อยู่ตามที่กำหนด: {result['address_full'][:50]}...")
        return result
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจสอบประเภทเอกสาร
        Returns:
            0 = ไม่มีภาษีมูลค่าเพิ่ม
            1 = มีภาษีมูลค่าเพิ่ม
        """
        # เอกสารนี้มีภาษีมูลค่าเพิ่ม (VAT > 0)
        if amounts.get('vat_amount') and amounts.get('vat_amount', 0) > 0:
            return 1
        return 1  # Default: มีภาษีมูลค่าเพิ่ม
    
    def clean_filename(self, filename: str) -> str:
        """
        ทำความสะอาดชื่อไฟล์
        เป็น: ค่าบริการ_Beam
        """
        if not filename:
            return ""
        
        # ถ้าเป็นเอกสาร Beam Data ให้แปลงเป็นชื่อที่กำหนด
        return "ค่าบริการ_Beam"
    
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
        logger.info(f"🔍 [Beam Data] เริ่มดึงข้อมูลจากเอกสาร...")
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
        logger.info(f"✅ [Beam Data] ดึงข้อมูลเสร็จสิ้น")
        logger.info(f"   - บริษัท: {company_name}")
        logger.info(f"   - เลขที่ผู้เสียภาษี: {tax_id}")
        logger.info(f"   - วันที่: {date}")
        logger.info(f"   - เลขที่เอกสาร: {document_number}")
        logger.info(f"   - ยอดก่อนภาษีมูลค่าเพิ่ม: {amounts.get('amount_before_vat')}")
        logger.info(f"   - ยอดภาษีมูลค่าเพิ่ม: {amounts.get('vat_amount')}")
        logger.info(f"   - ยอดหลังบวกภาษีมูลค่าเพิ่ม: {amounts.get('total_amount')}")
        logger.info("=" * 80)
        
        return result

