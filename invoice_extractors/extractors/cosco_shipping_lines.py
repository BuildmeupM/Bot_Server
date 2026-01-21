"""
COSCO Shipping Lines Invoice Extractor
======================================
Extractor สำหรับดึงข้อมูลจาก COSCO SHIPPING LINES (THAILAND) CO.,LTD.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class CoscoShippingLinesExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก COSCO SHIPPING LINES (THAILAND) CO.,LTD."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "COSCO SHIPPING LINES (THAILAND) CO.,LTD.",
        "COSCO SHIPPING LINES (THAILAND)",
        "COSCO SHIPPING LINES",
        "COSCO"
    ]
    
    # Tax ID
    TAX_ID = "0994002733078"
    
    def __init__(self):
        """Initialize COSCO Shipping Lines Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ COSCO SHIPPING LINES (THAILAND) CO.,LTD. หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "COSCO SHIPPING LINES (THAILAND) CO.,LTD."
        2. Tax ID "0994002733078"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร COSCO Shipping Lines (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0994002733078"
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
        return "COSCO SHIPPING LINES (THAILAND) CO.,LTD."
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TAX ID: 0994002733078
        patterns = [
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID: 0994002733078
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0994002733078
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0994002733078
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี 0994002733078
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
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: ISSUE DATE: 03 Nov 2025
        patterns = [
            r'ISSUE\s+DATE\s*[:.]?\s*(\d{1,2})\s+(\w{3})\s+(\d{4})',  # ISSUE DATE: 03 Nov 2025
            r'Issue\s+Date\s*[:.]?\s*(\d{1,2})\s+(\w{3})\s+(\d{4})',  # Issue Date: 03 Nov 2025
            r'วันที่\s*[:.]?\s*(\d{1,2})\s+(\w{3})\s+(\d{4})',  # วันที่: 03 Nov 2025
        ]
        
        # Mapping เดือน
        month_map = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                month_str = match.group(2).lower()[:3]  # เอา 3 ตัวแรก
                year = match.group(3)
                
                # แปลงเดือน
                month = month_map.get(month_str, '01')
                
                return f"{day}/{month}/{year}"
        
        return None
    
    def parse_html_table(self, text: str) -> Dict[str, str]:
        """
        Parse ข้อมูลจากตาราง HTML
        หา pattern เช่น: <tr><td>TAX INVOICE NO.</td><td>ST2511000170</td></tr>
        หรือ: TAX INVOICE NO. | ST2511000170 (text format)
        
        Returns:
            Dictionary ที่มี key-value จากตาราง
        """
        result = {}
        
        # Log โครงสร้าง HTML ที่พบ
        logger.info("🔍 [COSCO HTML Structure] เริ่มตรวจสอบโครงสร้าง HTML...")
        
        # ตรวจสอบว่ามี HTML tags หรือไม่
        has_html_tags = bool(re.search(r'<[^>]+>', text))
        logger.info(f"🔍 [COSCO HTML Structure] มี HTML tags: {has_html_tags}")
        
        # แสดงตัวอย่าง text (300 ตัวอักษรแรก)
        text_preview = text[:300].replace('\n', '\\n')
        logger.info(f"🔍 [COSCO HTML Structure] ตัวอย่าง text (300 ตัวอักษรแรก): {text_preview}...")
        
        # Pattern สำหรับหา <tr>...</tr> ที่มีหลาย <td>
        tr_pattern = r'<tr[^>]*>(.*?)</tr>'
        tr_matches = re.findall(tr_pattern, text, re.IGNORECASE | re.DOTALL)
        
        logger.info(f"🔍 [COSCO HTML Structure] พบ <tr> tags: {len(tr_matches)} แถว")
        
        for idx, tr_content in enumerate(tr_matches):
            # หา <td> ทั้งหมดในแถว
            td_pattern = r'<td[^>]*>([^<]+(?:<[^>]+>)*[^<]*)</td>'
            td_matches = re.findall(td_pattern, tr_content, re.IGNORECASE | re.DOTALL)
            
            logger.info(f"🔍 [COSCO HTML Structure] แถว {idx+1}: พบ <td> {len(td_matches)} คอลัมน์")
            if td_matches:
                logger.info(f"🔍 [COSCO HTML Structure] แถว {idx+1} เนื้อหา: {tr_content[:150]}...")
            
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
        logger.info(f"🔍 [COSCO HTML Structure] พบบรรทัดที่มี '|' (pipe): {len(pipe_lines)} บรรทัด")
        
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
        
        logger.info(f"🔍 [COSCO HTML Structure] สรุป: พบข้อมูลในตาราง {len(result)} รายการ")
        if result:
            logger.info(f"🔍 [COSCO HTML Structure] Keys ที่พบ: {', '.join(result.keys())}")
        
        return result
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        logger.info("🔍 [COSCO Document Number] เริ่มค้นหาเลขที่เอกสาร...")
        logger.info(f"🔍 [COSCO Document Number] ตัวอย่าง text (400 ตัวอักษรแรก): {text[:400].replace(chr(10), '\\n')}...")
        
        # ลองหาจาก HTML table ก่อน
        logger.info("🔍 [COSCO Document Number] กำลังค้นหาจาก HTML table...")
        table_data = self.parse_html_table(text)
        logger.info(f"🔍 [COSCO Document Number] พบข้อมูลใน table: {len(table_data)} รายการ")
        if table_data:
            logger.info(f"🔍 [COSCO Document Number] Keys ใน table: {', '.join(table_data.keys())}")
        
        for key in table_data.keys():
            logger.info(f"🔍 [COSCO Document Number] ตรวจสอบ key: {key}")
            if ('TAXINVOICENO' in key.upper() or 'INVOICENO' in key.upper() or 
                ('TAX' in key.upper() and 'INVOICE' in key.upper() and 'NO' in key.upper())):
                doc_num = table_data[key].strip()
                logger.info(f"🔍 [COSCO Document Number] พบ key ที่เกี่ยวข้อง: {key} = {doc_num}")
                # หาเฉพาะตัวเลขและตัวอักษร
                match = re.search(r'([A-Z0-9]+)', doc_num)
                if match:
                    doc_num = match.group(1).strip()
                    logger.info(f"✅ พบเลขที่เอกสารจาก HTML table (key: {key}): {doc_num}")
                    return doc_num
        
        # Pattern: รองรับทั้ง TAXINVOICE NO. : ST2511001810 (ไม่มีช่องว่างระหว่าง TAX และ INVOICE)
        # และ TAX INVOICE NO.: ST2511000170 (มีช่องว่างระหว่าง TAX และ INVOICE)
        # และ TAXINVOICE NO .: ST2511001810 (มีช่องว่างระหว่าง NO และ .)
        patterns = [
            # Pattern 1: TAXINVOICE NO .: ST2511001810 (มีช่องว่างระหว่าง NO และ .) - เพิ่ม pattern นี้ก่อน
            # รองรับทั้ง NO .: และ NO . : (มีช่องว่างหลัง dot)
            r'TAXINVOICE\s+NO\s+\.\s*:\s*([A-Z0-9]+)',  # TAXINVOICE NO .: ST2511001810
            r'TaxInvoice\s+No\s+\.\s*:\s*([A-Z0-9]+)',  # TaxInvoice No .: ST2511001810
            # Pattern 2: TAXINVOICE NO.: ST2511001810 (ไม่มีช่องว่างระหว่าง NO และ .)
            r'TAXINVOICE\s+NO\s*\.\s*:\s*([A-Z0-9]+)',  # TAXINVOICE NO.: ST2511001810
            r'TaxInvoice\s+No\s*\.\s*:\s*([A-Z0-9]+)',  # TaxInvoice No.: ST2511001810
            # Pattern 3: TAXINVOICE NO. : ST2511001810 (มีช่องว่างหลัง dot)
            r'TAXINVOICE\s+NO\s*\.\s+:\s*([A-Z0-9]+)',  # TAXINVOICE NO. : ST2511001810
            r'TaxInvoice\s+No\s*\.\s+:\s*([A-Z0-9]+)',  # TaxInvoice No. : ST2511001810
            # Pattern 4: TAX INVOICE NO.: ST2511000170 (มีช่องว่างระหว่าง TAX และ INVOICE)
            r'TAX\s+INVOICE\s+NO\s*\.\s*:\s*([A-Z0-9]+)',  # TAX INVOICE NO.: ST2511000170
            r'Tax\s+Invoice\s+No\s*\.\s*:\s*([A-Z0-9]+)',  # Tax Invoice No.: ST2511000170
            # Pattern 5: INVOICE NO.: ST2511000170
            r'INVOICE\s+NO\s*\.\s*:\s*([A-Z0-9]+)',  # INVOICE NO.: ST2511000170
            # Pattern 6: รองรับรูปแบบอื่นๆ (fallback)
            r'TAXINVOICE\s+NO\s*[.:]\s*[:.]?\s*([A-Z0-9]+)',  # TAXINVOICE NO. : ST2511001810 (generic)
            r'TAX\s+INVOICE\s+NO\s*[.:]\s*[:.]?\s*([A-Z0-9]+)',  # TAX INVOICE NO.: ST2511000170 (generic)
            # Pattern 7: เลขที่: ST2511000170
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: ST2511000170
        ]
        
        logger.info(f"🔍 [COSCO Document Number] กำลังทดสอบ {len(patterns)} patterns...")
        
        # อ่านทีละบรรทัดเพื่อหา TAXINVOICE NO.
        lines = text.split('\n')
        logger.info(f"🔍 [COSCO Document Number] กำลังค้นหา 'TAXINVOICE' หรือ 'TAX INVOICE' ใน {len(lines)} บรรทัด...")
        for idx, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # ตรวจสอบว่ามี "TAXINVOICE" หรือ "TAX INVOICE" ในบรรทัดนี้หรือไม่
            if 'TAXINVOICE' in line_clean.upper() or ('TAX' in line_clean.upper() and 'INVOICE' in line_clean.upper()):
                logger.info(f"🔍 [COSCO Document Number] บรรทัด {idx+1} พบ 'TAXINVOICE' หรือ 'TAX INVOICE': {line_clean[:150]}...")
        
        for idx, pattern in enumerate(patterns):
            logger.info(f"🔍 [COSCO Document Number] ทดสอบ pattern #{idx+1}: {pattern}")
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                matched_text = match.group(0)
                logger.info(f"  ✅ Pattern #{idx+1} MATCH!")
                logger.info(f"     Matched text: '{matched_text}'")
                logger.info(f"     Document number: '{doc_num}'")
                logger.info(f"✅ พบเลขที่เอกสาร (จาก pattern #{idx+1}): {doc_num}")
                return doc_num
            else:
                logger.info(f"  ❌ Pattern #{idx+1} ไม่ match")
        
        logger.warning("⚠️ ไม่พบเลขที่เอกสาร")
        return None
    
    def extract_reference(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงอ้างอิง (ชื่อไฟล์เก่า ตัด VAT_, WHT_, None_vat_ และไม่เอา EXC_ กับข้อมูลที่อยู่ด้านหลัง)"""
        if not filename:
            return None
        
        # ลบ VAT_, WHT_, None_vat_ ออกจากชื่อไฟล์
        cleaned = re.sub(r'(VAT_|WHT_|None_vat_)', '', filename, flags=re.IGNORECASE)
        
        # ตัด EXC_ และข้อมูลที่อยู่ด้านหลังออก (ไม่เอา EXC_ และข้อมูลที่อยู่ด้านหลัง)
        # เช่น EXC_2511-03 → ตัดออกทั้งหมด
        # เช่น EXC-2511-03 → ตัดออกทั้งหมด
        cleaned = re.sub(r'EXC_[^\s.]*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'EXC-[^\s.]*', '', cleaned, flags=re.IGNORECASE)
        
        # ลบ .pdf หรือ .PDF ออก
        cleaned = re.sub(r'\.pdf$', '', cleaned, flags=re.IGNORECASE)
        
        # ลบช่องว่างที่เหลือ
        cleaned = cleaned.strip()
        
        return cleaned if cleaned else None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # กำหนดชื่อบัญชีเป็น "ค่าใช้จ่ายในการขนส่ง" (ค่าคงที่)
        return {
            'account_name': 'ค่าใช้จ่ายในการขนส่ง',
            'account_code': None
        }
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """ดึงยอดเงิน"""
        # Pattern: AMOUNT | 7,000.00
        # Pattern: VAT 0% | -
        # Pattern: TOTAL AMOUNT | 7,000.00
        # VAT = 0.00 (ไม่มีภาษีมูลค่าเพิ่ม)
        
        amount_before_vat = None
        vat_amount = 0.00  # ไม่มีภาษีมูลค่าเพิ่ม
        total_amount = None
        
        # Debug: ตรวจสอบว่ามี text หรือไม่
        if not text:
            logger.warning("⚠️ ไม่มีข้อความสำหรับดึงยอดเงิน")
            return {
                'amount_before_vat': amount_before_vat,
                'vat_amount': vat_amount,
                'total_amount': total_amount
            }
        
        # Debug: ตรวจสอบว่ามี AMOUNT หรือ TOTAL AMOUNT ใน text หรือไม่
        if 'AMOUNT' not in text.upper() and 'TOTAL AMOUNT' not in text.upper():
            logger.warning("⚠️ ไม่พบคำว่า AMOUNT หรือ TOTAL AMOUNT ในข้อความ")
        else:
            logger.info(f"✅ พบคำว่า AMOUNT หรือ TOTAL AMOUNT ในข้อความ (ความยาว: {len(text)} ตัวอักษร)")
        
        # ดึงยอดก่อนภาษี: AMOUNT | 7,000.00
        # รองรับรูปแบบที่หลากหลายมากขึ้น
        # ใช้ multiline และ dotall เพื่อให้ match กับหลายบรรทัด
        amount_patterns = [
            # Pattern ที่มี pipe separator (แม่นยำที่สุด) - ต้อง match กับ "AMOUNT | 7,000.00"
            # รองรับ pipe character หลายแบบ: |, │, ｜
            r'AMOUNT\s*[|│｜]\s*([\d,]+\.\d{2})',  # AMOUNT | 7,000.00 (มีทศนิยม 2 ตำแหน่ง - แม่นยำที่สุด)
            r'AMOUNT\s*[|│｜]\s*([\d,]+\.?\d*)',  # AMOUNT | 7,000.00
            r'Amount\s*[|│｜]\s*([\d,]+\.\d{2})',  # Amount | 7,000.00 (มีทศนิยม 2 ตำแหน่ง)
            r'Amount\s*[|│｜]\s*([\d,]+\.?\d*)',  # Amount | 7,000.00
            # Pattern ที่ไม่มี pipe separator
            r'AMOUNT\s*[:.]?\s*([\d,]+\.\d{2})',  # AMOUNT: 7,000.00 (มีทศนิยม 2 ตำแหน่ง)
            r'AMOUNT\s*[:.]?\s*([\d,]+\.?\d*)',  # AMOUNT: 7,000.00
            r'Amount\s*[:.]?\s*([\d,]+\.\d{2})',  # Amount: 7,000.00 (มีทศนิยม 2 ตำแหน่ง)
            r'Amount\s*[:.]?\s*([\d,]+\.?\d*)',  # Amount: 7,000.00
            r'ยอดก่อนภาษี\s*[:.]?\s*([\d,]+\.?\d*)',  # ยอดก่อนภาษี: 7,000.00
        ]
        
        # Debug: แสดง text ที่ใช้ในการค้นหา (100 ตัวอักษรแรกและ 100 ตัวอักษรสุดท้าย)
        logger.info(f"🔍 Text ที่ใช้ในการค้นหายอดก่อนภาษี (ความยาว: {len(text)} ตัวอักษร)")
        if len(text) > 200:
            logger.info(f"🔍 100 ตัวอักษรแรก: {text[:100]}...")
            logger.info(f"🔍 100 ตัวอักษรสุดท้าย: ...{text[-100:]}")
        else:
            logger.info(f"🔍 Text ทั้งหมด: {text}")
        
        # Debug: ทดสอบ pattern โดยตรงกับ string "AMOUNT | 7,000.00"
        test_string = "AMOUNT | 7,000.00"
        logger.info(f"🔍 ทดสอบ pattern โดยตรงกับ string: '{test_string}'")
        logger.info(f"🔍 String repr: {repr(test_string)}")
        for idx, pattern in enumerate(amount_patterns[:4]):  # ทดสอบ 4 pattern แรก
            test_match = re.search(pattern, test_string, re.IGNORECASE)
            if test_match:
                matched_text = test_match.group(0)
                captured_group = test_match.group(1) if test_match.groups() else 'N/A'
                logger.info(f"  ✅ Pattern #{idx+1} MATCH กับ test string: {pattern}")
                logger.info(f"     Matched text: '{matched_text}'")
                logger.info(f"     Captured group: '{captured_group}'")
            else:
                logger.info(f"  ❌ Pattern #{idx+1} ไม่ match กับ test string: {pattern}")
        
        # Debug: หาบรรทัดที่มี "AMOUNT" และ "|" ก่อนเพื่อทดสอบ pattern
        test_lines = []
        if 'AMOUNT' in text.upper():
            lines = text.split('\n')
            logger.info(f"🔍 พบ {len(lines)} บรรทัดใน text")
            for i, line in enumerate(lines):
                if 'AMOUNT' in line.upper() and '|' in line:
                    test_lines.append((i+1, line.strip()))
                    logger.info(f"🔍 พบบรรทัดที่มี AMOUNT และ |: '{line.strip()}' (บรรทัด {i+1})")
                    logger.info(f"🔍 บรรทัด repr: {repr(line)}")
                    logger.info(f"🔍 บรรทัด strip repr: {repr(line.strip())}")
        
        # Debug: ทดสอบ pattern ทั้งหมดกับบรรทัดที่พบ
        if test_lines:
            logger.info(f"🔍 เริ่มทดสอบ pattern ทั้งหมด ({len(amount_patterns)} patterns) กับบรรทัดที่พบ...")
            for line_num, test_line in test_lines:
                logger.info(f"🔍 ทดสอบกับบรรทัด {line_num}: '{test_line}'")
                logger.info(f"🔍 Test line repr: {repr(test_line)}")
                for idx, pattern in enumerate(amount_patterns):
                    test_match = re.search(pattern, test_line, re.IGNORECASE)
                    if test_match:
                        matched_text = test_match.group(0)
                        captured_group = test_match.group(1) if test_match.groups() else 'N/A'
                        logger.info(f"  ✅ Pattern #{idx+1} MATCH: {pattern}")
                        logger.info(f"     Matched text: '{matched_text}'")
                        logger.info(f"     Captured group: '{captured_group}'")
                    else:
                        logger.info(f"  ❌ Pattern #{idx+1} ไม่ match: {pattern}")
        else:
            logger.warning("⚠️ ไม่พบบรรทัดที่มี AMOUNT และ | ใน text")
        
        # Debug: ทดสอบ pattern ทั้งหมดกับ text ทั้งหมด
        logger.info(f"🔍 เริ่มทดสอบ pattern ทั้งหมด ({len(amount_patterns)} patterns) กับ text ทั้งหมด...")
        for idx, pattern in enumerate(amount_patterns):
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                matched_text = match.group(0)
                amount_str = match.group(1).replace(',', '').strip()
                logger.info(f"  ✅ Pattern #{idx+1} MATCH: {pattern}")
                logger.info(f"     Matched text: '{matched_text}'")
                logger.info(f"     Captured amount: '{amount_str}'")
                try:
                    amount_value = float(amount_str)
                    # ตรวจสอบว่าค่าที่อ่านได้สมเหตุสมผล (มากกว่า 0)
                    if amount_value > 0:  # ต้องมากกว่า 0
                        amount_before_vat = amount_value
                        logger.info(f"✅ พบยอดก่อนภาษี: {amount_before_vat} (จาก pattern #{idx+1}: {pattern})")
                        break
                    else:
                        logger.warning(f"  ⚠️ Pattern #{idx+1} match แต่ค่าที่อ่านได้ ({amount_value}) น้อยกว่าหรือเท่ากับ 0 - ข้าม")
                except ValueError as e:
                    logger.warning(f"  ⚠️ Pattern #{idx+1} match แต่ไม่สามารถแปลง {amount_str} เป็น float: {e}")
                    continue
            else:
                logger.info(f"  ❌ Pattern #{idx+1} ไม่ match: {pattern}")
        
        if amount_before_vat is None:
            logger.warning("⚠️ ไม่พบยอดก่อนภาษีในเอกสาร")
            # Debug: แสดงส่วนของ text ที่มี "AMOUNT" อีกครั้งเพื่อตรวจสอบ
            if 'AMOUNT' in text.upper():
                logger.info("🔍 ตรวจสอบบรรทัดที่มี AMOUNT อีกครั้ง:")
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if 'AMOUNT' in line.upper():
                        logger.info(f"  บรรทัด {i+1}: '{line.strip()}'")
                        logger.info(f"    - มี '|': {'|' in line}")
                        logger.info(f"    - ความยาว: {len(line)} ตัวอักษร")
                        logger.info(f"    - รูปแบบ bytes: {repr(line)}")
                        
                        # ลองหาด้วยวิธีอื่น: หา "AMOUNT" แล้วหาตัวเลขที่อยู่ใกล้ๆ
                        amount_pos = line.upper().find('AMOUNT')
                        if amount_pos != -1:
                            # หาตัวเลขที่อยู่หลัง "AMOUNT" (ภายใน 50 ตัวอักษร)
                            search_text = line[amount_pos:amount_pos+50]
                            logger.info(f"    - ข้อความรอบๆ AMOUNT: '{search_text}'")
                            # หาตัวเลขที่มีรูปแบบ 7,000.00 หรือ 7000.00
                            numbers = re.findall(r'([\d,]+\.?\d{2})', search_text)
                            if not numbers:
                                numbers = re.findall(r'([\d,]+\.?\d*)', search_text)
                            if numbers:
                                logger.info(f"    - พบตัวเลข: {numbers}")
                                for num_str in numbers:
                                    try:
                                        amount = float(num_str.replace(',', '').replace(' ', ''))
                                        if amount > 0:
                                            amount_before_vat = amount
                                            logger.info(f"✅ พบยอดก่อนภาษี (fallback): {amount_before_vat}")
                                            break
                                    except ValueError:
                                        continue
                            if amount_before_vat:
                                break
        
        # ดึง VAT: VAT 0% | - (ไม่มีภาษีมูลค่าเพิ่ม)
        vat_patterns = [
            r'VAT\s+0%\s*\|\s*-',  # VAT 0% | -
            r'VAT\s+0%\s*[:.]?\s*([\d,]+\.?\d*)',  # VAT 0%: 0.00
            r'VAT\s*[:.]?\s*([\d,]+\.?\d*)',  # VAT: 0.00
        ]
        
        for pattern in vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # ถ้าเป็น "-" แสดงว่าไม่มี VAT
                if match.group(0).strip().endswith('-'):
                    vat_amount = 0.00
                    logger.info("✅ พบ VAT 0% (ไม่มีภาษีมูลค่าเพิ่ม)")
                    break
                # ถ้ามีตัวเลข
                elif len(match.groups()) > 0 and match.group(1):
                    amount_str = match.group(1).replace(',', '').strip()
                    try:
                        vat_amount = float(amount_str)
                        logger.info(f"✅ พบภาษีมูลค่าเพิ่ม: {vat_amount}")
                        break
                    except ValueError:
                        continue
        
        # ถ้ายังไม่พบ VAT ให้ตั้งเป็น 0.00
        if vat_amount is None:
            vat_amount = 0.00
        
        # ดึงยอดรวม: TOTAL AMOUNT | 7,000.00
        # รองรับรูปแบบที่หลากหลายมากขึ้น
        # ใช้ multiline และ dotall เพื่อให้ match กับหลายบรรทัด
        total_patterns = [
            # Pattern ที่มี pipe separator (แม่นยำที่สุด) - ต้อง match กับ "TOTAL AMOUNT | 7,000.00"
            # รองรับ pipe character หลายแบบ: |, │, ｜
            r'TOTAL\s+AMOUNT\s*[|│｜]\s*([\d,]+\.\d{2})',  # TOTAL AMOUNT | 7,000.00 (มีทศนิยม 2 ตำแหน่ง - แม่นยำที่สุด)
            r'TOTAL\s+AMOUNT\s*[|│｜]\s*([\d,]+\.?\d*)',  # TOTAL AMOUNT | 7,000.00
            r'Total\s+Amount\s*[|│｜]\s*([\d,]+\.\d{2})',  # Total Amount | 7,000.00 (มีทศนิยม 2 ตำแหน่ง)
            r'Total\s+Amount\s*[|│｜]\s*([\d,]+\.?\d*)',  # Total Amount | 7,000.00
            # Pattern ที่ไม่มี pipe separator
            r'TOTAL\s+AMOUNT\s*[:.]?\s*([\d,]+\.\d{2})',  # TOTAL AMOUNT: 7,000.00 (มีทศนิยม 2 ตำแหน่ง)
            r'TOTAL\s+AMOUNT\s*[:.]?\s*([\d,]+\.?\d*)',  # TOTAL AMOUNT: 7,000.00
            r'Total\s+Amount\s*[:.]?\s*([\d,]+\.\d{2})',  # Total Amount: 7,000.00 (มีทศนิยม 2 ตำแหน่ง)
            r'Total\s+Amount\s*[:.]?\s*([\d,]+\.?\d*)',  # Total Amount: 7,000.00
            r'ยอดรวม\s*[:.]?\s*([\d,]+\.?\d*)',  # ยอดรวม: 7,000.00
        ]
        
        # Debug: แสดง text ที่ใช้ในการค้นหา (100 ตัวอักษรแรกและ 100 ตัวอักษรสุดท้าย)
        logger.info(f"🔍 Text ที่ใช้ในการค้นหายอดรวม (ความยาว: {len(text)} ตัวอักษร)")
        if len(text) > 200:
            logger.info(f"🔍 100 ตัวอักษรแรก: {text[:100]}...")
            logger.info(f"🔍 100 ตัวอักษรสุดท้าย: ...{text[-100:]}")
        else:
            logger.info(f"🔍 Text ทั้งหมด: {text}")
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                logger.info(f"🔍 Pattern match: {pattern} -> {amount_str}")
                try:
                    total_value = float(amount_str)
                    # ตรวจสอบว่าค่าที่อ่านได้สมเหตุสมผล (มากกว่า 0)
                    if total_value > 0:
                        total_amount = total_value
                        logger.info(f"✅ พบยอดรวม: {total_amount} (จาก pattern: {pattern})")
                        break
                    else:
                        logger.warning(f"⚠️ ค่าที่อ่านได้ ({total_value}) น้อยกว่าหรือเท่ากับ 0 - ข้าม")
                except ValueError as e:
                    logger.warning(f"⚠️ ไม่สามารถแปลง {amount_str} เป็น float: {e}")
                    continue
            else:
                logger.debug(f"🔍 Pattern ไม่ match: {pattern}")
        
        # สำหรับเอกสารไม่มีภาษีมูลค่าเพิ่ม: ถ้าไม่พบยอดรวม ให้คำนวณจากยอดก่อนภาษี + ยอดภาษี
        # เพราะในเอกสารอาจจะไม่มี TOTAL AMOUNT แต่มีแค่ AMOUNT
        if total_amount is None:
            if amount_before_vat is not None:
                # คำนวณยอดรวม = ยอดก่อนภาษี + ยอดภาษี
                total_amount = amount_before_vat + vat_amount
                logger.info(f"✅ คำนวณยอดรวม: {total_amount} (จาก {amount_before_vat} + {vat_amount})")
            else:
                logger.warning("⚠️ ไม่พบยอดรวมในเอกสาร และไม่มียอดก่อนภาษี")
                # Debug: แสดงส่วนของ text ที่มี "TOTAL AMOUNT"
                if 'TOTAL AMOUNT' in text.upper():
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        if 'TOTAL AMOUNT' in line.upper() and '|' in line:
                            logger.info(f"🔍 พบบรรทัดที่มี TOTAL AMOUNT: {line.strip()} (บรรทัด {i+1})")
        else:
            # ถ้ามียอดรวมจากเอกสารแล้ว ให้ใช้ค่าที่อ่านได้
            logger.info(f"✅ ใช้ยอดรวมจากเอกสาร: {total_amount}")
        
        return {
            'amount_before_vat': amount_before_vat,
            'vat_amount': vat_amount,
            'total_amount': total_amount
        }
    
    def extract_address(self, text: str) -> str:
        """ดึงที่อยู่"""
        # กำหนดที่อยู่เป็นค่าคงที่
        return "319 Chamchuri Square Building 25th Floor, Unit 1-8 Phayathai Road, Pathumwan, Pathumwan, Bangkok 10330"
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ (ST2511000170 และชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_)"""
        remark_parts = []
        
        # ดึงเลขที่เอกสาร (TAX INVOICE NO.: ST2511000170)
        document_number = self.extract_document_number(text)
        if document_number:
            remark_parts.append(document_number)
        
        # ดึงชื่อไฟล์เก่าที่เริ่มต้นด้วย EXC_ (ถ้ามี)
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
        ดึงข้อมูลทั้งหมดจากเอกสาร COSCO Shipping Lines
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร COSCO Shipping Lines หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร COSCO SHIPPING LINES (THAILAND) CO.,LTD.'
            }
        
        # สำหรับ COSCO Shipping Lines: ไม่ใช้ extract_original_invoice_section()
        # เพราะอาจจะตัดส่วนที่มี "AMOUNT | 7,000.00" ออกไป
        # ใช้ text เดิมทั้งหมดในการดึงข้อมูล
        logger.info(f"✅ ใช้ text เดิมทั้งหมดในการดึงข้อมูล (ความยาว: {len(text)} ตัวอักษร)")
        # Debug: แสดงส่วนที่มี AMOUNT
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'AMOUNT' in line.upper() and '|' in line:
                logger.info(f"🔍 พบบรรทัดที่มี AMOUNT ใน text: {line.strip()} (บรรทัด {i+1})")
        
        # ดึงข้อมูล
        company_name = self.extract_company_name(text)
        tax_id = self.extract_tax_id(text)
        branch = self.extract_branch(text)
        date = self.extract_date(text)
        document_number = self.extract_document_number(text)
        logger.info(f"🔍 [COSCO Extract All Data] document_number ที่ดึงได้: {document_number}")
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
        # ที่อยู่: 319 Chamchuri Square Building 25th Floor, Unit 1-8 Phayathai Road, Pathumwan, Pathumwan, Bangkok 10330
        address_full = address or ''
        building_number = '319'
        other_info = 'Chamchuri Square Building 25th Floor'
        soi = ''
        road = 'Unit 1-8 Phayathai Road'
        subdistrict = 'Pathumwan'
        district = 'Pathumwan'
        province = 'Bangkok'
        postal_code = '10330'
        
        return {
            'success': True,
            'company': 'COSCO',
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
            'filepath': filepath,  # เพิ่ม filepath
            'document_type': document_type,
            'skip_amount_adjustment': True  # สำหรับเอกสารไม่มีภาษีมูลค่าเพิ่ม - ใช้ค่าที่อ่านได้เท่านั้น (ไม่ต้องคำนวณ)
        }

