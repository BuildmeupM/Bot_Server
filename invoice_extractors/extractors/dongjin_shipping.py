"""
Dongjin Shipping Invoice Extractor
===================================
Extractor สำหรับดึงข้อมูลจาก DONGJIN SHIPPING CO.,LTD. c/o PCL AGENCIES CO.,LTD.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class DongjinShippingExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก DONGJIN SHIPPING CO.,LTD. c/o PCL AGENCIES CO.,LTD."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "DONGJIN SHIPPING CO.,LTD. c/o PCL AGENCIES CO.,LTD.",
        "DONGJIN SHIPPING CO.,LTD.",
        "DONGJIN SHIPPING",
        "PCL AGENCIES CO.,LTD.",
        "PCL AGENCIES",
        "DONGJIN"
    ]
    
    # Tax ID
    TAX_ID = "0993000363931"
    
    def __init__(self):
        """Initialize Dongjin Shipping Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ DONGJIN SHIPPING หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "DONGJIN SHIPPING CO.,LTD. c/o PCL AGENCIES CO.,LTD."
        2. Tax ID "0993000363931"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร DONGJIN SHIPPING (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID
        has_tax_id = (
            self.TAX_ID in text or
            "Tax Id.: 0993000363931" in text or
            "Tax Id: 0993000363931" in text
        )
        
        # เงื่อนไข 3: ต้องมีเอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE" หรือ "Invoice"
        has_document_type = (
            "ใบเสร็จรับเงิน" in text or 
            "ใบกำกับภาษี" in text or 
            "RECEIPT" in text.upper() or 
            "TAX INVOICE" in text.upper() or
            "Invoice" in text or
            "INVOICE" in text.upper()
        )
        
        # ต้องมีทั้ง 3 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id and has_document_type
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท"""
        return "DONGJIN SHIPPING CO.,LTD. c/o PCL AGENCIES CO.,LTD."
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: Tax Id.: 0993000363931 Tax Branch: Head Office
        patterns = [
            r'Tax\s+Id\.?\s*[:.]?\s*(\d{13})',  # Tax Id.: 0993000363931
            r'Tax\s+ID\.?\s*[:.]?\s*(\d{13})',  # Tax ID: 0993000363931
            r'TAX\s+ID\.?\s*[:.]?\s*(\d{13})',  # TAX ID: 0993000363931
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
        # ลองหาจาก HTML table ก่อน (อ่านจาก parse_html_table)
        table_data = self.parse_html_table(text)
        for key in table_data.keys():
            if 'INVOICEDATE' in key.upper() or ('INVOICE' in key.upper() and 'DATE' in key.upper()):
                date_str = table_data[key].strip()
                # หาเฉพาะตัวเลขวันที่
                match = re.search(r'(\d{2}/\d{2}/\d{4})', date_str)
                if match:
                    date_str = match.group(1).strip()
                    logger.info(f"✅ พบวันที่จาก HTML table: {date_str}")
                    return date_str
        
        # ลองหาจาก HTML table โดยตรง
        # Pattern: <tr><td>Invoice Date</td><td>10/11/2025</td></tr>
        tr_pattern = r'<tr[^>]*>.*?Invoice\s+Date.*?</td>\s*<td[^>]*>([\d/]+)</td>'
        match = re.search(tr_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            date_str = match.group(1).strip()
            logger.info(f"✅ พบวันที่จาก HTML table (direct): {date_str}")
            return date_str
        
        # Pattern: Invoice Date | 10/11/2025
        patterns = [
            r'Invoice\s+Date\s*\|\s*(\d{2}/\d{2}/\d{4})',  # Invoice Date | 10/11/2025
            r'Invoice\s+Date\s*[:.]?\s*(\d{2}/\d{2}/\d{4})',  # Invoice Date: 10/11/2025
            r'Date\s*\|\s*(\d{2}/\d{2}/\d{4})',  # Date | 10/11/2025
            r'วันที่\s*[:.]?\s*(\d{2}/\d{2}/\d{4})',  # วันที่: 10/11/2025
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                logger.info(f"✅ พบวันที่: {date_str}")
                return date_str
        
        logger.warning("⚠️ ไม่พบวันที่")
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # ลองหาจาก HTML table ก่อน (อ่านจาก parse_html_table)
        table_data = self.parse_html_table(text)
        for key in table_data.keys():
            if 'INVOICENO' in key.upper() or ('INVOICE' in key.upper() and 'NO' in key.upper()):
                doc_num = table_data[key].strip()
                # หาเฉพาะตัวเลขและตัวอักษร (เช่น DII25110121)
                match = re.search(r'([A-Z0-9]+)', doc_num)
                if match:
                    doc_num = match.group(1).strip()
                    logger.info(f"✅ พบเลขที่เอกสารจาก HTML table: {doc_num}")
                    return doc_num
        
        # ลองหาจาก HTML table โดยตรง
        # Pattern: <tr><td>Invoice no.</td><td>DII25110121</td></tr>
        tr_pattern = r'<tr[^>]*>.*?Invoice\s+no\.?.*?</td>\s*<td[^>]*>([A-Z0-9\s]+)</td>'
        match = re.search(tr_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            doc_num = match.group(1).strip()
            logger.info(f"✅ พบเลขที่เอกสารจาก HTML table (direct): {doc_num}")
            return doc_num
        
        # Pattern: Invoice no. | DII25110121
        patterns = [
            r'Invoice\s+no\.\s*\|\s*([A-Z0-9]+)',  # Invoice no. | DII25110121
            r'Invoice\s+No\.\s*\|\s*([A-Z0-9]+)',  # Invoice No. | DII25110121
            r'Invoice\s+no\.\s*[:.]?\s*([A-Z0-9]+)',  # Invoice no.: DII25110121
            r'Invoice\s+No\.\s*[:.]?\s*([A-Z0-9]+)',  # Invoice No.: DII25110121
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # Document No.: DII25110121
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                logger.info(f"✅ พบเลขที่เอกสาร: {doc_num}")
                return doc_num
        
        logger.warning("⚠️ ไม่พบเลขที่เอกสาร")
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง"""
        # อ่านจาก "B/L Number DJSCSHK250002936" หรือชื่อไฟล์เก่า
        
        # Pattern: B/L Number DJSCSHK250002936
        patterns = [
            r'B/L\s+Number\s+([A-Z0-9]+)',  # B/L Number DJSCSHK250002936
            r'B/L\s*[:.]?\s*([A-Z0-9]+)',  # B/L : DJSCSHK250002936
            r'BILL\s+OF\s+LADING\s+NO\.?\s*[:.]?\s*([A-Z0-9]+)',  # BILL OF LADING NO.: DJSCSHK250002936
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bl_no = match.group(1).strip()
                ref = f"B/L : {bl_no}"
                logger.info(f"✅ พบอ้างอิง: {ref}")
                return ref
        
        # Fallback: ลองอ่านจากชื่อไฟล์เก่า
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
        หา pattern เช่น: <tr><td>Invoice Date</td><td>10/11/2025</td></tr>
        หรือ: Total |  |  |  | 6,600.00 (text format)
        
        Returns:
            Dictionary ที่มี key-value จากตาราง
        """
        result = {}
        
        # Pattern สำหรับหา <tr>...</tr> ที่มีหลาย <td>
        # เช่น: <tr><td>Invoice Date</td><td>10/11/2025</td></tr>
        tr_pattern = r'<tr[^>]*>(.*?)</tr>'
        tr_matches = re.findall(tr_pattern, text, re.IGNORECASE | re.DOTALL)
        
        for tr_content in tr_matches:
            # หา <td> ทั้งหมดในแถว
            td_pattern = r'<td[^>]*>([^<]+(?:<[^>]+>)*[^<]*)</td>'
            td_matches = re.findall(td_pattern, tr_content, re.IGNORECASE | re.DOTALL)
            
            if len(td_matches) >= 2:
                # key อยู่ที่ td แรก
                key = re.sub(r'<[^>]+>', '', td_matches[0]).strip()
                
                # value อยู่ที่ td สุดท้ายที่มีข้อมูล (หรือ td สุดท้าย)
                value = None
                for td in reversed(td_matches):
                    td_clean = re.sub(r'<[^>]+>', '', td).strip()
                    # ถ้าเจอข้อมูลที่ไม่ว่าง ให้ใช้ค่านี้
                    if td_clean and td_clean not in ['-', '']:
                        value = td_clean
                        break
                
                if key and value:
                    # ทำความสะอาด key (ลบ whitespace)
                    key_clean = re.sub(r'\s+', '', key)
                    result[key_clean] = value
                    logger.info(f"✅ Parse HTML table row: {key_clean} = {value[:100]}...")
        
        # Fallback: ลองหาแบบ text format (| separated)
        # เช่น: Invoice Date | 10/11/2025 หรือ Total |  |  |  | 6,600.00
        lines = text.split('\n')
        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    # หา key จากส่วนแรก
                    key = parts[0].strip()
                    # หา value จากส่วนสุดท้ายที่มีข้อมูล
                    for part in reversed(parts):
                        if part.strip() and part.strip() not in ['-', '']:
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
                'amount_before_vat': float,  # ยอดก่อนภาษี (จาก Total)
                'vat_amount': float,          # ยอดภาษี (0.00)
                'total_amount': float         # ยอดรวม (จาก Net to Pay)
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
        
        # 1. ยอดก่อนภาษี: 6,600.00 (จาก Total)
        # จากตาราง HTML: "Total = 6,600.00"
        # หรือจาก text format: "Total |  |  |  | 6,600.00"
        total_key = None
        for key in table_data.keys():
            if 'TOTAL' in key.upper() and 'NET' not in key.upper() and 'PAY' not in key.upper():
                total_key = key
                break
        
        if total_key:
            total_str = table_data[total_key].replace(',', '').strip()
            # หาเฉพาะตัวเลขแรกที่เจอ
            match = re.search(r'^([\d,]+\.?\d*)', total_str)
            if match:
                total_str = match.group(1).replace(',', '')
                try:
                    result['amount_before_vat'] = float(total_str)
                    logger.info(f"✅ พบยอดก่อนภาษีจากตาราง ({total_key}): {result['amount_before_vat']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ จาก HTML table โดยตรง
        if result['amount_before_vat'] is None:
            # ลองหาจาก HTML table โดยตรง
            # Pattern: <tr><td>Total</td><td>-</td><td>-</td><td>6,600.00</td></tr>
            pattern = r'<tr[^>]*>.*?Total.*?</td>\s*(?:<td[^>]*>[^<]*</td>\s*)*<td[^>]*>([\d,]+\.?\d*)</td>'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                total_str = match.group(1).replace(',', '')
                try:
                    result['amount_before_vat'] = float(total_str)
                    logger.info(f"✅ พบยอดก่อนภาษีจาก HTML table (direct): {result['amount_before_vat']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ จาก text format
        if result['amount_before_vat'] is None:
            # ลองหาจาก text format โดยตรง (อ่านทีละบรรทัด)
            lines = text.split('\n')
            for line in lines:
                # Pattern: "Total |  |  |  | 6,600.00"
                if 'Total' in line and 'Net' not in line and 'Pay' not in line and 'Grand' not in line:
                    # หา pattern ที่มี | และตัวเลข
                    parts = [p.strip() for p in line.split('|')]
                    for part in reversed(parts):
                        if re.search(r'\d', part) and part.strip() not in ['-', '']:
                            match = re.search(r'([\d,]+\.?\d*)', part)
                            if match:
                                total_str = match.group(1).replace(',', '')
                                try:
                                    result['amount_before_vat'] = float(total_str)
                                    logger.info(f"✅ พบยอดก่อนภาษีจาก text format: {result['amount_before_vat']}")
                                    break
                                except ValueError:
                                    continue
                    if result['amount_before_vat']:
                        break
        
        # 2. ยอดรวม: 6,600.00 (จาก Net to Pay)
        # จากตาราง HTML: "NettoPay = 6,600.00"
        # หรือจาก text format: "Net to Pay |  |  |  | 6,600.00"
        net_pay_key = None
        for key in table_data.keys():
            if 'NET' in key.upper() and 'PAY' in key.upper():
                net_pay_key = key
                break
        
        if net_pay_key:
            net_pay_str = table_data[net_pay_key].replace(',', '').strip()
            # หาเฉพาะตัวเลขแรกที่เจอ
            match = re.search(r'^([\d,]+\.?\d*)', net_pay_str)
            if match:
                net_pay_str = match.group(1).replace(',', '')
                try:
                    result['total_amount'] = float(net_pay_str)
                    logger.info(f"✅ พบยอดรวมจากตาราง ({net_pay_key}): {result['total_amount']}")
                except ValueError:
                    pass
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ จาก HTML table โดยตรง
        if result['total_amount'] is None:
            # ลองหาจาก HTML table โดยตรง
            # Pattern: <tr><td>Net to Pay</td><td>-</td><td>-</td><td>6,600.00</td></tr>
            # หรือ: <tr><td>Grand Total</td><td>-</td><td>-</td><td>6,600.00</td></tr>
            patterns = [
                r'<tr[^>]*>.*?Net.*?Pay.*?</td>\s*(?:<td[^>]*>[^<]*</td>\s*)*<td[^>]*>([\d,]+\.?\d*)</td>',
                r'<tr[^>]*>.*?Grand.*?Total.*?</td>\s*(?:<td[^>]*>[^<]*</td>\s*)*<td[^>]*>([\d,]+\.?\d*)</td>',
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    total_str = match.group(1).replace(',', '')
                    try:
                        result['total_amount'] = float(total_str)
                        logger.info(f"✅ พบยอดรวมจาก HTML table (direct): {result['total_amount']}")
                        break
                    except ValueError:
                        continue
        
        # ถ้ายังไม่พบ ให้ลองหา pattern อื่นๆ จาก text format
        if result['total_amount'] is None:
            # ลองหาจาก text format โดยตรง (อ่านทีละบรรทัด)
            lines = text.split('\n')
            for line in lines:
                # Pattern: "Net to Pay |  |  |  | 6,600.00" หรือ "Grand Total |  |  |  | 6,600.00"
                if ('Net' in line and 'Pay' in line) or ('Grand' in line and 'Total' in line):
                    # หา pattern ที่มี | และตัวเลข
                    parts = [p.strip() for p in line.split('|')]
                    for part in reversed(parts):
                        if re.search(r'\d', part) and part.strip() not in ['-', '']:
                            match = re.search(r'([\d,]+\.?\d*)', part)
                            if match:
                                total_str = match.group(1).replace(',', '')
                                try:
                                    result['total_amount'] = float(total_str)
                                    logger.info(f"✅ พบยอดรวมจาก text format: {result['total_amount']}")
                                    break
                                except ValueError:
                                    continue
                    if result['total_amount']:
                        break
        
        # 3. ยอดภาษี: 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        result['vat_amount'] = 0.00
        
        # 4. ถ้าไม่มียอดรวม แต่มียอดก่อนภาษี ให้ใช้ยอดก่อนภาษีเป็นยอดรวม
        # เพราะเอกสารนี้ไม่มีภาษีมูลค่าเพิ่ม (ยอดก่อนภาษี = ยอดรวม)
        if result['total_amount'] is None and result['amount_before_vat'] is not None:
            result['total_amount'] = result['amount_before_vat']
            logger.info(f"✅ ใช้ยอดก่อนภาษีเป็นยอดรวม (ไม่มีภาษีมูลค่าเพิ่ม): {result['total_amount']}")
        
        return result
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': None,
            'withholding_tax_amount': None
        }
    
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
        # ไม่มีภาษีมูลค่าเพิ่ม (vat_amount = 0.00)
        return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
    def extract_address(self, text: str) -> str:
        """ดึงที่อยู่"""
        # กำหนดที่อยู่เป็นค่าคงที่
        return "92/36 SATHORN THANI 2 BLDG., 14FL., North Sathorn Road, Silom, Bangrak, Bangkok 10500"
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร DONGJIN SHIPPING
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร DONGJIN SHIPPING หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร DONGJIN SHIPPING CO.,LTD. c/o PCL AGENCIES CO.,LTD.'
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
        # ที่อยู่: 92/36 SATHORN THANI 2 BLDG., 14FL., North Sathorn Road, Silom, Bangrak, Bangkok 10500
        address_full = address or ''
        building_number = '92/36'
        other_info = 'SATHORN THANI 2 BLDG., 14FL.'
        soi = ''
        road = 'North Sathorn Road'
        subdistrict = 'Silom'
        district = 'Bangrak'
        province = 'Bangkok'
        postal_code = '10500'
        
        return {
            'success': True,
            'company': 'DONGJIN_SHIPPING',
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
            'document_type': document_type,
            'skip_amount_adjustment': True  # ไม่ให้ manager คำนวณยอดภาษีและยอดรวมใหม่ (เพราะเอกสารนี้ไม่มีภาษีมูลค่าเพิ่ม)
        }

