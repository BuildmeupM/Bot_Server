"""
MST (Mediterranean Shipping Thailand) Invoice Extractor
========================================================
Extractor สำหรับดึงข้อมูลจาก Mediterranean Shipping (Thailand) Co., Ltd.

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class MSTInvoiceExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก Mediterranean Shipping (Thailand) Co., Ltd."""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "Mediterranean Shipping (Thailand)",
        "Mediterranean Shipping Co., Ltd."
    ]
    
    def __init__(self):
        """Initialize MST Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ MST หรือไม่
        ต้องมีทั้ง 2 เงื่อนไข:
        1. ชื่อบริษัท "Mediterranean Shipping (Thailand) Co., Ltd."
        2. Tax ID "0105544019079"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร MST (มีทั้ง 2 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมี "Mediterranean Shipping (Thailand) Co., Ltd."
        has_company = "Mediterranean Shipping (Thailand) Co., Ltd." in text
        
        # เงื่อนไข 2: ต้องมี Tax ID "0105544019079"
        has_tax_id = "0105544019079" in text
        
        # ต้องมีทั้ง 2 เงื่อนไขถึงจะผ่าน
        return has_company and has_tax_id
    
    def extract_company_name(self, text: str) -> str:
        """ดึงชื่อบริษัท MST"""
        # หาบรรทัดที่มี Mediterranean Shipping (Thailand)
        lines = text.split('\n')
        for line in lines:
            if 'Mediterranean Shipping (Thailand)' in line:
                # Clean up
                company_name = line.strip()
                # ถ้าไม่มี Co., Ltd. ให้เพิ่ม
                if 'Co., Ltd.' not in company_name:
                    company_name = 'Mediterranean Shipping (Thailand) Co., Ltd.'
                return company_name
        
        return 'Mediterranean Shipping (Thailand) Co., Ltd.'
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: TaxID 0105544019079
        pattern1 = r'TaxID\s*[:.]?\s*(\d{13})'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Pattern 2: Tax ID No. 0105544019079
        pattern2 = r'Tax\s+ID\s+No[.:]?\s*(\d{13})'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # Pattern: Date / วันที่ 15-OCT-2025 Branch No : 00000
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
    
    def extract_document_number(self, text: str) -> Optional[str]:
        """ดึงเลขที่เอกสารจาก No. 2510104513"""
        # Pattern: No. 2510104513
        pattern = r'No\.\s*(\d+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        Returns:
            ที่อยู่บริษัท (string) หรือ None
        """
        lines = text.split('\n')
        address_lines = []
        collecting = False
        
        # หาตำแหน่งที่เริ่มต้นที่อยู่ (มักจะอยู่หลังชื่อบริษัท)
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # หา "Head Office:" หรือ "Address:" หรือ "ที่อยู่" หรือ "Branch No"
            if any(keyword in line_clean for keyword in ['Head Office:', 'Address:', 'ที่อยู่:', 'Address', 'Branch No']):
                collecting = True
                # เก็บบรรทัดนี้ด้วย (ถ้ามีข้อมูล)
                if ':' in line_clean:
                    addr_part = line_clean.split(':', 1)[1].strip()
                    if addr_part and not addr_part.startswith('00000'):  # ไม่เก็บ Branch No
                        address_lines.append(addr_part)
                continue
            
            # ถ้ากำลังเก็บข้อมูลที่อยู่
            if collecting:
                # หยุดเมื่อเจอ TaxID, Tax ID, Date, หรือ No.
                if any(keyword in line_clean for keyword in ['TaxID', 'Tax ID', 'Date', 'No.', 'TAX INVOICE', 'Branch No']):
                    break
                
                # เก็บบรรทัดที่มีข้อมูล (ไม่ใช่บรรทัดว่าง)
                if line_clean and len(line_clean) > 5:
                    # ข้ามบรรทัดที่มี Branch No
                    if 'Branch No' in line_clean:
                        continue
                    address_lines.append(line_clean)
        
        # รวมที่อยู่ทั้งหมด
        if address_lines:
            address = ' '.join(address_lines).strip()
            # ทำความสะอาด: ลบ space หลายตัว
            address = re.sub(r'\s+', ' ', address)
            return address if len(address) > 10 else None
        
        return None
    
    def extract_account_info(self, text: str) -> Dict[str, Optional[str]]:
        """ดึงข้อมูลบัญชี (Account Name / Account Code)"""
        # สำหรับ MST ยังไม่มีข้อมูลบัญชีในเอกสาร
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
    
    def _extract_from_html_table(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงข้อมูลจากตาราง HTML โดยตรง
        
        รูปแบบตาราง:
        - Taxable Amount / ก่อนภาษีมูลค่าเพิ่ม | 1,800.00
        - Non-Taxable Amount / ไม่มีภาษีมูลค่าเพิ่ม | 1,500.00
        - 7% VAT / ภาษีมูลค่าเพิ่ม | 126.00
        - Total / รวม | 3,426.00
        
        Args:
            text: ข้อความที่อ่านจาก OCR (อาจมี HTML table)
        
        Returns:
            Dictionary ที่มีข้อมูลที่ดึงได้ หรือ None ถ้าไม่พบ
        """
        result = {
            'amount_before_vat': None,
            'amount_before_vat_2': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        try:
            # หาตาราง HTML ทั้งหมด
            table_pattern = r'<table[^>]*>(.*?)</table>'
            tables = re.findall(table_pattern, text, re.DOTALL | re.IGNORECASE)
            
            if not tables:
                return result
            
            # วนลูปทุกตาราง
            for table_html in tables:
                # แยก rows
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
                
                # เก็บข้อมูลชั่วคราวสำหรับเลือกค่าที่ถูกต้อง
                taxable_candidates = []  # เก็บค่าที่เป็นไปได้สำหรับ Taxable Amount
                
                for row in rows:
                    # แยก cells
                    cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
                    
                    if not cells:
                        continue
                    
                    # ทำความสะอาด cell content
                    cleaned_cells = []
                    for cell in cells:
                        # ลบ HTML tags
                        cell_text = re.sub(r'<[^>]+>', '', cell)
                        # ลบช่องว่างส่วนเกิน
                        cell_text = re.sub(r'\s+', ' ', cell_text).strip()
                        cleaned_cells.append(cell_text)
                    
                    if len(cleaned_cells) < 2:
                        continue
                    
                    # ตรวจสอบว่าเป็นแถวที่ต้องการ
                    row_text = ' '.join(cleaned_cells)
                    
                    # หาตัวเลขในแถว (มักจะอยู่ cell สุดท้าย)
                    amount_str = None
                    for cell in reversed(cleaned_cells):
                        # หาตัวเลขใน cell
                        numbers = re.findall(r'([\d,]+\.?\d{2})', cell)
                        if numbers:
                            amount_str = numbers[0]
                            break
                    
                    if not amount_str:
                        continue
                    
                    try:
                        amount = float(amount_str.replace(',', '').replace(' ', ''))
                        
                        # ตรวจสอบว่าเป็นแถวไหน
                        # แถวที่ 1: ก่อนภาษีมูลค่าเพิ่ม (Taxable Amount) - ต้องไม่มีคำว่า "ยอด" ข้างหน้า
                        if ('ก่อนภาษีมูลค่าเพิ่ม' in row_text or 'Taxable Amount' in row_text) and 'ยอด' not in row_text:
                            # ตรวจสอบว่าไม่ใช่แถว header (ไม่มีตัวเลขลำดับ เช่น "1 |", "2 |")
                            # และไม่ใช่แถวรายการ (ไม่มีคำว่า "CY CHARGE", "CLEANING" ฯลฯ)
                            is_header_row = bool(re.search(r'^\d+\s*\|', row_text)) or 'Description' in row_text or 'รายละเอียด' in row_text
                            is_item_row = bool(re.search(r'(CY CHARGE|CLEANING|GENERAL)', row_text, re.IGNORECASE))
                            
                            # ถ้าเป็นแถวสรุป (ไม่ใช่ header และไม่ใช่รายการ) หรือเป็นแถวที่มี "Taxable Amount" และ "ก่อนภาษีมูลค่าเพิ่ม" พร้อมกัน
                            is_summary_row = ('Taxable Amount' in row_text and 'ก่อนภาษีมูลค่าเพิ่ม' in row_text) or \
                                            (not is_header_row and not is_item_row and 'Taxable Amount' in row_text)
                            
                            if 100 <= amount < 100000000:
                                # เก็บค่าที่เป็นไปได้ทั้งหมด
                                taxable_candidates.append({
                                    'amount': amount,
                                    'is_summary': is_summary_row,
                                    'row_text': row_text
                                })
                                logger.info(f"🔍 พบยอดก่อนภาษี (บรรทัด 1) ในตาราง HTML: {amount} (is_summary: {is_summary_row})")
                        
                        # แถวที่ 2: ไม่มีภาษีมูลค่าเพิ่ม (Non-Taxable Amount)
                        elif 'ไม่มีภาษีมูลค่าเพิ่ม' in row_text or 'Non-Taxable Amount' in row_text:
                            if 100 <= amount < 100000000:
                                result['amount_before_vat_2'] = amount
                                logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 2) ในตาราง HTML: {amount}")
                        
                        # ภาษีมูลค่าเพิ่ม (VAT) - ต้องไม่มีคำว่า "ก่อน" หรือ "ไม่มี" ข้างหน้า
                        elif ('ภาษีมูลค่าเพิ่ม' in row_text or 'VAT' in row_text) and 'ก่อน' not in row_text and 'ไม่มี' not in row_text:
                            if 0 < amount < 100000000:
                                result['vat_amount'] = amount
                                logger.info(f"✅ พบยอดภาษีในตาราง HTML: {amount}")
                        
                        # รวม (Total)
                        elif 'รวม' in row_text or 'Total' in row_text:
                            if 100 <= amount < 100000000:
                                result['total_amount'] = amount
                                logger.info(f"✅ พบยอดรวมในตาราง HTML: {amount}")
                    
                    except ValueError:
                        continue
                
                # หลังจากวนลูปทุกแถวแล้ว ให้เลือกค่าที่ถูกต้องสำหรับ Taxable Amount
                if taxable_candidates:
                    # เรียงลำดับ: แถวสรุปมาก่อน, แล้วเลือกค่าที่มากที่สุด
                    summary_rows = [c for c in taxable_candidates if c['is_summary']]
                    if summary_rows:
                        # ถ้ามีแถวสรุป ให้เลือกค่าที่มากที่สุดจากแถวสรุป
                        best_candidate = max(summary_rows, key=lambda x: x['amount'])
                        result['amount_before_vat'] = best_candidate['amount']
                        logger.info(f"✅ เลือกยอดก่อนภาษี (บรรทัด 1) จากแถวสรุป: {best_candidate['amount']}")
                    else:
                        # ถ้าไม่มีแถวสรุป ให้เลือกค่าที่มากที่สุด (เพราะยอดรวมควรจะมากกว่ายอดรายการ)
                        best_candidate = max(taxable_candidates, key=lambda x: x['amount'])
                        result['amount_before_vat'] = best_candidate['amount']
                        logger.info(f"✅ เลือกยอดก่อนภาษี (บรรทัด 1) จากค่าที่มากที่สุด: {best_candidate['amount']}")
            
            # ตรวจสอบว่าดึงข้อมูลได้หรือไม่
            if any(result.values()):
                return result
            
        except Exception as e:
            logger.warning(f"⚠️ เกิดข้อผิดพลาดในการดึงข้อมูลจากตาราง HTML: {e}")
        
        return result
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด (MST มี 2 บรรทัด)
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (บรรทัดที่ 1)
                'amount_before_vat_2': float, # ยอดก่อนภาษี (บรรทัดที่ 2 - ไม่มีภาษี)
                'vat_amount': float,          # ยอดภาษี
                'total_amount': float         # ยอดรวม
            }
        """
        result = {
            'amount_before_vat': None,
            'amount_before_vat_2': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # Log ข้อความที่ได้รับ (สำหรับ debug)
        logger.debug(f"🔍 MST extract_amounts - Text length: {len(text)}")
        logger.debug(f"🔍 MST extract_amounts - First 500 chars: {text[:500]}")
        
        # ลองดึงข้อมูลจากตาราง HTML ก่อน
        table_data = self._extract_from_html_table(text)
        if table_data:
            logger.info(f"✅ พบข้อมูลในตาราง HTML")
            if table_data.get('amount_before_vat'):
                result['amount_before_vat'] = table_data['amount_before_vat']
                logger.info(f"✅ ดึงยอดก่อนภาษี (บรรทัด 1) จากตาราง HTML: {result['amount_before_vat']}")
            if table_data.get('amount_before_vat_2'):
                result['amount_before_vat_2'] = table_data['amount_before_vat_2']
                logger.info(f"✅ ดึงยอดก่อนภาษี (บรรทัด 2) จากตาราง HTML: {result['amount_before_vat_2']}")
            if table_data.get('vat_amount'):
                result['vat_amount'] = table_data['vat_amount']
                logger.info(f"✅ ดึงยอดภาษีจากตาราง HTML: {result['vat_amount']}")
            if table_data.get('total_amount'):
                result['total_amount'] = table_data['total_amount']
                logger.info(f"✅ ดึงยอดรวมจากตาราง HTML: {result['total_amount']}")
            
            # ถ้าดึงข้อมูลครบแล้ว ให้ return
            if result['amount_before_vat'] and result['amount_before_vat_2'] and result['vat_amount'] and result['total_amount']:
                logger.info(f"✅ ดึงข้อมูลครบทุกตัวจากตาราง HTML")
                return result
        
        # ลบ newline ที่อาจแทรกอยู่ในคำ
        text_clean = re.sub(r'(\S)\s*\n\s*(\S)', r'\1\2', text)
        # ลบ space หลายตัวในคำ (เช่น "มูลค่   าเพิ่ม" -> "มูลค่าเพิ่ม")
        text_clean = re.sub(r'([ก-๙])\s+([ก-๙])', r'\1\2', text_clean)
        # เพิ่ม space ระหว่างตัวเลขกับตัวอักษร (เช่น "1,800.00Taxable" -> "1,800.00 Taxable")
        text_clean = re.sub(r'([\d,]+\.?\d*)([A-Za-zก-๙])', r'\1 \2', text_clean)
        
        logger.debug(f"🔍 Text after cleaning (first 1000 chars): {text_clean[:1000]}")
        
        # ตรวจสอบว่ามีคีย์เวิร์ดในข้อความหรือไม่
        if 'ก่อนภาษีมูลค่าเพิ่ม' in text_clean:
            logger.info(f"✅ พบ 'ก่อนภาษีมูลค่าเพิ่ม' ในข้อความ")
            # หาตำแหน่งที่พบ
            idx = text_clean.find('ก่อนภาษีมูลค่าเพิ่ม')
            logger.info(f"   ตำแหน่ง: {idx}, ข้อความรอบๆ: '{text_clean[max(0, idx-50):idx+100]}'")
        else:
            logger.warning(f"❌ ไม่พบ 'ก่อนภาษีมูลค่าเพิ่ม' ในข้อความเลย")
        
        # Pattern 1: ก่อนภาษีมูลค่าเพิ่ม (Taxable Amount)
        # วิธี: หาคีย์เวิร์ด "ก่อนภาษีมูลค่าเพิ่ม" แล้วหาตัวเลขที่อยู่หลัง | ตัวถัดไป
        # รองรับรูปแบบต่างๆ: "ก่อนภาษีมูลค่าเพิ่ม | 1,800.00", "ก่อนภาษีมูลค่าเพิ่ม | / | 1,800.00", "Taxable Amount", "ก่อนภาษี" ฯลฯ
        patterns_before_vat = [
            # รูปแบบเต็ม: ก่อนภาษีมูลค่าเพิ่ม (รองรับ space หลายตัว) - ต้องไม่มีคำว่า "ยอด" ข้างหน้า
            r'(?<!ยอด)ก่อนภาษี\s*มูลค่า\s*เพิ่ม\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # ก่อนภาษี มูลค่า เพิ่ม | / | 1,800.00
            r'(?<!ยอด)ก่อนภาษี\s*มูลค่า\s*เพิ่ม\s*\|\s*([\d,]+\.?\d*)',  # ก่อนภาษี มูลค่า เพิ่ม | 1,800.00
            r'(?<!ยอด)ก่อนภาษีมูลค่าเพิ่ม\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # ก่อนภาษีมูลค่าเพิ่ม | / | 1,800.00
            r'(?<!ยอด)ก่อนภาษีมูลค่าเพิ่ม\s*\|\s*([\d,]+\.?\d*)',  # ก่อนภาษีมูลค่าเพิ่ม | 1,800.00
            r'(?<!ยอด)ก่อนภาษีมูลค่าเพิ่ม\s*:\s*([\d,]+\.?\d*)',  # ก่อนภาษีมูลค่าเพิ่ม : 1,800.00
            r'(?<!ยอด)ก่อนภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d*)',  # ก่อนภาษีมูลค่าเพิ่ม 1,800.00
            r'(?<!ยอด)ก่อนภาษีมูลค่าเพิ่ม[^|:]*[|:]\s*([\d,]+\.?\d*)',  # ก่อนภาษีมูลค่าเพิ่ม...|...1,800.00
            r'(?<!ยอด)ก่อนภาษีมูลค่าเพิ่ม[^|]*\|\s*([\d,]+\.?\d*)',  # ก่อนภาษีมูลค่าเพิ่ม...|...1,800.00 (fallback - ต้องมี |)
            # รูปแบบย่อ: ก่อนภาษี - ต้องไม่มีคำว่า "ยอด" ข้างหน้า
            r'(?<!ยอด)ก่อนภาษี\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # ก่อนภาษี | / | 1,800.00
            r'(?<!ยอด)ก่อนภาษี\s*\|\s*([\d,]+\.?\d*)',  # ก่อนภาษี | 1,800.00
            r'(?<!ยอด)ก่อนภาษี\s*:\s*([\d,]+\.?\d*)',  # ก่อนภาษี : 1,800.00
            r'(?<!ยอด)ก่อนภาษี\s+([\d,]+\.?\d*)',  # ก่อนภาษี 1,800.00
            r'(?<!ยอด)ก่อนภาษี[^|:]*[|:]\s*([\d,]+\.?\d*)',  # ก่อนภาษี...|...1,800.00
            # รูปแบบภาษาอังกฤษ: Taxable Amount (รองรับ space หลายตัว)
            r'Taxable\s+Amount\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # Taxable Amount | / | 1,800.00
            r'Taxable\s+Amount\s*\|\s*([\d,]+\.?\d*)',  # Taxable Amount | 1,800.00
            r'Taxable\s+Amount\s*:\s*([\d,]+\.?\d*)',  # Taxable Amount : 1,800.00
            r'Taxable\s+Amount\s+([\d,]+\.?\d*)',  # Taxable Amount 1,800.00
            r'Taxable\s+Amount[^|:]*[|:]\s*([\d,]+\.?\d*)',  # Taxable Amount...|...1,800.00
            r'Taxable[^|:]*[|:]\s*([\d,]+\.?\d*)',  # Taxable...|...1,800.00
        ]
        # ถ้ายังไม่ดึงข้อมูลจากตาราง HTML ให้ใช้ pattern matching
        if not result['amount_before_vat']:
            for idx, pattern in enumerate(patterns_before_vat):
                match = re.search(pattern, text_clean, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.info(f"✅ Pattern {idx+1} matched: '{pattern}' -> '{match.group(0)}' -> amount: '{amount_str}'")
                    try:
                        amount = float(amount_str)
                        # ตรวจสอบว่าเป็นตัวเลขที่สมเหตุสมผล (มากกว่า 100 เพื่อหลีกเลี่ยงตัวเลขเล็กๆ และไม่เกิน 100 ล้าน)
                        if 100 <= amount < 100000000:
                            result['amount_before_vat'] = amount
                            logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 1): {result['amount_before_vat']}")
                            break
                        else:
                            logger.warning(f"⚠️ ตัวเลขไม่สมเหตุสมผล: {amount} (ต้องมากกว่า 100)")
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                else:
                    logger.debug(f"🔍 Pattern {idx+1} ไม่ match: '{pattern}'")
        else:
            logger.info(f"⏭️ ข้าม pattern matching สำหรับยอดก่อนภาษี (บรรทัด 1) เพราะดึงจากตาราง HTML ได้แล้ว: {result['amount_before_vat']}")
        
        # ถ้ายังไม่พบ ลองหาด้วยวิธีอื่น: หาคีย์เวิร์ดแล้วหาตัวเลขที่อยู่ใกล้ๆ
        if not result['amount_before_vat']:
            logger.warning(f"⚠️ ไม่พบยอดก่อนภาษี (บรรทัด 1) - ลองหาด้วยวิธีอื่น...")
            # ลองหาคีย์เวิร์ดหลายแบบ
            keywords = ['ก่อนภาษีมูลค่าเพิ่ม', 'ก่อนภาษี', 'Taxable Amount', 'Taxable']
            for keyword in keywords:
                keyword_pos = text_clean.find(keyword)
                if keyword_pos != -1:
                    logger.info(f"   พบคีย์เวิร์ด '{keyword}' ที่ตำแหน่ง {keyword_pos}")
                    # หาตัวเลขที่อยู่หลังคีย์เวิร์ด (ภายใน 300 ตัวอักษร)
                    search_text = text_clean[keyword_pos:keyword_pos+300]
                    logger.debug(f"   ข้อความรอบๆ: '{search_text[:150]}'")
                    
                    # วิธีที่ 1: หาตัวเลขที่อยู่หลัง | หรือ : ตัวแรกที่อยู่หลังคีย์เวิร์ด (สำคัญที่สุด)
                    # หา | หรือ : ตัวแรกที่อยู่หลังคีย์เวิร์ด (ต้องอยู่หลังคีย์เวิร์ดเท่านั้น และต้องไม่มีคำว่า "ยอด" ข้างหน้า)
                    # ใช้ pattern ที่หาคีย์เวิร์ดแล้วตามด้วย | หรือ : และตัวเลข
                    # ตรวจสอบว่าไม่มีคำว่า "ยอด" ข้างหน้า (ภายใน 20 ตัวอักษร)
                    before_text = text_clean[max(0, keyword_pos-20):keyword_pos]
                    if 'ยอด' not in before_text:
                        direct_pattern = re.compile(rf'(?<!ยอด){re.escape(keyword)}\s*[^|:]*?[|:]\s*([\d,]+\.?\d*)', re.IGNORECASE)
                        direct_match = direct_pattern.search(text_clean, keyword_pos)
                        if direct_match:
                            num_str = direct_match.group(1)
                            try:
                                amount = float(num_str.replace(',', '').replace(' ', ''))
                                if 100 <= amount < 100000000:
                                    result['amount_before_vat'] = amount
                                    logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 1) ด้วยวิธีหา | ตัวแรกหลังคีย์เวิร์ด '{keyword}': {result['amount_before_vat']}")
                                break
                            except ValueError:
                                pass
                        else:
                            logger.debug(f"   ข้ามเพราะมีคำว่า 'ยอด' ข้างหน้า '{keyword}'")
                    
                    # วิธีที่ 2: หาตัวเลขที่อยู่หลัง | หรือ : (เรียงตามตำแหน่ง) - ถ้าวิธีที่ 1 ไม่ได้
                    if not result['amount_before_vat']:
                        matches = list(re.finditer(r'[|:]\s*([\d,]+\.?\d*)', search_text))
                        if matches:
                            # เลือกตัวเลขแรกที่สมเหตุสมผล (มากกว่า 100)
                            for match in matches:
                                num_str = match.group(1)
                                try:
                                    amount = float(num_str.replace(',', '').replace(' ', ''))
                                    if 100 <= amount < 100000000:
                                        result['amount_before_vat'] = amount
                                        logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 1) ด้วยวิธีหาใกล้ๆ '{keyword}': {result['amount_before_vat']}")
                                        break
                                except ValueError:
                                    continue
                            if result['amount_before_vat']:
                                break
                    
                    # วิธีที่ 3: หาตัวเลขที่อยู่หลังคีย์เวิร์ดโดยตรง (ไม่ต้องมี | หรือ :) - ใช้เป็น fallback สุดท้าย
                    # ต้องไม่มีคำว่า "ยอด" ข้างหน้า
                    if not result['amount_before_vat']:
                        before_text = text_clean[max(0, keyword_pos-20):keyword_pos]
                        if 'ยอด' not in before_text:
                            # หาตัวเลขที่อยู่หลังคีย์เวิร์ดโดยตรง (ภายใน 50 ตัวอักษรแรก)
                            direct_match = re.search(r'(?<!ยอด)ก่อนภาษีมูลค่าเพิ่ม\s*[^|:]*?([\d,]+\.?\d{2})', search_text[:100])
                            if direct_match:
                                num_str = direct_match.group(1)
                                try:
                                    amount = float(num_str.replace(',', '').replace(' ', ''))
                                    if 100 <= amount < 100000000:
                                        result['amount_before_vat'] = amount
                                        logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 1) ด้วยวิธีหาตัวเลขหลังคีย์เวิร์ดโดยตรง '{keyword}': {result['amount_before_vat']}")
                                        break
                                except ValueError:
                                    pass
                    
                    # วิธีที่ 3: หาตัวเลขที่อยู่ก่อนคีย์เวิร์ด (ในกรณีที่ตัวเลขอยู่ข้างหน้า)
                    if not result['amount_before_vat']:
                        before_text = text_clean[max(0, keyword_pos-100):keyword_pos]
                        # หาตัวเลขที่อยู่ก่อนคีย์เวิร์ด (มากกว่า 100)
                        before_numbers = re.findall(r'([\d,]+\.?\d{2})', before_text)
                        for num_str in reversed(before_numbers):  # เริ่มจากตัวเลขที่อยู่ใกล้คีย์เวิร์ดที่สุด
                            try:
                                amount = float(num_str.replace(',', '').replace(' ', ''))
                                if 100 <= amount < 100000000:
                                    result['amount_before_vat'] = amount
                                    logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 1) ด้วยวิธีหาตัวเลขก่อนคีย์เวิร์ด '{keyword}': {result['amount_before_vat']}")
                                    break
                            except ValueError:
                                continue
                        if result['amount_before_vat']:
                            break
                    
                    # ถ้ายังไม่พบ ให้ใช้ตัวเลขแรกที่มากกว่า 0
                    if not result['amount_before_vat']:
                        matches = list(re.finditer(r'[|:]\s*([\d,]+\.?\d*)', search_text))
                        if matches:
                            for match in matches:
                                num_str = match.group(1)
                                try:
                                    amount = float(num_str.replace(',', '').replace(' ', ''))
                                    if 0 < amount < 100000000:
                                        result['amount_before_vat'] = amount
                                        logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 1) ด้วยวิธีหาใกล้ๆ (fallback) '{keyword}': {result['amount_before_vat']}")
                                        break
                                except ValueError:
                                    continue
                        if result['amount_before_vat']:
                            break
        
        # Pattern 2: ไม่มีภาษีมูลค่าเพิ่ม (Non-Taxable Amount)
        # วิธี: หาคีย์เวิร์ด "ไม่มีภาษีมูลค่าเพิ่ม" แล้วหาตัวเลขที่อยู่หลัง | ตัวถัดไป
        # รองรับรูปแบบต่างๆ: "ไม่มีภาษีมูลค่าเพิ่ม | 1,500.00", "ไม่มีภาษีมูลค่าเพิ่ม | / | 1,500.00", "Non-Taxable Amount" ฯลฯ
        patterns_non_vat = [
            # รูปแบบเต็ม: ไม่มีภาษีมูลค่าเพิ่ม
            r'ไม่มีภาษีมูลค่าเพิ่ม\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # ไม่มีภาษีมูลค่าเพิ่ม | / | 1,500.00
            r'ไม่มีภาษีมูลค่าเพิ่ม\s*\|\s*([\d,]+\.?\d*)',  # ไม่มีภาษีมูลค่าเพิ่ม | 1,500.00
            r'ไม่มีภาษีมูลค่าเพิ่ม\s*:\s*([\d,]+\.?\d*)',  # ไม่มีภาษีมูลค่าเพิ่ม : 1,500.00
            r'ไม่มีภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d*)',  # ไม่มีภาษีมูลค่าเพิ่ม 1,500.00
            r'ไม่มีภาษีมูลค่าเพิ่ม[^|:]*[|:]\s*([\d,]+\.?\d*)',  # ไม่มีภาษีมูลค่าเพิ่ม...|...1,500.00
            r'ไม่มีภาษีมูลค่าเพิ่ม.*?([\d,]+\.?\d*)',  # ไม่มีภาษีมูลค่าเพิ่ม...1,500.00 (fallback)
            # รูปแบบย่อ: ไม่มีภาษี
            r'ไม่มีภาษี\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # ไม่มีภาษี | / | 1,500.00
            r'ไม่มีภาษี\s*\|\s*([\d,]+\.?\d*)',  # ไม่มีภาษี | 1,500.00
            r'ไม่มีภาษี\s*:\s*([\d,]+\.?\d*)',  # ไม่มีภาษี : 1,500.00
            r'ไม่มีภาษี\s+([\d,]+\.?\d*)',  # ไม่มีภาษี 1,500.00
            r'ไม่มีภาษี[^|:]*[|:]\s*([\d,]+\.?\d*)',  # ไม่มีภาษี...|...1,500.00
            # รูปแบบภาษาอังกฤษ: Non-Taxable Amount
            r'Non-Taxable\s+Amount\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # Non-Taxable Amount | / | 1,500.00
            r'Non-Taxable\s+Amount\s*\|\s*([\d,]+\.?\d*)',  # Non-Taxable Amount | 1,500.00
            r'Non-Taxable\s+Amount\s*:\s*([\d,]+\.?\d*)',  # Non-Taxable Amount : 1,500.00
            r'Non-Taxable\s+Amount\s+([\d,]+\.?\d*)',  # Non-Taxable Amount 1,500.00
            r'Non-Taxable\s+Amount[^|:]*[|:]\s*([\d,]+\.?\d*)',  # Non-Taxable Amount...|...1,500.00
            r'Non[-\s]?Taxable[^|:]*[|:]\s*([\d,]+\.?\d*)',  # Non-Taxable หรือ Non Taxable
        ]
        # ถ้ายังไม่ดึงข้อมูลจากตาราง HTML ให้ใช้ pattern matching
        if not result['amount_before_vat_2']:
            for idx, pattern in enumerate(patterns_non_vat):
                match = re.search(pattern, text_clean, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.info(f"✅ Pattern {idx+1} matched: '{pattern}' -> '{match.group(0)}' -> amount: '{amount_str}'")
                    try:
                        amount = float(amount_str)
                        if 100 <= amount < 100000000:
                            result['amount_before_vat_2'] = amount
                            logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 2): {result['amount_before_vat_2']}")
                            break
                        else:
                            logger.warning(f"⚠️ ตัวเลขไม่สมเหตุสมผล: {amount} (ต้องมากกว่า 100)")
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                else:
                    logger.debug(f"🔍 Pattern {idx+1} ไม่ match: '{pattern}'")
        else:
            logger.info(f"⏭️ ข้าม pattern matching สำหรับยอดก่อนภาษี (บรรทัด 2) เพราะดึงจากตาราง HTML ได้แล้ว: {result['amount_before_vat_2']}")
        
        # ถ้ายังไม่พบ ลองหาด้วยวิธีอื่น
        if not result['amount_before_vat_2']:
            logger.warning(f"⚠️ ไม่พบยอดก่อนภาษี (บรรทัด 2) - ลองหาด้วยวิธีอื่น...")
            keyword_pos = text_clean.find('ไม่มีภาษีมูลค่าเพิ่ม')
            if keyword_pos != -1:
                search_text = text_clean[keyword_pos:keyword_pos+200]
                matches = list(re.finditer(r'\|\s*([\d,]+\.?\d*)', search_text))
                if matches:
                    # เลือกตัวเลขแรกที่สมเหตุสมผล (มากกว่า 100)
                    for match in matches:
                        num_str = match.group(1)
                        try:
                            amount = float(num_str.replace(',', '').replace(' ', ''))
                            if 100 <= amount < 100000000:
                                result['amount_before_vat_2'] = amount
                                logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 2) ด้วยวิธีหาใกล้ๆ: {result['amount_before_vat_2']}")
                            break
                        except ValueError:
                            continue
                    # ถ้ายังไม่พบ ให้ใช้ตัวเลขแรก
                    if not result['amount_before_vat_2']:
                        for match in matches:
                            num_str = match.group(1)
                            try:
                                amount = float(num_str.replace(',', '').replace(' ', ''))
                                if 0 < amount < 100000000:
                                    result['amount_before_vat_2'] = amount
                                    logger.info(f"✅ พบยอดก่อนภาษี (บรรทัด 2) ด้วยวิธีหาใกล้ๆ (fallback): {result['amount_before_vat_2']}")
                                    break
                            except ValueError:
                                continue
        
        # Pattern 3: ภาษีมูลค่าเพิ่ม (7% VAT)
        # วิธี: หาคีย์เวิร์ด "ภาษีมูลค่าเพิ่ม" แล้วหาตัวเลขที่อยู่หลัง | ตัวถัดไป
        # ต้องไม่มีคำว่า "ก่อน" หรือ "ไม่มี" ข้างหน้า
        # รองรับรูปแบบต่างๆ: "ภาษีมูลค่าเพิ่ม | 126.00", "ภาษีมูลค่าเพิ่ม | / | 126.00", "7% VAT", "VAT" ฯลฯ
        patterns_vat = [
            # รูปแบบเต็ม: ภาษีมูลค่าเพิ่ม (ต้องไม่มี "ก่อน" หรือ "ไม่มี" ข้างหน้า)
            r'(?<!ก่อน)(?<!ไม่มี)ภาษีมูลค่าเพิ่ม\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม | / | 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษีมูลค่าเพิ่ม\s*\|\s*([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม | 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษีมูลค่าเพิ่ม\s*:\s*([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม : 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษีมูลค่าเพิ่ม\s+([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษีมูลค่าเพิ่ม[^|:]*[|:]\s*([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม...|...126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษีมูลค่าเพิ่ม.*?([\d,]+\.?\d*)',  # ภาษีมูลค่าเพิ่ม...126.00 (fallback)
            # รูปแบบย่อ: ภาษี (ต้องไม่มี "ก่อน" หรือ "ไม่มี" ข้างหน้า)
            r'(?<!ก่อน)(?<!ไม่มี)ภาษี\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # ภาษี | / | 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษี\s*\|\s*([\d,]+\.?\d*)',  # ภาษี | 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษี\s*:\s*([\d,]+\.?\d*)',  # ภาษี : 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษี\s+([\d,]+\.?\d*)',  # ภาษี 126.00
            r'(?<!ก่อน)(?<!ไม่มี)ภาษี[^|:]*[|:]\s*([\d,]+\.?\d*)',  # ภาษี...|...126.00
            # รูปแบบภาษาอังกฤษ: 7% VAT หรือ VAT
            r'(?:7%|7\s*%)\s*VAT\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # 7% VAT | / | 126.00
            r'(?:7%|7\s*%)\s*VAT\s*\|\s*([\d,]+\.?\d*)',  # 7% VAT | 126.00
            r'(?:7%|7\s*%)\s*VAT\s*:\s*([\d,]+\.?\d*)',  # 7% VAT : 126.00
            r'(?:7%|7\s*%)\s*VAT\s+([\d,]+\.?\d*)',  # 7% VAT 126.00
            r'VAT\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # VAT | / | 126.00 (ต้องไม่มี "ก่อน" หรือ "ไม่มี" ข้างหน้า)
            r'VAT\s*\|\s*([\d,]+\.?\d*)',  # VAT | 126.00
            r'VAT\s*:\s*([\d,]+\.?\d*)',  # VAT : 126.00
            r'VAT\s+([\d,]+\.?\d*)',  # VAT 126.00
        ]
        # ถ้ายังไม่ดึงข้อมูลจากตาราง HTML ให้ใช้ pattern matching
        if not result['vat_amount']:
            for idx, pattern in enumerate(patterns_vat):
                match = re.search(pattern, text_clean, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.info(f"✅ Pattern {idx+1} matched: '{pattern}' -> '{match.group(0)}' -> amount: '{amount_str}'")
                    try:
                        amount = float(amount_str)
                        if 0 < amount < 100000000:
                            result['vat_amount'] = amount
                            logger.info(f"✅ พบยอดภาษี: {result['vat_amount']}")
                            break
                        else:
                            logger.warning(f"⚠️ ตัวเลขไม่สมเหตุสมผล: {amount}")
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                else:
                    logger.debug(f"🔍 Pattern {idx+1} ไม่ match: '{pattern}'")
        else:
            logger.info(f"⏭️ ข้าม pattern matching สำหรับยอดภาษี เพราะดึงจากตาราง HTML ได้แล้ว: {result['vat_amount']}")
        
        # ถ้ายังไม่พบ ลองหาด้วยวิธีอื่น (ต้องไม่มีคำว่า "ก่อน" หรือ "ไม่มี" ข้างหน้า)
        if not result['vat_amount']:
            logger.warning(f"⚠️ ไม่พบยอดภาษี - ลองหาด้วยวิธีอื่น...")
            # หาทุกตำแหน่งของ "ภาษีมูลค่าเพิ่ม" ที่ไม่มี "ก่อน" หรือ "ไม่มี" ข้างหน้า
            for match in re.finditer(r'ภาษีมูลค่าเพิ่ม', text_clean, re.IGNORECASE):
                start_pos = match.start()
                # ตรวจสอบว่าไม่มี "ก่อน" หรือ "ไม่มี" ข้างหน้า (ภายใน 20 ตัวอักษร)
                before_text = text_clean[max(0, start_pos-20):start_pos]
                if 'ก่อน' not in before_text and 'ไม่มี' not in before_text:
                    search_text = text_clean[start_pos:start_pos+200]
                    numbers = re.findall(r'\|\s*([\d,]+\.?\d*)', search_text)
                    if numbers:
                        for num_str in numbers:
                            try:
                                amount = float(num_str.replace(',', '').replace(' ', ''))
                                if 0 < amount < 100000000:
                                    result['vat_amount'] = amount
                                    logger.info(f"✅ พบยอดภาษีด้วยวิธีหาใกล้ๆ: {result['vat_amount']}")
                                break
                            except ValueError:
                                continue
                    if result['vat_amount']:
                        break
        
        # Pattern 4: รวม (Total)
        # วิธี: หาคีย์เวิร์ด "รวม" แล้วหาตัวเลขที่อยู่หลัง | ตัวถัดไป
        # รองรับรูปแบบต่างๆ: "รวม | 3,426.00", "รวม | / | 3,426.00", "Total" ฯลฯ
        patterns_total = [
            # รูปแบบภาษาไทย: รวม
            r'รวม\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # รวม | / | 3,426.00
            r'รวม\s*\|\s*([\d,]+\.?\d*)',  # รวม | 3,426.00
            r'รวม\s*:\s*([\d,]+\.?\d*)',  # รวม : 3,426.00
            r'รวม\s+([\d,]+\.?\d*)',  # รวม 3,426.00
            r'รวม[^|:]*[|:]\s*([\d,]+\.?\d*)',  # รวม...|...3,426.00
            r'รวม.*?([\d,]+\.?\d*)',  # รวม...3,426.00 (fallback)
            # รูปแบบภาษาอังกฤษ: Total
            r'Total\s*\|\s*/\s*\|\s*([\d,]+\.?\d*)',  # Total | / | 3,426.00
            r'Total\s*\|\s*([\d,]+\.?\d*)',  # Total | 3,426.00
            r'Total\s*:\s*([\d,]+\.?\d*)',  # Total : 3,426.00
            r'Total\s+([\d,]+\.?\d*)',  # Total 3,426.00
            r'Total[^|:]*[|:]\s*([\d,]+\.?\d*)',  # Total...|...3,426.00
            r'Total.*?([\d,]+\.?\d*)',  # Total...3,426.00 (fallback)
        ]
        # ถ้ายังไม่ดึงข้อมูลจากตาราง HTML ให้ใช้ pattern matching
        if not result['total_amount']:
            for idx, pattern in enumerate(patterns_total):
                match = re.search(pattern, text_clean, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    logger.info(f"✅ Pattern {idx+1} matched: '{pattern}' -> '{match.group(0)}' -> amount: '{amount_str}'")
                    try:
                        amount = float(amount_str)
                        if 0 < amount < 100000000:
                            result['total_amount'] = amount
                            logger.info(f"✅ พบยอดรวม: {result['total_amount']}")
                            break
                        else:
                            logger.warning(f"⚠️ ตัวเลขไม่สมเหตุสมผล: {amount}")
                    except ValueError as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงเป็นตัวเลข: '{amount_str}', Error: {e}")
                else:
                    logger.debug(f"🔍 Pattern {idx+1} ไม่ match: '{pattern}'")
        else:
            logger.info(f"⏭️ ข้าม pattern matching สำหรับยอดรวม เพราะดึงจากตาราง HTML ได้แล้ว: {result['total_amount']}")
        
        # ถ้ายังไม่พบ ลองหาด้วยวิธีอื่น
        if not result['total_amount']:
            logger.warning(f"⚠️ ไม่พบยอดรวม - ลองหาด้วยวิธีอื่น...")
            keyword_pos = text_clean.find('รวม')
            if keyword_pos != -1:
                search_text = text_clean[keyword_pos:keyword_pos+200]
                numbers = re.findall(r'\|\s*([\d,]+\.?\d*)', search_text)
                if numbers:
                    for num_str in numbers:
                        try:
                            amount = float(num_str.replace(',', '').replace(' ', ''))
                            if 0 < amount < 100000000:
                                result['total_amount'] = amount
                                logger.info(f"✅ พบยอดรวมด้วยวิธีหาใกล้ๆ: {result['total_amount']}")
                            break
                        except ValueError:
                            continue
        
        # Log สรุปผลลัพธ์
        logger.info(f"📊 MST extract_amounts Results:")
        logger.info(f"   amount_before_vat (Line 1): {result['amount_before_vat']}")
        logger.info(f"   amount_before_vat_2 (Line 2): {result['amount_before_vat_2']}")
        logger.info(f"   vat_amount: {result['vat_amount']}")
        logger.info(f"   total_amount: {result['total_amount']}")
        
        return result
    
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
        
        Returns:
            1 = เอกสารมีภาษีมูลค่าเพิ่ม
            2 = เอกสารไม่มีภาษีมูลค่าเพิ่ม
        """
        # MST: มีทั้งยอดมี VAT และไม่มี VAT
        vat_amount = amounts.get('vat_amount') or 0
        has_vat = vat_amount > 0
        
        # ใช้แค่ 2 ประเภท: มีภาษี (1) หรือไม่มีภาษี (2)
        if has_vat:
            return 1  # มีภาษีมูลค่าเพิ่ม
        else:
            return 2  # ไม่มีภาษีมูลค่าเพิ่ม
    
    def extract_all_data(self, text: str, filename: str, filepath: str = None) -> Dict[str, Any]:
        """
        ดึงข้อมูลทั้งหมดจากเอกสาร MST
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร MST หรือไม่
        is_mst = self.is_company_document(text)
        
        if not is_mst:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร Mediterranean Shipping (Thailand)'
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
        document_number = self.extract_document_number(text)
        account_info = self.extract_account_info(text)
        amounts = self.extract_amounts(text)
        
        # Log ข้อมูลที่ดึงได้
        logger.info(f"📊 MST Extractor Results:")
        logger.info(f"   Company: {company_name}")
        logger.info(f"   Tax ID: {tax_id}")
        logger.info(f"   Date: {date}")
        logger.info(f"   Address: {address}")
        logger.info(f"   Document Number: {document_number}")
        logger.info(f"   Amount Line 1: {amounts.get('amount_before_vat')}")
        logger.info(f"   Amount Line 2: {amounts.get('amount_before_vat_2')}")
        logger.info(f"   VAT: {amounts.get('vat_amount')}")
        logger.info(f"   Total: {amounts.get('total_amount')}")
        
        withholding = self.extract_withholding_tax(text)
        bl_number = self.extract_bl_number(text)
        document_type = self.detect_document_type(text, amounts, withholding)
        
        # คำนวณยอดรวมก่อนภาษี (รวม 2 บรรทัด)
        line1_amount = amounts.get('amount_before_vat') or 0
        line2_amount = amounts.get('amount_before_vat_2') or 0
        vat_amount = amounts.get('vat_amount') or 0
        
        total_before_vat = line1_amount + line2_amount
        
        # คำนวณยอดรวมทั้งหมด (ก่อนภาษี + ภาษี)
        # ใช้ total_amount จากที่อ่านได้ หรือคำนวณเอง
        total_amount = amounts.get('total_amount')
        if not total_amount:
            # ถ้าไม่มี ให้คำนวณเอง: ยอดก่อนภาษีทั้งหมด + ภาษี
            total_amount = total_before_vat + vat_amount
        
        # หมายเหตุ: BL + ชื่อไฟล์เก่า
        remark = f"{bl_number} {filename}" if bl_number else filename
        
        return {
            'success': True,
            'company': 'MST',
            'company_name': company_name,
            'tax_id': tax_id,
            'date': date,
            'address': address,
            'document_number': document_number,
            'account_name': account_info['account_name'],
            'account_code': account_info['account_code'],
            'withholding_tax_percent': withholding['withholding_tax_percent'],
            'withholding_tax_amount': withholding['withholding_tax_amount'],
            'amount_before_vat': total_before_vat,  # รวมทั้ง 2 บรรทัด
            'vat_amount': vat_amount,
            'total_amount': total_amount,  # ยอดรวมทั้งหมด (คำนวณแล้ว)
            'remark': remark,
            'new_filename': filename,  # ใช้ชื่อเดิม
            'old_filename': filename,
            'filepath': filepath,
            'document_type': document_type,
            # ข้อมูลเพิ่มเติมสำหรับ MST (สำหรับสร้าง 2 แถว)
            'bl_number': bl_number,
            'amount_before_vat_line1': line1_amount,  # บรรทัดที่ 1
            'amount_before_vat_line2': line2_amount   # บรรทัดที่ 2 (ไม่มีภาษี)
        }
