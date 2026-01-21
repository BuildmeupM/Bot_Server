"""
MSC Invoice Extractor
======================
Extractor สำหรับดึงข้อมูลจาก MSC Mediterranean Shipping Company

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class MSCInvoiceExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก MSC Mediterranean Shipping Company"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "MSC Mediterranean Shipping Company",
        "Mediterranean Shipping (Thailand)"
    ]
    
    # Tax ID (default value)
    TAX_ID = "0993000003667"
    
    def __init__(self):
        """Initialize MSC Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ MSC หรือไม่
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร MSC
        """
        if not text:
            return False
        
        text_upper = text.upper()
        for identifier in self.COMPANY_IDENTIFIERS:
            if identifier.upper() in text_upper:
                return True
        return False
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท MSC"""
        lines = text.split('\n')
        for line in lines:
            if 'MSC Mediterranean Shipping Company' in line:
                company_name = line.strip()
                if 'S.A.' not in company_name:
                    company_name = 'MSC Mediterranean Shipping Company S.A.'
                return company_name
        
        return 'MSC Mediterranean Shipping Company S.A.'
    
    def parse_html_table(self, text: str) -> Dict[str, str]:
        """
        Parse ข้อมูลจากตาราง HTML
        หา pattern เช่น: <tr><td>Tax ID</td><td>0993000036677</td></tr>
        หรือ: Tax ID | 0993000036677 (text format)
        
        Returns:
            Dictionary ที่มี key-value จากตาราง
        """
        result = {}
        
        # Log โครงสร้าง HTML ที่พบ
        logger.info("🔍 [HTML Structure] เริ่มตรวจสอบโครงสร้าง HTML...")
        
        # ตรวจสอบว่ามี HTML tags หรือไม่
        has_html_tags = bool(re.search(r'<[^>]+>', text))
        logger.info(f"🔍 [HTML Structure] มี HTML tags: {has_html_tags}")
        
        # แสดงตัวอย่าง text (200 ตัวอักษรแรก)
        text_preview = text[:200].replace('\n', '\\n')
        logger.info(f"🔍 [HTML Structure] ตัวอย่าง text (200 ตัวอักษรแรก): {text_preview}...")
        
        # Pattern สำหรับหา <tr>...</tr> ที่มีหลาย <td>
        tr_pattern = r'<tr[^>]*>(.*?)</tr>'
        tr_matches = re.findall(tr_pattern, text, re.IGNORECASE | re.DOTALL)
        
        logger.info(f"🔍 [HTML Structure] พบ <tr> tags: {len(tr_matches)} แถว")
        
        for idx, tr_content in enumerate(tr_matches):
            # หา <td> ทั้งหมดในแถว
            td_pattern = r'<td[^>]*>([^<]+(?:<[^>]+>)*[^<]*)</td>'
            td_matches = re.findall(td_pattern, tr_content, re.IGNORECASE | re.DOTALL)
            
            logger.info(f"🔍 [HTML Structure] แถว {idx+1}: พบ <td> {len(td_matches)} คอลัมน์")
            if td_matches:
                logger.info(f"🔍 [HTML Structure] แถว {idx+1} เนื้อหา: {tr_content[:150]}...")
            
            if len(td_matches) >= 2:
                # key อยู่ที่ td แรก
                key = re.sub(r'<[^>]+>', '', td_matches[0]).strip()
                
                # value อยู่ที่ td สุดท้ายที่มีข้อมูล
                value = None
                for td in reversed(td_matches):
                    td_clean = re.sub(r'<[^>]+>', '', td).strip()
                    if td_clean and td_clean not in ['-', '']:
                        value = td_clean
                        break
                
                if key and value:
                    # ทำความสะอาด key (ลบ whitespace)
                    key_clean = re.sub(r'\s+', '', key)
                    result[key_clean] = value
                    logger.info(f"✅ Parse HTML table row: {key_clean} = {value[:100]}...")
        
        # Fallback: ลองหาแบบ text format (| separated)
        lines = text.split('\n')
        pipe_lines = [line for line in lines if '|' in line]
        logger.info(f"🔍 [HTML Structure] พบบรรทัดที่มี '|' (pipe): {len(pipe_lines)} บรรทัด")
        
        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    key = parts[0].strip()
                    for part in reversed(parts):
                        if part.strip() and part.strip() not in ['-', '']:
                            value = part.strip()
                            break
                    else:
                        continue
                    
                    key_clean = re.sub(r'\s+', '', key)
                    if key_clean and value:
                        result[key_clean] = value
                        logger.info(f"✅ Parse text table: {key_clean} = {value[:100]}...")
        
        logger.info(f"🔍 [HTML Structure] สรุป: พบข้อมูลในตาราง {len(result)} รายการ")
        if result:
            logger.info(f"🔍 [HTML Structure] Keys ที่พบ: {', '.join(result.keys())}")
        
        return result
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern 1: TaxID 0993000003667 (อ่านจาก text โดยตรงก่อน - เพราะมีใน text)
        pattern1 = r'TaxID\s+(\d{13})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            tax_id = match.group(1)
            if tax_id.startswith('99'):
                tax_id = '0' + tax_id[1:]
            logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษีจาก TaxID: {tax_id}")
            return tax_id
        
        # Pattern 2: TaxID : 0993000003667 หรือ TaxID: 0993000003667
        pattern2 = r'TaxID\s*[:.]?\s*(\d{13})'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            tax_id = match.group(1)
            if tax_id.startswith('99'):
                tax_id = '0' + tax_id[1:]
            logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษี: {tax_id}")
            return tax_id
        
        # Pattern 3: Tax ID No. 0993000003667
        pattern3 = r'Tax\s+ID\s+No[.:]?\s*(\d{13})'
        match = re.search(pattern3, text, re.IGNORECASE)
        if match:
            tax_id = match.group(1)
            if tax_id.startswith('99'):
                tax_id = '0' + tax_id[1:]
            logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษี: {tax_id}")
            return tax_id
        
        # Pattern 4: เลขที่มีจุลภาค
        pattern4 = r'TaxID\s*[:.]?\s*([\d,]{15,})'
        match = re.search(pattern4, text, re.IGNORECASE)
        if match:
            tax_id = match.group(1).replace(',', '')
            if len(tax_id) == 13:
                if tax_id.startswith('99'):
                    tax_id = '0' + tax_id[1:]
                logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษี: {tax_id}")
                return tax_id
        
        # ลองหาจาก HTML table (fallback)
        table_data = self.parse_html_table(text)
        for key in table_data.keys():
            if 'TAXID' in key.upper() or ('TAX' in key.upper() and 'ID' in key.upper()):
                tax_id_str = table_data[key].strip()
                # หาเฉพาะตัวเลข 13 หลัก
                match = re.search(r'(\d{13})', tax_id_str)
                if match:
                    tax_id = match.group(1)
                    if tax_id.startswith('99'):
                        tax_id = '0' + tax_id[1:]
                    logger.info(f"✅ พบเลขประจำตัวผู้เสียภาษีจาก HTML table: {tax_id}")
                    return tax_id
        
        # Fallback: ถ้าไม่พบข้อมูล ให้ใช้ค่า default
        logger.info(f"⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        pattern = r'Date\s*[/:]?\s*วันที่\s*[:.]?\s*(\d{1,2})-([A-Z]{3})-(\d{4})'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            day = match.group(1).zfill(2)
            month_abbr = match.group(2).upper()
            year = match.group(3)
            
            month_map = {
                'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
            }
            
            month = month_map.get(month_abbr, '01')
            return f"{day}/{month}/{year}"
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท (ที่อยู่รวม)
        
        Returns:
            ที่อยู่บริษัท (string) หรือ None
        """
        lines = text.split('\n')
        address_lines = []
        collecting = False
        
        # หาตำแหน่งที่เริ่มต้นที่อยู่ (มักจะอยู่หลังชื่อบริษัท)
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # หา "Head Office:" หรือ "Address:" หรือ "ที่อยู่"
            if any(keyword in line_clean for keyword in ['Head Office:', 'Address:', 'ที่อยู่:', 'Address']):
                collecting = True
                # เก็บบรรทัดนี้ด้วย (ถ้ามีข้อมูล)
                if ':' in line_clean:
                    addr_part = line_clean.split(':', 1)[1].strip()
                    if addr_part:
                        address_lines.append(addr_part)
                continue
            
            # ถ้ากำลังเก็บข้อมูลที่อยู่
            if collecting:
                # หยุดเมื่อเจอ TaxID, Tax ID, Date, หรือ No.
                if any(keyword in line_clean for keyword in ['TaxID', 'Tax ID', 'Date', 'No.', 'TAX INVOICE']):
                    break
                
                # เก็บบรรทัดที่มีข้อมูล (ไม่ใช่บรรทัดว่าง)
                if line_clean and len(line_clean) > 5:
                    address_lines.append(line_clean)
        
        # รวมที่อยู่ทั้งหมด
        if address_lines:
            address = ' '.join(address_lines).strip()
            # ทำความสะอาด: ลบ space หลายตัว
            address = re.sub(r'\s+', ' ', address)
            return address if len(address) > 10 else None
        
        return None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """
        ดึงข้อมูลบัญชี (Account Name / Account Code)
        
        Returns:
            {'account_name': str, 'account_code': str}
        """
        # สำหรับ MSC ยังไม่มีข้อมูลบัญชีในเอกสาร
        # ต้องดึงจาก Chart of Accounts
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลหัก ณ ที่จ่าย
        
        Returns:
            {
                'withholding_tax_percent': float,  # เปอร์เซ็นต์
                'withholding_tax_amount': float    # จำนวนเงิน
            }
        """
        result = {
            'withholding_tax_percent': 0.0,
            'withholding_tax_amount': 0.0
        }
        
        # Pattern: หัก ณ ที่จ่าย 3% หรือ Withholding Tax 3%
        pattern_percent = r'(?:หัก\s*ณ\s*ที่จ่าย|Withholding\s*Tax)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*%'
        match = re.search(pattern_percent, text, re.IGNORECASE)
        if match:
            result['withholding_tax_percent'] = float(match.group(1))
        
        # Pattern: จำนวนเงินหัก ณ ที่จ่าย
        pattern_amount = r'(?:หัก\s*ณ\s*ที่จ่าย|Withholding\s*Tax)\s*(?:Amount)?\s*[:=]?\s*([\d,]+\.?\d*)'
        match = re.search(pattern_amount, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                result['withholding_tax_amount'] = float(amount_str)
            except ValueError:
                pass
        
        return result
    
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
        
        # สำหรับ MSC: Non-Taxable Amount (ไม่มีภาษี)
        # Pattern: Non-Taxable Amount / ไม่มีภาษีมูลค่าเพิ่ม 6,000.00
        pattern_non_vat = r'Non-Taxable Amount\s*[/:]?\s*ไม่มีภาษีมูลค่าเพิ่ม\s*([\d,]+\.?\d*)'
        match = re.search(pattern_non_vat, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                result['amount_before_vat'] = float(amount_str)
                result['vat_amount'] = 0.0  # ไม่มีภาษี
            except ValueError:
                pass
        
        # Total / รวม
        pattern_total = r'Total\s*[/:]?\s*รวม\s*([\d,]+\.?\d*)'
        match = re.search(pattern_total, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                result['total_amount'] = float(amount_str)
            except ValueError:
                pass
        
        return result
    
    def extract_document_number(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        logger.info("🔍 [Document Number] เริ่มค้นหาเลขที่เอกสาร...")
        logger.info(f"🔍 [Document Number] ตัวอย่าง text (300 ตัวอักษรแรก): {text[:300].replace(chr(10), '\\n')}...")
        
        # Pattern 1: TAX INVOICE/RECEIPT No. 2511200301 (อ่านจาก text โดยตรงก่อน - เพราะมีใน text)
        # รองรับทั้ง TAX INVOICE/RECEIPT No. และ TAX INVOICE / RECEIPT No.
        pattern1 = r'TAX\s+INVOICE\s*/?\s*RECEIPT\s+No\.\s*[:.]?\s*(\d+)'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            doc_num = match.group(1).strip()
            logger.info(f"✅ พบเลขที่เอกสารจาก TAX INVOICE/RECEIPT No.: {doc_num}")
            return doc_num
        
        # อ่านทีละบรรทัดเพื่อหา TAX INVOICE/RECEIPT No. 2511200301
        lines = text.split('\n')
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # Pattern 2: TAX INVOICE/RECEIPT No. 2511200301 (ในบรรทัด)
            pattern2 = r'TAX\s+INVOICE\s*/?\s*RECEIPT\s+No\.\s*[:.]?\s*(\d+)'
            match = re.search(pattern2, line_clean, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                logger.info(f"✅ พบเลขที่เอกสารจากบรรทัด '{line_clean[:50]}...': {doc_num}")
                return doc_num
        
        # Pattern 3: TAX INVOICE No. 2511200301 (fallback)
        pattern3 = r'TAX\s+INVOICE\s+No\.\s*[:.]?\s*(\d+)'
        match = re.search(pattern3, text, re.IGNORECASE)
        if match:
            doc_num = match.group(1).strip()
            logger.info(f"✅ พบเลขที่เอกสารจาก TAX INVOICE No.: {doc_num}")
            return doc_num
        
        # Pattern 4: RECEIPT No. 2511200301 (fallback)
        pattern4 = r'RECEIPT\s+No\.\s*[:.]?\s*(\d+)'
        match = re.search(pattern4, text, re.IGNORECASE)
        if match:
            doc_num = match.group(1).strip()
            logger.info(f"✅ พบเลขที่เอกสารจาก RECEIPT No.: {doc_num}")
            return doc_num
        
        # Pattern 5: No. 2511200301 (ตัวเลขล้วนๆ 8-15 หลัก) - เพิ่ม pattern นี้ก่อน Pattern 6
        # รองรับรูปแบบ: No. 2511200301 หรือ No.: 2511200301 หรือ No.2511200301
        pattern5 = r'(?:^|\s)No\.\s*[:.]?\s*(\d{8,15})(?:\s|$)'
        match = re.search(pattern5, text, re.IGNORECASE | re.MULTILINE)
        if match:
            doc_num = match.group(1).strip()
            logger.info(f"✅ พบเลขที่เอกสารจาก No. (ตัวเลขล้วน): {doc_num}")
            return doc_num
        
        # อ่านทีละบรรทัดเพื่อหา No. 2511200301 (ตัวเลขล้วนๆ)
        logger.info(f"🔍 [Document Number] กำลังค้นหา 'No.' ใน {len(lines)} บรรทัด...")
        for idx, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # ตรวจสอบว่ามี "No." ในบรรทัดนี้หรือไม่
            if 'No.' in line_clean or 'no.' in line_clean.lower():
                logger.info(f"🔍 [Document Number] บรรทัด {idx+1} พบ 'No.': {line_clean[:100]}...")
            
            # Pattern 5b: No. 2511200301 ในบรรทัดเดียว (ตัวเลขล้วนๆ)
            pattern5b = r'No\.\s*[:.]?\s*(\d{8,15})'
            match = re.search(pattern5b, line_clean, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                logger.info(f"✅ พบเลขที่เอกสารจากบรรทัด {idx+1} 'No.': {doc_num} (จาก: {line_clean[:100]}...)")
                return doc_num
        
        # ลองหาจาก HTML table (fallback)
        logger.info("🔍 [Document Number] กำลังค้นหาจาก HTML table...")
        table_data = self.parse_html_table(text)
        logger.info(f"🔍 [Document Number] พบข้อมูลใน table: {len(table_data)} รายการ")
        if table_data:
            logger.info(f"🔍 [Document Number] Keys ใน table: {', '.join(table_data.keys())}")
        
        for key in table_data.keys():
            logger.info(f"🔍 [Document Number] ตรวจสอบ key: {key}")
            if ('NO' in key.upper() or 'INVOICE' in key.upper() or 'DOCUMENT' in key.upper() or 'RECEIPT' in key.upper()) and len(key) > 2:
                doc_num = table_data[key].strip()
                logger.info(f"🔍 [Document Number] พบ key ที่เกี่ยวข้อง: {key} = {doc_num}")
                # หาเฉพาะตัวเลข (เช่น 2511200301) - ไม่เอาแค่ตัวอักษรเดียว
                match = re.search(r'(\d{8,})', doc_num)
                if match:
                    doc_num = match.group(1).strip()
                    logger.info(f"✅ พบเลขที่เอกสารจาก HTML table (key: {key}): {doc_num}")
                    return doc_num
        
        # Pattern 6: No. 202511-008 หรือ Invoice No. XXX (fallback สำหรับรูปแบบอื่นๆ)
        patterns = [
            r'No\.\s*[:.]?\s*([A-Z0-9\-]+)',  # No.: 202511-008
            r'NO\.\s*[:.]?\s*([A-Z0-9\-]+)',  # NO.: 202511-008
            r'Invoice\s+No\.\s*[:.]?\s*([A-Z0-9\-]+)',  # Invoice No.: XXX
            r'INVOICE\s+NO\.\s*[:.]?\s*([A-Z0-9\-]+)',  # INVOICE NO.: XXX
            r'เลขที่\s*[:.]?\s*([A-Z0-9\-]+)',  # เลขที่: XXX
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                # ตรวจสอบว่าไม่ใช่ตัวอักษรเดียว และเป็นตัวเลขที่ยาวพอ (อย่างน้อย 8 หลัก)
                if len(doc_num) > 1:
                    # ถ้าเป็นตัวเลขล้วนๆ ให้ตรวจสอบว่ายาวพอ
                    if doc_num.isdigit() and len(doc_num) >= 8:
                        logger.info(f"✅ พบเลขที่เอกสาร: {doc_num}")
                        return doc_num
                    # ถ้าไม่ใช่ตัวเลขล้วนๆ ก็ใช้ได้ (เช่น 202511-008)
                    elif not doc_num.isdigit():
                        logger.info(f"✅ พบเลขที่เอกสาร: {doc_num}")
                        return doc_num
        
        # Fallback: ลองอ่านจากชื่อไฟล์
        if filename:
            name_without_ext = filename.replace('.pdf', '').replace('.PDF', '')
            parts = name_without_ext.split('_')
            if parts:
                doc_num = parts[0]
                logger.info(f"✅ พบเลขที่เอกสารจากชื่อไฟล์: {doc_num}")
                return doc_num
        
        logger.warning("⚠️ ไม่พบเลขที่เอกสาร")
        return None
    
    def extract_invoice_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่ใบแจ้งหนี้"""
        pattern = r'No\.\s*(\d{10,})'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def extract_bl_number(self, text: str) -> Optional[str]:
        """ดึงเลข BL (Bill of Lading)"""
        # Pattern: BL(s) : MEDUW0265381
        pattern = r'BL\(s\)\s*[:]\s*([A-Z0-9]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Pattern 2: BL: MEDUW0265381
        pattern2 = r'BL\s*[:]\s*([A-Z0-9]+)'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจจับประเภทเอกสาร
        
        Args:
            text: ข้อความ
            amounts: ยอดเงิน
            withholding: ข้อมูลหัก ณ ที่จ่าย
        
        Returns:
            1 = เอกสารมีภาษีมูลค่าเพิ่ม
            2 = เอกสารไม่มีภาษีมูลค่าเพิ่ม
        """
        # ตรวจสอบว่ามี VAT หรือไม่
        vat_amount = amounts.get('vat_amount') or 0
        has_vat = vat_amount > 0
        
        # ใช้แค่ 2 ประเภท: มีภาษี (1) หรือไม่มีภาษี (2)
        if has_vat:
            return 1  # มีภาษีมูลค่าเพิ่ม
        else:
            return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร MSC
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร MSC หรือไม่
        is_msc = self.is_company_document(text)
        
        if not is_msc:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร MSC'
            }
        
        # หาส่วนต้นฉบับของใบกำกับภาษีก่อน
        original_section = self.extract_original_invoice_section(text)
        if original_section:
            # ใช้เฉพาะส่วนต้นฉบับในการดึงข้อมูล
            text = original_section
            logger.info("✅ ใช้เฉพาะส่วนต้นฉบับของใบกำกับภาษีในการดึงข้อมูล")
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        date = self.extract_date(text)
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        document_number = self.extract_document_number(text, filename)
        invoice_number = self.extract_invoice_number(text)
        bl_number = self.extract_bl_number(text)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # หมายเหตุ: BL + document_number (ถ้ามี BL) หรือ document_number อย่างเดียว
        if bl_number:
            remark = f"{bl_number} {document_number}" if document_number else bl_number
        else:
            remark = document_number
        
        # Log ข้อมูลที่ดึงได้
        logger.info(f"🔍 [Extract All Data] document_number ที่ดึงได้: {document_number}")
        
        return {
            'success': True,
            'company': 'MSC',
            'company_name': company_name,
            'tax_id': tax_id,
            'date': date,
            'address': address,
            'account_name': account_info['account_name'],
            'account_code': account_info['account_code'],
            'withholding_tax_percent': withholding['withholding_tax_percent'],
            'withholding_tax_amount': withholding['withholding_tax_amount'],
            'amount_before_vat': amounts['amount_before_vat'],
            'vat_amount': amounts['vat_amount'],
            'total_amount': amounts['total_amount'],
            'document_number': document_number,  # เพิ่ม document_number ที่ขาดหายไป
            'remark': remark,
            'new_filename': f"{invoice_number}.pdf" if invoice_number else None,
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,
            'bl_number': bl_number
        }
