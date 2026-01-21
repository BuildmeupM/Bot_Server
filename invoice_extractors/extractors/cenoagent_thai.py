"""
Cenoagent Thai Invoice Extractor
=================================
Extractor สำหรับดึงข้อมูลจาก บริษัท ซีโนเอเจนต์ ไทย จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class CenoagentThaiExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท ซีโนเอเจนต์ ไทย จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "บริษัท ซีโนเอเจนต์ ไทย จำกัด",
        "บริษัท ซีโนเทรานส์ คอนเทนเนอร์ ไลน์ (ไต้หวัน) จำกัด",
        "CENOAGENT THAI",
        "CENO TRANS CONTAINER LINE"
    ]
    
    # Tax ID (รูปแบบที่มี -)
    TAX_ID_WITH_DASH = "099-3-00050116-1"
    # Tax ID (รูปแบบที่เอา - ออก)
    TAX_ID = "0993000501161"
    
    def __init__(self):
        """Initialize Cenoagent Thai Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ บริษัท ซีโนเอเจนต์ ไทย จำกัด หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท ซีโนเอเจนต์ ไทย จำกัด"
        2. Tax ID "099-3-00050116-1"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Cenoagent Thai (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier.upper() in text.upper() for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "099-3-00050116-1" หรือ "0993000501161"
        has_tax_id = self.TAX_ID_WITH_DASH in text or self.TAX_ID in text or "099-3-00050116-1" in text
        
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
        return "บริษัท ซีโนเอเจนต์ ไทย จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี (เอา - ออก)"""
        # Pattern: Tax ID. No. เลขประจำตัวผู้เสียภาษีอากร 099-3-00050116-1
        patterns = [
            r'Tax\s+ID\.\s+No\.\s*เลขประจำตัวผู้เสียภาษีอากร\s*(\d{3}[\-]\d[\-]\d{8}[\-]\d)',  # Tax ID. No. เลขประจำตัวผู้เสียภาษีอากร 099-3-00050116-1
            r'Tax\s+ID\.\s*No\.\s*(\d{3}[\-]\d[\-]\d{8}[\-]\d)',  # Tax ID. No. 099-3-00050116-1
            r'เลขประจำตัวผู้เสียภาษีอากร\s*(\d{3}[\-]\d[\-]\d{8}[\-]\d)',  # เลขประจำตัวผู้เสียภาษีอากร 099-3-00050116-1
            r'(\d{3}[\-]\d[\-]\d{8}[\-]\d)',  # 099-3-00050116-1
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id_with_dash = match.group(1).strip()
                # เอา - ออก
                tax_id = tax_id_with_dash.replace('-', '')
                if tax_id == self.TAX_ID or tax_id_with_dash == self.TAX_ID_WITH_DASH:
                    logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษี: {tax_id_with_dash} → {tax_id}")
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
                
                # หา row ที่มี "Date" ใน header
                date_index = -1
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
                    
                    # ตรวจสอบว่าเป็น header row ที่มี "Date"
                    row_text = ' '.join(cleaned_cells).upper()
                    if 'DATE' in row_text and ('DNO' in row_text or 'NUMBER' in row_text):
                        # หา column index ของ Date
                        for idx, cell in enumerate(cleaned_cells):
                            cell_upper = cell.upper()
                            if 'DATE' in cell_upper:
                                date_index = idx
                                header_row_index = i
                                logger.debug(f"✅ พบ Date column ที่ index: {date_index} ใน row: {header_row_index}")
                                break
                        
                        if date_index >= 0:
                            break
                
                # ถ้าพบ header row ที่มี Date
                if date_index >= 0 and header_row_index >= 0:
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
                        if any(keyword in row_text for keyword in ['DNO', 'NUMBER', 'DATE', 'EFT NUMBER', 'JOB NUMBER']):
                            continue
                        
                        # ดึงวันที่จาก column ที่ตรงกัน
                        if date_index < len(cleaned_cells):
                            date_cell = cleaned_cells[date_index].strip()
                            # หาวันที่ในรูปแบบ 2025-11-06 หรือ 10/11/2025
                            date_match = re.search(r'(\d{4})[\-](\d{1,2})[\-](\d{1,2})', date_cell)
                            if date_match:
                                year = date_match.group(1)
                                month = date_match.group(2).zfill(2)
                                day = date_match.group(3).zfill(2)
                                date_str = f"{day}/{month}/{year}"
                                logger.info(f"✅ พบวันที่จากตาราง HTML: {date_str}")
                                return date_str
                            
                            # ลองหาวันที่ในรูปแบบ 10/11/2025
                            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_cell)
                            if date_match:
                                day = date_match.group(1).zfill(2)
                                month = date_match.group(2).zfill(2)
                                year = date_match.group(3)
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
        # Pattern: : 10/11/2025
        patterns = [
            r':\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # : 10/11/2025
            r'วันที่\s*[:.]?\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # วันที่: 10/11/2025
            r'DATE\s*[:.]?\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # DATE: 10/11/2025
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
        """ดึงเลขที่เอกสาร"""
        # Pattern: No. : R125110412
        patterns = [
            r'No\.\s*[:.]?\s*([A-Z0-9]+)',  # No. : R125110412
            r'NO\.\s*[:.]?\s*([A-Z0-9]+)',  # NO. : R125110412
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: R125110412
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
        ดึงอ้างอิง (Job Number หรือ Eft Number) จากตาราง HTML
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            อ้างอิงหรือ None
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
                
                # หา header row ที่มี "Job Number" หรือ "Eft Number"
                job_index = -1
                eft_index = -1
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
                    if 'JOB NUMBER' in row_text or 'EFT NUMBER' in row_text:
                        # หา column index
                        for idx, cell in enumerate(cleaned_cells):
                            cell_upper = cell.upper()
                            if 'JOB NUMBER' in cell_upper:
                                job_index = idx
                                header_row_index = i
                            elif 'EFT NUMBER' in cell_upper:
                                eft_index = idx
                                header_row_index = i
                        
                        if job_index >= 0 or eft_index >= 0:
                            break
                
                # ถ้าพบ header row
                if header_row_index >= 0:
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
                        if any(keyword in row_text for keyword in ['DNO', 'NUMBER', 'DATE', 'EFT NUMBER', 'JOB NUMBER']):
                            continue
                        
                        # ดึง Job Number หรือ Eft Number
                        if job_index >= 0 and job_index < len(cleaned_cells):
                            job_no = cleaned_cells[job_index].strip()
                            if job_no and len(job_no) > 3:
                                logger.info(f"✅ พบ Job Number จากตาราง HTML: {job_no}")
                                return job_no
                        
                        if eft_index >= 0 and eft_index < len(cleaned_cells):
                            eft_no = cleaned_cells[eft_index].strip()
                            if eft_no and len(eft_no) > 3:
                                logger.info(f"✅ พบ Eft Number จากตาราง HTML: {eft_no}")
                                return eft_no
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงอ้างอิงจากตาราง HTML: {e}")
        
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง (Job Number/Eft Number จากตาราง หรือชื่อไฟล์เก่า)"""
        reference_parts = []
        
        # วิธีที่ 1: ลองดึงจาก HTML table ก่อน
        ref_from_table = self._extract_reference_from_html_table(text)
        if ref_from_table:
            reference_parts.append(ref_from_table)
            logger.info(f"✅ พบอ้างอิงจาก HTML table: {ref_from_table}")
        
        # วิธีที่ 2: ถ้ายังไม่พบ ให้ลองอ่านจาก text ธรรมดา
        if not ref_from_table:
            # Pattern: Job Number | SNLFNBILA451054
            job_patterns = [
                r'Job\s+Number\s*\|\s*([A-Z0-9]+)',  # Job Number | SNLFNBILA451054
                r'JOB\s+NUMBER\s*\|\s*([A-Z0-9]+)',  # JOB NUMBER | SNLFNBILA451054
            ]
            
            for pattern in job_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    ref_from_table = match.group(1).strip()
                    reference_parts.append(ref_from_table)
                    logger.info(f"✅ พบอ้างอิง: {ref_from_table}")
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
        # Pattern: Grand Total 6,660.00 6,660.00 (เอาตัวสุดท้าย)
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        
        amount_before_vat = None
        vat_amount = 0.00  # ไม่มีภาษีมูลค่าเพิ่ม
        total_amount = None
        
        # ดึงยอดรวม: Grand Total 6,660.00 6,660.00 (เอาตัวสุดท้าย)
        total_patterns = [
            r'Grand\s+Total\s+([\d,]+\.?\d{2})\s+([\d,]+\.?\d{2})',  # Grand Total 6,660.00 6,660.00 (เอาตัวที่ 2)
            r'GRAND\s+TOTAL\s+([\d,]+\.?\d{2})\s+([\d,]+\.?\d{2})',  # GRAND TOTAL 6,660.00 6,660.00
            r'Grand\s+Total\s*([\d,]+\.?\d{2})',  # Grand Total 6,660.00
            r'TOTAL\s*[:.]?\s*([\d,]+\.?\d{2})',  # TOTAL: 6,660.00
            r'ยอดรวม\s*[:.]?\s*([\d,]+\.?\d{2})',  # ยอดรวม: 6,660.00
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # ถ้ามี 2 กลุ่ม (Grand Total 6,660.00 6,660.00) ให้เอาตัวที่ 2
                if len(match.groups()) == 2:
                    amount_str = match.group(2).replace(',', '').strip()
                else:
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
        return "87/2 อาคารซีอาร์ซี ทาวเวอร์ ออล ซีซั่นส์ เพลส ชั้นที่ 37 ถนนวิทยุ แขวงลุมพินี เขตปทุมวัน กรุงเทพมหานคร 10330"
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (Ref. และชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_)"""
        remark_parts = []
        
        # ดึง Ref. : SNLFNBILA451054
        ref_patterns = [
            r'Ref\.\s*[:.]?\s*([A-Z0-9]+)',  # Ref. : SNLFNBILA451054
            r'REF\.\s*[:.]?\s*([A-Z0-9]+)',  # REF. : SNLFNBILA451054
            r'อ้างอิง\s*[:.]?\s*([A-Z0-9]+)',  # อ้างอิง: SNLFNBILA451054
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
        ดึงข้อมูลทั้งหมดจากเอกสาร Cenoagent Thai
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร Cenoagent Thai หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร บริษัท ซีโนเอเจนต์ ไทย จำกัด'
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
        building_number = '87/2'
        other_info = 'อาคารซีอาร์ซี ทาวเวอร์ ออล ซีซั่นส์ เพลส ชั้นที่ 37'
        soi = ''
        road = 'ถนนวิทยุ'
        subdistrict = 'ลุมพินี'
        district = 'ปทุมวัน'
        province = 'กรุงเทพมหานคร'
        postal_code = '10330'
        
        # ตั้งค่า skip_amount_adjustment = True เพื่อไม่ให้ระบบปรับยอดเงิน (ใช้ค่าที่อ่านได้เท่านั้น)
        # เพราะเอกสารนี้ไม่มีภาษีมูลค่าเพิ่ม
        return {
            'success': True,
            'company': 'CENOAGENT_THAI',
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

