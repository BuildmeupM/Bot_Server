"""
OOCL Thailand Invoice Extractor
================================
Extractor สำหรับดึงข้อมูลจาก OOCL (Thailand) Limited

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class OOCLThailandExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก OOCL (Thailand) Limited"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "OOCL (Thailand) Limited",
        "OOCL (Thailand) Limited As Agent For Orient Overseas Container Line Limited",
        "OOCL",
        "Orient Overseas Container Line"
    ]
    
    # Tax ID
    TAX_ID = "0993000037774"
    
    def __init__(self):
        """Initialize OOCL Thailand Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ OOCL (Thailand) Limited หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "OOCL (Thailand) Limited"
        2. Tax ID "0993000037774"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร OOCL Thailand (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier.upper() in text.upper() for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0993000037774"
        has_tax_id = self.TAX_ID in text or "Reg. No:" + self.TAX_ID in text
        
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
        return "OOCL (Thailand) Limited"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: OOCL (Thailand) Limited As Agent For Orient Overseas Container Line Limited Reg. No:0993000037774
        patterns = [
            r'Reg\.\s+No\s*[:.]?\s*(\d{13})',  # Reg. No:0993000037774
            r'REG\.\s+NO\s*[:.]?\s*(\d{13})',  # REG. NO:0993000037774
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0993000037774
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี 0993000037774
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
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: DATE : 06 Nov 2025
        patterns = [
            r'DATE\s*[:.]?\s*(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})',  # DATE : 06 Nov 2025
            r'วันที่\s*[:.]?\s*DATE\s*[:.]?\s*(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})',  # วันที่ : DATE : 06 Nov 2025
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
                year = match.group(3)
                
                month = month_map.get(month_abbr, '01')
                
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: RECEIPT NO. : 419RGS261130
        patterns = [
            r'RECEIPT\s+NO\.\s*[:.]?\s*([A-Z0-9]+)',  # RECEIPT NO. : 419RGS261130
            r'Receipt\s+No\.\s*[:.]?\s*([A-Z0-9]+)',  # Receipt No. : 419RGS261130
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: 419RGS261130
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
    
    def _extract_reference_from_html_table(self, text: str) -> Optional[str]:
        """
        ดึงอ้างอิง (BILL OF LADING NO.) จากตาราง HTML
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            BILL OF LADING NO. หรือ None
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
                
                # หา header row ที่มี "BILL OF LADING NO." หรือ "INVOICE NO. / BILL OF LADING NO."
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
                    
                    # ตรวจสอบว่าเป็น header row
                    row_text = ' '.join(cleaned_cells).upper()
                    if 'BILL OF LADING' in row_text or ('INVOICE NO' in row_text and 'BILL OF LADING' in row_text):
                        # หา column index
                        for idx, cell in enumerate(cleaned_cells):
                            cell_upper = cell.upper()
                            if 'BILL OF LADING' in cell_upper or ('INVOICE NO' in cell_upper and 'BILL OF LADING' in cell_upper):
                                bl_index = idx
                                header_row_index = i
                                logger.debug(f"✅ พบ BILL OF LADING column ที่ index: {bl_index} ใน row: {header_row_index}")
                                break
                        
                        if bl_index >= 0:
                            break
                
                # ถ้าพบ header row
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
                        if any(keyword in row_text for keyword in ['INVOICE NO', 'BILL OF LADING', 'VESSEL', 'VOYAGE', 'AMOUNT']):
                            continue
                        
                        # ดึง BILL OF LADING NO. จาก column ที่ตรงกัน
                        if bl_index < len(cleaned_cells):
                            bl_cell = cleaned_cells[bl_index].strip()
                            # ถ้ามีรูปแบบ "4193815494 / 2163752430" ให้เอาตัวที่ 2 (หลัง /)
                            if '/' in bl_cell:
                                parts = [p.strip() for p in bl_cell.split('/')]
                                if len(parts) >= 2:
                                    bl_no = parts[1].strip()
                                    if bl_no and len(bl_no) > 3:
                                        logger.info(f"✅ พบ BILL OF LADING NO. จากตาราง HTML: {bl_no}")
                                        return f"B/L : {bl_no}"
                            else:
                                # ถ้าไม่มี / ให้ใช้ทั้งหมด
                                if bl_cell and len(bl_cell) > 3:
                                    logger.info(f"✅ พบ BILL OF LADING NO. จากตาราง HTML: {bl_cell}")
                                    return f"B/L : {bl_cell}"
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงอ้างอิงจากตาราง HTML: {e}")
        
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง (BILL OF LADING NO. จากตาราง หรือชื่อไฟล์เก่า)"""
        reference_parts = []
        
        # วิธีที่ 1: ลองดึงจาก HTML table ก่อน
        ref_from_table = self._extract_reference_from_html_table(text)
        if ref_from_table:
            reference_parts.append(ref_from_table)
            logger.info(f"✅ พบอ้างอิงจาก HTML table: {ref_from_table}")
        
        # วิธีที่ 2: ถ้ายังไม่พบ ให้ลองอ่านจาก text ธรรมดา
        if not ref_from_table:
            # Pattern: INVOICE NO. / BILL OF LADING NO. | 4193815494 / 2163752430
            bl_patterns = [
                r'BILL\s+OF\s+LADING\s+NO\.\s*\|\s*[^\|]*\s*/\s*(\d+)',  # BILL OF LADING NO. | ... / 2163752430
                r'INVOICE\s+NO\.\s*/\s*BILL\s+OF\s+LADING\s+NO\.\s*\|\s*[^\|]*\s*/\s*(\d+)',  # INVOICE NO. / BILL OF LADING NO. | ... / 2163752430
            ]
            
            for pattern in bl_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    ref_from_table = match.group(1).strip()
                    reference_parts.append(f"B/L : {ref_from_table}")
                    logger.info(f"✅ พบอ้างอิง: B/L : {ref_from_table}")
                    break
        
        # วิธีที่ 3: ถ้ายังไม่พบ ให้ใช้ชื่อไฟล์เก่า
        if not ref_from_table and filename:
            # ลบ VAT_, WHT_, None_vat_ ออกจากชื่อไฟล์
            cleaned = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename, flags=re.IGNORECASE)
            
            # ตัด EXC_ และข้อมูลที่อยู่ด้านหลังออก
            cleaned = re.sub(r'EXC_[^\s.]*', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'EXC-[^\s.]*', '', cleaned, flags=re.IGNORECASE)
            
            # ลบ .pdf
            cleaned = re.sub(r'\.pdf$', '', cleaned, flags=re.IGNORECASE)
            
            # ลบช่องว่างที่เหลือ
            cleaned = cleaned.strip()
            
            if cleaned:
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
        # Pattern: TOTAL THB 6,950.00
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        
        amount_before_vat = None
        vat_amount = 0.00  # ไม่มีภาษีมูลค่าเพิ่ม
        total_amount = None
        
        # ดึงยอดรวม: TOTAL THB 6,950.00
        total_patterns = [
            r'TOTAL\s+THB\s*([\d,]+\.?\d{2})',  # TOTAL THB 6,950.00
            r'TOTAL\s*[:.]?\s*([\d,]+\.?\d{2})',  # TOTAL: 6,950.00
            r'ยอดรวม\s*[:.]?\s*([\d,]+\.?\d{2})',  # ยอดรวม: 6,950.00
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
        
        # ถ้าพบยอดรวม ให้ใช้เป็นยอดก่อนภาษีด้วย (เพราะไม่มีภาษี)
        if total_amount is not None:
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
        return "75/68-69, Sukhumvit 19, Klongtoey-nua, Wattana, Bangkok 10110"
    
    def _extract_invoice_no_from_html_table(self, text: str) -> Optional[str]:
        """
        ดึง INVOICE NO. จากตาราง HTML สำหรับหมายเหตุ
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            INVOICE NO. หรือ None
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
                
                # หา header row ที่มี "INVOICE NO. / BILL OF LADING NO."
                invoice_index = -1
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
                    
                    # ตรวจสอบว่าเป็น header row
                    row_text = ' '.join(cleaned_cells).upper()
                    if 'INVOICE NO' in row_text and 'BILL OF LADING' in row_text:
                        # หา column index
                        for idx, cell in enumerate(cleaned_cells):
                            cell_upper = cell.upper()
                            if 'INVOICE NO' in cell_upper and 'BILL OF LADING' in cell_upper:
                                invoice_index = idx
                                header_row_index = i
                                logger.debug(f"✅ พบ INVOICE NO. column ที่ index: {invoice_index} ใน row: {header_row_index}")
                                break
                        
                        if invoice_index >= 0:
                            break
                
                # ถ้าพบ header row
                if invoice_index >= 0 and header_row_index >= 0:
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
                        if any(keyword in row_text for keyword in ['INVOICE NO', 'BILL OF LADING', 'VESSEL', 'VOYAGE', 'AMOUNT']):
                            continue
                        
                        # ดึง INVOICE NO. จาก column ที่ตรงกัน
                        if invoice_index < len(cleaned_cells):
                            invoice_cell = cleaned_cells[invoice_index].strip()
                            # ถ้ามีรูปแบบ "4193815494 / 2163752430" ให้เอาตัวแรก (ก่อน /)
                            if '/' in invoice_cell:
                                parts = [p.strip() for p in invoice_cell.split('/')]
                                if len(parts) >= 1:
                                    invoice_no = parts[0].strip()
                                    if invoice_no and len(invoice_no) > 3:
                                        logger.info(f"✅ พบ INVOICE NO. จากตาราง HTML: {invoice_no}")
                                        return invoice_no
                            else:
                                # ถ้าไม่มี / ให้ใช้ทั้งหมด
                                if invoice_cell and len(invoice_cell) > 3:
                                    logger.info(f"✅ พบ INVOICE NO. จากตาราง HTML: {invoice_cell}")
                                    return invoice_cell
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึง INVOICE NO. จากตาราง HTML: {e}")
        
        return None
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (INVOICE NO. จากตาราง และชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_)"""
        remark_parts = []
        
        # ดึง INVOICE NO. จากตาราง HTML
        invoice_no = self._extract_invoice_no_from_html_table(text)
        if invoice_no:
            remark_parts.append(invoice_no)
            logger.info(f"✅ พบ INVOICE NO. สำหรับหมายเหตุ: {invoice_no}")
        
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
        ดึงข้อมูลทั้งหมดจากเอกสาร OOCL Thailand
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร OOCL Thailand หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร OOCL (Thailand) Limited'
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
        building_number = '75/68-69'
        other_info = ''
        soi = 'Sukhumvit 19'
        road = ''
        subdistrict = 'Klongtoey-nua'
        district = 'Wattana'
        province = 'Bangkok'
        postal_code = '10110'
        
        # ตั้งค่า skip_amount_adjustment = True เพื่อไม่ให้ระบบปรับยอดเงิน (ใช้ค่าที่อ่านได้เท่านั้น)
        # เพราะเอกสารนี้ไม่มีภาษีมูลค่าเพิ่ม
        return {
            'success': True,
            'company': 'OOCL_THAILAND',
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

