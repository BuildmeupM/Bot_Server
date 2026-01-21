"""
CK Line (Thailand) Invoice Extractor
======================================
Extractor สำหรับดึงข้อมูลจาก บริษัท ซีเค ไลน์ (ประเทศไทย) จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class CKLineThailandExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท ซีเค ไลน์ (ประเทศไทย) จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "ซีเค ไลน์",
        "CK Line",
        "CK LINE"
    ]
    
    def __init__(self):
        """Initialize CK Line (Thailand) Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ CK Line (Thailand) หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท ซีเค ไลน์ (ประเทศไทย) จำกัด"
        2. Tax ID "0105554036049"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร CK Line (Thailand) (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105554036049"
        has_tax_id = "0105554036049" in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "บริษัท ซีเค ไลน์ (ประเทศไทย) จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษีจาก 'เลขประจำตัวผู้เสียภาษีอากร 0105554036049'"""
        # Pattern: เลขประจำตัวผู้เสียภาษีอากร 0105554036049
        patterns = [
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # ถ้าไม่พบ pattern ให้ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่
        if "0105554036049" in text:
            return "0105554036049"
        
        return None
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา (ถ้ามี)"""
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่จาก 'วันที่ Date 07/11/2025' และแปลงเป็น dd/mm/yyyy"""
        # Pattern: วันที่ Date 07/11/2025
        patterns = [
            r'วันที่\s+Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
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
        """ดึงเลขที่เอกสารจาก 'เลขที่ CKTRT25110387'"""
        # Pattern: เลขที่ CKTRT25110387
        patterns = [
            r'เลขที่\s*[:.]?\s*([A-Z0-9\-]+)',
            r'เลขที่เอกสาร\s*[:.]?\s*([A-Z0-9\-]+)',
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_no = match.group(1).strip()
                if doc_no:
                    return doc_no
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: 628 ชั้น 3 อาคารทริปเพลสไอ ซอยกลับเข็ม ถนนนนทรี แขวงช่องนนทรี เขตยานนาวา กรุงเทพฯ 10120
        
        Returns:
            ที่อยู่รวม (string)
        """
        # หาที่อยู่จาก text
        lines = text.split('\n')
        address_lines = []
        
        # หาตำแหน่งที่เริ่มต้นที่อยู่
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # หา keyword ที่เกี่ยวข้องกับที่อยู่
            if any(keyword in line_clean for keyword in ['628', 'อาคารทริปเพลสไอ', 'ถนนนนทรี', 'แขวงช่องนนทรี', 'เขตยานนาวา', 'กรุงเทพฯ 10120']):
                # ลบข้อมูลที่ไม่จำเป็น
                line_clean = re.sub(r'\s*(โทร\.|แฟกซ์\.|Fax\.|Tel\.).*$', '', line_clean, flags=re.IGNORECASE)
                address_lines.append(line_clean)
                break
            
            # ถ้ามี keyword ที่เกี่ยวข้อง
            if any(keyword in line_clean for keyword in ['628', 'อาคาร', 'ถนนนนทรี', 'กรุงเทพ', '10120']):
                # ตรวจสอบว่ามีรูปแบบที่อยู่ (มีเลขที่, ถนน, แขวง, เขต)
                if re.search(r'\d{3}', line_clean) and ('ถนน' in line_clean or 'แขวง' in line_clean or 'เขต' in line_clean):
                    address_lines.append(line_clean)
                    break
        
        # รวมที่อยู่ทั้งหมด
        if address_lines:
            address = ' '.join(address_lines).strip()
            # ทำความสะอาด: ลบ space หลายตัว
            address = re.sub(r'\s+', ' ', address)
            if len(address) > 10:
                return address
        
        # Fallback: ใช้ที่อยู่ default
        return "628 ชั้น 3 อาคารทริปเพลสไอ ซอยกลับเข็ม ถนนนนทรี แขวงช่องนนทรี เขตยานนาวา กรุงเทพฯ 10120"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': None,
            'withholding_tax_amount': None
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลยอดเงิน
        
        - ยอดก่อนภาษีมูลค่าเพิ่ม: จำนวนเงิน TOTAL 1,308.41
        - ภาษีมูลค่าเพิ่ม: ภาษีมูลค่าเพิ่ม VALUE ADDED TAX 91.59
        - ยอดหลังบวกภาษีมูลค่าเพิ่ม: จำนวนเงินรวมทั้งสิ้น GRAND TOTAL 1,400.00
        """
        amounts = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # ยอดก่อนภาษีมูลค่าเพิ่ม: จำนวนเงิน TOTAL 1,308.41
        amount_patterns = [
            r'จำนวนเงิน\s+TOTAL\s+([\d,]+\.?\d*)',
            r'TOTAL\s+([\d,]+\.?\d*)',
            r'จำนวนเงิน\s+([\d,]+\.?\d*)',
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    amount_val = float(amount_str)
                    if amount_val > 0:
                        amounts['amount_before_vat'] = amount_val
                        break
                except ValueError:
                    pass
        
        # ภาษีมูลค่าเพิ่ม: ภาษีมูลค่าเพิ่ม VALUE ADDED TAX 91.59
        vat_patterns = [
            r'ภาษีมูลค่าเพิ่ม\s+VALUE\s+ADDED\s+TAX\s+([\d,]+\.?\d*)',
            r'ภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d*)',
            r'VALUE\s+ADDED\s+TAX\s+([\d,]+\.?\d*)',
        ]
        for pattern in vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vat_str = match.group(1).replace(',', '').strip()
                try:
                    vat_val = float(vat_str)
                    if vat_val > 0:
                        amounts['vat_amount'] = vat_val
                        break
                except ValueError:
                    pass
        
        # ยอดหลังบวกภาษีมูลค่าเพิ่ม: จำนวนเงินรวมทั้งสิ้น GRAND TOTAL 1,400.00
        total_patterns = [
            r'จำนวนเงินรวมทั้งสิ้น\s+GRAND\s+TOTAL\s+([\d,]+\.?\d*)',
            r'GRAND\s+TOTAL\s+([\d,]+\.?\d*)',
            r'จำนวนเงินรวมทั้งสิ้น\s+([\d,]+\.?\d*)',
        ]
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                total_str = match.group(1).replace(',', '').strip()
                try:
                    total_val = float(total_str)
                    if total_val > 0:
                        amounts['total_amount'] = total_val
                        break
                except ValueError:
                    pass
        
        return amounts
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงหมายเหตุ: B/L NO. CKCONSA0002312 INVOICE NO. CKTIN25110052 {ชื่อไฟล์เก่า}
        อ่านข้อมูลจาก:
        - B/L NO. และ JOB NO. (CKCONS A0002312) -> CKCONSA0002312
        - INVOICE NO. CKTIN25110052
        """
        remark_parts = []
        
        # หา B/L NO. และ JOB NO.
        # รูปแบบ: B/L NO. JOB NO.
        #         CKCONS A0002312
        bl_no = None
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            # หาบรรทัดที่มี "B/L NO." และ "JOB NO."
            if 'B/L NO.' in line_clean.upper() and 'JOB NO.' in line_clean.upper():
                # ดูบรรทัดถัดไป
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # แยกด้วย space และรวมเป็น B/L No. (เช่น CKCONS A0002312 -> CKCONSA0002312)
                    parts = next_line.split()
                    if len(parts) >= 2:
                        # รวมส่วนแรกและส่วนที่สอง (CKCONS + A0002312 = CKCONSA0002312)
                        bl_no = ''.join(parts[:2])
                        break
        
        # ถ้ายังไม่เจอ ลองหาจาก pattern ทั่วไป
        if not bl_no:
            bl_patterns = [
                r'B/L\s+NO[.:]?\s*[:.]?\s*([A-Z0-9]+)',
                r'JOB\s+NO[.:]?\s*[:.]?\s*([A-Z0-9]+)',
            ]
            for pattern in bl_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    bl_no = matches[0]
                    break
        
        # หา INVOICE NO.
        invoice_no = None
        invoice_patterns = [
            r'INVOICE\s+NO[.:]?\s*[:.]?\s*([A-Z0-9]+)',
            r'Invoice\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',
        ]
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_no = match.group(1).strip()
                break
        
        # เพิ่ม B/L NO. และ INVOICE NO. ใน remark
        if bl_no:
            remark_parts.append(f"B/L NO. {bl_no}")
        if invoice_no:
            remark_parts.append(f"INVOICE NO. {invoice_no}")
        
        # เพิ่มชื่อไฟล์ (ตัด WHT_, VAT_, None_vat_ ออก)
        if filename:
            filename_clean = filename
            filename_clean = re.sub(r'(WHT_|VAT_|None_vat_)', '', filename_clean, flags=re.IGNORECASE)
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
        # ที่อยู่: 628 ชั้น 3 อาคารทริปเพลสไอ ซอยกลับเข็ม ถนนนนทรี แขวงช่องนนทรี เขตยานนาวา กรุงเทพฯ 10120
        address_full = address or ''
        building_number = ''  # 628
        other_info = ''  # ชั้น 3 อาคารทริปเพลสไอ ซอยกลับเข็ม
        soi = ''  # ซอย/ตรอก
        road = ''  # ถนนนนทรี
        subdistrict = ''  # แขวงช่องนนทรี
        district = ''  # เขตยานนาวา
        province = ''  # จังหวัดกรุงเทพมหานคร
        postal_code = ''  # รหัสไปรษณีย์ 10120
        
        if address:
            # ดึงเลขที่จาก "628" (อยู่ต้นที่อยู่)
            building_match = re.search(r'^(\d+)', address.strip())
            if building_match:
                building_number = building_match.group(1).strip()
            
            # ดึงอื่นๆ จาก "ชั้น 3 อาคารทริปเพลสไอ ซอยกลับเข็ม"
            # หาส่วนหลังเลขที่และก่อน "ถนน"
            other_match = re.search(r'^\d+\s+(.+?)(?=\s+ถนน)', address)
            if other_match:
                other_info = other_match.group(1).strip()
            
            # ดึงถนนจาก "ถนนนนทรี"
            road_match = re.search(r'ถนน\s*([ก-๙A-Za-z]+)', address)
            if road_match:
                road = f"ถนน{road_match.group(1).strip()}"
            
            # ดึงแขวงจาก "แขวงช่องนนทรี"
            subdistrict_match = re.search(r'แขวง\s*([ก-๙A-Za-z]+)', address)
            if subdistrict_match:
                subdistrict = subdistrict_match.group(1).strip()
            
            # ดึงเขตจาก "เขตยานนาวา"
            district_match = re.search(r'เขต\s*([ก-๙A-Za-z]+)', address)
            if district_match:
                district = district_match.group(1).strip()
            
            # ดึงจังหวัดจาก "กรุงเทพฯ" หรือ "กรุงเทพมหานคร"
            if 'กรุงเทพ' in address:
                province = 'กรุงเทพมหานคร'
            
            # ดึงรหัสไปรษณีย์ (5 หลัก)
            postal_match = re.search(r'(\d{5})\s*$', address)
            if postal_match:
                postal_code = postal_match.group(1).strip()
        
        return {
            'success': True,
            'company': 'CK_LINE_THAILAND',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number or '',  # เลขที่ (628)
            'other_info': other_info or '',  # อื่นๆ (ชั้น 3 อาคารทริปเพลสไอ ซอยกลับเข็ม)
            'soi': soi or '',  # ซอย/ตรอก
            'road': road or '',  # ถนน (ถนนนนทรี)
            'subdistrict': subdistrict or '',  # แขวง (ช่องนนทรี)
            'district': district or '',  # เขต (ยานนาวา)
            'province': province or '',  # จังหวัด (กรุงเทพมหานคร)
            'postal_code': postal_code or '',  # รหัสไปรษณีย์ (10120)
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
