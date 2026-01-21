"""
Marvel Vision Invoice Extractor
================================
Extractor สำหรับดึงข้อมูลจาก บริษัท มาร์เวล วิชชั่น จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class MarvelVisionExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท มาร์เวล วิชชั่น จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "บริษัท มาร์เวล วิชชั่น จำกัด",
        "มาร์เวล วิชชั่น",
        "MARVEL VISION",
        "MARVEL"
    ]
    
    # Tax ID
    TAX_ID = "0105553009455"
    
    def __init__(self):
        """Initialize Marvel Vision Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ บริษัท มาร์เวล วิชชั่น จำกัด หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท มาร์เวล วิชชั่น จำกัด"
        2. Tax ID "0105553009455"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Marvel Vision (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105553009455"
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
        return "บริษัท มาร์เวล วิชชั่น จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: เลขประจำตัวผู้เสียภาษี : 0105553009455
        patterns = [
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี : 0105553009455
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร : 0105553009455
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID: 0105553009455
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0105553009455
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
        # ไม่มีสาขา (ว่าง)
        return None
    
    def parse_html_table(self, text: str) -> Dict[str, str]:
        """
        Parse ข้อมูลจากตาราง HTML
        หา pattern เช่น: <td>ว/ด/ป</td><td>07/11/2025</td>
        หรือ: <td>เลขที่</td><td>SIVW25110023</td>
        หรือ: ว/ด/ป | 07/11/2025 (text format)
        
        Returns:
            Dictionary ที่มี key-value จากตาราง
        """
        result = {}
        
        # Pattern สำหรับหา <td>key</td><td>value</td>
        # รองรับ whitespace และ <br/> tags
        pattern = r'<td[^>]*>([^<]+(?:<[^>]+>)*[^<]*)</td>\s*<td[^>]*>([^<]+(?:<[^>]+>)*[^<]*)</td>'
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            key = re.sub(r'<[^>]+>', '', match[0]).strip()
            value = re.sub(r'<[^>]+>', '', match[1]).strip()
            
            # ทำความสะอาด key (ลบ | และ whitespace แต่เก็บตัวอักษรและตัวเลข)
            # เช่น "จำนวนเงิน(AMOUNT)" -> "จำนวนเงิน(AMOUNT)"
            key = re.sub(r'[|\s]+', '', key)
            
            # ทำความสะอาด value (ลบ "ว/ด/ป" ออกถ้ามี)
            value = re.sub(r'ว/ด/ป\s*', '', value, flags=re.IGNORECASE).strip()
            
            if key and value:
                result[key] = value
                logger.info(f"✅ Parse HTML table: {key} = {value[:100]}...")
        
        # Fallback: ลองหาแบบ text format (| separated)
        # เช่น: ว/ด/ป | 07/11/2025
        # หรือ: เลขที่ | SIVW25110023
        # หรือ: จำนวนเงิน (AMOUNT) | 27,102.80
        # หรือ: จำนวนเงินรวมทั้งสิ้น (GRAND TOTAL) | 29,000.00
        lines = text.split('\n')
        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    
                    # ทำความสะอาด key (ลบ whitespace ทั้งหมดเพื่อให้ตรงกับ key จาก HTML)
                    # เช่น "จำนวนเงิน (AMOUNT)" -> "จำนวนเงิน(AMOUNT)"
                    key_clean = re.sub(r'\s+', '', key)
                    
                    # ทำความสะอาด value (ลบ "ว/ด/ป" ออกถ้ามี)
                    value = re.sub(r'ว/ด/ป\s*', '', value, flags=re.IGNORECASE).strip()
                    
                    if key_clean and value:
                        # ใช้ key_clean เป็น key เพื่อให้ตรงกับ key จาก HTML table
                        result[key_clean] = value
                        logger.info(f"✅ Parse text table: {key_clean} = {value[:100]}...")
        
        return result
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # อ่านจากตาราง HTML: <td>ว/ด/ป</td><td>07/11/2025</td>
        table_data = self.parse_html_table(text)
        
        # ลองหาจากตารางก่อน
        if 'ว/ด/ป' in table_data:
            date_str = table_data['ว/ด/ป']
            # ลบข้อความที่ติดมา เช่น "07/11/2025พนักงานขาย" -> "07/11/2025"
            # หาวันที่ในรูปแบบ dd/mm/yyyy (ต้องเป็นตัวเลขแรกที่เจอ)
            match = re.search(r'^(\d{2}/\d{2}/\d{4})', date_str)
            if match:
                date_found = match.group(1)
                logger.info(f"✅ พบวันที่จากตาราง: {date_found} (จาก: {date_str})")
                return date_found
        
        # Fallback: ลองหา pattern อื่นๆ จาก text format
        # Pattern: "ว/ด/ป | 07/11/2025"
        patterns = [
            r'ว/ด/ป\s*\|\s*(\d{2}/\d{2}/\d{4})',  # ว/ด/ป | 07/11/2025
            r'ว/ด/ป\s*[|:]\s*(\d{2}/\d{2}/\d{4})',  # ว/ด/ป | 07/11/2025 หรือ ว/ด/ป : 07/11/2025
            r'วันที่\s*[:.]?\s*(\d{2}/\d{2}/\d{4})',  # วันที่: 07/11/2025
            r'Date\s*[:.]?\s*(\d{2}/\d{2}/\d{4})',  # Date: 07/11/2025
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_found = match.group(1).strip()
                logger.info(f"✅ พบวันที่: {date_found}")
                return date_found
        
        logger.warning("⚠️ ไม่พบวันที่")
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # อ่านจากตาราง HTML: <td>เลขที่</td><td>SIVW25110023</td>
        table_data = self.parse_html_table(text)
        
        # ลองหาจากตารางก่อน
        if 'เลขที่' in table_data:
            doc_num = table_data['เลขที่']
            if doc_num:
                # ลบ "ว/ด/ป" ออก (ถ้ามี)
                doc_num = re.sub(r'ว/ด/ป\s*', '', doc_num, flags=re.IGNORECASE).strip()
                logger.info(f"✅ พบเลขที่เอกสารจากตาราง: {doc_num}")
                return doc_num
        
        # Fallback: ลองหา pattern อื่นๆ
        patterns = [
            r'เลขที่\s*[|:]\s*([A-Z0-9]+)',  # เลขที่ | SIVW25110023
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # Document No.: SIVW25110023
            r'Invoice\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # Invoice No.: SIVW25110023
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                # ลบ "ว/ด/ป" ออก (ถ้ามี)
                doc_num = re.sub(r'ว/ด/ป\s*', '', doc_num, flags=re.IGNORECASE).strip()
                logger.info(f"✅ พบเลขที่เอกสาร: {doc_num}")
                return doc_num
        
        logger.warning("⚠️ ไม่พบเลขที่เอกสาร")
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง"""
        # อ้างอิงว่าง
        return None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # ชื่อบัญชีว่าง
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี
                'vat_amount': float,          # ยอดภาษี
                'total_amount': float         # ยอดรวม
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # Parse ข้อมูลจากตาราง HTML ก่อน
        table_data = self.parse_html_table(text)
        logger.info(f"🔍 Table data keys: {list(table_data.keys())[:20]}...")  # แสดงแค่ 20 keys แรก
        
        # 1. ยอดก่อนภาษี: 27,102.80
        # จาก OCR text: "เงินมัดจำเลขที่ (DEPOSIT NO.) | จำนวนเงิน (AMOUNT) | 27,102.80"
        # หรือจากตาราง HTML: "จำนวนเงิน(AMOUNT) = 27,102.80จำนวนเงินหลังหักมัดจำ"
        # ลองหา key ที่มี "จำนวนเงิน" และ "AMOUNT"
        amount_key = None
        for key in table_data.keys():
            if 'จำนวนเงิน' in key and 'AMOUNT' in key.upper():
                amount_key = key
                break
        
        if amount_key:
            amount_str = table_data[amount_key].replace(',', '').strip()
            # ลบข้อความที่ติดมา เช่น "27,102.80จำนวนเงินหลังหักมัดจำ" -> "27,102.80"
            # หาเฉพาะตัวเลขแรกที่เจอ
            match = re.search(r'^([\d,]+\.?\d*)', amount_str)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    result['amount_before_vat'] = float(amount_str)
                    logger.info(f"✅ พบยอดก่อนภาษีจากตาราง ({amount_key}): {result['amount_before_vat']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองอ่านจาก text format โดยตรง
        # Pattern: "เงินมัดจำเลขที่ (DEPOSIT NO.) | จำนวนเงิน (AMOUNT) | 27,102.80"
        if result['amount_before_vat'] is None:
            # หา pattern ที่มี 3 columns: "เงินมัดจำเลขที่ (DEPOSIT NO.) | จำนวนเงิน (AMOUNT) | 27,102.80"
            pattern = r'เงินมัดจำเลขที่[^|]*\|\s*จำนวนเงิน\s*\(AMOUNT\)\s*\|\s*([\d,]+\.?\d*)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    result['amount_before_vat'] = float(amount_str)
                    logger.info(f"✅ พบยอดก่อนภาษีจาก text format: {result['amount_before_vat']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ
        if result['amount_before_vat'] is None:
            patterns_before_vat = [
                r'จำนวนเงิน\s*\(AMOUNT\)\s*[|:]\s*([\d,]+\.?\d*)',  # จำนวนเงิน (AMOUNT) | 27,102.80
                r'จำนวนเงิน\s*\(AMOUNT\)\s*=\s*([\d,]+\.?\d*)',  # จำนวนเงิน (AMOUNT) = 27,102.80
                r'\*\*เงินมัดจำเลขที่[^*]*\*\*\s*จำนวนเงิน\s*\(AMOUNT\)\s*([\d,]+\.?\d*)',  # **เงินมัดจำเลขที่: (DEPOSIT NO.)** จำนวนเงิน (AMOUNT) 27,102.80
                r'AMOUNT\s*[:.]?\s*([\d,]+\.?\d*)',  # AMOUNT: 27,102.80
            ]
            
            for pattern in patterns_before_vat:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    try:
                        result['amount_before_vat'] = float(amount_str)
                        logger.info(f"✅ พบยอดก่อนภาษี: {result['amount_before_vat']}")
                        break
                    except ValueError:
                        continue
        
        # 2. ยอดภาษี: 1,897.20
        # จาก OCR text: "จำนวนเงินหลังหักมัดจำ (TOTAL AMOUNT AFTER DEPOSIT) | ภาษีมูลค่าเพิ่ม (VAT) 7% | 1,897.20"
        # หรือจากตาราง HTML: "ภาษีมูลค่าเพิ่ม(VAT)7% = 1,897.20สองหมื่นเก้าพันบาทถ้วน"
        vat_key = None
        for key in table_data.keys():
            if 'ภาษีมูลค่าเพิ่ม' in key and ('VAT' in key.upper() or '7%' in key):
                vat_key = key
                break
        
        if vat_key:
            vat_str = table_data[vat_key].replace(',', '').strip()
            # ลบข้อความที่ติดมา เช่น "1,897.20สองหมื่นเก้าพันบาทถ้วน" -> "1,897.20"
            # หาเฉพาะตัวเลขแรกที่เจอ
            match = re.search(r'^([\d,]+\.?\d*)', vat_str)
            if match:
                vat_str = match.group(1).replace(',', '')
                try:
                    result['vat_amount'] = float(vat_str)
                    logger.info(f"✅ พบยอดภาษีจากตาราง ({vat_key}): {result['vat_amount']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองอ่านจาก text format โดยตรง
        # Pattern: "จำนวนเงินหลังหักมัดจำ (TOTAL AMOUNT AFTER DEPOSIT) | ภาษีมูลค่าเพิ่ม (VAT) 7% | 1,897.20"
        if result['vat_amount'] is None:
            # หา pattern ที่มี 3 columns: "จำนวนเงินหลังหักมัดจำ ... | ภาษีมูลค่าเพิ่ม (VAT) 7% | 1,897.20"
            pattern = r'จำนวนเงินหลังหักมัดจำ[^|]*\|\s*ภาษีมูลค่าเพิ่ม\s*\(VAT\)\s*7%\s*\|\s*([\d,]+\.?\d*)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vat_str = match.group(1).replace(',', '')
                try:
                    result['vat_amount'] = float(vat_str)
                    logger.info(f"✅ พบยอดภาษีจาก text format: {result['vat_amount']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ
        if result['vat_amount'] is None:
            patterns_vat = [
                r'ภาษีมูลค่าเพิ่ม\s*\(VAT\)\s*7%\s*[|:]\s*([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม (VAT) 7% | 1,897.20
                r'ภาษีมูลค่าเพิ่ม\s*\(VAT\)\s*7%\s*=\s*([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม (VAT) 7% = 1,897.20
                r'===?\s*จำนวนเงินหลังหักมัดจำ\s*\(TOTAL\s+AMOUNT\s+AFTER\s+DEPOSIT\)\s*===?\s*([\d,]+\.?\d*)',  # === จำนวนเงินหลังหักมัดจำ (TOTAL AMOUNT AFTER DEPOSIT) === 1,897.20
                r'จำนวนเงินหลังหักมัดจำ\s*\(TOTAL\s+AMOUNT\s+AFTER\s+DEPOSIT\)\s*[|:]\s*([\d,]+\.?\d*)',  # จำนวนเงินหลังหักมัดจำ (TOTAL AMOUNT AFTER DEPOSIT) | 1,897.20
                r'TOTAL\s+AMOUNT\s+AFTER\s+DEPOSIT\s*[:.]?\s*([\d,]+\.?\d*)',  # TOTAL AMOUNT AFTER DEPOSIT: 1,897.20
            ]
            
            for pattern in patterns_vat:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    vat_str = match.group(1).replace(',', '')
                    try:
                        result['vat_amount'] = float(vat_str)
                        logger.info(f"✅ พบยอดภาษี: {result['vat_amount']}")
                        break
                    except ValueError:
                        continue
        
        # 3. ยอดรวม: 29,000.00
        # จาก OCR text: "สองหมื่นเก้าพันบาทถ้วน | จำนวนเงินรวมทั้งสิ้น (GRAND TOTAL) | 29,000.00"
        # หรือจากตาราง HTML: "จำนวนเงินรวมทั้งสิ้น(GRANDTOTAL) = 29,000.00"
        total_key = None
        for key in table_data.keys():
            if 'จำนวนเงินรวมทั้งสิ้น' in key or 'GRANDTOTAL' in key.upper() or 'GRAND TOTAL' in key.upper():
                total_key = key
                break
        
        if total_key:
            total_str = table_data[total_key].replace(',', '').strip()
            # ลบข้อความที่ติดมา หาเฉพาะตัวเลขแรกที่เจอ
            match = re.search(r'^([\d,]+\.?\d*)', total_str)
            if match:
                total_str = match.group(1).replace(',', '')
                try:
                    result['total_amount'] = float(total_str)
                    logger.info(f"✅ พบยอดรวมจากตาราง ({total_key}): {result['total_amount']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองอ่านจาก text format โดยตรง
        # Pattern: "สองหมื่นเก้าพันบาทถ้วน | จำนวนเงินรวมทั้งสิ้น (GRAND TOTAL) | 29,000.00"
        if result['total_amount'] is None:
            # หา pattern ที่มี 3 columns: "... | จำนวนเงินรวมทั้งสิ้น (GRAND TOTAL) | 29,000.00"
            pattern = r'[^|]*\|\s*จำนวนเงินรวมทั้งสิ้น\s*\(GRAND\s+TOTAL\)\s*\|\s*([\d,]+\.?\d*)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                total_str = match.group(1).replace(',', '')
                try:
                    result['total_amount'] = float(total_str)
                    logger.info(f"✅ พบยอดรวมจาก text format: {result['total_amount']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ
        if result['total_amount'] is None:
            patterns_total = [
                r'จำนวนเงินรวมทั้งสิ้น\s*\(GRAND\s+TOTAL\)\s*[|:]\s*([\d,]+\.?\d*)',  # จำนวนเงินรวมทั้งสิ้น (GRAND TOTAL) | 29,000.00
                r'จำนวนเงินรวมทั้งสิ้น\s*\(GRAND\s+TOTAL\)\s*=\s*([\d,]+\.?\d*)',  # จำนวนเงินรวมทั้งสิ้น (GRAND TOTAL) = 29,000.00
                r'GRAND\s+TOTAL\s*[:.]?\s*([\d,]+\.?\d*)',  # GRAND TOTAL: 29,000.00
                r'รวมทั้งสิ้น\s*[:.]?\s*([\d,]+\.?\d*)',  # รวมทั้งสิ้น: 29,000.00
            ]
            
            for pattern in patterns_total:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    total_str = match.group(1).replace(',', '')
                    try:
                        result['total_amount'] = float(total_str)
                        logger.info(f"✅ พบยอดรวม: {result['total_amount']}")
                        break
                    except ValueError:
                        continue
        
        return result
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': None,
            'withholding_tax_amount': None
        }
    
    def extract_address(self, text: str) -> str:
        """ดึงที่อยู่"""
        # กำหนดที่อยู่เป็นค่าคงที่
        return "อาคารรัฐนาการ ชั้นที่ 8.27 เลขที่ 3 ถนนสาทรใต้ แขวงยานนาวา เขตสาทร กรุงเทพมหานคร 10120"
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ"""
        # หมายเหตุว่าง
        return None
    
    def clean_filename(self, filename: str) -> str:
        """ทำความสะอาดชื่อไฟล์"""
        if not filename:
            return "ซื้อสินค้า"
        
        # กำหนดชื่อไฟล์ใหม่เป็น "ซื้อสินค้า"
        return "ซื้อสินค้า"
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร"""
        # มีภาษีมูลค่าเพิ่ม (มี vat_amount)
        vat_amount = amounts.get('vat_amount') or 0
        if vat_amount > 0:
            return 1  # มีภาษีมูลค่าเพิ่ม
        return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร Marvel Vision
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร Marvel Vision หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร บริษัท มาร์เวล วิชชั่น จำกัด'
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
        
        # สร้างชื่อไฟล์ใหม่
        new_filename = self.clean_filename(filename)
        
        # แยกที่อยู่เป็นส่วนๆ
        # ที่อยู่: อาคารรัฐนาการ ชั้นที่ 8.27 เลขที่ 3 ถนนสาทรใต้ แขวงยานนาวา เขตสาทร กรุงเทพมหานคร 10120
        address_full = address or ''
        building_number = '3'
        other_info = 'อาคารรัฐนาการ ชั้นที่ 8.27'
        soi = ''
        road = 'ถนนสาทรใต้'
        subdistrict = 'ยานนาวา'
        district = 'สาทร'
        province = 'กรุงเทพมหานคร'
        postal_code = '10120'
        
        return {
            'success': True,
            'company': 'MARVEL_VISION',
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
            'amount_before_vat': amounts.get('amount_before_vat') or 0,
            'vat_amount': amounts.get('vat_amount') or 0,
            'total_amount': amounts.get('total_amount') or 0,
            'withholding_tax_percent': withholding.get('withholding_tax_percent'),
            'withholding_tax_amount': withholding.get('withholding_tax_amount'),
            'remark': remark,
            'new_filename': new_filename,
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type
        }

