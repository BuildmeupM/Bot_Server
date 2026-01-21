"""
TikTok Shop (Thailand) Ltd. Invoice Extractor
==============================================
Extractor สำหรับดึงข้อมูลจาก TikTok Shop (Thailand) Ltd. (Head Office)

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging
from datetime import datetime

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class TikTokShopExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก TikTok Shop (Thailand) Ltd. (Head Office)"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "TikTok Shop (Thailand) Ltd.",
        "TikTok Shop (Thailand) Ltd. (Head Office)",
        "TikTok Shop",
        "ติ๊กต๊อก ช็อป (ประเทศไทย) จำกัด"
    ]
    
    # Tax ID
    TAX_ID = "0105566214176"
    
    def __init__(self):
        """Initialize TikTok Shop Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def _is_creator_commission_format(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นรูปแบบ Creator commission หรือไม่
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นรูปแบบ Creator commission
        """
        has_by_tiktok_shop = "by TikTok Shop" in text or "by tiktok shop" in text.lower()
        has_creator_commission = "Creator commission" in text or "creator commission" in text.lower()
        return has_by_tiktok_shop and has_creator_commission
    
    def _is_tiktok_shop_creator(self, text: str) -> bool:
        """
        ตรวจสอบว่า Client Name เป็น "TikTok Shop Creator" หรือไม่
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้า Client Name เป็น "TikTok Shop Creator"
        """
        # Pattern: Client Name: TikTok Shop Creator
        patterns = [
            r'Client\s+Name\s*[:.]?\s*TikTok\s+Shop\s+Creator',
            r'CLIENT\s+NAME\s*[:.]?\s*TIKTOK\s+SHOP\s+CREATOR',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ TikTok Shop (Thailand) Ltd. หรือไม่
        รองรับ 2 รูปแบบ:
        
        รูปแบบที่ 1 (เดิม):
        1. ชื่อบริษัท "TikTok Shop (Thailand) Ltd."
        2. Tax ID "0105566214176"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        รูปแบบที่ 2 (ใหม่ - Creator commission):
        1. ชื่อบริษัท "by TikTok Shop"
        2. ข้อความ "Creator commission"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร TikTok Shop (มีเงื่อนไขครบถ้วน)
        """
        if not text:
            return False
        
        # ตรวจสอบรูปแบบที่ 2 ก่อน (ใหม่ - Creator commission)
        has_by_tiktok_shop = "by TikTok Shop" in text or "by tiktok shop" in text.lower()
        has_creator_commission = "Creator commission" in text or "creator commission" in text.lower()
        has_document_type = (
            "ใบเสร็จรับเงิน" in text or 
            "ใบกำกับภาษี" in text or 
            "RECEIPT" in text.upper() or 
            "TAX INVOICE" in text.upper()
        )
        
        # ถ้าเป็นรูปแบบที่ 2 (Creator commission)
        if has_by_tiktok_shop and has_creator_commission and has_document_type:
            return True
        
        # ตรวจสอบรูปแบบที่ 1 (เดิม)
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105566214176"
        has_tax_id = (
            self.TAX_ID in text or 
            "Tax Registration Number" in text and self.TAX_ID in text
        )
        
        # ต้องมีทั้ง 3 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id and has_document_type
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        # ถ้าเป็นรูปแบบ Creator commission ให้อ่าน Client Name จากเอกสาร
        if self._is_creator_commission_format(text):
            # Pattern: Client Name: โชติวัฒน์ เลิศภาสนวัฒน์
            patterns = [
                r'Client\s+Name\s*[:.]?\s*([^\n]+?)(?=\n\s*[A-Z]|\n\s*Billing|\n\s*Tax|\n\n|$)',  # Client Name: โชติวัฒน์ เลิศภาสนวัฒน์
                r'CLIENT\s+NAME\s*[:.]?\s*([^\n]+?)(?=\n\s*[A-Z]|\n\s*BILLING|\n\s*TAX|\n\n|$)',  # CLIENT NAME: โชติวัฒน์ เลิศภาสนวัฒน์
                r'Client\s+Name\s*[:.]?\s*([^\n]+)',  # Fallback: Client Name: โชติวัฒน์ เลิศภาสนวัฒน์
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    client_name = match.group(1).strip()
                    # ตัดช่องว่างและอักขระพิเศษที่อาจติดมา
                    client_name = re.sub(r'\s+', ' ', client_name).strip()
                    if client_name:
                        logger.info(f"✅ [Extract Company Name] พบ Client Name (Creator commission): {client_name}")
                        return client_name
            
            # Fallback: ถ้าไม่พบ Client Name ให้ใช้ "TikTok Shop"
            logger.warning("⚠️ [Extract Company Name] ไม่พบ Client Name - ใช้ค่า default: TikTok Shop")
            return "TikTok Shop"
        
        return "TikTok Shop (Thailand) Ltd. (Head Office)"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # ถ้า Client Name เป็น "TikTok Shop Creator" ให้ข้ามการอ่าน
        if self._is_tiktok_shop_creator(text):
            logger.info("ℹ️ [Extract Tax ID] ข้ามการอ่านเลขที่ผู้เสียภาษี (Client Name: TikTok Shop Creator)")
            return None
        
        # ถ้าเป็นรูปแบบ Creator commission ให้อ่านจาก "Tax Number:"
        if self._is_creator_commission_format(text):
            patterns = [
                r'Tax\s+Number\s*[:.]?\s*(\d{13})',  # Tax Number: 1103702433578
                r'TAX\s+NUMBER\s*[:.]?\s*(\d{13})',  # TAX NUMBER: 1103702433578
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    tax_id = match.group(1).strip()
                    logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษี (Creator commission): {tax_id}")
                    return tax_id
        
        # Pattern: Tax Registration Number : 0105566214176 (รูปแบบเดิม)
        patterns = [
            r'Tax\s+Registration\s+Number\s*[:.]?\s*(\d{13})',  # Tax Registration Number : 0105566214176
            r'TAX\s+REGISTRATION\s+NUMBER\s*[:.]?\s*(\d{13})',  # TAX REGISTRATION NUMBER : 0105566214176
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี: 0105566214176
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id = match.group(1).strip()
                if tax_id == self.TAX_ID:
                    logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษี: {tax_id}")
                    return tax_id
        
        # Fallback: ถ้าไม่พบข้อมูล ให้ใช้ค่า default
        logger.info(f"⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา"""
        # ไม่มีสาขา (ว่าง)
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """
        ดึงวันที่ออกเอกสาร
        รูปแบบเดิม: Invoice date : Nov 25, 2025 → 25/11/2025
        รูปแบบใหม่: Receipt Date : Dec 31, 2025 → 31/12/2025
        """
        logger.info("🔍 [Extract Date] เริ่มดึงวันที่...")
        
        # ถ้าเป็นรูปแบบ Creator commission ให้อ่านจาก "Receipt Date"
        if self._is_creator_commission_format(text):
            patterns = [
                r'Receipt\s+Date\s*[:.]?\s*([A-Za-z]{3})\s+(\d{1,2}),\s*(\d{4})',  # Receipt Date : Dec 31, 2025
                r'RECEIPT\s+DATE\s*[:.]?\s*([A-Za-z]{3})\s+(\d{1,2}),\s*(\d{4})',  # RECEIPT DATE : Dec 31, 2025
            ]
            
            # Mapping เดือน
            month_map = {
                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
            }
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 3:
                        month_name = match.group(1)
                        if month_name in month_map:
                            month = month_map[month_name]
                            day = match.group(2).zfill(2)
                            year = match.group(3)
                            date_str = f"{day}/{month}/{year}"
                            logger.info(f"✅ [Extract Date] พบวันที่ (Creator commission): {date_str}")
                            return date_str
        
        # Pattern: Invoice date : Nov 25, 2025 (รูปแบบเดิม)
        patterns = [
            r'Invoice\s+date\s*[:.]?\s*([A-Za-z]{3})\s+(\d{1,2}),\s*(\d{4})',  # Invoice date : Nov 25, 2025
            r'INVOICE\s+DATE\s*[:.]?\s*([A-Za-z]{3})\s+(\d{1,2}),\s*(\d{4})',  # INVOICE DATE : Nov 25, 2025
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # วันที่: 25/11/2025
        ]
        
        # Mapping เดือน
        month_map = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    if match.group(1) in month_map:
                        # รูปแบบ: Nov 25, 2025
                        month = month_map[match.group(1)]
                        day = match.group(2).zfill(2)
                        year = match.group(3)
                        date_str = f"{day}/{month}/{year}"
                        logger.info(f"✅ [Extract Date] พบวันที่: {date_str}")
                        return date_str
                    else:
                        # รูปแบบ: 25/11/2025
                        day = match.group(1).zfill(2)
                        month = match.group(2).zfill(2)
                        year = match.group(3)
                        date_str = f"{day}/{month}/{year}"
                        logger.info(f"✅ [Extract Date] พบวันที่: {date_str}")
                        return date_str
        
        logger.warning("⚠️ [Extract Date] ไม่พบวันที่")
        return None
    
    def extract_document_number(self, text: str, filename: str = None) -> Optional[str]:
        """
        ดึงเลขที่เอกสาร
        รูปแบบเดิม: Invoice number : TTSTH20250008335084
        รูปแบบใหม่: Receipt Number : TTSTHAC20250113700665
        """
        logger.info("🔍 [Extract Document Number] เริ่มดึงเลขที่เอกสาร...")
        
        # ถ้าเป็นรูปแบบ Creator commission ให้อ่านจาก "Receipt Number"
        if self._is_creator_commission_format(text):
            patterns = [
                r'Receipt\s+Number\s*[:.]?\s*([A-Z0-9]+)',  # Receipt Number : TTSTHAC20250113700665
                r'RECEIPT\s+NUMBER\s*[:.]?\s*([A-Z0-9]+)',  # RECEIPT NUMBER : TTSTHAC20250113700665
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    doc_num = match.group(1).strip()
                    if len(doc_num) >= 10:
                        logger.info(f"✅ [Extract Document Number] พบเลขที่เอกสาร (Creator commission): {doc_num}")
                        return doc_num
        
        # Pattern: Invoice number : TTSTH20250008335084 (รูปแบบเดิม)
        patterns = [
            r'Invoice\s+number\s*[:.]?\s*([A-Z0-9]+)',  # Invoice number : TTSTH20250008335084
            r'INVOICE\s+NUMBER\s*[:.]?\s*([A-Z0-9]+)',  # INVOICE NUMBER : TTSTH20250008335084
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: TTSTH20250008335084
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                if len(doc_num) >= 10:
                    logger.info(f"✅ [Extract Document Number] พบเลขที่เอกสาร: {doc_num}")
                    return doc_num
        
        logger.warning("⚠️ [Extract Document Number] ไม่พบเลขที่เอกสาร")
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงข้อมูลอ้างอิง"""
        # ไม่มีข้อมูลอ้างอิง (ว่าง)
        return None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี"""
        # ไม่มีข้อมูลบัญชี (ว่าง)
        return {'account_name': None, 'account_code': None}
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        # ไม่มีข้อมูลหัก ณ ที่จ่าย (ว่าง)
        return {'withholding_tax_percent': None, 'withholding_tax_amount': None}
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ"""
        # ไม่มีหมายเหตุ (ว่าง)
        return None
    
    def parse_html_table(self, text: str) -> Dict[str, str]:
        """
        แปลงข้อมูลจาก HTML table structure หรือ pipe-separated text
        อ่านทีละบรรทัด
        """
        result = {}
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Pattern 1: Key ฿Value หรือ Key Value (เช่น: Subtotal (excluding VAT) ฿1,439.11)
            # ลบ ฿ ออกก่อน แล้วแยก key และ value
            baht_match = re.search(r'^(.+?)\s*฿\s*([\d,]+\.?\d*)$', line)
            if baht_match:
                key = baht_match.group(1).strip()
                value = baht_match.group(2).strip()
                if value:
                    result[key] = value
                    logger.info(f"📋 [Parse HTML Table] พบ: {key} = {value}")
                    continue
            
            # Pattern 2: Key : Value หรือ Key Value (ไม่มี ฿)
            colon_match = re.search(r'^(.+?)\s*[:.]?\s*(.+)$', line)
            if colon_match:
                key = colon_match.group(1).strip()
                value = colon_match.group(2).strip()
                # ข้ามถ้า value เป็น empty หรือเป็น header
                if value and not any(keyword in line.upper() for keyword in ['DESCRIPTION', 'AMOUNT IN THB', 'TAX AMOUNT']):
                    result[key] = value
                    logger.info(f"📋 [Parse HTML Table] พบ: {key} = {value}")
            
            # Pattern 3: Pipe-separated values
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    # ถ้าเป็น header row ให้ข้าม
                    if any(keyword in line.upper() for keyword in ['DESCRIPTION', 'AMOUNT', 'TAX', 'HEADER']):
                        continue
                    # ถ้าเป็น data row ให้เก็บข้อมูล
                    for i, part in enumerate(parts):
                        if part and not part.startswith('-'):
                            result[f'Column_{i}'] = part
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        รูปแบบเดิม:
        - Subtotal (excluding VAT) ฿1,439.11
        - Total VAT 7% ฿100.74
        - Total amount (including VAT ) ฿1,539.85
        
        รูปแบบใหม่ (Creator commission):
        - Total Amount ฿4,179.22 → ยอดก่อนภาษีมูลค่าเพิ่ม = 4,179.22, VAT = 0.00, ยอดหลัง = 4,179.22
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        logger.info("🔍 [Extract Amounts] เริ่มดึงยอดเงิน...")
        
        # ถ้าเป็นรูปแบบ Creator commission ให้อ่านจาก "Total Amount"
        if self._is_creator_commission_format(text):
            patterns = [
                r'Total\s+Amount\s*฿\s*([\d,]+\.?\d*)',  # Total Amount ฿4,179.22
                r'TOTAL\s+AMOUNT\s*฿\s*([\d,]+\.?\d*)',  # TOTAL AMOUNT ฿4,179.22
                r'Total\s+Amount\s*([\d,]+\.?\d*)',  # Total Amount 4,179.22
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '').strip()
                        amount = float(amount_str)
                        # สำหรับรูปแบบ Creator commission: ยอดก่อน VAT = ยอดหลัง VAT = Total Amount, VAT = 0.00
                        result['amount_before_vat'] = amount
                        result['vat_amount'] = 0.00
                        result['total_amount'] = amount
                        logger.info(f"✅ [Extract Amounts] พบยอดเงิน (Creator commission): {amount}, VAT: 0.00")
                        return result
                    except (ValueError, IndexError):
                        continue
        
        # อ่านข้อมูลจาก HTML table structure (รูปแบบเดิม)
        table_data = self.parse_html_table(text)
        
        # ค้นหายอดก่อนภาษีมูลค่าเพิ่ม: Subtotal (excluding VAT)
        for key, value in table_data.items():
            if 'subtotal' in key.lower() and 'excluding' in key.lower() and 'vat' in key.lower():
                try:
                    amount_str = value.replace('฿', '').replace(',', '').replace(' ', '').strip()
                    amount = float(amount_str)
                    result['amount_before_vat'] = amount
                    logger.info(f"✅ [Extract Amounts] พบยอดก่อนภาษีมูลค่าเพิ่ม: {amount}")
                    break
                except (ValueError, AttributeError):
                    continue
        
        # ค้นหายอดภาษีมูลค่าเพิ่ม: Total VAT 7%
        for key, value in table_data.items():
            if 'total' in key.lower() and 'vat' in key.lower() and '7%' in key.lower():
                try:
                    amount_str = value.replace('฿', '').replace(',', '').replace(' ', '').strip()
                    amount = float(amount_str)
                    result['vat_amount'] = amount
                    logger.info(f"✅ [Extract Amounts] พบยอดภาษีมูลค่าเพิ่ม: {amount}")
                    break
                except (ValueError, AttributeError):
                    continue
        
        # ค้นหายอดหลังบวกภาษีมูลค่าเพิ่ม: Total amount (including VAT )
        for key, value in table_data.items():
            if 'total' in key.lower() and 'amount' in key.lower() and 'including' in key.lower() and 'vat' in key.lower():
                try:
                    amount_str = value.replace('฿', '').replace(',', '').replace(' ', '').strip()
                    amount = float(amount_str)
                    result['total_amount'] = amount
                    logger.info(f"✅ [Extract Amounts] พบยอดหลังบวกภาษีมูลค่าเพิ่ม: {amount}")
                    break
                except (ValueError, AttributeError):
                    continue
        
        # Fallback: ใช้ regex patterns ถ้าไม่พบจาก table
        if result['amount_before_vat'] is None:
            patterns = [
                r'Subtotal\s+\(excluding\s+VAT\)\s*฿\s*([\d,]+\.?\d*)',  # Subtotal (excluding VAT) ฿1,439.11
                r'Subtotal\s+\(excluding\s+VAT\)\s*([\d,]+\.?\d*)',  # Subtotal (excluding VAT) 1,439.11
                r'SUBTOTAL\s+\(EXCLUDING\s+VAT\)\s*฿?\s*([\d,]+\.?\d*)',
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '').strip()
                        amount = float(amount_str)
                        result['amount_before_vat'] = amount
                        logger.info(f"✅ [Extract Amounts] พบยอดก่อนภาษีมูลค่าเพิ่ม (regex): {amount}")
                        break
                    except (ValueError, IndexError):
                        continue
        
        if result['vat_amount'] is None:
            patterns = [
                r'Total\s+VAT\s+7%\s*฿\s*([\d,]+\.?\d*)',  # Total VAT 7% ฿100.74
                r'Total\s+VAT\s+7%\s*([\d,]+\.?\d*)',  # Total VAT 7% 100.74
                r'TOTAL\s+VAT\s+7%\s*฿?\s*([\d,]+\.?\d*)',
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '').strip()
                        amount = float(amount_str)
                        result['vat_amount'] = amount
                        logger.info(f"✅ [Extract Amounts] พบยอดภาษีมูลค่าเพิ่ม (regex): {amount}")
                        break
                    except (ValueError, IndexError):
                        continue
        
        if result['total_amount'] is None:
            patterns = [
                r'Total\s+amount\s+\(including\s+VAT\s*\)\s*฿\s*([\d,]+\.?\d*)',  # Total amount (including VAT ) ฿1,539.85
                r'Total\s+amount\s+\(including\s+VAT\s*\)\s*([\d,]+\.?\d*)',  # Total amount (including VAT ) 1,539.85
                r'TOTAL\s+AMOUNT\s+\(INCLUDING\s+VAT\s*\)\s*฿?\s*([\d,]+\.?\d*)',
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '').strip()
                        amount = float(amount_str)
                        result['total_amount'] = amount
                        logger.info(f"✅ [Extract Amounts] พบยอดหลังบวกภาษีมูลค่าเพิ่ม (regex): {amount}")
                        break
                    except (ValueError, IndexError):
                        continue
        
        if result['amount_before_vat'] is None and result['vat_amount'] is None and result['total_amount'] is None:
            logger.warning("⚠️ [Extract Amounts] ไม่พบยอดเงิน")
        
        return result
    
    def extract_address(self, text: str) -> Dict[str, Optional[str]]:
        """
        ดึงข้อมูลที่อยู่
        รูปแบบเดิม: Address: No. 1 Park Silom Building, 9th-10th Floors, Convent Road, Silom Sub-district, Bangrak District, Bangkok, 10500
        รูปแบบใหม่: Billing Address: 1514 ซ.เพชรเกษม 55/2 แขวงหลักสอง เขตบางแค กรุงเทพมหานคร
        """
        logger.info("🔍 [Extract Address] เริ่มดึงข้อมูลที่อยู่...")
        
        # ถ้า Client Name เป็น "TikTok Shop Creator" ให้ข้ามการอ่านที่อยู่
        if self._is_tiktok_shop_creator(text):
            logger.info("ℹ️ [Extract Address] ข้ามการอ่านที่อยู่ (Client Name: TikTok Shop Creator)")
            return {
                'address_full': None,
                'address_number': None,
                'address_other': None,
                'address_road': None,
                'address_soi': None,
                'address_subdistrict': None,
                'address_district': None,
                'address_province': None,
                'address_postal_code': None
            }
        
        # ถ้าเป็นรูปแบบ Creator commission ให้อ่านจาก "Billing Address"
        if self._is_creator_commission_format(text):
            # Pattern: Billing Address: 1514 ซ.เพชรเกษม 55/2 แขวงหลักสอง เขตบางแค กรุงเทพมหานคร
            billing_address_pattern = r'Billing\s+Address\s*[:.]?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n[A-Z]|\n\n|$)'
            match = re.search(billing_address_pattern, text, re.IGNORECASE | re.MULTILINE)
            
            if match:
                address_full = match.group(1).strip()
                logger.info(f"✅ [Extract Address] พบที่อยู่ (Creator commission): {address_full}")
                
                # แยกข้อมูลที่อยู่
                # ตัวอย่าง: 1514 ซ.เพชรเกษม 55/2 แขวงหลักสอง เขตบางแค กรุงเทพมหานคร
                # อื่นๆ: 1514
                # ซอย: เพชรเกษม 55/2
                # แขวง: หลักสอง
                # เขต: บางแค
                # จังหวัด: กรุงเทพมหานคร
                
                # หาเลขที่ (ตัวเลขที่อยู่ต้น)
                address_number_match = re.search(r'^(\d+)', address_full)
                address_number = address_number_match.group(1) if address_number_match else None
                
                # หาส่วนอื่นๆ (เลขที่)
                address_other = address_number if address_number else None
                
                # หาซอย (ซ. หรือ ซอย)
                # ตัวอย่าง: ซ.เพชรเกษม 55/2 หรือ ซอยเพชรเกษม 55/2
                soi_match = re.search(r'ซ\.?\s*([^แ]+?)(?=\s*แขวง|\s*เขต|\s*จังหวัด|$)', address_full)
                if not soi_match:
                    # ลองหาแบบ "ซอย" (ไม่มีจุด)
                    soi_match = re.search(r'ซอย\s*([^แ]+?)(?=\s*แขวง|\s*เขต|\s*จังหวัด|$)', address_full)
                address_soi = soi_match.group(1).strip() if soi_match else None
                
                # หาแขวง
                subdistrict_match = re.search(r'แขวง\s*([^เข]+?)(?=\s*เขต|\s*จังหวัด|$)', address_full)
                address_subdistrict = subdistrict_match.group(1).strip() if subdistrict_match else None
                
                # หาเขต
                district_match = re.search(r'เขต\s*([^จ]+?)(?=\s*จังหวัด|$)', address_full)
                address_district = district_match.group(1).strip() if district_match else None
                
                # หาจังหวัด (ส่วนท้ายสุด)
                province_match = re.search(r'จังหวัด\s*([^\s]+(?:\s+[^\s]+)*)', address_full)
                if not province_match:
                    # ถ้าไม่มีคำว่า "จังหวัด" ให้หาจากส่วนท้ายสุด
                    province_match = re.search(r'([ก-๙]+(?:\s+[ก-๙]+)*)$', address_full)
                address_province = province_match.group(1).strip() if province_match else None
                
                result = {
                    'address_full': address_full,
                    'address_number': None,  # เลขที่ (ว่าง)
                    'address_other': address_other,  # อื่นๆ: 1514
                    'address_road': None,  # ถนน (ว่าง)
                    'address_soi': address_soi,  # ซอย: เพชรเกษม 55/2
                    'address_subdistrict': address_subdistrict,  # แขวง: หลักสอง
                    'address_district': address_district,  # เขต: บางแค
                    'address_province': address_province,  # จังหวัด: กรุงเทพมหานคร
                    'address_postal_code': None  # เลขไปรษณีย์ (ว่าง)
                }
                
                logger.info(f"✅ [Extract Address] แยกข้อมูลที่อยู่สำเร็จ:")
                logger.info(f"   - อื่นๆ: {result['address_other']}")
                logger.info(f"   - ซอย: {result['address_soi']}")
                logger.info(f"   - แขวง: {result['address_subdistrict']}")
                logger.info(f"   - เขต: {result['address_district']}")
                logger.info(f"   - จังหวัด: {result['address_province']}")
                
                return result
        
        # Pattern: Address: No. 1 Park Silom Building, 9th-10th Floors, Convent Road, Silom Sub-district, Bangrak District, Bangkok, 10500 (รูปแบบเดิม)
        address_pattern = r'Address\s*[:.]?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n[A-Z]|\n\n|$)'
        match = re.search(address_pattern, text, re.IGNORECASE | re.MULTILINE)
        
        if match:
            address_full = match.group(1).strip()
            logger.info(f"✅ [Extract Address] พบที่อยู่: {address_full[:100]}...")
        
        # กำหนดค่าตามที่ระบุ (รูปแบบเดิม)
        result = {
            'address_full': 'No. 1 Park Silom Building, 9th-10th Floors, Convent Road, Silom Sub-district, Bangrak District, Bangkok, 10500',
            'address_number': '1',  # เลขที่
            'address_other': 'Park Silom Building, 9th-10th Floors',  # อื่นๆ
            'address_road': 'Convent Road',  # ถนน
            'address_soi': None,  # ซอย
            'address_subdistrict': 'Silom Sub-district',  # แขวง
            'address_district': 'Bangrak District',  # เขต
            'address_province': 'Bangkok',  # จังหวัด
            'address_postal_code': '10500'  # เลขไปรษณีย์
        }
        
        return result
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจสอบประเภทเอกสาร
        Returns:
            1 = มีภาษีมูลค่าเพิ่ม (VAT)
            2 = ไม่มีภาษีมูลค่าเพิ่ม (NoneVat)
        """
        # ถ้าเป็นรูปแบบ Creator commission ให้คืนค่า 2 (ไม่มีภาษีมูลค่าเพิ่ม)
        if self._is_creator_commission_format(text):
            return 2
        
        # เอกสารนี้มีภาษีมูลค่าเพิ่ม (VAT > 0)
        if amounts.get('vat_amount') and amounts.get('vat_amount', 0) > 0:
            return 1
        return 1  # Default: มีภาษีมูลค่าเพิ่ม
    
    def clean_filename(self, filename: str) -> str:
        """
        ทำความสะอาดชื่อไฟล์
        จาก: TTSTH20250008335084.pdf
        เป็น: ค่าบริการ_Tiktok
        
        สำหรับรูปแบบ Creator commission: ตัด VAT_ WHT _ None_vat ออกจากชื่อไฟล์
        """
        if not filename:
            return ""
        
        # ลบ .pdf
        cleaned = filename.replace('.pdf', '').replace('.PDF', '')
        
        # ตัด VAT_ WHT _ None_vat ออกจากชื่อไฟล์ (สำหรับรูปแบบ Creator commission)
        cleaned = re.sub(r'[_\s]*(VAT|WHT|None_vat|NoneVat|NONE_VAT)[_\s]*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'[_\s]+', '_', cleaned)  # แทนที่ช่องว่างหลายตัวด้วย _
        cleaned = cleaned.strip('_')  # ตัด _ ที่หัวท้าย
        
        # ถ้าเป็นเลขที่เอกสาร TikTok Shop ให้แปลงเป็นชื่อที่กำหนด
        # ตัวอย่าง: TTSTH20250008335084 -> ค่าบริการ_Tiktok
        if cleaned.startswith('TTSTH') or 'TikTok' in cleaned or 'tiktok' in cleaned.lower():
            return "ค่าบริการ_Tiktok"
        
        return cleaned
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์
            filepath: path ของไฟล์
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        logger.info("=" * 80)
        logger.info(f"🔍 [TikTok Shop] เริ่มดึงข้อมูลจากเอกสาร...")
        logger.info("=" * 80)
        
        # ดึงข้อมูลพื้นฐาน
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        branch = self.extract_branch(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text, filename)
        reference = self.extract_reference(text, filename)
        account_info = self.extract_account_info(text)
        withholding_tax = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        address = self.extract_address(text)
        amounts = self.extract_amounts(text)
        document_type = self.detect_document_type(text, amounts, withholding_tax)
        new_filename = self.clean_filename(filename) if filename else None
        
        # สร้างที่อยู่รวม (string) สำหรับ manager
        address_full_str = address.get('address_full') or ''
        
        # สร้าง dictionary ผลลัพธ์
        result = {
            'success': True,
            'company': company_name,
            'company_name': company_name,  # เพิ่ม field นี้สำหรับ manager
            'old_filename': filename,
            'filepath': filepath,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'reference': reference,
            'account_name': account_info.get('account_name'),
            'account_code': account_info.get('account_code'),
            'withholding_tax_percent': withholding_tax.get('withholding_tax_percent'),
            'withholding_tax_amount': withholding_tax.get('withholding_tax_amount'),
            'amount_before_vat': amounts.get('amount_before_vat'),
            'vat_amount': amounts.get('vat_amount'),
            'total_amount': amounts.get('total_amount'),
            'remark': remark,
            'new_filename': new_filename,
            'document_type': document_type,
            'skip_amount_adjustment': False,  # มี VAT ต้องคำนวณ
            # ที่อยู่
            'address': address_full_str,  # เพิ่ม field นี้สำหรับ manager (string)
            'address_full': address.get('address_full'),
            'address_number': address.get('address_number'),
            'address_other': address.get('address_other'),
            'address_road': address.get('address_road'),
            'address_soi': address.get('address_soi'),
            'address_subdistrict': address.get('address_subdistrict'),
            'address_district': address.get('address_district'),
            'address_province': address.get('address_province'),
            'address_postal_code': address.get('address_postal_code'),
        }
        
        logger.info("=" * 80)
        logger.info(f"✅ [TikTok Shop] ดึงข้อมูลเสร็จสิ้น")
        logger.info(f"   - บริษัท: {company_name}")
        logger.info(f"   - เลขที่ผู้เสียภาษี: {tax_id}")
        logger.info(f"   - วันที่: {date}")
        logger.info(f"   - เลขที่เอกสาร: {document_number}")
        logger.info(f"   - ยอดก่อนภาษีมูลค่าเพิ่ม: {amounts.get('amount_before_vat')}")
        logger.info(f"   - ยอดภาษีมูลค่าเพิ่ม: {amounts.get('vat_amount')}")
        logger.info(f"   - ยอดหลังบวกภาษีมูลค่าเพิ่ม: {amounts.get('total_amount')}")
        logger.info("=" * 80)
        
        return result

