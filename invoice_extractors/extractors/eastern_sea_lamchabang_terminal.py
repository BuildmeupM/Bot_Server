"""
Eastern Sea Lamchabang Terminal Invoice Extractor
===================================================
Extractor สำหรับดึงข้อมูลจาก บริษัท อีสเทิร์นซี แหลมฉบัง เทอร์มินัล จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class EasternSeaLamchabangTerminalExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท อีสเทิร์นซี แหลมฉบัง เทอร์มินัล จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "อีสเทิร์นซี แหลมฉบัง เทอร์มินัล",
        "Eastern Sea Lamchabang Terminal"
    ]
    
    def __init__(self):
        """Initialize Eastern Sea Lamchabang Terminal Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Eastern Sea Lamchabang Terminal หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท อีสเทิร์นซี แหลมฉบัง เทอร์มินัล จำกัด"
        2. Tax ID "0105533144471"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Eastern Sea Lamchabang Terminal (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105533144471"
        has_tax_id = "0105533144471" in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "บริษัท อีสเทิร์นซี แหลมฉบัง เทอร์มินัล จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TaxID 0105533144471 หรือ Tax ID No. 0105533144471 หรือ เลขประจำตัวผู้เสียภาษีอากร 0105533144471 (สำนักงานใหญ่)
        # เพิ่มความสำคัญให้กับ "เลขประจำตัวผู้เสียภาษีอากร" เป็นอันดับแรก
        patterns = [
            # รูปแบบหลัก: เลขประจำตัวผู้เสียภาษีอากร 0105533144471 (ไม่มีเครื่องหมาย : หรือ .)
            r'เลขประจำตัวผู้เสียภาษีอากร\s+(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0105533144471
            # รูปแบบที่มีเครื่องหมาย : หรือ . ตามหลัง
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร: 0105533144471
            # รูปแบบที่มีวงเล็บ (สำนักงานใหญ่)
            r'เลขประจำตัวผู้เสียภาษีอากร\s+(\d{13})\s*\([^)]+\)',  # เลขประจำตัวผู้เสียภาษีอากร 0105533144471 (สำนักงานใหญ่)
            # รูปแบบที่มีช่องว่างในเลข (0105 5331 44471)
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{4}\s+\d{4}\s+\d{5})',  # เลขประจำตัวผู้เสียภาษีอากร: 0105 5331 44471
            # รูปแบบอื่นๆ
            r'TaxID\s*[:.]?\s*(\d{13})',  # TaxID: 0105533144471
            r'Tax\s+ID\s+No[.:]?\s*(\d{13})',  # Tax ID No.: 0105533144471
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0105533144471
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี: 0105533144471
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID: 0105533144471
            r'TAXID\s*[:.]?\s*(\d{13})',  # TAXID: 0105533144471
            r'Tax\s*ID\s*[:.]?\s*(\d{4}\s+\d{4}\s+\d{5})',  # Tax ID: 0105 5331 44471 (มีช่องว่าง)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id = match.group(1).replace(' ', '')  # ลบช่องว่าง
                if len(tax_id) == 13:
                    return tax_id
        
        # Fallback: ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่ (รองรับช่องว่างและขีด)
        text_clean = text.replace(' ', '').replace('-', '')
        if "0105533144471" in text_clean:
            return "0105533144471"
        
        # ลองหาจากรูปแบบทั่วไป: ตัวเลข 13 หลักที่อยู่ใกล้กับคำว่า Tax, ID, หรือเลขประจำตัว
        # หา pattern ที่มี Tax ID หรือเลขประจำตัว แล้วตามด้วยตัวเลข 13 หลัก
        general_patterns = [
            r'(?:Tax|TAX|เลขประจำตัวผู้เสียภาษี)[^0-9]*(\d{13})',
            r'(\d{4}\s*\d{4}\s*\d{5})',  # รูปแบบที่มีช่องว่าง: 0105 5331 44471
        ]
        
        for pattern in general_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                tax_id = match.group(1).replace(' ', '').replace('-', '')
                if len(tax_id) == 13 and tax_id == "0105533144471":
                    return tax_id
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern 1: === วันที่ === แล้วตามด้วย 04/11/2025 (ในบรรทัดเดียวกัน)
        # รองรับกรณีที่ OCR อ่าน === เป็น = หรือ == หรือ === หรือมีช่องว่างผิดปกติ
        pattern1 = r'=+\s*วันที่\s*=+\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            return f"{day}/{month}/{year}"
        
        # Pattern 2: === วันที่ === แล้ววันที่อยู่ในบรรทัดถัดไป (ปรับปรุงให้จับได้ดีขึ้น)
        # รองรับทั้ง \n และ \r\n และช่องว่างผิดปกติ
        pattern2 = r'=+\s*วันที่\s*=+\s*[\r\n\s]+(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern2, text, re.IGNORECASE | re.MULTILINE)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            return f"{day}/{month}/{year}"
        
        # Pattern 3: หา "=== วันที่ ===" แล้วหาวันที่ในบรรทัดถัดไป (รองรับหลายรูปแบบ)
        # ปรับปรุงให้จับได้ดีขึ้น โดยเพิ่มระยะห่างที่รองรับได้มากขึ้น
        # รองรับกรณีที่ OCR อ่าน === เป็น = หรือ == หรือ ===
        date_header_match = re.search(r'=+\s*วันที่\s*=+', text, re.IGNORECASE)
        if date_header_match:
            # หาวันที่ในบรรทัดถัดไป (ภายใน 200 ตัวอักษร) - รองรับ space, newline, และ tab
            start_pos = date_header_match.end()
            next_text = text[start_pos:start_pos+200]
            # หาวันที่ (รองรับ space, newline, tab นำหน้าและหลัง)
            # รองรับทั้ง / และ - เป็นตัวคั่น
            # รองรับกรณีที่ OCR อ่านตัวเลขผิด เช่น 0 เป็น O หรือ 1 เป็น l
            date_match = re.search(r'[\s\r\n\t]*([0-9OIl]{1,2})[/-]([0-9OIl]{1,2})[/-]([0-9OIl]{4})[\s\r\n\t]*', next_text)
            if date_match:
                day = date_match.group(1).replace('O', '0').replace('I', '1').replace('l', '1').zfill(2)
                month = date_match.group(2).replace('O', '0').replace('I', '1').replace('l', '1').zfill(2)
                year = date_match.group(3).replace('O', '0').replace('I', '1').replace('l', '1')
                # ตรวจสอบว่าเป็นวันที่ที่ถูกต้อง
                if day.isdigit() and month.isdigit() and year.isdigit():
                    return f"{day}/{month}/{year}"
        
        # Pattern 4: วันที่: 04/11/2025 (รองรับช่องว่างผิดปกติ)
        pattern4 = r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern4, text)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            return f"{day}/{month}/{year}"
        
        # Pattern 5: Date: 04/11/2025 หรือ Date 04/11/2025 (รองรับช่องว่างผิดปกติ)
        pattern5 = r'Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern5, text, re.IGNORECASE)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            return f"{day}/{month}/{year}"
        
        # Pattern 6: รูปแบบอื่นๆ เช่น 04-Nov-2025, 04/Nov/2025
        month_map = {
            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
            'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        pattern6 = r'(?:วันที่|Date)\s*[:.]?\s*(\d{1,2})[/-]([A-Za-z]{3})[/-](\d{4})'
        match = re.search(pattern6, text, re.IGNORECASE)
        if match:
            day = match.group(1).zfill(2)
            month_abbr = match.group(2).upper()
            year = match.group(3)
            month = month_map.get(month_abbr, '01')
            return f"{day}/{month}/{year}"
        
        # Pattern 7: หาวันที่ที่อยู่ใกล้กับคำว่า "วันที่" หรือ "Date" (fallback)
        # หา "วันที่" หรือ "Date" แล้วหาตัวเลขในรูปแบบวันที่ในระยะ 50 ตัวอักษร
        date_keywords = [r'วันที่', r'Date']
        for keyword_pattern in date_keywords:
            keyword_matches = re.finditer(keyword_pattern, text, re.IGNORECASE)
            for keyword_match in keyword_matches:
                start_pos = keyword_match.end()
                search_text = text[start_pos:start_pos+50]
                date_match = re.search(r'[\s\r\n\t]*(\d{1,2})[/-](\d{1,2})[/-](\d{4})', search_text)
                if date_match:
                    day = date_match.group(1).zfill(2)
                    month = date_match.group(2).zfill(2)
                    year = date_match.group(3)
                    return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern 1: === เลขที่ === แล้วตามด้วย A25111491 (ในบรรทัดเดียวกัน)
        # รองรับกรณีที่ OCR อ่าน === เป็น = หรือ == หรือ === หรือมีช่องว่างผิดปกติ
        pattern1 = r'=+\s*เลขที่\s*=+\s*([A-Z0-9\-]+)'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            doc_num = match.group(1).strip()
            if len(doc_num) >= 6:
                return doc_num
        
        # Pattern 2: === เลขที่ === แล้วเลขที่อยู่ในบรรทัดถัดไป (ปรับปรุงให้จับได้ดีขึ้น)
        # รองรับทั้ง \n และ \r\n และช่องว่างผิดปกติ
        pattern2 = r'=+\s*เลขที่\s*=+\s*[\r\n\s]+([A-Z0-9\-]+)'
        match = re.search(pattern2, text, re.IGNORECASE | re.MULTILINE)
        if match:
            doc_num = match.group(1).strip()
            if len(doc_num) >= 6:
                return doc_num
        
        # Pattern 3: หา "=== เลขที่ ===" แล้วหาเลขที่ในบรรทัดถัดไป (รองรับหลายรูปแบบ)
        # ปรับปรุงให้จับได้ดีขึ้น โดยเพิ่มระยะห่างที่รองรับได้มากขึ้น
        # รองรับกรณีที่ OCR อ่าน === เป็น = หรือ == หรือ ===
        doc_header_match = re.search(r'=+\s*เลขที่\s*=+', text, re.IGNORECASE)
        if doc_header_match:
            # หาเลขที่ในบรรทัดถัดไป (ภายใน 150 ตัวอักษร) - รองรับ space, newline, และ tab
            start_pos = doc_header_match.end()
            next_text = text[start_pos:start_pos+150]
            # หา pattern ที่เริ่มด้วยตัวอักษรหรือตัวเลข (A-Z0-9) - รองรับ space, newline, tab นำหน้า
            # รูปแบบ: " A25111491" หรือ "A25111491" หรือ "\nA25111491"
            # ต้องมีอย่างน้อย 6 ตัวอักษร/ตัวเลข และอาจมีขีด (-)
            # รองรับกรณีที่ OCR อ่านตัวอักษรผิด เช่น 0 เป็น O หรือ 1 เป็น l
            doc_match = re.search(r'[\s\r\n\t]*([A-Z0-9OIl\-]{6,})', next_text, re.IGNORECASE)
            if doc_match:
                doc_num = doc_match.group(1).strip()
                # แก้ไขตัวอักษรที่ OCR อ่านผิด
                doc_num = doc_num.replace('O', '0').replace('I', '1').replace('l', '1')
                # ตรวจสอบว่าเป็นเลขที่เอกสารที่ถูกต้อง (ต้องมีตัวอักษรหรือตัวเลข)
                if len(doc_num) >= 6:
                    return doc_num
        
        # Pattern 4: เลขที่: A25111491 (รูปแบบเดิม - รองรับช่องว่างผิดปกติ)
        patterns = [
            r'เลขที่\s*[:.]?\s*([A-Z0-9\-]+)',  # เลขที่: A25111491
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',  # Document No: A25111491
            r'Document\s*No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',  # Document No.: A25111491
            r'Invoice\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',  # Invoice No: A25111491
            r'Receipt\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',  # Receipt No: A25111491
            r'No[.:]?\s*[:.]?\s*([A-Z0-9\-]{6,})',  # No: A25111491 (ต้องมีอย่างน้อย 6 ตัว)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                # แก้ไขตัวอักษรที่ OCR อ่านผิด
                doc_num = doc_num.replace('O', '0').replace('I', '1').replace('l', '1')
                if len(doc_num) >= 6:
                    return doc_num
        
        # Pattern 5: หาเลขที่ที่อยู่ใกล้กับคำว่า "เลขที่" หรือ "Document No" (fallback)
        # หา "เลขที่" หรือ "Document No" แล้วหาตัวอักษร/ตัวเลขในระยะ 50 ตัวอักษร
        doc_keywords = [r'เลขที่', r'Document\s+No', r'Invoice\s+No']
        for keyword_pattern in doc_keywords:
            keyword_matches = re.finditer(keyword_pattern, text, re.IGNORECASE)
            for keyword_match in keyword_matches:
                start_pos = keyword_match.end()
                search_text = text[start_pos:start_pos+50]
                doc_match = re.search(r'[\s\r\n\t]*([A-Z0-9\-]{6,})', search_text, re.IGNORECASE)
                if doc_match:
                    doc_num = doc_match.group(1).strip()
                    # แก้ไขตัวอักษรที่ OCR อ่านผิด
                    doc_num = doc_num.replace('O', '0').replace('I', '1').replace('l', '1')
                    if len(doc_num) >= 6:
                        return doc_num
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: อาคารท่าเทียบเรือพาณิชย์แหลมฉบัง ท่าเทียบเรือตู้สินค้า หมายเลข 3 ถนนสุขุมวิท ตำบลทุ่งสุขลา อำเภอศรีราชา จังหวัดชลบุรี 20230
        
        Returns:
            ที่อยู่รวม (string) - ระบบจะแยกเป็นส่วนๆ อัตโนมัติใน parse_address()
        """
        # ลองหาที่อยู่จาก text ก่อน (มักจะอยู่หลังชื่อบริษัท)
        lines = text.split('\n')
        address_lines = []
        collecting = False
        
        # หาตำแหน่งที่เริ่มต้นที่อยู่ (มักจะอยู่หลังชื่อบริษัท)
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # หา "บริษัท อีสเทิร์นซี แหลมฉบัง เทอร์มินัล จำกัด" แล้วเก็บบรรทัดถัดไปที่เป็นที่อยู่
            if 'อีสเทิร์นซี แหลมฉบัง เทอร์มินัล' in line_clean and 'บริษัท' in line_clean:
                # เริ่มเก็บบรรทัดถัดไป
                collecting = True
                continue
            
            # ถ้ากำลังเก็บข้อมูลที่อยู่
            if collecting:
                # หยุดเมื่อเจอ TaxID, Tax ID, เลขประจำตัวผู้เสียภาษี, หรือ header อื่นๆ
                if any(keyword in line_clean for keyword in ['TaxID', 'Tax ID', 'เลขประจำตัวผู้เสียภาษี', 'ใบเสร็จ', 'ใบกำกับ', '===']):
                    break
                
                # เก็บบรรทัดที่มีข้อมูล (ไม่ใช่บรรทัดว่าง และมีความยาวมากกว่า 20 ตัวอักษร)
                if line_clean and len(line_clean) > 20:
                    # ตรวจสอบว่ามีรูปแบบที่อยู่ (มีคำว่า "อาคาร", "ถนน", "ตำบล", "อำเภอ", "จังหวัด" หรือ "หมายเลข")
                    if any(keyword in line_clean for keyword in ['อาคาร', 'ถนน', 'ตำบล', 'อำเภอ', 'จังหวัด', 'หมายเลข', 'ชลบุรี']):
                        address_lines.append(line_clean)
                        break  # หาได้แล้ว ให้หยุด
        
        # รวมที่อยู่ทั้งหมด
        if address_lines:
            address = ' '.join(address_lines).strip()
            # ทำความสะอาด: ลบ space หลายตัว
            address = re.sub(r'\s+', ' ', address)
            if len(address) > 20:
                return address
        
        # Fallback: ใช้ที่อยู่ default
        return "อาคารท่าเทียบเรือพาณิชย์แหลมฉบัง ท่าเทียบเรือตู้สินค้า หมายเลข 3 ถนนสุขุมวิท ตำบลทุ่งสุขลา อำเภอศรีราชา จังหวัดชลบุรี 20230"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': 0.0,
            'withholding_tax_amount': 0.0
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (1,000.00)
                'vat_amount': float,          # ยอดภาษี (70.00)
                'total_amount': float         # ยอดรวม (1,070.00)
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # Pattern 1: รวมเงิน | 1,000.00 (รองรับหลายรูปแบบ)
        patterns_before_vat = [
            r'รวมเงิน\s*\|\s*([\d,]+\.?\d{2})',  # รวมเงิน | 1,000.00
            r'รวมเงิน\s*:\s*([\d,]+\.?\d{2})',  # รวมเงิน : 1,000.00
            r'รวมเงิน\s+([\d,]+\.?\d{2})',  # รวมเงิน 1,000.00
            r'รวมเงิน[^0-9]*([\d,]+\.?\d{2})',  # รวมเงิน...1,000.00 (flexible)
        ]
        
        for pattern in patterns_before_vat:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    amount = float(amount_str)
                    if amount > 0:
                        result['amount_before_vat'] = amount
                        break
                except ValueError:
                    continue
        
        # Pattern 2: ภาษีมูลค่าเพิ่ม | 70.00 (รองรับหลายรูปแบบ)
        patterns_vat = [
            r'ภาษีมูลค่าเพิ่ม\s*\|\s*([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม | 70.00
            r'ภาษีมูลค่าเพิ่ม\s*:\s*([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม : 70.00
            r'ภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม 70.00
            r'ภาษีมูลค่าเพิ่ม[^0-9]*([\d,]+\.?\d{2})',  # ภาษีมูลค่าเพิ่ม...70.00 (flexible)
        ]
        
        for pattern in patterns_vat:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    vat_str = match.group(1).replace(',', '').replace(' ', '')
                    vat = float(vat_str)
                    if vat > 0:
                        result['vat_amount'] = vat
                        break
                except ValueError:
                    continue
        
        # Pattern 3: ยอดเงินสุทธิ | 1,070.00 (รองรับหลายรูปแบบ)
        patterns_total = [
            r'ยอดเงินสุทธิ\s*\|\s*([\d,]+\.?\d{2})',  # ยอดเงินสุทธิ | 1,070.00
            r'ยอดเงินสุทธิ\s*:\s*([\d,]+\.?\d{2})',  # ยอดเงินสุทธิ : 1,070.00
            r'ยอดเงินสุทธิ\s+([\d,]+\.?\d{2})',  # ยอดเงินสุทธิ 1,070.00
            r'ยอดเงินสุทธิ[^0-9]*([\d,]+\.?\d{2})',  # ยอดเงินสุทธิ...1,070.00 (flexible)
        ]
        
        for pattern in patterns_total:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    total_str = match.group(1).replace(',', '').replace(' ', '')
                    total = float(total_str)
                    if total > 0:
                        result['total_amount'] = total
                        break
                except ValueError:
                    continue
        
        # ถ้ายังไม่มี total_amount ให้คำนวณจาก amount_before_vat + vat_amount
        if result['total_amount'] is None:
            if result['amount_before_vat'] and result['vat_amount']:
                result['total_amount'] = result['amount_before_vat'] + result['vat_amount']
        
        return result
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงหมายเหตุ (Ref. No. + เบอร์ตู้ + ชื่อไฟล์เก่า)
        
        รูปแบบ: Ref. No.: 125110410439 เบอร์ตู้ NBYYU8153857 {ชื่อไฟล์เก่า}
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF (optional)
        
        Returns:
            หมายเหตุในรูปแบบ "Ref. No.: 125110410439 เบอร์ตู้ NBYYU8153857 {ชื่อไฟล์เก่า}"
        """
        ref_no = None
        container_no = None
        
        # Pattern 1: Ref. No.: 125110410439
        ref_patterns = [
            r'Ref\.\s*No\.\s*[:.]?\s*([0-9]+)',  # Ref. No.: 125110410439
            r'Ref\s*No\s*[:.]?\s*([0-9]+)',  # Ref No: 125110410439
            r'Reference\s*No\.\s*[:.]?\s*([0-9]+)',  # Reference No.: 125110410439
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ref_no = match.group(1).strip()
                break
        
        # Pattern 2: เบอร์ตู้ NBYYU8153857
        container_patterns = [
            r'เบอร์ตู้\s+([A-Z0-9]+)',  # เบอร์ตู้ NBYYU8153857
            r'Container\s+No\.\s*[:.]?\s*([A-Z0-9]+)',  # Container No.: NBYYU8153857
            r'Container\s*[:.]?\s*([A-Z0-9]+)',  # Container: NBYYU8153857
        ]
        
        for pattern in container_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                container_no = match.group(1).strip()
                break
        
        # ดึงชื่อไฟล์เก่าที่ตัด VAT_/None_vat_/WHT_ แล้ว
        filename_clean = None
        if filename:
            # ตัด VAT_, None_vat_, WHT_ และ .pdf
            filename_clean = re.sub(r'(VAT_|None_vat_|WHT_)', '', filename, flags=re.IGNORECASE)
            filename_clean = re.sub(r'\.pdf$', '', filename_clean, flags=re.IGNORECASE)
            filename_clean = filename_clean.strip()
        
        # รวมผลลัพธ์
        parts = []
        if ref_no:
            parts.append(f"Ref. No.: {ref_no}")
        if container_no:
            parts.append(f"เบอร์ตู้ {container_no}")
        if filename_clean:
            parts.append(filename_clean)
        
        return ' '.join(parts) if parts else None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจจับประเภทเอกสาร
        
        Returns:
            1 = เอกสารมีภาษีมูลค่าเพิ่ม (VAT)
        """
        return 1  # มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร Eastern Sea Lamchabang Terminal
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร Eastern Sea Lamchabang Terminal หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร อีสเทิร์นซี แหลมฉบัง เทอร์มินัล'
            }
        
        # หาส่วนต้นฉบับของใบกำกับภาษีก่อน
        original_section = self.extract_original_invoice_section(text)
        if original_section:
            # ใช้เฉพาะส่วนต้นฉบับในการดึงข้อมูล
            text = original_section
            logger.info("✅ ใช้เฉพาะส่วนต้นฉบับของใบกำกับภาษีในการดึงข้อมูล")
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text)
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)  # ส่ง filename ไปด้วย
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, None_vat_, WHT_)
        new_filename = filename
        if new_filename:
            new_filename = re.sub(r'(VAT_|None_vat_|WHT_)', '', new_filename, flags=re.IGNORECASE)
        
        # แยกที่อยู่เป็นส่วนๆ สำหรับ Eastern Sea Lamchabang Terminal
        # ที่อยู่: อาคารท่าเทียบเรือพาณิชย์แหลมฉบัง ท่าเทียบเรือตู้สินค้า หมายเลข 3 ถนนสุขุมวิท ตำบลทุ่งสุขลา อำเภอศรีราชา จังหวัดชลบุรี 20230
        # เลขที่ = 3, อื่นๆ = อาคารท่าเทียบเรือพาณิชย์แหลมฉบัง ท่าเทียบเรือตู้สินค้า, จังหวัด = ชลบุรี
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
            # ดึงเลขที่จาก "หมายเลข 3" (ดึงแค่เลข 3)
            # Pattern: "หมายเลข 3" -> "3"
            building_match = re.search(r'หมายเลข\s+(\d+)', address)
            if building_match:
                building_number = building_match.group(1).strip()
            
            # ดึงอื่นๆ = "อาคารท่าเทียบเรือพาณิชย์แหลมฉบัง ท่าเทียบเรือตู้สินค้า"
            # หาส่วนที่อยู่ก่อน "หมายเลข" (ดึงทุกอย่างก่อน "หมายเลข")
            # Pattern: "อาคาร... หมายเลข" -> "อาคาร..."
            other_match = re.search(r'^(.+?)(?=\s*หมายเลข)', address)
            if other_match:
                other_info = other_match.group(1).strip()
            
            # ดึงถนนจาก "ถนนสุขุมวิท"
            # Pattern: "ถนนสุขุมวิท" -> "ถนนสุขุมวิท"
            road_match = re.search(r'(ถนน[ก-๙A-Za-z]+?)(?:\s+ตำบล|\s+อำเภอ|\s+จังหวัด|\s+\d{5}|$)', address)
            if road_match:
                road = road_match.group(1).strip()
            
            # ดึงตำบลจาก "ตำบลทุ่งสุขลา"
            # Pattern: "ตำบลทุ่งสุขลา" -> "ทุ่งสุขลา"
            subdistrict_match = re.search(r'ตำบล\s*([ก-๙A-Za-z]+?)(?:\s+อำเภอ|\s+จังหวัด|\s+\d{5}|$)', address)
            if subdistrict_match:
                subdistrict = subdistrict_match.group(1).strip()
            
            # ดึงอำเภอจาก "อำเภอศรีราชา"
            # Pattern: "อำเภอศรีราชา" -> "ศรีราชา"
            district_match = re.search(r'อำเภอ\s*([ก-๙A-Za-z]+?)(?:\s+จังหวัด|\s+\d{5}|$)', address)
            if district_match:
                district = district_match.group(1).strip()
            
            # ดึงจังหวัดจาก "จังหวัดชลบุรี"
            # Pattern: "จังหวัดชลบุรี" -> "ชลบุรี"
            province_match = re.search(r'จังหวัด\s*(ชลบุรี)', address)
            if province_match:
                province = province_match.group(1).strip()
            
            # ดึงรหัสไปรษณีย์ (5 หลัก) - หาเลข 5 หลักที่อยู่ท้ายสุด
            # Pattern: "20230" -> "20230"
            postal_match = re.search(r'(\d{5})\s*$', address)
            if postal_match:
                postal_code = postal_match.group(1).strip()
        
        return {
            'success': True,
            'company': 'EASTERN_SEA_LAMCHABANG_TERMINAL',
            'company_name': company_name,
            'tax_id': tax_id,
            'date': date,
            'document_number': document_number,  # เลขที่เอกสาร
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number,  # เลขที่ (3)
            'other_info': other_info,  # อื่นๆ (อาคารท่าเทียบเรือพาณิชย์แหลมฉบัง ท่าเทียบเรือตู้สินค้า)
            'soi': soi,  # ซอย/ตรอก
            'road': road,  # ถนน
            'subdistrict': subdistrict,  # ตำบล
            'district': district,  # อำเภอ
            'province': province,  # จังหวัด (ชลบุรี)
            'postal_code': postal_code,  # รหัสไปรษณีย์
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
