"""
Yang Ming Line (Thailand) Invoice Extractor
===========================================
Extractor สำหรับดึงข้อมูลจาก บริษัท หยางหมิง ไลน์ (ประเทศไทย) จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class YangMingLineExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท หยางหมิง ไลน์ (ประเทศไทย) จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "บริษัท หยางหมิง ไลน์ (ประเทศไทย) จำกัด",
        "หยางหมิง ไลน์",
        "Yang Ming Line",
        "YANG MING LINE"
    ]
    
    # Tax ID
    TAX_ID = "0105560162166"
    
    # Fixed address
    ADDRESS = {
        "ที่อยู่รวม": "1788 อาคารสิงห์ คอมเพล็กซ์ ชั้น 20 ห้องเลขที่ 2005-2006 ถนนเพชรบุรีตัดใหม่ แขวงบางกะปิ เขตห้วยขวาง กรุงเทพมหานคร 10310",
        "เลขที่": "",
        "อื่นๆ": "1788 อาคารสิงห์ คอมเพล็กซ์ ชั้น 20 ห้องเลขที่ 2005-2006",
        "ถนน": "ถนนเพชรบุรีตัดใหม่",
        "ซอย": "",
        "แขวง": "บางกะปิ",
        "เขต": "ห้วยขวาง",
        "จังหวัด": "กรุงเทพมหานคร",
        "เลขไปรษณีย์": "10310"
    }
    
    def __init__(self):
        """Initialize Yang Ming Line Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ บริษัท หยางหมิง ไลน์ (ประเทศไทย) จำกัด หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท หยางหมิง ไลน์ (ประเทศไทย) จำกัด"
        2. Tax ID "0105560162166"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Yang Ming Line (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier.upper() in text.upper() for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105560162166"
        has_tax_id = self.TAX_ID in text or f"Tax ID No. {self.TAX_ID}" in text
        
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
        return "บริษัท หยางหมิง ไลน์ (ประเทศไทย) จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: Tax ID No. 0105560162166 HEAD OFFICE
        patterns = [
            r'Tax\s+ID\s+No\.\s*(\d{13})\s*HEAD\s+OFFICE',  # Tax ID No. 0105560162166 HEAD OFFICE
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0105560162166
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0105560162166
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี 0105560162166
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
        # Pattern: DATE: 10/11/2025
        patterns = [
            r'DATE\s*[:.]?\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # DATE: 10/11/2025
            r'วันที่\s*[:.]?\s*DATE\s*[:.]?\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # วันที่ : DATE: 10/11/2025
            r'วันที่\s*[:.]?\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # วันที่: 10/11/2025
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                date_str = f"{day}/{month}/{year}"
                logger.info(f"✅ พบวันที่: {date_str}")
                return date_str
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: TAX INVOICE NO .: RCT/2025/YML/111846
        patterns = [
            r'TAX\s+INVOICE\s+NO\s*\.?\s*[:.]?\s*([A-Z0-9/]+)',  # TAX INVOICE NO .: RCT/2025/YML/111846
            r'Tax\s+Invoice\s+No\s*\.?\s*[:.]?\s*([A-Z0-9/]+)',  # Tax Invoice No.: RCT/2025/YML/111846
            r'เลขที่\s*[:.]?\s*([A-Z0-9/]+)',  # เลขที่: RCT/2025/YML/111846
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_number = match.group(1).strip()
                logger.info(f"✅ พบเลขที่เอกสาร: {doc_number}")
                return doc_number
        
        return None
    
    def _extract_bl_no_from_html_table(self, text: str) -> Optional[str]:
        """
        ดึง B/L NO. จากตาราง HTML หรือ text
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            B/L NO. หรือ None
        """
        try:
            # วิธีที่ 1: อ่านแบบบรรทัดต่อบรรทัด (line-by-line) - ยืดหยุ่นที่สุด
            lines = text.split('\n')
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                # ตรวจสอบว่าบรรทัดนี้มี "B/L NO" หรือ "B/L NO."
                if 'B/L NO' in line_stripped.upper() or 'BILL OF LADING' in line_stripped.upper():
                    # หา B/L NO. ในบรรทัดเดียวกันหรือบรรทัดถัดไป
                    # Pattern: B/L NO .: | I235248816 |
                    bl_match = re.search(r'B/L\s+NO\s*\.?\s*[:.]?\s*\|?\s*([A-Z0-9]{8,})', line_stripped, re.IGNORECASE)
                    if bl_match:
                        bl_no = bl_match.group(1).strip()
                        logger.info(f"✅ พบ B/L NO. จากบรรทัด {i+1}: {bl_no}")
                        return bl_no
                    
                    # ถ้าไม่พบในบรรทัดเดียวกัน ให้ตรวจสอบบรรทัดถัดไป
                    for j in range(i + 1, min(i + 3, len(lines))):
                        next_line = lines[j].strip()
                        # หา B/L NO. ในรูปแบบ I235248816 (ต้องมีตัวอักษรและตัวเลข)
                        bl_match = re.search(r'\|?\s*([A-Z]\d{8,})\s*\|?', next_line)
                        if bl_match:
                            bl_no = bl_match.group(1).strip()
                            logger.info(f"✅ พบ B/L NO. จากบรรทัด {j+1}: {bl_no}")
                            return bl_no
            
            # วิธีที่ 2: ลองอ่านจาก HTML table structure
            table_pattern = r'<table[^>]*>(.*?)</table>'
            tables = re.findall(table_pattern, text, re.DOTALL | re.IGNORECASE)
            
            if not tables:
                return None
            
            # วนลูปทุกตาราง
            for table_html in tables:
                # แยก rows
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
                
                # หา row ที่มี "B/L NO" ในบรรทัดแรก
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
                    
                    # ตรวจสอบว่ามี "B/L NO" ใน row นี้
                    row_text = ' '.join(cleaned_cells).upper()
                    if 'B/L NO' in row_text:
                        # หา B/L NO. ใน row นี้
                        for cell in cleaned_cells:
                            # Pattern: B/L NO .: | I235248816 |
                            bl_match = re.search(r'B/L\s+NO\s*\.?\s*[:.]?\s*\|?\s*([A-Z0-9]{8,})', cell, re.IGNORECASE)
                            if bl_match:
                                bl_no = bl_match.group(1).strip()
                                # ตรวจสอบว่าไม่ใช่คำทั่วไป
                                if not any(word in bl_no.upper() for word in ['DOCUMENTATION', 'FEE', 'CHARGE', 'MAINTENANCE']):
                                    logger.info(f"✅ พบ B/L NO. จากตาราง HTML: {bl_no}")
                                    return bl_no
                        
                        # ถ้าไม่พบใน row นี้ ให้ตรวจสอบ cell ถัดไป
                        for idx, cell in enumerate(cleaned_cells):
                            if 'B/L NO' in cell.upper() and idx + 1 < len(cleaned_cells):
                                next_cell = cleaned_cells[idx + 1].strip()
                                # หา B/L NO. ในรูปแบบ I235248816
                                bl_match = re.search(r'([A-Z]\d{8,})', next_cell)
                                if bl_match:
                                    bl_no = bl_match.group(1).strip()
                                    if not any(word in bl_no.upper() for word in ['DOCUMENTATION', 'FEE', 'CHARGE', 'MAINTENANCE']):
                                        logger.info(f"✅ พบ B/L NO. จากตาราง HTML (cell ถัดไป): {bl_no}")
                                        return bl_no
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึง B/L NO. จากตาราง HTML: {e}")
        
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง"""
        # วิธีที่ 1: ลองดึงจากตาราง HTML
        bl_no = self._extract_bl_no_from_html_table(text)
        if bl_no:
            reference = f"B/L : {bl_no}"
            logger.info(f"✅ พบอ้างอิงจาก HTML table: {reference}")
            return reference
        
        # วิธีที่ 2: ใช้ชื่อไฟล์เก่า (ถ้าไม่พบ B/L NO.)
        if filename:
            old_filename = self._clean_filename(filename)
            if old_filename:
                return old_filename
        
        return None
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงยอดเงิน"""
        amounts = {
            "before_vat": None,
            "vat": 0.00,
            "total": None
        }
        
        # Pattern: Total THB 7050.00
        patterns = [
            r'Total\s+THB\s+([\d,]+\.?\d*)',  # Total THB 7050.00
            r'TOTAL\s+THB\s+([\d,]+\.?\d*)',  # TOTAL THB 7050.00
            r'Total\s*[:.]?\s*THB\s*[:.]?\s*([\d,]+\.?\d*)',  # Total : THB : 7050.00
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                total_str = match.group(1).replace(',', '')
                try:
                    total = float(total_str)
                    amounts["before_vat"] = total
                    amounts["total"] = total
                    logger.info(f"✅ พบยอดรวม: {total}")
                    return amounts
                except ValueError:
                    continue
        
        return amounts
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ"""
        remark_parts = []
        
        # วิธีที่ 1: หา A/C No. จากข้อความ
        ac_patterns = [
            r'A/C\s+No\.\s*[:.]?\s*([A-Z0-9]+)',  # A/C No. : TCKWATSADU
            r'A/C\s*[:.]?\s*([A-Z0-9]+)',  # A/C : TCKWATSADU
        ]
        
        for pattern in ac_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ac_no = match.group(1).strip()
                remark_parts.append(f"A/C No. : {ac_no}")
                logger.info(f"✅ พบ A/C No. สำหรับหมายเหตุ: {ac_no}")
                break
        
        # วิธีที่ 2: เพิ่มชื่อไฟล์เก่าถ้าเริ่มต้นด้วย EXC_
        if filename:
            old_filename = self._clean_filename(filename)
            if old_filename and old_filename.startswith("EXC_"):
                remark_parts.append(old_filename)
        
        if remark_parts:
            return " ".join(remark_parts)
        
        return None
    
    def extract_address(self, text: str) -> str:
        """ดึงที่อยู่"""
        # Return string ตามรูปแบบที่ manager.py คาดหวัง
        return self.ADDRESS.get("ที่อยู่รวม", "1788 อาคารสิงห์ คอมเพล็กซ์ ชั้น 20 ห้องเลขที่ 2005-2006 ถนนเพชรบุรีตัดใหม่ แขวงบางกะปิ เขตห้วยขวาง กรุงเทพมหานคร 10310")
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """ดึงข้อมูลทั้งหมดจากเอกสาร"""
        # ดึงข้อมูลพื้นฐาน
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        branch = self.extract_branch(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text)
        reference = self.extract_reference(text, filename)
        withholding_tax = self.extract_withholding_tax(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        remark = self.extract_remark(text, filename)
        address = self.extract_address(text)
        
        # สร้างชื่อไฟล์ใหม่
        new_filename = self._clean_filename(filename)
        
        # สร้างข้อมูลที่ดึงได้
        extracted_data = {
            "success": True,  # ต้องมี success field
            "company": company_name,  # สำหรับ backward compatibility
            "company_name": company_name,
            "tax_id": tax_id,
            "branch": branch,
            "date": date,
            "document_number": document_number,
            "reference": reference,
            "withholding_tax_percent": withholding_tax.get("percent"),
            "withholding_tax_amount": withholding_tax.get("amount"),
            "account_name": account_info.get("account_name") or "ค่าใช้จ่ายในการขนส่ง",
            "account_code": account_info.get("account_code"),
            "amount_before_vat": amounts.get("before_vat"),
            "vat_amount": amounts.get("vat"),
            "total_amount": amounts.get("total"),
            "remark": remark,
            "new_filename": new_filename,
            "address": address,  # string สำหรับ manager.py
            "address_details": self.ADDRESS.copy(),  # dictionary สำหรับ Excel export
            "old_filename": self._get_old_filename(filename),
            "vat_status": "no_vat"  # ไม่มีภาษีมูลค่าเพิ่ม
        }
        
        return extracted_data
    
    def _clean_filename(self, filename: str) -> Optional[str]:
        """ทำความสะอาดชื่อไฟล์ (ตัด VAT_, WHT_, None_vat, EXC_... และ .pdf)"""
        if not filename:
            return None
        
        # ตัด .pdf
        cleaned = filename.replace('.pdf', '').replace('.PDF', '')
        
        # ตัด VAT_, WHT_, None_vat
        cleaned = re.sub(r'^(VAT_|WHT_|None_vat_)', '', cleaned, flags=re.IGNORECASE)
        
        # ตัด EXC_ และข้อมูลที่อยู่ด้านหลัง (ถ้ามี)
        if 'EXC_' in cleaned.upper():
            # หา EXC_ และตัดทุกอย่างหลัง EXC_ ออก
            ex_index = cleaned.upper().find('EXC_')
            if ex_index >= 0:
                # เก็บส่วนก่อน EXC_ เท่านั้น
                cleaned = cleaned[:ex_index].rstrip('_')
        
        return cleaned if cleaned else None
    
    def _get_old_filename(self, filename: str) -> Optional[str]:
        """ดึงชื่อไฟล์เก่า (ก่อนทำความสะอาด)"""
        if not filename:
            return None
        return filename.replace('.pdf', '').replace('.PDF', '')

