"""
Ocean Network Express Invoice Extractor
========================================
Extractor สำหรับดึงข้อมูลจาก OCEAN NETWORK EXPRESS (THAILAND) LTD.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class OceanNetworkExpressExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก OCEAN NETWORK EXPRESS (THAILAND) LTD."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "OCEAN NETWORK EXPRESS (THAILAND) LTD.",
        "OCEAN NETWORK EXPRESS",
        "ONE (THAILAND) LTD.",
        "ONE"
    ]
    
    # Tax ID
    TAX_ID = "0993000388267"
    
    def __init__(self):
        """Initialize Ocean Network Express Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ OCEAN NETWORK EXPRESS (THAILAND) LTD. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "OCEAN NETWORK EXPRESS (THAILAND) LTD."
        2. Tax ID "0993000388267"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Ocean Network Express (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier.upper() in text.upper() for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0993000388267"
        has_tax_id = self.TAX_ID in text or "TAX ID NO." + self.TAX_ID in text
        
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
        return "OCEAN NETWORK EXPRESS (THAILAND) LTD."
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TAX ID NO. 0993000388267 (HEAD OFFICE)
        patterns = [
            r'TAX\s+ID\s+NO\.\s*(\d{13})',  # TAX ID NO. 0993000388267
            r'Tax\s+ID\s+No\.\s*(\d{13})',  # Tax ID No. 0993000388267
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0993000388267
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี 0993000388267
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
        return None
    
    def _extract_date_from_html_table(self, text: str) -> Optional[str]:
        """
        ดึงวันที่จากตาราง HTML
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            วันที่ในรูปแบบ dd/mm/yyyy หรือ None
        """
        month_map = {
            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
            'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        
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
                
                # หา row ที่มี "Issue Date"
                for row in rows:
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
                    
                    # ตรวจสอบว่าเป็น row ที่มี "Issue Date"
                    row_text = ' '.join(cleaned_cells).upper()
                    if 'ISSUE DATE' in row_text:
                        # หา cell ที่มีวันที่ (รูปแบบ: 13Nov2025)
                        # อาจอยู่ใน cell เดียวกันหรือ cell ถัดไป
                        for i, cell in enumerate(cleaned_cells):
                            # ตรวจสอบว่า cell นี้มี "Issue Date"
                            if 'ISSUE DATE' in cell.upper():
                                # หาวันที่ใน cell นี้หรือ cell ถัดไป
                                date_match = re.search(r'(\d{1,2})([A-Za-z]{3})(\d{2,4})', cell, re.IGNORECASE)
                                if date_match:
                                    day = date_match.group(1).zfill(2)
                                    month_abbr = date_match.group(2).upper()
                                    year_str = date_match.group(3)
                                    
                                    month = month_map.get(month_abbr, '01')
                                    
                                    # แปลงปี
                                    if len(year_str) == 2:
                                        year = '20' + year_str
                                    else:
                                        year = year_str
                                    
                                    date_str = f"{day}/{month}/{year}"
                                    logger.info(f"✅ พบวันที่จากตาราง HTML: {date_str}")
                                    return date_str
                                
                                # ถ้าไม่พบใน cell นี้ ลองหาใน cell ถัดไป
                                if i + 1 < len(cleaned_cells):
                                    next_cell = cleaned_cells[i + 1]
                                    date_match = re.search(r'(\d{1,2})([A-Za-z]{3})(\d{2,4})', next_cell, re.IGNORECASE)
                                    if date_match:
                                        day = date_match.group(1).zfill(2)
                                        month_abbr = date_match.group(2).upper()
                                        year_str = date_match.group(3)
                                        
                                        month = month_map.get(month_abbr, '01')
                                        
                                        # แปลงปี
                                        if len(year_str) == 2:
                                            year = '20' + year_str
                                        else:
                                            year = year_str
                                        
                                        date_str = f"{day}/{month}/{year}"
                                        logger.info(f"✅ พบวันที่จากตาราง HTML (cell ถัดไป): {date_str}")
                                        return date_str
                            
                            # หรือหาวันที่ใน cell ใดๆ ที่มีรูปแบบวันที่
                            date_match = re.search(r'(\d{1,2})([A-Za-z]{3})(\d{2,4})', cell, re.IGNORECASE)
                            if date_match and 'ISSUE DATE' in row_text:
                                day = date_match.group(1).zfill(2)
                                month_abbr = date_match.group(2).upper()
                                year_str = date_match.group(3)
                                
                                month = month_map.get(month_abbr, '01')
                                
                                # แปลงปี
                                if len(year_str) == 2:
                                    year = '20' + year_str
                                else:
                                    year = year_str
                                
                                date_str = f"{day}/{month}/{year}"
                                logger.info(f"✅ พบวันที่จากตาราง HTML: {date_str}")
                                return date_str
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงวันที่จากตาราง HTML: {e}")
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # วิธีที่ 1: ลองดึงจาก HTML table ก่อน
        date_from_table = self._extract_date_from_html_table(text)
        if date_from_table:
            return date_from_table
        
        # วิธีที่ 2: ลองอ่านจาก text ธรรมดา
        # Pattern: Issue Date | 13Nov2025
        patterns = [
            r'Issue\s+Date\s*\|\s*(\d{1,2})([A-Za-z]{3})(\d{2,4})',  # Issue Date | 13Nov2025
            r'วันที่\s*Issue\s+Date\s*\|\s*(\d{1,2})([A-Za-z]{3})(\d{2,4})',  # วันที่ Issue Date | 13Nov2025
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
    
    def _extract_document_number_from_html_table(self, text: str) -> Optional[str]:
        """
        ดึงเลขที่เอกสารจากตาราง HTML
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            เลขที่เอกสารหรือ None
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
                
                # หา row ที่มี "Receipt No"
                for row in rows:
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
                    
                    # ตรวจสอบว่าเป็น row ที่มี "Receipt No"
                    row_text = ' '.join(cleaned_cells).upper()
                    if 'RECEIPT NO' in row_text or 'RECEIPT' in row_text:
                        # หา cell ที่มีเลขที่เอกสาร (รูปแบบ: E PBKI25111300144 หรือ PBKI25111300144)
                        for i, cell in enumerate(cleaned_cells):
                            # ตรวจสอบว่า cell นี้มี "Receipt No"
                            if 'RECEIPT' in cell.upper() and 'NO' in cell.upper():
                                # ลองหา pattern E PBKI25111300144 ใน cell นี้
                                doc_match = re.search(r'E\s*([A-Z0-9]{8,})', cell, re.IGNORECASE)
                                if doc_match:
                                    doc_number = doc_match.group(1).strip()
                                    if not re.match(r'^\d+$', doc_number):  # ตรวจสอบว่าไม่ใช่ตัวเลขล้วนๆ
                                        logger.info(f"✅ พบเลขที่เอกสารจากตาราง HTML: {doc_number}")
                                        return doc_number
                                
                                # ถ้าไม่พบใน cell นี้ ลองหาใน cell ถัดไป
                                if i + 1 < len(cleaned_cells):
                                    next_cell = cleaned_cells[i + 1]
                                    # ลองหา pattern E PBKI25111300144
                                    doc_match = re.search(r'E\s*([A-Z0-9]{8,})', next_cell, re.IGNORECASE)
                                    if doc_match:
                                        doc_number = doc_match.group(1).strip()
                                        if not re.match(r'^\d+$', doc_number):
                                            logger.info(f"✅ พบเลขที่เอกสารจากตาราง HTML (cell ถัดไป): {doc_number}")
                                            return doc_number
                                    
                                    # ลองหา pattern PBKI25111300144 โดยตรง
                                    doc_match = re.search(r'([A-Z]{2,}[A-Z0-9]{6,})', next_cell)
                                    if doc_match:
                                        doc_number = doc_match.group(1).strip()
                                        if not re.match(r'^\d+$', doc_number):
                                            logger.info(f"✅ พบเลขที่เอกสารจากตาราง HTML (cell ถัดไป): {doc_number}")
                                            return doc_number
                            
                            # หรือหาหมายเลขเอกสารใน cell ใดๆ ที่มีรูปแบบ (ถ้า row มี "Receipt No")
                            if 'RECEIPT NO' in row_text or 'RECEIPT' in row_text:
                                # ลองหา pattern E PBKI25111300144
                                doc_match = re.search(r'E\s*([A-Z0-9]{8,})', cell, re.IGNORECASE)
                                if doc_match:
                                    doc_number = doc_match.group(1).strip()
                                    if not re.match(r'^\d+$', doc_number):
                                        logger.info(f"✅ พบเลขที่เอกสารจากตาราง HTML: {doc_number}")
                                        return doc_number
                                
                                # ลองหา pattern PBKI25111300144 โดยตรง
                                doc_match = re.search(r'([A-Z]{2,}[A-Z0-9]{6,})', cell)
                                if doc_match:
                                    doc_number = doc_match.group(1).strip()
                                    if not re.match(r'^\d+$', doc_number):
                                        logger.info(f"✅ พบเลขที่เอกสารจากตาราง HTML: {doc_number}")
                                        return doc_number
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงเลขที่เอกสารจากตาราง HTML: {e}")
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # วิธีที่ 1: ลองดึงจาก HTML table ก่อน
        doc_number_from_table = self._extract_document_number_from_html_table(text)
        if doc_number_from_table:
            return doc_number_from_table
        
        # วิธีที่ 2: ลองอ่านจาก text ธรรมดา
        # Pattern: Receipt No | E PBKI25111300144
        patterns = [
            r'Receipt\s+No\s*\|\s*E\s*([A-Z0-9]+)',  # Receipt No | E PBKI25111300144
            r'Receipt\s+No\s*\|\s*([A-Z0-9]+)',  # Receipt No | PBKI25111300144
            r'RECEIPT\s+NO\s*\|\s*E\s*([A-Z0-9]+)',  # RECEIPT NO | E PBKI25111300144
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: PBKI25111300144
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
            B/L No. หรือ None (ถ้ามีหลาย B/L No. จะรวมด้วย /)
        """
        bl_numbers = []
        
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
                    # หา data rows (บรรทัดถัดไปหลังจาก header)
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
                        if any(keyword in row_text for keyword in ['VESSEL', 'VOYAGE', 'S/A DATE', 'B/L NO.', 'CURRENCY', 'AMOUNT']):
                            continue
                        
                        # ดึง B/L No. จาก column ที่ตรงกัน
                        if bl_index < len(cleaned_cells):
                            bl_no = cleaned_cells[bl_index].strip()
                            # ตรวจสอบว่ามีข้อมูลและไม่ใช่คำว่า "B/L No." หรือ header อื่นๆ
                            if bl_no and len(bl_no) > 3 and bl_no.upper() not in ['B/L NO.', 'B/L NO', 'B/L', 'NO.']:
                                # ตรวจสอบว่าเป็นรูปแบบ B/L No. ที่ถูกต้อง (มีตัวอักษรและตัวเลข)
                                if re.match(r'^[A-Z0-9]{4,}$', bl_no):
                                    if bl_no not in bl_numbers:
                                        bl_numbers.append(bl_no)
                                        logger.info(f"✅ พบ B/L No. จากตาราง HTML: {bl_no}")
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึง B/L No. จากตาราง HTML: {e}")
        
        # รวม B/L No. ทั้งหมดด้วย /
        if bl_numbers:
            return '/'.join(bl_numbers)
        
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
                    
                    # หา data rows (อาจมีหลายบรรทัด)
                    bl_numbers = []
                    for j in range(i + 1, min(i + 10, len(lines))):  # ตรวจสอบ 9 บรรทัดถัดไป
                        next_line = lines[j].strip()
                        if not next_line or not '|' in next_line:
                            continue
                        
                        # แยกด้วย |
                        parts = [p.strip() for p in next_line.split('|')]
                        
                        # ตรวจสอบว่าบรรทัดนี้มีข้อมูล (ไม่ใช่ header ซ้ำ)
                        if len(parts) < 2:
                            continue
                        
                        # ตรวจสอบว่าบรรทัดนี้ไม่ใช่ header (ไม่มีคำว่า "Vessel", "B/L No.", "Currency")
                        if any(keyword in next_line.upper() for keyword in ['VESSEL', 'VOYAGE', 'S/A DATE', 'B/L NO.', 'CURRENCY', 'AMOUNT']):
                            continue
                        
                        # ดึง B/L No. จาก column ที่ตรงกัน
                        if bl_index >= 0 and bl_index < len(parts):
                            bl_no_item = parts[bl_index].strip()
                            # ตรวจสอบว่ามีข้อมูลและไม่ใช่คำว่า "B/L No." หรือ header อื่นๆ
                            if bl_no_item and len(bl_no_item) > 3 and bl_no_item.upper() not in ['B/L NO.', 'B/L NO', 'B/L', 'NO.']:
                                # ตรวจสอบว่าเป็นรูปแบบ B/L No. ที่ถูกต้อง (มีตัวอักษรและตัวเลข)
                                if re.match(r'^[A-Z0-9]{4,}$', bl_no_item):
                                    if bl_no_item not in bl_numbers:
                                        bl_numbers.append(bl_no_item)
                                        logger.info(f"✅ พบ B/L No. จากตาราง: {bl_no_item}")
                    
                    if bl_numbers:
                        bl_no = '/'.join(bl_numbers)
                        reference_parts.append(f"B/L No. {bl_no}")
                        break
        
        # อ้างอิง: มีเฉพาะ B/L No. เท่านั้น (ไม่รวมชื่อไฟล์)
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
        # Pattern: FREIGHT AND CHARGE(S) ON B/L NO
        #          14,000.00
        # Pattern: GRAND TOTAL THB 14,000.00
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        
        amount_before_vat = None
        vat_amount = 0.00  # ไม่มีภาษีมูลค่าเพิ่ม
        total_amount = None
        
        # ดึงยอดก่อนภาษี: FREIGHT AND CHARGE(S) ON B/L NO
        #                 14,000.00
        amount_patterns = [
            r'FREIGHT\s+AND\s+CHARGE\(S\)\s+ON\s+B/L\s+NO\s*([\d,]+\.?\d{2})',  # FREIGHT AND CHARGE(S) ON B/L NO 14,000.00
            r'FREIGHT\s+AND\s+CHARGE\(S\)\s+ON\s+B/L\s+NO.*?\n\s*([\d,]+\.?\d{2})',  # FREIGHT AND CHARGE(S) ON B/L NO\n14,000.00
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    amount_before_vat = float(amount_str)
                    logger.info(f"✅ พบยอดก่อนภาษี: {amount_before_vat}")
                    break
                except ValueError:
                    continue
        
        # ถ้ายังไม่พบ ลองหาจากบรรทัดถัดไปหลังจาก "FREIGHT AND CHARGE(S) ON B/L NO"
        if amount_before_vat is None:
            freight_match = re.search(r'FREIGHT\s+AND\s+CHARGE\(S\)\s+ON\s+B/L\s+NO', text, re.IGNORECASE)
            if freight_match:
                # หาบรรทัดถัดไป
                start_pos = freight_match.end()
                next_line_match = re.search(r'([\d,]+\.\d{2})', text[start_pos:start_pos+50], re.IGNORECASE)
                if next_line_match:
                    amount_str = next_line_match.group(1).replace(',', '').strip()
                    try:
                        amount_before_vat = float(amount_str)
                        logger.info(f"✅ พบยอดก่อนภาษี (จากบรรทัดถัดไป): {amount_before_vat}")
                    except ValueError:
                        pass
        
        # ดึงยอดรวม: GRAND TOTAL THB 14,000.00
        total_patterns = [
            r'GRAND\s+TOTAL\s+THB\s*([\d,]+\.?\d{2})',  # GRAND TOTAL THB 14,000.00
            r'GRAND\s+TOTAL\s*([\d,]+\.?\d{2})',  # GRAND TOTAL 14,000.00
            r'TOTAL\s*[:.]?\s*([\d,]+\.?\d{2})',  # TOTAL: 14,000.00
            r'ยอดรวม\s*[:.]?\s*([\d,]+\.?\d{2})',  # ยอดรวม: 14,000.00
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
        # Pattern: CENTRAL PARK OFFICES, UNIT MM2701-2710, 27TH FLOOR,
        #          92 RAMA 4 ROAD, SILOM, BANGRAK, BANGKOK 10500
        address_patterns = [
            r'CENTRAL\s+PARK\s+OFFICES[^\n]*\n\s*92\s+RAMA\s+4\s+ROAD[^\n]*',
            r'CENTRAL\s+PARK\s+OFFICES.*?BANGKOK\s+\d{5}',
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                address = match.group(0).strip()
                # ทำความสะอาด address
                address = re.sub(r'\s+', ' ', address)
                logger.info(f"✅ พบที่อยู่: {address}")
                return address
        
        # Fallback: ใช้ที่อยู่ที่กำหนด
        return "CENTRAL PARK OFFICES, UNIT MM2701-2710, 27TH FLOOR, 92 RAMA 4 ROAD, SILOM, BANGRAK, BANGKOK 10500"
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (B/L No. จากตาราง + ชื่อไฟล์)"""
        remark_parts = []
        
        # ดึง B/L No. จากตาราง HTML
        bl_no = self._extract_bl_no_from_html_table(text)
        
        if bl_no:
            remark_parts.append(f"B/L No. {bl_no}")
            logger.info(f"✅ พบ B/L No. สำหรับหมายเหตุ: {bl_no}")
        
        # ดึงชื่อไฟล์เก่า (ตัด VAT_, WHT_, None_vat_ และไม่เอา .pdf แต่เก็บ EXC_ ไว้)
        if filename:
            # ลบ VAT_, WHT_, None_vat_ ออกจากชื่อไฟล์
            cleaned = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename, flags=re.IGNORECASE)
            
            # ลบ .pdf
            cleaned = re.sub(r'\.pdf$', '', cleaned, flags=re.IGNORECASE)
            
            # ลบช่องว่างที่เหลือ
            cleaned = cleaned.strip()
            
            if cleaned and cleaned not in remark_parts:
                remark_parts.append(cleaned)
        
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
        ดึงข้อมูลทั้งหมดจากเอกสาร Ocean Network Express
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร Ocean Network Express หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร OCEAN NETWORK EXPRESS (THAILAND) LTD.'
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
        building_number = ''
        other_info = 'CENTRAL PARK OFFICES, UNIT MM2701-2710, 27TH FLOOR'
        soi = ''
        road = '92 RAMA 4 ROAD'
        subdistrict = 'SILOM'
        district = 'SILOM'
        province = 'BANGRAK'
        postal_code = '10500'
        
        # ตั้งค่า skip_amount_adjustment = True เพื่อไม่ให้ระบบปรับยอดเงิน (ใช้ค่าที่อ่านได้เท่านั้น)
        # เพราะเอกสารนี้ไม่มีภาษีมูลค่าเพิ่ม
        return {
            'success': True,
            'company': 'OCEAN_NETWORK_EXPRESS',
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

