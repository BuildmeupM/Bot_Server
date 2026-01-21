"""
Siam Commercial Seaport Invoice Extractor
==========================================
Extractor สำหรับดึงข้อมูลจาก บริษัท สยามคอมเมอร์เชียล ซีพอร์ท จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class SiamCommercialSeaportExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท สยามคอมเมอร์เชียล ซีพอร์ท จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "สยามคอมเมอร์เชียล ซีพอร์ท",
        "สยามคอมเมอร์เชียล ซีพุธร์ท",  # รูปแบบที่มี "ซีพุธร์ท"
        "Siam Commercial Seaport",
        "SIAM COMMERCIAL SEAPORT",
        "SIAM COMMERCIAL SEAPORT CO.,LTD.",
        "SIAM C",  # รูปแบบย่อ
    ]
    
    def __init__(self):
        """Initialize Siam Commercial Seaport Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Siam Commercial Seaport หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท สยามคอมเมอร์เชียล ซีพอร์ท จำกัด" หรือรูปแบบอื่นๆ
        2. Tax ID "0105518012712"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Siam Commercial Seaport (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105518012712"
        has_tax_id = "0105518012712" in text.replace(' ', '').replace('-', '')
        
        # Log เพื่อ debug
        logger.debug(f"🔍 [Siam Commercial Seaport] ตรวจสอบเอกสาร:")
        logger.debug(f"   - มีชื่อบริษัท: {has_company}")
        logger.debug(f"   - มี Tax ID: {has_tax_id}")
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        result = has_company and has_tax_id
        logger.debug(f"   - ผลลัพธ์: {'✅ ผ่าน' if result else '❌ ไม่ผ่าน'}")
        
        return result
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "บริษัท สยามคอมเมอร์เชียล ซีพอร์ท จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษีจาก 'เลขประจำตัวผู้เสียภาษี : 0105518012712'"""
        # Pattern: เลขประจำตัวผู้เสียภาษี : 0105518012712 หรือ Tax ID : 0105518012712
        patterns = [
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',
            r'TaxID\s*[:.]?\s*(\d{13})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id = match.group(1).strip()
                if tax_id == "0105518012712":
                    return tax_id
        
        # ถ้าไม่พบ pattern ให้ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่ (รองรับช่องว่างและขีด)
        text_clean = text.replace(' ', '').replace('-', '')
        if "0105518012712" in text_clean:
            return "0105518012712"
        
        return None
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขาจาก 'สำนักงานสาขา : 00001'"""
        # Pattern: สำนักงานสาขา : 00001
        patterns = [
            r'สำนักงานสาขา\s*[:.]?\s*(\d{5})',
            r'Branch\s*[:.]?\s*(\d{5})',
            r'สาขา\s*[:.]?\s*(\d{5})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่จาก 'Date : 04/11/2025 15:08' หรือ 'Date: : 19/12/2025 15:47' และแปลงเป็น dd/mm/yyyy (ตัดเวลาออก)"""
        # Pattern: Date : 04/11/2025 15:08 หรือ Date: : 19/12/2025 15:47
        patterns = [
            r'Date\s*[:.]?\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})(?:\s+\d{1,2}:\d{2})?',  # Date: : 19/12/2025 15:47
            r'Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})(?:\s+\d{1,2}:\d{2})?',  # Date : 04/11/2025 15:08
            r'วันที่\s*[:.]?\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})(?:\s+\d{1,2}:\d{2})?',  # วันที่: : 19/12/2025 15:47
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})(?:\s+\d{1,2}:\d{2})?',  # วันที่ : 04/11/2025 15:08
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสารจาก 'Receipt No. : SCSP-2025-047338' หรือ 'Receipt No.: : SCSP-2025-053830'"""
        # Pattern: Receipt No. : SCSP-2025-047338 หรือ Receipt No.: : SCSP-2025-053830
        patterns = [
            r'Receipt\s+No[.:]?\s*[:.]?\s*[:.]?\s*([A-Z0-9\-]+)',  # Receipt No.: : SCSP-2025-053830
            r'Receipt\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',  # Receipt No. : SCSP-2025-047338
            r'เลขที่\s*[:.]?\s*[:.]?\s*([A-Z0-9\-]+)',  # เลขที่: : SCSP-2025-053830
            r'เลขที่\s*[:.]?\s*([A-Z0-9\-]+)',  # เลขที่ : SCSP-2025-047338
            r'Document\s+No[.:]?\s*[:.]?\s*[:.]?\s*([A-Z0-9\-]+)',  # Document No.: : SCSP-2025-053830
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',  # Document No. : SCSP-2025-047338
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_no = match.group(1).strip()
                if doc_no and len(doc_no) > 5:  # ตรวจสอบว่ามีความยาวพอสมควร
                    return doc_no
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: 113/30 ม.1 ถ.สุขุมวิท กม.123 ต.ทุ่งสุขลา อ.ศรีราชา จ.ชลบุรี 20230
        
        Returns:
            ที่อยู่รวม (string)
        """
        # ใช้ที่อยู่ที่กำหนดให้เลย
        return "113/30 ม.1 ถ.สุขุมวิท กม.123 ต.ทุ่งสุขลา อ.ศรีราชา จ.ชลบุรี 20230"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย (กำหนดเปอร์เซ็นต์เป็น 3%)"""
        return {
            'withholding_tax_percent': 3.0,  # กำหนดเป็น 3%
            'withholding_tax_amount': None  # คำนวณทีหลัง
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลยอดเงิน
        
        - Gross Amount 1,000.00 -> amount_before_vat
        - VAT 7% 70.00 -> vat_amount
        - Total Amount 1,070.00 -> total_amount
        - Net Payable Total 1,040.00 (หลังหัก WHT) -> อาจใช้เป็น total_amount ถ้าไม่มี Total Amount
        """
        amounts = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        logger.info("🔍 [Siam Commercial Seaport] เริ่มดึงยอดเงิน...")
        
        # ทำความสะอาด text: ลบ emoji และ label ที่อาจรบกวนการอ่านข้อมูล
        text_clean = text
        # ลบ emoji 💰 และ label "ยอดชำระ:" ถ้ามี
        text_clean = re.sub(r'💰\s*ยอดชำระ\s*[:.]?\s*', '', text_clean)
        text_clean = re.sub(r'ยอดชำระ\s*[:.]?\s*', '', text_clean)
        # ลบช่องว่างส่วนเกิน
        text_clean = re.sub(r'\s+', ' ', text_clean)
        
        logger.debug(f"📄 [Siam Commercial Seaport] Text length: {len(text_clean)} characters")
        
        # ดึง Gross Amount (ยอดก่อนภาษี)
        gross_patterns = [
            r'Gross\s+Amount\s+([\d,]+\.?\d*)',  # Gross Amount 1,000.00
            r'รวมเงิน\s+([\d,]+\.?\d*)',  # รวมเงิน 1,000.00
        ]
        for pattern in gross_patterns:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').replace(' ', '').strip()
                try:
                    amount_val = float(amount_str)
                    if amount_val > 0:
                        amounts['amount_before_vat'] = amount_val
                        logger.info(f"✅ [Siam Commercial Seaport] พบยอดก่อนภาษี: {amount_val}")
                        break
                except ValueError as e:
                    logger.debug(f"⚠️ [Siam Commercial Seaport] ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                    pass
        
        # ดึง VAT 7% (ยอดภาษี)
        vat_patterns = [
            r'VAT\s+7%\s+([\d,]+\.?\d*)',  # VAT 7% 70.00
            r'ภาษีมูลค่าเพิ่ม\s+7%\s+([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม 7% 70.00
            r'ภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม 70.00
        ]
        for pattern in vat_patterns:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').replace(' ', '').strip()
                try:
                    amount_val = float(amount_str)
                    if amount_val > 0:
                        amounts['vat_amount'] = amount_val
                        logger.info(f"✅ [Siam Commercial Seaport] พบยอดภาษี: {amount_val}")
                        break
                except ValueError as e:
                    logger.debug(f"⚠️ [Siam Commercial Seaport] ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                    pass
        
        # ดึง Total Amount (ยอดรวม)
        total_patterns = [
            r'Total\s+Amount\s+([\d,]+\.?\d*)',  # Total Amount 1,070.00
            r'ยอดเงินสุทธิ\s+([\d,]+\.?\d*)',  # ยอดเงินสุทธิ 1,070.00
            r'Net\s+Payable\s+Total\s+([\d,]+\.?\d*)',  # Net Payable Total 1,040.00 (ใช้เป็น fallback ถ้าไม่มี Total Amount)
        ]
        for pattern in total_patterns:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').replace(' ', '').strip()
                try:
                    amount_val = float(amount_str)
                    if amount_val > 0:
                        # ถ้าเป็น Net Payable Total และยังไม่มี total_amount ให้ใช้เป็น total_amount
                        if 'Net Payable' in pattern and amounts['total_amount'] is None:
                            amounts['total_amount'] = amount_val
                            logger.info(f"✅ [Siam Commercial Seaport] พบยอดรวม (Net Payable Total): {amount_val}")
                        elif 'Total Amount' in pattern or 'ยอดเงินสุทธิ' in pattern:
                            amounts['total_amount'] = amount_val
                            logger.info(f"✅ [Siam Commercial Seaport] พบยอดรวม: {amount_val}")
                        break
                except ValueError as e:
                    logger.debug(f"⚠️ [Siam Commercial Seaport] ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                    pass
        
        # Fallback: ถ้าไม่มี total_amount แต่มี amount_before_vat และ vat_amount ให้คำนวณ
        if amounts['total_amount'] is None and amounts['amount_before_vat'] is not None and amounts['vat_amount'] is not None:
            amounts['total_amount'] = amounts['amount_before_vat'] + amounts['vat_amount']
            logger.info(f"✅ [Siam Commercial Seaport] คำนวณยอดรวม: {amounts['total_amount']} = {amounts['amount_before_vat']} + {amounts['vat_amount']}")
        
        # Fallback: ถ้าไม่มี amount_before_vat แต่มี total_amount และ vat_amount ให้คำนวณ
        if amounts['amount_before_vat'] is None and amounts['total_amount'] is not None and amounts['vat_amount'] is not None:
            amounts['amount_before_vat'] = amounts['total_amount'] - amounts['vat_amount']
            logger.info(f"✅ [Siam Commercial Seaport] คำนวณยอดก่อนภาษี: {amounts['amount_before_vat']} = {amounts['total_amount']} - {amounts['vat_amount']}")
        
        # Fallback: ถ้าไม่มี vat_amount แต่มี total_amount และ amount_before_vat ให้คำนวณ
        if amounts['vat_amount'] is None and amounts['total_amount'] is not None and amounts['amount_before_vat'] is not None:
            amounts['vat_amount'] = amounts['total_amount'] - amounts['amount_before_vat']
            logger.info(f"✅ [Siam Commercial Seaport] คำนวณยอดภาษี: {amounts['vat_amount']} = {amounts['total_amount']} - {amounts['amount_before_vat']}")
        
        logger.info(f"📊 [Siam Commercial Seaport] ผลลัพธ์: amount_before_vat={amounts['amount_before_vat']}, vat_amount={amounts['vat_amount']}, total_amount={amounts['total_amount']}")
        
        return amounts
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงหมายเหตุ: B/L No. : SZXCB25090716 {ชื่อไฟล์เก่า}
        ตัด VAT_, WHT_, None_vat_ ออกจากชื่อไฟล์
        """
        remark_parts = []
        
        # ดึง B/L No.
        bl_patterns = [
            r'B/L\s+No[.:]?\s*[:.]?\s*[:.]?\s*([A-Z0-9]+)',  # B/L No.: : CANCB25085616
            r'B/L\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # B/L No. : CANCB25085616
            r'B\/L\s+No[.:]?\s*[:.]?\s*[:.]?\s*([A-Z0-9]+)',  # B/L No.: : CANCB25085616
            r'B\/L\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # B/L No. : CANCB25085616
        ]
        for pattern in bl_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bl_no = match.group(1).strip()
                if bl_no and len(bl_no) >= 6:  # ตรวจสอบว่ามีความยาวพอสมควร
                    remark_parts.append(f"B/L No. : {bl_no}")
                    break
        
        # เพิ่มชื่อไฟล์ (ตัด VAT_, WHT_, None_vat_ ออก)
        if filename:
            filename_clean = filename
            # ตัด VAT_, WHT_, None_vat_ ออก
            filename_clean = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename_clean, flags=re.IGNORECASE)
            # ตัด .pdf ออก
            filename_clean = re.sub(r'\.pdf$', '', filename_clean, flags=re.IGNORECASE)
            if filename_clean:
                remark_parts.append(filename_clean)
        
        if remark_parts:
            return ' '.join(remark_parts)
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร (1 = มีภาษีมูลค่าเพิ่ม)"""
        return 1  # มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ (optional)
            filepath: path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # หาส่วนต้นฉบับของใบกำกับภาษีก่อน
        original_section = self.extract_original_invoice_section(text)
        if original_section:
            # ใช้เฉพาะส่วนต้นฉบับในการดึงข้อมูล
            text = original_section
            logger.info("✅ ใช้เฉพาะส่วนต้นฉบับของใบกำกับภาษีในการดึงข้อมูล")
        
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
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, None_vat_, WHT_)
        new_filename = filename
        if new_filename:
            new_filename = re.sub(r'(VAT_|None_vat_|WHT_)', '', new_filename, flags=re.IGNORECASE)
        
        # แยกที่อยู่เป็นส่วนๆ
        # ที่อยู่: 113/30 ม.1 ถ.สุขุมวิท กม.123 ต.ทุ่งสุขลา อ.ศรีราชา จ.ชลบุรี 20230
        address_full = address or ''
        building_number = ''
        other_info = ''
        soi = ''  # ซอย/ตรอก
        road = ''
        subdistrict = ''
        district = ''
        province = ''
        postal_code = ''
        
        if address:
            # ดึงเลขที่จาก "113/30" (อยู่ต้นที่อยู่)
            building_match = re.search(r'^(\d+(?:/\d+)?)', address.strip())
            if building_match:
                building_number = building_match.group(1).strip()
            
            # ดึงอื่นๆ จาก "ม.1"
            moo_match = re.search(r'ม\.(\d+)', address)
            if moo_match:
                other_info = f"ม.{moo_match.group(1)}"
            
            # ดึงถนนจาก "ถ.สุขุมวิท กม.123"
            # หาชื่อถนนจาก "ถ.สุขุมวิท"
            road_name_match = re.search(r'ถ\.([ก-๙A-Za-z]+)', address)
            if road_name_match:
                road_name = road_name_match.group(1).strip()
                # หา "กม.123" ถ้ามี
                km_match = re.search(r'กม\.(\d+)', address)
                if km_match:
                    road = f"ถนน{road_name} กม.{km_match.group(1)}"
                else:
                    road = f"ถนน{road_name}"
            
            # ดึงตำบลจาก "ต.ทุ่งสุขลา"
            subdistrict_match = re.search(r'ต\.([ก-๙A-Za-z]+?)(?:\s+อ\.|จ\.|\d{5}|$)', address)
            if subdistrict_match:
                subdistrict = subdistrict_match.group(1).strip()
            
            # ดึงอำเภอจาก "อ.ศรีราชา"
            district_match = re.search(r'อ\.([ก-๙A-Za-z]+?)(?:\s+จ\.|\d{5}|$)', address)
            if district_match:
                district = district_match.group(1).strip()
            
            # ดึงจังหวัดจาก "จ.ชลบุรี"
            province_match = re.search(r'จ\.(ชลบุรี)', address)
            if province_match:
                province = province_match.group(1).strip()
            
            # ดึงรหัสไปรษณีย์ (5 หลัก)
            postal_match = re.search(r'(\d{5})\s*$', address)
            if postal_match:
                postal_code = postal_match.group(1).strip()
        
        return {
            'success': True,
            'company': 'SIAM_COMMERCIAL_SEAPORT',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,  # สาขา
            'date': date,
            'document_number': document_number,
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number,  # เลขที่ (113/30)
            'other_info': other_info,  # อื่นๆ (ม.1)
            'soi': soi,  # ซอย/ตรอก
            'road': road,  # ถนน (ถนนสุขุมวิท กม.123)
            'subdistrict': subdistrict,  # ตำบล (ทุ่งสุขลา)
            'district': district,  # อำเภอ (ศรีราชา)
            'province': province,  # จังหวัด (ชลบุรี)
            'postal_code': postal_code,  # รหัสไปรษณีย์ (20230)
            'account_name': account_info['account_name'],
            'account_code': account_info['account_code'],
            'withholding_tax_percent': withholding['withholding_tax_percent'],
            'withholding_tax_amount': withholding['withholding_tax_amount'],
            'amount_before_vat': amounts['amount_before_vat'],
            'vat_amount': amounts['vat_amount'],
            'total_amount': amounts['total_amount'],
            'remark': remark,
            'new_filename': new_filename,
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,  # 1 = มีภาษีมูลค่าเพิ่ม
        }
