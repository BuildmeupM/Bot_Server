"""
CU Lines Invoice Extractor
===========================
Extractor สำหรับดึงข้อมูลจาก CU LINES PTE LTD C/O CU LINES (THAILAND) CO.,LTD.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class CULinesExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก CU LINES PTE LTD C/O CU LINES (THAILAND) CO.,LTD."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "CU LINES PTE LTD C/O CU LINES (THAILAND) CO.,LTD.",
        "CU LINES PTE LTD",
        "CU LINES (THAILAND)",
        "CU LINES"
    ]
    
    # Tax ID
    TAX_ID = "0993000490266"
    
    # Fixed address
    ADDRESS = {
        "ที่อยู่รวม": "1168/53 20th FLOOR LUMPINI TOWER, RAMA 4 ROAD, THUNGMAHAMEK, SATHORN, BANGKOK 10120",
        "เลขที่": "",
        "อื่นๆ": "1168/53 20th FLOOR LUMPINI TOWER",
        "ถนน": "RAMA 4 ROAD",
        "ซอย": "",
        "แขวง": "THUNGMAHAMEK",
        "เขต": "SATHORN",
        "จังหวัด": "BANGKOK",
        "เลขไปรษณีย์": "10120"
    }
    
    def __init__(self):
        """Initialize CU Lines Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ CU LINES PTE LTD C/O CU LINES (THAILAND) CO.,LTD. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "CU LINES PTE LTD C/O CU LINES (THAILAND) CO.,LTD."
        2. Tax ID "0993000490266"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร CU Lines (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier.upper() in text.upper() for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0993000490266"
        has_tax_id = self.TAX_ID in text or f"TAX ID : {self.TAX_ID}" in text
        
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
        return "CU LINES PTE LTD C/O CU LINES (THAILAND) CO.,LTD."
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: Tel.(02)645-3112-3 Fax.(02)645-3114 TAX ID : 0993000490266
        patterns = [
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID : 0993000490266
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID : 0993000490266
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0993000490266
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี 0993000490266
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
        # Pattern: วันที่ DATE: 12/11/2025
        patterns = [
            r'วันที่\s+DATE\s*[:.]?\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # วันที่ DATE: 12/11/2025
            r'DATE\s*[:.]?\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # DATE: 12/11/2025
            r'วันที่\s*[:.]?\s*(\d{1,2})/(\d{1,2})/(\d{4})',  # วันที่: 12/11/2025
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
        # Pattern: เลขที่ NO.: SI2511-0443
        patterns = [
            r'เลขที่\s+NO\.\s*[:.]?\s*([A-Z0-9\-]+)',  # เลขที่ NO.: SI2511-0443
            r'เลขที่\s*[:.]?\s*([A-Z0-9\-]+)',  # เลขที่: SI2511-0443
            r'NO\.\s*[:.]?\s*([A-Z0-9\-]+)',  # NO.: SI2511-0443
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_number = match.group(1).strip()
                logger.info(f"✅ พบเลขที่เอกสาร: {doc_number}")
                return doc_number
        
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง"""
        # วิธีที่ 1: หา CULVNGB2539401 จากข้อความ
        # Pattern: CULVNGB2539401 (รูปแบบ: ตัวอักษร + ตัวเลข)
        ref_patterns = [
            r'\b([A-Z]{2,}\d{8,})\b',  # CULVNGB2539401
            r'CULVNG[A-Z0-9]+',  # CULVNGB2539401
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ref = match.group(1).strip() if match.groups() else match.group(0).strip()
                # ตรวจสอบว่าไม่ใช่คำทั่วไป
                if not any(word in ref.upper() for word in ['DOCUMENTATION', 'FEE', 'CHARGE', 'MAINTENANCE', 'INVOICE']):
                    # เพิ่ม "B/L : " ด้านหน้า
                    reference = f"B/L : {ref}"
                    logger.info(f"✅ พบอ้างอิง: {reference}")
                    return reference
        
        # วิธีที่ 2: ใช้ชื่อไฟล์เก่า (ถ้าไม่พบในข้อความ)
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
        
        # Pattern: TOTAL 7,000.00
        patterns = [
            r'TOTAL\s+([\d,]+\.?\d*)',  # TOTAL 7,000.00
            r'TOTAL\s*[:.]?\s*([\d,]+\.?\d*)',  # TOTAL : 7,000.00
            r'ยอดรวม\s*[:.]?\s*([\d,]+\.?\d*)',  # ยอดรวม: 7,000.00
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
        
        # วิธีที่ 1: หา REF. INVOICE NO. จากข้อความ
        # Pattern: REF. INVOICE NO. : IB2511-0392
        ref_patterns = [
            r'REF\.\s+INVOICE\s+NO\.\s*[:.]?\s*([A-Z0-9\-]+)',  # REF. INVOICE NO. : IB2511-0392
            r'REF\s+INVOICE\s+NO\.\s*[:.]?\s*([A-Z0-9\-]+)',  # REF INVOICE NO. : IB2511-0392
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ref_invoice = match.group(1).strip()
                remark_parts.append(f"REF. INVOICE NO. : {ref_invoice}")
                logger.info(f"✅ พบ REF. INVOICE NO. สำหรับหมายเหตุ: {ref_invoice}")
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
        return self.ADDRESS.get("ที่อยู่รวม", "1168/53 20th FLOOR LUMPINI TOWER, RAMA 4 ROAD, THUNGMAHAMEK, SATHORN, BANGKOK 10120")
    
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

