"""
CMA CGM Asia Shipping Invoice Extractor
========================================
Extractor สำหรับดึงข้อมูลจาก CMA CGM Asia Shipping Pte Ltd C/O CMA CGM (Thailand) Ltd.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class CMACGMAsiaShippingExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก CMA CGM Asia Shipping Pte Ltd C/O CMA CGM (Thailand) Ltd."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "CMA CGM Asia Shipping Pte Ltd C/O CMA CGM (Thailand) Ltd.",
        "CMA CGM Asia Shipping",
        "CMA CGM (Thailand) Ltd.",
        "CMA CGM"
    ]
    
    # Tax ID
    TAX_ID = "0993000377133"
    
    def __init__(self):
        """Initialize CMA CGM Asia Shipping Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ CMA CGM Asia Shipping Pte Ltd C/O CMA CGM (Thailand) Ltd. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "CMA CGM Asia Shipping Pte Ltd C/O CMA CGM (Thailand) Ltd."
        2. Tax ID "0993000377133"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร CMA CGM Asia Shipping (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier.upper() in text.upper() for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0993000377133"
        has_tax_id = self.TAX_ID in text or "TAX ID:" + self.TAX_ID in text
        
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
        return "CMA CGM Asia Shipping Pte Ltd C/O CMA CGM (Thailand) Ltd."
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TAX ID : 0993000377133
        patterns = [
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID : 0993000377133
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID : 0993000377133
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0993000377133
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี 0993000377133
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
        # Pattern: Branch 1
        patterns = [
            r'Branch\s+(\d+)',  # Branch 1
            r'สาขา\s*[:.]?\s*(\d+)',  # สาขา: 1
            r'Branch\s*[:.]?\s*(\d+)',  # Branch: 1
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                branch = match.group(1).strip()
                # เติม 0 นำหน้าให้เป็น 5 หลัก
                branch = branch.zfill(5)
                logger.info(f"✅ พบสาขา: {branch}")
                return branch
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: Date : 05-Nov-2025
        patterns = [
            r'Date\s*[:.]?\s*(\d{1,2})-([A-Za-z]{3})-(\d{2,4})',  # Date : 05-Nov-2025
            r'วันที่\s*Date\s*[:.]?\s*(\d{1,2})-([A-Za-z]{3})-(\d{2,4})',  # วันที่ Date : 05-Nov-2025
        ]
        
        month_map = {
            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
            'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month_abbr = match.group(2).upper()
                year_str = match.group(3)
                
                month = month_map.get(month_abbr, '01')
                
                # แปลงปี
                if len(year_str) == 2:
                    year = '20' + year_str
                else:
                    year = year_str
                
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: Doc No. : CNCI25051447
        patterns = [
            r'Doc\s+No\.\s*[:.]?\s*([A-Z0-9]+)',  # Doc No. : CNCI25051447
            r'DOC\s+NO\.\s*[:.]?\s*([A-Z0-9]+)',  # DOC NO. : CNCI25051447
            r'Document\s+No\.\s*[:.]?\s*([A-Z0-9]+)',  # Document No. : CNCI25051447
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: CNCI25051447
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_number = match.group(1).strip()
                # ตรวจสอบว่าไม่ใช่ตัวเลขล้วนๆ
                if re.match(r'^\d+$', doc_number):
                    continue
                logger.info(f"✅ พบเลขที่เอกสาร: {doc_number}")
                return doc_number
        
        return None
    
    def _extract_bl_no_from_html_table(self, text: str) -> Optional[str]:
        """
        ดึง B/L No. จากตาราง HTML
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            B/L No. หรือ None
        """
        try:
            # หาตาราง HTML ทั้งหมด
            table_pattern = r'<table[^>]*>(.*?)</table>'
            tables = re.findall(table_pattern, text, re.DOTALL | re.IGNORECASE)
            
            if not tables:
                return None
            
            # วนลูปทุกตาราง
            for table_html in tables:
                # แยก rows
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
                
                # หา header row ที่มี B/L No.
                bl_index = -1
                header_row_index = -1
                
                for i, row in enumerate(rows):
                    # แยก cells
                    cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
                    
                    if not cells:
                        continue
                    
                    # ทำความสะอาด cell content
                    cleaned_cells = []
                    for cell in cells:
                        cell_text = re.sub(r'<[^>]+>', '', cell)
                        cell_text = re.sub(r'\s+', ' ', cell_text).strip()
                        cleaned_cells.append(cell_text)
                    
                    # ตรวจสอบว่าเป็น header row ที่มี B/L No.
                    row_text = ' '.join(cleaned_cells).upper()
                    if 'B/L' in row_text and 'NO' in row_text:
                        # หา column index ของ B/L No.
                        for idx, cell in enumerate(cleaned_cells):
                            cell_upper = cell.upper()
                            if 'B/L' in cell_upper and 'NO' in cell_upper:
                                bl_index = idx
                                header_row_index = i
                                logger.debug(f"✅ พบ B/L No. column ที่ index: {bl_index} ใน row: {header_row_index}")
                                break
                        
                        if bl_index >= 0:
                            break
                
                # ถ้าพบ header row ที่มี B/L No.
                if bl_index >= 0 and header_row_index >= 0:
                    # หา data row (บรรทัดถัดไปหลังจาก header)
                    for i in range(header_row_index + 1, len(rows)):
                        row = rows[i]
                        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
                        
                        if not cells:
                            continue
                        
                        # ทำความสะอาด cell content
                        cleaned_cells = []
                        for cell in cells:
                            cell_text = re.sub(r'<[^>]+>', '', cell)
                            cell_text = re.sub(r'\s+', ' ', cell_text).strip()
                            cleaned_cells.append(cell_text)
                        
                        # ตรวจสอบว่าบรรทัดนี้ไม่ใช่ header ซ้ำ
                        row_text = ' '.join(cleaned_cells).upper()
                        if any(keyword in row_text for keyword in ['INVOICE NO.', 'DESCRIPTION', 'AMOUNT', 'B/L NO.']):
                            continue
                        
                        # ดึง B/L No. จาก column ที่ตรงกัน
                        if bl_index < len(cleaned_cells):
                            bl_no = cleaned_cells[bl_index].strip()
                            # ตรวจสอบว่ามีข้อมูลและไม่ใช่คำว่า "B/L No." หรือ header อื่นๆ
                            if bl_no and len(bl_no) > 3 and bl_no.upper() not in ['B/L NO.', 'B/L NO', 'B/L', 'NO.']:
                                # ตรวจสอบว่าเป็นรูปแบบ B/L No. ที่ถูกต้อง (มีตัวอักษรและตัวเลข)
                                if re.match(r'^[A-Z0-9]{4,}$', bl_no):
                                    logger.info(f"✅ พบ B/L No. จากตาราง HTML: {bl_no}")
                                    return bl_no
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึง B/L No. จากตาราง HTML: {e}")
        
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง (B/L No. จากตาราง และชื่อไฟล์เก่า)"""
        reference_parts = []
        
        # วิธีที่ 1: ลองดึง B/L No. จาก HTML table structure ก่อน
        bl_no = self._extract_bl_no_from_html_table(text)
        
        if bl_no:
            reference_parts.append(f"B/L No. {bl_no}")
            logger.info(f"✅ พบ B/L No. จาก HTML table: {bl_no}")
        
        # วิธีที่ 2: ถ้ายังไม่พบ ให้ลองอ่านจาก text ธรรมดา
        if not bl_no:
            # หาบรรทัดที่มี B/L No. ใน header
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                line_upper = line.upper()
                line_stripped = line.strip()
                
                # ตรวจสอบว่าบรรทัดนี้มี "B/L NO." หรือ "B/L No." และมี |
                if ('B/L NO.' in line_upper or 'B/L NO' in line_upper) and '|' in line:
                    logger.debug(f"🔍 พบบรรทัด header ที่มี B/L No.: {line_stripped}")
                    
                    # หา column index ของ B/L No. ใน header
                    header_parts = [p.strip() for p in line.split('|')]
                    bl_index = -1
                    
                    for idx, part in enumerate(header_parts):
                        part_upper = part.upper()
                        if ('B/L' in part_upper and 'NO' in part_upper) or part_upper == 'B/L NO.':
                            bl_index = idx
                            logger.debug(f"✅ พบ B/L No. column ที่ index: {bl_index}")
                            break
                    
                    # หาบรรทัดถัดไปที่มีข้อมูล (อาจจะต้องข้ามบรรทัดว่าง)
                    for j in range(i + 1, min(i + 5, len(lines))):  # ตรวจสอบ 4 บรรทัดถัดไป
                        next_line = lines[j].strip()
                        if not next_line or not '|' in next_line:
                            continue
                        
                        # แยกด้วย |
                        parts = [p.strip() for p in next_line.split('|')]
                        
                        # ตรวจสอบว่าบรรทัดนี้มีข้อมูล (ไม่ใช่ header ซ้ำ)
                        if len(parts) < 2:
                            continue
                        
                        # ตรวจสอบว่าบรรทัดนี้ไม่ใช่ header (ไม่มีคำว่า "Invoice", "Description", "Amount")
                        if any(keyword in next_line.upper() for keyword in ['INVOICE NO.', 'DESCRIPTION', 'AMOUNT']):
                            continue
                        
                        # ดึง B/L No. จาก column ที่ตรงกัน
                        if bl_index >= 0 and bl_index < len(parts):
                            bl_no = parts[bl_index].strip()
                            # ตรวจสอบว่ามีข้อมูลและไม่ใช่คำว่า "B/L No." หรือ header อื่นๆ
                            if bl_no and len(bl_no) > 3 and bl_no.upper() not in ['B/L NO.', 'B/L NO', 'B/L', 'NO.']:
                                # ตรวจสอบว่าเป็นรูปแบบ B/L No. ที่ถูกต้อง (มีตัวอักษรและตัวเลข)
                                if re.match(r'^[A-Z0-9]{4,}$', bl_no):
                                    reference_parts.append(f"B/L No. {bl_no}")
                                    logger.info(f"✅ พบ B/L No. จากตาราง: {bl_no}")
                                    break
                    
                    if bl_no:
                        break
        
        # วิธีที่ 3: ถ้ายังไม่พบ ลองใช้ pattern โดยตรง
        if not bl_no:
            # Pattern 1: หาจากรูปแบบตาราง: Invoice No. | B/L No. | Description | Amount
            #            THCIA353037 | CNA0303659 | FREIGHT/THC/OTHER INTERNATIONAL CHARGES | 7,078.26
            # หาบรรทัดที่มี "Invoice No." และ "B/L No." ในบรรทัดเดียวกัน
            table_match = re.search(
                r'Invoice\s+No\.\s*\|\s*B/L\s+No\.\s*\|\s*Description.*?\n\s*([A-Z0-9]+)\s*\|\s*([A-Z0-9]+)\s*\|',
                text,
                re.IGNORECASE | re.MULTILINE
            )
            if table_match:
                # group(1) = Invoice No., group(2) = B/L No.
                potential_bl = table_match.group(2).strip()
                if potential_bl and len(potential_bl) > 3:
                    bl_no = potential_bl
                    reference_parts.append(f"B/L No. {bl_no}")
                    logger.info(f"✅ พบ B/L No. จากตาราง (pattern): {bl_no}")
            
            # Pattern 2: หาจากรูปแบบ | CNA0303659 | (มี | ก่อนและหลัง และอยู่ระหว่าง Invoice No. กับ Description)
            if not bl_no:
                # หาบรรทัดที่มี Invoice No. และ Description
                invoice_desc_match = re.search(
                    r'Invoice\s+No\.\s*\|\s*B/L\s+No\.\s*\|\s*Description',
                    text,
                    re.IGNORECASE
                )
                if invoice_desc_match:
                    # หาบรรทัดถัดไปที่มีข้อมูล
                    start_pos = invoice_desc_match.end()
                    next_line_match = re.search(
                        r'([A-Z0-9]+)\s*\|\s*([A-Z0-9]{4,})\s*\|\s*[A-Z/]',
                        text[start_pos:start_pos+200],
                        re.IGNORECASE
                    )
                    if next_line_match:
                        potential_bl = next_line_match.group(2).strip()
                        if potential_bl and len(potential_bl) > 3:
                            bl_no = potential_bl
                            reference_parts.append(f"B/L No. จากตาราง (pattern 2): {bl_no}")
                            logger.info(f"✅ พบ B/L No. จากตาราง (pattern 2): {bl_no}")
            
            # Pattern 3: หาจากรูปแบบ | CNA0303659 | (มี | ก่อนและหลัง)
            if not bl_no:
                bl_match = re.search(r'\|\s*([A-Z]\d{9})\s*\|', text)
                if bl_match:
                    potential_bl = bl_match.group(1).strip()
                    # ตรวจสอบว่าไม่ใช่คำว่า "INVOICE", "DESCRIPTION", "AMOUNT"
                    if potential_bl.upper() not in ['INVOICE', 'DESCRIPTION', 'AMOUNT', 'THCIA353037']:
                        bl_no = potential_bl
                        reference_parts.append(f"B/L No. {bl_no}")
                        logger.info(f"✅ พบ B/L No. จาก pattern: {bl_no}")
            
            # Pattern 4: หาจากรูปแบบที่มี B/L No. ในบรรทัดเดียวกัน
            if not bl_no:
                bl_patterns = [
                    r'B/L\s+No\.\s*\|\s*([A-Z0-9]{4,})',  # B/L No. | CNA0303659
                    r'B\/L\s+No\.\s*\|\s*([A-Z0-9]{4,})',  # B/L No. | CNA0303659
                ]
                
                for pattern in bl_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        potential_bl = match.group(1).strip()
                        if potential_bl.upper() not in ['INVOICE', 'DESCRIPTION', 'AMOUNT']:
                            bl_no = potential_bl
                            reference_parts.append(f"B/L No. {bl_no}")
                            logger.info(f"✅ พบ B/L No. จาก pattern: {bl_no}")
                            break
        
        # ดึงชื่อไฟล์เก่า (ตัด VAT_, WHT_, None_vat_ และไม่เอา EXC_ กับข้อมูลที่อยู่ด้านหลัง และไม่เอา .pdf)
        if filename:
            # ลบ VAT_, WHT_, None_vat_ ออกจากชื่อไฟล์
            cleaned = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename, flags=re.IGNORECASE)
            
            # ตัด EXC_ และข้อมูลที่อยู่ด้านหลังออก
            cleaned = re.sub(r'EXC_[^\s.]*', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'EXC-[^\s.]*', '', cleaned, flags=re.IGNORECASE)
            
            # ลบ .pdf
            cleaned = re.sub(r'\.pdf$', '', cleaned, flags=re.IGNORECASE)
            
            # ลบช่องว่างที่เหลือ
            cleaned = cleaned.strip()
            
            if cleaned and cleaned not in reference_parts:
                reference_parts.append(cleaned)
        
        # รวมอ้างอิง
        if reference_parts:
            return ' '.join(reference_parts)
        
        return None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # กำหนดชื่อบัญชีเป็น "ค่าใช้จ่ายในการขนส่ง" (ค่าคงที่)
        return {
            'account_name': 'ค่าใช้จ่ายในการขนส่ง',
            'account_code': None
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงยอดเงิน"""
        # Pattern: Sub total (before VAT) 7,078.26
        # Pattern: Grand Total 7,078.26
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        
        amount_before_vat = None
        vat_amount = 0.00  # ไม่มีภาษีมูลค่าเพิ่ม
        total_amount = None
        
        # ดึงยอดก่อนภาษี: Sub total (before VAT) 7,078.26
        amount_patterns = [
            r'Sub\s+total\s*\(before\s+VAT\)\s*([\d,]+\.?\d{2})',  # Sub total (before VAT) 7,078.26
            r'Sub\s+Total\s*\(before\s+VAT\)\s*([\d,]+\.?\d{2})',  # Sub Total (before VAT) 7,078.26
            r'Subtotal\s*\(before\s+VAT\)\s*([\d,]+\.?\d{2})',  # Subtotal (before VAT) 7,078.26
            r'ยอดก่อนภาษี\s*[:.]?\s*([\d,]+\.?\d{2})',  # ยอดก่อนภาษี: 7,078.26
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    amount_before_vat = float(amount_str)
                    logger.info(f"✅ พบยอดก่อนภาษี: {amount_before_vat}")
                    break
                except ValueError:
                    continue
        
        # ดึงยอดรวม: Grand Total 7,078.26
        total_patterns = [
            r'Grand\s+Total\s*([\d,]+\.?\d{2})',  # Grand Total 7,078.26
            r'GRAND\s+TOTAL\s*([\d,]+\.?\d{2})',  # GRAND TOTAL 7,078.26
            r'TOTAL\s*[:.]?\s*([\d,]+\.?\d{2})',  # TOTAL: 7,078.26
            r'ยอดรวม\s*[:.]?\s*([\d,]+\.?\d{2})',  # ยอดรวม: 7,078.26
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    total_amount = float(amount_str)
                    logger.info(f"✅ พบยอดรวม: {total_amount}")
                    break
                except ValueError:
                    continue
        
        # ถ้าพบยอดรวมแต่ไม่พบยอดก่อนภาษี ให้ใช้ยอดรวมเป็นยอดก่อนภาษี
        if total_amount is not None and amount_before_vat is None:
            amount_before_vat = total_amount
            logger.info(f"✅ ใช้ยอดรวมเป็นยอดก่อนภาษี: {amount_before_vat}")
        
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        vat_amount = 0.00
        
        return {
            'amount_before_vat': amount_before_vat,
            'vat_amount': vat_amount,
            'total_amount': total_amount
        }
    
    def extract_address(self, text: str) -> str:
        """ดึงที่อยู่"""
        # กำหนดที่อยู่เป็นค่าคงที่
        return "No.53 Talay Thong Tower, Room No. 601-603, 6th Floor, 9, Thung Sukhla Sub-district, Si Racha District, Chonburi Province 20230"
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (REF. : R2554C101631RUD และชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_)"""
        remark_parts = []
        
        # ดึง REF. : R2554C101631RUD
        ref_patterns = [
            r'REF\.\s*[:.]?\s*([A-Z0-9]+)',  # REF. : R2554C101631RUD
            r'Ref\.\s*[:.]?\s*([A-Z0-9]+)',  # Ref. : R2554C101631RUD
            r'อ้างอิง\s*[:.]?\s*([A-Z0-9]+)',  # อ้างอิง: R2554C101631RUD
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ref_no = match.group(1).strip()
                if ref_no not in remark_parts:
                    remark_parts.append(ref_no)
                break
        
        # ดึงชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_
        if filename:
            # หาชื่อไฟล์ที่เริ่มต้นด้วย EXC_ หรือ EXC-
            exc_match = re.search(r'(EXC[_\-.][^\s.]*)', filename, re.IGNORECASE)
            if exc_match:
                exc_part = exc_match.group(1).strip()
                if exc_part not in remark_parts:
                    remark_parts.append(exc_part)
        
        # รวมหมายเหตุ
        if remark_parts:
            return ' '.join(remark_parts)
        
        return None
    
    def clean_filename(self, filename: str) -> str:
        """ทำความสะอาดชื่อไฟล์ (ลบ VAT_, WHT_, None_vat_)"""
        if not filename:
            return filename
        
        cleaned = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename, flags=re.IGNORECASE)
        return cleaned.strip()
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร"""
        # ไม่มีภาษีมูลค่าเพิ่ม (VAT = 0.00)
        return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร CMA CGM Asia Shipping
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร CMA CGM Asia Shipping หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร CMA CGM Asia Shipping Pte Ltd C/O CMA CGM (Thailand) Ltd.'
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
        
        # สร้างชื่อไฟล์ใหม่ (ตัด VAT_, None_vat_, WHT_)
        new_filename = self.clean_filename(filename) if filename else filename
        
        # แยกที่อยู่เป็นส่วนๆ
        address_full = address or ''
        building_number = 'No.53'
        other_info = 'Talay Thong Tower, Room No. 601-603, 6th Floor, 9'
        soi = ''
        road = ''
        subdistrict = 'Thung Sukhla Sub-district'
        district = 'Si Racha District'
        province = 'Chonburi'
        postal_code = '20230'
        
        # ตั้งค่า skip_amount_adjustment = True เพื่อไม่ให้ระบบปรับยอดเงิน (ใช้ค่าที่อ่านได้เท่านั้น)
        # เพราะเอกสารนี้ไม่มีภาษีมูลค่าเพิ่ม
        return {
            'success': True,
            'company': 'CMA_CGM_ASIA_SHIPPING',
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
            'amount_before_vat': amounts.get('amount_before_vat'),
            'vat_amount': amounts.get('vat_amount'),
            'total_amount': amounts.get('total_amount'),
            'withholding_tax_percent': withholding.get('withholding_tax_percent'),
            'withholding_tax_amount': withholding.get('withholding_tax_amount'),
            'remark': remark,
            'new_filename': new_filename,
            'old_filename': filename,  # เพิ่มชื่อไฟล์เก่า
            'document_type': document_type,
            'skip_amount_adjustment': True  # ไม่ให้ปรับยอดเงิน (ใช้ค่าที่อ่านได้เท่านั้น)
        }

