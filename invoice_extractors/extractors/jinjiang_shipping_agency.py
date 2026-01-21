"""
Jinjiang Shipping Agency Invoice Extractor
===========================================
Extractor สำหรับดึงข้อมูลจาก JINJIANG SHIPPING AGENCY (THAILAND) CO., LTD.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class JinjiangShippingAgencyExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก JINJIANG SHIPPING AGENCY (THAILAND) CO., LTD."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "JINJIANG SHIPPING AGENCY",
        "JINJIANG SHIPPING",
        "Jinjiang Shipping"
    ]
    
    def __init__(self):
        """Initialize Jinjiang Shipping Agency Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Jinjiang Shipping Agency หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "JINJIANG SHIPPING AGENCY"
        2. Tax ID "0105565190389"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Jinjiang Shipping Agency (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier.upper() in text.upper() for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105565190389"
        has_tax_id = "0105565190389" in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "JINJIANG SHIPPING AGENCY (THAILAND) CO., LTD."
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษีจาก 'Tax ID: 0105565190389'"""
        # Pattern: Tax ID: 0105565190389
        patterns = [
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # ถ้าไม่พบ pattern ให้ตรวจสอบว่า Tax ID อยู่ใน text หรือไม่
        if "0105565190389" in text:
            return "0105565190389"
        
        return None
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา (ถ้ามี)"""
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่จาก 'DATE : 03-Nov-25' และแปลงเป็น d/m/yyyy (เช่น 3/11/2025)"""
        # Pattern: DATE : 03-Nov-25
        patterns = [
            r'DATE\s*[:.]?\s*(\d{1,2})-([A-Za-z]{3})-(\d{2,4})',
            r'Date\s*[:.]?\s*(\d{1,2})-([A-Za-z]{3})-(\d{2,4})',
        ]
        
        month_map = {
            'JAN': '1', 'FEB': '2', 'MAR': '3', 'APR': '4',
            'MAY': '5', 'JUN': '6', 'JUL': '7', 'AUG': '8',
            'SEP': '9', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).lstrip('0') or '0'  # ตัด 0 นำหน้า (3 ไม่ใช่ 03)
                month_abbr = match.group(2).upper()
                year_str = match.group(3)
                
                # แปลงเดือน
                month = month_map.get(month_abbr, '1')
                
                # แปลงปี (25 -> 2025, 2025 -> 2025)
                if len(year_str) == 2:
                    # สมมติว่า 25 = 2025 (สามารถปรับได้ถ้าต้องการ)
                    year = '20' + year_str
                else:
                    year = year_str
                
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขใบกำกับภาษีจาก 'NO. : JJT-TX25110085'"""
        # Pattern: NO. : JJT-TX25110085
        patterns = [
            r'NO[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
            r'No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
            r'Invoice\s+No[.:]?\s*[:.]?\s*([A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_no = match.group(1).strip()
                # ตรวจสอบว่าเป็นรูปแบบ JJT-TX... หรือไม่ (หรือรูปแบบอื่นๆ)
                if doc_no:
                    return doc_no
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: Lumpini Tower, 37th floor, No.1168/110, Rama 4 Road, Tungmahamek, Sathorn, Bangkok 10120 Thailand.
        
        Returns:
            ที่อยู่รวม (string)
        """
        # หาที่อยู่จาก text (มักจะอยู่หลังชื่อบริษัทหรือ Tax ID)
        lines = text.split('\n')
        address_lines = []
        collecting = False
        
        # หาตำแหน่งที่เริ่มต้นที่อยู่
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # หา "Lumpini Tower" หรือ "Rama 4 Road" หรือ "Bangkok 10120"
            if any(keyword in line_clean for keyword in ['Lumpini Tower', 'Rama 4 Road', 'Bangkok 10120', 'Sathorn', 'Tungmahamek']):
                # ลบ "Thailand." หรือข้อมูลอื่นๆ ที่ไม่จำเป็น
                line_clean = re.sub(r'\s*Thailand[.,]?\s*$', '', line_clean, flags=re.IGNORECASE)
                address_lines.append(line_clean)
                break
            
            # ถ้ามี keyword ที่เกี่ยวข้อง
            if any(keyword in line_clean for keyword in ['Tower', 'Road', 'Bangkok', 'floor']):
                # ตรวจสอบว่ามีรูปแบบที่อยู่ (มี comma, number, road)
                if ',' in line_clean or re.search(r'\d{5}', line_clean):
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
        return "Lumpini Tower, 37th floor, No.1168/110, Rama 4 Road, Tungmahamek, Sathorn, Bangkok 10120"
    
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
    
    def _extract_from_html_table(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลจากตาราง HTML โดยค้นหา AMOUNT (THB), VALUE ADDED TAX 7%, และ TOTAL
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            Dictionary ที่มีข้อมูลที่ดึงได้
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        try:
            # หาตาราง HTML ทั้งหมด
            table_pattern = r'<table[^>]*>(.*?)</table>'
            tables = re.findall(table_pattern, text, re.DOTALL | re.IGNORECASE)
            
            if not tables:
                return result
            
            # วนลูปทุกตาราง
            for table_html in tables:
                # แยก rows
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
                
                # วนลูปทุกแถวเพื่อหาข้อมูล
                for row in rows:
                    # แยก cells
                    cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
                    
                    if not cells:
                        continue
                    
                    # ทำความสะอาด cell content
                    cleaned_cells = []
                    for cell in cells:
                        # ลบ HTML tags
                        cell_text = re.sub(r'<[^>]+>', '', cell)
                        # ลบช่องว่างส่วนเกิน
                        cell_text = re.sub(r'\s+', ' ', cell_text).strip()
                        cleaned_cells.append(cell_text)
                    
                    if len(cleaned_cells) < 2:
                        continue
                    
                    # ตรวจสอบว่าเป็นแถวที่ต้องการ
                    row_text = ' '.join(cleaned_cells)
                    row_upper = row_text.upper()
                    
                    # หา AMOUNT (THB)
                    if 'AMOUNT' in row_upper and '(THB)' in row_text and not result['amount_before_vat']:
                        # หาตัวเลขใน cell สุดท้าย
                        last_cell = cleaned_cells[-1].strip()
                        amount_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_cell)
                        if amount_match:
                            try:
                                result['amount_before_vat'] = float(amount_match.group(1).replace(',', ''))
                            except ValueError:
                                pass
                    
                    # หา VALUE ADDED TAX 7%
                    if 'VALUE ADDED TAX' in row_upper and '7%' in row_text and not result['vat_amount']:
                        # หาตัวเลขใน cell สุดท้าย
                        last_cell = cleaned_cells[-1].strip()
                        vat_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_cell)
                        if vat_match:
                            try:
                                result['vat_amount'] = float(vat_match.group(1).replace(',', ''))
                            except ValueError:
                                pass
                    
                    # หา TOTAL
                    if 'TOTAL' in row_upper and not result['total_amount']:
                        # ตรวจสอบว่ามี TOTAL เป็น cell แยกต่างหาก
                        has_total = False
                        total_cell_index = -1
                        for idx, cell in enumerate(cleaned_cells):
                            cell_upper = cell.strip().upper()
                            if cell_upper == 'TOTAL' or (cell_upper.startswith('TOTAL') and len(cell.strip()) <= 10):
                                has_total = True
                                total_cell_index = idx
                                break
                        
                        if has_total:
                            # หาตัวเลขใน cell สุดท้าย (อาจเป็นคอลัมน์สุดท้ายที่เป็น TOTAL column)
                            last_cell = cleaned_cells[-1].strip()
                            total_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_cell)
                            if total_match:
                                try:
                                    result['total_amount'] = float(total_match.group(1).replace(',', ''))
                                except ValueError:
                                    pass
                            # ถ้ายังไม่ได้ ลองหาจาก cell ที่อยู่หลัง TOTAL
                            elif total_cell_index >= 0 and total_cell_index + 1 < len(cleaned_cells):
                                next_cell = cleaned_cells[total_cell_index + 1].strip()
                                total_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', next_cell)
                                if total_match:
                                    try:
                                        result['total_amount'] = float(total_match.group(1).replace(',', ''))
                                    except ValueError:
                                        pass
                
                # ถ้าได้ข้อมูลครบแล้ว ให้ return
                if result['amount_before_vat'] and result['vat_amount'] and result['total_amount']:
                    logger.info(f"✅ ดึงยอดเงินจากตาราง HTML สำเร็จ: amount_before_vat={result['amount_before_vat']}, vat_amount={result['vat_amount']}, total_amount={result['total_amount']}")
                    return result
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงข้อมูลจากตาราง HTML: {e}")
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลยอดเงิน
        
        - ยอดก่อนภาษีมูลค่าเพิ่ม: AMOUNT (THB) | 1,800.00
        - ภาษีมูลค่าเพิ่ม: VALUE ADDED TAX 7% | 126.00
        - ยอดหลังบวกภาษีมูลค่าเพิ่ม: TOTAL | 1,926.00
        
        รูปแบบในเอกสารจริง:
        - ผิด ตก ยกเว้น / E & O.E. | ผิด ตก ยกเว้น / E & O.E. | AMOUNT (THB) | 1,800.00
        - หมายเหตุ | หมายเหตุ | VALUE ADDED TAX 7% | 126.00
        - 03/11/25 | 11:02:04 | TOTAL | 1,926.00
        """
        amounts = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # วิธีที่ 0: ลองดึงจาก HTML table ก่อน (ถ้าหน้าเว็บอ่านได้)
        html_table_result = self._extract_from_html_table(text)
        if html_table_result.get('amount_before_vat') or html_table_result.get('vat_amount') or html_table_result.get('total_amount'):
            amounts.update(html_table_result)
            # ถ้าได้ข้อมูลครบแล้ว ให้ return
            if amounts['amount_before_vat'] and amounts['vat_amount'] and amounts['total_amount']:
                return amounts
        
        # วิธีที่ 1: แยกแต่ละบรรทัดและตรวจสอบแบบง่ายๆ
        lines = text.split('\n')
        for line in lines:
            line_clean = line.strip()
            if '|' not in line_clean:
                continue
            
            # แยกคอลัมน์ด้วย |
            parts = [p.strip() for p in line_clean.split('|')]
            
            if len(parts) < 2:
                continue
            
            # ตรวจสอบทุกคอลัมน์และหาค่าจากคอลัมน์สุดท้าย
            line_upper = line_clean.upper()
            
            # หา AMOUNT (THB)
            if 'AMOUNT' in line_upper and '(THB)' in line_upper and not amounts['amount_before_vat']:
                # หาตัวเลขในคอลัมน์สุดท้าย
                last_col = parts[-1].strip()
                amount_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_col)
                if amount_match:
                    try:
                        amounts['amount_before_vat'] = float(amount_match.group(1).replace(',', ''))
                    except ValueError:
                        pass
            
            # หา VALUE ADDED TAX 7%
            if 'VALUE ADDED TAX' in line_upper and '7%' in line_clean and not amounts['vat_amount']:
                # หาตัวเลขในคอลัมน์สุดท้าย
                last_col = parts[-1].strip()
                vat_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_col)
                if vat_match:
                    try:
                        amounts['vat_amount'] = float(vat_match.group(1).replace(',', ''))
                    except ValueError:
                        pass
            
            # หา TOTAL
            if 'TOTAL' in line_upper and not amounts['total_amount']:
                # ตรวจสอบว่ามี TOTAL เป็นคอลัมน์แยกต่างหาก
                has_total = False
                for part in parts:
                    if part.strip().upper() == 'TOTAL':
                        has_total = True
                        break
                
                if has_total:
                    # หาตัวเลขในคอลัมน์สุดท้าย
                    last_col = parts[-1].strip()
                    total_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d{2})', last_col)
                    if total_match:
                        try:
                            amounts['total_amount'] = float(total_match.group(1).replace(',', ''))
                        except ValueError:
                            pass
        
        # ถ้ายังไม่ได้ข้อมูล ให้ลองหาแบบ regex patterns (backup method)
        # รูปแบบจริง: ผิด ตก ยกเว้น / E & O.E. | ผิด ตก ยกเว้น / E & O.E. | AMOUNT (THB) | 1,800.00
        if not amounts['amount_before_vat']:
            # Pattern: ... | AMOUNT (THB) | 1,800.00
            patterns_amount = [
                r'\|\s*AMOUNT\s*\(THB\)\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # | AMOUNT (THB) | 1,800.00
                r'AMOUNT\s*\(THB\)\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # AMOUNT (THB) | 1,800.00
                r'AMOUNT\s*\(THB\)[^|]*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # AMOUNT (THB) ... | 1,800.00
            ]
            for pattern in patterns_amount:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    try:
                        amounts['amount_before_vat'] = float(match.group(1).replace(',', ''))
                        break
                    except ValueError:
                        pass
        
        if not amounts['vat_amount']:
            # Pattern: ... | VALUE ADDED TAX 7% | 126.00
            patterns_vat = [
                r'\|\s*VALUE\s+ADDED\s+TAX\s+7%\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # | VALUE ADDED TAX 7% | 126.00
                r'VALUE\s+ADDED\s+TAX\s+7%\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # VALUE ADDED TAX 7% | 126.00
                r'VALUE\s+ADDED\s+TAX\s+7%[^|]*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # VALUE ADDED TAX 7% ... | 126.00
            ]
            for pattern in patterns_vat:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    try:
                        amounts['vat_amount'] = float(match.group(1).replace(',', ''))
                        break
                    except ValueError:
                        pass
        
        if not amounts['total_amount']:
            # Pattern: ... | TOTAL | 1,926.00 (รองรับคอลัมน์ว่าง)
            # รูปแบบจริง: 03/11/25 | 11:02:04 | TOTAL | 1,926.00
            patterns_total = [
                r'\|\s*TOTAL\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # | TOTAL | 1,926.00
                r'\|\s*\|\s*TOTAL\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # |  | TOTAL | 1,926.00
                r'TOTAL\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # TOTAL | 1,926.00
                r'[^|]*\|\s*TOTAL\s*\|\s*(\d{1,3}(?:,\d{3})*\.?\d{2})',  # ... | TOTAL | 1,926.00
            ]
            for pattern in patterns_total:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    try:
                        amounts['total_amount'] = float(match.group(1).replace(',', ''))
                        break
                    except ValueError:
                        pass
        
        return amounts
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (ถ้ามี)"""
        remark_parts = []
        
        # เพิ่มชื่อไฟล์ (ตัด VAT_, WHT_, None_vat_ ออก)
        if filename:
            filename_clean = filename
            filename_clean = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename_clean, flags=re.IGNORECASE)
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
        # ที่อยู่: Lumpini Tower, 37th floor, No.1168/110, Rama 4 Road, Tungmahamek, Sathorn, Bangkok 10120 Thailand.
        address_full = address or ''
        building_number = ''  # 1168/110
        other_info = ''  # Lumpini Tower, 37th floor
        soi = ''  # ซอย/ตรอก
        road = ''  # Rama 4 Road
        subdistrict = ''  # แขวง (Tungmahamek)
        district = ''  # ตำบล (Sathorn)
        province = ''  # จังหวัด (Bangkok)
        postal_code = ''  # รหัสไปรษณีย์ (10120)
        
        if address:
            # ดึงเลขที่จาก "No.1168/110" หรือ "1168/110"
            # Pattern: No.1168/110 หรือ 1168/110
            building_match = re.search(r'(?:No\.?\s*)?(\d+(?:/\d+)?)', address, re.IGNORECASE)
            if building_match:
                building_number = building_match.group(1).strip()
            
            # ดึงอื่นๆ จาก "Lumpini Tower, 37th floor"
            # หาส่วนก่อน "No.1168/110" หรือ ", No.1168/110"
            # ที่อยู่: "Lumpini Tower, 37th floor, No.1168/110, ..."
            # ต้องการ: "Lumpini Tower, 37th floor"
            other_match = re.search(r'^(.+?)(?=\s*,?\s*(?:No\.?\s*)?\d+(?:/\d+)?)', address)
            if other_match:
                other_info = other_match.group(1).strip()
                # ลบ comma ที่ท้าย
                other_info = re.sub(r',\s*$', '', other_info).strip()
            
            # ถ้ายังไม่มี other_info ลองหาจาก "Lumpini Tower" และ "37th floor"
            if not other_info:
                tower_match = re.search(r'(Lumpini Tower[^,]*?37th floor)', address, re.IGNORECASE)
                if tower_match:
                    other_info = tower_match.group(1).strip()
            
            # ดึงถนนจาก "Rama 4 Road"
            road_match = re.search(r'([A-Za-z0-9\s]+Road)', address, re.IGNORECASE)
            if road_match:
                road = road_match.group(1).strip()
            
            # ดึงแขวงจาก "Tungmahamek" (ค้นหาโดยตรง)
            tungmahamek_match = re.search(r'\b(Tungmahamek)\b', address, re.IGNORECASE)
            if tungmahamek_match:
                subdistrict = tungmahamek_match.group(1).strip()
            
            # ดึงตำบลจาก "Sathorn" (ค้นหาโดยตรง)
            sathorn_match = re.search(r'\b(Sathorn)\b', address, re.IGNORECASE)
            if sathorn_match:
                district = sathorn_match.group(1).strip()
            
            # ดึงจังหวัดจาก "Bangkok"
            province_match = re.search(r'Bangkok', address, re.IGNORECASE)
            if province_match:
                province = 'Bangkok'
            
            # ดึงรหัสไปรษณีย์ (5 หลัก) จาก "10120"
            postal_match = re.search(r'\b(\d{5})\b', address)
            if postal_match:
                postal_code = postal_match.group(1).strip()
        
        return {
            'success': True,
            'company': 'JINJIANG_SHIPPING_AGENCY',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number or '',  # เลขที่ (1168/110)
            'other_info': other_info or '',  # อื่นๆ (Lumpini Tower, 37th floor)
            'soi': soi or '',  # ซอย/ตรอก
            'road': road or '',  # ถนน (Rama 4 Road)
            'subdistrict': subdistrict or '',  # แขวง (Tungmahamek)
            'district': district or '',  # ตำบล (Sathorn)
            'province': province or '',  # จังหวัด (Bangkok)
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
