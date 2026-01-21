"""
MyOrder Intelligence Invoice Extractor
======================================
Extractor สำหรับดึงข้อมูลจาก บริษัท มายออเดอร์ อินเทลลิเจนซ์ จำกัด

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any, List
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class MyOrderIntelligenceExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บริษัท มายออเดอร์ อินเทลลิเจนซ์ จำกัด"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "บริษัท มายออเดอร์ อินเทลลิเจนซ์ จำกัด",
        "มายออเดอร์ อินเทลลิเจนซ์",
        "MYORDER INTELLIGENCE",
        "MYORDER"
    ]
    
    # Tax ID
    TAX_ID = "0835563010999"
    
    # Mapping เดือนภาษาไทย
    THAI_MONTH_MAP = {
        'มกราคม': '01', 'กุมภาพันธ์': '02', 'มีนาคม': '03', 'เมษายน': '04',
        'พฤษภาคม': '05', 'มิถุนายน': '06', 'กรกฎาคม': '07', 'สิงหาคม': '08',
        'กันยายน': '09', 'ตุลาคม': '10', 'พฤศจิกายน': '11', 'ธันวาคม': '12'
    }
    
    def __init__(self):
        """Initialize MyOrder Intelligence Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ บริษัท มายออเดอร์ อินเทลลิเจนซ์ จำกัด หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "บริษัท มายออเดอร์ อินเทลลิเจนซ์ จำกัด"
        2. Tax ID "0835563010999"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร MyOrder Intelligence (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0835563010999"
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
        # อ่านจาก "บริษัท มายออเดอร์ อินเทลลิเจนซ์ จำกัด (สำนักงานใหญ่)"
        pattern = r'บริษัท\s+มายออเดอร์\s+อินเทลลิเจนซ์\s+จำกัด(?:\s*\([^)]+\))?'
        match = re.search(pattern, text)
        if match:
            return "บริษัท มายออเดอร์ อินเทลลิเจนซ์ จำกัด"
        return "บริษัท มายออเดอร์ อินเทลลิเจนซ์ จำกัด"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: เลขประจำตัวผู้เสียภาษี 0835563010999
        patterns = [
            r'เลขประจำตัวผู้เสียภาษี\s+(\d{13})',  # เลขประจำตัวผู้เสียภาษี 0835563010999
            r'เลขประจำตัวผู้เสียภาษีอากร\s+(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0835563010999
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID: 0835563010999
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0835563010999
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
        # Pattern: 30 พฤศจิกายน 2568
        # อ่านข้อมูลทีละบรรทัดจากที่ระบบอ่านได้
        patterns = [
            r'(\d{1,2})\s+(มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s+(\d{4})',  # 30 พฤศจิกายน 2568
            r'วันที่\s*[:.]?\s*(\d{1,2})\s+(มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s+(\d{4})',  # วันที่: 30 พฤศจิกายน 2568
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                day = match.group(1).zfill(2)
                month_thai = match.group(2)
                year = match.group(3)
                
                # แปลงเดือนภาษาไทยเป็นตัวเลข
                month = self.THAI_MONTH_MAP.get(month_thai, '01')
                
                # แปลงปี พ.ศ. เป็น ค.ศ. (ถ้าปีมากกว่า 2500 ให้ลบ 543)
                year_int = int(year)
                if year_int > 2500:
                    year_int = year_int - 543
                year = str(year_int)
                
                return f"{day}/{month}/{year}"
        
        return None
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # Pattern: === เลขที่ใบกำกับภาษี ===\n: MF681130073
        # อ่านข้อมูลทีละบรรทัดจากที่ระบบอ่านได้
        
        # ลองหาบรรทัดที่มี "เลขที่ใบกำกับภาษี" ก่อน
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'เลขที่ใบกำกับภาษี' in line:
                logger.info(f"🔍 Found 'เลขที่ใบกำกับภาษี' at line {i}: '{line[:100]}...'")
                # ตรวจสอบบรรทัดถัดไป (อาจจะมีหลายบรรทัดว่าง)
                for j in range(i + 1, min(i + 5, len(lines))):  # ตรวจสอบสูงสุด 5 บรรทัดถัดไป
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    logger.info(f"🔍 Next line {j}: '{next_line[:100]}...'")
                    # Pattern: : MF681130073 หรือ MF681130073
                    match = re.search(r':\s*([A-Z0-9]+)', next_line)
                    if not match:
                        # ลองหาโดยตรง (ไม่มี :)
                        match = re.search(r'([A-Z]\d{9,})', next_line)  # Pattern: M + ตัวเลข 9 ตัวขึ้นไป
                    if match:
                        doc_num = match.group(1).strip()
                        logger.info(f"✅ พบเลขที่เอกสาร: {doc_num}")
                        return doc_num
                
                # ถ้าไม่พบในบรรทัดถัดไป ลองหาในบรรทัดเดียวกัน
                match = re.search(r'เลขที่ใบกำกับภาษี[^:]*:\s*([A-Z0-9]+)', line, re.IGNORECASE)
                if match:
                    doc_num = match.group(1).strip()
                    logger.info(f"✅ พบเลขที่เอกสารในบรรทัดเดียวกัน: {doc_num}")
                    return doc_num
        
        # Fallback: ใช้ pattern เดิม
        patterns = [
            r'===\s*เลขที่ใบกำกับภาษี\s*===\s*\n\s*:\s*([A-Z0-9]+)',  # === เลขที่ใบกำกับภาษี ===\n: MF681130073
            r'เลขที่ใบกำกับภาษี\s*===\s*\n\s*:\s*([A-Z0-9]+)',  # เลขที่ใบกำกับภาษี ===\n: MF681130073
            r'เลขที่ใบกำกับภาษี\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่ใบกำกับภาษี: MF681130073
            r'เลขที่\s*[:.]?\s*([A-Z0-9]+)',  # เลขที่: MF681130073
            r'Document\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # Document No.: MF681130073
            r'Invoice\s+No[.:]?\s*[:.]?\s*([A-Z0-9]+)',  # Invoice No.: MF681130073
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                doc_num = match.group(1).strip()
                logger.info(f"✅ พบเลขที่เอกสาร: {doc_num} (จาก pattern: {pattern})")
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
    
    def parse_table_data(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse ข้อมูลจากตาราง HTML
        รองรับทั้ง HTML format (<td>...</td>) และ text format (| separated)
        
        Returns:
            List of dictionaries containing table row data
        """
        rows = []
        
        # หาส่วนตาราง (รองรับทั้ง HTML และ text format)
        table_start_patterns = [
            r'<tr>.*?ลำดับ.*?รายการ',  # HTML format
            r'ลำดับ\s*</td><td>\s*รายการ',  # HTML format (no <tr>)
            r'ลำดับ\s*\|\s*รายการ',  # Text format
            r'ลำดับ.*?รายการ',  # Flexible
        ]
        
        table_start = -1
        for pattern in table_start_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                table_start = match.start()
                logger.info(f"✅ Found table start at position {table_start}")
                break
        
        if table_start == -1:
            logger.warning("⚠️ ไม่พบส่วนตารางในเอกสาร")
            return rows
        
        # หาส่วนตาราง (ประมาณ 2000 ตัวอักษรหลัง header)
        table_section = text[table_start:table_start+2000]
        
        logger.info(f"🔍 Table section (first 300 chars): {table_section[:300]}")
        
        # ตรวจสอบว่าเป็น HTML format หรือไม่
        is_html = '<td>' in table_section or '</td>' in table_section
        
        if is_html:
            # Parse HTML format: <tr><td>1</td><td>ค่าขนส่งภายในประเทศ</td><td>18</td><td>575.00</td><td>0</td><td>575.00</td></tr>
            logger.info("🔍 Detected HTML format, parsing HTML table...")
            
            # หาแถวข้อมูลทั้งหมด (ข้าม header)
            # Pattern: <tr><td>ลำดับ</td><td>รายการ</td>... (header)
            # แล้วตามด้วย <tr><td>1</td><td>...</td>... (data rows)
            
            # หา data rows โดยใช้ pattern: <tr><td>ตัวเลข</td>...
            # รองรับ whitespace และ <br/> tags
            row_pattern = r'<tr>\s*<td>(\d+)</td>\s*<td>([^<]+(?:<[^>]+>)*[^<]*)</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*</tr>'
            matches = re.findall(row_pattern, table_section, re.IGNORECASE | re.DOTALL)
            
            logger.info(f"🔍 Found {len(matches)} HTML table rows")
            
            # ถ้าไม่พบด้วย pattern นี้ ลอง pattern ที่ยืดหยุ่นกว่า
            if len(matches) == 0:
                # Pattern ที่ยืดหยุ่นกว่า: หา <td> ที่มีตัวเลข แล้วตามด้วย <td> อีก 5 ตัว
                row_pattern = r'<td>(\d+)</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>'
                matches = re.findall(row_pattern, table_section, re.IGNORECASE)
                logger.info(f"🔍 Found {len(matches)} HTML table rows (flexible pattern)")
            
            for match in matches:
                try:
                    # ทำความสะอาดข้อมูล (ลบ HTML tags และ whitespace)
                    clean_value = lambda x: re.sub(r'<[^>]+>', '', x).strip()
                    
                    row_data = {
                        'ลำดับ': match[0].strip(),
                        'รายการ': clean_value(match[1]),
                        'จำนวนชิ้น': clean_value(match[2]),
                        'ค่าบริการ(ไม่รวมภาษีมูลค่าเพิ่ม)': clean_value(match[3]),
                        'ภาษีมูลค่าเพิ่ม': clean_value(match[4]),
                        'จำนวนเงิน': clean_value(match[5])
                    }
                    rows.append(row_data)
                    logger.info(f"✅ Parse HTML row {len(rows)}: {row_data}")
                except Exception as e:
                    logger.warning(f"⚠️ ไม่สามารถ parse HTML row: {match}, Error: {e}")
                    continue
        else:
            # Parse text format: 1 | ค่าขนส่งภายในประเทศ | 18 | 575.00 | 0 | 575.00
            logger.info("🔍 Detected text format, parsing text table...")
            
            # แยกบรรทัด
            lines = table_section.split('\n')
            
            logger.info(f"🔍 Found {len(lines)} lines in table section")
            
            # หา header row
            header_line = None
            for i, line in enumerate(lines):
                if 'ลำดับ' in line and 'รายการ' in line:
                    header_line = i
                    logger.info(f"✅ Found header at line {i}: '{line[:100]}...'")
                    break
            
            if header_line is None:
                logger.warning("⚠️ ไม่พบ header row ในตาราง")
                return rows
            
            # Parse data rows (เริ่มจากบรรทัดถัดจาก header)
            for i in range(header_line + 1, min(header_line + 10, len(lines))):  # ตรวจสอบสูงสุด 10 บรรทัด
                line = lines[i].strip()
                if not line or line.startswith('===') or ('รวม' in line and i > header_line + 3) or 'หมายเหตุ' in line:
                    logger.debug(f"🔍 Skipping line {i}: '{line[:50]}...'")
                    continue
                
                # Parse row: 1 | ค่าขนส่งภายในประเทศ | 18 | 575.00 | 0 | 575.00
                parts = [p.strip() for p in line.split('|')]
                
                logger.info(f"🔍 Parsing line {i}: '{line[:100]}...' -> {len(parts)} parts")
                
                if len(parts) >= 6:
                    try:
                        row_data = {
                            'ลำดับ': parts[0],
                            'รายการ': parts[1],
                            'จำนวนชิ้น': parts[2],
                            'ค่าบริการ(ไม่รวมภาษีมูลค่าเพิ่ม)': parts[3],
                            'ภาษีมูลค่าเพิ่ม': parts[4],
                            'จำนวนเงิน': parts[5]
                        }
                        rows.append(row_data)
                        logger.info(f"✅ Parse text row {len(rows)}: {row_data}")
                    except Exception as e:
                        logger.warning(f"⚠️ ไม่สามารถ parse row: {line[:100]}, Error: {e}")
                        continue
        
        return rows
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        มี 2 บรรทัด:
        - บรรทัดที่ 1: ยอดก่อนภาษี = 430.50, ภาษี = 30.14, รวม = 460.64 (หัก ณ ที่จ่าย 3%)
        - บรรทัดที่ 2: ยอดก่อนภาษี = 575.00, ภาษี = 0.00, รวม = 575.00 (หัก ณ ที่จ่าย 1%)
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (บรรทัดที่ 1)
                'amount_before_vat_2': float, # ยอดก่อนภาษี (บรรทัดที่ 2)
                'vat_amount': float,          # ยอดภาษี (บรรทัดที่ 1)
                'vat_amount_2': float,         # ยอดภาษี (บรรทัดที่ 2)
                'total_amount': float         # ยอดรวม (รวมทั้ง 2 บรรทัด)
            }
        """
        result = {
            'amount_before_vat': None,
            'amount_before_vat_2': None,
            'vat_amount': None,
            'vat_amount_2': None,
            'total_amount': None
        }
        
        # Parse ข้อมูลจากตาราง
        table_rows = self.parse_table_data(text)
        
        logger.info(f"🔍 Found {len(table_rows)} table rows")
        for idx, row in enumerate(table_rows):
            logger.info(f"  Row {idx+1}: {row}")
        
        # ถ้าไม่พบข้อมูลจากตาราง ให้ลองหาด้วยวิธีอื่น
        if len(table_rows) < 2:
            logger.warning("⚠️ ไม่พบข้อมูลตารางครบถ้วน ลองหาด้วยวิธีอื่น...")
            # ลองหาจาก "มูลค่าบริการ-ยกเว้นภาษีมูลค่าเพิ่ม | 575.00"
            # และ "มูลค่าบริการ-ที่ต้องชำระภาษีมูลค่าเพิ่ม | 430.50"
            exempt_pattern = r'มูลค่าบริการ-ยกเว้นภาษีมูลค่าเพิ่ม\s*[|│]\s*([\d,]+\.?\d*)'
            taxable_pattern = r'มูลค่าบริการ-ที่ต้องชำระภาษีมูลค่าเพิ่ม\s*[|│]\s*([\d,]+\.?\d*)'
            
            exempt_match = re.search(exempt_pattern, text, re.IGNORECASE)
            taxable_match = re.search(taxable_pattern, text, re.IGNORECASE)
            
            if exempt_match and taxable_match:
                line2_before_vat = float(exempt_match.group(1).replace(',', ''))
                line1_before_vat = float(taxable_match.group(1).replace(',', ''))
                
                # หาภาษีจาก "จำนวนภาษีมูลค่าเพิ่ม 7% : 30.14"
                vat_pattern = r'จำนวนภาษีมูลค่าเพิ่ม\s+7%\s*[:.]?\s*([\d,]+\.?\d*)'
                vat_match = re.search(vat_pattern, text, re.IGNORECASE)
                line1_vat = float(vat_match.group(1).replace(',', '')) if vat_match else 0.0
                line2_vat = 0.0
                
                result['amount_before_vat'] = line1_before_vat
                result['amount_before_vat_2'] = line2_before_vat
                result['vat_amount'] = line1_vat
                result['vat_amount_2'] = line2_vat
                result['total_amount'] = line1_before_vat + line1_vat + line2_before_vat + line2_vat
                
                logger.info(f"✅ พบข้อมูลจาก fallback method:")
                logger.info(f"  บรรทัดที่ 1: ก่อนภาษี={line1_before_vat}, ภาษี={line1_vat}, รวม={line1_before_vat + line1_vat}")
                logger.info(f"  บรรทัดที่ 2: ก่อนภาษี={line2_before_vat}, ภาษี={line2_vat}, รวม={line2_before_vat + line2_vat}")
                return result
        
        if len(table_rows) >= 2:
            # หาบรรทัดที่ 1: ค่าบริการเรียกเก็บเงินปลายทาง (430.50, 30.14, 460.64) - หัก ณ ที่จ่าย 3%
            # หาบรรทัดที่ 2: ค่าขนส่งภายในประเทศ (575.00, 0, 575.00) - หัก ณ ที่จ่าย 1%
            row1 = None
            row2 = None
            
            for row in table_rows:
                row_item = row.get('รายการ', '')
                logger.info(f"🔍 Checking row item: '{row_item}'")
                if 'เรียกเก็บเงินปลายทาง' in row_item or 'เรียกเก็บ' in row_item:
                    row1 = row
                    logger.info(f"✅ Found row1: {row_item}")
                elif 'ขนส่งภายในประเทศ' in row_item or ('ขนส่ง' in row_item and 'ภายใน' in row_item):
                    row2 = row
                    logger.info(f"✅ Found row2: {row_item}")
            
            # ถ้าไม่พบ ให้ใช้ลำดับตามตาราง
            # บรรทัดที่ 2 ในตาราง (index 1) = บรรทัดที่ 1 ที่ต้องการ (ค่าบริการเรียกเก็บเงินปลายทาง)
            # บรรทัดที่ 1 ในตาราง (index 0) = บรรทัดที่ 2 ที่ต้องการ (ค่าขนส่งภายในประเทศ)
            if row1 is None:
                if len(table_rows) > 1:
                    row1 = table_rows[1]  # บรรทัดที่ 2 ในตาราง
                    logger.info(f"⚠️ Using table row 2 as row1: {row1.get('รายการ', '')}")
                elif len(table_rows) > 0:
                    row1 = table_rows[0]
            if row2 is None:
                if len(table_rows) > 0:
                    row2 = table_rows[0]  # บรรทัดที่ 1 ในตาราง
                    logger.info(f"⚠️ Using table row 1 as row2: {row2.get('รายการ', '')}")
            
            # บรรทัดที่ 1: ค่าบริการเรียกเก็บเงินปลายทาง (430.50, 30.14, 460.64)
            if row1:
                try:
                    amount_before_vat_1 = float(row1.get('ค่าบริการ(ไม่รวมภาษีมูลค่าเพิ่ม)', '0').replace(',', ''))
                    vat_1 = float(row1.get('ภาษีมูลค่าเพิ่ม', '0').replace(',', ''))
                    total_1 = float(row1.get('จำนวนเงิน', '0').replace(',', ''))
                    
                    result['amount_before_vat'] = amount_before_vat_1
                    result['vat_amount'] = vat_1
                    logger.info(f"✅ บรรทัดที่ 1: ยอดก่อนภาษี = {amount_before_vat_1}, ภาษี = {vat_1}, รวม = {total_1}")
                except (ValueError, KeyError) as e:
                    logger.warning(f"⚠️ ไม่สามารถ parse บรรทัดที่ 1: {e}")
            
            # บรรทัดที่ 2: ค่าขนส่งภายในประเทศ (575.00, 0, 575.00)
            if row2:
                try:
                    amount_before_vat_2 = float(row2.get('ค่าบริการ(ไม่รวมภาษีมูลค่าเพิ่ม)', '0').replace(',', ''))
                    vat_2 = float(row2.get('ภาษีมูลค่าเพิ่ม', '0').replace(',', ''))
                    total_2 = float(row2.get('จำนวนเงิน', '0').replace(',', ''))
                    
                    result['amount_before_vat_2'] = amount_before_vat_2
                    result['vat_amount_2'] = vat_2
                    logger.info(f"✅ บรรทัดที่ 2: ยอดก่อนภาษี = {amount_before_vat_2}, ภาษี = {vat_2}, รวม = {total_2}")
                except (ValueError, KeyError) as e:
                    logger.warning(f"⚠️ ไม่สามารถ parse บรรทัดที่ 2: {e}")
            
            # คำนวณยอดรวม
            total_1 = (result.get('amount_before_vat') or 0) + (result.get('vat_amount') or 0)
            total_2 = (result.get('amount_before_vat_2') or 0) + (result.get('vat_amount_2') or 0)
            result['total_amount'] = total_1 + total_2
            logger.info(f"✅ ยอดรวม: {result['total_amount']:.2f} (บรรทัด 1: {total_1:.2f} + บรรทัด 2: {total_2:.2f})")
        else:
            logger.warning(f"⚠️ ไม่พบข้อมูลตารางครบถ้วน (พบ {len(table_rows)} บรรทัด)")
        
        return result
    
    def extract_withholding_tax(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลหัก ณ ที่จ่าย
        - บรรทัดที่ 1: 3%
        - บรรทัดที่ 2: 1%
        """
        return {
            'withholding_tax_percent': 3.0,  # บรรทัดที่ 1
            'withholding_tax_percent_2': 1.0,  # บรรทัดที่ 2
            'withholding_tax_amount': None,
            'withholding_tax_amount_2': None
        }
    
    def extract_address(self, text: str) -> str:
        """ดึงที่อยู่"""
        # กำหนดที่อยู่เป็นค่าคงที่
        return "69/429 หมู่ที่ 2 ตำบลวิชิต อำเภอเมืองภูเก็ต จังหวัดภูเก็ต รหัสไปรษณีย์ 83000"
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ"""
        # อ่านข้อมูลจาก:
        # === วันที่ ===
        # : 04/12/2568
        # === ชำระโดย ===
        # : WALLET
        # === จำนวนเงินที่ชำระ ===
        # : 1,035.64 บาท
        # 
        # ผลลัพธ์ที่ต้องการ: "04/12/2568 ชำระโดย : WALLET จำนวนเงินที่ชำระ : 1,035.64 บาท"
        
        # อ่านข้อมูลทีละบรรทัด
        lines = text.split('\n')
        
        payment_date = None
        payment_method = None
        payment_amount = None
        
        # หาวันที่ชำระ (ลำดับที่ 2 ตามภาพ)
        # ต้องหาเฉพาะวันที่ที่อยู่หลัง "=== ชำระโดย ===" (ไม่ใช่วันที่ของเอกสาร)
        # หา "=== ชำระโดย ===" ก่อน แล้วหาวันที่ถัดไป
        found_payment_section = False
        for i, line in enumerate(lines):
            if '=== ชำระโดย ===' in line:
                found_payment_section = True
                logger.info(f"🔍 Found '=== ชำระโดย ===' at line {i}: '{line[:100]}...'")
                # หาวันที่ในบรรทัดถัดไป (หลังจากชำระโดย)
                for j in range(i + 1, min(i + 10, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    logger.info(f"🔍 Checking line {j} for date: '{next_line[:100]}...'")
                    # Pattern: === วันที่ === หรือ **วันที่**: 04/12/2568
                    if '=== วันที่ ===' in next_line:
                        # ตรวจสอบบรรทัดถัดไป
                        for k in range(j + 1, min(j + 5, len(lines))):
                            date_line = lines[k].strip()
                            if not date_line:
                                continue
                            match = re.search(r':\s*(\d{2}/\d{2}/\d{4})', date_line)
                            if match:
                                payment_date = match.group(1).strip()
                                logger.info(f"✅ พบวันที่ชำระ: {payment_date}")
                                break
                    elif 'วันที่' in next_line:
                        # ตรวจสอบว่าข้อมูลอยู่ในบรรทัดเดียวกัน (เช่น "**วันที่**: 04/12/2568")
                        # Pattern 1: **วันที่**: 04/12/2568 (มี ** หน้าและหลัง)
                        match = re.search(r'\*\*วันที่\*\s*:\s*(\d{2}/\d{2}/\d{4})', next_line, re.IGNORECASE)
                        if not match:
                            # Pattern 2: วันที่**: 04/12/2568 (มี * หลัง)
                            match = re.search(r'วันที่\*+\s*:\s*(\d{2}/\d{2}/\d{4})', next_line, re.IGNORECASE)
                        if not match:
                            # Pattern 3: วันที่: 04/12/2568 (ไม่มี *)
                            match = re.search(r'วันที่\s*[:.]?\s*(\d{2}/\d{2}/\d{4})', next_line, re.IGNORECASE)
                        if match:
                            payment_date = match.group(1).strip()
                            logger.info(f"✅ พบวันที่ชำระในบรรทัดเดียวกัน: {payment_date} (from pattern: {match.group(0)})")
                            break
                    if payment_date:
                        break
                if payment_date:
                    break
        
        # ถ้ายังไม่พบ ให้ลองหาแบบเดิม
        if not payment_date:
            for i, line in enumerate(lines):
                if '=== วันที่ ===' in line or 'วันที่' in line:
                    # ข้ามถ้าเป็นวันที่ของเอกสาร (ต้องเป็นวันที่ชำระ)
                    if '=== วันที่ ===' in line and i < 20:  # วันที่ของเอกสารมักจะอยู่ก่อนบรรทัด 20
                        continue
                    logger.info(f"🔍 Found 'วันที่' at line {i}: '{line[:100]}...'")
                    # ตรวจสอบว่าข้อมูลอยู่ในบรรทัดเดียวกันก่อน (เช่น "**วันที่**: 04/12/2568")
                    # Pattern 1: **วันที่**: 04/12/2568 (มี ** หน้าและหลัง)
                    match = re.search(r'\*\*วันที่\*\s*:\s*(\d{2}/\d{2}/\d{4})', line, re.IGNORECASE)
                    if not match:
                        # Pattern 2: วันที่**: 04/12/2568 (มี * หลัง)
                        match = re.search(r'วันที่\*+\s*:\s*(\d{2}/\d{2}/\d{4})', line, re.IGNORECASE)
                    if not match:
                        # Pattern 3: วันที่: 04/12/2568 (ไม่มี *)
                        match = re.search(r'วันที่\s*[:.]?\s*(\d{2}/\d{2}/\d{4})', line, re.IGNORECASE)
                    if match:
                        payment_date = match.group(1).strip()
                        logger.info(f"✅ พบวันที่ชำระในบรรทัดเดียวกัน: {payment_date} (from pattern: {match.group(0)})")
                        break
                    
                    # ถ้าไม่พบในบรรทัดเดียวกัน ตรวจสอบบรรทัดถัดไป
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        if not next_line:
                            continue
                        logger.info(f"🔍 Next line {j}: '{next_line[:100]}...'")
                        # Pattern: : 04/12/2568 หรือ 04/12/2568
                        match = re.search(r':\s*(\d{2}/\d{2}/\d{4})', next_line)
                        if not match:
                            # ลองหาโดยตรง (ไม่มี :)
                            match = re.search(r'(\d{2}/\d{2}/\d{4})', next_line)
                        if match:
                            payment_date = match.group(1).strip()
                            logger.info(f"✅ พบวันที่ชำระ: {payment_date}")
                            break
                    if payment_date:
                        break
        
        # หาวิธีชำระ (ลำดับที่ 1 ตามภาพ)
        for i, line in enumerate(lines):
            if '=== ชำระโดย ===' in line or 'ชำระโดย' in line:
                logger.info(f"🔍 Found 'ชำระโดย' at line {i}: '{line[:100]}...'")
                # ตรวจสอบว่าข้อมูลอยู่ในบรรทัดเดียวกันก่อน (เช่น "**ชำระโดย**: WALLET")
                # Pattern: **ชำระโดย**: WALLET หรือ ชำระโดย**: WALLET หรือ ชำระโดย: WALLET
                # รองรับทั้ง ** และไม่มี **
                # ใช้ pattern ที่ยืดหยุ่น: หา "ชำระโดย" แล้วหา ":" แล้วหาตัวอักษร
                # Pattern 1: **ชำระโดย**: WALLET (มี ** หน้าและหลัง)
                match = re.search(r'\*\*ชำระโดย\*\s*:\s*([A-Za-z]+)', line, re.IGNORECASE)
                if not match:
                    # Pattern 2: ชำระโดย**: WALLET (มี * หลัง)
                    match = re.search(r'ชำระโดย\*+\s*:\s*([A-Za-z]+)', line, re.IGNORECASE)
                if not match:
                    # Pattern 3: ชำระโดย: WALLET (ไม่มี *)
                    match = re.search(r'ชำระโดย\s*[:.]?\s*([A-Za-z]+)', line, re.IGNORECASE)
                if match:
                    payment_method = match.group(1).strip()
                    logger.info(f"✅ พบวิธีชำระในบรรทัดเดียวกัน: {payment_method} (from pattern: {match.group(0)})")
                    break
                
                # ถ้าไม่พบในบรรทัดเดียวกัน ตรวจสอบบรรทัดถัดไป
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    logger.info(f"🔍 Next line {j}: '{next_line[:100]}...'")
                    # Pattern: : WALLET (ต้องเป็นตัวอักษรเท่านั้น ไม่ใช่ตัวเลข)
                    match = re.search(r':\s*([A-Za-z]+)', next_line)
                    if match:
                        payment_method = match.group(1).strip()
                        logger.info(f"✅ พบวิธีชำระ: {payment_method}")
                        break
                if payment_method:
                    break
        
        # หาจำนวนเงินที่ชำระ (ลำดับที่ 3 ตามภาพ)
        for i, line in enumerate(lines):
            if '=== จำนวนเงินที่ชำระ ===' in line or 'จำนวนเงินที่ชำระ' in line:
                logger.info(f"🔍 Found 'จำนวนเงินที่ชำระ' at line {i}: '{line[:100]}...'")
                # ตรวจสอบว่าข้อมูลอยู่ในบรรทัดเดียวกันก่อน (เช่น "**จำนวนเงินที่ชำระ**: 1,035.64 บาท")
                # รองรับทั้ง ** และไม่มี **
                # Pattern 1: **จำนวนเงินที่ชำระ**: 1,035.64 บาท (มี ** หน้าและหลัง)
                match = re.search(r'\*\*จำนวนเงินที่ชำระ\*\s*:\s*([\d,]+\.?\d*)\s*บาท', line, re.IGNORECASE)
                if not match:
                    # Pattern 2: จำนวนเงินที่ชำระ**: 1,035.64 บาท (มี * หลัง)
                    match = re.search(r'จำนวนเงินที่ชำระ\*+\s*:\s*([\d,]+\.?\d*)\s*บาท', line, re.IGNORECASE)
                if not match:
                    # Pattern 3: จำนวนเงินที่ชำระ: 1,035.64 บาท (ไม่มี *)
                    match = re.search(r'จำนวนเงินที่ชำระ\s*[:.]?\s*([\d,]+\.?\d*)\s*บาท', line, re.IGNORECASE)
                if match:
                    payment_amount = match.group(1).strip()
                    logger.info(f"✅ พบจำนวนเงินที่ชำระในบรรทัดเดียวกัน: {payment_amount} (from pattern: {match.group(0)})")
                    break
                
                # ถ้าไม่พบในบรรทัดเดียวกัน ตรวจสอบบรรทัดถัดไป
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    logger.info(f"🔍 Next line {j}: '{next_line[:100]}...'")
                    # Pattern: : 1,035.64 บาท หรือ 1,035.64 บาท
                    match = re.search(r':\s*([\d,]+\.?\d*)\s*บาท', next_line)
                    if not match:
                        # ลองหาโดยตรง (ไม่มี :)
                        match = re.search(r'([\d,]+\.?\d*)\s*บาท', next_line)
                    if match:
                        payment_amount = match.group(1).strip()
                        logger.info(f"✅ พบจำนวนเงินที่ชำระ: {payment_amount}")
                        break
                if payment_amount:
                    break
        
        # ถ้ายังไม่พบข้อมูล ให้ลองหาแบบอื่น (fallback)
        if not payment_date:
            # ลองหาแบบ: วันที่ : 04/12/2568 (ในบรรทัดเดียวกัน)
            # แต่ต้องหาเฉพาะวันที่ที่อยู่หลัง "ชำระโดย" (ไม่ใช่วันที่ของเอกสาร)
            # หา "ชำระโดย" ก่อน แล้วหาวันที่ถัดไป
            payment_section_start = text.find('ชำระโดย')
            if payment_section_start != -1:
                # หาเฉพาะในส่วนหลัง "ชำระโดย"
                payment_section = text[payment_section_start:]
                date_pattern = r'วันที่\s*[:.]?\s*(\d{2}/\d{2}/\d{4})'
                match = re.search(date_pattern, payment_section, re.IGNORECASE)
                if match:
                    payment_date = match.group(1).strip()
                    logger.info(f"✅ พบวันที่ชำระ (fallback): {payment_date}")
        
        if not payment_method:
            # ลองหาแบบ: ชำระโดย : WALLET (ในบรรทัดเดียวกัน)
            method_pattern = r'ชำระโดย\s*[:.]?\s*([A-Za-z]+)'
            match = re.search(method_pattern, text, re.IGNORECASE)
            if match:
                payment_method = match.group(1).strip()
                logger.info(f"✅ พบวิธีชำระ (fallback): {payment_method}")
        
        if not payment_amount:
            # ลองหาแบบ: จำนวนเงินที่ชำระ : 1,035.64 บาท (ในบรรทัดเดียวกัน)
            amount_pattern = r'จำนวนเงินที่ชำระ\s*[:.]?\s*([\d,]+\.?\d*)\s*บาท'
            match = re.search(amount_pattern, text, re.IGNORECASE)
            if match:
                payment_amount = match.group(1).strip()
                logger.info(f"✅ พบจำนวนเงินที่ชำระ (fallback): {payment_amount}")
        
        # แปลงปี พ.ศ. เป็น ค.ศ. สำหรับวันที่ชำระ (ถ้ามี)
        if payment_date:
            # Pattern: 04/12/2568 -> 04/12/2025
            date_parts = payment_date.split('/')
            if len(date_parts) == 3:
                day = date_parts[0]
                month = date_parts[1]
                year = date_parts[2]
                
                # แปลงปี พ.ศ. เป็น ค.ศ. (ถ้าปีมากกว่า 2500 ให้ลบ 543)
                try:
                    year_int = int(year)
                    if year_int > 2500:
                        year_int = year_int - 543
                        year = str(year_int)
                        payment_date = f"{day}/{month}/{year}"
                        logger.info(f"✅ แปลงปี พ.ศ. {date_parts[2]} เป็น ค.ศ. {year}")
                except ValueError:
                    logger.warning(f"⚠️ ไม่สามารถแปลงปี: {year}")
        
        # สร้างหมายเหตุตามรูปแบบที่ต้องการ: "04/12/2025 ชำระโดย : WALLET จำนวนเงินที่ชำระ : 1,035.64 บาท"
        if payment_date or payment_method or payment_amount:
            remark_parts = []
            
            if payment_date:
                remark_parts.append(payment_date)
            if payment_method:
                remark_parts.append(f"ชำระโดย : {payment_method}")
            if payment_amount:
                remark_parts.append(f"จำนวนเงินที่ชำระ : {payment_amount} บาท")
            
            remark = " ".join(remark_parts)
            logger.info(f"✅ สร้างหมายเหตุ: {remark}")
            return remark
        
        # ถ้าไม่พบข้อมูล ให้คืนค่า None
        logger.warning("⚠️ ไม่พบข้อมูลสำหรับหมายเหตุ")
        return None
    
    def clean_filename(self, filename: str) -> str:
        """ทำความสะอาดชื่อไฟล์"""
        if not filename:
            return "ค่าบริการขนส่ง_Myorder"
        
        # กำหนดชื่อไฟล์ใหม่เป็น "ค่าบริการขนส่ง_Myorder"
        return "ค่าบริการขนส่ง_Myorder"
    
    def detect_document_type(self, text: str, amounts: Dict[str, Optional[float]], withholding: Dict[str, Optional[float]]) -> int:
        """ตรวจสอบประเภทเอกสาร"""
        # มีภาษีมูลค่าเพิ่ม (บรรทัดที่ 1 มีภาษี 30.14)
        # แต่จะบันทึกใน sheet มีภาษีมูลค่าเพิ่ม (document_type = 1) เหมือนกับ Customs Department
        return 1  # มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str = None, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร MyOrder Intelligence
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร MyOrder Intelligence หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร บริษัท มายออเดอร์ อินเทลลิเจนซ์ จำกัด'
            }
        
        # ใช้ text เดิมทั้งหมดในการดึงข้อมูล
        logger.info(f"✅ ใช้ text เดิมทั้งหมดในการดึงข้อมูล (ความยาว: {len(text)} ตัวอักษร)")
        
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
        # ที่อยู่: 69/429 หมู่ที่ 2 ตำบลวิชิต อำเภอเมืองภูเก็ต จังหวัดภูเก็ต รหัสไปรษณีย์ 83000
        address_full = address or ''
        building_number = '69/429'
        other_info = 'หมู่ที่ 2'
        soi = ''
        road = ''
        subdistrict = 'วิชิต'
        district = 'เมืองภูเก็ต'
        province = 'ภูเก็ต'
        postal_code = '83000'
        
        # คำนวณยอดรวม
        line1_before_vat = amounts.get('amount_before_vat') or 0
        line1_vat = amounts.get('vat_amount') or 0
        line2_before_vat = amounts.get('amount_before_vat_2') or 0
        line2_vat = amounts.get('vat_amount_2') or 0
        
        total_before_vat = line1_before_vat + line2_before_vat
        total_vat = line1_vat + line2_vat
        total_amount = amounts.get('total_amount') or (total_before_vat + total_vat)
        
        return {
            'success': True,
            'company': 'MYORDER_INTELLIGENCE',
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
            'amount_before_vat': total_before_vat,  # รวมทั้ง 2 บรรทัด
            'vat_amount': total_vat,  # รวมทั้ง 2 บรรทัด
            'total_amount': total_amount,
            'withholding_tax_percent': withholding.get('withholding_tax_percent'),
            'withholding_tax_amount': withholding.get('withholding_tax_amount'),
            'remark': remark,
            'new_filename': new_filename,
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,
            # ข้อมูลเพิ่มเติมสำหรับกรณีมี 2 บรรทัด
            'amount_before_vat_line1': line1_before_vat,  # บรรทัดที่ 1
            'amount_before_vat_line2': line2_before_vat,  # บรรทัดที่ 2
            'vat_amount_line1': line1_vat,  # ภาษีบรรทัดที่ 1
            'vat_amount_line2': line2_vat,  # ภาษีบรรทัดที่ 2
            'withholding_tax_percent_line1': 3.0,  # บรรทัดที่ 1: 3%
            'withholding_tax_percent_line2': 1.0,  # บรรทัดที่ 2: 1%
            'skip_amount_adjustment': True  # สำหรับเอกสารไม่มีภาษีมูลค่าเพิ่ม - ใช้ค่าที่อ่านได้เท่านั้น (ไม่ต้องคำนวณ)
        }

