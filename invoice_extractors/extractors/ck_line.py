"""
CK Line Invoice Extractor
==========================
Extractor สำหรับดึงข้อมูลจาก บริษัท ซีเค ไลน์ จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class CKLineExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท ซีเค ไลน์ จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "บริษัท ซีเค ไลน์ จำกัด",
        "CK LINE CO.,LTD.",
        "CK LINE",
        "ซีเค ไลน์"
    ]
    
    # Tax ID
    TAX_ID = "0993000095707"
    
    def __init__(self):
        """Initialize CK Line Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ บริษัท ซีเค ไลน์ จำกัด หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท ซีเค ไลน์ จำกัด"
        2. Tax ID "0993000095707"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร CK Line (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier.upper() in text.upper() for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0993000095707"
        has_tax_id = self.TAX_ID in text
        
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
        return "บริษัท ซีเค ไลน์ จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: เลขประจำตัวผู้เสียภาษีอากร 0993000095707
        patterns = [
            r'เลขประจำตัวผู้เสียภาษีอากร\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0993000095707
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี: 0993000095707
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0993000095707
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
        ดึงวันที่จากตาราง HTML หรือ text
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            วันที่ในรูปแบบ dd/mm/yyyy หรือ None
        """
        try:
            # วิธีที่ 1: อ่านแบบบรรทัดต่อบรรทัด (line-by-line) - ยืดหยุ่นที่สุด
            lines = text.split('\n')
            found_date_keyword = False
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                # ตรวจสอบว่าบรรทัดนี้มี "=== วันที่ ===" หรือ "**วันที่**" ตรงๆ
                if '=== วันที่ ===' in line_stripped or '**วันที่**' in line_stripped:
                    found_date_keyword = True
                    logger.info(f"🔍 พบ keyword 'วันที่' ในบรรทัด {i+1}: '{line_stripped}'")
                    
                    # ตรวจสอบวันที่ในบรรทัดเดียวกันก่อน (กรณี **วันที่** 07/11/2025)
                    date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', line_stripped)
                    if date_match:
                        day = date_match.group(1).zfill(2)
                        month = date_match.group(2).zfill(2)
                        year = date_match.group(3)
                        date_str = f"{day}/{month}/{year}"
                        logger.info(f"✅ พบวันที่ในบรรทัดเดียวกัน {i+1} (keyword + data: '{line_stripped}'): {date_str}")
                        return date_str
                    
                    # หาวันที่ในบรรทัดถัดไป (ตรวจสอบ 3 บรรทัดถัดไปเพื่อรองรับ newline)
                    for j in range(i + 1, min(i + 4, len(lines))):
                        next_line = lines[j].strip()
                        logger.debug(f"   ตรวจสอบบรรทัด {j+1}: '{next_line}'")
                        # หาวันที่ในรูปแบบ dd/mm/yyyy
                        date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', next_line)
                        if date_match:
                            day = date_match.group(1).zfill(2)
                            month = date_match.group(2).zfill(2)
                            year = date_match.group(3)
                            date_str = f"{day}/{month}/{year}"
                            logger.info(f"✅ พบวันที่จากบรรทัด {i+1} (keyword: '{line_stripped}') -> บรรทัด {j+1} (data: '{next_line}'): {date_str}")
                            return date_str
                    logger.warning(f"⚠️ พบ keyword 'วันที่' แต่ไม่พบข้อมูลวันที่ในบรรทัดเดียวกันหรือบรรทัดถัดไป (บรรทัด {i+1}-{min(i+4, len(lines))})")
            
            if not found_date_keyword:
                logger.debug("🔍 ไม่พบ keyword '=== วันที่ ===' หรือ '**วันที่**' ในข้อความ")
            
            # วิธีที่ 2: ลองอ่านจาก HTML table structure
            table_pattern = r'<table[^>]*>(.*?)</table>'
            tables = re.findall(table_pattern, text, re.DOTALL | re.IGNORECASE)
            
            for table_html in tables:
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
                
                for row in rows:
                    cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
                    
                    for cell in cells:
                        cell_text = re.sub(r'<[^>]+>', '', cell)
                        cell_text = re.sub(r'\s+', ' ', cell_text).strip()
                        
                        # ตรวจสอบว่า cell มี "=== วันที่ ===" และวันที่
                        if '=== วันที่ ===' in cell_text or '=== Date ===' in cell_text:
                            # หาวันที่ใน cell นี้หรือ cell ถัดไป
                            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', cell_text)
                            if date_match:
                                day = date_match.group(1).zfill(2)
                                month = date_match.group(2).zfill(2)
                                year = date_match.group(3)
                                date_str = f"{day}/{month}/{year}"
                                logger.info(f"✅ พบวันที่จาก HTML table: {date_str}")
                                return date_str
            
            # วิธีที่ 3: ลองอ่านจาก text ธรรมดาด้วย regex patterns
            # Pattern: === วันที่ === หรือ **วันที่**
            #          07/11/2025
            date_patterns = [
                r'\*\*วันที่\*\*\s*\n\s+(\d{1,2})/(\d{1,2})/(\d{4})',  # **วันที่**\n 07/11/2025 (มีช่องว่างหน้า)
                r'\*\*วันที่\*\*\s*\n\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # **วันที่**\n 07/11/2025
                r'\*\*วันที่\*\*\s*\n+\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # **วันที่**\n\n 07/11/2025 (หลาย newline)
                r'===?\s*วันที่\s*===?\s*\n\s+(\d{1,2})/(\d{1,2})/(\d{4})',  # === วันที่ ===\n 07/11/2025 (มีช่องว่างหน้า)
                r'===?\s*วันที่\s*===?\s*\n\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # === วันที่ ===\n 07/11/2025
                r'===?\s*วันที่\s*===?\s*\n+\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # === วันที่ ===\n\n 07/11/2025 (หลาย newline)
                r'===?\s*วันที่\s*===?\s+(\d{1,2})/(\d{1,2})/(\d{4})',  # === วันที่ === 07/11/2025 (มีช่องว่าง)
                r'===?\s*วันที่\s*===?\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # === วันที่ === 07/11/2025
                r'===?\s*Date\s*===?\s*\n+\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # === Date ===\n\n 07/11/2025
            ]
            
            for date_pattern in date_patterns:
                match = re.search(date_pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    day = match.group(1).zfill(2)
                    month = match.group(2).zfill(2)
                    year = match.group(3)
                    date_str = f"{day}/{month}/{year}"
                    logger.info(f"✅ พบวันที่จาก regex pattern: {date_str}")
                    return date_str
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงวันที่: {e}")
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        logger.debug("🔍 เริ่มต้นการดึงวันที่...")
        # ตรวจสอบว่ามี keyword "=== วันที่ ===" หรือไม่
        if '=== วันที่ ===' in text or '**วันที่**' in text:
            logger.info("✅ พบ keyword '=== วันที่ ===' หรือ '**วันที่**' ในข้อความ")
        else:
            logger.debug("❌ ไม่พบ keyword '=== วันที่ ===' หรือ '**วันที่**' ในข้อความ")
        
        # วิธีที่ 1: ลองดึงจาก pattern === วันที่ ===
        date_from_table = self._extract_date_from_html_table(text)
        if date_from_table:
            logger.info(f"✅ ดึงวันที่สำเร็จ: {date_from_table}")
            return date_from_table
        
        # วิธีที่ 2: ลองอ่านจาก text ธรรมดา
        patterns = [
            r'วันที่\s*[:.]?\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # วันที่: 07/11/2025
            r'DATE\s*[:.]?\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # DATE: 07/11/2025
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                date_str = f"{day}/{month}/{year}"
                logger.info(f"✅ พบวันที่จาก pattern: {date_str}")
                return date_str
        
        logger.warning("⚠️ ไม่พบวันที่ในข้อความ")
        return None
    
    def _extract_document_number_from_html_table(self, text: str) -> Optional[str]:
        """
        ดึงเลขที่เอกสารจาก text
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            เลขที่เอกสารหรือ None
        """
        try:
            # วิธีที่ 1: อ่านแบบบรรทัดต่อบรรทัด (line-by-line) - ยืดหยุ่นที่สุด
            lines = text.split('\n')
            found_doc_keyword = False
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                # ตรวจสอบว่าบรรทัดนี้มี "=== เลขที่ ===" หรือ "**เลขที่**" ตรงๆ
                if '=== เลขที่ ===' in line_stripped or '**เลขที่**' in line_stripped:
                    found_doc_keyword = True
                    logger.info(f"🔍 พบ keyword 'เลขที่' ในบรรทัด {i+1}: '{line_stripped}'")
                    
                    # ตรวจสอบเลขที่เอกสารในบรรทัดเดียวกันก่อน (กรณี **เลขที่** CKLRRC25110171)
                    doc_match = re.search(r'\b([A-Z]{2,}[A-Z0-9]{6,})\b', line_stripped)
                    if doc_match:
                        doc_number = doc_match.group(1).strip()
                        logger.debug(f"   พบ pattern match ในบรรทัดเดียวกัน: '{doc_number}'")
                        # ตรวจสอบว่าไม่ใช่ตัวเลขล้วนๆ และไม่ใช่คำที่สั้นเกินไป
                        if not re.match(r'^\d+$', doc_number) and len(doc_number) >= 8:
                            # ตรวจสอบว่าเป็นรูปแบบเลขที่เอกสารที่ถูกต้อง (มีตัวเลขและตัวอักษรผสมกัน)
                            if re.search(r'[0-9]', doc_number) and re.search(r'[A-Z]', doc_number):
                                logger.info(f"✅ พบเลขที่เอกสารในบรรทัดเดียวกัน {i+1} (keyword + data: '{line_stripped}'): {doc_number}")
                                return doc_number
                    
                    # หาเลขที่เอกสารในบรรทัดถัดไป (ตรวจสอบ 3 บรรทัดถัดไปเพื่อรองรับ newline)
                    for j in range(i + 1, min(i + 4, len(lines))):
                        next_line = lines[j].strip()
                        logger.debug(f"   ตรวจสอบบรรทัด {j+1}: '{next_line}'")
                        # หาเลขที่เอกสารในรูปแบบ A-Z0-9 (อย่างน้อย 8 ตัว) - ต้องเริ่มต้นด้วยตัวอักษร
                        # Pattern: เริ่มต้นด้วยตัวอักษรอย่างน้อย 2 ตัว ตามด้วยตัวอักษรหรือตัวเลขอย่างน้อย 6 ตัว
                        # ใช้ \b เพื่อให้จับคำเต็มๆ ไม่จับส่วนของคำอื่น
                        doc_match = re.search(r'\b([A-Z]{2,}[A-Z0-9]{6,})\b', next_line)
                        if doc_match:
                            doc_number = doc_match.group(1).strip()
                            logger.debug(f"   พบ pattern match: '{doc_number}'")
                            # ตรวจสอบว่าไม่ใช่ตัวเลขล้วนๆ และไม่ใช่คำที่สั้นเกินไป
                            # และไม่ใช่คำทั่วไปที่อาจจะผิดพลาด (เช่น SUPAPORN)
                            if not re.match(r'^\d+$', doc_number) and len(doc_number) >= 8:
                                # ตรวจสอบว่าเป็นรูปแบบเลขที่เอกสารที่ถูกต้อง (มีตัวเลขและตัวอักษรผสมกัน)
                                if re.search(r'[0-9]', doc_number) and re.search(r'[A-Z]', doc_number):
                                    logger.info(f"✅ พบเลขที่เอกสารจากบรรทัด {i+1} (keyword: '{line_stripped}') -> บรรทัด {j+1} (data: '{next_line}'): {doc_number}")
                                    return doc_number
                                else:
                                    logger.debug(f"   ข้าม '{doc_number}' (ไม่มีทั้งตัวเลขและตัวอักษร)")
                            else:
                                logger.debug(f"   ข้าม '{doc_number}' (สั้นเกินไปหรือเป็นตัวเลขล้วนๆ)")
                    logger.warning(f"⚠️ พบ keyword 'เลขที่' แต่ไม่พบข้อมูลเลขที่เอกสารในบรรทัดเดียวกันหรือบรรทัดถัดไป (บรรทัด {i+1}-{min(i+4, len(lines))})")
            
            if not found_doc_keyword:
                logger.debug("🔍 ไม่พบ keyword '=== เลขที่ ===' หรือ '**เลขที่**' ในข้อความ")
            
            # วิธีที่ 2: ลองอ่านจาก HTML table structure
            table_pattern = r'<table[^>]*>(.*?)</table>'
            tables = re.findall(table_pattern, text, re.DOTALL | re.IGNORECASE)
            
            for table_html in tables:
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
                
                for row in rows:
                    cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
                    
                    for cell in cells:
                        cell_text = re.sub(r'<[^>]+>', '', cell)
                        cell_text = re.sub(r'\s+', ' ', cell_text).strip()
                        
                        # ตรวจสอบว่า cell มี "=== เลขที่ ===" และเลขที่เอกสาร
                        if '=== เลขที่ ===' in cell_text or '=== NO.' in cell_text.upper():
                            # หาเลขที่เอกสารใน cell นี้
                            doc_match = re.search(r'([A-Z]{2,}[A-Z0-9]{6,})', cell_text)
                            if doc_match:
                                doc_number = doc_match.group(1).strip()
                                if not re.match(r'^\d+$', doc_number):
                                    logger.info(f"✅ พบเลขที่เอกสารจาก HTML table: {doc_number}")
                                    return doc_number
            
            # วิธีที่ 3: ลองอ่านจาก text ธรรมดาด้วย regex patterns
            # Pattern: === เลขที่ === หรือ **เลขที่**
            #          CKLRRC25110171
            doc_patterns = [
                r'\*\*เลขที่\*\*\s*\n\s+([A-Z0-9]+)',  # **เลขที่**\n CKLRRC25110171 (มีช่องว่างหน้า)
                r'\*\*เลขที่\*\*\s*\n\s*([A-Z0-9]+)',  # **เลขที่**\n CKLRRC25110171
                r'\*\*เลขที่\*\*\s*\n+\s*([A-Z0-9]+)',  # **เลขที่**\n\n CKLRRC25110171 (หลาย newline)
                r'===?\s*เลขที่\s*===?\s*\n\s+([A-Z0-9]+)',  # === เลขที่ ===\n CKLRRC25110171 (มีช่องว่างหน้า)
                r'===?\s*เลขที่\s*===?\s*\n\s*([A-Z0-9]+)',  # === เลขที่ ===\n CKLRRC25110171
                r'===?\s*เลขที่\s*===?\s*\n+\s*([A-Z0-9]+)',  # === เลขที่ ===\n\n CKLRRC25110171 (หลาย newline)
                r'===?\s*เลขที่\s*===?\s+([A-Z0-9]+)',  # === เลขที่ === CKLRRC25110171 (มีช่องว่าง)
                r'===?\s*เลขที่\s*===?\s*([A-Z0-9]+)',  # === เลขที่ === CKLRRC25110171
                r'===?\s*NO\.?\s*===?\s*\n+\s*([A-Z0-9]+)',  # === NO. ===\n\n CKLRRC25110171
            ]
            
            for doc_pattern in doc_patterns:
                match = re.search(doc_pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    doc_number = match.group(1).strip()
                    # ตรวจสอบว่าไม่ใช่ตัวเลขล้วนๆ
                    if re.match(r'^\d+$', doc_number):
                        continue
                    logger.info(f"✅ พบเลขที่เอกสารจาก regex pattern: {doc_number}")
                    return doc_number
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงเลขที่เอกสาร: {e}")
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        logger.debug("🔍 เริ่มต้นการดึงเลขที่เอกสาร...")
        # ตรวจสอบว่ามี keyword "=== เลขที่ ===" หรือไม่
        if '=== เลขที่ ===' in text or '**เลขที่**' in text:
            logger.info("✅ พบ keyword '=== เลขที่ ===' หรือ '**เลขที่**' ในข้อความ")
        else:
            logger.debug("❌ ไม่พบ keyword '=== เลขที่ ===' หรือ '**เลขที่**' ในข้อความ")
        
        # วิธีที่ 1: ลองดึงจาก pattern === เลขที่ ===
        doc_number_from_table = self._extract_document_number_from_html_table(text)
        if doc_number_from_table:
            logger.info(f"✅ ดึงเลขที่เอกสารสำเร็จ: {doc_number_from_table}")
            return doc_number_from_table
        
        # วิธีที่ 2: ลองอ่านจาก text ธรรมดา
        patterns = [
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: CKLRRC25110171
            r'NO\.\s*[:.]?\s*([A-Z0-9]+)',  # NO. : CKLRRC25110171
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_number = match.group(1).strip()
                # ตรวจสอบว่าไม่ใช่ตัวเลขล้วนๆ
                if re.match(r'^\d+$', doc_number):
                    continue
                logger.info(f"✅ พบเลขที่เอกสารจาก pattern: {doc_number}")
                return doc_number
        
        logger.warning("⚠️ ไม่พบเลขที่เอกสารในข้อความ")
        return None
    
    def _extract_bl_no_from_html_table(self, text: str) -> Optional[str]:
        """
        ดึง B/L NO. จากตาราง HTML
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            B/L NO. หรือ None
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
                
                # หา header row ที่มี "B/L NO."
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
                    if 'B/L NO' in row_text:
                        # หา column index
                        for idx, cell in enumerate(cleaned_cells):
                            cell_upper = cell.upper()
                            if 'B/L NO' in cell_upper:
                                bl_index = idx
                                header_row_index = i
                                logger.debug(f"✅ พบ B/L NO. column ที่ index: {bl_index} ใน row: {header_row_index}")
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
                        if any(keyword in row_text for keyword in ['B/L NO', 'JOB NO', 'INVOICE NO', 'FEEDER', 'VESSEL']):
                            continue
                        
                        # ดึง B/L NO. จาก column ที่ตรงกัน
                        if bl_index < len(cleaned_cells):
                            bl_cell = cleaned_cells[bl_index].strip()
                            # ลบช่องว่างออก (เช่น "CKCONS A0002312" → "CKCONSA0002312")
                            bl_cell = re.sub(r'\s+', '', bl_cell)
                            if bl_cell and len(bl_cell) > 3:
                                logger.info(f"✅ พบ B/L NO. จากตาราง HTML: {bl_cell}")
                                return bl_cell
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึง B/L NO. จากตาราง HTML: {e}")
        
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง (B/L NO. จากตาราง หรือชื่อไฟล์เก่า)"""
        reference_parts = []
        
        # วิธีที่ 1: ลองดึงจาก HTML table ก่อน
        bl_no = self._extract_bl_no_from_html_table(text)
        if bl_no:
            reference_parts.append(f"B/L : {bl_no}")
            logger.info(f"✅ พบอ้างอิงจาก HTML table: B/L : {bl_no}")
        
        # วิธีที่ 2: ถ้ายังไม่พบ ให้ลองอ่านจาก text ธรรมดา
        if not bl_no:
            # Pattern: B/L NO. | CKCONS A0002312
            bl_patterns = [
                r'B/L\s+NO\.\s*\|\s*([A-Z0-9\s]+)',  # B/L NO. | CKCONS A0002312
            ]
            
            for pattern in bl_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    bl_no = match.group(1).strip()
                    # ลบช่องว่างออก
                    bl_no = re.sub(r'\s+', '', bl_no)
                    reference_parts.append(f"B/L : {bl_no}")
                    logger.info(f"✅ พบอ้างอิง: B/L : {bl_no}")
                    break
        
        # วิธีที่ 3: ถ้ายังไม่พบ ให้ใช้ชื่อไฟล์เก่า
        if not bl_no and filename:
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
    
    def _extract_total_from_html_table(self, text: str) -> Optional[float]:
        """
        ดึงยอดรวมจากตาราง HTML
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            ยอดรวมหรือ None
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
                
                # หา row ที่มี "GRAND TOTAL"
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
                    
                    # ตรวจสอบว่าเป็น row ที่มี "GRAND TOTAL"
                    row_text = ' '.join(cleaned_cells).upper()
                    if 'GRAND TOTAL' in row_text or 'จำนวนเงินรวมทั้งสิ้น' in row_text:
                        # หา cell ที่มียอดเงิน (รูปแบบ: 5,300.00)
                        for cell in cleaned_cells:
                            amount_match = re.search(r'([\d,]+\.\d{2})', cell)
                            if amount_match:
                                amount_str = amount_match.group(1).replace(',', '').strip()
                                try:
                                    total_amount = float(amount_str)
                                    logger.info(f"✅ พบยอดรวมจากตาราง HTML: {total_amount}")
                                    return total_amount
                                except ValueError:
                                    continue
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงยอดรวมจากตาราง HTML: {e}")
        
        return None
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงยอดเงิน"""
        # Pattern: จำนวนเงินรวมทั้งสิ้น GRAND TOTAL | 5,300.00
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        
        amount_before_vat = None
        vat_amount = 0.00  # ไม่มีภาษีมูลค่าเพิ่ม
        total_amount = None
        
        # วิธีที่ 1: ลองดึงจาก HTML table ก่อน
        total_from_table = self._extract_total_from_html_table(text)
        if total_from_table:
            total_amount = total_from_table
        
        # วิธีที่ 2: ถ้ายังไม่พบ ให้ลองอ่านจาก text ธรรมดา
        if total_amount is None:
            total_patterns = [
                r'จำนวนเงินรวมทั้งสิ้น\s+GRAND\s+TOTAL\s*\|?\s*([\d,]+\.?\d{2})',  # จำนวนเงินรวมทั้งสิ้น GRAND TOTAL | 5,300.00
                r'GRAND\s+TOTAL\s*\|?\s*([\d,]+\.?\d{2})',  # GRAND TOTAL | 5,300.00
                r'TOTAL\s*[:.]?\s*([\d,]+\.?\d{2})',  # TOTAL: 5,300.00
                r'ยอดรวม\s*[:.]?\s*([\d,]+\.?\d{2})',  # ยอดรวม: 5,300.00
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
        # Pattern: 628 ชั้น 3 อาคารทรัพเพิลไอ ซอยกลับขน ถนนนนทรี
        #          แขวงช่องนนทรี เขตยานนาวา กรุงเทพฯ 10120
        address_patterns = [
            r'628\s+ชั้น\s+3\s+อาคารทรัพเพิลไอ[^\n]*\n\s*แขวงช่องนนทรี[^\n]*',
            r'628\s+ชั้น\s+3\s+อาคารทรัพเพิลไอ.*?กรุงเทพฯ\s+\d{5}',
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
        return "628 ชั้น 3 อาคารทรัพเพิลไอ ซอยกลับขน ถนนนนทรี แขวงช่องนนทรี เขตยานนาวา กรุงเทพมหานคร 10120"
    
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
                
                # หา header row ที่มี "INVOICE NO."
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
                    if 'INVOICE NO' in row_text:
                        # หา column index
                        for idx, cell in enumerate(cleaned_cells):
                            cell_upper = cell.upper()
                            if 'INVOICE NO' in cell_upper:
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
                        if any(keyword in row_text for keyword in ['B/L NO', 'JOB NO', 'INVOICE NO', 'FEEDER', 'VESSEL']):
                            continue
                        
                        # ดึง INVOICE NO. จาก column ที่ตรงกัน
                        if invoice_index < len(cleaned_cells):
                            invoice_cell = cleaned_cells[invoice_index].strip()
                            # ถ้ามีรูปแบบ "CKLIN25110053FEEDER / VESSEL" ให้เอาส่วนแรก (ก่อน FEEDER)
                            if 'FEEDER' in invoice_cell.upper():
                                # หา pattern CKLIN25110053 (ก่อน FEEDER) - ต้องมีตัวอักษรและตัวเลข
                                invoice_match = re.search(r'([A-Z]{2,}[A-Z0-9]{6,})(?=FEEDER)', invoice_cell, re.IGNORECASE)
                                if invoice_match:
                                    invoice_no = invoice_match.group(1).strip()
                                    if invoice_no and len(invoice_no) > 3:
                                        logger.info(f"✅ พบ INVOICE NO. จากตาราง HTML: {invoice_no}")
                                        return invoice_no
                            else:
                                # ถ้าไม่มี FEEDER ให้ใช้ทั้งหมด แต่ลบ FEEDER / VESSEL ออกถ้ามี
                                invoice_no = invoice_cell.strip()
                                # ลบ FEEDER / VESSEL ออกถ้ามี
                                invoice_no = re.sub(r'\s*FEEDER\s*/?\s*VESSEL\s*', '', invoice_no, flags=re.IGNORECASE)
                                invoice_no = invoice_no.strip()
                                if invoice_no and len(invoice_no) > 3:
                                    logger.info(f"✅ พบ INVOICE NO. จากตาราง HTML: {invoice_no}")
                                    return invoice_no
            
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
        ดึงข้อมูลทั้งหมดจากเอกสาร CK Line
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร CK Line หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร บริษัท ซีเค ไลน์ จำกัด'
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
        building_number = '628'
        other_info = 'ชั้น 3 อาคารทรัพเพิลไอ ซอยกลับขน'
        soi = ''
        road = 'ถนนนนทรี'
        subdistrict = 'ช่องนนทรี'
        district = 'ยานนาวา'
        province = 'กรุงเทพมหานคร'
        postal_code = '10120'
        
        # ตั้งค่า skip_amount_adjustment = True เพื่อไม่ให้ระบบปรับยอดเงิน (ใช้ค่าที่อ่านได้เท่านั้น)
        # เพราะเอกสารนี้ไม่มีภาษีมูลค่าเพิ่ม
        return {
            'success': True,
            'company': 'CK_LINE',
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

