"""
Kasikorn Bank Invoice Extractor
=================================
Extractor สำหรับดึงข้อมูลจาก บมจ.ธนาคารกสิกรไทย

Author: BotV3
Version: 3.0.0
"""

import re
from typing import Dict, Optional, Any
import logging

from ..base import BaseInvoiceExtractor

logger = logging.getLogger(__name__)


class KasikornBankExtractor(BaseInvoiceExtractor):
    """Extractor สำหรับดึงข้อมูลจาก บมจ.ธนาคารกสิกรไทย"""
    
    # Company identifiers
    COMPANY_IDENTIFIERS = [
        "บมจ.ธนาคารกสิกรไทย",
        "ธนาคารกสิกรไทย",
        "Kasikorn Bank",
        "KASIKORNBANK"
    ]
    
    # Tax ID
    TAX_ID = "0107536000315"
    
    def __init__(self):
        """Initialize Kasikorn Bank Extractor"""
        super().__init__()
        self.company_identifiers = self.COMPANY_IDENTIFIERS
    
    def is_company_document(self, text: str) -> bool:
        """
        ตรวจสอบว่าเป็นเอกสารของ บมจ.ธนาคารกสิกรไทย หรือไม่
        ต้องมีทั้ง 3 เงื่อนไข:
        1. ชื่อบริษัท "บมจ.ธนาคารกสิกรไทย"
        2. Tax ID "0107536000315"
        3. เอกสาร "ใบเสร็จรับเงิน / ใบกำกับภาษี" หรือ "RECEIPT / TAX INVOICE"
        
        Args:
            text: ข้อความที่อ่านจาก OCR
        
        Returns:
            True ถ้าเป็นเอกสาร บมจ.ธนาคารกสิกรไทย (มีทั้ง 3 เงื่อนไข)
        """
        if not text:
            return False
        
        # เงื่อนไข 1: ต้องมีชื่อบริษัท
        has_company = any(identifier in text for identifier in self.COMPANY_IDENTIFIERS)
        
        # เงื่อนไข 2: ต้องมี Tax ID "0107536000315"
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
        # หาชื่อบริษัทจาก "บมจ.ธนาคารกสิกรไทย สำนักงานใหญ่"
        # แต่ return เป็น "ธนาคารกสิกรไทย"
        return "ธนาคารกสิกรไทย"
    
    def extract_tax_id(self, text: str) -> Optional[str]:
        """ดึงเลขประจำตัวผู้เสียภาษี"""
        # Pattern: เลขประจำตัวผู้เสียภาษีอากร 0107536000315
        patterns = [
            r'เลขประจำตัวผู้เสียภาษีอากร\s+(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร 0107536000315
            r'เลขประจำตัวผู้เสียภาษีอากร\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษีอากร: 0107536000315
            r'TAX\s+ID\s+(\d{13})',  # TAX ID 0107536000315
            r'TAX\s+ID\s*[:.]?\s*(\d{13})',  # TAX ID: 0107536000315
            r'Tax\s+ID\s+(\d{13})',  # Tax ID 0107536000315
            r'Tax\s+ID\s*[:.]?\s*(\d{13})',  # Tax ID: 0107536000315
            r'TaxID\s*[:.]?\s*(\d{13})',  # TaxID: 0107536000315
            r'TAXID\s*[:.]?\s*(\d{13})',  # TAXID: 0107536000315
            r'เลขประจำตัวผู้เสียภาษี\s*[:.]?\s*(\d{13})',  # เลขประจำตัวผู้เสียภาษี: 0107536000315
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax_id = match.group(1).replace(' ', '').replace('-', '')
                if len(tax_id) == 13 and tax_id == self.TAX_ID:
                    return tax_id
        
        # Fallback: ถ้าไม่พบข้อมูล ให้ใช้ค่า default
        logger.info(f"⚠️ ไม่พบเลขประจำตัวผู้เสียภาษีในเอกสาร - ใช้ค่า default: {self.TAX_ID}")
        return self.TAX_ID
    
    def extract_branch(self, text: str) -> Optional[str]:
        """ดึงสาขา"""
        # Pattern: สาขาเมกาบางนา 2 หรือ BRANCH NAME: สาขาเมกาบางนา 2
        # ต้องการแค่ "เมกาบางนา 2" (ไม่ต้องมีคำว่า "สาขา")
        patterns = [
            # รูปแบบ: BRANCH NAME: สาขาเมกาบางนา 2
            r'BRANCH\s+NAME[^\n:]*:\s*สาขา\s*([^\n|]+?)(?:\s*\||\s*$|\s*\n)',  # BRANCH NAME: สาขาเมกาบางนา 2
            r'BRANCH\s+NAME[^\n:]*:\s*([^\n|]+?)(?:\s*\||\s*$|\s*\n)',  # BRANCH NAME: เมกาบางนา 2
            # รูปแบบ: สาขาเมกาบางนา 2 (ตัดคำว่า "สาขา" ออก)
            r'สาขา\s*([^\n|]+?)(?:\s*\||\s*$|\s*\n)',  # สาขาเมกาบางนา 2
            r'สาขา\s*([ก-๙A-Za-z0-9\s]+)',  # สาขาเมกาบางนา 2
            # รูปแบบ: Branch: เมกาบางนา 2
            r'Branch[^\n:]*:\s*([^\n|]+?)(?:\s*\||\s*$|\s*\n)',  # Branch: เมกาบางนา 2
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                branch = match.group(1).strip()
                # ตัดคำว่า "สาขา" ออกถ้ายังมีอยู่
                branch = re.sub(r'^สาขา\s*', '', branch, flags=re.IGNORECASE)
                branch = branch.strip()
                if branch and len(branch) > 0:
                    return branch
        
        return None
    
    def parse_html_table(self, text: str) -> Dict[str, str]:
        """
        Parse ข้อมูลจากตาราง HTML
        หา pattern เช่น: <td>วันที่ออกเอกสาร<br/>Issued Date</td><td>เลขที่เอกสาร<br/>Document number</td>
                        <td>11/11/2025</td><td>11112SE00020562</td>
        หรือ: วันที่ออกเอกสารIssued Date | เลขที่เอกสารDocument number
             11/11/2025 | 11112SE00020562 (text format)
        
        Returns:
            Dictionary ที่มี key-value จากตาราง
        """
        result = {}
        
        # Pattern สำหรับหา <tr>...</tr> ที่มีหลาย <td>
        tr_pattern = r'<tr[^>]*>(.*?)</tr>'
        tr_matches = re.findall(tr_pattern, text, re.IGNORECASE | re.DOTALL)
        
        logger.info(f"🔍 พบ <tr> tags: {len(tr_matches)} แถว")
        
        header_row = None
        header_keys = []
        
        for idx, tr_content in enumerate(tr_matches):
            logger.info(f"🔍 แถว {idx+1}: {tr_content[:150]}...")
            
            # หา <td> ทั้งหมดในแถว (รองรับ <br/> tag)
            td_pattern = r'<td[^>]*>(.*?)</td>'
            td_matches = re.findall(td_pattern, tr_content, re.IGNORECASE | re.DOTALL)
            
            if len(td_matches) < 2:
                continue
            
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
            
            logger.info(f"🔍 แถว {idx+1} หลังทำความสะอาด: {td_cleaned}")
            
            # ตรวจสอบว่าเป็น header row หรือไม่
            # Header row จะมี "วันที่ออกเอกสาร" หรือ "Issued Date" หรือ "เลขที่เอกสาร" หรือ "Document number"
            is_header = any(keyword in td_cleaned[0] for keyword in [
                'วันที่ออกเอกสาร', 'Issued Date', 'IssuedDate',
                'เลขที่เอกสาร', 'Document number', 'Documentnumber'
            ])
            
            if is_header:
                header_row = idx
                header_keys = td_cleaned
                logger.info(f"✅ พบ header row (แถว {idx+1}): {header_keys}")
                continue
            
            # ถ้าเจอ header row แล้ว ให้อ่าน data row
            if header_row is not None and len(td_cleaned) >= len(header_keys):
                # ตรวจสอบว่า td_cleaned[0] เป็นรูปแบบวันที่ (dd/mm/yyyy)
                date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', td_cleaned[0])
                if date_match:
                    # td_cleaned[0] คือวันที่ (ตรงกับ header_keys[0] ที่เป็น "วันที่ออกเอกสาร")
                    date_value = td_cleaned[0].strip()
                    # td_cleaned[1] คือเลขที่เอกสาร (ตรงกับ header_keys[1] ที่เป็น "เลขที่เอกสาร")
                    doc_num_value = td_cleaned[1].strip() if len(td_cleaned) > 1 else None
                    
                    # เก็บวันที่
                    result['วันที่ออกเอกสาร'] = date_value
                    result['IssuedDate'] = date_value
                    logger.info(f"✅ Parse HTML table (data row แถว {idx+1}): วันที่ออกเอกสาร = {date_value}")
                    
                    # เก็บเลขที่เอกสาร
                    if doc_num_value:
                        result['เลขที่เอกสาร'] = doc_num_value
                        result['Documentnumber'] = doc_num_value
                        logger.info(f"✅ Parse HTML table (data row แถว {idx+1}): เลขที่เอกสาร = {doc_num_value}")
                    
                    # หยุดหลังจากเจอ data row แรก
                    break
        
        # Fallback: ลองหาแบบ text format (| separated)
        # รูปแบบ: วันที่ออกเอกสารIssued Date | เลขที่เอกสารDocument number
        #         11/11/2025 | 11112SE00020562
        # อ่านทีละบรรทัดตามที่ OCR อ่านได้
        lines = text.split('\n')
        logger.info(f"🔍 เริ่มอ่านทีละบรรทัด (ทั้งหมด {len(lines)} บรรทัด)")
        
        for idx, line in enumerate(lines):
            line_clean = line.strip()
            logger.info(f"🔍 บรรทัด {idx+1}: {line_clean[:150]}...")
            
            if not line_clean:
                continue
            
            # ตรวจสอบว่าเป็น header row หรือไม่
            # Header row จะมี "วันที่ออกเอกสาร" หรือ "Issued Date" หรือ "เลขที่เอกสาร" หรือ "Document number"
            is_header = (
                'วันที่ออกเอกสาร' in line_clean or 
                'Issued Date' in line_clean or 
                'IssuedDate' in line_clean or
                ('เลขที่เอกสาร' in line_clean and 'Document' in line_clean)
            )
            
            if is_header and '|' in line_clean:
                logger.info(f"✅ พบ header row (บรรทัด {idx+1}): {line_clean[:100]}...")
                
                # ตรวจสอบบรรทัดถัดไปทันที (data row)
                if idx + 1 < len(lines):
                    next_line = lines[idx + 1].strip()
                    logger.info(f"🔍 ตรวจสอบบรรทัดถัดไป ({idx+2}): {next_line[:150]}...")
                    
                    if next_line and '|' in next_line:
                        next_parts = [p.strip() for p in next_line.split('|')]
                        logger.info(f"🔍 แยกส่วนได้ {len(next_parts)} ส่วน: {next_parts}")
                        
                        if len(next_parts) >= 2:
                            # ตรวจสอบว่า next_parts[0] เป็นรูปแบบวันที่ (dd/mm/yyyy)
                            date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', next_parts[0])
                            if date_match:
                                # next_parts[0] คือวันที่
                                date_value = next_parts[0].strip()
                                # next_parts[1] คือเลขที่เอกสาร
                                doc_num_value = next_parts[1].strip() if len(next_parts) > 1 else None
                                
                                # เก็บวันที่
                                result['วันที่ออกเอกสาร'] = date_value
                                result['IssuedDate'] = date_value
                                logger.info(f"✅ Parse text table (data row บรรทัด {idx+2}): วันที่ออกเอกสาร = {date_value}")
                                
                                # เก็บเลขที่เอกสาร
                                if doc_num_value:
                                    result['เลขที่เอกสาร'] = doc_num_value
                                    result['Documentnumber'] = doc_num_value
                                    logger.info(f"✅ Parse text table (data row บรรทัด {idx+2}): เลขที่เอกสาร = {doc_num_value}")
                                
                                # หยุดหลังจากเจอ data row
                                break
                            else:
                                logger.warning(f"⚠️ บรรทัด {idx+2} ไม่ใช่รูปแบบวันที่: {next_parts[0]}")
                    else:
                        logger.warning(f"⚠️ บรรทัด {idx+2} ไม่มี '|' หรือว่างเปล่า")
                else:
                    logger.warning(f"⚠️ ไม่มีบรรทัดถัดไป (บรรทัดสุดท้าย)")
        
        return result
    
    def extract_date(self, text: str) -> Optional[str]:
        """ดึงวันที่และแปลงเป็น dd/mm/yyyy"""
        # วิธีที่ 1: อ่านจาก HTML table (ลำดับแรก - ตรงกับโครงสร้างจริง)
        # รูปแบบ: วันที่ออกเอกสารIssued Date | เลขที่เอกสารDocument number
        #         11/11/2025 | 11112SE00020562
        table_data = self.parse_html_table(text)
        
        # หาวันที่จาก key "วันที่ออกเอกสาร" หรือ "IssuedDate"
        date_keys = ['วันที่ออกเอกสาร', 'IssuedDate', 'วันที่ออกเอกสารIssuedDate']
        for key in date_keys:
            if key in table_data:
                date_str = table_data[key].strip()
                # ตรวจสอบว่าเป็นรูปแบบวันที่ (dd/mm/yyyy)
                date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', date_str)
                if date_match:
                    day = date_match.group(1).zfill(2)
                    month = date_match.group(2).zfill(2)
                    year = date_match.group(3)
                    date_result = f"{day}/{month}/{year}"
                    logger.info(f"✅ พบวันที่จาก HTML table (key: {key}): {date_result}")
                    return date_result
        
        # วิธีที่ 2: อ่านจากรูปแบบที่มี | คั่น (fallback)
        # รูปแบบ: วันที่ออกเอกสาร Issued Date | เลขที่เอกสาร Document number
        #         11/11/2025 | 11112SE00020562
        patterns_pipe = [
            # รูปแบบที่สมบูรณ์: วันที่ออกเอกสาร Issued Date | เลขที่เอกสาร Document number | 11/11/2025 | 11112SE00020562
            r'วันที่ออกเอกสาร[^|]*Issued\s+Date[^|]*\|\s*เลขที่เอกสาร[^|]*Document\s+number[^|]*\|\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})\s*\|\s*[A-Z0-9]+',
            # รูปแบบที่ไม่มี Issued Date: วันที่ออกเอกสาร | เลขที่เอกสาร | 11/11/2025 | 11112SE00020562
            r'วันที่ออกเอกสาร[^|]*\|\s*เลขที่เอกสาร[^|]*\|\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})\s*\|\s*[A-Z0-9]+',
            # รูปแบบภาษาอังกฤษ: Issued Date | Document number | 11/11/2025 | 11112SE00020562
            r'Issued\s+Date[^|]*\|\s*Document\s+number[^|]*\|\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})\s*\|\s*[A-Z0-9]+',
        ]
        
        for pattern in patterns_pipe:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                # ตรวจสอบว่าไม่ใช่ "Date:" ที่เป็น Digital Signature
                match_start = match.start()
                context_before = text[max(0, match_start - 200):match_start]
                if 'Digitally signed' in context_before or re.search(r'Date:\s*\d{1,2}/\d{1,2}/\d{4}', context_before):
                    logger.warning(f"⚠️ ข้ามวันที่ที่พบ (น่าจะเป็น Digital Signature Date)")
                    continue
                
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                date_str = f"{day}/{month}/{year}"
                logger.info(f"✅ พบวันที่จาก 'วันที่ออกเอกสาร/Issued Date' (pipe): {date_str}")
                return date_str
        
        logger.warning("⚠️ ไม่พบวันที่จาก 'วันที่ออกเอกสาร/Issued Date'")
        return None
    
    def extract_document_number(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงเลขที่เอกสาร"""
        # ตรวจสอบว่าไม่ใช่ Tax ID
        tax_id = self.TAX_ID
        
        # Pattern: วันที่ออกเอกสารIssued Date | เลขที่เอกสารDocument number 01/11/2025 | 11112SE00020562
        # รองรับหลายรูปแบบที่ OCR อาจอ่านได้
        patterns = [
            # รูปแบบที่มี | คั่นระหว่างวันที่และเลขที่เอกสาร - หาเลขที่เอกสารที่อยู่หลัง |
            # รูปแบบ: วันที่ออกเอกสารIssued Date | เลขที่เอกสารDocument number | 12/11/2025 | 11112SE00020562
            r'วันที่ออกเอกสาร[^|]*\|\s*เลขที่เอกสาร[^|]*\|\s*\d{1,2}[/-]\d{1,2}[/-]\d{4}\s*\|\s*([A-Z0-9]{10,})',  # ...| 12/11/2025 | 11112SE00020562
            r'Issued\s+Date[^|]*\|\s*Document\s+number[^|]*\|\s*\d{1,2}[/-]\d{1,2}[/-]\d{4}\s*\|\s*([A-Z0-9]{10,})',  # ...| 12/11/2025 | 11112SE00020562
            # รูปแบบที่มี | คั่นแต่ไม่มีวันที่ (รองรับกรณีที่ OCR อ่านผิด)
            r'เลขที่เอกสาร[^|]*Document\s+number[^|]*\|\s*([A-Z0-9]{10,})',  # เลขที่เอกสารDocument number | 11112SE00020562
            r'Document\s+number[^|]*\|\s*([A-Z0-9]{10,})',  # Document number | 11112SE00020562
            # รูปแบบที่มี newline ระหว่าง header กับข้อมูล
            r'เลขที่เอกสาร[^\n]*\n[^\w]*([A-Z0-9]{10,})',  # เลขที่เอกสาร...\n...11112SE00020562
            r'Document\s+number[^\n]*\n[^\w]*([A-Z0-9]{10,})',  # Document number...\n...11112SE00020562
            # รูปแบบทั่วไป (รองรับช่องว่างผิดปกติ) - แต่ต้องไม่ใช่ Tax ID
            r'เลขที่เอกสาร[^\w]*([A-Z0-9]{10,})',  # เลขที่เอกสารDocument number ... 11112SE00020562
            r'Document\s+number[^\w]*([A-Z0-9]{10,})',  # Document number 11112SE00020562
            # รูปแบบที่มีช่องว่างผิดปกติ (รองรับ OCR ที่อ่านผิด)
            r'เลขที่[^\w]*([A-Z0-9]{6,}\s*[A-Z0-9]{4,})',  # เลขที่ 11112SE 00020562
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                doc_num = match.group(1).strip()
                # ลบช่องว่างออก
                doc_num = doc_num.replace(' ', '')
                # ตรวจสอบว่าไม่ใช่ Tax ID และมีความยาวอย่างน้อย 10 ตัวอักษร
                if len(doc_num) >= 10 and doc_num != tax_id:
                    # ตรวจสอบว่าไม่ใช่ตัวเลขล้วนๆ 13 หลัก (Tax ID format)
                    if not (doc_num.isdigit() and len(doc_num) == 13):
                        logger.info(f"✅ พบเลขที่เอกสาร: {doc_num}")
                        return doc_num
        
        # Fallback: ลองอ่านจากชื่อไฟล์ (ถ้ามี)
        # รูปแบบ: E-TAX_INVOICE_CARD_401017193759001_111125E00020562_20251111.pdf
        # เลขที่เอกสาร: 11112SE00020562 หรือ 111125E00020562
        if filename:
            # หา pattern ที่มีตัวอักษรและตัวเลขผสม (เช่น 11112SE00020562 หรือ 111125E00020562)
            filename_pattern = r'[_\s](\d{5,6}[A-Z]\d{8,10})[_\s]'
            match = re.search(filename_pattern, filename, re.IGNORECASE)
            if match:
                doc_num = match.group(1).strip()
                # ตรวจสอบว่าไม่ใช่ Tax ID
                if doc_num != tax_id and len(doc_num) >= 10:
                    logger.info(f"✅ พบเลขที่เอกสารจากชื่อไฟล์: {doc_num}")
                    return doc_num
        
        logger.warning("⚠️ ไม่พบเลขที่เอกสาร")
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        ดึงข้อมูลที่อยู่บริษัท
        
        ที่อยู่: 400/22 ถนนพหลโยธิน แขวงสามเสนใน เขตพญาไท กรุงเทพฯ 10400
        
        Returns:
            ที่อยู่รวม (string)
        """
        # ใช้ที่อยู่ที่กำหนดให้
        return "400/22 ถนนพหลโยธิน แขวงสามเสนใน เขตพญาไท กรุงเทพมหานคร 10400"
    
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
    
    def extract_amounts(self, text: str) -> Dict[str, Optional[float]]:
        """
        ดึงยอดเงินทั้งหมด
        
        จากตาราง:
        ประเภทรายการPAYMENT TYPE | จำนวนรายการITEM | ยอดเงินAMOUNT | ค่าธรรมเนียมFEE/COMMISSION AMOUNT | ภาษีมูลค่าเพิ่มVAT (7.00%) | ยอดเงินสุทธิNET AMOUNT
        บัตรเครดิต/เดบิต | 2 | 375.00 | 9.00 | 0.63 | 365.37
        
        Returns:
            {
                'amount_before_vat': float,  # ยอดก่อนภาษี (9.00) - จาก FEE/COMMISSION AMOUNT
                'vat_amount': float,          # ยอดภาษี (0.63) - จาก VAT (7.00%)
                'total_amount': float         # ยอดรวม (9.63) - คำนวณจาก amount_before_vat + vat_amount
            }
        """
        result = {
            'amount_before_vat': None,
            'vat_amount': None,
            'total_amount': None
        }
        
        # Pattern 1: หาแถวข้อมูลในตารางที่มี "บัตรเครดิต/เดบิต" หรือข้อมูลจริง
        # รูปแบบ: บัตรเครดิต/เดบิต | 2 | 375.00 | 9.00 | 0.63 | 365.37
        # ดึงค่าจากคอลัมน์ที่ 4 (FEE/COMMISSION AMOUNT = 9.00) และคอลัมน์ที่ 5 (VAT = 0.63)
        
        # วิธีที่ 1: หาแถวที่มี "บัตรเครดิต/เดบิต" หรือ "กระเป๋าเงินอิเล็กทรอนิกส์" (E-WALLET) แล้วแยกคอลัมน์
        # รองรับทั้งกรณีที่อยู่ในบรรทัดเดียวกันและแยกบรรทัด
        # รองรับทั้งรูปแบบ | และ HTML table format (<td>)
        card_row_patterns = [
            # รูปแบบบัตรเครดิต/เดบิต
            r'บัตรเครดิต[^\n]*เดบิต[^\n]*',  # บัตรเครดิต/เดบิต | 2 | 375.00 | 9.00 | 0.63 | 365.37
            r'บัตรเครดิต/เดบิต[^\n]*',  # บัตรเครดิต/เดบิต | 2 | 375.00 | 9.00 | 0.63 | 365.37
            r'บัตรเครดิต[^\n]*\|\s*[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*[^\n|]*',  # บัตรเครดิต | ... | ... | ... | ...
            # รูปแบบ E-WALLET (กระเป๋าเงินอิเล็กทรอนิกส์)
            r'กระเป๋าเงินอิเล็กทรอนิกส์[^\n]*',  # กระเป๋าเงินอิเล็กทรอนิกส์ | 1 | 75.00 | 1.20 | 0.08 | 73.72
            r'E-WALLET[^\n]*',  # E-WALLET | 1 | 75.00 | 1.20 | 0.08 | 73.72
            r'EWALLET[^\n]*',  # EWALLET | 1 | 75.00 | 1.20 | 0.08 | 73.72
            r'กระเป๋าเงิน[^\n]*',  # กระเป๋าเงิน | 1 | 75.00 | 1.20 | 0.08 | 73.72
            r'อิเล็กทรอนิกส์[^\n]*',  # อิเล็กทรอนิกส์ | 1 | 75.00 | 1.20 | 0.08 | 73.72
        ]
        
        for card_row_pattern in card_row_patterns:
            card_row_match = re.search(card_row_pattern, text, re.IGNORECASE | re.MULTILINE)
            if card_row_match:
                card_row = card_row_match.group(0)
                # ตรวจสอบว่าไม่ใช่แถว TOTAL
                # ข้ามแถว TOTAL แต่เก็บแถวที่มีข้อมูลจริง (บัตรเครดิต, เดบิต, กระเป๋าเงินอิเล็กทรอนิกส์, E-WALLET)
                if 'TOTAL' in card_row.upper():
                    # ตรวจสอบว่ามีข้อมูลจริงหรือไม่
                    has_data = any(keyword in card_row for keyword in [
                        'บัตรเครดิต', 'เดบิต', 'กระเป๋าเงิน', 'อิเล็กทรอนิกส์', 
                        'E-WALLET', 'EWALLET', 'E WALLET'
                    ])
                    if not has_data:
                        continue
                
                logger.info(f"🔍 พบแถวข้อมูล: {card_row[:150]}")
                
                # ตรวจสอบว่าเป็น HTML table format หรือ pipe format
                if '</td>' in card_row or '<td>' in card_row:
                    # HTML table format: แยกด้วย </td><td> หรือ <td> หรือ </td>
                    # รูปแบบ: บัตรเครดิต/เดบิต</td><td>2</td><td>375.00</td><td>9.00</td><td>0.63</td><td>365.37</td></tr>
                    # หา pattern: <td>value</td> หรือ value</td><td>value</td>
                    # ใช้ regex หาค่าที่อยู่ใน <td>...</td>
                    td_pattern = r'<td[^>]*>([^<]*)</td>'
                    columns = re.findall(td_pattern, card_row)
                    # กรองคอลัมน์ที่ว่างและไม่ใช่ "TOTAL"
                    columns = [col.strip() for col in columns if col.strip() and col.strip().upper() != 'TOTAL']
                    logger.info(f"🔍 HTML table format - จำนวนคอลัมน์: {len(columns)}, คอลัมน์: {columns}")
                else:
                    # Pipe format: แยกด้วย |
                    columns = [col.strip() for col in card_row.split('|')]
                    # กรองคอลัมน์ที่ว่างและไม่ใช่ "TOTAL"
                    columns = [col for col in columns if col.strip() and col.strip().upper() != 'TOTAL']
                    logger.info(f"🔍 Pipe format - จำนวนคอลัมน์: {len(columns)}, คอลัมน์: {columns}")
                
                # จาก log: คอลัมน์: ['2', '375.00', '9.00', '0.63', '365.37', 'TOTAL']
                # ตาราง: ประเภทรายการPAYMENT TYPE | จำนวนรายการITEM | ยอดเงินAMOUNT | ค่าธรรมเนียมFEE/COMMISSION AMOUNT | ภาษีมูลค่าเพิ่มVAT (7.00%) | ยอดเงินสุทธิNET AMOUNT
                # ข้อมูล: บัตรเครดิต/เดบิต | 2 | 375.00 | 9.00 | 0.63 | 365.37
                # 
                # แต่เมื่ออ่านจาก HTML table อาจจะไม่มีคอลัมน์แรก (บัตรเครดิต/เดบิต) เพราะอาจจะอยู่ใน tag อื่น
                # ดังนั้นคอลัมน์ที่ได้คือ:
                # คอลัมน์ที่ 0: '2' (จำนวนรายการ ITEM)
                # คอลัมน์ที่ 1: '375.00' (ยอดเงิน AMOUNT)
                # คอลัมน์ที่ 2: '9.00' (ค่าธรรมเนียม FEE/COMMISSION AMOUNT) ← ยอดก่อนภาษี
                # คอลัมน์ที่ 3: '0.63' (ภาษีมูลค่าเพิ่ม VAT) ← ยอดภาษี
                # คอลัมน์ที่ 4: '365.37' (ยอดเงินสุทธิ NET AMOUNT)
                # คอลัมน์ที่ 5: 'TOTAL' (ถ้ามี - จะถูกกรองออก)
                
                # ตรวจสอบจำนวนคอลัมน์ (ต้องมีอย่างน้อย 4 คอลัมน์: ITEM, AMOUNT, FEE, VAT)
                if len(columns) >= 4:
                    try:
                        # ค่าธรรมเนียม (คอลัมน์ที่ 3, index 2) - ยอดก่อนภาษี
                        fee_str = columns[2].replace(',', '').replace(' ', '').replace('<', '').replace('>', '').strip()
                        try:
                            fee = float(fee_str)
                            if fee > 0:
                                result['amount_before_vat'] = fee
                                logger.info(f"✅ พบยอดก่อนภาษี: {fee} (จากคอลัมน์ที่ 3, index 2: '{columns[2]}')")
                        except ValueError:
                            logger.warning(f"⚠️ ไม่สามารถแปลงค่าธรรมเนียมเป็นตัวเลขได้: '{fee_str}'")
                        
                        # ภาษีมูลค่าเพิ่ม (คอลัมน์ที่ 4, index 3) - ยอดภาษี
                        vat_str = columns[3].replace(',', '').replace(' ', '').replace('<', '').replace('>', '').strip()
                        try:
                            vat = float(vat_str)
                            if vat > 0:
                                result['vat_amount'] = vat
                                logger.info(f"✅ พบยอดภาษี: {vat} (จากคอลัมน์ที่ 4, index 3: '{columns[3]}')")
                        except ValueError:
                            logger.warning(f"⚠️ ไม่สามารถแปลงภาษีเป็นตัวเลขได้: '{vat_str}'")
                        
                        # ถ้าพบทั้งสองค่าแล้ว ให้หยุด
                        if result['amount_before_vat'] is not None and result['vat_amount'] is not None:
                            break
                    except (ValueError, IndexError) as e:
                        logger.warning(f"⚠️ ไม่สามารถแปลงค่าจากคอลัมน์ได้: {e}, columns: {columns}")
                        continue
        
        # วิธีที่ 2: ถ้ายังไม่พบ ให้ใช้ pattern matching (fallback)
        if result['amount_before_vat'] is None or result['vat_amount'] is None:
            # หาแถวที่มี "บัตรเครดิต" หรือ "เดบิต" หรือข้อมูลจริง (ไม่ใช่ header)
            # Pattern: [คำอธิบาย] | [ตัวเลข] | [ตัวเลข] | [ค่าธรรมเนียม] | [VAT] | [ยอดสุทธิ]
            # รองรับ newline และช่องว่างผิดปกติ
            table_row_patterns = [
                # รูปแบบเฉพาะ: หาแถวที่มี "บัตรเครดิต/เดบิต" (รองรับ / และ newline)
                r'บัตรเครดิต[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*[^\n|]*',
                r'บัตรเครดิต/เดบิต[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*[^\n|]*',
                r'เดบิต[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*[^\n|]*',
                # รูปแบบ E-WALLET (กระเป๋าเงินอิเล็กทรอนิกส์)
                r'กระเป๋าเงินอิเล็กทรอนิกส์[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*[^\n|]*',
                r'กระเป๋าเงิน[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*[^\n|]*',
                r'E-WALLET[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*[^\n|]*',
                r'EWALLET[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*[^\n|]*',
                # รูปแบบที่ยืดหยุ่น: หาแถวที่มี | อย่างน้อย 5 ตัว แล้วดึงค่าที่ 4 และ 5
                r'[^\n|]+\s*\|\s*[^\n|]*\s*\|\s*[^\n|]*\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*([\d,]+\.?\d{0,2})\s*\|\s*[^\n|]*',
            ]
            
            for pattern in table_row_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    try:
                        # ตรวจสอบว่าไม่ใช่แถว TOTAL
                        matched_text = match.group(0)
                        if 'TOTAL' in matched_text.upper():
                            # ตรวจสอบว่ามีข้อมูลจริงหรือไม่
                            has_data = any(keyword in matched_text for keyword in [
                                'บัตรเครดิต', 'เดบิต', 'กระเป๋าเงิน', 'อิเล็กทรอนิกส์', 
                                'E-WALLET', 'EWALLET', 'E WALLET'
                            ])
                            if not has_data:
                                continue
                        
                        # ค่าธรรมเนียม (คอลัมน์ที่ 4) - ยอดก่อนภาษี
                        if result['amount_before_vat'] is None:
                            fee_str = match.group(1).replace(',', '').replace(' ', '')
                            fee = float(fee_str)
                            if fee > 0:
                                result['amount_before_vat'] = fee
                                logger.info(f"✅ พบยอดก่อนภาษี (pattern): {fee}")
                        
                        # ภาษีมูลค่าเพิ่ม (คอลัมน์ที่ 5) - ยอดภาษี
                        if result['vat_amount'] is None:
                            vat_str = match.group(2).replace(',', '').replace(' ', '')
                            vat = float(vat_str)
                            if vat > 0:
                                result['vat_amount'] = vat
                                logger.info(f"✅ พบยอดภาษี (pattern): {vat}")
                        
                        # ถ้าพบทั้งสองค่าแล้ว ให้หยุด
                        if result['amount_before_vat'] is not None and result['vat_amount'] is not None:
                            break
                    except (ValueError, IndexError) as e:
                        logger.debug(f"⚠️ ไม่สามารถแปลงค่าได้: {e}")
                        continue
                
                # ถ้าพบทั้งสองค่าแล้ว ให้หยุด loop pattern
                if result['amount_before_vat'] is not None and result['vat_amount'] is not None:
                    break
        
        # Pattern 2: ถ้ายังไม่พบ ให้ลองหาจาก pattern อื่นๆ (fallback)
        if result['amount_before_vat'] is None:
            patterns_before_vat = [
                r'ค่าธรรมเนียม[^|]*\|\s*([\d,]+\.?\d{0,2})',  # ค่าธรรมเนียมFEE/COMMISSION AMOUNT | 9.00
                r'FEE/COMMISSION\s+AMOUNT[^|]*\|\s*([\d,]+\.?\d{0,2})',  # FEE/COMMISSION AMOUNT | 9.00
                r'FEE[^|]*\|\s*([\d,]+\.?\d{0,2})',  # FEE | 9.00
                r'COMMISSION[^|]*\|\s*([\d,]+\.?\d{0,2})',  # COMMISSION | 9.00
            ]
            
            for pattern in patterns_before_vat:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        amount_str = match.group(1).replace(',', '').replace(' ', '')
                        amount = float(amount_str)
                        if amount > 0:
                            result['amount_before_vat'] = amount
                            logger.info(f"✅ พบยอดก่อนภาษี (fallback): {amount}")
                            break
                    except ValueError:
                        continue
        
        # Pattern 3: ถ้ายังไม่พบ VAT ให้ลองหาจาก pattern อื่นๆ (fallback)
        if result['vat_amount'] is None:
            patterns_vat = [
                r'ภาษีมูลค่าเพิ่ม[^|]*VAT[^|]*\|\s*([\d,]+\.?\d{0,2})',  # ภาษีมูลค่าเพิ่มVAT (7.00%) | 0.63
                r'VAT\s*\([^)]*\)[^|]*\|\s*([\d,]+\.?\d{0,2})',  # VAT (7.00%) | 0.63
                r'ภาษีมูลค่าเพิ่ม[^|]*\|\s*([\d,]+\.?\d{0,2})',  # ภาษีมูลค่าเพิ่ม | 0.63
            ]
            
            for pattern in patterns_vat:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        vat_str = match.group(1).replace(',', '').replace(' ', '')
                        vat = float(vat_str)
                        if vat > 0:
                            result['vat_amount'] = vat
                            logger.info(f"✅ พบยอดภาษี (fallback): {vat}")
                            break
                    except ValueError:
                        continue
        
        # คำนวณยอดรวมจาก amount_before_vat + vat_amount
        if result['amount_before_vat'] is not None and result['vat_amount'] is not None:
            result['total_amount'] = result['amount_before_vat'] + result['vat_amount']
            logger.info(f"✅ คำนวณยอดรวม: {result['total_amount']} = {result['amount_before_vat']} + {result['vat_amount']}")
        else:
            logger.warning(f"⚠️ ไม่สามารถคำนวณยอดรวมได้ - ยอดก่อนภาษี: {result['amount_before_vat']}, ยอดภาษี: {result['vat_amount']}")
        
        return result
    
    def extract_remark(self, text: str, filename: str = None) -> Optional[str]:
        """ดึงหมายเหตุ"""
        # ไม่มี remark สำหรับ Kasikorn Bank
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
        ดึงข้อมูลทั้งหมดจากเอกสาร บมจ.ธนาคารกสิกรไทย
        
        Args:
            text: ข้อความที่อ่านจาก OCR
            filename: ชื่อไฟล์ PDF
            filepath: Path ของไฟล์ (optional)
        
        Returns:
            Dictionary ที่มีข้อมูลทั้งหมด
        """
        # ตรวจสอบว่าเป็นเอกสาร บมจ.ธนาคารกสิกรไทย หรือไม่
        is_company = self.is_company_document(text)
        
        if not is_company:
            return {
                'success': False,
                'company': None,
                'error': 'ไม่ใช่เอกสาร บมจ.ธนาคารกสิกรไทย'
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
        
        # สร้างชื่อไฟล์ใหม่: ค่าบริการบัตรเครดิต
        new_filename = "ค่าบริการบัตรเครดิต"
        
        # แยกที่อยู่เป็นส่วนๆ
        # ที่อยู่: 400/22 ถนนพหลโยธิน แขวงสามเสนใน เขตพญาไท กรุงเทพมหานคร 10400
        address_full = address or ''
        building_number = '400/22'  # เลขที่
        other_info = ''  # อื่นๆ (ว่าง)
        soi = ''  # ซอย/ตรอก
        road = 'ถนนพหลโยธิน'  # ถนน
        subdistrict = 'สามเสนใน'  # แขวง
        district = 'พญาไท'  # เขต
        province = 'กรุงเทพมหานคร'  # จังหวัด
        postal_code = '10400'  # รหัสไปรษณีย์
        
        return {
            'success': True,
            'company': 'KASIKORN_BANK',
            'company_name': company_name,
            'tax_id': tax_id,
            'branch': branch,
            'date': date,
            'document_number': document_number,
            'address': address,  # ที่อยู่รวม
            'address_full': address_full,  # ที่อยู่รวม (สำหรับ parse_address)
            'building_number': building_number,  # เลขที่ (400/22)
            'other_info': other_info,  # อื่นๆ (ว่าง)
            'soi': soi,  # ซอย/ตรอก
            'road': road,  # ถนน (ถนนพหลโยธิน)
            'subdistrict': subdistrict,  # แขวง (สามเสนใน)
            'district': district,  # เขต (พญาไท)
            'province': province,  # จังหวัด (กรุงเทพมหานคร)
            'postal_code': postal_code,  # รหัสไปรษณีย์ (10400)
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

