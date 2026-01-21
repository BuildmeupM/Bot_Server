"""
Omise Company Limited Invoice Extractor
=======================================
Extractor สำหรับดึงข้อมูลจาก Omise Company Limited (Head Office)

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class OmiseExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก Omise Company Limited (Head Office)"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "Omise Company Limited",
        "Omise Company Limited (Head Office)",
        "OMISE"
    ]
    
    # Tax ID
    TAX_ID = "0105556091152"
    
    def __init__(self):
        """Initialize Omise Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ Omise Company Limited หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "Omise Company Limited"
        2. Tax ID "0105556091152"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร Omise Company Limited (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105556091152"
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
        return "Omise Company Limited (Head Office)"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: Tax ID: 0105556091152
        patterns = [
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0105556091152
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID: 0105556091152
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี: 0105556091152
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
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: Date | วันที่
        #         (บรรทัดว่าง)
        #         OMTH202511030233
        #         03/11/2025 (ประมาณ 3 บรรทัดถัดจาก "Date | วันที่")
        
        logger.info("🔍 [Extract Date] เริ่มค้นหาวันที่...")
        lines = text.split('\n')
        
        for idx, line in enumerate(lines):
            line_clean = line.strip()
            
            # หา "Date | วันที่"
            if 'Date' in line_clean and '|' in line_clean and 'วันที่' in line_clean:
                logger.info(f"✅ [Extract Date] พบ 'Date | วันที่' ที่บรรทัด {idx+1}: {line_clean[:100]}...")
                
                # อ่านบรรทัดถัดไปประมาณ 3 บรรทัด (index + 1, +2, +3)
                for offset in [1, 2, 3]:
                    if idx + offset < len(lines):
                        next_line = lines[idx + offset].strip()
                        logger.info(f"🔍 [Extract Date] ตรวจสอบบรรทัด {idx+offset+1}: {next_line[:100]}...")
                        
                        # ตรวจสอบว่าเป็นรูปแบบวันที่ (dd/mm/yyyy)
                        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', next_line)
                        if date_match:
                            day = date_match.group(1).zfill(2)
                            month = date_match.group(2).zfill(2)
                            year = date_match.group(3)
                            date_str = f"{day}/{month}/{year}"
                            logger.info(f"✅ [Extract Date] พบวันที่: {date_str} (บรรทัด {idx+offset+1})")
                            return date_str
        
        # Fallback: ลองหาแบบ regex pattern
        patterns = [
            r'Date\s*\|\s*วันที่[^\n]*\n[^\d]*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # Date | วันที่\n03/11/2025
            r'วันที่\s*\|\s*Date[^\n]*\n[^\d]*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # วันที่ | Date\n03/11/2025
            r'Date\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # Date: 03/11/2025
            r'วันที่\s*[:.]?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # วันที่: 03/11/2025
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                date_str = f"{day}/{month}/{year}"
                logger.info(f"✅ [Extract Date] พบวันที่ (regex): {date_str}")
                return date_str
        
        logger.warning("⚠️ [Extract Date] ไม่พบวันที่")
        return None
    
    def extract_document_number(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: Date | วันที่
        #         (บรรทัดว่าง)
        #         OMTH202511030233 (ประมาณ 2 บรรทัดถัดจาก "Date | วันที่")
        #         03/11/2025
        
        logger.info("🔍 [Extract Document Number] เริ่มค้นหาเลขที่เอกสาร...")
        lines = text.split('\n')
        
        for idx, line in enumerate(lines):
            line_clean = line.strip()
            
            # หา "Date | วันที่"
            if 'Date' in line_clean and '|' in line_clean and 'วันที่' in line_clean:
                logger.info(f"✅ [Extract Document Number] พบ 'Date | วันที่' ที่บรรทัด {idx+1}: {line_clean[:100]}...")
                
                # อ่านบรรทัดถัดไปประมาณ 2 บรรทัด (index + 1, +2)
                for offset in [1, 2]:
                    if idx + offset < len(lines):
                        next_line = lines[idx + offset].strip()
                        logger.info(f"🔍 [Extract Document Number] ตรวจสอบบรรทัด {idx+offset+1}: {next_line[:100]}...")
                        
                        # ตรวจสอบว่าเป็นรูปแบบเลขที่เอกสาร (ตัวอักษรและตัวเลข 10 หลักขึ้นไป)
                        # เช่น OMTH202511030233
                        doc_match = re.search(r'([A-Z0-9]{10,})', next_line)
                        if doc_match:
                            doc_num = doc_match.group(1).strip()
                            # ตรวจสอบว่าไม่ใช่รูปแบบวันที่ (dd/mm/yyyy)
                            if not re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{4}$', doc_num):
                                logger.info(f"✅ [Extract Document Number] พบเลขที่เอกสาร: {doc_num} (บรรทัด {idx+offset+1})")
                                return doc_num
        
        # Fallback: ลองหาแบบ regex pattern
        patterns = [
            # รูปแบบที่มี Receipt No.
            r'Receipt\s+No\.\s*[^\n]*\n[^\w]*([A-Z0-9]{10,})',  # Receipt No.\nOMTH202511030233
            r'เลขที่ใบเสร็จ[^\n]*\n[^\w]*([A-Z0-9]{10,})',  # เลขที่ใบเสร็จ\nOMTH202511030233
            # รูปแบบทั่วไป
            r'Receipt\s+No\.\s*[:.]?\s*([A-Z0-9]{10,})',  # Receipt No.: OMTH202511030233
            r'เลขที่\s*[:.]?\s*([A-Z0-9]{10,})',  # เลขที่: OMTH202511030233
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                doc_num = match.group(1).strip()
                if len(doc_num) >= 10:
                    logger.info(f"✅ [Extract Document Number] พบเลขที่เอกสาร (regex): {doc_num}")
                    return doc_num
        
        logger.warning("⚠️ [Extract Document Number] ไม่พบเลขที่เอกสาร")
        return None
    
    def parse_html_table(self, text: str) -> Dict[str, str]:
        """
        Parse ข้อมูลจากตาราง HTML หรือ text format (| separated)
        หา pattern เช่น: Subtotal | ค่าธรรมเนียมรวม | 166.65
        หรือ: VAT | ภาษีมูลค่าเพิ่ม 7% | 11.67
        
        Returns:
            Dictionary ที่มี key-value จากตาราง
        """
        result = {}
        
        logger.info("🔍 [HTML Table] เริ่ม parse HTML table...")
        
        # Pattern สำหรับหา <tr>...</tr> ที่มีหลาย <td>
        tr_pattern = r'<tr[^>]*>(.*?)</tr>'
        tr_matches = re.findall(tr_pattern, text, re.IGNORECASE | re.DOTALL)
        
        logger.info(f"🔍 [HTML Table] พบ <tr> tags: {len(tr_matches)} แถว")
        
        for idx, tr_content in enumerate(tr_matches):
            logger.info(f"🔍 [HTML Table] แถว {idx+1}: {tr_content[:150]}...")
            
            # หา <td> ทั้งหมดในแถว (รองรับ <br/> tag)
            td_pattern = r'<td[^>]*>(.*?)</td>'
            td_matches = re.findall(td_pattern, tr_content, re.IGNORECASE | re.DOTALL)
            
            if len(td_matches) >= 2:
                # ทำความสะอาด <td> content (ลบ HTML tags แต่เก็บข้อความ)
                td_cleaned = []
                for td in td_matches:
                    # แทนที่ <br/> และ <br> ด้วย space
                    td_text = re.sub(r'<br\s*/?>', ' ', td, flags=re.IGNORECASE)
                    # ลบ HTML tags อื่นๆ
                    td_text = re.sub(r'<[^>]+>', '', td_text)
                    # ทำความสะอาด whitespace
                    td_text = re.sub(r'\s+', ' ', td_text).strip()
                    td_cleaned.append(td_text)
                
                logger.info(f"🔍 [HTML Table] แถว {idx+1} หลังทำความสะอาด: {td_cleaned}")
                
                # key อยู่ที่ td แรก
                key = td_cleaned[0]
                
                # value อยู่ที่ td สุดท้ายที่มีข้อมูล
                value = None
                for td in reversed(td_cleaned):
                    if td and td not in ['-', '']:
                        value = td
                        break
                
                if key and value:
                    # ทำความสะอาด key (ลบ whitespace)
                    key_clean = re.sub(r'\s+', '', key)
                    result[key_clean] = value
                    logger.info(f"✅ [HTML Table] Parse HTML table row: {key_clean} = {value[:100]}...")
        
        # Fallback: ลองหาแบบ text format (| separated)
        # รูปแบบ: Subtotal | ค่าธรรมเนียมรวม | 166.65
        # หรือ: VAT | ภาษีมูลค่าเพิ่ม 7% | 11.67
        # หรือ: DESCRIPTION | รายการ | AMOUNT | จำนวนเงิน (THB)
        #      Subtotal | ค่าธรรมเนียมรวม | 166.65
        logger.info("🔍 [Text Table] เริ่ม parse text format (| separated)...")
        lines = text.split('\n')
        logger.info(f"🔍 [Text Table] จำนวนบรรทัด: {len(lines)}")
        
        for idx, line in enumerate(lines):
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                logger.info(f"🔍 [Text Table] บรรทัด {idx+1}: {len(parts)} ส่วน - {line[:150]}...")
                
                if len(parts) >= 2:
                    # key อยู่ที่ส่วนแรก (เช่น "Subtotal", "VAT", "Total")
                    key = parts[0].strip()
                    # value อยู่ที่ส่วนสุดท้าย (เช่น "166.65", "11.67", "178.32")
                    value = parts[-1].strip()
                    
                    # ทำความสะอาด key (ลบ whitespace)
                    key_clean = re.sub(r'\s+', '', key)
                    
                    # ตรวจสอบว่า key ไม่ใช่ header row
                    if key_clean.upper() in ['DESCRIPTION', 'รายการ', 'AMOUNT', 'จำนวนเงิน(THB)', 'DESCRIPTIONรายการ', 'AMOUNTจำนวนเงิน(THB)']:
                        logger.info(f"🔍 [Text Table] ข้าม header row: {key_clean}")
                        continue
                    
                    # ตรวจสอบว่า value เป็นตัวเลข (ยอดเงิน) - รองรับทั้ง 166.65 และ 178.32
                    if re.match(r'^[\d,]+\.?\d*$', value):
                        if key_clean and value:
                            result[key_clean] = value
                            logger.info(f"✅ [Text Table] Parse text table: {key_clean} = {value}")
                    # ถ้า value ไม่ใช่ตัวเลข แต่มี 3 ส่วนขึ้นไป ให้ลองหาตัวเลขจากส่วนอื่นๆ
                    elif len(parts) >= 3:
                        # ลองหาตัวเลขจากส่วนที่ 2 หรือ 3
                        for part_idx, part in enumerate(parts[1:], start=1):
                            part_clean = part.strip()
                            if re.match(r'^[\d,]+\.?\d*$', part_clean):
                                if key_clean and part_clean:
                                    result[key_clean] = part_clean
                                    logger.info(f"✅ [Text Table] Parse text table (multi-column, ส่วนที่ {part_idx+1}): {key_clean} = {part_clean}")
                                    break
        
        logger.info(f"🔍 [Summary] สรุปข้อมูลที่ parse ได้: {len(result)} รายการ")
        for key, value in result.items():
            logger.info(f"   - {key} = {value}")
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        จากตาราง:
        Subtotal | ค่าธรรมเนียมรวม | 166.65
        VAT | ภาษีมูลค่าเพิ่ม 7% | 11.67
        Total | ราคารวมทั้งสิ้น | 178.32
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (166.65) - จาก Subtotal
                'vat_amount': float,          # ยอดภาษี (11.67) - จาก VAT
                'total_amount': float         # ยอดรวม (178.32) - จาก Total
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        logger.info("🔍 [Extract Amounts] เริ่มดึงยอดเงิน...")
        
        # อ่านจาก HTML table
        table_data = self.parse_html_table(text)
        
        logger.info(f"🔍 [Extract Amounts] ข้อมูลจาก table: {len(table_data)} รายการ")
        for key, value in table_data.items():
            logger.info(f"   - {key} = {value}")
        
        # หายอดก่อนภาษีจาก "Subtotal" หรือ "ค่าธรรมเนียมรวม"
        subtotal_keys = ['Subtotal', 'SUBTOTAL', 'ค่าธรรมเนียมรวม', 'Subtotalค่าธรรมเนียมรวม']
        for search_key in subtotal_keys:
            # ตรวจสอบทั้ง key ที่ทำความสะอาดแล้วและ key ที่มี whitespace
            for table_key, table_value in table_data.items():
                if search_key.lower() in table_key.lower() or table_key.lower() in search_key.lower():
                    try:
                        amount_str = str(table_value).replace(',', '').replace(' ', '')
                        amount = float(amount_str)
                        if amount > 0:
                            result['amount_before_vat'] = amount
                            logger.info(f"✅ [Extract Amounts] พบยอดก่อนภาษี: {amount} (จาก key: {table_key})")
                            break
                    except (ValueError, TypeError):
                        continue
            if result['amount_before_vat'] is not None:
                break
        
        # หายอดภาษีจาก "VAT" หรือ "ภาษีมูลค่าเพิ่ม"
        vat_keys = ['VAT', 'ภาษีมูลค่าเพิ่ม', 'VATภาษีมูลค่าเพิ่ม']
        for search_key in vat_keys:
            # ตรวจสอบทั้ง key ที่ทำความสะอาดแล้วและ key ที่มี whitespace
            for table_key, table_value in table_data.items():
                if search_key.lower() in table_key.lower() or table_key.lower() in search_key.lower():
                    try:
                        amount_str = str(table_value).replace(',', '').replace(' ', '')
                        amount = float(amount_str)
                        if amount > 0:
                            result['vat_amount'] = amount
                            logger.info(f"✅ [Extract Amounts] พบยอดภาษี: {amount} (จาก key: {table_key})")
                            break
                    except (ValueError, TypeError):
                        continue
            if result['vat_amount'] is not None:
                break
        
        # หายอดรวมจาก "Total" หรือ "ราคารวมทั้งสิ้น"
        # รองรับ key ที่รวมกัน เช่น "Total|ราคารวมทั้งสิ้น" หรือ "Totalราคารวมทั้งสิ้น"
        total_keywords = ['Total', 'TOTAL', 'ราคารวมทั้งสิ้น']
        for table_key, table_value in table_data.items():
            logger.info(f"🔍 [Extract Amounts] ตรวจสอบ key สำหรับยอดรวม: '{table_key}' = '{table_value}'")
            
            # ตรวจสอบว่า key มี "Total" หรือ "ราคารวมทั้งสิ้น"
            # แต่ต้องไม่ใช่ "Subtotal" (เพราะ Subtotal คือยอดก่อนภาษี)
            has_total = any(keyword.lower() in table_key.lower() for keyword in total_keywords)
            is_subtotal = 'Subtotal' in table_key or 'SUBTOTAL' in table_key or 'ค่าธรรมเนียมรวม' in table_key
            
            if has_total and not is_subtotal:
                try:
                    amount_str = str(table_value).replace(',', '').replace(' ', '')
                    amount = float(amount_str)
                    if amount > 0:
                        result['total_amount'] = amount
                        logger.info(f"✅ [Extract Amounts] พบยอดรวม: {amount} (จาก key: {table_key})")
                        break
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️ [Extract Amounts] ไม่สามารถแปลงค่า '{table_value}' เป็นตัวเลข: {e}")
                    continue
        
        # Fallback: ลองหาแบบ regex pattern (อ่านจาก text โดยตรง)
        logger.info("🔍 [Extract Amounts] กำลังลองหาแบบ regex pattern...")
        
        if result['amount_before_vat'] is None:
            patterns = [
                r'Subtotal\s*\|\s*[^|]*\|\s*([\d,]+\.?\d*)',  # Subtotal | ... | 166.65
                r'Subtotal\s*\|\s*ค่าธรรมเนียมรวม\s*\|\s*([\d,]+\.?\d*)',  # Subtotal | ค่าธรรมเนียมรวม | 166.65
                r'ค่าธรรมเนียมรวม\s*\|\s*([\d,]+\.?\d*)',  # ค่าธรรมเนียมรวม | 166.65
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '')
                        amount = float(amount_str)
                        result['amount_before_vat'] = amount
                        logger.info(f"✅ [Extract Amounts] พบยอดก่อนภาษี (regex): {amount}")
                        break
                    except (ValueError, IndexError):
                        continue
        
        if result['vat_amount'] is None:
            patterns = [
                r'VAT\s*\|\s*[^|]*\|\s*([\d,]+\.?\d*)',  # VAT | ... | 11.67
                r'VAT\s*\|\s*ภาษีมูลค่าเพิ่ม[^|]*\|\s*([\d,]+\.?\d*)',  # VAT | ภาษีมูลค่าเพิ่ม 7% | 11.67
                r'ภาษีมูลค่าเพิ่ม[^|]*\|\s*([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม | 11.67
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '')
                        amount = float(amount_str)
                        result['vat_amount'] = amount
                        logger.info(f"✅ [Extract Amounts] พบยอดภาษี (regex): {amount}")
                        break
                    except (ValueError, IndexError):
                        continue
        
        if result['total_amount'] is None:
            patterns = [
                r'Total\s*\|\s*[^|]*\|\s*([\d,]+\.?\d*)',  # Total | ... | 178.32
                r'Total\s*\|\s*ราคารวมทั้งสิ้น\s*\|\s*([\d,]+\.?\d*)',  # Total | ราคารวมทั้งสิ้น | 178.32
                r'ราคารวมทั้งสิ้น\s*\|\s*([\d,]+\.?\d*)',  # ราคารวมทั้งสิ้น | 178.32
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '')
                        amount = float(amount_str)
                        result['total_amount'] = amount
                        logger.info(f"✅ [Extract Amounts] พบยอดรวม (regex): {amount}")
                        break
                    except (ValueError, IndexError):
                        continue
        
        logger.info(f"🔍 [Extract Amounts] สรุปยอดเงินที่อ่านได้:")
        logger.info(f"   - ยอดก่อนภาษี: {result['amount_before_vat']}")
        logger.info(f"   - ยอดภาษี: {result['vat_amount']}")
        logger.info(f"   - ยอดรวม: {result['total_amount']}")
        
        return result
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: 1448/4, J2 Building, Soi Ladprao 87
        (Chandrasuk), Praditmanutham Road,
        Klongchan, Bangkapi, Bangkok, 10240
        
        Returns:
            ที่อยู่รวม (string)
        """
        # ใช้ที่อยู่ที่กำหนดให้
        return "1448/4, J2 Building, Soi Ladprao 87 (Chandrasuk), Praditmanutham Road, Klongchan, Bangkapi, Bangkok, 10240"
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        return {
            'account_name': None,
            'account_code': None
        }
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงข้อมูลหัก ณ ที่จ่าย"""
        return {
            'withholding_tax_percent': 0.0,
            'withholding_tax_amount': 0.0
        }
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ"""
        # ไม่มี remark สำหรับ Omise
        return None
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """
        ตรวจจับประเภทเอกสาร
        
        Returns:
            1 = เอกสารมีภาษีมูลค่าเพิ่ม (VAT)
        """
        return 1  # มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร Omise Company Limited
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร Omise Company Limited หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร Omise Company Limited'
            }
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        branch = self.extract_branch(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text, filename)
        address = self.extract_address(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        withholding = self.extract_withholding_tax(text)
        remark = self.extract_remark(text, filename)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # สร้างชื่อไฟล์ใหม่: ค่าธรรมเนียม_OMISE
        new_filename = "ค่าธรรมเนียม_OMISE"
        
        # แยกที่อยู่เป็นส่วนๆ
        # ที่อยู่: 1448/4, J2 Building, Soi Ladprao 87 (Chandrasuk), Praditmanutham Road, Klongchan, Bangkapi, Bangkok, 10240
        address_full = address or ''
        building_number = '1448/4'  # เลขที่
        other_info = 'J2 Building, Soi Ladprao 87 (Chandrasuk)'  # อื่นๆ
        soi = ''  # ซอย/ตรอก
        road = 'Praditmanutham Road'  # ถนน
        subdistrict = 'Klongchan'  # แขวง
        district = 'Bangkapi'  # เขต
        province = 'Bangkok'  # จังหวัด
        postal_code = '10240'  # รหัสไปรษณีย์
        
        return {
            'success': True,
            'company': 'OMISE',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number,  # เลขที่ (1448/4)
            'other_info': other_info,  # อื่นๆ (J2 Building, Soi Ladprao 87 (Chandrasuk))
            'soi': soi,  # ซอย/ตรอก
            'road': road,  # ถนน (Praditmanutham Road)
            'subdistrict': subdistrict,  # แขวง (Klongchan)
            'district': district,  # เขต (Bangkapi)
            'province': province,  # จังหวัด (Bangkok)
            'postal_code': postal_code,  # รหัสไปรษณีย์ (10240)
            'account_name': account_info['account_name'],
            'account_code': account_info['account_code'],
            'withholding_tax_percent': withholding['withholding_tax_percent'],
            'withholding_tax_amount': withholding['withholding_tax_amount'],
            'amount_before_vat': amounts['amount_before_vat'],
            'vat_amount': amounts['vat_amount'],
            'total_amount': amounts['total_amount'],
            'remark': remark,
            'new_filename': new_filename,
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,  # 1 = มีภาษีมูลค่าเพิ่ม
        }

