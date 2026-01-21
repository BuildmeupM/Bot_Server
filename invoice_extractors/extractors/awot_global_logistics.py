"""
AWOT Global Logistics (Thailand) Invoice Extractor
==================================================
Extractor สำหรับดึงข้อมูลจาก AWOT Global Logistics (Thailand) Co., Ltd

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class AWOTGlobalLogisticsExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก AWOT Global Logistics (Thailand) Co., Ltd"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "AWOT Global Logistics (Thailand) Co., Ltd",
        "AWOT Global Logistics (Thailand)",
        "AWOT Global Logistics",
        "AWOT"
    ]
    
    # Tax ID
    TAX_ID = "0105557106960"
    
    def __init__(self):
        """Initialize AWOT Global Logistics Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ AWOT Global Logistics (Thailand) Co., Ltd หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "AWOT Global Logistics (Thailand) Co., Ltd"
        2. Tax ID "0105557106960"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE" หรือ "INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร AWOT Global Logistics (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID
        has_tax_id = (
            self.TAX_ID in text or
            "Tax ID" in text and "0105557106960" in text
        )
        
        # เงื่อนไข 3: ต้องมีเอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE" หรือ "INVOICE"
        has_document_type = (
            "ใบเสร็จรับเงิน" in text or 
            "ใบกำกับภาษี" in text or 
            "RECEIPT" in text.upper() or 
            "TAX INVOICE" in text.upper() or
            "INVOICE" in text.upper()  # เพิ่มรองรับ INVOICE เพียงอย่างเดียว
        )
        
        # ต้องมีทั้ง 3 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id and has_document_type
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "AWOT Global Logistics (Thailand) Co., Ltd"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: Tax ID: 0105557106960
        patterns = [
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0105557106960
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID: 0105557106960
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี: 0105557106960
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id = match.group(1).strip()
                if tax_id == self.TAX_ID:
                    logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษี: {tax_id}")
                    return tax_id
        
        # Fallback: ถ้าไม่พบข้อมูล ให้ใช้ค่า default
        if self.TAX_ID in text:
            return self.TAX_ID
        
        logger.info(f"⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา"""
        # ไม่มีสาขา (ว่าง)
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern 1: Invoice Date: 2025.11.12 (รูปแบบใหม่)
        patterns = [
            r'Invoice\s+Date\s*[:.]?\s*(\d{4})\.(\d{1,2})\.(\d{1,2})',  # Invoice Date: 2025.11.12
            r'วันที่\s+([A-Za-z]{3})\s+(\d{1,2}),\s+(\d{4})\s+Date',  # วันที่ Nov 10, 2025 Date
            r'Date\s+([A-Za-z]{3})\s+(\d{1,2}),\s+(\d{4})',  # Date Nov 10, 2025
            r'([A-Za-z]{3})\s+(\d{1,2}),\s+(\d{4})',  # Nov 10, 2025
        ]
        
        # Mapping เดือน
        month_map = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        
        for idx, pattern in enumerate(patterns):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if idx == 0:  # Pattern แรก: 2025.11.12
                    year = match.group(1)
                    month = match.group(2).zfill(2)
                    day = match.group(3).zfill(2)
                    date_str = f"{day}/{month}/{year}"
                    logger.info(f"✅ พบวันที่ (รูปแบบ Invoice Date): {date_str}")
                    return date_str
                else:  # Pattern อื่นๆ: Nov 10, 2025
                    month_str = match.group(1).capitalize()
                    day = match.group(2).zfill(2)
                    year = match.group(3)
                    
                    month = month_map.get(month_str, '01')
                    date_str = f"{day}/{month}/{year}"
                    logger.info(f"✅ พบวันที่: {date_str}")
                    return date_str
        
        logger.warning("⚠️ ไม่พบวันที่")
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern 1: Invoice No.: BKKDB25115431 (รูปแบบใหม่)
        patterns = [
            r'Invoice\s+No\.\s*[:.]?\s*([A-Z0-9\s]+)',  # Invoice No.: BKKDB25115431
            r'เลขที่\s*/?\s*No\.\s*([A-Z0-9\s]+)',  # เลขที่/No. AWOT 25110221
            r'เลขที่\s*[:.]?\s*([A-Z0-9\s]+)',  # เลขที่: AWOT 25110221
            r'No\.\s*[:.]?\s*([A-Z0-9\s]+)',  # No.: AWOT 25110221
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9\s]+)',  # Document No.: AWOT 25110221
        ]
        
        for idx, pattern in enumerate(patterns):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                logger.info(f"✅ พบเลขที่เอกสาร (pattern #{idx+1}): {doc_num}")
                return doc_num
        
        logger.warning("⚠️ ไม่พบเลขที่เอกสาร")
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง"""
        # อ่านจากชื่อไฟล์เก่า (ตัดข้อมูล VAT_, WHT_, None_vat และข้อมูลที่เริ่มต้นด้วย EXC_)
        if filename:
            # ตัดข้อมูล VAT_, WHT_, None_vat และข้อมูลที่เริ่มต้นด้วย EXC_
            ref = filename
            ref = re.sub(r'^VAT_', '', ref, flags=re.IGNORECASE)
            ref = re.sub(r'^WHT_', '', ref, flags=re.IGNORECASE)
            ref = re.sub(r'^None_vat_', '', ref, flags=re.IGNORECASE)
            ref = re.sub(r'EXC_[^_]*_', '', ref, flags=re.IGNORECASE)
            ref = re.sub(r'\.pdf$', '', ref, flags=re.IGNORECASE)
            if ref and ref != filename:
                logger.info(f"✅ พบอ้างอิงจากชื่อไฟล์: {ref}")
                return ref
        
        return None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # ชื่อบัญชี: ค่าใช้จ่ายในการขนส่ง
        return {
            'account_name': 'ค่าใช้จ่ายในการขนส่ง',
            'account_code': None
        }
    
    def parse_html_table(self, text: str) -> Dict[str, str]:
        """
        Parse ข้อมูลจากตาราง HTML
        หา pattern เช่น: <tr><td>Total Excluding VAT</td><td>-</td><td>-</td><td>8,650.00</td></tr>
        หรือ: รวมทั้งสิ้น Total Excluding VAT |  |  | 8,650.00 (text format)
        
        Returns:
            Dictionary ที่มี key-value จากตาราง
        """
        result = {}
        
        # Pattern สำหรับหา <tr>...</tr> ที่มีหลาย <td>
        # เช่น: <tr><td>Total Excluding VAT</td><td>-</td><td>-</td><td>8,650.00</td></tr>
        tr_pattern = r'<tr[^>]*>(.*?)</tr>'
        tr_matches = re.findall(tr_pattern, text, re.IGNORECASE | re.DOTALL)
        
        for tr_content in tr_matches:
            # หา <td> ทั้งหมดในแถว
            td_pattern = r'<td[^>]*>([^<]+(?:<[^>]+>)*[^<]*)</td>'
            td_matches = re.findall(td_pattern, tr_content, re.IGNORECASE | re.DOTALL)
            
            if len(td_matches) >= 2:
                # key อยู่ที่ td แรก
                key = re.sub(r'<[^>]+>', '', td_matches[0]).strip()
                
                # value อยู่ที่ td สุดท้ายที่มีตัวเลข (หรือ td สุดท้าย)
                value = None
                for td in reversed(td_matches):
                    td_clean = re.sub(r'<[^>]+>', '', td).strip()
                    # ถ้าเจอตัวเลข ให้ใช้ค่านี้
                    if re.search(r'\d', td_clean) and td_clean not in ['-', '']:
                        value = td_clean
                        break
                
                if key and value:
                    # ทำความสะอาด key (ลบ whitespace)
                    key_clean = re.sub(r'\s+', '', key)
                    result[key_clean] = value
                    logger.info(f"✅ Parse HTML table row: {key_clean} = {value[:100]}...")
        
        # Fallback: ลองหาแบบ text format (| separated)
        # เช่น: รวมทั้งสิ้น Total Excluding VAT |  |  | 8,650.00
        lines = text.split('\n')
        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    # หา key จากส่วนแรก
                    key = parts[0].strip()
                    # หา value จากส่วนสุดท้ายที่มีตัวเลข
                    for part in reversed(parts):
                        if re.search(r'\d', part) and part.strip() not in ['-', '']:
                            value = part.strip()
                            break
                    else:
                        continue
                    
                    # ทำความสะอาด key (ลบ whitespace)
                    key_clean = re.sub(r'\s+', '', key)
                    
                    if key_clean and value:
                        result[key_clean] = value
                        logger.info(f"✅ Parse text table: {key_clean} = {value[:100]}...")
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (จาก Total Excluding VAT)
                'vat_amount': float,          # ยอดภาษี (จาก VAT)
                'total_amount': float         # ยอดรวม (จาก Grand Total)
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # Parse ข้อมูลจากตาราง HTML ก่อน
        table_data = self.parse_html_table(text)
        logger.info(f"🔍 Table data keys: {list(table_data.keys())[:20]}...")
        
        # 1. ยอดก่อนภาษี: 8,650.00 (จาก Total Excluding VAT)
        # จากตาราง HTML: "TotalExcludingVAT = 8,650.00"
        # หรือจาก text format: "รวมทั้งสิ้น Total Excluding VAT |  |  | 8,650.00"
        total_excl_key = None
        for key in table_data.keys():
            if ('TOTAL' in key.upper() and 'EXCLUDING' in key.upper() and 'VAT' in key.upper()) or \
               ('รวมทั้งสิ้น' in key or 'รวมทั้งสิ้น' in text and 'Total' in key.upper() and 'Excluding' in key.upper()):
                total_excl_key = key
                break
        
        if total_excl_key:
            total_excl_str = table_data[total_excl_key].replace(',', '').strip()
            # หาเฉพาะตัวเลขแรกที่เจอ
            match = re.search(r'^([\d,]+\.?\d*)', total_excl_str)
            if match:
                total_excl_str = match.group(1).replace(',', '')
                try:
                    result['amount_before_vat'] = float(total_excl_str)
                    logger.info(f"✅ พบยอดก่อนภาษีจากตาราง ({total_excl_key}): {result['amount_before_vat']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ จาก HTML table โดยตรง
        if result['amount_before_vat'] is None:
            # ลองหาจาก HTML table โดยตรง
            # Pattern: <tr><td>รวมทั้งสิ้น Total Excluding VAT</td><td>-</td><td>-</td><td>8,650.00</td></tr>
            pattern = r'<tr[^>]*>.*?Total.*?Excluding.*?VAT.*?</td>\s*(?:<td[^>]*>[^<]*</td>\s*)*<td[^>]*>([\d,]+\.?\d*)</td>'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                total_excl_str = match.group(1).replace(',', '')
                try:
                    result['amount_before_vat'] = float(total_excl_str)
                    logger.info(f"✅ พบยอดก่อนภาษีจาก HTML table: {result['amount_before_vat']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ จาก text format
        if result['amount_before_vat'] is None:
            # ลองหาจาก text format โดยตรง (อ่านทีละบรรทัด)
            # Pattern 1: Sub - Total: THB === 8,650.00 === (รูปแบบใหม่)
            pattern_sub_total = r'Sub\s*[-]?\s*Total\s*[:.]?\s*THB\s*===?\s*([\d,]+\.?\d{2})\s*===?'
            match = re.search(pattern_sub_total, text, re.IGNORECASE)
            if match:
                total_excl_str = match.group(1).replace(',', '')
                try:
                    result['amount_before_vat'] = float(total_excl_str)
                    logger.info(f"✅ พบยอดก่อนภาษีจาก Sub - Total: {result['amount_before_vat']}")
                except ValueError:
                    pass
            
            # Pattern 2: "รวมทั้งสิ้น Total Excluding VAT |  |  | 8,650.00"
            if result['amount_before_vat'] is None:
                lines = text.split('\n')
                for line in lines:
                    if ('Total' in line and 'Excluding' in line and 'VAT' in line) or \
                       ('รวมทั้งสิ้น' in line and 'Total' in line):
                        # หา pattern ที่มี | และตัวเลข
                        parts = [p.strip() for p in line.split('|')]
                        for part in reversed(parts):
                            if re.search(r'\d', part) and part.strip() not in ['-', '']:
                                match = re.search(r'([\d,]+\.?\d*)', part)
                                if match:
                                    total_excl_str = match.group(1).replace(',', '')
                                    try:
                                        result['amount_before_vat'] = float(total_excl_str)
                                        logger.info(f"✅ พบยอดก่อนภาษีจาก text format: {result['amount_before_vat']}")
                                        break
                                    except ValueError:
                                        continue
                        if result['amount_before_vat']:
                            break
        
        # 2. ยอดภาษี: 605.50 (จาก VAT)
        # จากตาราง HTML: "VAT = 605.50"
        # หรือจาก text format: "จำนวนภาษีมูลค่าเพิ่ม VAT |  |  | 605.50"
        vat_key = None
        for key in table_data.keys():
            if ('VAT' in key.upper() and 'TOTAL' not in key.upper() and 'EXCLUDING' not in key.upper()) or \
               ('ภาษี' in key or 'ภาษีมูลค่าเพิ่ม' in text and 'VAT' in key.upper()):
                vat_key = key
                break
        
        if vat_key:
            vat_str = table_data[vat_key].replace(',', '').strip()
            # หาเฉพาะตัวเลขแรกที่เจอ
            match = re.search(r'^([\d,]+\.?\d*)', vat_str)
            if match:
                vat_str = match.group(1).replace(',', '')
                try:
                    result['vat_amount'] = float(vat_str)
                    logger.info(f"✅ พบยอดภาษีจากตาราง ({vat_key}): {result['vat_amount']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ จาก HTML table โดยตรง
        if result['vat_amount'] is None:
            # ลองหาจาก HTML table โดยตรง
            # Pattern: <tr><td>จำนวนภาษีมูลค่าเพิ่ม VAT</td><td>-</td><td>-</td><td>605.50</td></tr>
            pattern = r'<tr[^>]*>.*?(?:ภาษีมูลค่าเพิ่ม|VAT).*?</td>\s*(?:<td[^>]*>[^<]*</td>\s*)*<td[^>]*>([\d,]+\.?\d*)</td>'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                vat_str = match.group(1).replace(',', '')
                try:
                    result['vat_amount'] = float(vat_str)
                    logger.info(f"✅ พบยอดภาษีจาก HTML table: {result['vat_amount']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ จาก text format
        if result['vat_amount'] is None:
            # ลองหาจาก text format โดยตรง (อ่านทีละบรรทัด)
            # Pattern 1: VAT: THB === 605.50 === (รูปแบบใหม่)
            pattern_vat = r'VAT\s*[:.]?\s*THB\s*===?\s*([\d,]+\.?\d{2})\s*===?'
            match = re.search(pattern_vat, text, re.IGNORECASE)
            if match:
                vat_str = match.group(1).replace(',', '')
                try:
                    result['vat_amount'] = float(vat_str)
                    logger.info(f"✅ พบยอดภาษีจาก VAT: THB ===: {result['vat_amount']}")
                except ValueError:
                    pass
            
            # Pattern 2: "จำนวนภาษีมูลค่าเพิ่ม VAT |  |  | 605.50"
            if result['vat_amount'] is None:
                lines = text.split('\n')
                for line in lines:
                    if ('VAT' in line and 'ภาษี' in line) or ('ภาษีมูลค่าเพิ่ม' in line):
                        # หา pattern ที่มี | และตัวเลข
                        parts = [p.strip() for p in line.split('|')]
                        for part in reversed(parts):
                            if re.search(r'\d', part) and part.strip() not in ['-', '']:
                                match = re.search(r'([\d,]+\.?\d*)', part)
                                if match:
                                    vat_str = match.group(1).replace(',', '')
                                    try:
                                        result['vat_amount'] = float(vat_str)
                                        logger.info(f"✅ พบยอดภาษีจาก text format: {result['vat_amount']}")
                                        break
                                    except ValueError:
                                        continue
                        if result['vat_amount']:
                            break
        
        # 3. ยอดรวม: 9,255.50 (จาก Grand Total)
        # จากตาราง HTML: "GrandTotal = 9,255.50"
        # หรือจาก text format: "จำนวนเงินทั้งสิ้น Grand Total |  |  | 9,255.50"
        grand_total_key = None
        for key in table_data.keys():
            if ('GRAND' in key.upper() and 'TOTAL' in key.upper()) or \
               ('จำนวนเงินทั้งสิ้น' in key or 'จำนวนเงินทั้งสิ้น' in text and 'Grand' in key.upper() and 'Total' in key.upper()):
                grand_total_key = key
                break
        
        if grand_total_key:
            grand_total_str = table_data[grand_total_key].replace(',', '').strip()
            # หาเฉพาะตัวเลขแรกที่เจอ
            match = re.search(r'^([\d,]+\.?\d*)', grand_total_str)
            if match:
                grand_total_str = match.group(1).replace(',', '')
                try:
                    result['total_amount'] = float(grand_total_str)
                    logger.info(f"✅ พบยอดรวมจากตาราง ({grand_total_key}): {result['total_amount']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ จาก HTML table โดยตรง
        if result['total_amount'] is None:
            # ลองหาจาก HTML table โดยตรง
            # Pattern: <tr><td>จำนวนเงินทั้งสิ้น Grand Total</td><td>-</td><td>-</td><td>9,255.50</td></tr>
            pattern = r'<tr[^>]*>.*?Grand.*?Total.*?</td>\s*(?:<td[^>]*>[^<]*</td>\s*)*<td[^>]*>([\d,]+\.?\d*)</td>'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                grand_total_str = match.group(1).replace(',', '')
                try:
                    result['total_amount'] = float(grand_total_str)
                    logger.info(f"✅ พบยอดรวมจาก HTML table: {result['total_amount']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ จาก text format
        if result['total_amount'] is None:
            # ลองหาจาก text format โดยตรง (อ่านทีละบรรทัด)
            # Pattern 1: Total: THB === 9,255.50 === (รูปแบบใหม่)
            pattern_total = r'Total\s*[:.]?\s*THB\s*===?\s*([\d,]+\.?\d{2})\s*===?'
            match = re.search(pattern_total, text, re.IGNORECASE)
            if match:
                grand_total_str = match.group(1).replace(',', '')
                try:
                    result['total_amount'] = float(grand_total_str)
                    logger.info(f"✅ พบยอดรวมจาก Total: THB ===: {result['total_amount']}")
                except ValueError:
                    pass
            
            # Pattern 2: TOTAL: THB === 9,255.50 === (รูปแบบใหม่ - อีกบรรทัด)
            if result['total_amount'] is None:
                pattern_total2 = r'TOTAL\s*[:.]?\s*THB\s*===?\s*([\d,]+\.?\d{2})\s*===?'
                match = re.search(pattern_total2, text, re.IGNORECASE)
                if match:
                    grand_total_str = match.group(1).replace(',', '')
                    try:
                        result['total_amount'] = float(grand_total_str)
                        logger.info(f"✅ พบยอดรวมจาก TOTAL: THB ===: {result['total_amount']}")
                    except ValueError:
                        pass
            
            # Pattern 3: "จำนวนเงินทั้งสิ้น Grand Total |  |  | 9,255.50"
            if result['total_amount'] is None:
                lines = text.split('\n')
                for line in lines:
                    if ('Grand' in line and 'Total' in line) or ('จำนวนเงินทั้งสิ้น' in line):
                        # หา pattern ที่มี | และตัวเลข
                        parts = [p.strip() for p in line.split('|')]
                        for part in reversed(parts):
                            if re.search(r'\d', part) and part.strip() not in ['-', '']:
                                match = re.search(r'([\d,]+\.?\d*)', part)
                                if match:
                                    grand_total_str = match.group(1).replace(',', '')
                                    try:
                                        result['total_amount'] = float(grand_total_str)
                                        logger.info(f"✅ พบยอดรวมจาก text format: {result['total_amount']}")
                                        break
                                    except ValueError:
                                        continue
                        if result['total_amount']:
                            break
        
        return result
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        result = {
            'withholding_tax_percent': 0.0,
            'withholding_tax_amount': 0.0
        }
        
        # Pattern 1: W/H TAX 3% (8,650 X 3%) = THB 259.50 (รูปแบบใหม่)
        pattern_wht_with_amount = r'W[/\\]\s*H\s*TAX\s*3\s*%\s*\([^)]+\)\s*=\s*THB\s*([\d,]+\.?\d{2})'
        match = re.search(pattern_wht_with_amount, text, re.IGNORECASE)
        if match:
            result['withholding_tax_percent'] = 3.0
            amount_str = match.group(1).replace(',', '').strip()
            try:
                result['withholding_tax_amount'] = float(amount_str)
                logger.info(f"✅ พบ WHT 3%: {result['withholding_tax_amount']}")
                return result
            except ValueError:
                pass
        
        # Pattern 2: W/H TAX 3% (ไม่มีจำนวนเงิน)
        patterns = [
            r'W[/\\]\s*H\s*TAX\s*3\s*%',  # W/H TAX 3%
            r'WHT\s*3\s*%',  # WHT 3%
            r'หัก\s*ณ\s*ที่จ่าย\s*3\s*%',  # หัก ณ ที่จ่าย 3%
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['withholding_tax_percent'] = 3.0
                logger.info(f"✅ พบ WHT 3% (ไม่มีจำนวนเงิน)")
                break
        
        return result
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ"""
        # อ่านจาก "REF. : R2554C101631RUD" และชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_
        remark_parts = []
        
        # หา REF. : R2554C101631RUD
        ref_pattern = r'REF\.\s*[:.]?\s*([A-Z0-9]+)'
        match = re.search(ref_pattern, text, re.IGNORECASE)
        if match:
            ref = match.group(1).strip()
            remark_parts.append(f"REF. : {ref}")
        
        # หาชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_
        if filename and filename.upper().startswith('EXC_'):
            exc_part = filename
            remark_parts.append(exc_part)
        
        if remark_parts:
            remark = ' '.join(remark_parts)
            logger.info(f"✅ พบหมายเหตุ: {remark}")
            return remark
        
        return None
    
    def clean_filename(self, filename: str) -> str:
        """ทำความสะอาดชื่อไฟล์"""
        if not filename:
            return ""
        
        # ตัดข้อมูล VAT_, WHT_, None_vat
        cleaned = filename
        cleaned = re.sub(r'^VAT_', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^WHT_', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^None_vat_', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร"""
        # มีภาษีมูลค่าเพิ่ม (vat_amount > 0)
        return 1  # มีภาษีมูลค่าเพิ่ม
    
    def extract_address(self, text: str) -> str:
        """ดึงที่อยู่"""
        # กำหนดที่อยู่เป็นค่าคงที่
        return "เลขที่ 36/135-137 หมู่บ้าน อาร์ เค บิซ เซ็นเตอร์ ถนนมอเตอร์เวย์ แขวงคลองสองต้นนุ่น เขตลาดกระบัง กรุงเทพฯ 10520"
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร AWOT Global Logistics
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร AWOT Global Logistics หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            # ตรวจสอบว่ามีชื่อบริษัทและ Tax ID แต่ไม่มี document type ที่ตรงกับเงื่อนไข
            has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
            has_tax_id = (self.TAX_ID in text or ("Tax ID" in text and "0105557106960" in text))
            has_invoice_only = "INVOICE" in text.upper() and "TAX INVOICE" not in text.upper()
            
            # ถ้ามีชื่อบริษัท, Tax ID และมีแค่ "INVOICE" (ไม่ใช่ "TAX INVOICE") ให้แสดงแจ้งเตือนและผ่าน
            if has_company and has_tax_id and has_invoice_only:
                warning_message = "⚠️ พบเอกสารเป็นใบแจ้งหนี้ (INVOICE) ไม่ใช่ใบกำกับภาษี (TAX INVOICE) - แต่จะดำเนินการอ่านข้อมูลต่อ"
                logger.warning(warning_message)
                # ผ่านการตรวจสอบและดำเนินการอ่านข้อมูลต่อ
                # จะเพิ่ม warning_message ใน return dictionary
            else:
                return {
                    'success': False,
                    'company': None,
                    'error': 'ไม่ใช่เอกสาร AWOT Global Logistics (Thailand) Co., Ltd'
                }
        
        # ตรวจสอบว่ามี warning message หรือไม่ (กรณีเป็น INVOICE แทน TAX INVOICE)
        warning_message = None
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        has_tax_id = (self.TAX_ID in text or ("Tax ID" in text and "0105557106960" in text))
        has_invoice_only = "INVOICE" in text.upper() and "TAX INVOICE" not in text.upper()
        if has_company and has_tax_id and has_invoice_only:
            warning_message = "⚠️ พบเอกสารเป็นใบแจ้งหนี้ (INVOICE) ไม่ใช่ใบกำกับภาษี (TAX INVOICE)"
        
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
        # ที่อยู่: เลขที่ 36/135-137 หมู่บ้าน อาร์ เค บิซ เซ็นเตอร์ ถนนมอเตอร์เวย์ แขวงคลองสองต้นนุ่น เขตลาดกระบัง กรุงเทพฯ 10520
        address_full = address or ''
        building_number = '36/135-137'
        other_info = 'หมู่บ้าน อาร์ เค บิซ เซ็นเตอร์'
        soi = ''
        road = 'ถนนมอเตอร์เวย์'
        subdistrict = 'คลองสองต้นนุ่น'
        district = 'ลาดกระบัง'
        province = 'กรุงเทพมหานคร'
        postal_code = '10520'
        
        result = {
            'success': True,
            'company': 'AWOT_GLOBAL_LOGISTICS',
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
            'document_type': document_type,  # 1 = มีภาษีมูลค่าเพิ่ม
        }
        
        # เพิ่ม warning message ถ้ามี
        if warning_message:
            result['warning_message'] = warning_message
        
        return result

